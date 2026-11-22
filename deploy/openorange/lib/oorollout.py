import fcntl
import json
import os
import re
import signal
import subprocess
import time
import uuid

import ooreceipt
from pathlib import Path


TERMINAL = {'promoted', 'rejected', 'recovered', 'needs-operator'}
POST_PREPARE = {'prepared', 'activated', 'verifying', 'recovering'}


def now():
    return time.time()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic(path, value):
    temp = path.with_name('.' + path.name + '-' + uuid.uuid4().hex)
    try:
        with temp.open('x') as out:
            json.dump(value, out, sort_keys=True)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
        sync_dir(path.parent)
    finally:
        if temp.exists():
            temp.unlink()


def crash(point):
    if os.environ.get('ROLLOUT_CRASH') == point:
        os._exit(137)


class LockHeld(Exception):
    pass


class StaleToken(Exception):
    pass


class AmbiguousIdentity(ValueError):
    pass


class FakeAdapter:
    """Local test adapter; all calls that mutate target state require a live fence."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.guard = self.directory / '.guard'

    def locked(self):
        return self.guard.open('a+')

    def acquire(self, holder, operation, lease_s):
        with self.locked() as guard:
            fcntl.flock(guard, fcntl.LOCK_EX)
            path = self.directory / 'lock.json'
            old = json.loads(path.read_text()) if path.exists() else None
            if old and old['lease_expiry'] > now() and old['holder'] != holder:
                raise LockHeld(old['holder'])
            if old and old['holder'] == holder and old['lease_expiry'] > now():
                token = old['fencing_token']
            else:
                counter = self.directory / 'fence.json'
                token = (json.loads(counter.read_text())['token'] if counter.exists() else 0) + 1
                atomic(counter, {'token': token})
            record = {'holder': holder, 'operation': operation, 'fencing_token': token, 'lease_expiry': now() + lease_s}
            if not path.exists():
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, 'w') as out:
                    json.dump(record, out)
                    out.flush()
                    os.fsync(out.fileno())
                sync_dir(self.directory)
            else:
                atomic(path, record)
            return token

    def renew(self, holder, token, lease_s):
        with self.locked() as guard:
            fcntl.flock(guard, fcntl.LOCK_EX)
            self._check(holder, token)
            path = self.directory / 'lock.json'
            record = json.loads(path.read_text())
            record['lease_expiry'] = now() + lease_s
            atomic(path, record)
            return token

    def release(self, holder, token):
        with self.locked() as guard:
            fcntl.flock(guard, fcntl.LOCK_EX)
            self._check(holder, token)
            (self.directory / 'lock.json').unlink()
            sync_dir(self.directory)

    def _check(self, holder, token):
        path = self.directory / 'lock.json'
        record = json.loads(path.read_text()) if path.exists() else {}
        if record.get('holder') != holder or record.get('fencing_token') != token or record.get('lease_expiry', 0) <= now():
            raise StaleToken('expired or stale fencing token')

    def observe(self):
        return json.loads((self.directory / 'state.json').read_text())

    def preparations(self, config):
        return []

    def classify(self, state, expected, release, digest):
        if state['selected'] == release and state['running'] == release and state['digest'] == digest:
            return 'applied'
        if state['selected'] == expected and state['running'] == expected:
            return 'not-applied'
        return 'ambiguous'

    def activate(self, holder, token, expected, release, digest):
        with self.locked() as guard:
            fcntl.flock(guard, fcntl.LOCK_EX)
            self._check(holder, token)
            state = self.observe()
            if state['selected'] == release and state['running'] == release and state['digest'] == digest:
                return state
            if state['selected'] != expected or state['running'] != expected:
                raise ValueError('conditional activation identity mismatch')
            state.update(selected=release, running=release, digest=state.get('activated_digest', {}).get(release, digest))
            state.setdefault('activations', []).append(release)
            atomic(self.directory / 'state.json', state)
            return state

    def check(self, release, digest):
        state = self.observe()
        healthy = state.get('health', True) and not (release in state.get('fail_checks', []))
        return {'ok': healthy and state['selected'] == release and state['running'] == release and state['digest'] == digest, 'state': state}


class Journal:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / 'journal.jsonl'
        self.records = []
        self.torn = False
        if self.path.exists():
            data = self.path.read_bytes()
            lines = data.splitlines(keepends=True)
            for index, line in enumerate(lines):
                if not line.endswith(b'\n') and index == len(lines) - 1:
                    self.torn = True
                    break
                record = json.loads(line)
                if record['seq'] != len(self.records) + 1:
                    raise ValueError('invalid journal sequence')
                self.records.append(record)

    def append(self, kind, **fields):
        if self.torn:
            with self.path.open('r+b') as out:
                data = out.read()
                out.truncate(data.rfind(b'\n') + 1)
                out.flush()
                os.fsync(out.fileno())
            sync_dir(self.directory)
            self.torn = False
        record = {'seq': len(self.records) + 1, 'kind': kind, 'at': now(), **fields}
        with self.path.open('ab') as out:
            out.write((json.dumps(record, sort_keys=True) + '\n').encode())
            out.flush()
            os.fsync(out.fileno())
        sync_dir(self.directory)
        self.records.append(record)
        crash('after-' + kind + '-' + str(fields.get('step', fields.get('state', ''))))
        return record

    def last(self, kind):
        return next((r for r in reversed(self.records) if r['kind'] == kind), None)

    def state(self):
        record = self.last('state')
        return record['state'] if record else 'staged'

    def transition(self, state, deadline_s, **fields):
        self.append('state', state=state, deadline=now() + deadline_s, **fields)


ADMISSION = {'fake': 'promotion', 'native': 'promotion', 'oo-containers': 'promotion', 'native-app': 'app-deploy'}


def gate(config):
    if ADMISSION[config['target_kind']] == 'app-deploy':
        receipt, reasons = ooreceipt.verify_admission(config['receipt'], config['evidence_dir'])
    else:
        receipt, reasons = ooreceipt.verify(config['receipt'], config['evidence_dir'], config['evaluator'])
    if reasons:
        return None, reasons
    if receipt['candidate']['releaseId'] != config['candidate']:
        return None, ['release-identity-mismatch']
    if receipt['candidate']['artifactDigest'] != config['artifact']:
        return None, ['artifact-not-qualified']
    return receipt, []


def reconcile(journal, adapter, holder, token, step, expected, release, digest):
    intents = [r for r in journal.records if r['kind'] == 'intent' and r['step'] == step]
    done = [r for r in journal.records if r['kind'] == 'done' and r['step'] == step]
    if done:
        return done[-1]['observed']
    if not intents:
        journal.append('intent', step=step, expected=expected, release=release, digest=digest)
    state = adapter.observe()
    classification = adapter.classify(state, expected, release, digest)
    if classification == 'applied':
        observed = state
    elif classification == 'not-applied':
        adapter.activate(holder, token, expected, release, digest)
        crash('after-effect-' + step)
        observed = adapter.observe()
    elif classification == 'partial':
        adapter.complete(holder, token, state, release, digest)
        crash('after-effect-' + step)
        observed = adapter.observe()
    else:
        raise AmbiguousIdentity('ambiguous target identity: ' + json.dumps(state, sort_keys=True))
    if observed['selected'] != release or observed['running'] != release or observed['digest'] != digest:
        raise ValueError('activated identity or digest mismatch: ' + json.dumps(observed, sort_keys=True))
    journal.append('done', step=step, observed=observed)
    return observed


def adapter_for(config):
    if config['target_kind'] == 'fake':
        return FakeAdapter(config['target'])
    if config['target_kind'] == 'native':
        import oorollout_native
        return oorollout_native.NativeAdapter(oorollout_native.ssh_runner(config['ssh_config'], config['host']), 'runtime', bound_s=config['bound_s'])
    if config['target_kind'] == 'native-app':
        import oorollout_native
        return oorollout_native.NativeAdapter(oorollout_native.ssh_runner(config['ssh_config'], config['host']), 'app', bound_s=config['bound_s'])
    if config['target_kind'] == 'oo-containers':
        import oorollout_containers
        return oorollout_containers.ContainersAdapter(oorollout_containers.ssh_runner(config['ssh_config'], config['host']), config['app'], bound_s=config['bound_s'])
    raise ValueError('unknown target kind: ' + str(config['target_kind']))


def component_reasons(target, receipt):
    declared = receipt['candidate']['components']
    return ['component-mismatch:' + name for name, digest in sorted(target.get('components', {}).items()) if declared.get(name) != digest]


def authority(policy):
    """Reads writer authority through the policy's authority_check; returns (digest, record) or raises."""
    spec = policy.get('authority_check')
    if spec is None:
        return None, None
    try:
        child = subprocess.Popen(spec['argv'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            stdout, stderr = child.communicate(timeout=spec['timeout_s'])
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.communicate()
            raise ValueError('writer authority check timed out')
        value = json.loads(stdout)
    except (OSError, ValueError) as exc:
        raise ValueError('writer authority unavailable: ' + str(exc)) from None
    if child.returncode != 0 or not isinstance(value, dict) or value.get('ok') is not True or not isinstance(value.get('authority'), dict):
        raise ValueError('writer authority refused: ' + stdout.strip()[:500])
    return ooreceipt.sha(ooreceipt.canonical(value['authority'])), value['authority']


def functional_check(policy, release, digest):
    spec = policy['functional_check']
    try:
        child = subprocess.Popen(spec['argv'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True, env={**os.environ, 'ROLLOUT_RELEASE': release, 'ROLLOUT_DIGEST': digest})
        try:
            stdout, stderr = child.communicate(timeout=spec['timeout_s'])
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.communicate()
            return {'ok': False, 'error': 'functional check timed out'}
        try:
            value = json.loads(stdout)
        except ValueError as exc:
            return {'ok': False, 'error': str(exc), 'exit_code': child.returncode, 'stdout': stdout, 'stderr': stderr}
        return {'ok': child.returncode == 0 and isinstance(value, dict) and value.get('ok') is True, 'exit_code': child.returncode, 'output': value, 'stderr': stderr}
    except (OSError, ValueError) as exc:
        return {'ok': False, 'error': str(exc)}


def run(journal, recovery=False, adapter=None, recovered_by=None):
    config = journal.records[0]['config']
    if adapter is None:
        adapter = adapter_for(config)
    policy = config['policy']
    duration = config['deadline_s']
    lease_s = max(duration, config['bound_s'] + 10)
    run_id = config['run_id']
    holder = 'watchdog-' + uuid.uuid4().hex if recovered_by else run_id
    with (journal.directory / '.controller').open('a+') as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LockHeld(run_id) from None
        journal = Journal(journal.directory)
        state = journal.state()
        if state in TERMINAL:
            return state
        journal.append('intent', step='lock-acquire', operation='deployment')
        token = adapter.acquire(holder, 'deployment', lease_s)
        crash('after-effect-lock-acquire')
        journal.append('done', step='lock-acquire', observed={'holder': holder, 'fencing_token': token})
        try:
            journal.append('heartbeat', deadline=now() + duration)
            if state in {'staged', 'qualified'} and journal.last('state') and journal.last('state')['deadline'] < now():
                journal.transition('rejected', duration, reasons=['deadline-expired'])
                return 'rejected'
            if recovery and state in {'staged', 'qualified'}:
                journal.transition('rejected', duration, reasons=['aborted'])
                return 'rejected'
            if state in POST_PREPARE and state != 'recovering' and journal.last('state')['deadline'] < now():
                recovery = True
            if recovery and state in POST_PREPARE:
                journal.transition('recovering', duration, reason='controller recovery requested', **({'recovered-by': recovered_by} if recovered_by else {}))
                state = 'recovering'
            if state == 'staged':
                receipt, reasons = gate(config)
                if reasons:
                    journal.transition('rejected', duration, reasons=reasons)
                    return 'rejected'
                journal.transition('qualified', duration, receipt=receipt, receiptSha256=ooreceipt.sha(ooreceipt.canonical(receipt)), rolloutPolicySha256=config['rollout_policy_sha256'])
                state = 'qualified'
            if state == 'qualified':
                qualified = journal.last('state')
                target = adapter.observe()
                receipt = qualified['receipt']
                age = now() * 1000 - receipt['decision']['evaluatedAtMs']
                recovery_digest = receipt['baseline']['artifactDigest']
                reasons = []
                if target.get('running') != config['baseline'] or target.get('selected') != config['baseline']:
                    reasons.append('baseline-identity-mismatch')
                if age < 0 or age > policy['max_age_s'] * 1000:
                    reasons.append('stale-decision')
                if target.get('digest') != recovery_digest or target.get('selected_digest', recovery_digest) != recovery_digest or target.get('artifacts', {}).get(target.get('running')) != recovery_digest or target.get('running_digest', recovery_digest) != recovery_digest or target.get('running_image_id', recovery_digest) != recovery_digest:
                    reasons.append('baseline-artifact-mismatch')
                staged = target.get('artifacts', {}).get(receipt['candidate']['releaseId'])
                if staged is None:
                    reasons.append('candidate-not-staged')
                elif staged != receipt['candidate']['artifactDigest']:
                    reasons.append('staged-artifact-mismatch')
                if not target.get('headroom', False):
                    reasons.append('insufficient-headroom:' + str(target.get('headroom_detail', 'unknown')))
                reasons += component_reasons(target, receipt)
                try:
                    authority_digest, authority_record = authority(policy)
                except ValueError as exc:
                    authority_digest, authority_record = None, None
                    reasons.append(str(exc))
                if reasons:
                    journal.transition('rejected', duration, reasons=reasons)
                    return 'rejected'
                journal.transition('prepared', duration, baseline_digest=recovery_digest, authority=authority_record, authority_sha256=authority_digest)
                state = 'prepared'
            qualified_receipt = next(r['receipt'] for r in journal.records if r['kind'] == 'state' and r['state'] == 'qualified')
            qualified_digest = qualified_receipt['candidate']['artifactDigest']
            candidate = qualified_receipt['candidate']['releaseId']
            baseline = config['baseline']
            prepared = next(r for r in journal.records if r['kind'] == 'state' and r['state'] == 'prepared')
            baseline_digest = prepared['baseline_digest']
            if state == 'prepared':
                try:
                    for step in adapter.preparations(config):
                        if any(r['kind'] == 'done' and r['step'] == step for r in journal.records):
                            continue
                        if not any(r['kind'] == 'intent' and r['step'] == step for r in journal.records):
                            journal.append('intent', step=step)
                        if not adapter.prepare_observed(step):
                            token = adapter.renew(holder, token, lease_s)
                            adapter.prepare_step(holder, token, step)
                            crash('after-effect-' + step)
                        if not adapter.prepare_observed(step):
                            raise ValueError('preparation incomplete: ' + step)
                        journal.append('done', step=step, observed=adapter.observe())
                    if not any(r['kind'] == 'intent' and r['step'] == 'activate' for r in journal.records):
                        target = adapter.observe()
                        reasons = [] if target.get('artifacts', {}).get(candidate) == qualified_digest else ['staged-artifact-mismatch']
                        reasons += component_reasons(target, qualified_receipt)
                        try:
                            if authority(policy)[0] != prepared.get('authority_sha256'):
                                reasons.append('writer-authority-changed')
                        except ValueError as exc:
                            reasons.append(str(exc))
                        if reasons:
                            journal.transition('rejected', duration, reasons=reasons)
                            return 'rejected'
                    token = adapter.renew(holder, token, lease_s)
                    reconcile(journal, adapter, holder, token, 'activate', baseline, candidate, qualified_digest)
                    journal.transition('activated', duration)
                    state = 'activated'
                except AmbiguousIdentity as exc:
                    journal.transition('needs-operator', duration, reason=str(exc), evidence=adapter.observe())
                    return 'needs-operator'
                except ValueError as exc:
                    journal.transition('recovering', duration, reason=str(exc))
                    state = 'recovering'
            if state == 'activated':
                journal.transition('verifying', policy['observation_s'] + duration, observation_until=now() + policy['observation_s'])
                state = 'verifying'
            if state == 'verifying':
                until = journal.last('state')['observation_until']
                while True:
                    journal.append('intent', step='lock-renew', fencing_token=token)
                    token = adapter.renew(holder, token, lease_s)
                    journal.append('done', step='lock-renew', observed={'holder': holder, 'fencing_token': token})
                    journal.append('heartbeat', deadline=now() + duration)
                    if now() > journal.last('state')['deadline']:
                        journal.transition('recovering', duration, reason='verification deadline expired')
                        state = 'recovering'
                        break
                    result = adapter.check(candidate, qualified_digest)
                    functional = functional_check(policy, candidate, qualified_digest)
                    journal.append('check', result=result, functional=functional)
                    if not result['ok'] or not functional['ok']:
                        journal.transition('recovering', duration, reason='post-activation check failed', evidence=result)
                        state = 'recovering'
                        break
                    if now() >= until:
                        token = adapter.renew(holder, token, lease_s)
                        journal.transition('promoted', duration)
                        return 'promoted'
                    time.sleep(min(policy['check_interval_s'], until - now()))
            if state == 'recovering':
                try:
                    token = adapter.renew(holder, token, lease_s)
                    reconcile(journal, adapter, holder, token, 'recover', candidate, baseline, baseline_digest)
                    result = adapter.check(baseline, baseline_digest)
                    functional = functional_check(policy, baseline, baseline_digest)
                    journal.append('check', result=result, functional=functional)
                    if not result['ok'] or not functional['ok']:
                        raise ValueError('baseline verification failed: ' + json.dumps({'adapter': result, 'functional': functional}))
                    token = adapter.renew(holder, token, lease_s)
                    journal.transition('recovered', duration, evidence=result, **({'recovered-by': recovered_by} if recovered_by else {}))
                    return 'recovered'
                except ValueError as exc:
                    journal.transition('needs-operator', duration, reason=str(exc), evidence=adapter.observe())
                    return 'needs-operator'
        finally:
            try:
                journal.append('intent', step='lock-release', fencing_token=token)
                adapter.release(holder, token)
                journal.append('done', step='lock-release', observed={'released': True})
            except StaleToken:
                pass


def status(journal):
    return {'run_id': journal.records[0]['config']['run_id'], 'state': journal.state(), 'records': journal.records, 'note': 'torn final line ignored' if journal.torn else None}
