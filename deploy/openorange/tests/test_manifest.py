import os
import subprocess
import sys
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[1] / 'lib'
sys.path.insert(0, str(LIB))
import oomanifest
import oorollout_native


def test_content_and_metadata(tmp_path):
    js = tmp_path / 'node_modules/open-orange/dist/other.js'
    js.parent.mkdir(parents=True)
    js.write_text('a')
    dep = tmp_path / 'node_modules/.pnpm/transitive/index.js'
    dep.parent.mkdir(parents=True)
    dep.write_text('a')
    link = tmp_path / 'link'
    link.symlink_to('one')
    digest = oomanifest.closure_digest(tmp_path)
    for change in (lambda: js.write_text('b'), lambda: dep.write_text('b'), lambda: js.chmod(0o755), lambda: (link.unlink(), link.symlink_to('two')), lambda: (tmp_path / 'empty').mkdir()):
        change()
        new = oomanifest.closure_digest(tmp_path)
        assert new != digest
        digest = new
    (tmp_path / 'release.json').write_text('ignored')
    assert oomanifest.closure_digest(tmp_path) == digest
    os.mkfifo(tmp_path / 'fifo')
    with pytest.raises(ValueError, match='unsupported file type'):
        oomanifest.closure_digest(tmp_path)


def test_guest_agrees(tmp_path):
    (tmp_path / 'a').write_text('hello')
    source = oorollout_native.GUEST_SCRIPT.split('\nOPERATIONS = ')[0]
    code = source + '\nprint(closure_digest(' + repr(str(tmp_path)) + '))\n'
    result = subprocess.check_output([sys.executable, '-c', code], text=True).strip()
    assert result == oomanifest.closure_digest(tmp_path)
