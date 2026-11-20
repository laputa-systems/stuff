import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
import oorelease  # noqa: E402


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.manifest = {'schema': 'openorange-release-manifest/1', 'id': '', 'commits': {'stats': 'a' * 40, 'stuff': 'b' * 40}, 'sources': [{'name': 'rivet', 'revision': 'c' * 40, 'patches': [{'file': 'x.patch', 'sha256': 'sha256:' + 'a' * 64}]}], 'lockfiles': {'pnpm': 'sha256:' + 'b' * 64}, 'toolchains': {'node': '26'}, 'build': {'recipe': 'make', 'target_arch': 'x86_64', 'libc': 'musl', 'features': [], 'inspector_ui': False}, 'artifacts': {'packages': {'rivetkit': 'sha256:' + 'c' * 64}, 'native_addon': {'addon': 'sha256:' + 'c' * 64}, 'executables': {'engine': 'sha256:' + 'c' * 64}}, 'compatibility': {'config': 'v1', 'persisted_format': 'v1'}, 'previous_release': 'oor-' + 'a' * 16, 'recovery_method': 'restore backup'}
        self.manifest['id'] = oorelease.manifest_id(self.manifest)

    def test_valid_roundtrip(self):
        self.assertEqual(oorelease.validate_manifest(json.loads(json.dumps(self.manifest))), self.manifest)

    def test_invalid(self):
        for mutate in ('unknown', 'digest', 'previous'):
            item = copy.deepcopy(self.manifest)
            if mutate == 'unknown':
                item['build']['extra'] = 1
            elif mutate == 'digest':
                item['artifacts']['native_addon']['addon'] = 'sha256:bad'
            else:
                del item['previous_release']
            with self.subTest(mutate=mutate), self.assertRaises(oorelease.ValidationError):
                oorelease.validate_manifest(item)


class InspectionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        repo = Path(self.temp.name) / 'deploy/orange'
        repo.mkdir(parents=True)
        self.package = json.dumps({'dependencies': {'open-orange': '1.0.2', 'rivetkit': '3.1.2-rc.1'}})
        (repo / 'package.json').write_text(self.package)
        (repo / 'pnpm-lock.yaml').write_text('lock')
        self.inventory = {'ssh_config': 'ssh_config', 'hosts': {'lisa': {'kind': 'oo-containers', 'writer_address': 'local:80', 'doas': True, 'engine_container': 'oo-engine', 'engine_config': '/etc/openorange/engine/config.json', 'storage_roots': ['/var/lib/openorange/engine']}, 'stats-standby': {'kind': 'native', 'writer_address': 'standby:80', 'doas': False, 'engine_container': 'standby-engine', 'engine_config': '/opt/native-rehearsal/engine/config.json', 'storage_roots': ['/opt/native-rehearsal/app/.open-orange']}}}
        self.selected_id = 'sha256:' + 'a' * 64
        self.route = 'standby:80'
        self.lock = hashlib.sha256(b'lock').hexdigest()
        self.commands = []

    def runner(self, host, argv):
        self.commands.append((host, argv))
        if argv[:2] == ['cat', '/opt/openorange/apps.toml']:
            return '[apps.stats]\nkind = "orange"\n'
        if argv[:2] == ['/opt/openorange/bin/oo', 'deployment']:
            return json.dumps({'image': 'stats:v1', **({'recoveryWriter': self.route} if self.route else {})})
        if argv[0] == 'sha256sum':
            path = argv[1]
            value = self.lock if path.endswith('pnpm-lock.yaml') else hashlib.sha256(self.package.encode()).hexdigest() if path.endswith('package.json') else 'f' * 64
            return value + '  ' + path
        if argv[:2] == ['docker', 'ps']:
            return 'oo-engine\noo-app-stats'
        if argv[:2] == ['docker', 'inspect']:
            if argv[-1] not in ('oo-engine', 'oo-app-stats', 'standby-engine'):
                raise subprocess.CalledProcessError(1, argv)
            return self.selected_id + ' stats:v1'
        if argv[:3] == ['docker', 'image', 'inspect']:
            return '["repo@sha256:' + 'b' * 64 + '"]' if '{{json .RepoDigests}}' in argv else self.selected_id
        if argv[:2] == ['docker', 'exec']:
            return 'Rivet 3.1.1'
        if argv[:2] == ['python3', '-c']:
            code = argv[2]
            if 'package.json' in code:
                return json.dumps({'open-orange': '1.0.2', 'rivetkit': '3.1.2-rc.1'})
            if '*.node' in code:
                return json.dumps({'addon.node': 'a' * 64})
            return 'stats-123456789abc'
        raise subprocess.CalledProcessError(1, argv)

    def inspect(self):
        return oorelease.inspect(self.inventory, self.temp.name, self.runner)

    def test_consistent_and_secrets_not_read(self):
        result = self.inspect()
        self.assertEqual(result['drift'], [])
        self.assertEqual(oorelease.inspection_exit_code(result), 0)
        self.assertEqual(result['writer']['host'], 'stats-standby')
        self.assertFalse(any('.env' in str(command).lower() or 'secret' in str(command).lower() for _, command in self.commands))

    def test_selected_image_differs(self):
        self.route = None
        original = self.runner
        def runner(host, argv):
            if argv[:3] == ['docker', 'image', 'inspect'] and '{{.Id}}' in argv:
                return 'sha256:' + 'c' * 64
            return original(host, argv)
        result = oorelease.inspect(self.inventory, self.temp.name, runner)
        self.assertTrue(any('selected image differs' in x for x in result['drift']))
        self.assertEqual(oorelease.inspection_exit_code(result), 3)

    def test_lock_drift_and_unknown_route(self):
        self.lock = '0' * 64
        self.route = None
        result = self.inspect()
        self.assertIsNone(result['writer']['host'])
        self.assertTrue(any('pnpm-lock.yaml differs' in x for x in result['drift']))
        self.assertTrue(any('writer unknown' in x for x in result['drift']))


if __name__ == '__main__':
    unittest.main()
