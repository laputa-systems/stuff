import importlib.machinery
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('sources', str(ROOT / 'bin/sources'))
spec = importlib.util.spec_from_loader(loader.name, loader)
sources = importlib.util.module_from_spec(spec)
loader.exec_module(sources)


class SourceRegistryTest(unittest.TestCase):
    def setUp(self):
        self.data = sources.tomllib.loads((ROOT / 'sources/sources.toml').read_text())
        self.lock = json.loads((ROOT / 'images.lock.json').read_text())

    def test_registry_and_patch_integrity(self):
        sources.verify(self.data, self.lock)
        engine = next(item for item in self.data['components'] if item['name'] == 'rivet-engine-source')
        engine['patches'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'sha256 mismatch'):
            sources.verify(self.data, self.lock)

    def test_open_orange_patch_order_and_hash(self):
        orange = next(item for item in self.data['components'] if item['name'] == 'open-orange')
        self.assertEqual([p['file'] for p in orange['patches']], ['open-orange-1cabf2e-multi-worker-metrics.patch', 'open-orange-1cabf2e-serve-version.patch'])
        orange['patches'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'sha256 mismatch'):
            sources.verify(self.data, self.lock)

    def test_order_images_and_unknown_fields(self):
        engine = next(item for item in self.data['components'] if item['name'] == 'rivet-engine-source')
        dropped = engine['patches'].pop()
        with self.assertRaisesRegex(ValueError, 'unregistered patches'):
            sources.verify(self.data, self.lock)
        engine['patches'].append(dropped)
        self.data['components'] = [x for x in self.data['components'] if x.get('image') != 'engine']
        with self.assertRaisesRegex(ValueError, 'missing images'):
            sources.verify(self.data, self.lock)
        self.data['components'][0]['deployment'] = 'staging'
        with self.assertRaisesRegex(ValueError, 'invalid deployment'):
            sources.verify(self.data, self.lock)
        self.data['components'][0]['deployment'] = 'production'
        del self.data['components'][0]['deployment']
        with self.assertRaisesRegex(ValueError, 'missing or unknown keys'):
            sources.verify(self.data, self.lock)
        self.data['components'][0]['deployment'] = 'production'
        self.data['components'][0]['surprise'] = True
        with self.assertRaisesRegex(ValueError, 'unknown keys'):
            sources.verify(self.data, self.lock)


if __name__ == '__main__':
    unittest.main()
