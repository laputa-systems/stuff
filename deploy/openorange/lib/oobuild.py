import base64
import hashlib
import json
import os
import re
import subprocess
import tarfile
import tomllib
import urllib.request
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


def requirements(src, runner=run):
    package = json.loads((src / 'package.json').read_text())
    required_pnpm = package['packageManager']
    required_node = package['engines']['node']
    match = re.fullmatch(r'>=(\d+)', required_node)
    if not match or not re.fullmatch(r'pnpm@\d+\.\d+\.\d+', required_pnpm):
        raise ValueError('unsupported upstream Node or pnpm requirement')
    node = runner(['node', '--version'], cwd=src).removeprefix('v')
    if not re.fullmatch(r'\d+\.\d+\.\d+', node) or int(node.split('.')[0]) < int(match.group(1)):
        raise ValueError(f'required Node {required_node} and {required_pnpm}; found Node {node}')
    return node, required_pnpm.removeprefix('pnpm@')


def integrity(data):
    return 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode('ascii')


def acquire_pnpm(root, version):
    with urllib.request.urlopen('https://registry.npmjs.org/pnpm/' + version) as response:
        metadata = json.load(response)
    if metadata['name'] != 'pnpm' or metadata['version'] != version:
        raise ValueError('pnpm registry identity mismatch')
    expected = metadata['dist']['integrity']
    with urllib.request.urlopen(metadata['dist']['tarball']) as response:
        data = response.read()
    if integrity(data) != expected:
        raise ValueError('pnpm tarball integrity mismatch')
    toolchain = root / 'toolchain'
    toolchain.mkdir()
    archive_path = toolchain / 'pnpm.tgz'
    archive_path.write_bytes(data)
    (toolchain / 'integrity').write_text(expected + '\n')
    destination = toolchain / 'pnpm'
    destination.mkdir()
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive:
            parts = Path(member.name).parts
            if not parts or parts[0] != 'package' or any(x in ('.', '..') for x in parts) or not (member.isfile() or member.isdir()):
                raise ValueError('invalid pnpm archive member')
            target = destination.joinpath(*parts[1:])
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open('wb') as output:
                    output.write(source.read())
                target.chmod(member.mode & 0o777)
    bin_dir = toolchain / 'bin'
    bin_dir.mkdir()
    (bin_dir / 'pnpm').symlink_to('../pnpm/bin/pnpm.cjs')


def pnpm_environment(root, **extra):
    return dict(os.environ, PATH=str(root / 'toolchain/bin') + os.pathsep + os.environ.get('PATH', ''), npm_config_manage_package_manager_versions='false', COREPACK_ENABLE_STRICT='0', **extra)


def toolchain(root, src, runner=run):
    node, required_pnpm = requirements(src, runner)
    tool = root / 'toolchain'
    expected = (tool / 'integrity').read_text().strip()
    if integrity((tool / 'pnpm.tgz').read_bytes()) != expected:
        raise ValueError('acquired pnpm tarball integrity mismatch')
    command = ['node', str(tool / 'pnpm/bin/pnpm.cjs')]
    pnpm = runner([*command, '--version'], cwd=src, env=pnpm_environment(root))
    if pnpm != required_pnpm:
        raise ValueError(f'required Node {node} and pnpm@{required_pnpm}; found pnpm@{pnpm}')
    return node, pnpm, expected, command


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
    _, required_pnpm = requirements(src, runner)
    acquire_pnpm(out, required_pnpm)
    _, _, _, command = toolchain(out, src, runner)
    env = pnpm_environment(out)
    store = str(out / 'store')
    runner([*command, 'fetch', '--frozen-lockfile', '--store-dir', store], cwd=src, env=env)
    runner([*command, 'install', '--offline', '--frozen-lockfile', '--store-dir', store], cwd=src, env=env)


def validate_record(record):
    oorelease._object(record, {'schema', 'component', 'upstream', 'patches', 'lockfile_sha256', 'node', 'pnpm', 'pnpm_integrity', 'source_date_epoch', 'platform', 'tarball', 'downstream_version'}, 'build record')
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
    if not isinstance(record['pnpm_integrity'], str) or not re.fullmatch(r'sha512-[A-Za-z0-9+/]{86}==', record['pnpm_integrity']):
        raise ValueError('invalid pnpm integrity')
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
    node, pnpm, pnpm_integrity, command = toolchain(root, source, runner)
    epoch = int(runner(['git', 'show', '-s', '--format=%ct', item['revision']], cwd=source))
    package_path = source / 'package.json'
    original = package_path.read_text()
    package = json.loads(original)
    version = downstream_version(package['version'], item['patches'])
    output = Path(out).resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = pnpm_environment(root, SOURCE_DATE_EPOCH=str(epoch), npm_config_offline='true')
    try:
        runner([*command, 'install', '--offline', '--frozen-lockfile', '--store-dir', str(store)], cwd=source, env=env)
        runner([*command, 'build'], cwd=source, env=env)
        package_path.write_text(re.sub(r'("version"\s*:\s*)' + re.escape(json.dumps(package['version'])), lambda m: m.group(1) + json.dumps(version), original, count=1))
        runner([*command, 'pack', '--pack-destination', str(output)], cwd=source, env=env)
    finally:
        package_path.write_text(original)
    archives = list(output.glob('*.tgz'))
    if len(archives) != 1:
        raise ValueError('expected exactly one packed tarball')
    archive = archives[0]
    record = {'schema': 'openorange-build-record/1', 'component': item['name'], 'upstream': {'repository': item['upstream'], 'revision': item['revision']}, 'patches': [{'file': p['file'], 'sha256': 'sha256:' + p['sha256']} for p in item['patches']], 'lockfile_sha256': digest(source / 'pnpm-lock.yaml'), 'node': node, 'pnpm': pnpm, 'pnpm_integrity': pnpm_integrity, 'source_date_epoch': epoch, 'platform': 'JavaScript package; build uses platform-specific esbuild, no native binaries packaged', 'tarball': {'file': archive.name, 'sha256': digest(archive)}, 'downstream_version': version}
    validate_record(record)
    (output / 'build-record.json').write_text(json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False) + '\n')
    print(f'{record["tarball"]["sha256"]}  {archive}')


ENGINE_BUILDER = 'ghcr.io/rivet-dev/rivet/engine-base-builder@sha256:61ba0bec231a20ebe8501be2d26b4649bbb74f31353d0ea8740785ee467d5d11'


def engine_component():
    registry = tomllib.loads((ROOT / 'sources/sources.toml').read_text())
    items = [x for x in registry['components'] if x['name'] == 'rivet-engine-source']
    if len(items) != 1 or len(items[0]['patches']) != 6:
        raise ValueError('expected one Engine component with six patches')
    item = items[0]
    for patch in item['patches']:
        if digest(ROOT / 'patches' / patch['file']) != 'sha256:' + patch['sha256']:
            raise ValueError('patch sha256 mismatch: ' + patch['file'])
    return item


def acquire_engine(out, runner=run):
    item = engine_component()
    root = Path(out).resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = root / 'source'
    source.mkdir()
    runner(['git', 'init', '-q', str(source)])
    runner(['git', 'fetch', '--depth', '1', item['upstream'], item['revision']], cwd=source)
    if runner(['git', 'rev-parse', 'FETCH_HEAD'], cwd=source) != item['revision']:
        raise ValueError('fetched Engine revision differs from registry')
    runner(['git', 'checkout', '-q', '--detach', item['revision']], cwd=source)
    for patch in item['patches']:
        path = str(ROOT / 'patches' / patch['file'])
        runner(['git', 'apply', '--check', path], cwd=source)
        runner(['git', 'apply', path], cwd=source)
    toolchain = root / 'rustup'
    toolchain.mkdir()
    runner(['docker', 'run', '--rm', '--platform', 'linux/amd64', '--cpus', '4', '--memory', '8g', '-v', f'{source}:/src', '-v', f'{toolchain}:/usr/local/rustup', '-w', '/src', ENGINE_BUILDER, 'sh', '-c', 'rustc --version && cargo vendor --locked /src/cargo-vendor > vendor-config.toml'])


def validate_engine_record(record):
    oorelease._object(record, {'schema', 'component', 'upstream', 'patches', 'lockfile_sha256', 'builder', 'rustc', 'source_date_epoch', 'platform', 'rustflags', 'jobs', 'memory_bytes', 'binary'}, 'Engine build record')
    item = engine_component()
    if record['schema'] != 'rivet-engine-build-record/1' or record['component'] != item['name']:
        raise ValueError('invalid Engine build record identity')
    if record['upstream'] != {'repository': item['upstream'], 'revision': item['revision']}:
        raise ValueError('invalid Engine upstream identity')
    if record['patches'] != [{'file': p['file'], 'sha256': 'sha256:' + p['sha256']} for p in item['patches']]:
        raise ValueError('invalid Engine patches')
    oorelease._digest(record['lockfile_sha256'], 'lockfile_sha256')
    if record['builder'] != ENGINE_BUILDER or record['platform'] != 'linux-x86_64' or record['rustflags'] != '--cfg tokio_unstable' or type(record['jobs']) is not int or record['jobs'] != 4 or type(record['memory_bytes']) is not int or record['memory_bytes'] != 8589934592:
        raise ValueError('invalid Engine build environment')
    if not isinstance(record['rustc'], str) or 'release: 1.99.0' not in record['rustc'].splitlines() or 'host: x86_64-unknown-linux-gnu' not in record['rustc'].splitlines():
        raise ValueError('invalid Engine Rust toolchain')
    if type(record['source_date_epoch']) is not int or record['source_date_epoch'] < 0:
        raise ValueError('invalid source_date_epoch')
    oorelease._object(record['binary'], {'file', 'sha256'}, 'binary')
    if record['binary']['file'] != 'rivet-engine':
        raise ValueError('invalid Engine binary name')
    oorelease._digest(record['binary']['sha256'], 'binary.sha256')
    return record


def build_engine(src, out, runner=run):
    item = engine_component()
    root = Path(src).resolve()
    source = root / 'source'
    if runner(['git', 'rev-parse', 'HEAD'], cwd=source) != item['revision']:
        raise ValueError('source revision differs from registry')
    if not (source / 'vendor-config.toml').is_file() or not (source / 'cargo-vendor').is_dir():
        raise ValueError('offline build requires vendored dependencies')
    output = Path(out).resolve()
    output.mkdir(parents=True, exist_ok=False)
    index = output / 'source.index'
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    try:
        runner(['git', 'read-tree', 'HEAD'], cwd=source, env=env)
        for patch in item['patches']:
            runner(['git', 'apply', '--cached', str(ROOT / 'patches' / patch['file'])], cwd=source, env=env)
        runner(['git', 'diff', '--exit-code', '--no-ext-diff'], cwd=source, env=env)
        untracked = runner(['git', 'ls-files', '--others', '--exclude-standard'], cwd=source, env=env).splitlines()
        if any(path != 'vendor-config.toml' and not path.startswith('cargo-vendor/') for path in untracked):
            raise ValueError('unexpected untracked Engine source files')
    finally:
        index.unlink(missing_ok=True)
    epoch = int(runner(['git', 'show', '-s', '--format=%ct', item['revision']], cwd=source))
    container = ['docker', 'run', '--rm', '--network', 'none', '--platform', 'linux/amd64', '--cpus', '4', '--memory', '8g', '-v', f'{source}:/src:ro', '-v', f'{root / "rustup"}:/usr/local/rustup:ro', '-v', f'{output}:/out', '-w', '/src', '-e', 'RUSTFLAGS=--cfg tokio_unstable', '-e', f'SOURCE_DATE_EPOCH={epoch}', '-e', 'CARGO_TARGET_DIR=/out/target', '-e', 'RIVET_ERROR_OUTPUT_DIR=/out/errors', ENGINE_BUILDER]
    rustc = runner([*container, 'rustc', '-vV'])
    if 'release: 1.99.0' not in rustc.splitlines() or 'host: x86_64-unknown-linux-gnu' not in rustc.splitlines():
        raise ValueError('unexpected Engine Rust toolchain')
    runner([*container, 'sh', '-c', 'mkdir -p /out/errors && cargo --config /src/vendor-config.toml build --release --locked --offline -j4 -p rivet-engine --bin rivet-engine && cp /out/target/release/rivet-engine /out/rivet-engine'])
    record = {'schema': 'rivet-engine-build-record/1', 'component': item['name'], 'upstream': {'repository': item['upstream'], 'revision': item['revision']}, 'patches': [{'file': p['file'], 'sha256': 'sha256:' + p['sha256']} for p in item['patches']], 'lockfile_sha256': digest(source / 'Cargo.lock'), 'builder': ENGINE_BUILDER, 'rustc': rustc, 'source_date_epoch': epoch, 'platform': 'linux-x86_64', 'rustflags': '--cfg tokio_unstable', 'jobs': 4, 'memory_bytes': 8589934592, 'binary': {'file': 'rivet-engine', 'sha256': digest(output / 'rivet-engine')}}
    validate_engine_record(record)
    (output / 'build-record.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
    print(f'{record["binary"]["sha256"]}  {output / "rivet-engine"}')
