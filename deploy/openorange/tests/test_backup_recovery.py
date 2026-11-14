import os
from pathlib import Path
import runpy
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
backup = runpy.run_path(str(ROOT / 'bin/backup'))


class BackupRecoveryTests(unittest.TestCase):
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

            with patch.dict(scope, {'running': lambda svc: svc in running, 'run': drain, 'du': lambda _: 0}), \
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
