"""Rollout adapter for the native standby Stats writer.

Every guest operation runs GUEST_SCRIPT with the guest's python3. Over SSH the
script arrives on stdin; tests run the same script locally with ROOT pointing
at a simulated guest filesystem.
"""
import json
import shlex
import subprocess
from pathlib import Path

GUEST_SCRIPT = Path(__file__).with_name('oomanifest.py').read_text() + r'''
import base64, fcntl, hashlib, json, math, os, shutil, signal, subprocess, sys, tarfile, time, urllib.request, uuid

ROOT = os.environ.get('ROLLOUT_GUEST_ROOT', '/')
BIN = '/opt/native-rehearsal/orange/node_modules/open-orange/dist/bin.js'


def path(p):
    return os.path.join(ROOT, p.lstrip('/'))


RUNTIME = path('/opt/native-rehearsal/orange')
RELEASES = path('/opt/native-rehearsal/runtime')
PREVIOUS = os.path.join(RELEASES, '.previous')
APP = path('/opt/native-rehearsal/app')
APP_CURRENT = os.path.join(APP, 'current')
APPS = path('/opt/native-rehearsal/apps')
APP_PREVIOUS = os.path.join(APPS, '.previous')
APP_LINKED = ('observe', 'observe.jsonc', 'stats', 'stats.jsonc')
COLLECTOR = path('/opt/stats-infra-collector')
COLLECTOR_LINK = 'native-rehearsal/app/current/collector'
COLLECTOR_MAIN = '/opt/stats-infra-collector/main.mjs'
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


def release_record(directory):
    with open(os.path.join(directory, 'release.json')) as f:
        return json.load(f)


def artifacts(releases=RELEASES, prefix='rt-'):
    found = {}
    if os.path.isdir(releases):
        for name in sorted(os.listdir(releases)):
            directory = os.path.join(releases, name)
            if name.startswith(prefix) and os.path.isfile(os.path.join(directory, 'release.json')):
                found[name] = release_record(directory)['digest']
    return found


def process(script=BIN):
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
        if argv and os.path.basename(argv[0]) == b'node' and len(argv) > 1 and argv[1] == script.encode():
            matches.append({'pid': int(pid), 'started_at': btime + int(fields[19]) / ticks})
    return matches


def health(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return response.status == 200 and json.load(response).get('ok') is True
    except Exception:
        return False


def observe_runtime(args):
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
    digest = closure_digest(os.path.join(RELEASES, selected)) if os.path.islink(RUNTIME) and selected in state['artifacts'] else state['artifacts'].get(selected)
    state.update(selected=selected, running=running, previous=previous, digest=digest, healthy=health(args['health_url']))
    usage = shutil.disk_usage(path('/opt'))
    state['headroom'] = usage.free >= args['min_free_bytes']
    state['headroom_detail'] = {'free_bytes': usage.free, 'required_bytes': args['min_free_bytes']}
    return state


GUARD_DEPTH = 0


def guarded(fn):
    global GUARD_DEPTH
    if GUARD_DEPTH:
        return fn()
    os.makedirs(LOCKS, exist_ok=True)
    with open(os.path.join(LOCKS, '.guard'), 'a+') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        GUARD_DEPTH = 1
        try:
            return fn()
        finally:
            GUARD_DEPTH = 0


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


def renew(args):
    def body():
        check_token(args)
        lock = os.path.join(LOCKS, 'lock.json')
        record = read_json(lock, {})
        record['lease_expiry'] = time.time() + args['lease_s']
        write_atomic(lock, json.dumps(record))
        return {'token': args['token']}
    return guarded(body)


def release(args):
    def body():
        check_token(args)
        os.unlink(os.path.join(LOCKS, 'lock.json'))
        sync_dir(LOCKS)
        return {}
    return guarded(body)


def check_bound(args):
    check_token(args)
    record = read_json(os.path.join(LOCKS, 'lock.json'), {})
    if record['lease_expiry'] - time.time() < args['bound_s'] + 1:
        raise ValueError('insufficient-lease')


def bounded(request):
    args = request['args']
    bound = args['bound_s']
    if type(bound) not in (int, float) or not math.isfinite(bound) or bound <= 0:
        raise ValueError('invalid bound')
    child = subprocess.Popen([sys.executable, '-c', sys.orig_argv[2], '--internal'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        output, error = child.communicate(json.dumps(request) + '\n', timeout=bound)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.communicate()
        raise TimeoutError('mutation timed out')
    if child.returncode:
        raise OSError('mutation process failed: ' + error)
    return json.loads(output)


def point_runtime(name):
    link = RUNTIME + '.' + uuid.uuid4().hex
    os.symlink(os.path.join('runtime', name), link)
    os.replace(link, RUNTIME)
    sync_dir(os.path.dirname(RUNTIME))


def restart(args):
    check_token(args)
    subprocess.run(['rc-service', 'native-stats', 'restart'], check=True, stdout=subprocess.DEVNULL)
    deadline = time.time() + args['health_deadline_s']
    while time.time() < deadline:
        if health(args['health_url']):
            return True
        time.sleep(1)
    raise TimeoutError('native-stats did not become healthy')


def convert_runtime(args):
    def body():
        check_token(args)
        if os.path.islink(RUNTIME):
            return {}
        digest = closure_digest(RUNTIME)
        name = release_id(digest)
        check_token(args)
        os.makedirs(RELEASES, exist_ok=True)
        write_atomic(os.path.join(RUNTIME, 'release.json'), json.dumps({'release': name, 'digest': digest, 'source': 'converted in place'}))
        write_atomic(PREVIOUS, name + '\n')
        target = os.path.join(RELEASES, name)
        os.rename(RUNTIME, target)
        point_runtime(name)
        return {'release': name}
    return guarded(body)


def activate_runtime(args):
    def body():
        check_token(args)
        state = observe_runtime(args)
        if state['selected'] != args['expected'] or not state['converted']:
            raise ValueError('conditional activation identity mismatch')
        directory = os.path.join(RELEASES, args['release'])
        if closure_digest(directory) != args['digest']:
            raise ValueError('staged-content-mismatch')
        check_token(args)
        write_atomic(PREVIOUS, args['expected'] + '\n')
        point_runtime(args['release'])
        return {}
    guarded(body)
    restart(args)
    return {}


def complete_runtime(args):
    def body():
        check_token(args)
        if closure_digest(os.path.join(RELEASES, args['release'])) != args['digest']:
            raise ValueError('staged-content-mismatch')
    guarded(body)
    restart(args)
    return {}


def run_command(args):
    check_token(args)
    result = subprocess.run(args['argv'], capture_output=True)
    return {'returncode': result.returncode, 'stdout': base64.b64encode(result.stdout).decode('ascii'), 'stderr': base64.b64encode(result.stderr).decode('ascii')}


def stage_runtime(args):
    def body():
        check_token(args)
        os.makedirs(RELEASES, exist_ok=True)
        staging = os.path.join(RELEASES, '.staging-' + uuid.uuid4().hex)
        os.mkdir(staging)
        incoming = path(args['archive'])
        try:
            with tarfile.open(incoming) as archive:
                declared = archive.pax_headers.get('openorange.manifest_digest')
                archive.extractall(staging, filter='data')
            digest = closure_digest(staging)
            if digest != declared:
                raise ValueError('artifact manifest digest mismatch')
        except Exception:
            shutil.rmtree(staging)
            raise
        finally:
            if os.path.dirname(incoming) == LOCKS and os.path.exists(incoming):
                os.unlink(incoming)
        name = release_id(digest)
        write_atomic(os.path.join(staging, 'release.json'), json.dumps({'release': name, 'digest': digest, 'source': args['source']}))
        target = os.path.join(RELEASES, name)
        if os.path.exists(target):
            shutil.rmtree(staging)
            if closure_digest(target) != digest:
                raise ValueError('staged-content-mismatch')
        else:
            os.rename(staging, target)
            sync_dir(RELEASES)
        return {'release': name, 'digest': digest}
    return guarded(body)


def engine_running(args):
    engine = subprocess.run(['docker', 'inspect', '-f', '{{.State.Running}}', args['engine_container']], capture_output=True, text=True)
    return engine.returncode == 0 and engine.stdout.strip() == 'true'


def check_runtime(args):
    state = observe_runtime(args)
    state['engine_running'] = engine_running(args)
    ok = state['healthy'] and state['engine_running'] and state['selected'] == args['release'] and state['running'] == args['release'] and state['digest'] == args['digest']
    return {'ok': ok, 'state': state}


def app_inplace_parts():
    parts = {name: os.path.join(APP, name) for name in APP_LINKED}
    parts['collector'] = COLLECTOR
    return parts


def app_converted():
    linked = all(os.path.islink(os.path.join(APP, name)) and os.readlink(os.path.join(APP, name)) == 'current/' + name for name in APP_LINKED)
    return os.path.islink(APP_CURRENT) and linked and os.path.islink(COLLECTOR) and os.readlink(COLLECTOR) == COLLECTOR_LINK


def selected_runtime_digest():
    if os.path.islink(RUNTIME):
        return artifacts().get(os.path.basename(os.readlink(RUNTIME).rstrip('/')))
    return closure_digest(RUNTIME) if os.path.isdir(RUNTIME) else None


def running_identity(processes, selected, switched_at, previous):
    if len(processes) != 1:
        return None
    return selected if switched_at is None or processes[0]['started_at'] > switched_at else previous


def observe_app(args):
    found = artifacts(APPS, 'app-')
    state = {'kind': 'native-app', 'converted': app_converted(), 'artifacts': found}
    if os.path.islink(APP_CURRENT):
        selected = os.path.basename(os.readlink(APP_CURRENT).rstrip('/'))
        switched_at = os.lstat(APP_CURRENT).st_mtime
        previous = open(APP_PREVIOUS).read().strip() if os.path.exists(APP_PREVIOUS) else None
        digest = app_digest(os.path.join(APPS, selected)) if selected in found else None
    elif all(os.path.exists(p) for p in app_inplace_parts().values()):
        digest = manifest_digest(app_manifest(app_inplace_parts()))
        selected = app_release_id(digest)
        found[selected] = digest
        switched_at, previous = None, selected
    else:
        selected, switched_at, previous, digest = None, None, None, None
    processes = process()
    collectors = process(COLLECTOR_MAIN)
    state.update(selected=selected, running=running_identity(processes, selected, switched_at, previous), previous=previous, digest=digest, processes=processes, collector_processes=collectors, collector_running=running_identity(collectors, selected, switched_at, previous), components={'runtime': selected_runtime_digest()}, healthy=health(args['health_url']))
    usage = shutil.disk_usage(path('/opt'))
    state['headroom'] = usage.free >= args['min_free_bytes']
    state['headroom_detail'] = {'free_bytes': usage.free, 'required_bytes': args['min_free_bytes']}
    return state


def point_app(name):
    link = APP_CURRENT + '.' + uuid.uuid4().hex
    os.symlink(os.path.join('..', 'apps', name), link)
    os.replace(link, APP_CURRENT)
    sync_dir(APP)


def replace_with_link(p, target):
    if os.path.islink(p) and os.readlink(p) == target:
        return
    old = None
    if os.path.lexists(p):
        old = os.path.join(os.path.dirname(p), '.converted-' + os.path.basename(p) + '-' + uuid.uuid4().hex)
        os.rename(p, old)
    link = p + '.' + uuid.uuid4().hex
    os.symlink(target, link)
    os.replace(link, p)
    sync_dir(os.path.dirname(p))
    if old is not None:
        if os.path.isdir(old) and not os.path.islink(old):
            shutil.rmtree(old)
        else:
            os.unlink(old)


def convert_app(args):
    def body():
        check_token(args)
        if app_converted():
            return {}
        os.makedirs(APPS, exist_ok=True)
        if os.path.islink(APP_CURRENT):
            name = os.path.basename(os.readlink(APP_CURRENT).rstrip('/'))
        else:
            digest = manifest_digest(app_manifest(app_inplace_parts()))
            name = app_release_id(digest)
            target = os.path.join(APPS, name)
            if not os.path.exists(target):
                staging = os.path.join(APPS, '.staging-' + uuid.uuid4().hex)
                os.mkdir(staging)
                for part, source in app_inplace_parts().items():
                    source = os.path.realpath(source)
                    if os.path.isdir(source):
                        shutil.copytree(source, os.path.join(staging, part), symlinks=True)
                    else:
                        shutil.copy2(source, os.path.join(staging, part))
                if app_digest(staging) != digest:
                    shutil.rmtree(staging)
                    raise ValueError('in-place app changed during conversion')
                write_atomic(os.path.join(staging, 'release.json'), json.dumps({'release': name, 'digest': digest, 'source': 'converted in place'}))
                os.rename(staging, target)
                sync_dir(APPS)
            elif app_digest(target) != digest:
                raise ValueError('staged-content-mismatch')
            check_token(args)
            write_atomic(APP_PREVIOUS, name + '\n')
            point_app(name)
        check_token(args)
        for part in APP_LINKED:
            replace_with_link(os.path.join(APP, part), 'current/' + part)
        replace_with_link(COLLECTOR, COLLECTOR_LINK)
        return {'release': name}
    return guarded(body)


def restart_app(args):
    check_token(args)
    subprocess.run(['rc-service', 'native-stats', 'restart'], check=True, stdout=subprocess.DEVNULL)
    deadline = time.time() + args['health_deadline_s']
    while time.time() < deadline:
        state = observe_app(args)
        if state['healthy'] and state['running'] == args['release'] and state['collector_running'] == args['release']:
            return True
        time.sleep(1)
    raise TimeoutError('native-stats or its collector did not become healthy on ' + args['release'])


def activate_app(args):
    def body():
        check_token(args)
        state = observe_app(args)
        if state['selected'] != args['expected'] or not state['converted']:
            raise ValueError('conditional activation identity mismatch')
        if app_digest(os.path.join(APPS, args['release'])) != args['digest']:
            raise ValueError('staged-content-mismatch')
        check_token(args)
        write_atomic(APP_PREVIOUS, args['expected'] + '\n')
        point_app(args['release'])
        return {}
    guarded(body)
    restart_app(args)
    return {}


def complete_app(args):
    def body():
        check_token(args)
        if app_digest(os.path.join(APPS, args['release'])) != args['digest']:
            raise ValueError('staged-content-mismatch')
    guarded(body)
    restart_app(args)
    return {}


def stage_app(args):
    def body():
        check_token(args)
        os.makedirs(APPS, exist_ok=True)
        staging = os.path.join(APPS, '.staging-' + uuid.uuid4().hex)
        os.mkdir(staging)
        incoming = path(args['archive'])
        try:
            with tarfile.open(incoming) as archive:
                declared = archive.pax_headers.get('openorange.manifest_digest')
                archive.extractall(staging, filter='data')
            digest = app_digest(staging)
            if digest != declared:
                raise ValueError('artifact manifest digest mismatch')
        except Exception:
            shutil.rmtree(staging)
            raise
        finally:
            if os.path.dirname(incoming) == LOCKS and os.path.exists(incoming):
                os.unlink(incoming)
        name = app_release_id(digest)
        write_atomic(os.path.join(staging, 'release.json'), json.dumps({'release': name, 'digest': digest, 'source': args['source']}))
        target = os.path.join(APPS, name)
        if os.path.exists(target):
            shutil.rmtree(staging)
            if app_digest(target) != digest:
                raise ValueError('staged-content-mismatch')
        else:
            os.rename(staging, target)
            sync_dir(APPS)
        return {'release': name, 'digest': digest}
    return guarded(body)


def check_app(args):
    state = observe_app(args)
    state['engine_running'] = engine_running(args)
    identity = state['selected'] == args['release'] and state['running'] == args['release'] and state['collector_running'] == args['release'] and state['digest'] == args['digest']
    return {'ok': state['healthy'] and state['engine_running'] and identity, 'state': state}


COMPONENTS = {
    'runtime': {'observe': observe_runtime, 'convert': convert_runtime, 'activate': activate_runtime, 'complete': complete_runtime, 'stage': stage_runtime, 'check': check_runtime},
    'app': {'observe': observe_app, 'convert': convert_app, 'activate': activate_app, 'complete': complete_app, 'stage': stage_app, 'check': check_app},
}


def operation(op):
    if op in ('acquire', 'renew', 'release', 'run_command'):
        return {'acquire': acquire, 'renew': renew, 'release': release, 'run_command': run_command}[op]
    return lambda args: COMPONENTS[args['component']][op](args)


OPERATIONS = {op: operation(op) for op in ('observe', 'acquire', 'renew', 'release', 'convert', 'activate', 'complete', 'stage', 'check', 'run_command')}
request = json.loads(sys.stdin.readline())
try:
    if request['op'] in ('convert', 'activate', 'complete', 'stage', 'run_command') and sys.argv[1:] != ['--internal']:
        result = bounded(request)
    else:
        if sys.argv[1:] == ['--internal']:
            def act():
                check_bound(request['args'])
                return OPERATIONS[request['op']](request['args'])
            result = {'ok': guarded(act)}
        else:
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
        request = json.loads(payload)
        timeout = max(600, request['args'].get('bound_s', 0) + 30)
        result = subprocess.run(['ssh', '-F', str(Path(ssh_config).expanduser()), '-o', 'BatchMode=yes', host, command], input=payload, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            raise OSError(f'ssh {host} failed: {result.stderr.strip()}')
        return result.stdout
    return run


PREPARATIONS = {'runtime': 'convert-runtime', 'app': 'convert-app'}


class NativeAdapter:
    def __init__(self, runner, component, health_url='http://127.0.0.1:8080/health', engine_container='live-stats-engine', min_free_bytes=1 << 30, health_deadline_s=180, bound_s=240):
        if component not in PREPARATIONS:
            raise ValueError('unknown native component: ' + str(component))
        self.runner = runner
        self.component = component
        self.settings = {'component': component, 'bound_s': bound_s, 'health_url': health_url, 'engine_container': engine_container, 'min_free_bytes': min_free_bytes, 'health_deadline_s': health_deadline_s}

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

    def renew(self, holder, token, lease_s):
        return self.call('renew', holder=holder, token=token, lease_s=lease_s)['token']

    def release(self, holder, token):
        self.call('release', holder=holder, token=token)

    def observe(self):
        return self.call('observe')

    def preparations(self, config):
        return [PREPARATIONS[self.component]]

    def prepare_observed(self, step):
        return self.observe()['converted']

    def prepare_step(self, holder, token, step):
        self.call('convert', holder=holder, token=token)

    def classify(self, state, expected, release, digest):
        collector = state['collector_running'] if self.component == 'app' else release
        if state['selected'] == release and state['running'] == release and collector == release and state['digest'] == digest:
            return 'applied'
        if state['selected'] == release and state['running'] in (expected, release, None) and state['digest'] == digest:
            return 'partial'
        if state['selected'] == expected and state['running'] == expected:
            return 'not-applied'
        return 'ambiguous'

    def activate(self, holder, token, expected, release, digest):
        self.call('activate', holder=holder, token=token, expected=expected, release=release, digest=digest)

    def complete(self, holder, token, state, release, digest):
        self.call('complete', holder=holder, token=token, release=release, digest=digest)

    def stage(self, holder, token, archive, source):
        return self.call('stage', holder=holder, token=token, archive=archive, source=source)

    def check(self, release, digest):
        return self.call('check', release=release, digest=digest)
