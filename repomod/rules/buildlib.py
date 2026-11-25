from __future__ import annotations

import datetime
import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from repomod import buildlib_pins, owned_python, paths
from repomod.catalog import load_catalog
from repomod.io import read_json_object, safe_relative
from repomod.rules.workflows import workflow_files
from repomod.types import Finding, RepoId, Repository, Rule, TagPredicate, operational, violation

_RULE = 'buildlib-usage'
_POLICY = 'fleet/policy/buildlib.toml'
_ACTIONS_POLICY = 'fleet/policy/actions.toml'
_TOOLS_LOCK = '.github/tools.lock.json'
_BOOTSTRAP = ('buildlib-run', 'python.lock')
_SETUP_USES = re.compile(
    r'^[ \t]*(?:-[ \t]+)?uses:[ \t]+laputa-systems/buildlib/setup@(?P<tail>[^\r\n]*)'
)
_SHA256 = re.compile(r'[0-9a-f]{64}')
_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
_PACKAGE = re.compile(r'laputa-buildlib(\[[^\]]*\])?(?:[=<>!~@;\s]|$)', re.IGNORECASE)
_SOURCE_NAMES = frozenset({'laputa-buildlib', 'buildlib-wheel'})
_WHEEL_PREFIX = 'laputa_buildlib-'


@dataclass(frozen=True, slots=True)
class Policy:
    wheel_version: str
    wheel_filename: str
    wheel_sha256: str
    bootstrap_sha256: dict[str, frozenset[str]]
    enrolled: dict[str, object]
    assess: dict[str, object]
    exempt: dict[str, object]


def _policy_path() -> Path:
    return paths.POLICY / 'buildlib.toml'


def _digest_set(value: object, label: str) -> frozenset[str]:
    if isinstance(value, str):
        items: tuple[str, ...] = (value,)
    elif isinstance(value, list) and value and all(isinstance(item, str) for item in value):
        items = tuple(item for item in value if isinstance(item, str))
    else:
        raise ValueError(f'{label} must be a sha256 string or a non-empty list of sha256 strings')
    if any(_SHA256.fullmatch(item) is None for item in items):
        raise ValueError(f'{label} must contain 64 lowercase hex digits')
    return frozenset(items)


def _declared_digests(value: object, label: str) -> dict[str, frozenset[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f'{label} must be a table of bootstrap shim sha256 values')
    declared: dict[str, frozenset[str]] = {}
    for raw_name, raw in value.items():
        if not isinstance(raw_name, str):
            raise ValueError(f'{label} keys must be bootstrap shim names')
        if raw_name not in _BOOTSTRAP:
            raise ValueError(f'{label} names an unknown bootstrap shim {raw_name!r}')
        declared[raw_name] = _digest_set(raw, f'{label}.{raw_name}')
    return declared


def _table(data: dict[str, Any], key: str) -> dict[str, object]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f'[{key}] must be a table')
    return {str(name): entry for name, entry in value.items()}


def _load_policy() -> Policy:
    path = _policy_path()
    if path.is_symlink():
        raise ValueError('buildlib policy is a symlink')
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f'cannot load buildlib policy: {error}') from error
    if set(data) - {'version', 'artifact', 'enrolled', 'assess', 'exempt'} or data.get('version') != 1:
        raise ValueError('unknown or missing buildlib policy, or invalid version')
    artifact = data.get('artifact')
    if not isinstance(artifact, dict):
        raise ValueError('buildlib policy needs an [artifact] table')
    unknown = {
        key for key in artifact
        if isinstance(key, str) and key not in {
            'wheel_version', 'wheel_filename', 'wheel_sha256', 'wheel_size', 'bootstrap_sha256',
            'bootstrap_revision',
        }
    }
    if unknown:
        raise ValueError(f'unknown artifact keys: {", ".join(sorted(unknown))}')
    version = artifact.get('wheel_version')
    filename = artifact.get('wheel_filename')
    digest = artifact.get('wheel_sha256')
    if not isinstance(version, str) or re.fullmatch(r'\d+\.\d+\.\d+', version) is None:
        raise ValueError('artifact wheel_version must be an exact version')
    if not isinstance(filename, str) or not filename.endswith('.whl'):
        raise ValueError('artifact wheel_filename must name a wheel')
    if not filename.startswith(f'laputa_buildlib-{version}-'):
        raise ValueError('artifact wheel_filename must agree with wheel_version')
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise ValueError('artifact wheel_sha256 must be 64 lowercase hex digits')
    size = artifact.get('wheel_size')
    if size is not None and (not isinstance(size, int) or isinstance(size, bool) or size <= 0):
        raise ValueError('artifact wheel_size must be a positive byte count when present')
    revision = artifact.get('bootstrap_revision')
    if revision is not None and (not isinstance(revision, str) or re.fullmatch(r'[0-9a-f]{40}', revision) is None):
        raise ValueError('artifact bootstrap_revision must be a 40-hex revision when present')
    assess = _table(data, 'assess')
    for name, entry in assess.items():
        if not isinstance(entry, dict) or entry:
            raise ValueError(f'assess {name} must be an empty table')
    return Policy(
        version,
        filename,
        digest,
        _declared_digests(artifact.get('bootstrap_sha256'), 'artifact.bootstrap_sha256'),
        _table(data, 'enrolled'),
        assess,
        _table(data, 'exempt'),
    )


def _known_repositories() -> frozenset[str]:
    return frozenset(str(repository.id) for repository in load_catalog(paths.CATALOG).repositories)


def _requirement_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        stripped
        for stripped in (item.strip() for item in value if isinstance(item, str))
        if stripped
    ]


def _raw_requirement_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _dependency_requirement_values(data: dict[str, Any]) -> list[str]:
    requirements: list[str] = []
    project = data.get('project')
    if isinstance(project, dict):
        requirements.extend(_raw_requirement_strings(project.get('dependencies')))
        optional = project.get('optional-dependencies')
        if isinstance(optional, dict):
            for value in optional.values():
                requirements.extend(_raw_requirement_strings(value))
    groups = data.get('dependency-groups')
    if isinstance(groups, dict):
        for value in groups.values():
            requirements.extend(_raw_requirement_strings(value))
    return requirements


def _dependency_requirements(data: dict[str, Any]) -> list[str]:
    requirements: list[str] = []
    project = data.get('project')
    if isinstance(project, dict):
        requirements.extend(_requirement_strings(project.get('dependencies')))
        optional = project.get('optional-dependencies')
        if isinstance(optional, dict):
            for value in optional.values():
                requirements.extend(_requirement_strings(value))
    groups = data.get('dependency-groups')
    if isinstance(groups, dict):
        for value in groups.values():
            requirements.extend(_requirement_strings(value))
    return requirements


def _pin(root: Path, repository: Repository, policy: Policy) -> list[Finding]:
    path = root / 'pyproject.toml'
    expected = f'laputa-buildlib=={policy.wheel_version}'
    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return [violation(repository, _RULE, 'pyproject.toml',
                          f'missing pyproject.toml; enrolled consumers must pin {expected}')]
    except (OSError, UnicodeError) as error:
        return [operational(repository, _RULE, 'pyproject.toml', str(error))]
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return [operational(repository, _RULE, 'pyproject.toml', str(error))]
    entries = [entry for entry in _dependency_requirements(data) if _PACKAGE.match(entry)]
    if not entries:
        return [violation(repository, _RULE, 'pyproject.toml',
                          f'missing laputa-buildlib dependency; enrolled consumers must pin {expected}')]
    exact = re.compile(
        rf'laputa-buildlib(?:\[[^\]]*\])?\s*==\s*{re.escape(policy.wheel_version)}\Z',
        re.IGNORECASE,
    )
    if all(exact.fullmatch(entry.split(';', 1)[0].strip()) for entry in entries):
        return []
    repaired = _repair_pyproject(text, policy)
    return [violation(repository, _RULE, 'pyproject.toml',
                      f'laputa-buildlib must be pinned exactly as {expected}; found {", ".join(entries)}',
                      fixable=repaired is not None and repaired != text)]


def _wheel_digests(document: object, filename: str) -> tuple[bool, list[str | None]]:
    matched = False
    digests: list[str | None] = []

    def walk(node: object) -> None:
        nonlocal matched
        if isinstance(node, dict):
            url = node.get('url')
            if isinstance(url, str) and PurePosixPath(url.split('?', 1)[0]).name == filename:
                matched = True
                hashed = node.get('hash')
                digests.append(hashed.removeprefix('sha256:') if isinstance(hashed, str) else None)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(document)
    return matched, digests


def _source_urls(entry: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    url = entry.get('url')
    if isinstance(url, str):
        urls.append(url)
    many = entry.get('urls')
    if isinstance(many, list):
        urls.extend(item for item in many if isinstance(item, str))
    return urls


def _source_basename(value: str) -> str:
    return PurePosixPath(value.split('?', 1)[0]).name


def _is_buildlib_source(entry: dict[str, Any]) -> bool:
    name = entry.get('name')
    if isinstance(name, str) and name in _SOURCE_NAMES:
        return True
    filename = entry.get('filename')
    if isinstance(filename, str) and _source_basename(filename).startswith(_WHEEL_PREFIX):
        return True
    return any(_source_basename(url).startswith(_WHEEL_PREFIX) for url in _source_urls(entry))


def _source_findings(
    document: dict[str, Any], repository: Repository, policy: Policy, *, fixable: bool = False
) -> list[Finding]:
    inputs = document.get('inputs')
    if not isinstance(inputs, list):
        return []
    findings: list[Finding] = []
    for entry in inputs:
        if not isinstance(entry, dict) or not _is_buildlib_source(entry):
            continue
        filename = entry.get('filename')
        declared = _source_basename(filename) if isinstance(filename, str) else None
        basenames = [_source_basename(url) for url in _source_urls(entry)]
        if declared is not None and declared != policy.wheel_filename:
            findings.append(violation(
                repository, _RULE, 'sources.lock.json',
                f'sources.lock.json records wheel filename {declared}; '
                f'policy approves {policy.wheel_filename}',
                fixable=fixable,
            ))
        findings.extend(
            violation(
                repository, _RULE, 'sources.lock.json',
                f'sources.lock.json records wheel URL basename {basename}; '
                f'policy approves {policy.wheel_filename}',
                fixable=fixable,
            )
            for basename in basenames
            if basename != policy.wheel_filename
        )
        if declared is None and not basenames:
            findings.append(violation(
                repository, _RULE, 'sources.lock.json',
                'sources.lock.json buildlib entry does not record the approved wheel filename or URL',
                fixable=fixable,
            ))
        version = entry.get('version')
        if version is not None and version != policy.wheel_version:
            findings.append(violation(
                repository, _RULE, 'sources.lock.json',
                f'sources.lock.json records wheel version {version}; '
                f'policy approves {policy.wheel_version}',
                fixable=fixable,
            ))
        digest = entry.get('sha256')
        if not isinstance(digest, str) or digest != policy.wheel_sha256:
            findings.append(violation(
                repository, _RULE, 'sources.lock.json',
                f'sources.lock.json records wheel sha256 '
                f'{digest if isinstance(digest, str) else "missing"}; '
                f'policy approves {policy.wheel_sha256}',
                fixable=fixable,
            ))
    return findings


def _uv_lock(root: Path, repository: Repository, policy: Policy) -> list[Finding]:
    path = root / 'uv.lock'
    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return [violation(repository, _RULE, 'uv.lock',
                          f'missing uv.lock; cannot verify the approved {policy.wheel_filename} sha256')]
    except (OSError, UnicodeError) as error:
        return [operational(repository, _RULE, 'uv.lock', str(error))]
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return [operational(repository, _RULE, 'uv.lock', str(error))]
    repaired = _repair_uv_lock(text, policy)
    fixable = repaired is not None and repaired != text
    findings: list[Finding] = []
    packages = data.get('package')
    if isinstance(packages, list):
        for entry in packages:
            if isinstance(entry, dict) and entry.get('name') == 'laputa-buildlib':
                version = entry.get('version')
                if version != policy.wheel_version:
                    findings.append(violation(
                        repository, _RULE, 'uv.lock',
                        f'uv.lock records laputa-buildlib version {version}; '
                        f'policy approves {policy.wheel_version}',
                        fixable=fixable,
                    ))
    matched, digests = _wheel_digests(data, policy.wheel_filename)
    if not matched:
        findings.append(violation(
            repository, _RULE, 'uv.lock',
            f'uv.lock does not record the approved {policy.wheel_filename} wheel',
            fixable=fixable,
        ))
        return findings
    findings.extend(
        violation(repository, _RULE, 'uv.lock',
                  f'uv.lock records wheel sha256 {digest or "missing"}; policy approves {policy.wheel_sha256}',
                  fixable=fixable)
        for digest in digests
        if digest != policy.wheel_sha256
    )
    return findings


def _sources_lock(root: Path, repository: Repository, policy: Policy) -> list[Finding]:
    path = root / 'sources.lock.json'
    if path.is_symlink():
        return [operational(repository, _RULE, 'sources.lock.json',
                            'sources.lock.json is a symlink and was not inspected')]
    if not path.exists():
        return []
    document, error = read_json_object(path)
    if document is None:
        return [violation(repository, _RULE, 'sources.lock.json',
                          f'sources.lock.json is not a valid JSON object: {error}')]
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        text = None
    repaired = _repair_sources_lock(text, repository, policy) if text is not None else None
    return _source_findings(document, repository, policy,
                            fixable=repaired is not None and repaired != text)


def _bootstrap(
    root: Path,
    repository: Repository,
    required: bool,
    approved: dict[str, frozenset[str]],
    local: dict[str, frozenset[str]],
) -> list[Finding]:
    findings: list[Finding] = []
    for name in _BOOTSTRAP:
        relative = f'bootstrap/{name}'
        path = root / 'bootstrap' / name
        if safe_relative(root, path) is None:
            findings.append(operational(repository, _RULE, relative, f'{relative} is a symlink and was not inspected'))
            continue
        if not path.exists():
            if required:
                vendored = buildlib_pins.approved_shim(name, approved.get(name, frozenset()))
                findings.append(violation(
                    repository, _RULE, relative, f'missing bootstrap shim {relative}',
                    fixable=vendored is not None,
                ))
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            findings.append(operational(repository, _RULE, relative, str(error)))
            continue
        allowed = approved.get(name, frozenset()) | local.get(name, frozenset())
        if digest not in allowed:
            vendored = buildlib_pins.approved_shim(name, approved.get(name, frozenset()))
            findings.append(violation(
                repository, _RULE, relative,
                f'{relative} sha256 {digest} is not an approved identity or declared local difference',
                fixable=vendored is not None,
            ))
    return findings


def _entrypoints(root: Path, repository: Repository, entrypoints: list[str]) -> list[Finding]:
    findings = []
    for entry in entrypoints:
        relpath = Path(entry)
        if relpath.is_absolute() or '..' in relpath.parts:
            findings.append(violation(repository, _RULE, _POLICY,
                                      f'enrolled entrypoint {entry!r} must be repository-relative'))
            continue
        relative = safe_relative(root, root / relpath)
        if relative is None:
            findings.append(violation(repository, _RULE, entry,
                                      f'declared entrypoint {entry} must not traverse a symlink'))
        elif not (root / relative).exists():
            findings.append(violation(repository, _RULE, entry, f'declared entrypoint {entry} does not exist'))
        elif not (root / relative).is_file():
            findings.append(violation(repository, _RULE, entry,
                                      f'declared entrypoint {entry} is not a regular file'))
    return findings


def _enrolled(root: Path, repository: Repository, entry: object, policy: Policy) -> list[Finding]:
    name = str(repository.id)
    if not isinstance(entry, dict):
        return [violation(repository, _RULE, _POLICY, f'enrolled {name} must be a table')]
    findings: list[Finding] = []
    unknown = set(entry) - {'entrypoints', 'bootstrap', 'bootstrap_sha256'}
    extra = ', '.join(sorted(str(key) for key in unknown))
    if extra:
        findings.append(violation(repository, _RULE, _POLICY,
                                  f'enrolled {name} has unknown keys: {extra}'))
    raw_entrypoints = entry.get('entrypoints')
    entrypoints: list[str] = []
    if (not isinstance(raw_entrypoints, list) or not raw_entrypoints
            or any(not isinstance(item, str) or not item.strip() for item in raw_entrypoints)):
        findings.append(violation(
            repository, _RULE, _POLICY,
            f'enrolled {name} needs a non-empty entrypoints list of repository-relative paths',
        ))
    else:
        entrypoints = [item.strip() for item in raw_entrypoints if isinstance(item, str)]
    bootstrap = entry.get('bootstrap')
    if not isinstance(bootstrap, bool):
        findings.append(violation(repository, _RULE, _POLICY,
                                  f'enrolled {name} must declare bootstrap = true or false'))
    try:
        local = _declared_digests(entry.get('bootstrap_sha256'), f'enrolled {name}.bootstrap_sha256')
    except ValueError as error:
        findings.append(violation(repository, _RULE, _POLICY, str(error)))
        local = {}
    if bootstrap is not True or (root / 'pyproject.toml').exists():
        findings.extend(_pin(root, repository, policy))
        findings.extend(_uv_lock(root, repository, policy))
    findings.extend(_sources_lock(root, repository, policy))
    findings.extend(_bootstrap(root, repository, bootstrap is True, policy.bootstrap_sha256, local))
    findings.extend(_entrypoints(root, repository, entrypoints))
    return findings


def _exempt(repository: Repository, entry: object) -> list[Finding]:
    name = str(repository.id)
    if not isinstance(entry, dict):
        return [violation(repository, _RULE, _POLICY,
                          f'exempt {name} must be a table with reason and reassess')]
    findings: list[Finding] = []
    unknown = set(entry) - {'reason', 'reassess'}
    extra = ', '.join(sorted(str(key) for key in unknown))
    if extra:
        findings.append(violation(repository, _RULE, _POLICY, f'exempt {name} has unknown keys: {extra}'))
    reason = entry.get('reason')
    if not isinstance(reason, str) or not reason.strip():
        findings.append(violation(repository, _RULE, _POLICY, f'exempt {name} needs a non-empty reason'))
    reassess = entry.get('reassess')
    if not isinstance(reassess, str) or not reassess.strip():
        findings.append(violation(repository, _RULE, _POLICY,
                                  f'exempt {name} needs a non-empty reassessment condition'))
        return findings
    condition = reassess.strip()
    if _DATE.fullmatch(condition) is not None:
        try:
            reassess_date = datetime.date.fromisoformat(condition)
        except ValueError:
            findings.append(violation(repository, _RULE, _POLICY,
                                      f'exempt {name} reassess {condition!r} is not a valid date'))
        else:
            if reassess_date < datetime.date.today():
                findings.append(violation(repository, _RULE, _POLICY,
                                          f'exempt {name} expired on {condition}; '
                                          'reassess it against current conditions'))
    return findings


def _unknown_repositories(anchor: Repository, policy: Policy, known: frozenset[str]) -> list[Finding]:
    findings = []
    names = dict.fromkeys((*policy.enrolled, *policy.assess, *policy.exempt))
    for name in names:
        if name in known:
            continue
        try:
            target = Repository(RepoId.parse(name), ())
        except ValueError:
            target = anchor
        findings.append(violation(target, _RULE, _POLICY,
                                  f'buildlib policy classifies {name}, which is not an active catalog repository'))
    return findings


def _approved_setup_pin() -> str:
    pin = owned_python.buildlib_setup_pin()
    return f'{pin.sha} # {pin.version}'


def _setup_steps(
    root: Path, repository: Repository
) -> list[tuple[str, int, str]]:
    if not (root / _TOOLS_LOCK).is_file():
        return []
    files, _problems = workflow_files(root, repository)
    steps: list[tuple[str, int, str]] = []
    for path in files:
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        relative = path.relative_to(root).as_posix()
        for number, line in enumerate(text.splitlines(), 1):
            if _SETUP_USES.match(line):
                steps.append((relative, number, line))
    return steps


def _setup_pin_findings(
    repository: Repository, steps: list[tuple[str, int, str]]
) -> list[Finding]:
    try:
        approved = _approved_setup_pin()
    except ValueError as error:
        return [operational(repository, _RULE, _ACTIONS_POLICY, str(error))]
    findings: list[Finding] = []
    for relative, number, line in steps:
        match = _SETUP_USES.match(line)
        tail = match.group('tail').strip() if match is not None else ''
        if tail == approved:
            continue
        found = tail.split('#', 1)[0].strip() or tail
        findings.append(violation(
            repository, _RULE, relative,
            'buildlib setup action must use the approved pin '
            f'laputa-systems/buildlib/setup@{approved}; found {found}',
            line=number,
            fixable=True,
        ))
    return findings


def _rewrite_setup_line(line: str, approved: str) -> str | None:
    match = _SETUP_USES.match(line)
    if match is None:
        return None
    body = line.rstrip('\r\n')
    ending = line[len(body):]
    return f'{line[:match.start("tail")]}{approved}{ending}'


def _tools_fix(root: Path, repository: Repository) -> dict[str, str]:
    steps = _setup_steps(root, repository)
    if not steps:
        return {}
    try:
        approved = _approved_setup_pin()
    except ValueError:
        return {}
    files, _problems = workflow_files(root, repository)
    wanted = {relative for relative, _number, _line in steps}
    plan: dict[str, str] = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        if relative not in wanted:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        output: list[str] = []
        changed = False
        for line in text.splitlines(keepends=True):
            match = _SETUP_USES.match(line.rstrip('\r\n'))
            if match is not None and match.group('tail').strip() == approved:
                output.append(line)
                continue
            rewritten = _rewrite_setup_line(line, approved)
            if rewritten is not None and rewritten != line:
                changed = True
                output.append(rewritten)
            else:
                output.append(line)
        if changed:
            plan[relative] = ''.join(output)
    return plan


def _classifications(policy: Policy, name: str) -> list[str]:
    values = []
    if name in policy.enrolled:
        values.append('enrolled')
    if name in policy.assess:
        values.append('assess')
    if name in policy.exempt:
        values.append('exempt')
    return values


def _check(root: Path, repository: Repository) -> list[Finding]:
    try:
        policy = _load_policy()
        known = _known_repositories()
    except ValueError as error:
        return [operational(repository, _RULE, _POLICY, str(error))]
    name = str(repository.id)
    findings: list[Finding] = []
    if known and name == min(known, key=str.casefold):
        findings.extend(_unknown_repositories(repository, policy, known))
    classifications = _classifications(policy, name)
    steps = _setup_steps(root, repository)
    adopted = bool(steps)
    if 'exempt' in classifications and ('enrolled' in classifications or adopted):
        basis = (
            'enrolled'
            if 'enrolled' in classifications
            else 'adopted through buildlib owned tools'
        )
        findings.append(violation(
            repository, _RULE, _POLICY,
            f'stale exempt.{name} entry: the repository is {basis}; '
            f'delete [exempt."{name}"] from {_POLICY}',
        ))
        classifications = [kind for kind in classifications if kind != 'exempt']
    if len(classifications) > 1:
        findings.append(violation(repository, _RULE, _POLICY,
                                  f'{name} is classified more than once in the buildlib policy: '
                                  + ', '.join(classifications)))
        return findings
    if 'enrolled' in classifications:
        findings.extend(_enrolled(root, repository, policy.enrolled[name], policy))
    elif adopted:
        findings.extend(_setup_pin_findings(repository, steps))
    elif 'exempt' in classifications:
        findings.extend(_exempt(repository, policy.exempt[name]))
    elif 'assess' in classifications:
        findings.append(violation(
            repository, _RULE, _POLICY,
            'buildlib assessment pending: repository is eligible but not yet enrolled; no blocking check',
            severity='info',
        ))
    else:
        findings.append(violation(
            repository, _RULE, _POLICY,
            'unclassified buildlib disposition; add this repository to fleet/policy/buildlib.toml '
            'as enrolled, assess, or exempt',
            severity='info',
        ))
    return findings


_REQUIREMENT_NAME = re.compile(r'laputa-buildlib(?:\[[^\]]*\])?', re.IGNORECASE)
_UV_NAME_LINE = re.compile(r'^name = "laputa-buildlib"\s*$')
_UV_VERSION_LINE = re.compile(r'^version = "[^"]*"\s*$')
_UV_UHEAD = re.compile(r'^\[\[')
_UV_WHEEL_FILE = re.compile(r'laputa_buildlib-[^\s"\']*\.whl')
_UV_HASH = re.compile(r'sha256:[0-9a-f]{64}')
_UV_SPECIFIER = re.compile(r'(specifier = ")[^"]*(")')


def _rewrite_requirement(entry: str, version: str) -> str | None:
    head, sep, marker = entry.partition(';')
    stripped = head.strip()
    match = _REQUIREMENT_NAME.match(stripped)
    if match is None:
        return None
    rebuilt = f'{match.group(0)}=={version}'
    if sep:
        rebuilt += f';{marker}'
    lead = entry[: len(entry) - len(entry.lstrip())]
    trail = entry[len(entry.rstrip()):]
    return lead + rebuilt + trail


def _repair_pyproject(text: str, policy: Policy) -> str | None:
    try:
        data = tomllib.loads(text)
    except (UnicodeError, tomllib.TOMLDecodeError):
        return None
    replacements: dict[str, str] = {}
    for raw in _dependency_requirement_values(data):
        core = raw.strip()
        if not core or _PACKAGE.match(core) is None:
            continue
        updated = _rewrite_requirement(core, policy.wheel_version)
        if updated is None:
            return None
        lead = raw[: len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        new_raw = f'{lead}{updated}{trail}'
        if new_raw != raw:
            replacements[raw] = new_raw
    result = text
    for old, new in replacements.items():
        replaced = False
        for quote in ('"', "'"):
            literal_old = f'{quote}{old}{quote}'
            if literal_old in result:
                result = result.replace(literal_old, f'{quote}{new}{quote}')
                replaced = True
        if not replaced:
            return None
    if result == text:
        return text
    try:
        repaired = tomllib.loads(result)
    except (UnicodeError, tomllib.TOMLDecodeError):
        return None
    exact = re.compile(
        rf'laputa-buildlib(?:\[[^\]]*\])?\s*==\s*{re.escape(policy.wheel_version)}\Z',
        re.IGNORECASE,
    )
    for raw in _dependency_requirement_values(repaired):
        core = raw.strip()
        if not core or _PACKAGE.match(core) is None:
            continue
        head = core.split(';', 1)[0].strip()
        if not exact.fullmatch(head):
            return None
    return result


def _uv_lock_approved(data: dict[str, Any], policy: Policy) -> bool:
    packages = data.get('package')
    found = False
    if isinstance(packages, list):
        for entry in packages:
            if isinstance(entry, dict) and entry.get('name') == 'laputa-buildlib':
                found = True
                if entry.get('version') != policy.wheel_version:
                    return False
    if not found:
        return False
    matched, digests = _wheel_digests(data, policy.wheel_filename)
    return matched and all(digest == policy.wheel_sha256 for digest in digests)


def _repair_uv_lock(text: str, policy: Policy) -> str | None:
    try:
        tomllib.loads(text)
    except (UnicodeError, tomllib.TOMLDecodeError):
        return None
    output: list[str] = []
    in_package = False
    target = False
    version_done = False
    changed = False
    for line in text.splitlines(keepends=True):
        body = line.rstrip('\r\n')
        ending = line[len(body):]
        if _UV_UHEAD.match(body):
            in_package = True
            target = False
            version_done = False
        elif in_package and _UV_NAME_LINE.match(body):
            target = True
        if target:
            if not version_done and _UV_VERSION_LINE.match(body):
                newline = f'version = "{policy.wheel_version}"'
                changed = changed or newline != body
                output.append(newline + ending)
                version_done = True
                continue
            if 'laputa_buildlib-' in body and '.whl' in body:
                new_body = _UV_WHEEL_FILE.sub(policy.wheel_filename, body)
                new_body = _UV_HASH.sub(f'sha256:{policy.wheel_sha256}', new_body)
                changed = changed or new_body != body
                output.append(new_body + ending)
                continue
        if 'laputa-buildlib' in body and 'specifier = "' in body:
            new_body = _UV_SPECIFIER.sub(
                lambda match: f'{match.group(1)}=={policy.wheel_version}{match.group(2)}',
                body,
                count=1,
            )
            changed = changed or new_body != body
            output.append(new_body + ending)
            continue
        output.append(line)
    if not changed:
        return text
    result = ''.join(output)
    try:
        repaired = tomllib.loads(result)
    except (UnicodeError, tomllib.TOMLDecodeError):
        return None
    if not _uv_lock_approved(repaired, policy):
        return None
    return result


def _url_with_basename(url: str, filename: str) -> str:
    base, query_sep, query = url.partition('?')
    head, slash, _ = base.rpartition('/')
    if not slash:
        return filename
    return f'{head}/{filename}{query_sep}{query}'


def _repair_sources_lock(
    text: str | None, repository: Repository, policy: Policy
) -> str | None:
    if text is None:
        return None
    try:
        document = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(document, dict):
        return None
    inputs = document.get('inputs')
    if not isinstance(inputs, list):
        return text
    changed = False
    for entry in inputs:
        if not isinstance(entry, dict) or not _is_buildlib_source(entry):
            continue
        version = entry.get('version')
        if version is not None and version != policy.wheel_version:
            entry['version'] = policy.wheel_version
            changed = True
        filename = entry.get('filename')
        if isinstance(filename, str) and _source_basename(filename) != policy.wheel_filename:
            entry['filename'] = policy.wheel_filename
            changed = True
        url = entry.get('url')
        if isinstance(url, str) and _source_basename(url) != policy.wheel_filename:
            entry['url'] = _url_with_basename(url, policy.wheel_filename)
            changed = True
        urls = entry.get('urls')
        if isinstance(urls, list):
            for index, item in enumerate(urls):
                if isinstance(item, str) and _source_basename(item) != policy.wheel_filename:
                    urls[index] = _url_with_basename(item, policy.wheel_filename)
                    changed = True
        if entry.get('sha256') != policy.wheel_sha256:
            entry['sha256'] = policy.wheel_sha256
            changed = True
        size = entry.get('size')
        if 'size' in entry and size != buildlib_pins.wheel_size():
            entry['size'] = buildlib_pins.wheel_size()
            changed = True
        if (entry.get('filename') is None and entry.get('url') is None
                and not isinstance(entry.get('urls'), list)):
            entry['url'] = buildlib_pins.wheel_url()
            changed = True
    if not changed:
        return text
    result = json.dumps(document, indent=2) + '\n'
    try:
        repaired = json.loads(result)
    except json.JSONDecodeError:
        return None
    if _source_findings(repaired, repository, policy):
        return None
    return result


def _read_text_file(path: Path) -> str | None:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        return path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return None


def _fix(root: Path, repository: Repository) -> dict[str, str]:
    try:
        policy = _load_policy()
    except ValueError:
        return {}
    entry = policy.enrolled.get(str(repository.id))
    if not isinstance(entry, dict):
        return _tools_fix(root, repository)
    plan: dict[str, str] = {}
    bootstrap = entry.get('bootstrap')
    if bootstrap is not True or (root / 'pyproject.toml').exists():
        for relative, repair in (
            ('pyproject.toml', lambda text: _repair_pyproject(text, policy)),
            ('uv.lock', lambda text: _repair_uv_lock(text, policy)),
        ):
            text = _read_text_file(root / relative)
            if text is None:
                continue
            repaired = repair(text)
            if repaired is not None and repaired != text:
                plan[relative] = repaired
    text = _read_text_file(root / 'sources.lock.json')
    repaired = _repair_sources_lock(text, repository, policy)
    if text is not None and repaired is not None and repaired != text:
        plan['sources.lock.json'] = repaired
    try:
        local = _declared_digests(entry.get('bootstrap_sha256'), 'enrolled bootstrap_sha256')
    except ValueError:
        local = {}
    required = bootstrap is True
    for shim in _BOOTSTRAP:
        relative = f'bootstrap/{shim}'
        path = root / 'bootstrap' / shim
        if path.is_symlink():
            continue
        approved = policy.bootstrap_sha256.get(shim, frozenset())
        content = buildlib_pins.approved_shim(shim, approved)
        if content is None:
            continue
        if not path.exists():
            if required:
                plan[relative] = content
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
        allowed = approved | local.get(shim, frozenset())
        if digest not in allowed:
            plan[relative] = content
    return plan


def buildlib_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            'buildlib-usage',
            'Enforce the approved laputa-buildlib pin, bootstrap provenance, and declared entrypoints',
            TagPredicate(),
            _check,
            _fix,
            'build(buildlib): pin the approved laputa-buildlib wheel',
            (
                'pyproject.toml',
                'uv.lock',
                'sources.lock.json',
                'bootstrap/buildlib-run',
                'bootstrap/python.lock',
                '.github/workflows/*.yml',
                '.github/workflows/*.yaml',
            ),
        ),
    )
