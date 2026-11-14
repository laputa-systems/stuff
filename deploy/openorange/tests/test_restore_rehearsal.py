import io
import os
from pathlib import Path
import runpy
import tempfile
import unittest

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
