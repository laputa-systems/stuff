from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from repomod.fix import _write_plan
from repomod.rules import buildlib
from repomod.rules.buildlib import buildlib_rules
from repomod.types import RepoId, Repository

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'buildlib_fix'

_REPOSITORIES = {
    'consumer': 'joshuarli/pi-build',
    'node-build': 'laputa-systems/node-build',
    'exempt-repo': 'laputa-systems/stuff',
}


@pytest.fixture(autouse=True)
def _frozen_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(buildlib.paths, 'POLICY', FIXTURES / 'policy')


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob('*'))
        if path.is_file()
    }


def _copy(name: str, target: Path) -> Path:
    source = FIXTURES / 'before' / name
    shutil.copytree(source, target)
    return target


def _repository(name: str) -> Repository:
    return Repository(RepoId.parse(_REPOSITORIES[name]), ('build', 'python'))


def _apply_fix(root: Path, repository: Repository) -> list[str]:
    rule = buildlib_rules()[0]
    assert rule.fix is not None
    findings = rule.check(root, repository)
    assert any(finding.fixable for finding in findings), 'fixture must start with fixable findings'
    plan = rule.fix(root, repository)
    assert plan, 'fixer must return a plan'
    _write_plan(root, plan, rule.allowed_paths)
    remaining = rule.check(root, repository)
    assert not any(finding.fixable for finding in remaining), [
        finding.message for finding in remaining if finding.fixable
    ]
    return sorted(plan)


@pytest.mark.parametrize('name', ['consumer', 'node-build'])
def test_enrolled_fixture_is_rewritten_to_the_approved_artifact(
    tmp_path: Path, name: str
) -> None:
    root = _copy(name, tmp_path / name)
    plan = _apply_fix(root, _repository(name))
    assert set(plan) <= {
        'pyproject.toml',
        'uv.lock',
        'sources.lock.json',
        'bootstrap/buildlib-run',
        'bootstrap/python.lock',
    }
    expected = _tree(FIXTURES / 'after' / name)
    assert _tree(root) == expected


def test_node_build_keeps_the_still_approved_buildlib_run_shim(tmp_path: Path) -> None:
    root = _copy('node-build', tmp_path / 'node-build')
    plan = _apply_fix(root, _repository('node-build'))
    assert 'bootstrap/buildlib-run' not in plan
    assert (root / 'bootstrap/buildlib-run').read_bytes() == (
        FIXTURES / 'before/node-build/bootstrap/buildlib-run'
    ).read_bytes()
    assert (root / 'bootstrap/python.lock').read_bytes() == (
        FIXTURES / 'after/node-build/bootstrap/python.lock'
    ).read_bytes()


def test_missing_required_shim_is_recreated_from_the_vendored_bytes(tmp_path: Path) -> None:
    root = _copy('node-build', tmp_path / 'node-build')
    (root / 'bootstrap/python.lock').unlink()
    repository = _repository('node-build')
    rule = buildlib_rules()[0]
    assert rule.fix is not None
    findings = rule.check(root, repository)
    missing = [f for f in findings if 'missing bootstrap shim' in f.message]
    assert missing
    assert all(finding.fixable for finding in missing)
    plan = rule.fix(root, repository)
    assert plan['bootstrap/python.lock'] == buildlib.buildlib_pins.vendored_shims()['python.lock']
    _write_plan(root, plan, rule.allowed_paths)
    assert not any(f.fixable for f in rule.check(root, repository))


def test_exempt_fixture_is_untouched(tmp_path: Path) -> None:
    root = _copy('exempt-repo', tmp_path / 'exempt-repo')
    repository = _repository('exempt-repo')
    rule = buildlib_rules()[0]
    assert rule.fix is not None
    before = _tree(root)
    assert rule.check(root, repository) == []
    assert rule.fix(root, repository) == {}
    assert _tree(root) == before


def test_unparseable_pyproject_stays_unfixed_and_reported(tmp_path: Path) -> None:
    root = _copy('consumer', tmp_path / 'consumer')
    (root / 'pyproject.toml').write_text('not [valid toml\n', encoding='utf-8')
    repository = _repository('consumer')
    rule = buildlib_rules()[0]
    assert rule.fix is not None
    findings = rule.check(root, repository)
    operational = [f for f in findings if f.file == 'pyproject.toml' and f.kind == 'operational']
    assert operational
    assert not any(f.fixable for f in operational)
    plan = rule.fix(root, repository)
    assert 'pyproject.toml' not in plan
    _write_plan(root, plan, rule.allowed_paths)
    after = rule.check(root, repository)
    assert any(f.file == 'pyproject.toml' and f.kind == 'operational' for f in after)
    assert not any(f.fixable for f in after)
    assert (root / 'pyproject.toml').read_text(encoding='utf-8') == 'not [valid toml\n'
