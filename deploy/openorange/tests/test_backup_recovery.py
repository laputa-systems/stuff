import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
backup = runpy.run_path(str(ROOT / 'bin/backup'))


class BackupRecoveryTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith('linux'), 'backup uses Linux rsync xattr flags')
    def test_fenced_pass_reconciles_changed_bytes_and_deleted_files(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            state = Path(directory) / 'state'
            out = Path(directory) / 'copy'
            for sub in ('engine/log', 'engine/objects', 'store/data', 'store/versions', 'store/iam'):
                (state / sub).mkdir(parents=True)
            source = state / 'store/data/object'
            source.write_bytes(b'before')
            (state / 'store/data/deleted').write_bytes(b'old')
            cfg = SimpleNamespace(state=state)
            backup['copy_state'](cfg, out, None, fenced=False)
            previous = source.stat()
            source.write_bytes(b'after!')
            os.utime(source, ns=(previous.st_atime_ns, previous.st_mtime_ns))
            (state / 'store/data/deleted').unlink()
            backup['copy_state'](cfg, out, None, fenced=True)
            self.assertEqual((out / 'store/data/object').read_bytes(), b'after!')
            self.assertFalse((out / 'store/data/deleted').exists())

    def exercise_failure(self, failure):
        main = backup['main']
        scope = main.__globals__
        cfg = scope['oolib'].load()
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            cfg.stack['state_dir'] = directory
            cfg.stack['run_dir'] = str(Path(directory) / 'run')
            initially_up = {'oo-store', 'oo-engine', 'oo-identity', 'oo-ingress', cfg.orange_apps()[0].service}
            running = set(initially_up)
            started = []
            handlers = {}

            def install(sig, handler):
                handlers[sig] = handler

            def drain(*args, **kwargs):
                running.clear()
                if isinstance(failure, int):
                    handlers[failure](failure, None)
                raise subprocess.CalledProcessError(1, args)

            def process(args, **kwargs):
                self.assertEqual(args[0], 'rc-service')
                self.assertEqual(args[2], 'start')
                started.append(args[1])
                running.add(args[1])
                return subprocess.CompletedProcess(args, 0)

            with patch.dict(scope, {'running': lambda svc: svc in running, 'run': drain, 'du': lambda _: 0, 'copy_state': lambda *args, **kwargs: None}), \
                 patch.object(scope['oolib'], 'load', return_value=cfg), \
                 patch.object(scope['os'], 'geteuid', return_value=0), \
                 patch.object(scope['shutil'], 'disk_usage', return_value=type('Disk', (), {'free': 8 << 30})()), \
                 patch.object(scope['signal'], 'signal', side_effect=install), \
                 patch.object(scope['subprocess'], 'run', side_effect=process), \
                 patch.object(scope['sys'], 'argv', ['backup', '--no-restart']):
                with self.assertRaises(SystemExit) as result:
                    main()
            self.assertEqual(result.exception.code, 1)
            self.assertEqual(set(started), initially_up)
            self.assertEqual(running, initially_up)
            self.assertNotIn('oo-tunnel', started)
            self.assertNotIn('oo-dns', started)
            self.assertLess(started.index('oo-app.stats'), started.index('oo-ingress'))
            self.assertTrue(callable(handlers[signal.SIGTERM]))
            self.assertTrue(callable(handlers[signal.SIGINT]))

    def test_partial_drain_error_restores_only_previously_running_services(self):
        self.exercise_failure(None)

    def test_signals_during_drain_restore_only_previously_running_services(self):
        for sig in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(signal=sig):
                self.exercise_failure(sig)


if __name__ == '__main__':
    unittest.main()
