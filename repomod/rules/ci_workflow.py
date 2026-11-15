from __future__ import annotations

import re
from pathlib import Path

from repomod.git import GitError
from repomod.rules.actions import _validate_workflows
from repomod.rules.consistency import _declared_make_targets
from repomod.rules.languages import _language_sources
from repomod.rules.lint import _root_makefile, workflow_source
from repomod.rules.workflow_redundancy import _run_commands, _trigger_events
from repomod.rules.workflows import read_workflow_sources
from repomod.types import Finding, Repository, Rule, TagPredicate, operational, violation

RULE = "gha-test-workflow"
_CI_WORKFLOW_NAMES = ("ci.yml", "ci.yaml")
_MAKE_TEST = re.compile(r"(?:^|&&|\|\||;)\s*make\b[^;&|]*?\stest(?:-ci)?(?![\w-])")
_DIRECT_TEST = re.compile(
    r"\bcargo\s+(?:\+\S+\s+)?(?:test|nextest)\b"
    r"|\bpytest\b"
    r"|\bvitest\b"
    r"|\b(?:pnpm|npm|yarn)\s+(?:run\s+)?test\b"
    r"|\bnode\s+(?:\S+\s+)*--test\b"
    r"|\bgo\s+test\b"
)


def _covered(repository: Repository) -> bool:
    tags = set(repository.tags)
    return "fork" not in tags or "fork-diverged" in tags


def _pull_request_workflows(root: Path) -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    sources, problems = read_workflow_sources(root)
    workflows: dict[str, list[str]] = {}
    for path, source in sources:
        lines = source.splitlines()
        events = _trigger_events(lines)
        if events is None:
            problems.append((path, "cannot determine the workflow triggers"))
        elif "pull_request" in events:
            workflows[path] = _run_commands(lines)
    return workflows, problems


def _has_test_target(root: Path) -> bool:
    makefile = _root_makefile(root)
    if makefile is None or not makefile.is_file():
        return False
    try:
        targets = _declared_make_targets(makefile)
    except (OSError, UnicodeError):
        return True
    return targets is None or "test" in targets


def _ci_workflow_findings(root: Path, repository: Repository) -> list[Finding]:
    if not _covered(repository):
        return []
    workflows, problems = _pull_request_workflows(root)
    if problems:
        return [operational(repository, RULE, path, message) for path, message in problems]
    if any(_MAKE_TEST.search(command) for commands in workflows.values() for command in commands):
        return []
    direct = sorted(
        path
        for path, commands in workflows.items()
        if any(_DIRECT_TEST.search(command) for command in commands)
    )
    if direct:
        return [
            violation(
                repository,
                RULE,
                path,
                "runs tests directly on pull requests; run make test or make test-ci instead so CI "
                "and local verification share one entry point",
            )
            for path in direct
        ]
    if not _has_test_target(root):
        return [
            violation(
                repository,
                RULE,
                "Makefile",
                "no pull request workflow runs the tests; add a root Makefile test target and a "
                "workflow that runs make test",
            )
        ]
    existing = next(
        (name for name in _CI_WORKFLOW_NAMES if (root / ".github" / "workflows" / name).exists()), None
    )
    if existing is not None:
        return [
            violation(
                repository,
                RULE,
                f".github/workflows/{existing}",
                "no pull request workflow runs make test; add a make test step",
            )
        ]
    return [
        violation(
            repository,
            RULE,
            ".github/workflows/ci.yml",
            "add a CI workflow that runs make test on pull requests",
            fixable=True,
        )
    ]


def _ci_workflow_fix(root: Path, repository: Repository) -> dict[str, str]:
    findings = _ci_workflow_findings(root, repository)
    if not any(finding.fixable for finding in findings):
        return {}
    if any((root / ".github" / "workflows" / name).exists() for name in _CI_WORKFLOW_NAMES):
        raise GitError("ci workflow appeared while planning the fix")
    return {
        ".github/workflows/ci.yml": workflow_source(
            root, _language_sources(root), name="ci", step="test", target="test"
        )
    }


def ci_workflow_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            RULE,
            "Require a pull request workflow that runs make test",
            TagPredicate(),
            _ci_workflow_findings,
            _ci_workflow_fix,
            "ci(repomod): run make test on pull requests",
            (".github/workflows/ci.yml",),
            _validate_workflows,
        ),
    )
