"""Count lines of code in catalogued repositories with the `loc` tool.

`fleet/loc/v1` tracks the result so `repomod deps render` can put a language
breakdown of the fleet into the dashboard. The counts describe the checkout
each repository was at when the snapshot ran; the recorded commit says which
one that was. Forks and private repositories are counted like every other
repository; the dashboard decides which ones to show.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from repomod import paths
from repomod.catalog import Catalog, atomic_write, repository_path
from repomod.dependencies.git_tree import GitError, default_commit

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from repomod.types import Repository

SCHEMA_VERSION = 1
LOC = paths.LOC
_TIMEOUT_SECONDS = 900
_COMPLETE = "complete"
_FAILED = "failed"
_UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class Inspection:
    repository: str
    state: str
    commit: str | None
    payload: dict[str, object] | None
    error: str | None


@dataclass(frozen=True, slots=True)
class Snapshot:
    output: Path
    repositories: tuple[Inspection, ...]
    written: tuple[Path, ...]
    deleted: tuple[Path, ...]


def snapshot(
    catalog: Catalog,
    repositories: Sequence[Repository],
    *,
    output: Path = LOC,
    filtered: bool = False,
    workers: int = 4,
) -> Snapshot:
    inspected = _inspect_all(catalog, repositories, workers=workers)
    entries = _entries(output, inspected)
    written: list[Path] = []
    for item in inspected:
        target = _repository_path(output, item.repository)
        if _write_if_changed(target, serialize(_repository_dict(item))):
            written.append(target)
    index_path = output / "index.json"
    version = _loc_version()
    if _write_if_changed(index_path, serialize(_index_dict(entries, version))):
        written.append(index_path)
    deleted = () if filtered else _delete_unselected(output, set(entries))
    return Snapshot(output, tuple(inspected), tuple(written), deleted)


def _inspect_all(
    catalog: Catalog, repositories: Sequence[Repository], *, workers: int
) -> list[Inspection]:
    if not repositories:
        return []
    inspect = partial(_inspect, catalog)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return list(pool.map(inspect, repositories))


def _inspect(catalog: Catalog, repository: Repository) -> Inspection:
    name = str(repository.id)
    try:
        path = repository_path(catalog, repository)
    except OSError as error:
        return Inspection(name, _UNAVAILABLE, None, None, f"cannot resolve the checkout path: {error}")
    if path.is_symlink() or not path.is_dir():
        return Inspection(name, _UNAVAILABLE, None, None, "no checkout at the catalogued path")
    try:
        commit = default_commit(path)
    except GitError as error:
        return Inspection(name, _FAILED, None, None, str(error))
    executable = shutil.which("loc")
    if executable is None:
        return Inspection(
            name,
            _FAILED,
            commit,
            None,
            "`loc` is required; build it from ~/repos/loc (cargo install --path .)",
        )
    try:
        result = subprocess.run(
            [executable, "--git", ".", "--output", "json"],
            cwd=path,
            capture_output=True,
            encoding="utf-8",
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return Inspection(name, _FAILED, commit, None, f"cannot run loc: {error}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or f"loc exited {result.returncode}").strip()
        return Inspection(name, _FAILED, commit, None, detail)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return Inspection(name, _FAILED, commit, None, f"loc produced invalid JSON: {error}")
    if not _valid(payload):
        return Inspection(name, _FAILED, commit, None, "loc produced an unexpected JSON shape")
    assert isinstance(payload, dict)
    payload = dict(payload)
    payload["paths"] = [name]
    return Inspection(name, _COMPLETE, commit, payload, None)


def _valid(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    languages = payload.get("languages")
    totals = payload.get("totals")
    if not isinstance(languages, list) or not isinstance(totals, dict):
        return False
    for language in languages:
        if not isinstance(language, dict):
            return False
        if not isinstance(language.get("name"), str):
            return False
        if not isinstance(language.get("file_count"), int):
            return False
        lines = language.get("lines")
        if not isinstance(lines, dict):
            return False
        for key in ("total", "code", "comment", "blank", "shebang"):
            if not isinstance(lines.get(key), int):
                return False
    return True


def _fingerprint(payload: Mapping[str, object] | None) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _entries(output: Path, inspected: Sequence[Inspection]) -> dict[str, dict[str, object]]:
    recorded = _recorded_entries(output)
    entries: dict[str, dict[str, object]] = {}
    for item in inspected:
        fingerprint = _fingerprint(item.payload)
        previous = recorded.get(item.repository)
        commit = item.commit
        if (
            previous is not None
            and previous.get("state") == item.state
            and previous.get("loc_fingerprint") == fingerprint
            and isinstance(previous.get("commit"), str)
        ):
            commit = previous["commit"]
        entries[item.repository] = {
            "commit": commit,
            "state": item.state,
            "loc_fingerprint": fingerprint,
        }
    return entries


def _recorded_entries(output: Path) -> dict[str, dict[str, object]]:
    try:
        source = json.loads((output / "index.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
        return {}
    repositories = source.get("repositories") if isinstance(source, dict) else None
    if not isinstance(repositories, dict):
        return {}
    return {name: entry for name, entry in repositories.items() if isinstance(entry, dict)}


def _repository_path(output: Path, repository: str) -> Path:
    owner, name = repository.split("/", 1)
    return output / "repos" / owner / f"{name}.json"


def _repository_dict(item: Inspection) -> dict[str, object]:
    return {
        "schema": SCHEMA_VERSION,
        "repository": item.repository,
        "commit": item.commit,
        "state": item.state,
        "loc": item.payload,
        "error": item.error,
    }


def _index_dict(entries: Mapping[str, dict[str, object]], version: str) -> dict[str, object]:
    return {
        "schema": SCHEMA_VERSION,
        "loc_version": version,
        "repositories": {key: entries[key] for key in sorted(entries)},
    }


def serialize(value: dict[str, object]) -> str:
    return json.dumps(value, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def _loc_version() -> str:
    executable = shutil.which("loc")
    if executable is None:
        return "unknown"
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _write_if_changed(path: Path, content: str) -> bool:
    payload = content.encode("utf-8")
    try:
        if path.read_bytes() == payload:
            return False
    except FileNotFoundError:
        pass
    atomic_write(path, content)
    return True


def _unselected_files(output: Path, selected: set[str]) -> tuple[Path, ...]:
    root = output / "repos"
    if not root.is_dir():
        return ()
    found: list[Path] = []
    for owner_dir in sorted(root.iterdir()):
        if owner_dir.is_symlink() or not owner_dir.is_dir():
            continue
        for file in sorted(owner_dir.iterdir()):
            if file.is_dir() or file.suffix != ".json":
                continue
            if f"{owner_dir.name}/{file.stem}" not in selected:
                found.append(file)
    return tuple(found)


def _delete_unselected(output: Path, selected: set[str]) -> tuple[Path, ...]:
    deleted: list[Path] = []
    for path in _unselected_files(output, selected):
        path.unlink()
        deleted.append(path)
    root = output / "repos"
    if root.is_dir():
        for owner_dir in sorted(root.iterdir()):
            if owner_dir.is_symlink() or not owner_dir.is_dir():
                continue
            if not any(owner_dir.iterdir()):
                owner_dir.rmdir()
    return tuple(deleted)
