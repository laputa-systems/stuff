import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import test_rollout_native as native

CLI = native.ROOT / 'deploy/openorange/bin/rollout'

SSH = '''#!/usr/bin/env python3
import json, os, shlex, subprocess, sys
request = json.loads(sys.stdin.read())
request['args']['health_url'] = os.environ['FAKE_HEALTH_URL']
request['args']['min_free_bytes'] = 1
if os.environ.get('FAKE_STALE') and request['op'] == 'run_command':
    request['args']['token'] += 1
result = subprocess.run(shlex.split(sys.argv[-1]), input=json.dumps(request) + '\\n', text=True, capture_output=True)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
'''


@pytest.fixture
def guest():
    case = native.NativeAdapterTest('test_observe_before_conversion_identifies_the_in_place_runtime')
    case.setUp()
    try:
        ssh = case.base / 'bin/ssh'
        ssh.write_text(SSH)
        ssh.chmod(0o755)
        case.env['FAKE_HEALTH_URL'] = case.health_url
        yield case
    finally:
        case.tearDown()


def test_blocked_action_expires_and_competing_holder_fences(guest):
    token = guest.adapter.acquire('a', 'test', 2.4)
    marker = guest.base / 'late'
    with pytest.raises(ValueError, match='insufficient-lease'):
        guest.adapter.call('run_command', holder='a', token=token, bound_s=5, argv=['true'])
    before = time.monotonic()
    with pytest.raises(ValueError, match='timed out'):
        guest.adapter.call('run_command', holder='a', token=token, bound_s=0.4, argv=[sys.executable, '-c', f'import time; time.sleep(2); open({str(marker)!r}, "w").write("late")'])
    assert time.monotonic() - before < 2.0
    with pytest.raises(native.oorollout.LockHeld):
        guest.adapter.acquire('b', 'test', 10)
    expiry = json.loads((guest.guest / 'var/lib/openorange-rollout/lock.json').read_text())['lease_expiry']
    time.sleep(max(0, expiry - time.time()) + .05)
    newer = guest.adapter.acquire('b', 'test', 10)
    assert newer > token
    with pytest.raises(native.oorollout.StaleToken):
        guest.adapter.renew('a', token, 10)
    with pytest.raises(native.oorollout.StaleToken):
        guest.adapter.call('run_command', holder='a', token=token, bound_s=.1, argv=['true'])
    assert not marker.exists()
    guest.adapter.release('b', newer)


def test_hung_native_restart_is_killed_within_bound(guest):
    staged = guest.stage_candidate()
    token = guest.adapter.acquire('a', 'test', 30)
    guest.adapter.prepare_step('a', token, 'convert-runtime')
    rc = guest.base / 'bin/rc-service'
    marker = guest.base / 'restart-finished'
    rc.write_text(f'#!/bin/sh\nsleep 1.2\ntouch {marker}\n')
    before = time.monotonic()
    with pytest.raises(ValueError, match='timed out'):
        guest.adapter.call('activate', holder='a', token=token, bound_s=.4, expected=guest.baseline, release=staged['release'], digest=staged['digest'])
    assert time.monotonic() - before < 2
    time.sleep(1.3)
    assert not marker.exists()
    guest.adapter.release('a', token)


def test_lease_run_refuses_held_and_stale_tokens(guest):
    args = [str(CLI), 'lease', 'run', '--target-kind', 'native', '--host', 'guest', '--ssh-config', 'unused', '--operation', 'test', '--bound-s', '1', '--', sys.executable, '-c', 'print(42)']
    token = guest.adapter.acquire('other', 'test', 10)
    held = subprocess.run(args, text=True, capture_output=True, env=guest.env)
    assert held.returncode == 4, held.stderr
    guest.adapter.release('other', token)
    stale = subprocess.run(args, text=True, capture_output=True, env={**guest.env, 'FAKE_STALE': '1'})
    assert stale.returncode == 1 and 'stale' in stale.stderr
    assert '42' not in stale.stdout
    success = subprocess.run(args, text=True, capture_output=True, env=guest.env)
    assert success.returncode == 0 and success.stdout.strip() == '42', success.stderr
    failed = subprocess.run(args[:-1] + ['import sys; sys.exit(7)'], text=True, capture_output=True, env=guest.env)
    assert failed.returncode == 7, failed.stderr
