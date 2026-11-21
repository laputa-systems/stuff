import json
import os
import signal
import subprocess
import sys
import time

import receipt_support
from test_lease import CLI, guest


def wait_for(predicate, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(.05)
    raise AssertionError('timed out waiting for rollout state')


def test_sigkill_controller_watchdog_takes_lease_and_recovers(guest):
    staged = guest.stage_candidate()
    baseline_digest = guest.adapter.observe()['digest']
    receipt, evidence, evaluator = receipt_support.make_receipt(guest.base / 'qualification', guest.baseline, staged['release'], baseline_digest, staged['digest'])
    policy = guest.base / 'policy.json'
    policy.write_text(json.dumps({'max_age_s': 600, 'observation_s': 60, 'check_interval_s': .1, 'functional_check': {'argv': [sys.executable, '-c', 'import json,os; print(json.dumps({"ok": bool(os.environ.get("ROLLOUT_RELEASE")) and bool(os.environ.get("ROLLOUT_DIGEST")), "release": os.environ.get("ROLLOUT_RELEASE"), "digest": os.environ.get("ROLLOUT_DIGEST")}))'], 'timeout_s': 5}}))
    journals = guest.base / 'runs'
    journals.mkdir()
    cmd = [str(CLI), 'start', '--candidate', staged['release'], '--artifact', staged['digest'], '--baseline', guest.baseline, '--target-kind', 'native', '--host', 'guest', '--ssh-config', 'unused', '--policy', str(policy), '--receipt', str(receipt), '--evaluator', str(evaluator), '--evidence-dir', str(evidence), '--journal-dir', str(journals), '--deadline-s', '2', '--bound-s', '3', '--json']
    controller = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=guest.env)
    watchdog = None
    log = guest.base / 'watchdog.log'
    output = log.open('w')
    try:
        def records():
            paths = list(journals.glob('*/journal.jsonl'))
            if not paths:
                return []
            return [json.loads(line) for line in paths[0].read_text().splitlines() if line.endswith('}')]
        wait_for(lambda: any(r.get('state') == 'verifying' for r in records()), 20)
        lock = guest.guest / 'var/lib/openorange-rollout/lock.json'
        controller_token = json.loads(lock.read_text())['fencing_token']
        controller.kill()
        controller.communicate(timeout=5)
        assert controller.returncode == -signal.SIGKILL
        watchdog = subprocess.Popen([str(CLI), 'watchdog', '--journal-dir', str(journals), '--loop', '--interval-s', '.2'], stdout=output, stderr=subprocess.PIPE, text=True, env=guest.env)
        wait_for(lambda: any(r.get('state') in ('recovered', 'needs-operator') for r in records()), 35)
        wait_for(lambda: '"state": "recovered"' in log.read_text(), 5)
        rows = records()
        final = [r for r in rows if r.get('kind') == 'state'][-1]
        assert final['state'] == 'recovered', final
        assert final['recovered-by'] == 'watchdog'
        acquisitions = [r['observed'] for r in rows if r.get('kind') == 'done' and r.get('step') == 'lock-acquire']
        assert acquisitions[-1]['fencing_token'] > controller_token
        assert acquisitions[-1]['holder'].startswith('watchdog-')
        state = guest.adapter.observe()
        assert (state['selected'], state['running'], state['digest']) == (guest.baseline, guest.baseline, baseline_digest)
        checks = [r for r in rows if r['kind'] == 'check' and r['functional']['ok']]
        assert checks[-1]['result']['state']['selected'] == guest.baseline
        assert checks[-1]['functional']['output']['release'] == guest.baseline
        assert checks[-1]['functional']['output']['digest'] == baseline_digest
        assert all(r.get('step') != 'abort' for r in rows)
    finally:
        if controller.poll() is None:
            controller.kill()
            controller.communicate(timeout=5)
        if watchdog is not None:
            watchdog.terminate()
            _, err = watchdog.communicate(timeout=5)
        output.close()
    passes = [json.loads(line) for line in log.read_text().splitlines()]
    assert any(any(item['state'] == 'lock-held' for item in batch) for batch in passes), (passes, err)
    assert any(any(item['state'] == 'recovered' for item in batch) for batch in passes), (passes, err)


def test_watchdog_service_templates_render_explicit_paths(tmp_path):
    installer = CLI.parent.parent / 'watchdog/install'
    for kind in ('launchd', 'openrc'):
        output = tmp_path / kind
        log = tmp_path / (kind + '.log')
        argv = [str(installer), '--kind', kind, '--journal-dir', str(tmp_path / 'journals'), '--rollout', str(CLI), '--python', sys.executable, '--log', str(log), '--output', str(output)]
        wrong = argv + ['--user', 'josh'] if kind == 'launchd' else argv
        assert subprocess.run(wrong, capture_output=True, text=True).returncode == 2
        result = subprocess.run(argv + ['--user', 'josh'] if kind == 'openrc' else argv, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        rendered = output.read_text()
        assert str(CLI) in rendered and str(tmp_path / 'journals') in rendered
        assert sys.executable in rendered and str(log) in rendered
        assert rendered.index(sys.executable) < rendered.index(str(CLI))
        assert '--loop' in rendered and '--interval-s' in rendered
        if kind == 'openrc':
            assert os.access(output, os.X_OK)
            assert 'supervisor=supervise-daemon' in rendered and 'command_user="josh"' in rendered
            assert 'respawn_max=0' in rendered and 'command_background' not in rendered
