from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from repomod import paths
from repomod.fix import _write_plan
from repomod.rules import owned_substitution
from repomod.types import RepoId, Repository

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "owned_dockerfile"
REPOSITORY = Repository(RepoId.parse("acme/consumer"), ("build",))
DOCKERFILE = "Dockerfile"
UNFIXABLE_LABELS = ("installed by apt", "package 'python3'")


@pytest.fixture(autouse=True)
def _fixture_policy(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    policy = tmp_path_factory.mktemp("policy") / "policy"
    shutil.copytree(paths.POLICY, policy)
    shutil.copyfile(FIXTURES / "image-policy.toml", policy / "owned-tools-image.toml")
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


def test_dockerfile_findings_fix_and_match_fixture(tmp_path: Path) -> None:
    rule = owned_substitution.owned_substitution_rules()[0]
    root = _consumer(tmp_path, "consumer")
    findings = rule.check(root, REPOSITORY)
    fixable = [finding for finding in findings if finding.fixable]
    assert fixable
    assert all(finding.rule == "owned-tool-substitution" for finding in fixable)
    assert {finding.file for finding in fixable} == {DOCKERFILE}
    assert {finding.line for finding in fixable} == {3, 5, 6, 11}
    unfixed = [finding for finding in findings if not finding.fixable]
    assert unfixed
    assert all(finding.file == DOCKERFILE for finding in unfixed)
    assert all(
        any(token in finding.message for token in UNFIXABLE_LABELS)
        for finding in unfixed
    )
    assert rule.fix is not None
    plan = rule.fix(root, REPOSITORY)
    assert plan == {DOCKERFILE: (FIXTURES / "after" / "consumer" / DOCKERFILE).read_text()}
    _write_plan(root, plan, rule.allowed_paths)
    assert _tree(root) == _tree(FIXTURES / "after" / "consumer")
    remaining = rule.check(root, REPOSITORY)
    assert not any(finding.fixable for finding in remaining)
    assert remaining
    assert all(
        any(token in finding.message for token in UNFIXABLE_LABELS)
        for finding in remaining
    )


def test_unfixable_dockerfile_findings_have_no_plan(tmp_path: Path) -> None:
    root = tmp_path / "consumer"
    root.mkdir()
    (root / "Dockerfile").write_text(
        "FROM debian:bookworm\nRUN apt-get install -y git cmake\n"
        "FROM alpine\nRUN apk add --no-cache python3 curl\n",
        encoding="utf-8",
    )
    rule = owned_substitution.owned_substitution_rules()[0]
    findings = rule.check(root, REPOSITORY)
    assert findings
    assert not any(finding.fixable for finding in findings)
    assert rule.fix is not None
    assert rule.fix(root, REPOSITORY) == {}
