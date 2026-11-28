from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

import repomod.artifacts as artifacts_module
import repomod.cli as cli_module
import repomod.cmd.clean as clean_cmd
from repomod.artifacts import ArtifactResult, clean_repositories
from repomod.catalog import find_repository, load_catalog, repository_path
from repomod.cmd import common as cmd_common
from repomod.types import Catalog


def git(*arguments: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def make_catalog(tmp_path: Path) -> Catalog:
    path = tmp_path / "catalog.toml"
    path.write_text(
        'version = 1\n\n[workspace]\nroot = "~/repos"\npersonal_owner = "joshuarli"\n\n'
        '[repos."acme"]\ntool = ["tool", "rust", "python", "typescript"]\n'
        'ziggy = ["tool", "zig"]\n'
        '[repos."joshuarli"]\nmine = ["tool", "swift"]\n',
        encoding="utf-8",
    )
    return load_catalog(
        path,
        {"HOME": str(tmp_path), "REPOMOD_ROOT": str(tmp_path / "fleet")},
    )


def checkout(catalog: Catalog, name: str, owner: str = "acme") -> Path:
    path = repository_path(catalog, find_repository(catalog, f"{owner}/{name}"))
    path.parent.mkdir(parents=True, exist_ok=True)
    git("init", "--initial-branch=main", str(path))
    git("remote", "add", "origin", f"https://github.com/{owner}/{name}.git", cwd=path)
    return path


def by_artifact(results: list[ArtifactResult]) -> dict[str, ArtifactResult]:
    return {result.message.split(":", 1)[0]: result for result in results}


def test_clean_removes_tagged_artifacts_and_leaves_unknown_paths(
    tmp_path: Path, git_environment: None
) -> None:
    catalog = make_catalog(tmp_path)
    rust = checkout(catalog, "tool")
    zig = checkout(catalog, "ziggy")
    for name in (
        "target", "node_modules", ".venv", "venv", "__pycache__",
        ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ):
        (rust / name).mkdir(parents=True)
    (rust / "target" / "debug").mkdir(parents=True)
    (rust / "target" / "debug" / "app").write_text("binary\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep\n", encoding="utf-8")
    (rust / "target" / "link").symlink_to(outside, target_is_directory=True)
    (rust / "dist").mkdir()
    (rust / "notes.txt").write_text("keep\n", encoding="utf-8")
    for name in (".zig-cache", "zig-cache"):
        (zig / name).mkdir(parents=True)

    results = clean_repositories(catalog, catalog.repositories, dry_run=False)

    removed = {result.message.split(":", 1)[0] for result in results if result.action == "removed"}
    assert removed == {
        "target", "node_modules", ".venv", "venv", "__pycache__",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", ".zig-cache", "zig-cache",
    }
    for name in removed:
        owner_dir = zig if name in {".zig-cache", "zig-cache"} else rust
        assert not (owner_dir / name).exists()
    assert (rust / "dist").is_dir()
    assert (rust / "notes.txt").is_file()
    assert (outside / "keep.txt").is_file()
    assert all(not result.failed for result in results)


def test_clean_dry_run_plans_without_removing(tmp_path: Path, git_environment: None) -> None:
    catalog = make_catalog(tmp_path)
    rust = checkout(catalog, "tool")
    (rust / "target").mkdir()
    (rust / "node_modules").mkdir()

    results = clean_repositories(catalog, catalog.repositories, dry_run=True)

    assert by_artifact(results)["target"].action == "planned"
    assert by_artifact(results)["node_modules"].action == "planned"
    assert (rust / "target").is_dir()
    assert (rust / "node_modules").is_dir()


def test_clean_refuses_a_candidate_replaced_after_inspection(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    catalog = make_catalog(tmp_path)
    rust = checkout(catalog, "tool")
    (rust / "target").mkdir()
    original_stat = os.stat
    altered = False

    def stat_after_replacement(
        path: str | os.PathLike[str] | int,
        *,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> os.stat_result:
        nonlocal altered
        result = original_stat(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        if not altered and str(path) == "target" and dir_fd is not None:
            altered = True
            fields = list(result)
            fields[1] += 1
            return os.stat_result(fields)
        return result

    monkeypatch.setattr(artifacts_module.os, "stat", stat_after_replacement)

    results = clean_repositories(catalog, catalog.repositories, dry_run=False)

    assert altered is True
    assert by_artifact(results)["target"].action == "skipped"
    assert "changed during inspection" in by_artifact(results)["target"].message
    assert (rust / "target").is_dir()


def test_clean_refuses_symlink_tracked_and_nested_checkout(
    tmp_path: Path, git_environment: None
) -> None:
    catalog = make_catalog(tmp_path)
    rust = checkout(catalog, "tool")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep\n", encoding="utf-8")
    (rust / "node_modules").symlink_to(outside, target_is_directory=True)
    (rust / "target").mkdir()
    (rust / "target" / "keep").write_text("tracked\n", encoding="utf-8")
    git("add", "target/keep", cwd=rust)
    git("commit", "-m", "keep build output", cwd=rust)
    (rust / ".venv").mkdir()
    (rust / ".venv" / ".git").mkdir()

    results = clean_repositories(catalog, catalog.repositories, dry_run=False)

    found = by_artifact(results)
    assert "symlink" in found["node_modules"].message
    assert "tracked by Git" in found["target"].message
    assert "contains a checkout" in found[".venv"].message
    assert all(result.action == "skipped" for result in results)
    assert (outside / "keep.txt").is_file()
    assert (rust / "target" / "keep").is_file()
    assert (rust / ".venv" / ".git").is_dir()


def test_clean_leaves_uncatalogued_and_unverified_checkouts(
    tmp_path: Path, git_environment: None
) -> None:
    catalog = make_catalog(tmp_path)
    stray = catalog.root / "stray"
    git("init", "--initial-branch=main", str(stray))
    git("remote", "add", "origin", "https://github.com/acme/stray.git", cwd=stray)
    (stray / "target").mkdir()
    catalogued = repository_path(catalog, find_repository(catalog, "acme/tool"))
    catalogued.mkdir(parents=True)
    (catalogued / "target").mkdir()

    results = clean_repositories(catalog, catalog.repositories, dry_run=False)

    assert {result.repository for result in results} == {"acme/tool"}
    assert all(result.action == "failed" for result in results)
    assert "unverified checkout" in results[0].message
    assert (stray / "target").is_dir()
    assert (catalogued / "target").is_dir()


def test_clean_respects_repo_and_tag_filters(tmp_path: Path, git_environment: None) -> None:
    catalog = make_catalog(tmp_path)
    rust = checkout(catalog, "tool")
    zig = checkout(catalog, "ziggy")
    swift = checkout(catalog, "mine", "joshuarli")
    (rust / "target").mkdir()
    (rust / "node_modules").mkdir()
    (zig / ".zig-cache").mkdir()
    (swift / ".build").mkdir()

    tagged = clean_repositories(
        catalog, cmd_common.select_repositories(catalog, (), ("rust",)), dry_run=False
    )
    assert {result.message.split(":", 1)[0] for result in tagged} == {"target", "node_modules"}
    assert (zig / ".zig-cache").is_dir()
    assert (swift / ".build").is_dir()

    named = clean_repositories(
        catalog,
        cmd_common.select_repositories(catalog, ("joshuarli/mine",), ()),
        dry_run=False,
    )
    assert [result.action for result in named] == ["removed"]
    assert not (swift / ".build").exists()


def test_clean_rejects_invalid_job_counts(tmp_path: Path) -> None:
    catalog = make_catalog(tmp_path)

    with pytest.raises(ValueError, match="jobs must be at least one"):
        clean_repositories(catalog, catalog.repositories, dry_run=True, jobs=0)


def test_clean_is_registered_in_cli_parser(
    tmp_path: Path,
    git_environment: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = cli_module._parser().parse_args(["clean", "--dry-run", "--tag", "rust"])
    assert args.command == "clean"
    assert args.dry_run is True
    assert args.tag == ["rust"]

    catalog = make_catalog(tmp_path)
    rust = checkout(catalog, "tool")
    (rust / "target").mkdir()
    monkeypatch.setattr(cmd_common, "default_catalog", lambda: catalog)

    assert clean_cmd._clean(args) == 0
    out = capsys.readouterr().out
    assert "acme/tool: planned: target:" in out
    assert (rust / "target").is_dir()


def test_clean_reports_when_no_artifacts_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    catalog = make_catalog(tmp_path)
    args = cli_module._parser().parse_args(["clean"])
    monkeypatch.setattr(cmd_common, "default_catalog", lambda: catalog)

    assert clean_cmd._clean(args) == 0
    assert capsys.readouterr().out.strip() == "no cached build artifacts"
