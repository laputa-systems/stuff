import copy
import json
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
drift = runpy.run_path(str(ROOT / 'bin/standby-engine'))['drift']
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

    def test_absent_container_is_drift(self):
        self.assertEqual(drift(DECLARED, {'inspect': None}), ['container live-stats-engine is absent'])


if __name__ == '__main__':
    unittest.main()
