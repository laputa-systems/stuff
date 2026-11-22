from __future__ import annotations

from pathlib import Path

from repomod.run_cache import cached
from repomod.types import Finding, Repository, Rule, TagPredicate, operational, violation
from repomod.workflow_policy import is_fork_workflow


def _workflow_files(
    root: Path, repository: Repository | None = None
) -> tuple[list[Path], list[tuple[str, str]]]:
    github = root / ".github"
    workflows = github / "workflows"
    if github.is_symlink():
        return [], [(".github", "workflow parent directory is a symlink")]
    if not workflows.exists() and not workflows.is_symlink():
        return [], []
    if workflows.is_symlink() or not workflows.is_dir():
        return [], [(".github/workflows", "workflow directory is not a real directory")]
    files: list[Path] = []
    problems: list[tuple[str, str]] = []
    for child in sorted(workflows.iterdir(), key=lambda item: item.name.casefold()):
        if child.suffix.casefold() not in {".yml", ".yaml"}:
            continue
        if repository is not None and "fork" in repository.tags and not is_fork_workflow(child.name):
            continue
        if child.is_symlink():
            problems.append((child.relative_to(root).as_posix(), "workflow symlinks are not followed"))
        elif child.is_file():
            files.append(child)
    return files, problems


def workflow_files(
    root: Path, repository: Repository | None = None
) -> tuple[list[Path], list[tuple[str, str]]]:
    return cached(
        ("workflow_files", root, repository is not None and "fork" in repository.tags),
        lambda: _workflow_files(root, repository),
    )


def _read_workflow_sources(
    root: Path, repository: Repository | None = None
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    files, problems = workflow_files(root, repository)
    sources: list[tuple[str, str]] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        try:
            sources.append((relative, path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError) as error:
            problems.append((relative, f"cannot read workflow: {error}"))
    return sources, problems


def read_workflow_sources(
    root: Path, repository: Repository | None = None
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    return cached(
        ("workflow_sources", root, repository is not None and "fork" in repository.tags),
        lambda: _read_workflow_sources(root, repository),
    )


def _fork_workflow_findings(root: Path, repository: Repository) -> list[Finding]:
    files, problems = workflow_files(root)
    rule = "fork-workflow-names"
    findings = [operational(repository, rule, path, message) for path, message in problems]
    findings.extend(
        violation(
            repository,
            rule,
            path.relative_to(root).as_posix(),
            "use a fleet workflow name and retire the upstream workflow",
        )
        for path in files
        if not is_fork_workflow(path.name)
    )
    return findings


def fork_workflow_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            "fork-workflow-names",
            "Require forks to use fleet workflow names",
            TagPredicate(all_of=frozenset({"fork"})),
            _fork_workflow_findings,
            None,
            None,
            (),
        ),
    )
