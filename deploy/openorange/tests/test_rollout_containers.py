import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / 'deploy/openorange/lib'
sys.path.insert(0, str(LIB))
import oorollout
import oorollout_containers

BASE = 'app:base'
CANDIDATE = 'app:new'
IDS = {BASE: 'sha256:' + 'a' * 64, CANDIDATE: 'sha256:' + 'b' * 64}

FAKE = r'''#!/usr/bin/env python3
import json, os, signal, sys, urllib.request
from pathlib import Path
root = Path(os.environ['ROLLOUT_GUEST_ROOT'])
state_path = root / 'state.json'
s = json.loads(state_path.read_text())
a = sys.argv[1:]
name = Path(sys.argv[0]).name
def crash(point):
    if os.environ.get('GUEST_CRASH') == point and not (root / 'crashed').exists():
        (root / 'crashed').touch()
        os.kill(int(os.environ['ENGINE_PID']), signal.SIGKILL)
        os.kill(os.getppid(), signal.SIGKILL)
with (root / 'commands').open('a') as f: f.write(json.dumps([name, *a]) + '\n')
if name == 'oo':
    if a[0] == 'deployment': print(json.dumps({k:s[k] for k in ('image', 'version', 'recoveryWriter') if k in s}))
    elif a[0] == 'set-image':
        assert a[2] in s['ids'] and a[3:] == ['--if-current', s['image']]
        if a[2] != s['image']: s['image'] = a[2]; s['version'] += 1
        state_path.write_text(json.dumps(s))
        crash('selection')
    elif a[0] == 'wait':
        try:
            with urllib.request.urlopen(os.environ['HEALTH_URL']) as response:
                if response.status != 200: sys.exit(1)
        except Exception: sys.exit(1)
    elif a[0] == 'record-deployment':
        assert a[1:] == ['app', '--if-current', s['image']]
        if (root / 'fail-marker').exists(): sys.exit(1)
        marker = root / ('var/lib/openorange/deployments/app/delivered/oo-app-%s.json' % s['version'])
        marker.parent.mkdir(parents=True, exist_ok=True); marker.write_text('{}')
        crash('marker')
    else: raise AssertionError(a)
elif name == 'docker':
    if a[:2] == ['image', 'ls']: print('\n'.join(s['ids']))
    elif a[:2] == ['image', 'inspect']: print(s['ids'][a[-1]])
    elif a[0] == 'inspect': print(s['running'], s['ids'][s['running']], 'true')
    elif a[0] == 'exec': print(s['running_version'])
    else: raise AssertionError(a)
elif name == 'rc-service':
    assert a == ['oo-app.app', 'restart']
    s['running'] = s['image']; s['running_version'] = s['version']
    state_path.write_text(json.dumps(s))
    crash('restart')
else: raise AssertionError(name)
'''

ENGINE = r'''
import json, os, subprocess, sys
sys.path.insert(0, sys.argv[1])
import oorollout, oorollout_containers
spec = json.loads(sys.argv[2])
spec['env']['ENGINE_PID'] = str(os.getpid())
def runner(payload):
    p = subprocess.run([sys.executable, '-c', oorollout_containers.GUEST_SCRIPT], input=payload, text=True, capture_output=True, env=spec['env'])
    if p.returncode: raise OSError(p.stderr)
    return p.stdout
adapter = oorollout_containers.ContainersAdapter(runner, 'app', min_free_bytes=1, health_deadline_s=2)
journal = oorollout.Journal(spec['journal'])
if not journal.records:
    journal.append('start', config=spec['config'])
    journal.transition('staged', 60)
print(json.dumps({'state': oorollout.run(journal, adapter=adapter, recovery=spec['recovery'])}))
'''


class Health(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200 if self.server.healthy else 503)
        self.end_headers()
    def log_message(self, *args):
        pass


class ContainersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.root = Path(self.tmp.name) / 'guest'
        self.root.mkdir()
        self.state = {'image': BASE, 'version': 1, 'running': BASE, 'running_version': 1, 'ids': IDS}
        self.save()
        for name in ('opt/openorange/bin/oo', 'sbin/rc-service', 'bin/docker'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(FAKE)
            path.chmod(0o755)
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Health)
        self.server.healthy = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.env = {**os.environ, 'ROLLOUT_GUEST_ROOT': str(self.root), 'PATH': str(self.root / 'bin') + ':' + os.environ['PATH'], 'HEALTH_URL': f'http://127.0.0.1:{self.server.server_address[1]}/health'}
        self.adapter = oorollout_containers.ContainersAdapter(self.runner, 'app', min_free_bytes=1, health_deadline_s=2)
        self.evidence = Path(self.tmp.name) / 'evidence'
        self.evidence.mkdir()
        self.journal = Path(self.tmp.name) / 'journal'
        self.journal.mkdir()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def save(self):
        (self.root / 'state.json').write_text(json.dumps(self.state))

    def runner(self, payload):
        p = subprocess.run([sys.executable, '-c', oorollout_containers.GUEST_SCRIPT], input=payload, text=True, capture_output=True, env=self.env)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def engine(self, crash=None, recovery=False, guest_crash=None):
        for name, value in (('decision.json', {'verdict': 'pass', 'evaluatedAtMs': int(time.time() * 1000), 'reasonCodes': []}), ('candidate.manifest.json', {'releaseId': CANDIDATE}), ('baseline.manifest.json', {'releaseId': BASE})):
            (self.evidence / name).write_text(json.dumps(value))
        config = {'target_kind': 'oo-containers', 'host': 'simulated', 'app': 'app', 'ssh_config': 'unused', 'run_id': str(self.journal), 'candidate': CANDIDATE, 'artifact': IDS[CANDIDATE], 'baseline': BASE, 'policy': {'max_age_s': 600, 'observation_s': 0, 'check_interval_s': .01}, 'evidence_dir': str(self.evidence), 'deadline_s': 60}
        spec = {'env': {**self.env, **({'GUEST_CRASH': guest_crash} if guest_crash else {})}, 'journal': str(self.journal), 'config': config, 'recovery': recovery}
        env = {**os.environ, **({'ROLLOUT_CRASH': crash} if crash else {})}
        return subprocess.run([sys.executable, '-c', ENGINE, str(LIB), json.dumps(spec)], text=True, capture_output=True, env=env)

    def commands(self, name):
        p = self.root / 'commands'
        return [v for v in map(json.loads, p.read_text().splitlines()) if v[0] == name] if p.exists() else []

    def test_activation_and_resume_at_engine_boundaries(self):
        for point in (None, 'after-intent-activate', 'after-effect-activate', 'after-done-activate', 'after-state-verifying'):
            with self.subTest(point=point):
                self.tearDown(); self.setUp()
                if point: self.assertEqual(self.engine(point).returncode, 137)
                result = self.engine()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['state'], 'promoted')
                self.assertEqual([x[2:4] for x in self.commands('oo') if x[1] == 'set-image'], [['app', CANDIDATE]])
                self.assertEqual(len(self.commands('rc-service')), 1)
                self.assertEqual(len([x for x in self.commands('oo') if x[1] == 'record-deployment']), 1)
                self.assertTrue(self.adapter.observe()['identity_valid'])

    def test_crash_after_each_guest_effect_resumes(self):
        for effect in ('selection', 'restart', 'marker'):
            with self.subTest(effect=effect):
                self.tearDown(); self.setUp()
                self.assertNotEqual(self.engine(guest_crash=effect).returncode, 0)
                result = self.engine()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['state'], 'promoted')
                self.assertEqual(len([x for x in self.commands('oo') if x[1] == 'set-image']), 1)
                self.assertEqual(len(self.commands('rc-service')), 1)
                self.assertEqual(len([x for x in self.commands('oo') if x[1] == 'record-deployment']), 1)

    def test_partial_selection_completes_and_records(self):
        self.assertEqual(self.engine('after-intent-activate').returncode, 137)
        self.state.update(image=CANDIDATE, version=2); self.save()
        self.assertEqual(self.adapter.classify(self.adapter.observe(), BASE, CANDIDATE, IDS[CANDIDATE]), 'partial')
        result = self.engine()
        self.assertEqual(json.loads(result.stdout)['state'], 'promoted', result.stderr)
        self.assertEqual(len(self.commands('rc-service')), 1)
        self.assertEqual(len([x for x in self.commands('oo') if x[1] == 'record-deployment']), 1)

    def test_resume_after_restart_before_marker(self):
        self.assertEqual(self.engine('after-intent-activate').returncode, 137)
        self.state.update(image=CANDIDATE, version=2, running=CANDIDATE, running_version=2); self.save()
        result = self.engine()
        self.assertEqual(json.loads(result.stdout)['state'], 'promoted', result.stderr)
        self.assertEqual(self.commands('rc-service'), [])
        self.assertEqual(len([x for x in self.commands('oo') if x[1] == 'record-deployment']), 1)

    def test_failed_marker_preserves_healthy_activation_for_retry(self):
        marker_failure = self.root / 'fail-marker'
        marker_failure.touch()
        failed = self.engine()
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(self.adapter.observe()['selected'], CANDIDATE)
        self.assertEqual(len(self.commands('rc-service')), 1)
        marker_failure.unlink()
        result = self.engine()
        self.assertEqual(json.loads(result.stdout)['state'], 'promoted', result.stderr)
        self.assertEqual(len(self.commands('rc-service')), 1)

    def test_recovery_and_resume(self):
        for point in ('after-intent-recover', 'after-effect-recover', 'after-done-recover'):
            with self.subTest(point=point):
                self.tearDown(); self.setUp()
                self.assertEqual(self.engine('after-state-activated').returncode, 137)
                self.assertEqual(self.engine(point, recovery=True).returncode, 137)
                result = self.engine(recovery=True)
                self.assertEqual(json.loads(result.stdout)['state'], 'recovered', result.stderr)
                state = self.adapter.observe()
                self.assertEqual((state['selected'], state['running'], state['version']), (BASE, BASE, 3))
                self.assertEqual(len([x for x in self.commands('oo') if x[1] == 'record-deployment']), 2)

    def test_stale_fence_and_conditional_selection(self):
        token = self.adapter.acquire('first', 'deployment', 60)
        with self.assertRaises(oorollout.StaleToken): self.adapter.activate('first', token + 1, BASE, CANDIDATE, IDS[CANDIDATE])
        with self.assertRaises(ValueError): self.adapter.activate('first', token, 'app:other', CANDIDATE, IDS[CANDIDATE])
        self.adapter.release('first', token)
        self.assertFalse(any(x[1] == 'set-image' for x in self.commands('oo')))

    def test_fenced_writer_and_unknown_running_identity_need_operator(self):
        for change in ({'recoveryWriter': 'standby:8080'}, {'running_version': 99}):
            with self.subTest(change=change):
                self.tearDown(); self.setUp()
                self.assertEqual(self.engine('after-state-prepared').returncode, 137)
                self.state.update(change); self.save()
                result = self.engine()
                self.assertEqual(json.loads(result.stdout)['state'], 'needs-operator', result.stderr)
                self.assertFalse(any(x[1] == 'set-image' for x in self.commands('oo')))


if __name__ == '__main__':
    unittest.main()
