import hashlib
import http.server
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / 'deploy/openorange/lib'
sys.path.insert(0, str(LIB))
import oomanifest
import oorollout
import oorollout_native

BTIME = 1_000_000
TICKS = os.sysconf('SC_CLK_TCK')
BIN = '/opt/native-rehearsal/orange/node_modules/open-orange/dist/bin.js'
COLLECTOR = '/opt/stats-infra-collector/main.mjs'

FAKE_RC_SERVICE = r'''#!/usr/bin/env python3
import os, sys, time
root = os.environ['ROLLOUT_GUEST_ROOT']
assert sys.argv[1:] == ['native-stats', 'restart'], sys.argv
link = os.path.join(root, 'opt/native-rehearsal/app/current')
release = os.path.basename(os.readlink(link)) if os.path.islink(link) else 'in-place'
with open(os.path.join(root, 'restarts'), 'a') as out:
    out.write(release + '\n')
start = int((time.time() + 0.5 - %d) * %d)
for pid in ('100', '200'):
    marker = os.path.join(root, 'collector-fails')
    if pid == '200' and os.path.exists(marker) and open(marker).read().strip() == release:
        continue
    with open(os.path.join(root, 'proc', pid, 'stat'), 'w') as out:
        out.write(pid + ' (node) S ' + ' '.join(['0'] * 18) + ' ' + str(start) + ' 0 0\n')
failing = open(os.path.join(root, 'fail-release')).read().strip() if os.path.exists(os.path.join(root, 'fail-release')) else ''
open(os.path.join(root, 'healthy'), 'w').write('no' if release == failing else 'yes')
''' % (BTIME, TICKS)

CONTROLLER = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import oorollout, oorollout_native
spec = json.loads(sys.argv[2])
def runner(payload):
    import subprocess
    result = subprocess.run([sys.executable, '-c', oorollout_native.GUEST_SCRIPT], input=payload, capture_output=True, text=True, env=spec['env'])
    if result.returncode != 0:
        raise OSError(result.stderr)
    return result.stdout
adapter = oorollout_native.NativeAdapter(runner, 'app', health_url=spec['health_url'], health_deadline_s=5, min_free_bytes=1, bound_s=10)
journal = oorollout.Journal(spec['journal'])
if not journal.records:
    journal.append('start', config=spec['config'])
    journal.transition('staged', 60)
print(json.dumps({'state': oorollout.run(journal, adapter=adapter, recovery=spec.get('recovery', False))}))
'''


class Health(http.server.BaseHTTPRequestHandler):
    root = None

    def do_GET(self):
        healthy = (self.root / 'healthy').read_text().strip() == 'yes'
        body = json.dumps({'ok': healthy, 'service': 'stats'}).encode()
        self.send_response(200)
        self.send_header('content-length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def write_app(directory, version):
    (directory / 'stats/bundle').mkdir(parents=True)
    (directory / 'stats/assets').mkdir(parents=True)
    (directory / 'observe/bundle').mkdir(parents=True)
    (directory / 'stats/bundle/index.js').write_text('stats ' + version)
    (directory / 'stats/assets/index.html').write_text('<html>' + version)
    (directory / 'observe/bundle/index.js').write_text('observe ' + version)
    (directory / 'stats.jsonc').write_text(json.dumps({'vars': {'APPLICATION_EVENTS_RELEASE': 'stats-' + version}}))
    (directory / 'observe.jsonc').write_text('{"name":"stats-observe"}')


def write_collector(directory, version):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'main.mjs').write_text('collector ' + version)
    (directory / 'manifest.json').write_text('{}')


def write_stat(path, started_at):
    path.write_text(path.parent.name + ' (node) S ' + ' '.join(['0'] * 18) + f' {int((started_at - BTIME) * TICKS)} 0 0\n')


class NativeAppTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.base = Path(self.tmp.name)
        self.guest = self.base / 'guest'
        runtime = self.guest / 'opt/native-rehearsal/orange'
        (runtime / 'node_modules/open-orange/dist').mkdir(parents=True)
        (runtime / 'package.json').write_text('{}')
        (runtime / 'node_modules/open-orange/dist/bin.js').write_text('bin')
        app = self.guest / 'opt/native-rehearsal/app'
        write_app(app, 'aaaaaaaaaaaa')
        (app / '.open-orange/rivetkit/identity').mkdir(parents=True)
        (app / '.open-orange/rivetkit/identity/deployment-identity').write_text('identity')
        write_collector(self.guest / 'opt/stats-infra-collector', 'old')
        for pid, script in (('100', [b'/usr/bin/node', BIN.encode(), b'serve']), ('200', [b'/usr/bin/node', COLLECTOR.encode()])):
            (self.guest / 'proc' / pid).mkdir(parents=True)
            (self.guest / 'proc' / pid / 'cmdline').write_bytes(b'\0'.join(script) + b'\0')
            write_stat(self.guest / 'proc' / pid / 'stat', time.time() - 3600)
        (self.guest / 'proc/stat').write_text(f'cpu 0\nbtime {BTIME}\n')
        (self.guest / 'healthy').write_text('yes')
        fake_bin = self.base / 'bin'
        fake_bin.mkdir()
        (fake_bin / 'rc-service').write_text(FAKE_RC_SERVICE)
        (fake_bin / 'docker').write_text('#!/bin/sh\necho true\n')
        for name in ('rc-service', 'docker'):
            (fake_bin / name).chmod(0o755)
        handler = type('H', (Health,), {'root': self.guest})
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.health_url = f'http://127.0.0.1:{self.server.server_address[1]}/health'
        self.env = {**os.environ, 'ROLLOUT_GUEST_ROOT': str(self.guest), 'PATH': f'{fake_bin}:{os.environ["PATH"]}'}
        self.adapter = oorollout_native.NativeAdapter(self.local_runner, 'app', health_url=self.health_url, health_deadline_s=5, min_free_bytes=1, bound_s=10)
        initial = self.adapter.observe()
        self.baseline, self.baseline_digest = initial['selected'], initial['digest']
        self.runtime_digest = initial['components']['runtime']
        self.authority = self.base / 'authority.json'
        self.authority.write_text(json.dumps({'stats': {'mode': 'writer', 'upstream': '127.0.0.1:18489'}}))
        self.journals = self.base / 'journals'
        self.journals.mkdir()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def local_runner(self, payload):
        result = subprocess.run([sys.executable, '-c', oorollout_native.GUEST_SCRIPT], input=payload, capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def stage(self, version):
        source = self.base / ('build-' + version)
        write_app(source, version)
        write_collector(source / 'collector', version)
        parts = oomanifest.app_release_parts(source)
        incoming = self.guest / 'var/lib/openorange-rollout' / ('incoming-' + version + '.tar')
        incoming.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(incoming, 'w', format=tarfile.PAX_FORMAT, pax_headers={'openorange.manifest_digest': oomanifest.manifest_digest(oomanifest.app_manifest(parts))}) as out:
            for name, path in parts.items():
                out.add(path, arcname=name)
        token = self.adapter.acquire('stager', 'stage', 60)
        try:
            return self.adapter.stage('stager', token, '/var/lib/openorange-rollout/' + incoming.name, 'test ' + version)
        finally:
            self.adapter.release('stager', token)

    def admission(self, name, candidate, exit_code=0, baseline=None, runtime=None):
        root = self.base / ('admission-' + name)
        evidence = root / 'evidence'
        if (root / 'receipt.json').exists():
            return root / 'receipt.json', evidence
        evidence.mkdir(parents=True)
        (evidence / 'build.log').write_text('built')
        sha = lambda data: hashlib.sha256(data).hexdigest()
        now = int(time.time() * 1000)
        baseline = baseline or (self.baseline, self.baseline_digest)
        receipt = {'schema': 'stats-app-admission/1',
                   'baseline': {'releaseId': baseline[0], 'artifactDigest': baseline[1]},
                   'candidate': {'releaseId': candidate['release'], 'artifactDigest': candidate['digest'], 'components': {'runtime': runtime or self.runtime_digest}},
                   'source': {'repository': 'stats', 'commit': 'c' * 40},
                   'checks': [{'name': 'build', 'argv': ['make', 'build'], 'exitCode': exit_code, 'log': 'build.log'}],
                   'inputs': [{'path': 'build.log', 'sha256': sha(b'built'), 'bytes': 5}],
                   'decision': {'verdict': 'admitted' if exit_code == 0 else 'refused', 'reasonCodes': [], 'evaluatedAtMs': now},
                   'createdAtMs': now}
        (root / 'receipt.json').write_text(json.dumps(receipt))
        return root / 'receipt.json', evidence

    def controller(self, name, candidate, baseline=None, crash=None, recovery=False, admission=None, policy=None):
        receipt, evidence = admission or self.admission(name, candidate)
        journal = self.journals / name
        journal.mkdir(exist_ok=True)
        read_authority = 'import json, sys; print(json.dumps({"ok": True, "authority": json.load(open(sys.argv[1]))}))'
        config = {'target_kind': 'native-app', 'host': 'simulated', 'ssh_config': 'unused', 'run_id': str(journal), 'candidate': candidate['release'], 'artifact': candidate['digest'], 'baseline': baseline or self.baseline,
                  'policy': {'functional_check': {'argv': [sys.executable, '-c', 'import json; print(json.dumps(dict(ok=True)))'], 'timeout_s': 5},
                             'authority_check': {'argv': [sys.executable, '-c', read_authority, str(self.authority)], 'timeout_s': 5},
                             'max_age_s': 600, 'observation_s': 0, 'check_interval_s': 0.01, **(policy or {})},
                  'rollout_policy_sha256': '0' * 64, 'receipt': str(receipt), 'evaluator': None, 'evidence_dir': str(evidence), 'bound_s': 10, 'deadline_s': 60}
        spec = {'env': self.env, 'health_url': self.health_url, 'journal': str(journal), 'config': config, 'recovery': recovery}
        env = {**os.environ, **({'ROLLOUT_CRASH': crash} if crash else {})}
        result = subprocess.run([sys.executable, '-c', CONTROLLER, str(LIB), json.dumps(spec)], capture_output=True, text=True, env=env)
        if crash:
            self.assertEqual(result.returncode, 137, result.stdout + result.stderr)
            return None
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout.splitlines()[-1])['state']

    def journal_text(self, name):
        return (self.journals / name / 'journal.jsonl').read_text()

    def restarts(self):
        path = self.guest / 'restarts'
        return path.read_text().split() if path.exists() else []

    def identity(self):
        state = self.adapter.observe()
        return state['selected'], state['running'], state['collector_running'], state['digest']

    def test_conversion_preserves_the_app_digest_state_directory_and_collector(self):
        token = self.adapter.acquire('operator', 'deployment', 60)
        self.adapter.prepare_step('operator', token, 'convert-app')
        self.adapter.release('operator', token)
        state = self.adapter.observe()
        self.assertTrue(state['converted'])
        self.assertEqual((state['selected'], state['digest'], state['running']), (self.baseline, self.baseline_digest, self.baseline))
        app = self.guest / 'opt/native-rehearsal/app'
        self.assertEqual(os.readlink(app / 'stats.jsonc'), 'current/stats.jsonc')
        self.assertTrue((app / '.open-orange/rivetkit/identity/deployment-identity').is_file())
        self.assertFalse((app / '.open-orange').is_symlink())
        self.assertEqual((self.guest / 'opt/stats-infra-collector/main.mjs').read_text(), 'collector old')
        self.assertTrue((self.guest / 'opt/stats-infra-collector').is_symlink())
        self.assertEqual(list(app.glob('.converted-*')), [])
        self.assertEqual(self.restarts(), [])

    def test_app_promotion_reuses_the_runtime_and_survives_each_crash(self):
        for point in (None, 'after-intent-convert-app', 'after-effect-convert-app', 'after-done-convert-app', 'after-intent-activate', 'after-effect-activate', 'after-done-activate', 'after-state-verifying'):
            with self.subTest(point=point):
                self.tearDown()
                self.setUp()
                candidate = self.stage('bbbbbbbbbbbb')
                runtime_before = (self.guest / 'opt/native-rehearsal/orange/node_modules/open-orange/dist/bin.js').stat().st_mtime_ns
                if point:
                    self.controller('run', candidate, crash=point)
                self.assertEqual(self.controller('run', candidate), 'promoted', self.journal_text('run'))
                self.assertEqual(self.identity(), (candidate['release'], candidate['release'], candidate['release'], candidate['digest']))
                self.assertEqual(self.restarts(), [candidate['release']])
                self.assertEqual((self.guest / 'opt/stats-infra-collector/main.mjs').read_text(), 'collector bbbbbbbbbbbb')
                self.assertEqual((self.guest / 'opt/native-rehearsal/orange/node_modules/open-orange/dist/bin.js').stat().st_mtime_ns, runtime_before)

    def test_refused_lease_changes_nothing(self):
        candidate = self.stage('bbbbbbbbbbbb')
        token = self.adapter.acquire('other-operation', 'backup-fence', 60)
        receipt, evidence = self.admission('held', candidate)
        journal = self.journals / 'held'
        journal.mkdir()
        spec = {'env': self.env, 'health_url': self.health_url, 'journal': str(journal), 'config': {'target_kind': 'native-app', 'run_id': str(journal), 'candidate': candidate['release'], 'artifact': candidate['digest'], 'baseline': self.baseline, 'policy': {'functional_check': {'argv': ['true'], 'timeout_s': 5}, 'max_age_s': 600, 'observation_s': 0, 'check_interval_s': 1}, 'rollout_policy_sha256': '0' * 64, 'receipt': str(receipt), 'evaluator': None, 'evidence_dir': str(evidence), 'bound_s': 10, 'deadline_s': 60}}
        result = subprocess.run([sys.executable, '-c', CONTROLLER, str(LIB), json.dumps(spec)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('LockHeld', result.stderr)
        self.adapter.release('other-operation', token)
        state = self.adapter.observe()
        self.assertFalse(state['converted'])
        self.assertEqual(self.identity(), (self.baseline, self.baseline, self.baseline, self.baseline_digest))
        self.assertEqual(self.restarts(), [])

    def test_a_stale_deployment_cannot_roll_back_a_later_one(self):
        first = self.stage('bbbbbbbbbbbb')
        second = self.stage('cccccccccccc')
        self.controller('a', first, crash='after-state-verifying')
        self.assertEqual(self.identity()[0], first['release'])
        lock = self.guest / 'var/lib/openorange-rollout/lock.json'
        record = json.loads(lock.read_text())
        record['lease_expiry'] = 0
        lock.write_text(json.dumps(record))
        self.assertEqual(self.controller('b', second, baseline=first['release'], admission=self.admission('b', second, baseline=(first['release'], first['digest']))), 'promoted', self.journal_text('b'))
        self.assertEqual(self.controller('a', first, recovery=True), 'needs-operator', self.journal_text('a'))
        self.assertEqual(self.identity(), (second['release'], second['release'], second['release'], second['digest']))
        self.assertEqual(self.restarts(), [first['release'], second['release']])

    def test_writer_authority_change_after_prepare_prevents_activation(self):
        candidate = self.stage('bbbbbbbbbbbb')
        self.controller('run', candidate, crash='after-done-convert-app')
        self.authority.write_text(json.dumps({'stats': {'mode': 'fenced', 'upstream': '127.0.0.1:18489'}}))
        self.assertEqual(self.controller('run', candidate), 'rejected')
        self.assertIn('writer-authority-changed', self.journal_text('run'))
        self.assertEqual(self.identity(), (self.baseline, self.baseline, self.baseline, self.baseline_digest))
        self.assertEqual(self.restarts(), [])

    def test_refused_writer_authority_rejects_before_preparation(self):
        candidate = self.stage('bbbbbbbbbbbb')
        self.authority.write_text('not json')
        self.assertEqual(self.controller('run', candidate), 'rejected')
        self.assertIn('writer authority unavailable', self.journal_text('run'))
        self.assertFalse(self.adapter.observe()['converted'])

    def test_changed_runtime_or_app_bytes_are_refused(self):
        candidate = self.stage('bbbbbbbbbbbb')
        self.assertEqual(self.controller('runtime', candidate, admission=self.admission('runtime', candidate, runtime='sha256:' + 'f' * 64)), 'rejected')
        self.assertIn('component-mismatch:runtime', self.journal_text('runtime'))
        (self.guest / 'opt/native-rehearsal/apps' / candidate['release'] / 'stats/bundle/index.js').write_text('tampered')
        self.assertEqual(self.controller('bytes', candidate), 'recovered', self.journal_text('bytes'))
        self.assertIn('staged-content-mismatch', self.journal_text('bytes'))
        self.assertEqual(self.identity(), (self.baseline, self.baseline, self.baseline, self.baseline_digest))
        self.assertEqual(self.restarts(), [])

    def test_admission_with_altered_evidence_is_rejected(self):
        candidate = self.stage('bbbbbbbbbbbb')
        receipt, evidence = self.admission('altered', candidate)
        (evidence / 'build.log').write_text('BUILT')
        self.assertEqual(self.controller('run', candidate, admission=(receipt, evidence)), 'rejected')
        self.assertIn('invalid-evidence', self.journal_text('run'))
        self.assertFalse(self.adapter.observe()['converted'])

    def test_failed_admission_check_is_rejected(self):
        candidate = self.stage('bbbbbbbbbbbb')
        self.assertEqual(self.controller('run', candidate, admission=self.admission('failed', candidate, exit_code=2)), 'rejected')
        self.assertIn('check-failed:build', self.journal_text('run'))

    def test_candidate_whose_collector_does_not_start_recovers_the_previous_app(self):
        candidate = self.stage('bbbbbbbbbbbb')
        (self.guest / 'collector-fails').write_text(candidate['release'])
        self.assertEqual(self.controller('run', candidate), 'recovered', self.journal_text('run'))
        self.assertIn('collector did not become healthy', self.journal_text('run'))
        self.assertEqual(self.identity(), (self.baseline, self.baseline, self.baseline, self.baseline_digest))
        self.assertEqual(self.restarts(), [candidate['release'], self.baseline])

    def scripted_functional_check(self, release, outcomes):
        """Functional check whose Nth call for release passes when outcomes[N] is 'T'; later calls repeat the last outcome."""
        counter = self.base / ('functional-' + release)
        script = ('import json, os, sys\n'
                  'release, counter, outcomes = sys.argv[1], sys.argv[2], sys.argv[3]\n'
                  'n = int(open(counter).read()) if os.path.exists(counter) else 0\n'
                  'ok = os.environ["ROLLOUT_RELEASE"] != release or outcomes[min(n, len(outcomes) - 1)] == "T"\n'
                  'if os.environ["ROLLOUT_RELEASE"] == release: open(counter, "w").write(str(n + 1))\n'
                  'print(json.dumps({"ok": ok})); sys.exit(0 if ok else 1)\n')
        return {'argv': [sys.executable, '-c', script, release, str(counter), outcomes], 'timeout_s': 5}

    def slow_functional_check(self, release, failures):
        return self.scripted_functional_check(release, 'F' * failures + 'T')

    def checks(self, name):
        return [json.loads(line) for line in self.journal_text(name).splitlines() if json.loads(line)['kind'] == 'check']

    def test_candidate_that_becomes_ready_within_ready_s_is_promoted(self):
        candidate = self.stage('bbbbbbbbbbbb')
        policy = {'ready_s': 30, 'functional_check': self.slow_functional_check(candidate['release'], 2)}
        self.assertEqual(self.controller('run', candidate, policy=policy), 'promoted', self.journal_text('run'))
        self.assertEqual([(c['phase'], c['ok']) for c in self.checks('run')], [('readiness', False), ('readiness', False), ('readiness', True)])
        self.assertIn('ready_after_s', self.journal_text('run'))

    def test_candidate_not_ready_within_ready_s_recovers(self):
        candidate = self.stage('bbbbbbbbbbbb')
        policy = {'ready_s': 1, 'functional_check': self.slow_functional_check(candidate['release'], 100)}
        self.assertEqual(self.controller('run', candidate, policy=policy), 'recovered', self.journal_text('run'))
        self.assertIn('not functionally ready within 1s', self.journal_text('run'))
        self.assertEqual(self.identity(), (self.baseline, self.baseline, self.baseline, self.baseline_digest))

    def test_failure_after_readiness_recovers_without_waiting(self):
        candidate = self.stage('bbbbbbbbbbbb')
        policy = {'ready_s': 60, 'observation_s': 2, 'check_interval_s': 0.2, 'functional_check': self.scripted_functional_check(candidate['release'], 'TF')}
        started = time.time()
        self.assertEqual(self.controller('run', candidate, policy=policy), 'recovered', self.journal_text('run'))
        self.assertLess(time.time() - started, 30)
        self.assertIn('post-activation check failed', self.journal_text('run'))
        self.assertEqual([(c['phase'], c['ok']) for c in self.checks('run')][:2], [('readiness', True), ('verification', False)])

    def test_recovery_waits_ready_s_for_the_baseline(self):
        for ready_s, outcome in ((30, 'recovered'), (0, 'needs-operator')):
            with self.subTest(ready_s=ready_s):
                self.tearDown()
                self.setUp()
                candidate = self.stage('bbbbbbbbbbbb')
                (self.guest / 'fail-release').write_text(candidate['release'])
                policy = {'ready_s': ready_s, 'functional_check': self.slow_functional_check(self.baseline, 2)}
                self.assertEqual(self.controller('run', candidate, policy=policy), outcome, self.journal_text('run'))
                self.assertEqual(self.adapter.observe()['selected'], self.baseline)

    def test_unhealthy_candidate_recovers_to_the_baseline(self):
        candidate = self.stage('bbbbbbbbbbbb')
        (self.guest / 'fail-release').write_text(candidate['release'])
        self.assertEqual(self.controller('run', candidate), 'recovered', self.journal_text('run'))
        self.assertEqual(self.identity(), (self.baseline, self.baseline, self.baseline, self.baseline_digest))
        self.assertEqual(self.restarts(), [candidate['release'], self.baseline])


if __name__ == '__main__':
    unittest.main()
