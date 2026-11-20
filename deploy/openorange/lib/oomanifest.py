import hashlib
import json
import os
import stat


def manifest(root):
    entries = []
    def walk(directory, prefix=''):
        with os.scandir(directory) as scan:
            children = sorted(scan, key=lambda entry: os.fsencode(entry.name))
        for entry in children:
            path = prefix + entry.name
            if path == 'release.json':
                continue
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                entries.append({'path': path, 'type': 'directory'})
                walk(entry.path, path + '/')
            elif stat.S_ISREG(info.st_mode):
                h = hashlib.sha256()
                with open(entry.path, 'rb') as stream:
                    for chunk in iter(lambda: stream.read(1 << 20), b''):
                        h.update(chunk)
                entries.append({'path': path, 'type': 'file', 'sha256': 'sha256:' + h.hexdigest(), 'size': info.st_size, 'executable': bool(info.st_mode & 0o111)})
            elif stat.S_ISLNK(info.st_mode):
                entries.append({'path': path, 'type': 'symlink', 'target': os.readlink(entry.path)})
            else:
                raise ValueError('unsupported file type: ' + path)
    walk(os.fspath(root))
    entries.sort(key=lambda entry: os.fsencode(entry['path']))
    return {'schema': 'openorange-runtime-manifest/1', 'excluded': ['release.json'], 'entries': entries}


def manifest_digest(value):
    return 'sha256:' + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def closure_digest(root):
    return manifest_digest(manifest(root))


def release_id(digest):
    return 'rt-' + digest.removeprefix('sha256:')[:12]
