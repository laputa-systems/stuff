from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from repomod.git import GitError
from repomod.rules.actions import _validate_workflows
from repomod.rules.consistency import _declared_make_targets
from repomod.rules.languages import _language_sources
from repomod.rules.lint import _root_makefile, workflow_source
from repomod.rules.workflow_settings import _local_default_branch
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


_MAKE_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*=(?:[A-Za-z0-9_./:$-]|\$\{\{ *[A-Za-z0-9_.]+ *\}\})*")


def _make_command(command: str, targets: frozenset[str]) -> bool:
    if "\n" in command.strip():
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if len(tokens) < 2 or tokens[0] != "make":
        return False
    rest = tokens[1:]
    return (
        sum(token in targets for token in rest) == 1
        and all(
            token in targets or _MAKE_ASSIGNMENT.fullmatch(token)
            for token in rest
        )
    )


def _trigger_problem(document: dict[str, Any], root: Path) -> tuple[bool, str | None]:
    trigger = document.get("on")
    if isinstance(trigger, str):
        return trigger == "pull_request", None
    if isinstance(trigger, list):
        return "pull_request" in trigger, None
    if not isinstance(trigger, dict):
        return False, "cannot determine the workflow triggers"
    if "pull_request" not in trigger:
        return False, None
    options = trigger["pull_request"]
    if options is None:
        return True, None
    if not isinstance(options, dict):
        return True, "unsupported pull_request configuration"
    for key in ("paths", "paths-ignore", "branches-ignore"):
        if key in options:
            return True, f"unsupported pull_request {key}"
    if "branches" in options:
        branch = _local_default_branch(root)
        branches = options["branches"]
        if branch is None or not isinstance(branches, list) or branch not in branches:
            return True, "unsupported or ambiguous pull_request branches"
    if "types" in options:
        types = options["types"]
        if not isinstance(types, list) or not all(
            event in types for event in ("opened", "synchronize", "reopened")
        ):
            return True, "unsupported pull_request types: require opened, synchronize, reopened"
    return True, None


def _run_shell(*scopes: dict[str, Any]) -> object:
    for scope in scopes:
        if "shell" in scope:
            return scope["shell"]
        defaults = scope.get("defaults")
        run = defaults.get("run") if isinstance(defaults, dict) else None
        if isinstance(run, dict) and "shell" in run:
            return run["shell"]
    return None


def _step_problem(
    document: dict[str, Any], job: dict[str, Any], step: dict[str, Any], targets: frozenset[str]
) -> str | None:
    if "if" in job:
        return "unsupported job-level if"
    if "continue-on-error" in job and job["continue-on-error"] is not False:
        return "unsupported job continue-on-error"
    if "uses" in job:
        return "unsupported reusable-workflow job uses"
    if "if" in step:
        return "unsupported step-level if"
    if "continue-on-error" in step and step["continue-on-error"] is not False:
        return "unsupported step continue-on-error"
    shell = _run_shell(step, job, document)
    if shell is not None and (not isinstance(shell, str) or shell.split()[0] not in ("bash", "sh")):
        return "unsupported step shell"
    command = step.get("run")
    if isinstance(command, str) and "\n" not in command.strip():
        try:
            tokens = shlex.split(command)
        except ValueError:
            tokens = []
        if tokens and tokens[0] == "make":
            flag = next((token for token in tokens[1:] if token.startswith("-")), None)
            if flag is not None:
                return f"unsupported make flag {flag}; put make test in its own step"
            operator = next((token for token in ("||", "&&", ";", "|", ">", "<") if token in command), None)
            if operator is not None:
                return f"unsupported shell operator {operator}; put make test in its own step"
    if not isinstance(command, str) or not _make_command(command, targets):
        return ("unsupported multi-line or wrapped command; cannot verify failure propagation; "
                "put make test in its own step; "
                "for a container, use a single-line make test-ci step whose Make target wraps the container run")
    return None


def _pull_request_workflows(
    root: Path,
) -> tuple[dict[str, tuple[list[str], list[str]]], list[tuple[str, str]], bool]:
    sources, problems = read_workflow_sources(root)
    workflows: dict[str, tuple[list[str], list[str]]] = {}
    supported = False
    for path, source in sources:
        try:
            document = YAML(typ="safe").load(source)
        except YAMLError as error:
            problems.append((path, f"cannot parse workflow YAML: {error}"))
            continue
        if not isinstance(document, dict):
            problems.append((path, "cannot determine the workflow triggers"))
            continue
        pr, trigger_problem = _trigger_problem(document, root)
        if not pr:
            if trigger_problem is not None:
                problems.append((path, trigger_problem))
            continue
        commands: list[str] = []
        unsupported: list[str] = []
        jobs = document.get("jobs", {})
        if isinstance(jobs, dict):
            for job in jobs.values():
                if not isinstance(job, dict):
                    continue
                if "uses" in job:
                    unsupported.append("unsupported reusable-workflow job uses")
                steps = job.get("steps", [])
                if not isinstance(steps, list):
                    continue
                for step in steps:
                    if not isinstance(step, dict) or not isinstance(step.get("run"), str):
                        continue
                    command = step["run"]
                    commands.append(command)
                    if _MAKE_TEST.search(command) or re.search(r"\bmake\s+(?:-\S+\s+)*test(?:-ci)?\b", command):
                        problem = trigger_problem or _step_problem(document, job, step, frozenset({"test", "test-ci"}))
                        if problem is None:
                            supported = True
                        else:
                            unsupported.append(problem)
        workflows[path] = (commands, unsupported)
    return workflows, problems, supported


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
    workflows, problems, supported = _pull_request_workflows(root)
    if problems:
        return [operational(repository, RULE, path, message) for path, message in problems]
    if supported:
        return []
    unsupported = [(path, message) for path, (_, messages) in workflows.items() for message in messages]
    if unsupported:
        return [violation(repository, RULE, path, message) for path, message in unsupported]
    direct = sorted(
        path
        for path, (commands, _) in workflows.items()
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
