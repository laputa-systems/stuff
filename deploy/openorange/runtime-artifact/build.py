import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
import oomanifest

INPUTS = ('deploy/orange/package.json', 'deploy/orange/pnpm-lock.yaml', 'deploy/orange/pnpm-workspace.yaml')


def sha(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def validate(descriptor, repo):
    if descriptor['schema'] != 'openorange-runtime-build/1' or not re.fullmatch(r'[0-9a-f]{40}', descriptor['stats']['revision']):
        raise ValueError('invalid descriptor revision or schema')
    if not descriptor['stats']['repository'] or set(descriptor['inputs']) != set(INPUTS):
        raise ValueError('invalid descriptor inputs')
    if not re.fullmatch(r'[^@]+@sha256:[0-9a-f]{64}', descriptor['base_image']):
        raise ValueError('invalid base image')
    for key in ('node_version', 'pnpm_version'):
        if not re.fullmatch(r'\d+\.\d+\.\d+', descriptor[key]):
            raise ValueError('invalid ' + key)
    if not re.fullmatch(r'sha512-[A-Za-z0-9+/]{86}==', descriptor['pnpm_integrity']):
        raise ValueError('invalid pnpm integrity')
    inputs = {}
    for path in INPUTS:
        data = subprocess.check_output(['git', '-C', str(repo), 'show', descriptor['stats']['revision'] + ':' + path])
        if sha(data) != descriptor['inputs'][path]:
            raise ValueError('input hash mismatch: ' + path)
        inputs[path] = data
    return inputs


def normalize(root):
    modules = root / 'node_modules/.modules.yaml'
    data = json.loads(modules.read_text())
    data['prunedAt'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
    modules.write_text(json.dumps(data, indent=2) + '\n')
    state = root / 'node_modules/.pnpm-workspace-state-v1.json'
    def clean(value):
        if isinstance(value, dict):
            return {key: 0 if key in ('lastValidatedTimestamp', 'recordedAtNs', 'mtimeNs', 'ctimeNs') else clean(item) for key, item in value.items()}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value
    state.write_text(json.dumps(clean(json.loads(state.read_text())), indent=2) + '\n')


def pack(root, archive):
    value = oomanifest.manifest(root)
    digest = oomanifest.manifest_digest(value)
    with tarfile.open(archive, 'w', format=tarfile.PAX_FORMAT, pax_headers={'openorange.manifest_digest': digest}) as tar:
        for entry in value['entries']:
            path = root / entry['path']
            info = tar.gettarinfo(str(path), arcname=entry['path'])
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ''
            if info.isfile():
                with path.open('rb') as stream:
                    tar.addfile(info, stream)
            else:
                tar.addfile(info)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--descriptor', required=True)
    parser.add_argument('--stats-repo', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    descriptor_bytes = Path(args.descriptor).read_bytes()
    descriptor = json.loads(descriptor_bytes)
    inputs = validate(descriptor, args.stats_repo)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='runtime-build-', dir=out) as temporary:
        work = Path(temporary)
        closure = work / 'closure'
        closure.mkdir()
        for path, data in inputs.items():
            (closure / Path(path).name).write_bytes(data)
        version = descriptor['pnpm_version']
        with urllib.request.urlopen('https://registry.npmjs.org/pnpm/-/pnpm-' + version + '.tgz') as response:
            data = response.read()
        integrity = 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode()
        if integrity != descriptor['pnpm_integrity']:
            raise ValueError('pnpm integrity mismatch')
        (work / 'pnpm.tgz').write_bytes(data)
        script = Path(__file__).with_name('install.sh')
        subprocess.run(['docker', 'run', '--rm', '--platform', 'linux/amd64', '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'HOME=/work/home', '-v', f'{work}:/work', '-v', f'{script}:/install.sh:ro', '-e', 'NODE_VERSION=' + descriptor['node_version'], descriptor['base_image'], 'sh', '/install.sh'], check=True)
        normalize(closure)
        value = pack(closure, out / 'runtime.tar')
    digest = oomanifest.manifest_digest(value)
    (out / 'manifest.json').write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    record = {'schema': 'openorange-runtime-build-record/1', 'descriptor_sha256': sha(descriptor_bytes), 'tools': {'base_image': descriptor['base_image'], 'node_version': descriptor['node_version'], 'pnpm_version': descriptor['pnpm_version'], 'pnpm_integrity': descriptor['pnpm_integrity']}, 'manifest_digest': digest, 'tar_sha256': sha((out / 'runtime.tar').read_bytes()), 'release_id': oomanifest.release_id(digest)}
    (out / 'build.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
