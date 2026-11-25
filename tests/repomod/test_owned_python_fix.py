from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from repomod import paths
from repomod.fix import _write_plan
from repomod.rules import owned_substitution, tools_lock
from repomod.rules.lint import _lint_workflow_fix
from repomod.types import RepoId, Repository

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "owned_python"
FROZEN_POLICY = Path(__file__).resolve().parent / "fixtures" / "tools_lock" / "policy"
REPOSITORY = Repository(RepoId.parse("acme/consumer"), ())
REWRITTEN = {
    "consumer": {".github/workflows/lint.yml", ".github/workflows/ci.yml"},
    "bare": {".github/workflows/lint.yml"},
}
UNTOUCHED = {
    ".github/workflows/setup-python.yml",
    ".github/workflows/other-python.yml",
    ".github/workflows/python-version.yml",
    ".github/workflows/separated.yml",
}


@pytest.fixture(autouse=True)
def _frozen_policy(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    policy = tmp_path_factory.mktemp("policy") / "policy"
    shutil.copytree(paths.POLICY, policy)
    shutil.copyfile(FROZEN_POLICY / "tools-lock.toml", policy / "tools-lock.toml")
    shutil.copyfile(FIXTURES / "actions.toml", policy / "actions.toml")
    monkeypatch.setattr(paths, "POLICY", policy)


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _consumer(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name
    shutil.copytree(FIXTURES / "before" / name, root)
    return root


def test_pattern_a_workflows_rewrite_byte_exact(tmp_path: Path) -> None:
    rule = owned_substitution.owned_substitution_rules()[0]
    for name in ("consumer", "bare"):
        root = _consumer(tmp_path, name)
        findings = rule.check(root, REPOSITORY)
        fixable = [finding for finding in findings if finding.fixable]
        assert fixable
        assert all(finding.rule == "owned-tool-substitution" for finding in fixable)
        assert {finding.file for finding in fixable} <= REWRITTEN[name]
        if name == "consumer":
            untouched = [
                finding for finding in findings if finding.file in UNTOUCHED
            ]
            assert untouched
            assert not any(finding.fixable for finding in untouched)
        assert rule.fix is not None
        plan = rule.fix(root, REPOSITORY)
        assert plan
        _write_plan(root, plan, rule.allowed_paths)
        assert _tree(root) == _tree(FIXTURES / "after" / name)
        remaining = rule.check(root, REPOSITORY)
        assert not any(finding.fixable for finding in remaining)
        assert not any(
            finding.file in REWRITTEN[name] for finding in remaining
        )
        assert {finding.file for finding in remaining} <= UNTOUCHED


def test_lock_file_passes_the_tools_lock_rule(tmp_path: Path) -> None:
    rule = owned_substitution.owned_substitution_rules()[0]
    lock_rule = tools_lock.tools_lock_rules()[0]
    for name in ("consumer", "bare"):
        root = _consumer(tmp_path, name)
        assert rule.fix is not None
        plan = rule.fix(root, REPOSITORY)
        _write_plan(root, plan, rule.allowed_paths)
        findings = lock_rule.check(root, REPOSITORY)
        assert not any(
            finding.file == ".github/tools.lock.json" for finding in findings
        )


def test_existing_lock_entries_are_preserved(tmp_path: Path) -> None:
    root = _consumer(tmp_path, "consumer")
    rule = owned_substitution.owned_substitution_rules()[0]
    assert rule.fix is not None
    plan = rule.fix(root, REPOSITORY)
    document = json.loads(plan[".github/tools.lock.json"])
    assert document["schema"] == 1
    assert set(document["tools"]) == {"cpython", "gluon"}
    assert document["tools"]["cpython"]["version"] == "3.15.1"
    assert document["tools"]["gluon"]["tag"] == (
        "release-fa8b6aace38683a17ee3f398d8b568341c7192fe"
    )


def test_lint_workflow_fix_uses_the_owned_python_form(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "demo.py").write_text("print(1)\n", encoding="utf-8")

    plan = _lint_workflow_fix(tmp_path, REPOSITORY)

    assert set(plan) == {".github/workflows/lint.yml", ".github/tools.lock.json"}
    rendered = plan[".github/workflows/lint.yml"]
    assert "laputa-systems/buildlib/setup@" in rendered
    assert "tools: cpython" in rendered
    assert "lock: .github/tools.lock.json" in rendered
    assert "UV_PYTHON_DOWNLOADS: never" in rendered
    assert "UV_PYTHON_PREFERENCE: only-system" in rendered
    assert "env:" in rendered
    assert "uv python install" not in rendered
    document = json.loads(plan[".github/tools.lock.json"])
    assert document["schema"] == 1
    assert document["tools"]["cpython"]["version"] == "3.15.1"
    for relative, content in plan.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    lock_rule = tools_lock.tools_lock_rules()[0]
    assert not any(
        finding.file == ".github/tools.lock.json"
        for finding in lock_rule.check(tmp_path, REPOSITORY)
    )


def test_lint_workflow_fix_without_python_skips_the_lock(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    source = tmp_path / "src" / "main.rs"
    source.parent.mkdir()
    source.write_text("fn main() {}\n", encoding="utf-8")

    plan = _lint_workflow_fix(tmp_path, REPOSITORY)

    assert set(plan) == {".github/workflows/lint.yml"}
    assert "buildlib/setup" not in plan[".github/workflows/lint.yml"]
