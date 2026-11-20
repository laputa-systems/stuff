import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
import ooreceipt
from receipt_support import make_receipt


class ReceiptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.paths = make_receipt(self.root, 'old', 'new', 'sha256:' + 'a' * 64, 'sha256:' + 'b' * 64)

    def tearDown(self):
        self.tmp.cleanup()

    def verify(self):
        return ooreceipt.verify(*self.paths)

    def test_fixture_matches_the_stats_receipt_writer_shape(self):
        def shape(value):
            if isinstance(value, dict):
                return {key: shape(item) for key, item in value.items() if key != 'components'}
            if isinstance(value, list):
                return [shape(value[0])] if value else []
            return type(value).__name__
        real = json.loads((Path(__file__).parent / 'fixtures/stats-receipt-promotion.json').read_text())
        self.assertEqual(shape(json.loads(self.paths[0].read_text())), shape(real))

    def test_missing_or_unknown_schema_rejects(self):
        for value in (None, 'stats-qualification-receipt/2'):
            with self.subTest(schema=value):
                receipt = json.loads(self.paths[0].read_text())
                if value is None: del receipt['schema']
                else: receipt['schema'] = value
                self.paths[0].write_text(json.dumps(receipt))
                self.assertEqual(self.verify(), (None, ['invalid-evidence']))

    def test_evidence_mutations_reject(self):
        for name in ('policy.json', 'workload.json', 'ledger.json', 'missing', 'extra', 'symlink'):
            with self.subTest(name=name):
                self.tearDown(); self.setUp()
                evidence = self.paths[1]
                if name == 'missing': (evidence / 'ledger.json').unlink()
                elif name == 'extra': (evidence / 'extra').write_text('extra')
                elif name == 'symlink': (evidence / 'link').symlink_to(evidence / 'policy.json')
                else: (evidence / name).write_text('changed')
                self.assertEqual(self.verify()[1], ['invalid-evidence'])

    def test_evaluator_and_profile_reject(self):
        self.paths[2].write_text('changed')
        self.assertEqual(self.verify()[1], ['evaluator-mismatch'])
        self.paths = make_receipt(self.root, 'old', 'new', 'sha256:' + 'a' * 64, 'sha256:' + 'b' * 64, replay_exit=4)
        self.assertEqual(self.verify()[1], ['replay-mismatch'])
        self.paths = make_receipt(self.root, 'old', 'new', 'sha256:' + 'a' * 64, 'sha256:' + 'b' * 64, profile='smoke')
        self.assertEqual(self.verify()[1], ['profile-not-promotion'])

    def test_schema_rejects_unknown_and_invalid_paths(self):
        for change in ('unknown', 'path'):
            with self.subTest(change=change):
                self.tearDown(); self.setUp()
                receipt = json.loads(self.paths[0].read_text())
                if change == 'unknown': receipt['unknown'] = 1
                else: receipt['inputs'][0]['path'] = '../escape'
                self.paths[0].write_text(json.dumps(receipt))
                self.assertEqual(self.verify()[1], ['invalid-evidence'])
