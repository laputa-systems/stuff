import copy
import io
import json
import os
import runpy
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = runpy.run_path(str(ROOT / 'bin/standby-engine'))
drift, create_args, state_root_archive, CONTAINER_FACTS = TOOL['drift'], TOOL['create_args'], TOOL['state_root_archive'], TOOL['CONTAINER_FACTS']
DECLARED = json.loads((ROOT / 'standby/stats-engine.json').read_text())


def observed():
    return {
        'inspect': {
            'Image': DECLARED['image'].rsplit('@', 1)[1],
            'Config': {'Image': DECLARED['image'], 'Entrypoint': DECLARED['entrypoint'], 'Cmd': DECLARED['cmd'], 'User': DECLARED['user'], 'Env': ['RIVET__AUTH__ADMIN_TOKEN=secret', 'PATH=/usr/bin']},
            'HostConfig': {'NetworkMode': 'host', 'RestartPolicy': {'Name': 'unless-stopped'}, 'NanoCpus': 4000000000, 'Memory': 3221225472, 'MemorySwap': 6442450944},
            'Mounts': [{'Source': m['source'], 'Destination': m['target'], 'RW': not m['read_only']} for m in reversed(DECLARED['mounts'])],
            'State': {'Running': True},
        },
        'config': copy.deepcopy(DECLARED['config']),
        'listening': [22, 6420, 6430, 8080],
        'state_root': '10001:10001 700',
        'vcpus': 8,
        'namespace': 'stats-prod',
    }


class StandbyEngineDriftTest(unittest.TestCase):
    def test_matching_target_has_no_drift(self):
        self.assertEqual(drift(DECLARED, observed()), [])

    def test_each_declared_fact_is_compared(self):
        cases = {
            'nano_cpus': lambda o: o['inspect']['HostConfig'].update(NanoCpus=2000000000),
            'memory_bytes': lambda o: o['inspect']['HostConfig'].update(Memory=1 << 30),
            'image id': lambda o: o['inspect'].update(Image='sha256:' + '0' * 64),
            'env: RIVET__AUTH__ADMIN_TOKEN': lambda o: o['inspect']['Config'].update(Env=['PATH=/usr/bin']),
            'mounts': lambda o: next(m for m in o['inspect']['Mounts'] if m['Destination'] == '/etc/rivet/config.json').update(RW=True),
            'config': lambda o: o['config']['storage'].update(auto_provision_partitions=4),
            'listener': lambda o: o.update(listening=[22, 6420]),
            'namespace': lambda o: o.update(namespace='stats-staging'),
            'state root': lambda o: o.update(state_root='0:0 755'),
            'guest vcpus': lambda o: o.update(vcpus=4),
            'state': lambda o: o['inspect']['State'].update(Running=False),
        }
        for prefix, change in cases.items():
            with self.subTest(prefix):
                value = observed()
                change(value)
                found = drift(DECLARED, value)
                self.assertEqual(len(found), 1, found)
                self.assertTrue(found[0].startswith(prefix), found)

    def test_create_args_refuse_an_env_file_without_exactly_the_declared_keys(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            env = Path(directory) / 'engine.env'
            for text in ('', 'OTHER=1\n', 'RIVET__AUTH__ADMIN_TOKEN=\n', 'RIVET__AUTH__ADMIN_TOKEN=a\nOTHER=1\n'):
                env.write_text(text)
                with self.assertRaises(ValueError):
                    create_args(DECLARED, env)
            env.write_text('RIVET__AUTH__ADMIN_TOKEN=secret-value\n')
            argv = create_args(DECLARED, env)
            self.assertNotIn('secret-value', ' '.join(argv))
            self.assertEqual(argv[-3:], [DECLARED['image'], *DECLARED['cmd']])

    def test_absent_container_is_drift(self):
        self.assertEqual(drift(DECLARED, {'inspect': None}), ['container live-stats-engine is absent'])


if __name__ == '__main__':
    unittest.main()


def image_present():
    return shutil.which('docker') is not None and subprocess.run(['docker', 'image', 'inspect', DECLARED['image']], capture_output=True).returncode == 0


@unittest.skipUnless(image_present(), 'needs docker with the declared Engine image already pulled')
class CreateFromDeclarationTest(unittest.TestCase):
    def test_container_created_from_the_declaration_runs_without_drift(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            root = Path(directory)
            declared = copy.deepcopy(DECLARED)
            declared['container'] = 'standby-engine-test-' + uuid.uuid4().hex[:12]
            for mount in declared['mounts']:
                source = root / mount['source'].lstrip('/')
                if mount['target'].endswith('.json'):
                    source.parent.mkdir(parents=True, exist_ok=True)
                    source.write_text(json.dumps(declared['config']))
                else:
                    source.mkdir(parents=True)
                mount['source'] = str(source)
            env = root / 'engine.env'
            env.write_text('RIVET__AUTH__ADMIN_TOKEN=test-token\n')
            for mount in declared['mounts']:
                os.chmod(mount['source'], 0o777)
            subprocess.run(create_args(declared, env), check=True, capture_output=True)
            try:
                archive = io.BytesIO()
                state_root_archive(declared, archive)
                parent = declared['state_root']['path'].rstrip('/').rsplit('/', 1)[0]
                subprocess.run(['docker', 'cp', '-', f"{declared['container']}:{parent}"], input=archive.getvalue(), check=True, capture_output=True)
                subprocess.run(['docker', 'start', declared['container']], check=True, capture_output=True)
                time.sleep(8)
                inspect = json.loads(subprocess.run(['docker', 'inspect', declared['container']], check=True, capture_output=True, text=True).stdout)[0]
                root = subprocess.run(['docker', 'exec', declared['container'], 'stat', '-c', '%u:%g %a', declared['state_root']['path']], capture_output=True, text=True).stdout.strip()
                logs = subprocess.run(['docker', 'logs', declared['container']], capture_output=True, text=True)
                found = [line for line in drift(declared, {'inspect': inspect, 'state_root': root}) if line.startswith(CONTAINER_FACTS + ('state root',))]
                self.assertEqual(found, [], logs.stdout + logs.stderr)
                self.assertTrue(inspect['State']['Running'] and inspect['RestartCount'] == 0, logs.stdout + logs.stderr)
            finally:
                subprocess.run(['docker', 'rm', '-f', declared['container']], capture_output=True)
