import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import oobuild


class BuildTest(unittest.TestCase):
    def test_version_counts_patches(self):
        self.assertEqual(oobuild.downstream_version('1.0.2', [{}, {}]), '1.0.2-laputa.2')
        with self.assertRaises(ValueError):
            oobuild.downstream_version('1.0.2', [])

    def test_acquire_rejects_wrong_revision_before_checkout(self):
        calls = []
        def run(argv, **kwargs):
            calls.append(argv)
            return '0' * 40 if argv[1] == 'rev-parse' else ''
        with tempfile.TemporaryDirectory(dir=ROOT.parents[1] / '.work/tmp') as tmp:
            with self.assertRaisesRegex(ValueError, 'fetched revision'):
                oobuild.acquire(Path(tmp) / 'source', run)
        self.assertFalse(any('checkout' in call for call in calls))

    def test_build_requires_store(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parents[1] / '.work/tmp') as tmp:
            with self.assertRaisesRegex(ValueError, 'offline build requires'):
                oobuild.build(tmp, Path(tmp) / 'out')

    def test_record_rejects_unknown_fields_and_bad_digests(self):
        record = {'schema': 'openorange-build-record/1', 'component': 'open-orange', 'upstream': {'repository': 'repo', 'revision': 'a' * 40}, 'patches': [{'file': 'a.patch', 'sha256': 'sha256:' + 'a' * 64}], 'lockfile_sha256': 'sha256:' + 'b' * 64, 'node': '26.0.0', 'pnpm': '10.34.9', 'source_date_epoch': 1, 'platform': 'js', 'tarball': {'file': 'a.tgz', 'sha256': 'sha256:' + 'c' * 64}, 'downstream_version': '1.0.2-laputa.1'}
        oobuild.validate_record(record)
        bad = copy.deepcopy(record)
        bad['patches'][0]['extra'] = True
        with self.assertRaises(ValueError):
            oobuild.validate_record(bad)
        bad = copy.deepcopy(record)
        bad['tarball']['sha256'] = 'bad'
        with self.assertRaises(ValueError):
            oobuild.validate_record(bad)


if __name__ == '__main__':
    unittest.main()
