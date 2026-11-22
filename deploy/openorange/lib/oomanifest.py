import hashlib
import json
import os
import stat


def walk(directory, prefix, entries, skip=()):
    with os.scandir(directory) as scan:
        children = sorted(scan, key=lambda entry: os.fsencode(entry.name))
    for entry in children:
        path = prefix + entry.name
        if path in skip:
            continue
        info = entry.stat(follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            entries.append({'path': path, 'type': 'directory'})
            walk(entry.path, path + '/', entries)
        elif stat.S_ISREG(info.st_mode):
            entries.append(file_entry(path, entry.path, info))
        elif stat.S_ISLNK(info.st_mode):
            entries.append({'path': path, 'type': 'symlink', 'target': os.readlink(entry.path)})
        else:
            raise ValueError('unsupported file type: ' + path)


def file_entry(path, source, info):
    h = hashlib.sha256()
    with open(source, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return {'path': path, 'type': 'file', 'sha256': 'sha256:' + h.hexdigest(), 'size': info.st_size, 'executable': bool(info.st_mode & 0o111)}


def manifest(root):
    entries = []
    walk(os.fspath(root), '', entries, skip=('release.json',))
    entries.sort(key=lambda entry: os.fsencode(entry['path']))
    return {'schema': 'openorange-runtime-manifest/1', 'excluded': ['release.json'], 'entries': entries}


def manifest_digest(value):
    return 'sha256:' + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def closure_digest(root):
    return manifest_digest(manifest(root))


def release_id(digest):
    return 'rt-' + digest.removeprefix('sha256:')[:12]


# A Stats app release: both Worker bundles, their descriptors and the
# infrastructure collector. Parts are named explicitly so that the in-place
# layout and a release directory produce the same digest.
APP_PARTS = ('collector', 'observe', 'observe.jsonc', 'stats', 'stats.jsonc')


def app_manifest(parts):
    if set(parts) != set(APP_PARTS):
        raise ValueError('app release parts must be exactly ' + ', '.join(APP_PARTS))
    entries = []
    for name in APP_PARTS:
        source = os.path.realpath(parts[name])
        info = os.stat(source)
        if stat.S_ISDIR(info.st_mode):
            entries.append({'path': name, 'type': 'directory'})
            walk(source, name + '/', entries)
        elif stat.S_ISREG(info.st_mode):
            entries.append(file_entry(name, source, info))
        else:
            raise ValueError('unsupported app part: ' + name)
    entries.sort(key=lambda entry: os.fsencode(entry['path']))
    return {'schema': 'stats-app-manifest/1', 'entries': entries}


def app_release_parts(root):
    names = set(os.listdir(root)) - {'release.json'}
    if names != set(APP_PARTS):
        raise ValueError('app release contents must be exactly ' + ', '.join(APP_PARTS))
    return {name: os.path.join(root, name) for name in APP_PARTS}


def app_digest(root):
    return manifest_digest(app_manifest(app_release_parts(root)))


def app_release_id(digest):
    return 'app-' + digest.removeprefix('sha256:')[:12]
