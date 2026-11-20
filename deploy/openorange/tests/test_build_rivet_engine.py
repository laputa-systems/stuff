import sys
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import oobuild


class EngineBuildTest(unittest.TestCase):
    def test_acquire_checks_each_patch_before_applying_in_registry_order(self):
        item = oobuild.engine_component()
        commands = []

        def runner(argv, cwd=None, env=None):
            commands.append(argv)
            return item['revision'] if argv[:2] == ['git', 'rev-parse'] else ''

        with tempfile.TemporaryDirectory(dir=Path.cwd() / '.work/tmp') as tmp:
            oobuild.acquire_engine(Path(tmp) / 'acquired', runner)
        applies = [command for command in commands if command[:2] == ['git', 'apply']]
        self.assertEqual(len(applies), 12)
        for index, entry in enumerate(item['patches']):
            check, apply = applies[2 * index:2 * index + 2]
            self.assertEqual(check[2], '--check')
            self.assertEqual(check[3], apply[2])
            self.assertEqual(Path(apply[2]).name, entry['file'])
        self.assertIn('cargo vendor --locked /src/cargo-vendor > vendor-config.toml', commands[-1][-1])

    def test_record_rejects_changed_identity_and_unknown_fields(self):
        item = oobuild.engine_component()
        record = {'schema': 'rivet-engine-build-record/1', 'component': item['name'], 'upstream': {'repository': item['upstream'], 'revision': item['revision']}, 'patches': [{'file': p['file'], 'sha256': 'sha256:' + p['sha256']} for p in item['patches']], 'lockfile_sha256': 'sha256:' + '1' * 64, 'builder': oobuild.ENGINE_BUILDER, 'rustc': 'release: 1.99.0\nhost: x86_64-unknown-linux-gnu', 'source_date_epoch': 1, 'platform': 'linux-x86_64', 'rustflags': '--cfg tokio_unstable', 'jobs': 4, 'memory_bytes': 8589934592, 'binary': {'file': 'rivet-engine', 'sha256': 'sha256:' + '2' * 64}}
        self.assertEqual(oobuild.validate_engine_record(record), record)
        for key, value in [('jobs', True), ('builder', 'other'), ('patches', []), ('surprise', 1)]:
            invalid = copy.deepcopy(record)
            invalid[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                oobuild.validate_engine_record(invalid)

    def test_acquire_rejects_modified_patch(self):
        with patch.object(oobuild, 'digest', return_value='sha256:' + '0' * 64):
            with self.assertRaisesRegex(ValueError, 'patch sha256 mismatch'):
                oobuild.engine_component()


if __name__ == '__main__':
    unittest.main()
