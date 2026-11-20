import hashlib
import json
import re
import shlex
import subprocess
import tomllib
from pathlib import Path


class ValidationError(ValueError):
    pass


def _object(value, keys, where):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValidationError(f'{where}: expected keys {sorted(keys)}')


def _string(value, where):
    if not isinstance(value, str) or not value:
        raise ValidationError(f'{where}: expected nonempty string')


def _digest(value, where):
    if not isinstance(value, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', value):
        raise ValidationError(f'{where}: expected sha256 digest')


def manifest_id(manifest):
    content = {key: value for key, value in manifest.items() if key != 'id'}
    canonical = json.dumps(content, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return 'oor-' + hashlib.sha256(canonical).hexdigest()[:16]


def validate_manifest(manifest):
    keys = {'schema', 'id', 'commits', 'sources', 'lockfiles', 'toolchains', 'build', 'artifacts', 'compatibility', 'previous_release', 'recovery_method'}
    _object(manifest, keys, 'manifest')
    if manifest['schema'] != 'openorange-release-manifest/1':
        raise ValidationError('manifest: invalid schema')
    _object(manifest['commits'], {'stats', 'stuff'}, 'commits')
    for key, value in manifest['commits'].items():
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}', value):
            raise ValidationError(f'commits.{key}: expected full revision')
    if not isinstance(manifest['sources'], list) or not manifest['sources']:
        raise ValidationError('sources: expected nonempty list')
    for source in manifest['sources']:
        _object(source, {'name', 'revision', 'patches'}, 'source')
        _string(source['name'], 'source.name')
        if not isinstance(source['revision'], str) or not re.fullmatch(r'[0-9a-f]{40}', source['revision']):
            raise ValidationError('source.revision: expected full revision')
        if not isinstance(source['patches'], list):
            raise ValidationError('source.patches: expected list')
        for patch in source['patches']:
            _object(patch, {'file', 'sha256'}, 'patch')
            _string(patch['file'], 'patch.file')
            _digest(patch['sha256'], 'patch.sha256')
    for key in ('lockfiles',):
        value = manifest[key]
        if not isinstance(value, dict) or not value:
            raise ValidationError(f'{key}: expected nonempty object')
        for name, digest in value.items():
            _string(name, key)
            _digest(digest, f'{key}.{name}')
    artifacts = manifest['artifacts']
    if not isinstance(artifacts, dict) or not {'packages', 'native_addon', 'executables'} <= artifacts.keys() or artifacts.keys() - {'packages', 'native_addon', 'executables', 'oci'}:
        raise ValidationError('artifacts: expected packages, native_addon, executables and optional oci')
    for kind, entries in artifacts.items():
        if not isinstance(entries, dict) or not entries:
            raise ValidationError(f'artifacts.{kind}: expected nonempty object')
        for name, digest in entries.items():
            _string(name, f'artifacts.{kind}')
            _digest(digest, f'artifacts.{kind}.{name}')
    if not isinstance(manifest['toolchains'], dict) or not manifest['toolchains']:
        raise ValidationError('toolchains: expected nonempty object')
    for name, identity in manifest['toolchains'].items():
        _string(name, 'toolchains')
        _string(identity, f'toolchains.{name}')
    _object(manifest['build'], {'recipe', 'target_arch', 'libc', 'features', 'inspector_ui'}, 'build')
    build = manifest['build']
    for key in ('recipe', 'target_arch', 'libc'):
        _string(build[key], f'build.{key}')
    if not isinstance(build['features'], list) or any(not isinstance(x, str) or not x for x in build['features']) or type(build['inspector_ui']) is not bool:
        raise ValidationError('build: invalid features or inspector_ui')
    _object(manifest['compatibility'], {'config', 'persisted_format'}, 'compatibility')
    for key, value in manifest['compatibility'].items():
        _string(value, f'compatibility.{key}')
    if not isinstance(manifest['previous_release'], str) or not re.fullmatch(r'oor-[0-9a-f]{16}', manifest['previous_release']):
        raise ValidationError('previous_release: expected release id')
    _string(manifest['recovery_method'], 'recovery_method')
    if manifest['id'] != manifest_id(manifest):
        raise ValidationError('manifest: id does not match content')
    return manifest


def ssh_runner(config, host, argv, *, privilege=False):
    command = ['doas', '-n', *argv] if privilege else argv
    result = subprocess.run(['ssh', '-F', str(config), '-o', 'BatchMode=yes', host, shlex.join(command)], text=True, capture_output=True, check=False)
    if result.returncode == 255:
        raise RuntimeError(f'{host}: SSH transport failed')
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, argv)
    return result.stdout.strip()


def inspect(inventory, stats_repo, runner):
    _object(inventory, {'ssh_config', 'hosts'}, 'inventory')
    _string(inventory['ssh_config'], 'ssh_config')
    if not isinstance(inventory['hosts'], dict) or not inventory['hosts']:
        raise ValidationError('hosts: expected nonempty object')
    repo = Path(stats_repo) / 'deploy/orange'
    pins = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in ('package.json', 'pnpm-lock.yaml')}
    result = {'schema': 'openorange-release-inspection/1', 'hosts': {}, 'writer': {'host': None, 'route': None}, 'drift': []}
    drift = result['drift']
    route = None
    for host, spec in inventory['hosts'].items():
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', host):
            raise ValidationError('invalid host alias')
        _object(spec, {'kind', 'writer_address', 'doas', 'engine_container', 'engine_config', 'storage_roots'}, f'hosts.{host}')
        paths = [spec['engine_config'], *spec['storage_roots']] if isinstance(spec['storage_roots'], list) else []
        if not paths or any(not isinstance(path, str) or not path.startswith('/') or '..' in Path(path).parts or 'secret' in path.lower() or '.env' in path.lower() for path in paths):
            raise ValidationError(f'{host}: invalid config or storage paths')
        if not isinstance(spec['engine_container'], str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', spec['engine_container']):
            raise ValidationError(f'{host}: invalid engine container')
        if type(spec['doas']) is not bool:
            raise ValidationError(f'{host}: doas must be boolean')
        if spec['kind'] not in ('oo-containers', 'native'):
            raise ValidationError(f'{host}: invalid topology')
        _string(spec['writer_address'], f'{host}.writer_address')
        out = {'kind': spec['kind'], 'config_sha256': {}, 'durable_storage_roots': [], 'engine_consumers': [], 'engine': {}}
        result['hosts'][host] = out

        def run(*args):
            try:
                return runner(host, list(args))
            except subprocess.CalledProcessError:
                return None

        def identity(label, value):
            if not value:
                drift.append(f'{host}: unknown {label}')
            return value or None

        def checksum(path):
            value = run('sha256sum', path)
            return identity(path + ' sha256', value.split()[0] if value and re.fullmatch(r'[0-9a-f]{64}', value.split()[0]) else None)

        def container(name):
            value = run('docker', 'inspect', '--format', '{{.Image}} {{.Config.Image}}', name)
            parts = value.split() if value else []
            if len(parts) != 2:
                identity(name + ' container image', None)
                return {'image_id': None, 'image_ref': None}
            return {'image_id': parts[0], 'image_ref': parts[1]}

        if spec['kind'] == 'oo-containers':
            raw = run('cat', '/opt/openorange/apps.toml')
            if not raw:
                raise RuntimeError(f'{host}: cannot read apps.toml')
            apps = tomllib.loads(raw).get('apps', {})
            enabled = {name: app for name, app in apps.items() if app.get('enabled', True)}
            out['engine_consumers'] = sorted(name for name, app in enabled.items() if app.get('kind') == 'orange')
            out['deployments'] = {}
            for name, app in enabled.items():
                if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name):
                    raise ValidationError(f'{host}: invalid app name')
                raw_deployment = run('/opt/openorange/bin/oo', 'deployment', name)
                if not raw_deployment:
                    if app.get('kind') == 'orange':
                        identity(name + ' deployment', None)
                    else:
                        out['deployments'][name] = {'selected': None, 'reason': 'native app has no image deployment'}
                    continue
                deployment = json.loads(raw_deployment)
                selected = identity(name + ' selected image', deployment.get('image'))
                if name == 'stats':
                    route = deployment.get('recoveryWriter')
                    out['recovery_writer'] = route
                record = {'selected': selected}
                if app.get('kind') == 'orange' and not (name == 'stats' and route):
                    running = container('oo-app.' + name)
                    record['running'] = running
                    if selected and running['image_id']:
                        selected_id = run('docker', 'image', 'inspect', '--format', '{{.Id}}', selected)
                        if not selected_id:
                            identity(name + ' selected image id', None)
                        elif selected_id != running['image_id']:
                            drift.append(f'{host}: {name} selected image differs from running image')
                out['deployments'][name] = record
            out['durable_storage_roots'] = spec['storage_roots']
            for path in (spec['engine_config'], '/etc/openorange/ingress/Caddyfile'):
                out['config_sha256'][path] = checksum(path)
            names = run('docker', 'ps', '--filter', 'name=oo-', '--format', '{{.Names}}')
            out['containers'] = {name: container(name) for name in names.splitlines()} if names else {}
            identity('running oo containers', out['containers'])
            out['engine'] = container(spec['engine_container'])
            out['engine']['self_report'] = run('docker', 'exec', spec['engine_container'], 'rivet-engine', '--version')
        else:
            out['durable_storage_roots'] = spec['storage_roots']
            out['config_sha256'][spec['engine_config']] = checksum(spec['engine_config'])
            out['engine_consumers'] = ['stats']
            out['runtime_files_sha256'] = {}
            for name in pins:
                value = checksum('/opt/native-rehearsal/orange/' + name)
                out['runtime_files_sha256'][name] = value
                if value and value != pins[name]:
                    drift.append(f'{host}: {name} differs from Stats repository')
            code = "import json,pathlib; p=pathlib.Path('/opt/native-rehearsal/orange/node_modules'); print(json.dumps({n:json.loads((p/n/'package.json').read_text())['version'] for n in ('open-orange','rivetkit')}))"
            versions = run('python3', '-c', code)
            out['package_versions'] = json.loads(versions) if versions else None
            identity('installed package versions', out['package_versions'])
            local_versions = json.loads((repo / 'package.json').read_text())['dependencies']
            if out['package_versions']:
                for name, version in out['package_versions'].items():
                    if version != local_versions.get(name):
                        drift.append(f'{host}: {name} package version differs from Stats repository')
            code = "import hashlib,json,pathlib; p=pathlib.Path('/opt/native-rehearsal/orange/node_modules/@rivetkit'); print(json.dumps({str(x):hashlib.sha256(x.read_bytes()).hexdigest() for d in p.iterdir() for x in d.resolve().rglob('*.node')}))"
            addons = run('python3', '-c', code)
            out['native_addons_sha256'] = json.loads(addons) if addons else {}
            identity('native addon', out['native_addons_sha256'])
            for path in ('/opt/native-rehearsal/app/stats.jsonc', '/opt/native-rehearsal/app/observe.jsonc'):
                out['config_sha256'][path] = checksum(path)
            code = "import pathlib,re; s=pathlib.Path('/opt/native-rehearsal/app/stats.jsonc').read_text(); m=re.search(r'\"APPLICATION_EVENTS_RELEASE\"\\s*:\\s*\"(stats-[0-9a-f]{12})\"',s); print(m.group(1) if m else '')"
            out['release'] = identity('running descriptor release', run('python3', '-c', code))
            out['engine'] = container(spec['engine_container'])
            out['engine']['self_report'] = run('docker', 'exec', spec['engine_container'], 'rivet-engine', '--version')
        image_id = out['engine'].get('image_id')
        digests = run('docker', 'image', 'inspect', '--format', '{{json .RepoDigests}}', image_id) if image_id else None
        out['engine']['repository_digests'] = json.loads(digests) if digests else []
        identity('Engine repository digest', out['engine']['repository_digests'])
    result['writer']['route'] = route
    matches = [host for host, spec in inventory['hosts'].items() if route and spec['writer_address'] == route]
    if len(matches) == 1:
        result['writer']['host'] = matches[0]
    else:
        drift.append('Stats writer unknown: recoveryWriter missing or does not uniquely match inventory')
    return result


def inspection_exit_code(result):
    return 3 if result['drift'] else 0
