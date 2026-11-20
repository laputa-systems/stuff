import hashlib
import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

import oorelease

ROOT = Path(__file__).resolve().parent.parent


def run(argv, cwd=None, env=None):
    return subprocess.run(argv, cwd=cwd, env=env, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def component():
    registry = tomllib.loads((ROOT / 'sources/sources.toml').read_text())
    items = [x for x in registry['components'] if x['name'] == 'open-orange']
    if len(items) != 1:
        raise ValueError('expected one open-orange component')
    item = items[0]
    for patch in item['patches']:
        if digest(ROOT / 'patches' / patch['file']) != 'sha256:' + patch['sha256']:
            raise ValueError('patch sha256 mismatch: ' + patch['file'])
    return item


def toolchain(src, runner=run):
    package = json.loads((src / 'package.json').read_text())
    required_pnpm = package['packageManager']
    required_node = package['engines']['node']
    match = re.fullmatch(r'>=(\d+)', required_node)
    if not match or not re.fullmatch(r'pnpm@\d+\.\d+\.\d+', required_pnpm):
        raise ValueError('unsupported upstream Node or pnpm requirement')
    node = runner(['node', '--version'], cwd=src).removeprefix('v')
    pnpm = runner(['pnpm', '--version'], cwd=src)
    if not re.fullmatch(r'\d+\.\d+\.\d+', node) or int(node.split('.')[0]) < int(match.group(1)) or 'pnpm@' + pnpm != required_pnpm:
        raise ValueError(f'required Node {required_node} and {required_pnpm}; found Node {node} and pnpm@{pnpm}')
    return node, pnpm


def downstream_version(version, patches):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version) or not patches:
        raise ValueError('expected upstream release version and downstream patches')
    return f'{version}-laputa.{len(patches)}'


def acquire(out, runner=run):
    item = component()
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    src = out / 'source'
    src.mkdir()
    runner(['git', 'init', '-q', str(src)])
    runner(['git', 'fetch', '--depth', '1', item['upstream'], item['revision']], cwd=src)
    actual = runner(['git', 'rev-parse', 'FETCH_HEAD'], cwd=src)
    if actual != item['revision']:
        raise ValueError(f'fetched revision {actual} differs from {item["revision"]}')
    runner(['git', 'checkout', '-q', '--detach', actual], cwd=src)
    for patch in item['patches']:
        path = str(ROOT / 'patches' / patch['file'])
        runner(['git', 'apply', '--check', path], cwd=src)
        runner(['git', 'apply', path], cwd=src)
    toolchain(src, runner)
    store = str(out / 'store')
    runner(['pnpm', 'fetch', '--frozen-lockfile', '--store-dir', store], cwd=src)
    runner(['pnpm', 'install', '--offline', '--frozen-lockfile', '--store-dir', store], cwd=src)


def validate_record(record):
    oorelease._object(record, {'schema', 'component', 'upstream', 'patches', 'lockfile_sha256', 'node', 'pnpm', 'source_date_epoch', 'platform', 'tarball', 'downstream_version'}, 'build record')
    if record['schema'] != 'openorange-build-record/1' or record['component'] != 'open-orange':
        raise ValueError('invalid build record identity')
    oorelease._object(record['upstream'], {'repository', 'revision'}, 'upstream')
    oorelease._string(record['upstream']['repository'], 'upstream.repository')
    if not re.fullmatch(r'[0-9a-f]{40}', record['upstream']['revision']):
        raise ValueError('invalid upstream revision')
    if not isinstance(record['patches'], list) or not record['patches']:
        raise ValueError('expected patches')
    for patch in record['patches']:
        oorelease._object(patch, {'file', 'sha256'}, 'patch')
        oorelease._string(patch['file'], 'patch.file')
        oorelease._digest(patch['sha256'], 'patch.sha256')
    oorelease._digest(record['lockfile_sha256'], 'lockfile_sha256')
    for key in ('node', 'pnpm', 'platform', 'downstream_version'):
        oorelease._string(record[key], key)
    if type(record['source_date_epoch']) is not int or record['source_date_epoch'] < 0:
        raise ValueError('invalid source_date_epoch')
    oorelease._object(record['tarball'], {'file', 'sha256'}, 'tarball')
    oorelease._string(record['tarball']['file'], 'tarball.file')
    oorelease._digest(record['tarball']['sha256'], 'tarball.sha256')
    return record


def build(src, out, runner=run):
    item = component()
    root = Path(src).resolve()
    source, store = root / 'source', root / 'store'
    if not store.is_dir():
        raise ValueError('offline build requires the acquired store')
    if runner(['git', 'rev-parse', 'HEAD'], cwd=source) != item['revision']:
        raise ValueError('source revision differs from registry')
    for patch in item['patches']:
        runner(['git', 'apply', '--reverse', '--check', str(ROOT / 'patches' / patch['file'])], cwd=source)
    node, pnpm = toolchain(source, runner)
    epoch = int(runner(['git', 'show', '-s', '--format=%ct', item['revision']], cwd=source))
    package_path = source / 'package.json'
    original = package_path.read_text()
    package = json.loads(original)
    version = downstream_version(package['version'], item['patches'])
    output = Path(out).resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, SOURCE_DATE_EPOCH=str(epoch), npm_config_offline='true')
    try:
        runner(['pnpm', 'install', '--offline', '--frozen-lockfile', '--store-dir', str(store)], cwd=source, env=env)
        runner(['pnpm', 'build'], cwd=source, env=env)
        package_path.write_text(re.sub(r'("version"\s*:\s*)' + re.escape(json.dumps(package['version'])), lambda m: m.group(1) + json.dumps(version), original, count=1))
        runner(['pnpm', 'pack', '--pack-destination', str(output)], cwd=source, env=env)
    finally:
        package_path.write_text(original)
    archives = list(output.glob('*.tgz'))
    if len(archives) != 1:
        raise ValueError('expected exactly one packed tarball')
    archive = archives[0]
    record = {'schema': 'openorange-build-record/1', 'component': item['name'], 'upstream': {'repository': item['upstream'], 'revision': item['revision']}, 'patches': [{'file': p['file'], 'sha256': 'sha256:' + p['sha256']} for p in item['patches']], 'lockfile_sha256': digest(source / 'pnpm-lock.yaml'), 'node': node, 'pnpm': pnpm, 'source_date_epoch': epoch, 'platform': 'JavaScript package; build uses platform-specific esbuild, no native binaries packaged', 'tarball': {'file': archive.name, 'sha256': digest(archive)}, 'downstream_version': version}
    validate_record(record)
    (output / 'build-record.json').write_text(json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False) + '\n')
    print(f'{record["tarball"]["sha256"]}  {archive}')
