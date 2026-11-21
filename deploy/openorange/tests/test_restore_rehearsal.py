import json
import io
import os
from pathlib import Path
import runpy
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
restore = runpy.run_path(str(ROOT / 'bin/restore-rehearsal'))
import oolib


class RestoreTests(unittest.TestCase):
    def test_environment_uses_backed_secrets_and_private_endpoints(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            etc = Path(directory)
            (etc / 'apps').mkdir()
            (etc / 'apps/stats.env').write_text('S3_ENDPOINT=http://live\nORANGE_R2_A_S3_ENDPOINT=http://live\nGATEWAY_SECRET=backed\n')
            (etc / 'apps/stats.extra.env').write_text('APPLICATION_EVENTS_TOKEN=production\nEXTRA=backed\n')
            app = oolib.load().apps['stats']
            env = restore['app_env'](etc, app, 'http://engine-copy', 'http://store-copy', 4)
            self.assertEqual(env['S3_ENDPOINT'], 'http://store-copy')
            self.assertEqual(env['ORANGE_R2_A_S3_ENDPOINT'], 'http://store-copy')
            self.assertEqual(env['RIVET_ENDPOINT'], 'http://engine-copy')
            self.assertEqual(env['APPLICATION_EVENTS_TOKEN'], '')
            self.assertEqual(env['EXTRA'], 'backed')
            self.assertEqual(env['GATEWAY_SECRET'], 'backed')
            (etc / 'apps/stats.extra.env').unlink()
            self.assertEqual(restore['app_env'](etc, app, 'e', 's', 4)['S3_ENDPOINT'], 's')

    def test_backed_images_and_directories_are_used_by_shared_args(self):
        cfg = oolib.load()
        p = Path('/backup')
        engine = oolib.engine_args(cfg, 'copy', '10.0.0.2', p/'engine.env', p/'config', p/'log', p/'objects', image='engine@sha256:backed')
        store = oolib.store_args(cfg, 'copy-store', '10.0.0.3', p/'store.env', data_dir=p/'data', versions_dir=p/'versions', iam_dir=p/'iam', admin_dir=p/'admin', image='store@sha256:backed')
        self.assertIn('engine@sha256:backed', engine)
        self.assertIn('/backup/log:/var/lib/rivet/log', engine)
        self.assertIn('store@sha256:backed', store)
        self.assertIn('/backup/data:/data', store)
        self.assertIn('/backup/versions:/versions', store)
        self.assertIn('/backup/iam:/iam', store)

    def test_stream_hash_reads_in_bounded_chunks(self):
        class Stream(io.BytesIO):
            def read(self, size=-1):
                if size < 0 or size > 65536:
                    raise AssertionError('unbounded read')
                return super().read(size)
        size, digest = restore['digest_stream'](Stream(b'x' * 200000))
        import hashlib
        self.assertEqual((size, digest), (200000, hashlib.sha256(b'x' * 200000).hexdigest()))

    def test_bucket_fetches_every_object(self):
        class Client:
            def request(self, method, path, **kw):
                if path == '/bucket':
                    return 200, {}, b'<ListBucketResult><Contents><Key>a</Key><Size>3</Size></Contents><IsTruncated>false</IsTruncated></ListBucketResult>'
                self.path = path
                return 200, {}, kw['consume'](io.BytesIO(b'abc'))
        client = Client()
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            data = Path(directory)
            (data / 'bucket').mkdir()
            (data / 'bucket/a').write_bytes(b'abc')
            restore['verify_bucket'](client, 'bucket', data)
            self.assertEqual(client.path, '/bucket/a')
            (data / 'bucket/a').write_bytes(b'xyz')
            with self.assertRaisesRegex(RuntimeError, 'differs'):
                restore['verify_bucket'](client, 'bucket', data)


if __name__ == '__main__':
    unittest.main()


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class SoakTests(unittest.TestCase):
    def soak(self, statuses, soak_s=60, restart_every_s=0, recovers=True):
        clock = FakeClock()
        stops = []
        globals_ = restore['soak'].__globals__
        saved = globals_['time'], globals_['subprocess']
        globals_['time'] = clock
        globals_['subprocess'] = type('Subprocess', (), {'run': staticmethod(lambda argv, **kw: stops.append(argv))})
        self.addCleanup(lambda: globals_.update(time=saved[0], subprocess=saved[1]))
        answers = iter(statuses)

        def probe():
            clock.now += 0.05
            answer = next(answers, 200)
            return answer if isinstance(answer, tuple) else (answer, b'')

        def healthy():
            clock.now += 1
            return recovers

        args = type('Args', (), {'soak_s': soak_s, 'restart_every_s': restart_every_s})()
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            restore['soak'](args, probe, lambda: stops.append(['restart']), healthy)
        return [line for line in out.getvalue().splitlines()], stops

    def test_reports_latency_and_passes_when_every_probe_answers(self):
        lines, stops = self.soak([])
        self.assertIn('"ok_probes": 6', lines[-1])
        self.assertIn('"failed_outside_recovery": 0', lines[-1])
        self.assertEqual(stops, [])

    def test_a_failure_outside_a_restart_window_fails_the_soak(self):
        with self.assertRaises(RuntimeError):
            self.soak([200, 503])

    def test_failures_right_after_an_engine_restart_are_excused(self):
        lines, stops = self.soak([200, 200, 200, 503, 503], soak_s=60, restart_every_s=20)
        self.assertEqual(stops, [['restart']] * 2)
        self.assertIn('"restarts": 2', lines[-1])
        self.assertIn('"failed_outside_recovery": 0', lines[-1])

    def test_an_engine_that_does_not_recover_fails_the_soak(self):
        with self.assertRaises(RuntimeError):
            self.soak([], soak_s=60, restart_every_s=10, recovers=False)


    def test_a_failed_probe_records_when_it_happened_and_what_it_answered(self):
        clock = FakeClock()
        globals_ = restore['soak'].__globals__
        saved = globals_['time']
        globals_['time'] = clock
        self.addCleanup(lambda: globals_.update(time=saved))
        args = type('Args', (), {'soak_s': 20, 'restart_every_s': 0})()
        out = io.StringIO()
        with self.assertRaises(RuntimeError), unittest.mock.patch('sys.stdout', out):
            restore['soak'](args, lambda: (500, b'engine unavailable'), lambda: None, lambda: True)
        failed = json.loads(out.getvalue().splitlines()[0])
        self.assertEqual(failed['event'], 'probe_failed')
        self.assertEqual(failed['body'], 'engine unavailable')
        self.assertRegex(failed['at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')


class EngineRestartTests(unittest.TestCase):
    def test_the_engine_restarts_only_after_its_stopped_container_is_removed(self):
        clock = FakeClock()
        calls = []
        present = iter([True, True, False])

        def run(argv, **kw):
            calls.append(argv[:2])
            code = 0 if argv[1] != 'inspect' or next(present) else 1
            return type('Done', (), {'returncode': code})()

        restore['stop_engine']('engine', run, clock)
        self.assertEqual(calls, [['docker', 'stop'], ['docker', 'inspect'], ['docker', 'inspect'], ['docker', 'inspect']])

    def test_a_stopped_engine_that_is_never_removed_fails_instead_of_racing_its_restart(self):
        clock = FakeClock()
        run = lambda argv, **kw: type('Done', (), {'returncode': 0})()
        with self.assertRaises(RuntimeError):
            restore['stop_engine']('engine', run, clock)


class EvidenceTests(unittest.TestCase):
    def test_a_failed_rehearsal_keeps_engine_logs_and_container_output(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            root, dest = Path(directory) / 'root', Path(directory) / 'evidence'
            (root / 'engine/log').mkdir(parents=True)
            (root / 'engine/log/engine.log').write_text('refusing envoy connect\n')

            def run(argv, **kw):
                return type('Done', (), {'returncode': 0, 'stdout': f'output of {argv[-1]}\n'.encode(), 'stderr': b''})()

            restore['preserve_evidence'](root, ['store', 'app'], dest, run)
            self.assertEqual((dest / 'engine-log/engine.log').read_text(), 'refusing envoy connect\n')
            self.assertEqual((dest / 'app.log').read_bytes(), b'output of app\n')
            self.assertEqual((dest / 'store.log').read_bytes(), b'output of store\n')
            self.assertEqual(dest.stat().st_mode & 0o777, 0o700)


class RehearsalRootTests(unittest.TestCase):
    def test_rehearsals_started_in_the_same_second_get_separate_copies(self):
        state = Path('/var/lib/openorange')
        first = restore['rehearsal_root'](state, '20261121T071514Z', 101)
        second = restore['rehearsal_root'](state, '20261121T071514Z', 102)
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent, state / 'restore')
