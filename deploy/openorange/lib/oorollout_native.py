"""Rollout adapter for the native standby Stats writer.

Every guest operation runs GUEST_SCRIPT with the guest's python3. Over SSH the
script arrives on stdin; tests run the same script locally with ROOT pointing
at a simulated guest filesystem.
"""
import json
import shlex
import subprocess
from pathlib import Path

GUEST_SCRIPT = r'''
import fcntl, hashlib, json, os, shutil, subprocess, sys, tarfile, time, urllib.request, uuid

ROOT = os.environ.get('ROLLOUT_GUEST_ROOT', '/')
BIN = '/opt/native-rehearsal/orange/node_modules/open-orange/dist/bin.js'


def path(p):
    return os.path.join(ROOT, p.lstrip('/'))


RUNTIME = path('/opt/native-rehearsal/orange')
RELEASES = path('/opt/native-rehearsal/runtime')
PREVIOUS = os.path.join(RELEASES, '.previous')
LOCKS = path('/var/lib/openorange-rollout')


def sync_dir(p):
    fd = os.open(p, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_atomic(p, text):
    temp = p + '.' + uuid.uuid4().hex
    with open(temp, 'x') as out:
        out.write(text)
        out.flush()
        os.fsync(out.fileno())
    os.replace(temp, p)
    sync_dir(os.path.dirname(p))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def closure_digest(root):
    modules = os.path.join(root, 'node_modules')
    identity = {'package.json': sha(os.path.join(root, 'package.json')), 'pnpm-lock.yaml': sha(os.path.join(root, 'pnpm-lock.yaml')), 'open-orange/dist/bin.js': sha(os.path.join(modules, 'open-orange/dist/bin.js'))}
    for name in ('open-orange', 'rivetkit'):
        with open(os.path.join(modules, name, 'package.json')) as f:
            identity[name + '@version'] = json.load(f)['version']
    store = os.path.join(modules, '.pnpm')
    for entry in sorted(os.listdir(store)) if os.path.isdir(store) else []:
        if not entry.startswith('@rivetkit+rivetkit-napi'):
            continue
        for dirpath, _, files in os.walk(os.path.join(store, entry)):
            for file in sorted(files):
                if file.endswith('.node'):
                    full = os.path.join(dirpath, file)
                    identity[os.path.relpath(full, store)] = sha(full)
    canonical = json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()
    return 'sha256:' + hashlib.sha256(canonical).hexdigest()


def release_id(digest):
    return 'rt-' + digest.removeprefix('sha256:')[:12]


def release_record(directory):
    with open(os.path.join(directory, 'release.json')) as f:
        return json.load(f)


def artifacts():
    found = {}
    if os.path.isdir(RELEASES):
        for name in sorted(os.listdir(RELEASES)):
            directory = os.path.join(RELEASES, name)
            if name.startswith('rt-') and os.path.isfile(os.path.join(directory, 'release.json')):
                found[name] = release_record(directory)['digest']
    return found


def process():
    proc = path('/proc')
    with open(os.path.join(proc, 'stat')) as f:
        btime = next(int(line.split()[1]) for line in f if line.startswith('btime '))
    ticks = os.sysconf('SC_CLK_TCK')
    matches = []
    for pid in os.listdir(proc):
        if not pid.isdigit():
            continue
        try:
            with open(os.path.join(proc, pid, 'cmdline'), 'rb') as f:
                argv = f.read().split(b'\0')
            with open(os.path.join(proc, pid, 'stat')) as f:
                fields = f.read().rsplit(')', 1)[1].split()
        except OSError:
            continue
        if argv and os.path.basename(argv[0]) == b'node' and len(argv) > 1 and argv[1] == BIN.encode():
            matches.append({'pid': int(pid), 'started_at': btime + int(fields[19]) / ticks})
    return matches


def health(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status == 200 and json.load(response).get('ok') is True
    except Exception:
        return False


def observe(args):
    state = {'kind': 'native', 'converted': os.path.islink(RUNTIME), 'artifacts': artifacts()}
    if os.path.islink(RUNTIME):
        selected = os.path.basename(os.readlink(RUNTIME).rstrip('/'))
        switched_at = os.lstat(RUNTIME).st_mtime
        previous = open(PREVIOUS).read().strip() if os.path.exists(PREVIOUS) else None
    elif os.path.isdir(RUNTIME):
        digest = closure_digest(RUNTIME)
        selected = release_id(digest)
        state['artifacts'][selected] = digest
        switched_at, previous = None, selected
    else:
        selected, switched_at, previous = None, None, None
    processes = process()
    state['processes'] = processes
    if len(processes) != 1:
        running = None
    elif switched_at is None or processes[0]['started_at'] > switched_at:
        running = selected
    else:
        running = previous
    state.update(selected=selected, running=running, previous=previous, digest=state['artifacts'].get(selected), healthy=health(args['health_url']))
    usage = shutil.disk_usage(path('/opt'))
    state['headroom'] = usage.free >= args['min_free_bytes']
    state['headroom_detail'] = {'free_bytes': usage.free, 'required_bytes': args['min_free_bytes']}
    return state


def guarded(fn):
    os.makedirs(LOCKS, exist_ok=True)
    with open(os.path.join(LOCKS, '.guard'), 'a+') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        return fn()


def read_json(p, default):
    return json.load(open(p)) if os.path.exists(p) else default


def check_token(args):
    record = read_json(os.path.join(LOCKS, 'lock.json'), {})
    if record.get('holder') != args['holder'] or record.get('fencing_token') != args['token'] or record.get('lease_expiry', 0) <= time.time():
        raise PermissionError('stale-token')


def acquire(args):
    def body():
        lock = os.path.join(LOCKS, 'lock.json')
        old = read_json(lock, None)
        if old and old['lease_expiry'] > time.time() and old['holder'] != args['holder']:
            return {'held_by': old['holder']}
        if old and old['holder'] == args['holder'] and old['lease_expiry'] > time.time():
            token = old['fencing_token']
        else:
            counter = os.path.join(LOCKS, 'fence.json')
            token = read_json(counter, {'token': 0})['token'] + 1
            write_atomic(counter, json.dumps({'token': token}))
        record = json.dumps({'holder': args['holder'], 'operation': args['operation'], 'fencing_token': token, 'lease_expiry': time.time() + args['lease_s']})
        if old is None:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as out:
                out.write(record)
                out.flush()
                os.fsync(out.fileno())
            sync_dir(LOCKS)
        else:
            write_atomic(lock, record)
        return {'token': token}
    return guarded(body)


def release(args):
    def body():
        check_token(args)
        os.unlink(os.path.join(LOCKS, 'lock.json'))
        sync_dir(LOCKS)
        return {}
    return guarded(body)


def point_runtime(name):
    link = RUNTIME + '.' + uuid.uuid4().hex
    os.symlink(os.path.join('runtime', name), link)
    os.replace(link, RUNTIME)
    sync_dir(os.path.dirname(RUNTIME))


def restart(args):
    subprocess.run(['rc-service', 'native-stats', 'restart'], check=True, stdout=subprocess.DEVNULL)
    deadline = time.time() + args['health_deadline_s']
    while time.time() < deadline:
        if health(args['health_url']):
            return True
        time.sleep(1)
    raise TimeoutError('native-stats did not become healthy')


def convert(args):
    def body():
        check_token(args)
        if os.path.islink(RUNTIME):
            return {}
        digest = closure_digest(RUNTIME)
        name = release_id(digest)
        os.makedirs(RELEASES, exist_ok=True)
        write_atomic(os.path.join(RUNTIME, 'release.json'), json.dumps({'release': name, 'digest': digest, 'source': 'converted in place'}))
        write_atomic(PREVIOUS, name + '\n')
        target = os.path.join(RELEASES, name)
        os.rename(RUNTIME, target)
        point_runtime(name)
        return {'release': name}
    return guarded(body)


def activate(args):
    def body():
        check_token(args)
        state = observe(args)
        if state['selected'] != args['expected'] or not state['converted']:
            raise ValueError('conditional activation identity mismatch')
        directory = os.path.join(RELEASES, args['release'])
        if release_record(directory)['digest'] != args['digest'] or closure_digest(directory) != args['digest']:
            raise ValueError('staged release digest mismatch')
        write_atomic(PREVIOUS, args['expected'] + '\n')
        point_runtime(args['release'])
        return {}
    guarded(body)
    restart(args)
    return {}


def complete(args):
    guarded(lambda: check_token(args))
    restart(args)
    return {}


def stage(args):
    def body():
        check_token(args)
        os.makedirs(RELEASES, exist_ok=True)
        staging = os.path.join(RELEASES, '.staging-' + uuid.uuid4().hex)
        os.mkdir(staging)
        incoming = path(args['archive'])
        with tarfile.open(incoming) as archive:
            archive.extractall(staging, filter='data')
        if os.path.dirname(incoming) == LOCKS:
            os.unlink(incoming)
        digest = closure_digest(staging)
        name = release_id(digest)
        write_atomic(os.path.join(staging, 'release.json'), json.dumps({'release': name, 'digest': digest, 'source': args['source']}))
        target = os.path.join(RELEASES, name)
        if os.path.exists(target):
            shutil.rmtree(staging)
        else:
            os.rename(staging, target)
            sync_dir(RELEASES)
        return {'release': name, 'digest': digest}
    return guarded(body)


def check(args):
    state = observe(args)
    engine = subprocess.run(['docker', 'inspect', '-f', '{{.State.Running}}', args['engine_container']], capture_output=True, text=True)
    state['engine_running'] = engine.returncode == 0 and engine.stdout.strip() == 'true'
    ok = state['healthy'] and state['engine_running'] and state['selected'] == args['release'] and state['running'] == args['release'] and state['digest'] == args['digest']
    return {'ok': ok, 'state': state}


OPERATIONS = {f.__name__: f for f in (observe, acquire, release, convert, activate, complete, stage, check)}
request = json.loads(sys.stdin.readline())
try:
    result = {'ok': OPERATIONS[request['op']](request['args'])}
except PermissionError as exc:
    result = {'error': 'stale-token', 'detail': str(exc)}
except Exception as exc:
    result = {'error': type(exc).__name__, 'detail': str(exc)}
print(json.dumps(result))
'''


def ssh_runner(ssh_config, host):
    def run(payload):
        command = 'python3 -c ' + shlex.quote(GUEST_SCRIPT)
        result = subprocess.run(['ssh', '-F', str(Path(ssh_config).expanduser()), '-o', 'BatchMode=yes', host, command], input=payload, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise OSError(f'ssh {host} failed: {result.stderr.strip()}')
        return result.stdout
    return run


class NativeAdapter:
    def __init__(self, runner, health_url='http://127.0.0.1:8080/health', engine_container='live-stats-engine', min_free_bytes=1 << 30, health_deadline_s=180):
        self.runner = runner
        self.settings = {'health_url': health_url, 'engine_container': engine_container, 'min_free_bytes': min_free_bytes, 'health_deadline_s': health_deadline_s}

    def call(self, op, **args):
        reply = json.loads(self.runner(json.dumps({'op': op, 'args': {**self.settings, **args}}) + '\n'))
        if reply.get('error') == 'stale-token':
            from oorollout import StaleToken
            raise StaleToken(reply['detail'])
        if 'error' in reply:
            raise ValueError(f"guest {op} failed: {reply['error']}: {reply['detail']}")
        return reply['ok']

    def acquire(self, holder, operation, lease_s):
        result = self.call('acquire', holder=holder, operation=operation, lease_s=lease_s)
        if 'held_by' in result:
            from oorollout import LockHeld
            raise LockHeld(result['held_by'])
        return result['token']

    def release(self, holder, token):
        self.call('release', holder=holder, token=token)

    def observe(self):
        return self.call('observe')

    def preparations(self, config):
        return ['convert-runtime']

    def prepare_observed(self, step):
        return self.observe()['converted']

    def prepare_step(self, holder, token, step):
        self.call('convert', holder=holder, token=token)

    def classify(self, state, expected, release, digest):
        if state['selected'] == release and state['running'] == release and state['digest'] == digest:
            return 'applied'
        if state['selected'] == release and state['running'] in (expected, None) and state['digest'] == digest:
            return 'partial'
        if state['selected'] == expected and state['running'] == expected:
            return 'not-applied'
        return 'ambiguous'

    def activate(self, holder, token, expected, release, digest):
        self.call('activate', holder=holder, token=token, expected=expected, release=release, digest=digest)

    def complete(self, holder, token, state, release, digest):
        self.call('complete', holder=holder, token=token)

    def stage(self, holder, token, archive, source):
        return self.call('stage', holder=holder, token=token, archive=archive, source=source)

    def check(self, release, digest):
        return self.call('check', release=release, digest=digest)
