from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from repomod import buildlib_pins, paths
from repomod.fix import _write_plan
from repomod.rules import tools_lock
from repomod.rules.tools_lock import tools_lock_rules
from repomod.types import RepoId, Repository

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'tools_lock'
SHIPPED_POLICY = paths.POLICY
REPOSITORY = Repository(RepoId.parse('laputa-systems/gluon'), ('build',))


@pytest.fixture(autouse=True)
def _frozen_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools_lock.paths, 'POLICY', FIXTURES / 'policy')


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob('*'))
        if path.is_file()
    }


def _consumer(tmp_path: Path) -> Path:
    root = tmp_path / 'consumer'
    shutil.copytree(FIXTURES / 'before/consumer', root)
    return root


def test_fixture_reports_only_policy_approved_tools(tmp_path: Path) -> None:
    root = _consumer(tmp_path)
    findings = tools_lock_rules()[0].check(root, REPOSITORY)
    messages = [finding.message for finding in findings]
    assert any('gluon' in message for message in messages)
    assert any('.github/tools.lock.json' in message and 'ffmpeg-runtime' in message for message in messages)
    assert not any('fd' in message or 'rg' in message for message in messages)
    assert all(finding.fixable for finding in findings)


def test_fixture_fix_rewrites_to_the_approved_release(tmp_path: Path) -> None:
    root = _consumer(tmp_path)
    rule = tools_lock_rules()[0]
    assert rule.fix is not None
    findings = rule.check(root, REPOSITORY)
    assert findings
    assert all(finding.fixable for finding in findings)
    plan = rule.fix(root, REPOSITORY)
    assert set(plan) == {'tools.lock.json', '.github/tools.lock.json'}
    _write_plan(root, plan, rule.allowed_paths)
    remaining = rule.check(root, REPOSITORY)
    assert not any(finding.fixable for finding in remaining)
    assert _tree(root) == _tree(FIXTURES / 'after/consumer')


def test_lock_is_rewritten_in_the_canonical_layout(tmp_path: Path) -> None:
    root = _consumer(tmp_path)
    rule = tools_lock_rules()[0]
    assert rule.fix is not None
    plan = rule.fix(root, REPOSITORY)
    text = plan['tools.lock.json']
    assert text.endswith('\n')
    assert not text.endswith('\n\n')
    document = json.loads(text)
    assert document['tools']['gluon']['tag'] == (
        'release-fa8b6aace38683a17ee3f398d8b568341c7192fe'
    )
    assert list(document['tools']) == sorted(document['tools'])
    assert _tree(FIXTURES / 'after/consumer')['tools.lock.json'] == text.encode()


def test_unknown_tool_is_reported_but_not_fixed(tmp_path: Path) -> None:
    root = tmp_path / 'repo'
    root.mkdir()
    (root / 'tools.lock.json').write_text(json.dumps({
        'schema': 1,
        'tools': {'not-a-tool': {'tag': 'release-x'}},
    }), encoding='utf-8')
    findings = tools_lock_rules()[0].check(root, REPOSITORY)
    assert len(findings) == 1
    assert 'unknown tool' in findings[0].message
    assert not findings[0].fixable
    fix = tools_lock_rules()[0].fix
    assert fix is not None
    assert fix(root, REPOSITORY) == {}


def test_invalid_schema_is_reported_but_not_fixed(tmp_path: Path) -> None:
    root = tmp_path / 'repo'
    root.mkdir()
    (root / 'tools.lock.json').write_text(
        json.dumps({'schema': 2, 'tools': {}}), encoding='utf-8'
    )
    findings = tools_lock_rules()[0].check(root, REPOSITORY)
    assert len(findings) == 1
    assert 'schema must be 1' in findings[0].message
    assert not findings[0].fixable
    fix = tools_lock_rules()[0].fix
    assert fix is not None
    assert fix(root, REPOSITORY) == {}


def test_unparseable_lock_is_reported_but_not_fixed(tmp_path: Path) -> None:
    root = tmp_path / 'repo'
    root.mkdir()
    (root / 'tools.lock.json').write_text('{not json', encoding='utf-8')
    findings = tools_lock_rules()[0].check(root, REPOSITORY)
    assert len(findings) == 1
    assert 'not a valid JSON object' in findings[0].message
    assert not findings[0].fixable
    fix = tools_lock_rules()[0].fix
    assert fix is not None
    assert fix(root, REPOSITORY) == {}


def test_shipped_policy_approves_only_known_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools_lock.paths, 'POLICY', SHIPPED_POLICY)
    approved = tools_lock._load_policy()
    assert approved
    for tool, entry in approved.items():
        assert tool in buildlib_pins.TOOLS_LOCK_TOOLS
        assert entry["tag"]
        assert entry["assets"]
        assert all(len(asset["sha256"]) == 64 for asset in entry["assets"].values())


def test_conforming_lock_is_clean(tmp_path: Path) -> None:
    root = tmp_path / 'repo'
    root.mkdir()
    policy = tools_lock._load_policy()
    document = {'schema': 1, 'tools': dict(policy)}
    (root / 'tools.lock.json').write_text(
        json.dumps(document, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    assert tools_lock_rules()[0].check(root, REPOSITORY) == []
    fix = tools_lock_rules()[0].fix
    assert fix is not None
    assert fix(root, REPOSITORY) == {}
