from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from fix_helpers import git, initialize_repository

import repomod.fix as fix_module
from repomod.fix import push_fix_branch, push_repository
from repomod.git import head, status


@pytest.mark.parametrize(
    ("checkout", "expected"),
    [
        ("missing", ("skipped", "checkout is unavailable")),
        ("fleet", ("skipped", "directory is not a valid Git checkout")),
    ],
)
def test_fix_push_reports_unavailable_checkout(
    tmp_path: Path, git_environment: None, checkout: str, expected: tuple[str, str],
) -> None:
    _catalog, repository, _path, base = initialize_repository(tmp_path)
    branch = "repomod/fix/" + "b" * 32

    result = push_fix_branch(
        repository, tmp_path / checkout, branch, "main", base, base,
        canonical_head=base, canonical_branch="main",
    )

    assert result == expected
    assert git("--git-dir", str(tmp_path / "remote.git"), "show-ref", "--heads").stdout == f"{base} refs/heads/main\n"


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("invalid ref", ("failed", "fix branch name is invalid")),
        ("wrong origin", ("failed", "origin does not match the catalogued GitHub repository")),
        ("dirty checkout", ("skipped", "checkout is dirty")),
        ("missing default", ("skipped", "local default branch main is unavailable; sync before publishing fixes")),
        ("advanced default", ("skipped", "local default branch changed since fixing; sync before publishing fixes")),
        ("missing fix ref", ("failed", "fix branch tip changed before push")),
        ("moved fix ref", ("failed", "fix branch tip changed before push")),
        ("missing remote default", ("failed", "cannot verify remote default branch main: remote branch was not found")),
    ],
)
def test_fix_push_reports_publication_refusals(
    tmp_path: Path, git_environment: None, change: str, expected: tuple[str, str],
) -> None:
    _catalog, repository, path, base = initialize_repository(tmp_path)
    bare = tmp_path / "remote.git"
    git("checkout", "-b", "feature", cwd=path)
    branch = "repomod/fix/" + "b" * 32
    if change != "missing fix ref":
        git("branch", branch, base, cwd=path)
    if change == "invalid ref":
        branch = "invalid-fix-branch"
        git("branch", branch, base, cwd=path)
    elif change == "wrong origin":
        git("remote", "set-url", "origin", str(bare), cwd=path)
    elif change == "dirty checkout":
        (path / "README.md").write_text("uncommitted user work\n", encoding="utf-8")
    elif change == "missing default":
        git("branch", "-D", "main", cwd=path)
    elif change in ("advanced default", "moved fix ref"):
        advanced_ref = "main" if change == "advanced default" else branch
        new_head = git("commit-tree", f"{base}^{{tree}}", "-p", base, "-m", "advanced", cwd=path).stdout.strip()
        git("update-ref", f"refs/heads/{advanced_ref}", new_head, base, cwd=path)
    elif change == "missing remote default":
        git("--git-dir", str(bare), "update-ref", "-d", "refs/heads/main", base)
    local_refs = git("show-ref", "--heads", cwd=path).stdout
    remote_refs = git("--git-dir", str(bare), "for-each-ref", "refs/heads").stdout
    readme = (path / "README.md").read_bytes()

    result = push_fix_branch(
        repository, path, branch, "main", base, base,
        canonical_head=base, canonical_branch="feature",
    )

    assert result == expected
    assert head(path) == base
    assert git("show-ref", "--heads", cwd=path).stdout == local_refs
    assert git("--git-dir", str(bare), "for-each-ref", "refs/heads").stdout == remote_refs
    assert (path / "README.md").read_bytes() == readme


@pytest.mark.parametrize("during_remote_query", [False, True])
@pytest.mark.parametrize("change", ["commit", "branch"])
def test_fix_push_refuses_changed_canonical_identity(
    tmp_path: Path,
    git_environment: None,
    monkeypatch: pytest.MonkeyPatch,
    during_remote_query: bool,
    change: str,
) -> None:
    _catalog, repository, path, base = initialize_repository(tmp_path)
    git("checkout", "-b", "user-feature", cwd=path)
    branch = "repomod/fix/" + "b" * 32
    git("branch", branch, base, cwd=path)

    def change_checkout() -> None:
        if change == "commit":
            (path / "user.txt").write_text("user work\n", encoding="utf-8")
            git("add", "user.txt", cwd=path)
            git("commit", "-m", "user work", cwd=path)
        else:
            git("checkout", "-b", "another-feature", cwd=path)

    original_remote_head = fix_module._remote_branch_head

    def query_remote(checkout: Path, default_branch: str) -> str:
        change_checkout()
        return original_remote_head(checkout, default_branch)

    if during_remote_query:
        monkeypatch.setattr(fix_module, "_remote_branch_head", query_remote)
    else:
        change_checkout()

    state, message = push_fix_branch(
        repository, path, branch, "main", base, base,
        canonical_head=base, canonical_branch="user-feature",
    )

    assert state == "skipped"
    assert message == (
        "checkout changed before push" if during_remote_query else "canonical checkout changed since fixing"
    )
    assert git("--git-dir", str(tmp_path / "remote.git"), "for-each-ref", f"refs/heads/{branch}").stdout == ""
    assert git("rev-parse", f"refs/heads/{branch}", cwd=path).stdout.strip() == base
    assert git("status", "--porcelain", cwd=path).stdout == ""
    if change == "commit":
        assert head(path) != base
        assert (path / "user.txt").read_text(encoding="utf-8") == "user work\n"
    else:
        assert head(path) == base
        assert git("branch", "--show-current", cwd=path).stdout.strip() == "another-feature"


def test_push_fix_branch_skips_when_remote_default_advanced(
    tmp_path: Path,
    git_environment: None,
) -> None:
    _catalog, repository, path, base = initialize_repository(tmp_path)
    update_worktree = tmp_path / "remote-update"
    git("worktree", "add", "-b", "remote-update", str(update_worktree), base, cwd=path)
    (update_worktree / "remote.txt").write_text("remote advanced\n", encoding="utf-8")
    git("add", "remote.txt", cwd=update_worktree)
    git("commit", "-m", "advance remote", cwd=update_worktree)
    git("push", "origin", "HEAD:refs/heads/main", cwd=update_worktree)
    git("worktree", "remove", "--force", str(update_worktree), cwd=path)
    branch = "repomod/fix/" + "a" * 32
    git("branch", branch, base, cwd=path)

    state, message = push_fix_branch(
        repository, path, branch, "main", base, base, canonical_head=base, canonical_branch="main"
    )

    assert state == "skipped"
    assert message == "remote default branch changed; sync before publishing fixes"

def test_push_rejection_keeps_local_commit_and_never_rewrites_remote(
    tmp_path: Path,
    git_environment: None,
) -> None:
    _catalog, repository, path, _ = initialize_repository(tmp_path)
    (path / "local.txt").write_text("local\n", encoding="utf-8")
    git("add", "local.txt", cwd=path)
    git("commit", "-m", "local", cwd=path)
    other = tmp_path / "other"
    url = "https://github.com/acme/demo.git"
    git("clone", url, str(other))
    (other / "remote.txt").write_text("remote\n", encoding="utf-8")
    git("add", "remote.txt", cwd=other)
    git("commit", "-m", "remote", cwd=other)
    git("push", "origin", "main", cwd=other)
    previous_head = head(path)

    state, message = push_repository(repository, path)

    assert state == "failed"
    assert "rejected" in (message or "")
    assert head(path) == previous_head
    assert status(path, repository.id).origin_valid


def test_fix_push_rejection_preserves_both_branch_tips(
    tmp_path: Path, git_environment: None,
) -> None:
    _catalog, repository, path, base = initialize_repository(tmp_path)
    branch = "repomod/fix/" + "b" * 32
    ref = f"refs/heads/{branch}"
    git("branch", branch, base, cwd=path)
    remote_tip = git("commit-tree", f"{base}^{{tree}}", "-p", base, "-m", "newer remote fix", cwd=path).stdout.strip()
    git("push", "origin", f"{remote_tip}:{ref}", cwd=path)

    state, message = push_fix_branch(
        repository, path, branch, "main", base, base, canonical_head=base, canonical_branch="main",
    )

    assert state == "failed"
    assert message is not None
    assert "[rejected]" in message
    assert git("rev-parse", ref, cwd=path).stdout.strip() == base
    assert git("--git-dir", str(tmp_path / "remote.git"), "rev-parse", ref).stdout.strip() == remote_tip


@pytest.mark.parametrize(
    ("stdout", "stderr", "expected"),
    [
        ("push output", "push diagnostic\n", "push diagnostic"),
        ("push output\n", "  ", "push output"),
        ("  ", "  ", "git push failed"),
    ],
)
def test_fix_push_reports_available_command_diagnostics(
    tmp_path: Path,
    git_environment: None,
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    stderr: str,
    expected: str,
) -> None:
    _catalog, repository, path, base = initialize_repository(tmp_path)
    branch = "repomod/fix/" + "b" * 32
    git("branch", branch, base, cwd=path)
    before = git("show-ref", "--heads", cwd=path).stdout
    real_run_git = fix_module.run_git

    def reject_push(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args[0] == "push":
            assert args == ["push", "origin", f"{base}:refs/heads/{branch}"]
            return subprocess.CompletedProcess(args, 1, stdout, stderr)
        return real_run_git(args, **kwargs)

    monkeypatch.setattr(fix_module, "run_git", reject_push)

    result = push_fix_branch(
        repository, path, branch, "main", base, base,
        canonical_head=base, canonical_branch="main",
    )

    assert result == ("failed", expected)
    assert git("show-ref", "--heads", cwd=path).stdout == before
    assert git("--git-dir", str(tmp_path / "remote.git"), "show-ref", "--heads").stdout == f"{base} refs/heads/main\n"


def test_push_uses_checked_commit_when_checkout_changes_before_push(
    tmp_path: Path,
    git_environment: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _catalog, repository, path, _ = initialize_repository(tmp_path)
    (path / "main.txt").write_text("main\n", encoding="utf-8")
    git("add", "main.txt", cwd=path)
    git("commit", "-m", "main change", cwd=path)
    main_head = head(path)
    original_run_git = fix_module.run_git
    switched: list[str] = []

    def switch_before_push(
        arguments: list[str], cwd: Path | None = None, **options: Any
    ) -> subprocess.CompletedProcess[str]:
        if arguments[0] == "push" and not switched:
            git("checkout", "-b", "feature", cwd=path)
            (path / "feature.txt").write_text("feature\n", encoding="utf-8")
            git("add", "feature.txt", cwd=path)
            git("commit", "-m", "feature change", cwd=path)
            switched.append(head(path))
        return original_run_git(arguments, cwd=cwd, **options)

    monkeypatch.setattr(fix_module, "run_git", switch_before_push)

    state, message = push_repository(repository, path)

    remote_head = git(
        "--git-dir", str(tmp_path / "remote.git"), "rev-parse", "refs/heads/main"
    ).stdout.strip()
    assert state == "pushed", message
    assert remote_head == main_head
    assert head(path) == switched[0]


def test_fix_push_uses_validated_commit_when_branch_moves(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _catalog, repository, path, base = initialize_repository(tmp_path)
    branch = "repomod/fix/" + "b" * 32
    git("branch", branch, base, cwd=path)
    original_run_git = fix_module.run_git
    moved: list[str] = []

    def advance_before_push(
        arguments: list[str], cwd: Path | None = None, **options: Any,
    ) -> subprocess.CompletedProcess[str]:
        if arguments[0] == "push" and not moved:
            new_head = git("commit-tree", f"{base}^{{tree}}", "-p", base, "-m", "unvalidated", cwd=path).stdout.strip()
            git("update-ref", f"refs/heads/{branch}", new_head, cwd=path)
            moved.append(new_head)
        return original_run_git(arguments, cwd=cwd, **options)

    monkeypatch.setattr(fix_module, "run_git", advance_before_push)
    state, message = push_fix_branch(
        repository, path, branch, "main", base, base, canonical_head=base, canonical_branch="main"
    )
    assert state == "pushed", message
    remote_head = git("--git-dir", str(tmp_path / "remote.git"), "rev-parse", f"refs/heads/{branch}").stdout.strip()
    assert remote_head == base
    assert git("rev-parse", f"refs/heads/{branch}", cwd=path).stdout.strip() == moved[0]


def _commit_on(path: Path, start: str, name: str) -> str:
    git("checkout", "-q", "--detach", start, cwd=path)
    (path / name).write_text(f"{name}\n", encoding="utf-8")
    git("add", name, cwd=path)
    git("commit", "-q", "-m", name, cwd=path)
    commit = head(path)
    git("checkout", "-q", "main", cwd=path)
    return commit


@pytest.mark.parametrize("remote_moved", [False, True])
def test_rebuilt_fix_branch_replaces_only_the_remote_tip_it_last_published(
    tmp_path: Path, git_environment: None, remote_moved: bool,
) -> None:
    _catalog, repository, path, base = initialize_repository(tmp_path)
    bare = tmp_path / "remote.git"
    branch = "repomod/fix/" + "b" * 32
    previous = _commit_on(path, base, "old.txt")
    git("push", "-q", "origin", f"{previous}:refs/heads/{branch}", cwd=path)
    if remote_moved:
        moved = _commit_on(path, previous, "other.txt")
        git("push", "-q", "origin", f"{moved}:refs/heads/{branch}", cwd=path)
    rebuilt = _commit_on(path, base, "new.txt")
    git("branch", "-f", branch, rebuilt, cwd=path)

    state, message = push_fix_branch(
        repository, path, branch, "main", base, rebuilt,
        canonical_head=base, canonical_branch="main", replaces=previous,
    )

    published = git("--git-dir", str(bare), "rev-parse", f"refs/heads/{branch}").stdout.strip()
    if remote_moved:
        assert (state, message) == (
            "failed", "remote fix branch moved since repomod last fixed it; integrate or delete it",
        )
        assert published == moved
    else:
        assert (state, message) == ("pushed", None)
        assert published == rebuilt
