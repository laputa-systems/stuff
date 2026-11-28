from __future__ import annotations

import contextlib
import os
import stat
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from repomod.catalog import Catalog, CatalogError, repository_path
from repomod.git import GitError, repository_lock, status, tracked_paths
from repomod.types import Repository

type ArtifactAction = Literal["absent", "planned", "removed", "skipped", "failed"]

_ARTIFACT_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC

ARTIFACTS_BY_TAG: dict[str, tuple[str, ...]] = {
    "rust": ("target",),
    "python": (".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"),
    "javascript": ("node_modules",),
    "typescript": ("node_modules",),
    "zig": (".zig-cache", "zig-cache"),
    "swift": (".build",),
}


@dataclass(frozen=True, slots=True)
class ArtifactResult:
    repository: str
    path: Path | None
    action: ArtifactAction
    message: str

    @property
    def failed(self) -> bool:
        return self.action == "failed"


def artifact_names(repository: Repository) -> tuple[str, ...]:
    names: set[str] = set()
    for tag in repository.tags:
        names.update(ARTIFACTS_BY_TAG.get(tag, ()))
    return tuple(sorted(names, key=str.casefold))


def _present(checkout: Path, names: tuple[str, ...]) -> list[Path]:
    wanted = frozenset(names)
    try:
        with os.scandir(checkout) as entries:
            found = [Path(entry.path) for entry in entries if entry.name in wanted]
    except FileNotFoundError:
        return []
    return sorted(found, key=lambda path: path.name.casefold())


def _remove_tree(fd: int, parent_fd: int, name: str) -> None:
    with os.scandir(fd) as entries:
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                child = os.open(entry.name, _ARTIFACT_FLAGS, dir_fd=fd)
                try:
                    with contextlib.suppress(FileNotFoundError):
                        _remove_tree(child, fd, entry.name)
                finally:
                    os.close(child)
            else:
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(entry.name, dir_fd=fd)
    os.rmdir(name, dir_fd=parent_fd)


def clean_one(catalog: Catalog, repository: Repository, *, dry_run: bool) -> list[ArtifactResult]:
    names = artifact_names(repository)
    if not names:
        return []
    label = str(repository.id)
    try:
        checkout = repository_path(catalog, repository)
    except CatalogError as error:
        return [ArtifactResult(label, None, "failed", str(error))]
    candidates = _present(checkout, names)
    if not candidates:
        return []
    try:
        current = status(checkout, repository.id)
    except GitError as error:
        return [ArtifactResult(label, checkout, "failed", str(error))]
    if not current.valid or not current.origin_valid:
        detail = current.error or "checkout origin does not match the catalog"
        return [
            ArtifactResult(label, checkout, "failed", f"{detail}; refusing to clean an unverified checkout")
        ]
    if current.dirty:
        return [
            ArtifactResult(label, checkout, "skipped", "checkout has uncommitted changes; refusing to clean")
        ]
    try:
        tracked = tracked_paths(checkout, tuple(path.name for path in candidates))
    except GitError as error:
        return [ArtifactResult(label, checkout, "failed", str(error))]
    tracked_names = {value.split("/", 1)[0] for value in tracked}

    results: list[ArtifactResult] = []
    prepared: list[tuple[Path, int, os.stat_result]] = []
    try:
        checkout_fd = os.open(checkout, _ARTIFACT_FLAGS)
    except OSError as error:
        return [ArtifactResult(label, checkout, "failed", str(error))]
    try:
        for path in candidates:
            name = path.name
            if name in tracked_names:
                results.append(ArtifactResult(label, path, "skipped", f"{name}: tracked by Git; refusing to remove"))
                continue
            if path.is_symlink():
                results.append(ArtifactResult(label, path, "skipped", f"{name}: symlink; refusing to remove"))
                continue
            if not path.is_dir():
                results.append(ArtifactResult(label, path, "skipped", f"{name}: not a directory"))
                continue
            try:
                fd = os.open(name, _ARTIFACT_FLAGS, dir_fd=checkout_fd)
            except OSError as error:
                results.append(ArtifactResult(label, path, "failed", f"{name}: {error}"))
                continue
            try:
                identity = os.fstat(fd)
                try:
                    os.stat(".git", dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    prepared.append((path, fd, identity))
                else:
                    os.close(fd)
                    results.append(
                        ArtifactResult(label, path, "skipped", f"{name}: contains a checkout; refusing to remove")
                    )
            except OSError as error:
                os.close(fd)
                results.append(ArtifactResult(label, path, "failed", f"{name}: {error}"))
        if not prepared:
            return results
        try:
            with repository_lock(catalog.root, repository.id):
                for path, fd, identity in prepared:
                    name = path.name
                    try:
                        current = os.stat(name, dir_fd=checkout_fd, follow_symlinks=False)
                    except FileNotFoundError:
                        results.append(ArtifactResult(label, path, "absent", f"{name}: already removed"))
                        continue
                    except OSError as error:
                        results.append(ArtifactResult(label, path, "failed", f"{name}: {error}"))
                        continue
                    if (
                        current.st_dev != identity.st_dev
                        or current.st_ino != identity.st_ino
                        or stat.S_ISLNK(current.st_mode)
                    ):
                        results.append(
                            ArtifactResult(
                                label, path, "skipped", f"{name}: changed during inspection; refusing to remove"
                            )
                        )
                        continue
                    if dry_run:
                        results.append(ArtifactResult(label, path, "planned", f"{name}: generated build artifact"))
                        continue
                    try:
                        _remove_tree(fd, checkout_fd, name)
                    except OSError as error:
                        results.append(ArtifactResult(label, path, "failed", f"{name}: {error}"))
                    else:
                        results.append(ArtifactResult(label, path, "removed", f"{name}: generated build artifact"))
        except (CatalogError, GitError, OSError) as error:
            for path, _, _ in prepared:
                results.append(ArtifactResult(label, path, "failed", f"{path.name}: {error}"))
    finally:
        for _, fd, _ in prepared:
            os.close(fd)
        os.close(checkout_fd)
    return results


def clean_repositories(
    catalog: Catalog,
    repositories: Sequence[Repository],
    *,
    dry_run: bool,
    jobs: int = 4,
) -> list[ArtifactResult]:
    if jobs < 1:
        raise ValueError("jobs must be at least one")
    if not repositories:
        return []
    results: list[ArtifactResult] = []
    workers = min(jobs, 32, len(repositories))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="repomod-clean") as pool:
        futures = {
            pool.submit(clean_one, catalog, repository, dry_run=dry_run): repository
            for repository in repositories
        }
        for future in as_completed(futures):
            repository = futures[future]
            try:
                results.extend(future.result())
            except Exception as error:
                results.append(ArtifactResult(str(repository.id), None, "failed", str(error)))
    return sorted(
        results,
        key=lambda result: (
            result.repository.casefold(),
            "" if result.path is None else result.path.name.casefold(),
        ),
    )
