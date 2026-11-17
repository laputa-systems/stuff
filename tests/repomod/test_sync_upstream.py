from __future__ import annotations

from pathlib import Path

import pytest
from git_helpers import git, make_catalog, make_parent, make_remote, parent_remote, upstream_refs

import repomod.sync as sync_module
from repomod.catalog import repository_path
from repomod.sync import sync_one
from repomod.types import RemoteRepository


def test_sync_clone_adds_and_fetches_upstream_remote(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_remote(tmp_path)
    upstream_bare, upstream_sha = make_parent(tmp_path)
    def local_upstream(parent: str) -> str:
        assert parent == "acme/upstream"
        return f"file://{upstream_bare}"

    monkeypatch.setattr(sync_module, "upstream_url", local_upstream)
    catalog, repository = make_catalog(tmp_path)

    result = sync_one(catalog, repository, parent_remote(repository, upstream_sha))

    checkout = repository_path(catalog, repository)
    assert result.action == "cloned"
    assert "upstream acme/upstream added and fetched" in result.message
    assert git("config", "--get", "remote.upstream.url", cwd=checkout) == f"file://{upstream_bare}"
    assert "refs/remotes/upstream/main" in upstream_refs(checkout)
    assert git("rev-parse", "--is-shallow-repository", cwd=checkout) == "false"


def test_sync_existing_checkout_gains_upstream_remote(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_remote(tmp_path)
    upstream_bare, upstream_sha = make_parent(tmp_path)
    monkeypatch.setattr(sync_module, "upstream_url", lambda parent: f"file://{upstream_bare}")
    catalog, repository = make_catalog(tmp_path)
    plain = RemoteRepository(str(repository.id), "main", "unused", False)
    sync_one(catalog, repository, plain)
    checkout = repository_path(catalog, repository)
    assert upstream_refs(checkout) == []

    result = sync_one(catalog, repository, parent_remote(repository, upstream_sha))

    assert result.action in {"updated", "current", "fetched"}
    assert "upstream acme/upstream added and fetched" in result.message
    assert "refs/remotes/upstream/main" in upstream_refs(checkout)


def test_sync_repoints_wrong_upstream_url(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_remote(tmp_path)
    upstream_bare, upstream_sha = make_parent(tmp_path)
    monkeypatch.setattr(sync_module, "upstream_url", lambda parent: f"file://{upstream_bare}")
    catalog, repository = make_catalog(tmp_path)
    sync_one(catalog, repository, RemoteRepository(str(repository.id), "main", "unused", False))
    checkout = repository_path(catalog, repository)
    git("remote", "add", "upstream", "file:///elsewhere.git", cwd=checkout)
    base = git("rev-parse", "HEAD", cwd=checkout)
    preserved = git("commit-tree", f"{base}^{{tree}}", "-p", base, "-m", "old upstream work", cwd=checkout)
    git("update-ref", "refs/remotes/upstream/preserved", preserved, cwd=checkout)
    git("branch", "--set-upstream-to=upstream/preserved", "main", cwd=checkout)
    git("config", "remote.upstream.pushurl", "file:///user-push.git", cwd=checkout)

    result = sync_one(catalog, repository, parent_remote(repository, upstream_sha))

    assert "upstream acme/upstream repointed and fetched" in result.message
    assert git("config", "--get", "remote.upstream.url", cwd=checkout) == f"file://{upstream_bare}"
    assert "refs/remotes/upstream/preserved" in upstream_refs(checkout)
    assert git("rev-parse", "refs/remotes/upstream/preserved", cwd=checkout) == preserved
    assert git("config", "--get", "branch.main.remote", cwd=checkout) == "upstream"
    assert git("config", "--get", "branch.main.merge", cwd=checkout) == "refs/heads/preserved"
    assert git("config", "--get", "remote.upstream.pushurl", cwd=checkout) == "file:///user-push.git"
    assert git("rev-parse", "refs/remotes/upstream/main", cwd=checkout) == upstream_sha
    assert git("branch", "--show-current", cwd=checkout) == "main"
    assert git("rev-parse", "HEAD", cwd=checkout) == base


def test_sync_leaves_non_forks_without_upstream_remote(
    tmp_path: Path, git_environment: None
) -> None:
    make_remote(tmp_path)
    catalog, repository = make_catalog(tmp_path)
    result = sync_one(catalog, repository, RemoteRepository(str(repository.id), "main", "unused", False))

    assert result.action == "cloned"
    assert "upstream" not in result.message
    assert upstream_refs(repository_path(catalog, repository)) == []


@pytest.mark.parametrize(("parent", "branch"), [("acme/upstream", None), (None, "main")])
def test_sync_ignores_incomplete_upstream_metadata(
    tmp_path: Path,
    git_environment: None,
    monkeypatch: pytest.MonkeyPatch,
    parent: str | None,
    branch: str | None,
) -> None:
    make_remote(tmp_path)
    catalog, repository = make_catalog(tmp_path)

    def unexpected_upstream(value: str) -> str:
        pytest.fail(f"incomplete metadata attempted upstream access for {value}")

    monkeypatch.setattr(sync_module, "upstream_url", unexpected_upstream)
    remote = RemoteRepository(str(repository.id), "main", "unused", False, parent=parent, parent_branch=branch)

    outcome = sync_one(catalog, repository, remote)

    assert outcome.action == "cloned"
    assert outcome.message == "cloned main"
    assert upstream_refs(repository_path(catalog, repository)) == []


def test_upstream_fetch_keeps_only_the_tip_for_a_shallow_checkout(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    bare, _, _ = make_remote(tmp_path)
    upstream, first = make_parent(tmp_path)
    tree = git("rev-parse", f"{first}^{{tree}}", cwd=upstream)
    middle = git("commit-tree", tree, "-p", first, "-m", "upstream middle", cwd=upstream)
    tip = git("commit-tree", tree, "-p", middle, "-m", "upstream tip", cwd=upstream)
    git("update-ref", "refs/heads/main", tip, cwd=upstream)
    checkout = tmp_path / "shallow-checkout"
    git("clone", "--depth=1", f"file://{bare}", str(checkout))
    _, repository = make_catalog(tmp_path)
    monkeypatch.setattr(sync_module, "upstream_url", lambda _parent: f"file://{upstream}")

    outcome = sync_module._sync_upstream(checkout, parent_remote(repository, tip))

    assert outcome == "upstream acme/upstream added and fetched"
    assert git("rev-list", "refs/remotes/upstream/main", cwd=checkout) == tip
    assert git("rev-parse", "--is-shallow-repository", cwd=checkout) == "true"


def test_sync_upstream_failure_is_non_fatal(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, seed, _ = make_remote(tmp_path)
    monkeypatch.setattr(sync_module, "upstream_url", lambda parent: "file:///does/not/exist.git")
    catalog, repository = make_catalog(tmp_path)
    sha = git("rev-parse", "HEAD", cwd=seed)
    remote = RemoteRepository(
        str(repository.id), "main", sha, False,
        parent="acme/upstream", parent_branch="main", parent_sha="b" * 40,
    )
    sync_one(catalog, repository, remote)

    result = sync_one(catalog, repository, remote)

    assert result.action == "current"
    assert result.failed is False
    assert "upstream acme/upstream unavailable" in result.message


def test_sync_dry_run_reports_upstream_plan_without_mutating(
    tmp_path: Path, git_environment: None
) -> None:
    make_remote(tmp_path)
    catalog, repository = make_catalog(tmp_path)
    checkout = repository_path(catalog, repository)

    missing = sync_one(catalog, repository, parent_remote(repository, "b" * 40), dry_run=True)
    assert missing.action == "planned"
    assert "would clone into" in missing.message
    assert "would ensure the upstream acme/upstream remote and fetch main" in missing.message
    assert not checkout.exists()

    sync_one(catalog, repository, RemoteRepository(str(repository.id), "main", "unused", False))
    assert upstream_refs(checkout) == []
    planned = sync_one(catalog, repository, parent_remote(repository, "b" * 40), dry_run=True)
    assert planned.action == "planned"
    assert "would ensure the upstream acme/upstream remote and fetch main" in planned.message
    assert upstream_refs(checkout) == []


def test_ensure_upstream_remote_states(tmp_path: Path, git_environment: None) -> None:
    from repomod.git import ensure_upstream_remote

    work = tmp_path / "work"
    git("init", "--initial-branch=main", str(work))
    assert ensure_upstream_remote(work, "file:///one.git") == "added"
    assert ensure_upstream_remote(work, "file:///one.git") == "current"
    assert ensure_upstream_remote(work, "file:///two.git") == "updated"
    assert git("config", "--get", "remote.upstream.url", cwd=work) == "file:///two.git"
