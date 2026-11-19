from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from repomod import paths
from repomod.catalog import load_catalog
from repomod.dependencies.adapters.cargo import _excluded
from repomod.rules.ci_workflow import _step_problem, _trigger_problem
from repomod.rules.consistency import _declared_make_targets
from repomod.rules.languages import _rust_manifests
from repomod.rules.workflows import read_workflow_sources
from repomod.types import Finding, Repository, Rule, TagPredicate, operational, violation

_POLICY = 'fleet/policy/retention.toml'
_SETTINGS = {
    'rust.unsafe_code=forbid',
    'clippy.needless_pass_by_value=deny',
    'clippy.redundant_clone=deny',
    'ty.missing-type-argument=error',
    'ty.unsound-return-statement=error',
    'ty.unused-ignore-comment=error',
    'ruff.ANN401=selected',
}


def _policy() -> dict[str, Any]:
    path = paths.POLICY / 'retention.toml'
    if path.is_symlink():
        raise ValueError('retention policy is a symlink')
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8'))
        catalog = load_catalog(paths.CATALOG)
    except (OSError, ValueError) as error:
        raise ValueError(f'cannot load retention policy or catalog: {error}') from error
    if set(data) != {'version', 'mutation-lane', 'coverage-target', 'strict-profile'} or data['version'] != 1:
        raise ValueError('unknown or missing retention guarantee, or invalid version')
    known = {str(repo.id) for repo in (*catalog.repositories, *catalog.ignored)}
    known.update(str(repo) for repo in catalog.pending)
    for guarantee in ('mutation-lane', 'coverage-target'):
        section = data[guarantee]
        if (not isinstance(section, dict) or set(section) != {'repositories'}
                or not isinstance(section['repositories'], list)):
            raise ValueError(f'invalid {guarantee} policy')
        if any(not isinstance(repo, str) or repo not in known for repo in section['repositories']):
            raise ValueError(f'{guarantee} names a repository outside the catalog')
    strict = data['strict-profile']
    if not isinstance(strict, dict):
        raise ValueError('invalid strict-profile policy')
    for repo, entry in strict.items():
        if repo not in known:
            raise ValueError(f'strict-profile names a repository outside the catalog: {repo}')
        if not isinstance(entry, dict) or set(entry) != {'settings'} or not isinstance(entry['settings'], list):
            raise ValueError(f'invalid strict-profile settings for {repo}')
        if any(not isinstance(setting, str) or setting not in _SETTINGS for setting in entry['settings']):
            raise ValueError(f'unknown strict-profile setting for {repo}')
    return data


def _targets(root: Path, repository: Repository, rule: str, target: str) -> list[Finding]:
    path = root / 'Makefile'
    try:
        declared = _declared_make_targets(path) if path.is_file() else set()
        source = path.read_text(encoding='utf-8') if path.is_file() else ''
    except (OSError, UnicodeError) as error:
        return [operational(repository, rule, 'Makefile', str(error))]
    if declared is None:
        return [operational(repository, rule, 'Makefile', f'cannot determine {target} target')]
    rules = (line.partition(':')[0].split() for line in source.splitlines()
             if line and not line[0].isspace() and ':' in line and not line.startswith('#'))
    has_rule = any(target in names and '.PHONY' not in names for names in rules)
    return [] if target in declared and has_rule else [
        violation(repository, rule, 'Makefile', f'missing {target} target')
    ]


def _mutation(root: Path, repository: Repository, rule: str = 'mutation-lane', pin: str | None = None) -> list[Finding]:
    findings = _targets(root, repository, rule, 'mutants-diff')
    python_job = pin is None and 'python' in repository.tags and 'rust' not in repository.tags
    if python_job:
        findings.extend(_locked_mutmut(root, repository, rule))
    sources, problems = read_workflow_sources(root)
    findings.extend(operational(repository, rule, path, message) for path, message in problems)
    for path, source in sources:
        try:
            doc = YAML(typ='safe').load(source)
        except YAMLError as error:
            findings.append(operational(repository, rule, path, f'cannot parse workflow YAML: {error}'))
            continue
        if not isinstance(doc, dict):
            continue
        pr, trigger_problem = _trigger_problem(doc, root)
        if not pr or trigger_problem is not None:
            continue
        jobs = doc.get('jobs', {})
        if not isinstance(jobs, dict):
            continue
        for job in jobs.values():
            if not isinstance(job, dict) or not isinstance(job.get('steps'), list):
                continue
            if job.get('if') == "github.event_name == 'pull_request'":
                job = {key: value for key, value in job.items() if key != 'if'}
            steps = [step for step in job['steps'] if isinstance(step, dict)]
            for index, step in enumerate(steps):
                if _step_problem(doc, job, step, frozenset({'mutants-diff'})) is not None:
                    continue
                setup = [
                    item for item in steps[:index]
                    if 'if' not in item and item.get('continue-on-error', False) is False
                ]
                checkout = any(
                    isinstance(item.get('uses'), str)
                    and re.fullmatch(r'actions/checkout@[0-9a-f]{40}', item['uses'])
                    and isinstance(item.get('with'), dict) and item['with'].get('fetch-depth') == 0
                    for item in setup
                )
                tool_pattern = (
                    rf'cargo-mutants@{re.escape(pin)}' if pin is not None
                    else r'cargo-mutants@\d+\.\d+\.\d+'
                )
                if python_job:
                    tool = any(
                        isinstance(item.get('uses'), str)
                        and re.fullmatch(r'astral-sh/setup-uv@[0-9a-f]{40}', item['uses'])
                        and isinstance(item.get('with'), dict)
                        and re.fullmatch(r'\d+\.\d+\.\d+', str(item['with'].get('version', '')))
                        for item in setup
                    )
                else:
                    tool = any(
                        isinstance(item.get('uses'), str)
                        and re.fullmatch(r'taiki-e/install-action@[0-9a-f]{40}', item['uses'])
                        and isinstance(item.get('with'), dict)
                        and re.fullmatch(tool_pattern, str(item['with'].get('tool', '')))
                        for item in setup
                    )
                if checkout and tool:
                    return findings
    message = 'missing supported pull_request mutants-diff job with full checkout and pinned cargo-mutants'
    if python_job:
        message = 'missing supported pull_request mutants-diff job with full checkout and pinned setup-uv'
    elif pin is not None:
        message = ('missing supported pull_request mutants-diff job with full checkout '
                    f'and cargo-mutants pinned at {pin}')
    findings.append(violation(repository, rule, '.github/workflows', message))
    return findings


def _locked_mutmut(root: Path, repository: Repository, rule: str) -> list[Finding]:
    missing = 'missing exact mutmut development pin in pyproject.toml and uv.lock'
    data = {}
    for relative in ('pyproject.toml', 'uv.lock'):
        try:
            data[relative] = tomllib.loads((root / relative).read_text(encoding='utf-8'))
        except FileNotFoundError:
            return [violation(repository, rule, relative, missing)]
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            return [operational(repository, rule, relative, str(error))]
    groups = data['pyproject.toml'].get('dependency-groups')
    dev = groups.get('dev') if isinstance(groups, dict) else None
    packages = data['uv.lock'].get('package')
    if isinstance(dev, list) and isinstance(packages, list):
        versions = [
            str(package.get('version')) for package in packages
            if isinstance(package, dict) and package.get('name') == 'mutmut'
        ]
        if len(versions) == 1 and re.fullmatch(r'\d+\.\d+\.\d+', versions[0]) and f'mutmut=={versions[0]}' in dev:
            return []
    return [violation(repository, rule, 'uv.lock', missing)]


def _rust_lint_matches(lints: object, group: str, name: str, level: str) -> bool:
    lint_group = lints.get(group) if isinstance(lints, dict) else None
    value = lint_group.get(name) if isinstance(lint_group, dict) else None
    return (value.get('level') if isinstance(value, dict) else value) == level


def _workspace_strict(
    root: Path, repository: Repository, rule: str, workspace: dict[str, object], setting: str
) -> list[Finding]:
    name, level = setting.split('=')
    group, lint_name = name.split('.')
    manifests, problems = _rust_manifests(root)
    exclusions = workspace.get('exclude')
    excludes = exclusions if isinstance(exclusions, list) else []
    findings = [
        operational(repository, rule, relative, problem)
        for relative, problem in problems
        if not _excluded(Path(relative).parent.as_posix(), '.', excludes)
    ]
    members = [
        (path, document)
        for path, document, _, workspace_root in manifests
        if workspace_root == root and isinstance(document.get('package'), dict)
        and (path.parent == root or not _excluded(path.parent.relative_to(root).as_posix(), '.', excludes))
    ]
    if not members and not findings:
        return [violation(repository, rule, 'Cargo.toml', f'no workspace packages found for {setting}')]
    for path, document in members:
        lints = document.get('lints')
        if isinstance(lints, dict) and lints.get('workspace') is True:
            lints = workspace.get('lints') if len(lints) == 1 else None
        if not _rust_lint_matches(lints, group, lint_name, level):
            findings.append(violation(repository, rule, path.relative_to(root).as_posix(),
                                      f'missing strict setting {setting}'))
    return findings


def _strict(root: Path, repository: Repository, settings: list[str], rule: str = 'strict-profile') -> list[Finding]:
    findings = []
    for setting in settings:
        name, level = setting.split('=')
        group, lint_name = name.split('.')
        relative = 'Cargo.toml' if group in {'rust', 'clippy'} else 'pyproject.toml'
        try:
            data = tomllib.loads((root / relative).read_text(encoding='utf-8'))
        except FileNotFoundError:
            data = {}
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            findings.append(operational(repository, rule, relative, str(error)))
            continue
        if group in {'rust', 'clippy'}:
            workspace = data.get('workspace')
            if isinstance(workspace, dict):
                findings.extend(_workspace_strict(root, repository, rule, workspace, setting))
                continue
            valid = _rust_lint_matches(data.get('lints'), group, lint_name, level)
        elif group == 'ty':
            value = data.get('tool', {}).get('ty', {}).get('rules', {}).get(lint_name)
            valid = value == level
        else:
            lint = data.get('tool', {}).get('ruff', {}).get('lint', {})
            valid = 'ANN401' in lint.get('select', []) and 'ANN401' not in lint.get('ignore', [])
        if not valid:
            findings.append(violation(repository, rule, relative, f'missing strict setting {setting}'))
    return findings


def _check(root: Path, repository: Repository, rule: str) -> list[Finding]:
    try:
        policy = _policy()
    except ValueError as error:
        return [operational(repository, rule, _POLICY, str(error))]
    name = str(repository.id)
    if rule in {'strict-profile', 'strict-typing-profile'}:
        entry = policy['strict-profile'].get(name)
        return [] if entry is None else _strict(root, repository, entry['settings'], rule)
    if name not in policy[rule]['repositories']:
        return []
    if rule == 'coverage-target':
        return _targets(root, repository, rule, 'coverage')
    return _mutation(root, repository)


def retention_rules() -> tuple[Rule, ...]:
    def check(rule: str):
        def run(root: Path, repository: Repository) -> list[Finding]:
            return _check(root, repository, rule)
        return run
    return tuple(
        Rule(rule, f'Retain {rule}', TagPredicate(), check(rule), None, None, ())
        for rule in ('mutation-lane', 'coverage-target', 'strict-profile')
    )
