from __future__ import annotations

import argparse
from pathlib import Path

import pytest
from fix_helpers import file_rule, git, initialize_repository

from repomod.cmd import fix as command
from repomod.github import AutoMergeSkipped, FixPullRequest
from repomod.types import RemoteRepository, Repository


@pytest.mark.parametrize("change_during_fix", [False, True])
def test_fix_publishes_only_from_unchanged_canonical_checkout(
    tmp_path: Path,
    git_environment: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    change_during_fix: bool,
) -> None:
    catalog, repository, path, base = initialize_repository(tmp_path)
    git("checkout", "-b", "user-feature", cwd=path)

    def commit_user_change(root: Path, repo: Repository) -> None:
        if not change_during_fix:
            return
        (path / "user.txt").write_text("user work\n", encoding="utf-8")
        git("add", "user.txt", cwd=path)
        git("commit", "-m", "user work", cwd=path)

    rule = file_rule("witness", "fix.txt", "fixed\n", on_fix=commit_user_change)
    remote = RemoteRepository(str(repository.id), "main", base, False)
    monkeypatch.setattr(command.common, "default_catalog", lambda: catalog)
    monkeypatch.setattr(command.common, "with_visibility", lambda repos: repos)
    monkeypatch.setattr(command.policy, "validate_ignored_rules", lambda repos: None)
    monkeypatch.setattr(command.policy, "selected_rules", lambda **kwargs: (rule,))
    monkeypatch.setattr(command.github, "remote_metadata", lambda repos: {str(repository.id): remote})
    monkeypatch.setattr(command, "sync_repositories", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        command.fix_engine, "_policy_findings", lambda root, repo, extra: tuple(extra.check(root, repo))
    )
    published: list[str] = []

    def create_pr(repo: object, branch: str, base_branch: str) -> FixPullRequest:
        published.append(branch)
        return FixPullRequest("https://example.invalid/pr/1", AutoMergeSkipped("fixture"))

    monkeypatch.setattr(command.github, "ensure_fix_pull_request", create_pr)
    args = argparse.Namespace(workers=1, repo=["acme/demo"], tag=[], rule=["witness"], no_mirror=True)

    assert command._fix(args) == int(change_during_fix)

    output = capsys.readouterr()
    branches = git("for-each-ref", "--format=%(refname:short)", "refs/heads/repomod/fix", cwd=path).stdout.splitlines()
    assert len(branches) == 1
    assert git("show", f"{branches[0]}:fix.txt", cwd=path).stdout == "fixed\n"
    assert git("branch", "--show-current", cwd=path).stdout.strip() == "user-feature"
    assert git("status", "--porcelain", cwd=path).stdout == ""
    remote_branches = git(
        "--git-dir", str(tmp_path / "remote.git"), "for-each-ref", "--format=%(refname:short)", "refs/heads/repomod/fix"
    ).stdout.splitlines()
    if change_during_fix:
        assert "canonical checkout changed during fixing" in output.err
        assert published == []
        assert remote_branches == []
        assert "pushed" not in output.out
        assert (path / "user.txt").read_text(encoding="utf-8") == "user work\n"
    else:
        assert output.err == ""
        assert published == branches
        assert remote_branches == branches
        assert "pushed; PR https://example.invalid/pr/1" in output.out
