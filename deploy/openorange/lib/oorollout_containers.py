"""OpenOrange container rollout adapter; guest operations share the SSH script."""
import json
import re
import shlex
import subprocess
from pathlib import Path

import oorollout_native

_native = oorollout_native.GUEST_SCRIPT
GUEST_SCRIPT = _native[:_native.index('RUNTIME =')] + "LOCKS = path('/var/lib/openorange-rollout')\n\n" + _native[_native.index('def sync_dir'): _native.index('def sha(')] + _native[_native.index('GUARD_DEPTH = 0'):_native.index('def point_runtime(')] + r'''

def command(*args, required=True):
    result = subprocess.run(list(args), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    if required and result.returncode:
        raise ValueError('command failed: ' + args[0])
    return result.stdout.strip() if result.returncode == 0 else None


def oo(*args, required=True):
    return command(path('/opt/openorange/bin/oo'), *args, required=required)


def observe(args):
    app = args['app']
    deployment = json.loads(oo('deployment', app))
    selected, version = deployment['image'], deployment['version']
    if not isinstance(selected, str) or not selected or type(version) is not int or version < 1:
        raise ValueError('invalid deployment identity')
    refs = command('docker', 'image', 'ls', '--format', '{{.Repository}}:{{.Tag}}').splitlines()
    artifacts = {}
    for ref in set(refs + [selected]):
        if '<none>' not in ref:
            image_id = command('docker', 'image', 'inspect', '--format', '{{.Id}}', ref, required=False)
            if image_id:
                artifacts[ref] = image_id
    container = 'oo-app-' + app
    identity = command('docker', 'inspect', '--format', '{{.Config.Image}} {{.Image}} {{.State.Running}}', container, required=False)
    parts = identity.split() if identity else []
    ref, image_id, running = parts if len(parts) == 3 else (None, None, None)
    node = command('docker', 'exec', container, 'node', '-p', 'process.env.RIVET_NODE_VERSION', required=False) if running == 'true' else None
    valid = ref == selected and image_id == artifacts.get(selected) and node == str(version) and running == 'true'
    healthy = oo('wait', 'app', app, '1', required=False) is not None
    usage = shutil.disk_usage(path('/'))
    marker = os.path.isfile(path('/var/lib/openorange/deployments/' + app + '/delivered/oo-' + app + '-' + str(version) + '.json'))
    return {'kind': 'oo-containers', 'selected': selected, 'version': version, 'running': ref if running == 'true' else None, 'running_image_id': image_id, 'running_node_version': node, 'digest': artifacts.get(selected), 'artifacts': artifacts, 'healthy': healthy, 'identity_valid': valid, 'marker_delivered': marker, 'recoveryWriter': deployment.get('recoveryWriter'), 'writer_fenced': 'recoveryWriter' in deployment, 'headroom': usage.free >= args['min_free_bytes'], 'headroom_detail': {'free_bytes': usage.free, 'required_bytes': args['min_free_bytes']}}


def finish(args):
    state = observe(args)
    if state['writer_fenced'] or state['selected'] != args['release'] or state['digest'] != args['digest']:
        raise ValueError('activation identity changed')
    if not state['identity_valid']:
        check_token(args)
        command(path('/sbin/rc-service'), 'oo-app.' + args['app'], 'restart')
    deadline = time.time() + args['health_deadline_s']
    while time.time() < deadline:
        state = observe(args)
        if state['writer_fenced'] or state['selected'] != args['release'] or state['digest'] != args['digest']:
            raise ValueError('activation identity changed')
        if state['identity_valid'] and state['healthy']:
            if not state['marker_delivered']:
                check_token(args)
                if oo('record-deployment', args['app'], '--if-current', args['release'], required=False) is None:
                    raise OSError('deployment marker delivery failed')
            return {}
        time.sleep(1)
    raise ValueError('app did not become healthy with the selected identity')


def activate(args):
    def body():
        check_token(args)
        state = observe(args)
        if state['writer_fenced'] or state['selected'] != args['expected'] or not state['identity_valid'] or state['artifacts'].get(args['release']) != args['digest']:
            raise ValueError('conditional activation identity mismatch')
        check_token(args)
        oo('set-image', args['app'], args['release'], '--if-current', args['expected'])
        return finish(args)
    return guarded(body)


def complete(args):
    def body():
        check_token(args)
        return finish(args)
    return guarded(body)


def check(args):
    state = observe(args)
    return {'ok': not state['writer_fenced'] and state['identity_valid'] and state['healthy'] and state['marker_delivered'] and state['selected'] == args['release'] and state['digest'] == args['digest'], 'state': state}


OPERATIONS = {f.__name__: f for f in (observe, acquire, renew, release, activate, complete, check)}
request = json.loads(sys.stdin.readline())
try:
    if request['op'] in ('activate', 'complete') and sys.argv[1:] != ['--internal']:
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
        command = 'doas -n python3 -c ' + shlex.quote(GUEST_SCRIPT)
        result = subprocess.run(['ssh', '-F', str(Path(ssh_config).expanduser()), '-o', 'BatchMode=yes', host, command], input=payload, capture_output=True, text=True, timeout=600)
        if result.returncode:
            raise OSError(f'ssh {host} failed: {result.stderr.strip()}')
        return result.stdout
    return run


class ContainersAdapter(oorollout_native.NativeAdapter):
    def __init__(self, runner, app, min_free_bytes=1 << 30, health_deadline_s=180, bound_s=10):
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,31}', app):
            raise ValueError('invalid app name')
        self.runner = runner
        self.settings = {'bound_s': bound_s, 'app': app, 'min_free_bytes': min_free_bytes, 'health_deadline_s': health_deadline_s}

    def call(self, op, **args):
        reply = json.loads(self.runner(json.dumps({'op': op, 'args': {**self.settings, **args}}) + '\n'))
        if reply.get('error') == 'stale-token':
            from oorollout import StaleToken
            raise StaleToken(reply['detail'])
        if reply.get('error') == 'OSError':
            raise OSError(f"guest {op} failed: {reply['detail']}")
        if 'error' in reply:
            raise ValueError(f"guest {op} failed: {reply['error']}: {reply['detail']}")
        return reply['ok']

    def preparations(self, config):
        return []

    def classify(self, state, expected, release, digest):
        if state['writer_fenced']:
            return 'ambiguous'
        if state['selected'] == release and state['digest'] == digest:
            if state['identity_valid']:
                return 'applied' if state['marker_delivered'] else 'partial'
            if state['running'] == expected and state['running_image_id'] == state['artifacts'].get(expected) and state['running_node_version'] == str(state['version'] - 1):
                return 'partial'
        if state['selected'] == expected and state['running'] == expected and state['identity_valid']:
            return 'not-applied'
        return 'ambiguous'

    def complete(self, holder, token, state, release, digest):
        self.call('complete', holder=holder, token=token, release=release, digest=digest)
