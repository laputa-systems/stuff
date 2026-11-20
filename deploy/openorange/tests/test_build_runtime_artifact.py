import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runtime_build', ROOT / 'runtime-artifact/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def test_descriptor_and_deterministic_tar(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    inputs = {}
    for name in build.INPUTS:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        inputs[name] = build.sha(path.read_bytes())
    subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-qm', 'fixture'], check=True)
    revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    d = json.loads((ROOT / 'descriptors/runtime-production.json').read_text())
    d['stats']['revision'] = revision
    d['inputs'] = inputs
    build.validate(d, repo)
    d['inputs'][build.INPUTS[0]] = 'sha256:' + '0' * 64
    with pytest.raises(ValueError, match='input hash mismatch'):
        build.validate(d, repo)
    d['stats']['revision'] = 'main'
    with pytest.raises(ValueError, match='revision'):
        build.validate(d, repo)
    root = tmp_path / 'tree'
    root.mkdir()
    (root / 'a').write_text('x')
    (root / 'link').symlink_to('a')
    build.pack(root, tmp_path / 'a.tar')
    build.pack(root, tmp_path / 'b.tar')
    assert (tmp_path / 'a.tar').read_bytes() == (tmp_path / 'b.tar').read_bytes()
