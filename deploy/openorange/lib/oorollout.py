import fcntl
import json
import os
import re
import time
import uuid
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


def gate(config):
    root = Path(config['evidence_dir'])
    try:
        decision = json.loads((root / 'decision.json').read_text())
        candidate = json.loads((root / 'candidate.manifest.json').read_text())
        baseline = json.loads((root / 'baseline.manifest.json').read_text())
        if decision['verdict'] != 'pass':
            return None, decision.get('reasonCodes', []) or ['verdict-' + str(decision['verdict'])]
        if candidate['releaseId'] != config['candidate'] or baseline['releaseId'] != config['baseline']:
            return None, ['release-identity-mismatch']
        if type(decision['evaluatedAtMs']) is not int:
            return None, ['invalid-evaluation-time']
        return decision, []
    except (OSError, ValueError, KeyError, TypeError):
        return None, ['invalid-evidence']


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
        return oorollout_native.NativeAdapter(oorollout_native.ssh_runner(config['ssh_config'], config['host']))
    raise ValueError('unknown target kind: ' + str(config['target_kind']))


def run(journal, recovery=False, adapter=None):
    config = journal.records[0]['config']
    if adapter is None:
        adapter = adapter_for(config)
    policy = config['policy']
    duration = config['deadline_s']
    run_id = config['run_id']
    with (journal.directory / '.controller').open('a+') as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LockHeld(run_id) from None
        state = journal.state()
        if state in TERMINAL:
            return state
        journal.append('intent', step='lock-acquire', operation='deployment')
        token = adapter.acquire(run_id, 'deployment', max(duration, 1))
        crash('after-effect-lock-acquire')
        journal.append('done', step='lock-acquire', observed={'holder': run_id, 'fencing_token': token})
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
                journal.transition('recovering', duration, reason='controller recovery requested')
                state = 'recovering'
            if state == 'staged':
                decision, reasons = gate(config)
                if reasons:
                    journal.transition('rejected', duration, reasons=reasons)
                    return 'rejected'
                journal.transition('qualified', duration, decision=decision, artifact=config['artifact'])
                state = 'qualified'
            if state == 'qualified':
                qualified = journal.last('state')
                target = adapter.observe()
                age = now() * 1000 - qualified['decision']['evaluatedAtMs']
                recovery_digest = target.get('artifacts', {}).get(config['baseline'])
                reasons = []
                if target.get('running') != config['baseline'] or target.get('selected') != config['baseline']:
                    reasons.append('baseline-identity-mismatch')
                if age < 0 or age > policy['max_age_s'] * 1000:
                    reasons.append('stale-decision')
                if not recovery_digest or target.get('digest') != recovery_digest:
                    reasons.append('missing-baseline-artifact')
                if not target.get('headroom', False):
                    reasons.append('insufficient-headroom:' + str(target.get('headroom_detail', 'unknown')))
                if reasons:
                    journal.transition('rejected', duration, reasons=reasons)
                    return 'rejected'
                journal.transition('prepared', duration, baseline_digest=recovery_digest)
                state = 'prepared'
            qualified_digest = next(r['artifact'] for r in journal.records if r['kind'] == 'state' and r['state'] == 'qualified')
            baseline_digest = next(r['baseline_digest'] for r in journal.records if r['kind'] == 'state' and r['state'] == 'prepared')
            if state == 'prepared':
                try:
                    for step in adapter.preparations(config):
                        if any(r['kind'] == 'done' and r['step'] == step for r in journal.records):
                            continue
                        if not any(r['kind'] == 'intent' and r['step'] == step for r in journal.records):
                            journal.append('intent', step=step)
                        if not adapter.prepare_observed(step):
                            adapter.prepare_step(run_id, token, step)
                            crash('after-effect-' + step)
                        if not adapter.prepare_observed(step):
                            raise ValueError('preparation incomplete: ' + step)
                        journal.append('done', step=step, observed=adapter.observe())
                    reconcile(journal, adapter, run_id, token, 'activate', config['baseline'], config['candidate'], qualified_digest)
                    journal.transition('activated', duration)
                    state = 'activated'
                except AmbiguousIdentity as exc:
                    journal.transition('needs-operator', duration, reason=str(exc), evidence=adapter.observe())
                    return 'needs-operator'
                except ValueError as exc:
                    journal.transition('recovering', duration, reason=str(exc))
                    state = 'recovering'
            if state == 'activated':
                journal.transition('verifying', duration, observation_until=now() + policy['observation_s'])
                state = 'verifying'
            if state == 'verifying':
                until = journal.last('state')['observation_until']
                while True:
                    journal.append('intent', step='lock-renew', fencing_token=token)
                    token = adapter.acquire(run_id, 'deployment', max(duration, 1))
                    journal.append('done', step='lock-renew', observed={'holder': run_id, 'fencing_token': token})
                    journal.append('heartbeat', deadline=now() + duration)
                    if now() > journal.last('state')['deadline']:
                        journal.transition('recovering', duration, reason='verification deadline expired')
                        state = 'recovering'
                        break
                    result = adapter.check(config['candidate'], qualified_digest)
                    journal.append('check', result=result)
                    if not result['ok']:
                        journal.transition('recovering', duration, reason='post-activation check failed', evidence=result)
                        state = 'recovering'
                        break
                    if now() >= until:
                        journal.transition('promoted', duration)
                        return 'promoted'
                    time.sleep(min(policy['check_interval_s'], until - now()))
            if state == 'recovering':
                try:
                    reconcile(journal, adapter, run_id, token, 'recover', config['candidate'], config['baseline'], baseline_digest)
                    result = adapter.check(config['baseline'], baseline_digest)
                    if not result['ok']:
                        raise ValueError('baseline verification failed: ' + json.dumps(result))
                    journal.transition('recovered', duration, evidence=result)
                    return 'recovered'
                except ValueError as exc:
                    journal.transition('needs-operator', duration, reason=str(exc), evidence=adapter.observe())
                    return 'needs-operator'
        finally:
            try:
                journal.append('intent', step='lock-release', fencing_token=token)
                adapter.release(run_id, token)
                journal.append('done', step='lock-release', observed={'released': True})
            except StaleToken:
                pass


def status(journal):
    return {'run_id': journal.records[0]['config']['run_id'], 'state': journal.state(), 'records': journal.records, 'note': 'torn final line ignored' if journal.torn else None}
