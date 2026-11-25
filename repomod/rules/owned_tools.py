from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from repomod.owned_tools import (
    RULE_ID,
    HelpIntegration,
    OwnedTools,
    Producer,
    github_url,
    installer_repositories,
    load_owned_tools,
    needs_coverage,
    tracked_commands,
)
from repomod.run_cache import cached
from repomod.types import Finding, RepoId, Repository, Rule, TagPredicate, operational, violation

_POLICY_PATH = "fleet/policy/owned-tools.toml"
_GITHUB = re.compile(r"github\.com[/:]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:[/#?]|\Z)")
_EXEMPT_TAGS = frozenset({"tool", "build"})


def _read(root: Path, relative: str) -> str | None:
    path = root / relative
    if path.is_symlink() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


_GITHUB_LINK = r"https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)"


def _repo_ids(matches: list[tuple[str, str]]) -> set[str]:
    found = set()
    for owner, raw in matches:
        name = raw.rstrip(".").removesuffix(".git")
        if name:
            found.add(f"{owner}/{name}".casefold())
    return found


_HTML_LINK_OPEN = r'(?:<a href="(?P<href>[^"]+)">(?=(?P=href)</a>))?'


def _maintained_by(text: str, maintainer: str) -> set[str]:
    pattern = re.escape(f"Maintained by {maintainer}: ") + _HTML_LINK_OPEN + _GITHUB_LINK
    return _repo_ids([(match.group(2), match.group(3)) for match in re.finditer(pattern, text)])


def _linked(text: str) -> set[str]:
    return _repo_ids(re.findall(_GITHUB_LINK, text))


def _help_findings(
    root: Path, repository: Repository, policy: OwnedTools, command: str, help_: HelpIntegration
) -> list[Finding]:
    findings: list[Finding] = []
    expected = policy.footer(repository.id)
    source = _read(root, help_.source)
    if source is None:
        findings.append(
            violation(repository, RULE_ID, help_.source, f"{command}: declared help source does not exist")
        )
    elif str(repository.id).casefold() not in (maintained := _maintained_by(source, policy.maintainer)):
        named = sorted(maintained)
        message = (
            f"{command}: help footer names {', '.join(named)} instead of {repository.id}"
            if named
            else f"{command}: help source does not contain {expected!r}"
        )
        findings.append(violation(repository, RULE_ID, help_.source, message))
    test = _read(root, help_.test)
    if test is None:
        findings.append(violation(repository, RULE_ID, help_.test, f"{command}: declared help test does not exist"))
    elif str(repository.id).casefold() not in _linked(test):
        findings.append(
            violation(
                repository,
                RULE_ID,
                help_.test,
                f"{command}: help test does not check the footer's {github_url(repository.id)} link",
            )
        )
    return findings


def _manifest_links(root: Path) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    cargo = _read(root, "Cargo.toml")
    if cargo is not None:
        try:
            manifest = tomllib.loads(cargo)
        except tomllib.TOMLDecodeError:
            manifest = {}
        tables = (manifest.get("package"), manifest.get("workspace", {}).get("package"))
        links.extend(
            ("Cargo.toml", table["repository"])
            for table in tables
            if isinstance(table, dict) and isinstance(table.get("repository"), str)
        )
    package = _read(root, "package.json")
    if package is not None:
        try:
            document = json.loads(package)
        except json.JSONDecodeError:
            document = {}
        value = document.get("repository") if isinstance(document, dict) else None
        if isinstance(value, dict):
            value = value.get("url")
        if isinstance(value, str):
            links.append(("package.json", value))
    pyproject = _read(root, "pyproject.toml")
    if pyproject is not None:
        try:
            project = tomllib.loads(pyproject).get("project", {})
        except tomllib.TOMLDecodeError:
            project = {}
        urls = project.get("urls") if isinstance(project, dict) else None
        if isinstance(urls, dict):
            links.extend(("pyproject.toml", value) for value in urls.values() if isinstance(value, str))
    return links


def _identity_findings(root: Path, repository: Repository, producer: Producer) -> list[Finding]:
    allowed = {str(repository.id).casefold()}
    if producer.upstream is not None:
        allowed.add(str(producer.upstream).casefold())
    findings = []
    for path, value in _manifest_links(root):
        match = _GITHUB.search(value)
        if match is None:
            continue
        named = RepoId(match.group(1), match.group(2))
        if str(named).casefold() not in allowed:
            findings.append(
                violation(
                    repository,
                    RULE_ID,
                    path,
                    f"repository link names {named}, not the maintained {repository.id}"
                    + ("" if producer.upstream is None else f" or the declared upstream {producer.upstream}"),
                )
            )
    return findings


def _consumer_findings(root: Path, repository: Repository, policy: OwnedTools, producer: Producer) -> list[Finding]:
    findings = []
    if producer.installer is not None:
        source = _read(root, producer.installer)
        if source is None:
            findings.append(violation(repository, RULE_ID, producer.installer, "declared installer does not exist"))
        else:
            try:
                installed = installer_repositories(source, policy.owners)
            except SyntaxError as error:
                return [operational(repository, RULE_ID, producer.installer, f"cannot parse installer: {error}")]
            findings.extend(
                violation(
                    repository,
                    RULE_ID,
                    producer.installer,
                    f"installs {repo}, which has no owned-tools producer; "
                    "a renamed or uncatalogued repository must use its maintained name",
                )
                for repo in installed
                if policy.producer(repo) is None
            )
    declared = {command.name for command in producer.commands}
    findings.extend(
        violation(repository, RULE_ID, directory, "declared command directory does not exist")
        for directory in producer.bin
        if not (root / directory).is_dir()
    )
    findings.extend(
        violation(
            repository,
            RULE_ID,
            _POLICY_PATH,
            f"tracked executable {name} is not declared under producers.{repository.id}.commands",
        )
        for name in tracked_commands(root, producer.bin)
        if name not in declared
    )
    return findings


def _owned_tool_findings(root: Path, repository: Repository) -> list[Finding]:
    try:
        policy = cached(("owned-tools-policy",), load_owned_tools)
    except ValueError as error:
        return [operational(repository, RULE_ID, _POLICY_PATH, str(error))]
    producer = policy.producer(repository.id)
    if producer is None:
        if policy.exemption(repository.id) is not None:
            if set(repository.tags) & _EXEMPT_TAGS:
                return [
                    violation(
                        repository,
                        RULE_ID,
                        _POLICY_PATH,
                        "tool and build repositories cannot be not_applicable; declare their commands",
                    )
                ]
            return []
        if not policy.owned(repository.id) or not needs_coverage(repository):
            return []
        return [
            violation(
                repository,
                RULE_ID,
                _POLICY_PATH,
                "missing owned-tool coverage: declare its commands or a not_applicable reason",
            )
        ]
    findings: list[Finding] = []
    for command in producer.commands:
        if isinstance(command.support, HelpIntegration):
            findings.extend(_help_findings(root, repository, policy, command.name, command.support))
        elif command.status == "gap":
            findings.append(
                violation(
                    repository,
                    RULE_ID,
                    _POLICY_PATH,
                    f"{command.name}: help integration gap: {command.support}",
                    severity="warning",
                )
            )
    findings.extend(_identity_findings(root, repository, producer))
    findings.extend(_consumer_findings(root, repository, policy, producer))
    return sorted(findings, key=lambda finding: (finding.file or "", finding.message))


def owned_tool_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            RULE_ID,
            "Require owned agent-facing commands to name their maintained repository in help",
            TagPredicate(),
            _owned_tool_findings,
            None,
            None,
            (),
        ),
    )
