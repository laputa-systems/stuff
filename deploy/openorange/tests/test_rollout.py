import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / 'deploy/openorange/bin/rollout'
sys.path.insert(0, str(ROOT / 'deploy/openorange/lib'))
import oorollout
from receipt_support import make_receipt

A = 'sha256:' + 'a' * 64
B = 'sha256:' + 'b' * 64


class RolloutTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.target = self.root / 'target'
        self.target.mkdir()
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()
        self.journals = self.root / 'journals'
        self.journals.mkdir()
        self.policy = self.root / 'policy.json'
        self.write(self.policy, {'max_age_s': 1000, 'observation_s': 0, 'check_interval_s': 0.01})
        self.write(self.target / 'state.json', {'selected': 'old', 'running': 'old', 'digest': B, 'artifacts': {'old': B, 'new': A}, 'headroom': True, 'health': True})
        self.receipt, self.evidence, self.evaluator = make_receipt(self.root, 'old', 'new', B, A)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, value):
        path.write_text(json.dumps(value))

    def command(self, *args, env=None):
        return subprocess.run([str(CLI), *map(str, args)], text=True, capture_output=True, env={**os.environ, **(env or {})})

    def start(self, env=None, artifact=A):
        return self.command('start', '--candidate', 'new', '--artifact', artifact, '--baseline', 'old', '--target-kind', 'fake', '--target', self.target, '--policy', self.policy, '--receipt', self.receipt, '--evaluator', self.evaluator, '--evidence-dir', self.evidence, '--journal-dir', self.journals, '--deadline-s', '30', '--json', env=env)

    def only_run(self):
        return next(self.journals.iterdir())

    def state(self):
        return json.loads((self.target / 'state.json').read_text())

    def test_crashes_across_transitions(self):
        for point in ('after-state-staged', 'after-intent-lock-acquire', 'after-effect-lock-acquire', 'after-state-qualified', 'after-state-prepared', 'after-intent-activate', 'after-effect-activate', 'after-done-activate', 'after-state-activated', 'after-state-verifying'):
            with self.subTest(point=point):
                self.tearDown()
                self.setUp()
                result = self.start({'ROLLOUT_CRASH': point})
                self.assertEqual(result.returncode, 137, result.stderr)
                result = self.command('resume', '--run', self.only_run())
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.state()['activations'], ['new'])

    def test_recovery_crashes(self):
        for point in ('after-state-recovering', 'after-intent-recover', 'after-effect-recover', 'after-done-recover'):
            with self.subTest(point=point):
                self.tearDown()
                self.setUp()
                state = self.state()
                state['fail_checks'] = ['new']
                self.write(self.target / 'state.json', state)
                self.assertEqual(self.start({'ROLLOUT_CRASH': point}).returncode, 137)
                result = self.command('resume', '--run', self.only_run())
                self.assertEqual(result.returncode, 3, result.stderr)
                self.assertEqual(self.state()['activations'], ['new', 'old'])
                self.assertEqual(self.state()['digest'], B)

    def test_rejected_and_operator(self):
        self.write(self.evidence / 'decision.json', {'verdict': 'reject', 'evaluatedAtMs': 1, 'reasonCodes': ['bad']})
        self.assertEqual(self.start().returncode, 3)
        self.assertNotIn('activations', self.state())
        self.tearDown()
        self.setUp()
        state = self.state()
        state['fail_checks'] = ['new', 'old']
        self.write(self.target / 'state.json', state)
        self.assertEqual(self.start().returncode, 5)
        self.assertEqual(oorollout.Journal(self.only_run()).state(), 'needs-operator')

    def test_gate_identity_and_digest(self):
        receipt = json.loads(self.receipt.read_text())
        receipt['candidate']['releaseId'] = 'wrong'
        self.write(self.receipt, receipt)
        self.assertEqual(self.start().returncode, 3)
        self.assertNotIn('activations', self.state())
        self.tearDown()
        self.setUp()
        self.assertEqual(self.start({'ROLLOUT_CRASH': 'after-state-qualified'}).returncode, 137)
        journal = oorollout.Journal(self.only_run())
        journal.records[0]['config']['artifact'] = B
        self.assertEqual(oorollout.run(journal), 'promoted')
        self.assertEqual(self.state()['digest'], A)
        self.tearDown()
        self.setUp()
        state = self.state()
        state['activated_digest'] = {'new': B}
        self.write(self.target / 'state.json', state)
        self.assertEqual(self.start().returncode, 3)
        self.assertEqual(self.state()['activations'], ['new', 'old'])
        self.assertEqual(self.state()['digest'], B)

    def reasons(self):
        return oorollout.Journal(self.only_run()).last('state')['reasons']

    def test_artifact_and_target_preconditions(self):
        for case, reason in (('artifact', 'artifact-not-qualified'), ('baseline', 'baseline-artifact-mismatch'), ('missing', 'candidate-not-staged'), ('staged', 'staged-artifact-mismatch')):
            with self.subTest(case=case):
                self.tearDown(); self.setUp()
                if case != 'artifact':
                    state = self.state()
                    if case == 'baseline': state['digest'] = A
                    elif case == 'missing': del state['artifacts']['new']
                    else: state['artifacts']['new'] = B
                    self.write(self.target / 'state.json', state)
                self.assertEqual(self.start(artifact=B if case == 'artifact' else A).returncode, 3)
                self.assertIn(reason, self.reasons())
                self.assertNotIn('activations', self.state())

    def test_staged_digest_changes_before_activation(self):
        self.assertEqual(self.start({'ROLLOUT_CRASH': 'after-state-prepared'}).returncode, 137)
        state = self.state()
        state['artifacts']['new'] = B
        self.write(self.target / 'state.json', state)
        self.assertEqual(self.command('resume', '--run', self.only_run()).returncode, 3)
        self.assertEqual(self.reasons(), ['staged-artifact-mismatch'])
        self.assertNotIn('activations', self.state())

    def test_qualified_receipt_survives_deleted_evidence(self):
        self.assertEqual(self.start({'ROLLOUT_CRASH': 'after-state-qualified'}).returncode, 137)
        shutil.rmtree(self.evidence)
        self.receipt.unlink()
        self.evaluator.unlink()
        self.assertEqual(self.command('resume', '--run', self.only_run()).returncode, 0)
        self.assertEqual(self.state()['digest'], A)

    def test_lock_race_and_fence(self):
        self.write(self.policy, {'max_age_s': 1000, 'observation_s': 2, 'check_interval_s': .05})
        args = [str(CLI), 'start', '--candidate', 'new', '--artifact', A, '--baseline', 'old', '--target-kind', 'fake', '--target', str(self.target), '--policy', str(self.policy), '--receipt', str(self.receipt), '--evaluator', str(self.evaluator), '--evidence-dir', str(self.evidence), '--journal-dir', str(self.journals), '--deadline-s', '30', '--json']
        first = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        one = first.communicate(timeout=10)
        two = second.communicate(timeout=10)
        self.assertEqual(sorted([first.returncode, second.returncode]), [0, 4], (one, two))
        adapter = oorollout.FakeAdapter(self.target)
        token = adapter.acquire('first', 'backup/fence', 0.01)
        time.sleep(.02)
        newer = adapter.acquire('second', 'engine replacement', 30)
        self.assertGreater(newer, token)
        with self.assertRaises(oorollout.StaleToken):
            adapter.activate('first', token, 'new', 'old', B)
        adapter.release('second', newer)

    def test_terminal_state_crashes(self):
        for terminal, failures, verdict, code, activations in (
            ('promoted', [], 'pass', 0, ['new']),
            ('rejected', [], 'reject', 3, []),
            ('recovered', ['new'], 'pass', 3, ['new', 'old']),
            ('needs-operator', ['new', 'old'], 'pass', 5, ['new', 'old']),
        ):
            with self.subTest(terminal=terminal):
                self.tearDown()
                self.setUp()
                state = self.state()
                state['fail_checks'] = failures
                self.write(self.target / 'state.json', state)
                make_receipt(self.root, 'old', 'new', B, A, verdict=verdict)
                self.assertEqual(self.start({'ROLLOUT_CRASH': 'after-state-' + terminal}).returncode, 137)
                result = self.command('resume', '--run', self.only_run())
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(self.state().get('activations', []), activations)

    def test_abort_and_preconditions(self):
        self.assertEqual(self.start({'ROLLOUT_CRASH': 'after-state-qualified'}).returncode, 137)
        self.assertEqual(self.command('abort', '--run', self.only_run()).returncode, 3)
        self.assertNotIn('activations', self.state())
        self.tearDown()
        self.setUp()
        self.assertEqual(self.start({'ROLLOUT_CRASH': 'after-effect-activate'}).returncode, 137)
        self.assertEqual(self.command('abort', '--run', self.only_run()).returncode, 3)
        self.assertEqual(self.state()['activations'], ['new', 'old'])
        self.tearDown()
        self.setUp()
        state = self.state()
        state['headroom'] = False
        state['headroom_detail'] = 'disk full'
        self.write(self.target / 'state.json', state)
        self.assertEqual(self.start().returncode, 3)
        self.assertNotIn('activations', self.state())

    def test_torn_line_and_watchdog(self):
        self.assertEqual(self.start({'ROLLOUT_CRASH': 'after-effect-activate'}).returncode, 137)
        path = self.only_run()
        with (path / 'journal.jsonl').open('ab') as stream:
            stream.write(b'{"seq":')
        result = self.command('status', '--run', path)
        self.assertIn('torn final line ignored', result.stdout)
        result = self.command('resume', '--run', path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.tearDown()
        self.setUp()
        self.assertEqual(self.start({'ROLLOUT_CRASH': 'after-effect-activate'}).returncode, 137)
        path = self.only_run()
        journal = oorollout.Journal(path)
        journal.append('heartbeat', deadline=0)
        result = self.command('watchdog', '--journal-dir', self.journals)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(self.state()['activations'], ['new', 'old'])


if __name__ == '__main__':
    unittest.main()
