import copy
import sys
import tempfile
import unittest
from pathlib import Path

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

    def test_build_uses_acquired_pnpm_for_all_commands(self):
        calls = []
        def run(argv, **kwargs):
            calls.append((argv, kwargs))
            if argv[1:3] == ['rev-parse', 'HEAD']:
                return oobuild.component()['revision']
            if '--format=%ct' in argv:
                return '1'
            if argv[-1] == '--version':
                return '10.34.9' if len(argv) > 2 else 'v26.12.0'
            if 'pack' in argv:
                (output / 'package.tgz').write_bytes(b'package')
            return ''
        with tempfile.TemporaryDirectory(dir=ROOT.parents[1] / '.work/tmp') as tmp:
            root = Path(tmp)
            source = root / 'source'
            source.mkdir()
            (root / 'store').mkdir()
            tool = root / 'toolchain'
            tool.mkdir()
            (tool / 'pnpm.tgz').write_bytes(b'pnpm')
            (tool / 'integrity').write_text(oobuild.integrity(b'pnpm'))
            (source / 'package.json').write_text('{"version":"1.0.2","packageManager":"pnpm@10.34.9","engines":{"node":">=22"}}')
            (source / 'pnpm-lock.yaml').write_text('lock')
            output = root / 'out'
            oobuild.build(root, output, run)
            pnpm_calls = [(argv, opts) for argv, opts in calls if len(argv) > 1 and argv[1].endswith('pnpm.cjs')]
            self.assertEqual([argv[2] for argv, _ in pnpm_calls], ['--version', 'install', 'build', 'pack'])
            for argv, opts in pnpm_calls:
                self.assertEqual(argv[:2], ['node', str(tool / 'pnpm/bin/pnpm.cjs')])
                self.assertEqual(opts['env']['npm_config_manage_package_manager_versions'], 'false')
                self.assertTrue(opts['env']['PATH'].startswith(str(tool / 'bin') + ':'))

    def test_record_rejects_unknown_fields_and_bad_digests(self):
        record = {'schema': 'openorange-build-record/1', 'component': 'open-orange', 'upstream': {'repository': 'repo', 'revision': 'a' * 40}, 'patches': [{'file': 'a.patch', 'sha256': 'sha256:' + 'a' * 64}], 'lockfile_sha256': 'sha256:' + 'b' * 64, 'node': '26.0.0', 'pnpm': '10.34.9', 'pnpm_integrity': 'sha512-' + 'A' * 86 + '==', 'source_date_epoch': 1, 'platform': 'js', 'tarball': {'file': 'a.tgz', 'sha256': 'sha256:' + 'c' * 64}, 'downstream_version': '1.0.2-laputa.1'}
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
