from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from git_helpers import git

from repomod import loc as loc_module
from repomod.catalog import Catalog, load_catalog
from repomod.cli import _parser
from repomod.cmd import loc as cmd_loc
from repomod.dependencies import loc_view

DOCUMENT = "version = 1\n\n[workspace]\nroot = \"~/repos\"\npersonal_owner = \"acme\"\n\n"


def _catalog(tmp_path: Path, entries: str) -> Catalog:
    path = tmp_path / "catalog.toml"
    path.write_text(DOCUMENT + entries, encoding="utf-8")
    return load_catalog(path, {"HOME": str(tmp_path), "REPOMOD_ROOT": str(tmp_path / "fleet")})


def _checkout(tmp_path: Path, name: str, files: dict[str, str]) -> Path:
    path = tmp_path / "fleet" / name
    path.mkdir(parents=True)
    git("init", "--initial-branch=main", str(path))
    for relative, content in files.items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    git("add", "-A", cwd=path)
    git("commit", "-m", "initial", cwd=path)
    git("remote", "add", "origin", f"https://github.com/acme/{name}.git", cwd=path)
    head = git("rev-parse", "HEAD", cwd=path)
    git("update-ref", "refs/remotes/origin/main", head, cwd=path)
    git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main", cwd=path)
    return path


def _loc_payload(marker: str) -> str:
    return json.dumps(
        {
            "schema_version": 2,
            "paths": ["."],
            "totals": {
                "file_count": 2,
                "lines": {"total": 40, "code": 30, "comment": 5, "blank": 5, "shebang": 0},
                "bytes": 1024,
            },
            "languages": [
                {
                    "name": "XSH",
                    "file_count": 1,
                    "lines": {"total": 20, "code": 15, "comment": 2, "blank": 3, "shebang": 0},
                    "bytes": 512,
                },
                {
                    "name": f"Lang-{marker}",
                    "file_count": 1,
                    "lines": {"total": 20, "code": 15, "comment": 3, "blank": 2, "shebang": 0},
                    "bytes": 512,
                },
            ],
            "hidden_languages": 0,
        }
    )


def _fake_loc(
    monkeypatch: pytest.MonkeyPatch,
    payloads: dict[str, str] | None = None,
    *,
    returncode: int = 0,
    stderr: str = "",
) -> None:
    real_run = subprocess.run
    monkeypatch.setattr(loc_module.shutil, "which", lambda _name: "/usr/local/bin/loc")

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        if command[0] == "git":
            return real_run(command, **kwargs)
        if "--version" in command:
            return SimpleNamespace(returncode=0, stdout="loc 2.0.0 (git testversion)", stderr="")
        cwd = Path(str(kwargs["cwd"])).name
        if returncode != 0:
            return SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)
        return SimpleNamespace(returncode=0, stdout=(payloads or {}).get(cwd, _loc_payload(cwd)), stderr="")

    monkeypatch.setattr(loc_module.subprocess, "run", fake_run)


def test_snapshot_writes_tracked_data_with_scrubbed_paths(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _checkout(tmp_path, "active", {"tool.xsh": "# comment\nprint 1\n", "README.md": "hi\n"})
    catalog = _catalog(tmp_path, '[repos."acme"]\nactive = ["tool"]\nignored = ["IGNORE", "tool"]\n')
    _fake_loc(monkeypatch)

    result = loc_module.snapshot(catalog, catalog.repositories, output=tmp_path / "v1", workers=1)

    repository = tmp_path / "v1" / "repos" / "acme" / "active.json"
    assert repository.is_file()
    assert not (tmp_path / "v1" / "repos" / "acme" / "ignored.json").exists()
    source = json.loads(repository.read_text(encoding="utf-8"))
    assert source["repository"] == "acme/active"
    assert source["state"] == "complete"
    assert source["commit"] == git("rev-parse", "HEAD", cwd=tmp_path / "fleet" / "active")
    assert source["loc"]["paths"] == ["acme/active"]
    index = json.loads((tmp_path / "v1" / "index.json").read_text(encoding="utf-8"))
    assert set(index["repositories"]) == {"acme/active"}
    assert index["repositories"]["acme/active"]["state"] == "complete"
    assert result.written


def test_snapshot_is_a_fixed_point(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _checkout(tmp_path, "active", {"tool.xsh": "print 1\n"})
    catalog = _catalog(tmp_path, '[repos."acme"]\nactive = ["tool"]\n')
    _fake_loc(monkeypatch)

    loc_module.snapshot(catalog, catalog.repositories, output=tmp_path / "v1", workers=1)
    before = {
        path.relative_to(tmp_path / "v1").as_posix(): path.read_bytes()
        for path in (tmp_path / "v1").rglob("*.json")
    }
    result = loc_module.snapshot(catalog, catalog.repositories, output=tmp_path / "v1", workers=1)
    after = {
        path.relative_to(tmp_path / "v1").as_posix(): path.read_bytes()
        for path in (tmp_path / "v1").rglob("*.json")
    }

    assert result.written == ()
    assert before == after


def test_full_catalog_deletes_stale_entries_and_filtered_keeps_them(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _checkout(tmp_path, "keep", {"keep.xsh": "print 1\n"})
    _checkout(tmp_path, "drop", {"drop.xsh": "print 2\n"})
    full = _catalog(tmp_path, '[repos."acme"]\nkeep = ["tool"]\ndrop = ["tool"]\n')
    _fake_loc(monkeypatch)
    loc_module.snapshot(full, full.repositories, output=tmp_path / "v1", workers=1)

    shrunk = _catalog(tmp_path, '[repos."acme"]\nkeep = ["tool"]\n')
    kept = loc_module.snapshot(shrunk, shrunk.repositories, output=tmp_path / "v1", filtered=True, workers=1)
    assert (tmp_path / "v1" / "repos" / "acme" / "drop.json").is_file()
    assert kept.deleted == ()

    shrunk_repositories = [
        repository for repository in shrunk.repositories if repository.id.name == "keep"
    ]
    removed = loc_module.snapshot(shrunk, shrunk_repositories, output=tmp_path / "v1", workers=1)
    assert not (tmp_path / "v1" / "repos" / "acme" / "drop.json").is_file()
    assert removed.deleted


def test_failing_loc_records_the_failure(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _checkout(tmp_path, "active", {"tool.xsh": "print 1\n"})
    catalog = _catalog(tmp_path, '[repos."acme"]\nactive = ["tool"]\n')
    _fake_loc(monkeypatch, returncode=1, stderr="cannot read a file")

    result = loc_module.snapshot(catalog, catalog.repositories, output=tmp_path / "v1", workers=1)

    source = json.loads((tmp_path / "v1" / "repos" / "acme" / "active.json").read_text(encoding="utf-8"))
    assert source["state"] == "failed"
    assert source["loc"] is None
    assert source["error"] == "cannot read a file"
    index = json.loads((tmp_path / "v1" / "index.json").read_text(encoding="utf-8"))
    assert index["repositories"]["acme/active"]["state"] == "failed"
    assert result.repositories[0].state == "failed"


def test_unexpected_loc_output_records_the_failure(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _checkout(tmp_path, "active", {"tool.xsh": "print 1\n"})
    catalog = _catalog(tmp_path, '[repos."acme"]\nactive = ["tool"]\n')
    monkeypatch.setattr(loc_module.shutil, "which", lambda _name: "/usr/local/bin/loc")
    real_run = subprocess.run

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        if command[0] == "git":
            return real_run(command, **kwargs)
        return SimpleNamespace(returncode=0, stdout="not json", stderr="")

    monkeypatch.setattr(loc_module.subprocess, "run", fake_run)

    result = loc_module.snapshot(catalog, catalog.repositories, output=tmp_path / "v1", workers=1)

    assert result.repositories[0].state == "failed"
    assert "invalid JSON" in (result.repositories[0].error or "")


def test_missing_checkout_is_unavailable(
    tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    catalog = _catalog(tmp_path, '[repos."acme"]\nactive = ["tool"]\n')
    monkeypatch.setattr(loc_module.shutil, "which", lambda _name: "/usr/local/bin/loc")

    result = loc_module.snapshot(catalog, catalog.repositories, output=tmp_path / "v1", workers=1)

    assert result.repositories[0].state == "unavailable"
    source = json.loads((tmp_path / "v1" / "repos" / "acme" / "active.json").read_text(encoding="utf-8"))
    assert source["loc"] is None


def test_missing_loc_binary_exits_2(tmp_path: Path, git_environment: None, monkeypatch: pytest.MonkeyPatch) -> None:
    _checkout(tmp_path, "active", {"tool.xsh": "print 1\n"})
    monkeypatch.setattr(cmd_loc.shutil, "which", lambda _name: None)
    args = _parser().parse_args(["loc", "snapshot"])

    assert cmd_loc._loc(args) == 2


def test_view_loads_renders_and_hides_non_reportable_repositories(tmp_path: Path) -> None:
    root = tmp_path / "v1"
    for name, code in (("acme/own", 100), ("acme/fork", 900), ("acme/private", 700)):
        target = Path(f"{root / 'repos' / name}.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "repository": name,
                    "commit": "abc123",
                    "state": "complete",
                    "loc": {
                        "schema_version": 2,
                        "paths": [name],
                        "totals": {
                            "file_count": 1,
                            "lines": {"total": code, "code": code, "comment": 0, "blank": 0, "shebang": 0},
                            "bytes": code * 10,
                        },
                        "languages": [
                            {
                                "name": "XSH",
                                "file_count": 1,
                                "lines": {"total": code, "code": code, "comment": 0, "blank": 0, "shebang": 0},
                                "bytes": code * 10,
                            }
                        ],
                        "hidden_languages": 0,
                    },
                    "error": None,
                }
            ),
            encoding="utf-8",
        )
    (root / "index.json").write_text(
        json.dumps({"schema": 1, "loc_version": "loc 2.0.0 (git abcdef1)", "repositories": {}}),
        encoding="utf-8",
    )

    data = loc_view.load(root)
    assert {repository.name for repository in data.repositories} == {"acme/own", "acme/fork", "acme/private"}
    assert data.version == "loc 2.0.0 (git abcdef1)"

    body = loc_view.page(data, forks=["acme/fork"], hidden=["acme/private"])
    assert "acme/own" in body
    assert "acme/fork" not in body
    assert "acme/private" not in body
    assert "100" in body
    assert "900" not in body
    assert "700" not in body


def test_view_renders_an_empty_state_without_data(tmp_path: Path) -> None:
    data = loc_view.load(tmp_path / "missing")
    assert data.missing
    body = loc_view.page(data, forks=(), hidden=())
    assert "No line counts" in body
