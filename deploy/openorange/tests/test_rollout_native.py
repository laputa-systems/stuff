import http.server
import io
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
import oorollout
import oorollout_native

BTIME = 1_000_000
TICKS = os.sysconf('SC_CLK_TCK')
BIN = '/opt/native-rehearsal/orange/node_modules/open-orange/dist/bin.js'

FAKE_RC_SERVICE = r'''#!/usr/bin/env python3
import json, os, sys, time
root = os.environ['ROLLOUT_GUEST_ROOT']
assert sys.argv[1:] == ['native-stats', 'restart'], sys.argv
link = os.path.join(root, 'opt/native-rehearsal/orange')
release = os.path.basename(os.readlink(link)) if os.path.islink(link) else 'in-place'
with open(os.path.join(root, 'restarts'), 'a') as out:
    out.write(release + '\n')
start = int((time.time() + 0.5 - %d) * %d)
with open(os.path.join(root, 'proc/100/stat'), 'w') as out:
    out.write('100 (node) S ' + ' '.join(['0'] * 18) + ' ' + str(start) + ' 0 0\n')
failing = open(os.path.join(root, 'fail-release')).read().strip() if os.path.exists(os.path.join(root, 'fail-release')) else ''
open(os.path.join(root, 'healthy'), 'w').write('no' if release == failing else 'yes')
''' % (BTIME, TICKS)

ENGINE_CHILD = r'''
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
adapter = oorollout_native.NativeAdapter(runner, health_url=spec['health_url'], health_deadline_s=5, min_free_bytes=1)
journal = oorollout.Journal(spec['journal'])
if not journal.records:
    journal.append('start', config=spec['config'])
    journal.transition('staged', 60)
print(json.dumps({'state': oorollout.run(journal, adapter=adapter)}))
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


def write_closure(directory, bin_text):
    modules = directory / 'node_modules'
    (modules / 'open-orange/dist').mkdir(parents=True)
    (modules / 'rivetkit').mkdir(parents=True)
    addon = modules / '.pnpm/@rivetkit+rivetkit-napi-linux-x64-musl@3.1.2-rc.1/node_modules/@rivetkit/rivetkit-napi-linux-x64-musl'
    addon.mkdir(parents=True)
    (directory / 'package.json').write_text('{"dependencies":{}}')
    (directory / 'pnpm-lock.yaml').write_text('lock')
    (modules / 'open-orange/package.json').write_text(json.dumps({'version': '1.0.2' if bin_text == 'upstream' else '1.0.2-laputa.1'}))
    (modules / 'open-orange/dist/bin.js').write_text(bin_text)
    (modules / 'rivetkit/package.json').write_text('{"version":"3.1.2-rc.1"}')
    (addon / 'rivetkit-napi.linux-x64-musl.node').write_bytes(b'addon')


class NativeAdapterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.base = Path(self.tmp.name)
        self.guest = self.base / 'guest'
        write_closure(self.guest / 'opt/native-rehearsal/orange', 'upstream')
        (self.guest / 'proc/100').mkdir(parents=True)
        (self.guest / 'proc/stat').write_text(f'cpu 0\nbtime {BTIME}\n')
        (self.guest / 'proc/100/cmdline').write_bytes(b'\0'.join([b'/usr/bin/node', BIN.encode(), b'serve']) + b'\0')
        (self.guest / 'proc/100/stat').write_text('100 (node) S ' + ' '.join(['0'] * 18) + f' {int((time.time() - 3600 - BTIME) * TICKS)} 0 0\n')
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
        self.adapter = oorollout_native.NativeAdapter(self.local_runner, health_url=self.health_url, health_deadline_s=5, min_free_bytes=1)
        self.baseline = self.adapter.observe()['selected']
        self.evidence = self.base / 'evidence'
        self.evidence.mkdir()
        self.journal = self.base / 'journal'
        self.journal.mkdir()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def local_runner(self, payload):
        result = subprocess.run([sys.executable, '-c', oorollout_native.GUEST_SCRIPT], input=payload, capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def stage_candidate(self):
        closure = self.base / 'candidate'
        write_closure(closure, 'patched')
        archive = self.base / 'candidate.tar'
        with tarfile.open(archive, 'w') as out:
            for name in ('package.json', 'pnpm-lock.yaml', 'node_modules'):
                out.add(closure / name, arcname=name)
        token = self.adapter.acquire('stager', 'stage', 60)
        staged = self.adapter.stage('stager', token, str(archive), 'test build')
        self.adapter.release('stager', token)
        return staged

    def engine(self, staged, crash=None):
        for name, value in (('decision.json', {'verdict': 'pass', 'evaluatedAtMs': int(time.time() * 1000), 'reasonCodes': []}), ('candidate.manifest.json', {'releaseId': staged['release']}), ('baseline.manifest.json', {'releaseId': self.baseline})):
            (self.evidence / name).write_text(json.dumps(value))
        config = {'target_kind': 'native', 'host': 'simulated', 'ssh_config': 'unused', 'run_id': str(self.journal), 'candidate': staged['release'], 'artifact': staged['digest'], 'baseline': self.baseline, 'policy': {'max_age_s': 600, 'observation_s': 0, 'check_interval_s': 0.01}, 'evidence_dir': str(self.evidence), 'deadline_s': 60}
        spec = {'env': self.env, 'health_url': self.health_url, 'journal': str(self.journal), 'config': config}
        env = {**os.environ, **({'ROLLOUT_CRASH': crash} if crash else {})}
        return subprocess.run([sys.executable, '-c', ENGINE_CHILD, str(LIB), json.dumps(spec)], capture_output=True, text=True, env=env)

    def restarts(self):
        path = self.guest / 'restarts'
        return path.read_text().split() if path.exists() else []

    def test_observe_before_conversion_identifies_the_in_place_runtime(self):
        state = self.adapter.observe()
        self.assertFalse(state['converted'])
        self.assertEqual(state['selected'], state['running'])
        self.assertEqual(state['artifacts'], {state['selected']: state['digest']})
        self.assertTrue(state['selected'].startswith('rt-'))

    def test_promotion_converts_once_activates_once_and_survives_each_crash(self):
        for point in (None, 'after-intent-convert-runtime', 'after-effect-convert-runtime', 'after-done-convert-runtime', 'after-intent-activate', 'after-effect-activate', 'after-done-activate', 'after-state-verifying'):
            with self.subTest(point=point):
                self.tearDown()
                self.setUp()
                staged = self.stage_candidate()
                if point:
                    self.assertEqual(self.engine(staged, point).returncode, 137)
                result = self.engine(staged)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout.splitlines()[-1])['state'], 'promoted')
                state = self.adapter.observe()
                self.assertEqual((state['selected'], state['running'], state['digest']), (staged['release'], staged['release'], staged['digest']))
                self.assertEqual(self.restarts(), [staged['release']])
                self.assertTrue((self.guest / 'opt/native-rehearsal/runtime' / self.baseline / 'release.json').exists())

    def test_switched_but_not_restarted_is_completed_with_one_restart(self):
        staged = self.stage_candidate()
        self.assertEqual(self.engine(staged, 'after-intent-activate').returncode, 137)
        runtime = self.guest / 'opt/native-rehearsal'
        (runtime / 'runtime/.previous').write_text(self.baseline + '\n')
        (runtime / 'orange.tmp').symlink_to('runtime/' + staged['release'])
        os.replace(runtime / 'orange.tmp', runtime / 'orange')
        state = self.adapter.observe()
        self.assertEqual((state['selected'], state['running']), (staged['release'], self.baseline))
        self.assertEqual(self.adapter.classify(state, self.baseline, staged['release'], staged['digest']), 'partial')
        result = self.engine(staged)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1])['state'], 'promoted', result.stderr)
        self.assertEqual(self.restarts(), [staged['release']])

    def test_failed_candidate_recovers_to_the_baseline(self):
        staged = self.stage_candidate()
        (self.guest / 'fail-release').write_text(staged['release'])
        result = self.engine(staged)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1])['state'], 'recovered', result.stderr)
        state = self.adapter.observe()
        self.assertEqual((state['selected'], state['running']), (self.baseline, self.baseline))
        self.assertEqual(self.restarts(), [staged['release'], self.baseline])

    def test_stale_tokens_and_competing_holders_are_refused(self):
        staged = self.stage_candidate()
        token = self.adapter.acquire('first', 'deployment', 60)
        with self.assertRaises(oorollout.LockHeld):
            self.adapter.acquire('second', 'deployment', 60)
        with self.assertRaises(oorollout.StaleToken):
            self.adapter.activate('first', token + 1, self.baseline, staged['release'], staged['digest'])
        self.adapter.release('first', token)
        with self.assertRaises(oorollout.StaleToken):
            self.adapter.prepare_step('first', token, 'convert-runtime')
        self.assertFalse(self.adapter.observe()['converted'])

    def test_unknown_selected_release_is_rejected_before_any_effect(self):
        staged = self.stage_candidate()
        token = self.adapter.acquire('operator', 'deployment', 60)
        self.adapter.prepare_step('operator', token, 'convert-runtime')
        self.adapter.release('operator', token)
        runtime = self.guest / 'opt/native-rehearsal'
        (runtime / 'runtime/rt-000000000000').mkdir()
        (runtime / 'orange.tmp').symlink_to('runtime/rt-000000000000')
        os.replace(runtime / 'orange.tmp', runtime / 'orange')
        (self.guest / 'proc/100/stat').write_text('100 (node) S ' + ' '.join(['0'] * 18) + f' {int((time.time() + 5 - BTIME) * TICKS)} 0 0\n')
        result = self.engine(staged)
        self.assertEqual(json.loads(result.stdout.splitlines()[-1])['state'], 'rejected', result.stderr)
        self.assertEqual(self.restarts(), [])


if __name__ == '__main__':
    unittest.main()
