from __future__ import annotations

import datetime
import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from repomod import paths
from repomod.catalog import load_catalog
from repomod.io import read_json_object
from repomod.types import Finding, RepoId, Repository, Rule, TagPredicate, operational, violation

_RULE = 'buildlib-usage'
_POLICY = 'fleet/policy/buildlib.toml'
_BOOTSTRAP = ('buildlib-run', 'python.lock')
_SHA256 = re.compile(r'[0-9a-f]{64}')
_DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
_PACKAGE = re.compile(r'laputa-buildlib(\[[^\]]*\])?(?:[=<>!~@;\s]|$)', re.IGNORECASE)
_EXACT = 'laputa-buildlib{}=={}'


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
            'wheel_version', 'wheel_filename', 'wheel_sha256', 'bootstrap_sha256', 'bootstrap_revision',
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
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise ValueError('artifact wheel_sha256 must be 64 lowercase hex digits')
    revision = artifact.get('bootstrap_revision')
    if revision is not None and (not isinstance(revision, str) or re.fullmatch(r'[0-9a-f]{40}', revision) is None):
        raise ValueError('artifact bootstrap_revision must be a 40-hex revision when present')
    return Policy(
        version,
        filename,
        digest,
        _declared_digests(artifact.get('bootstrap_sha256'), 'artifact.bootstrap_sha256'),
        _table(data, 'enrolled'),
        _table(data, 'assess'),
        _table(data, 'exempt'),
    )


def _known_repositories() -> frozenset[str]:
    return frozenset(str(repository.id) for repository in load_catalog(paths.CATALOG).repositories)


def _dependency_strings(value: object) -> list[str]:
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                if isinstance(child, str):
                    found.append(child)
                else:
                    walk(child)

    walk(value)
    return found


def _pin(root: Path, repository: Repository, policy: Policy) -> list[Finding]:
    path = root / 'pyproject.toml'
    expected = _EXACT.format('', policy.wheel_version)
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return [violation(repository, _RULE, 'pyproject.toml',
                          f'missing pyproject.toml; enrolled consumers must pin {expected}')]
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        return [operational(repository, _RULE, 'pyproject.toml', str(error))]
    entries = [entry.strip() for entry in _dependency_strings(data) if _PACKAGE.match(entry.strip())]
    if not entries:
        return [violation(repository, _RULE, 'pyproject.toml',
                          f'missing laputa-buildlib dependency; enrolled consumers must pin {expected}')]
    if any(entry.split(';', 1)[0].strip() == expected for entry in entries):
        return []
    return [violation(repository, _RULE, 'pyproject.toml',
                      f'laputa-buildlib must be pinned exactly as {expected}; found {", ".join(entries)}')]


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


def _source_digests(document: dict[str, Any], filename: str) -> list[str | None]:
    inputs = document.get('inputs')
    if not isinstance(inputs, list):
        return []
    digests: list[str | None] = []
    for entry in inputs:
        if not isinstance(entry, dict):
            continue
        urls: list[str] = []
        url = entry.get('url')
        if isinstance(url, str):
            urls.append(url)
        many = entry.get('urls')
        if isinstance(many, list):
            urls.extend(item for item in many if isinstance(item, str))
        if any(PurePosixPath(item.split('?', 1)[0]).name == filename for item in urls):
            digest = entry.get('sha256')
            digests.append(digest if isinstance(digest, str) else None)
    return digests


def _uv_lock(root: Path, repository: Repository, policy: Policy) -> list[Finding]:
    path = root / 'uv.lock'
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return [violation(repository, _RULE, 'uv.lock',
                          f'missing uv.lock; cannot verify the approved {policy.wheel_filename} sha256')]
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        return [operational(repository, _RULE, 'uv.lock', str(error))]
    matched, digests = _wheel_digests(data, policy.wheel_filename)
    if not matched:
        return [violation(repository, _RULE, 'uv.lock',
                          f'uv.lock does not record the approved {policy.wheel_filename} wheel')]
    return [
        violation(repository, _RULE, 'uv.lock',
                  f'uv.lock records wheel sha256 {digest or "missing"}; policy approves {policy.wheel_sha256}')
        for digest in digests
        if digest != policy.wheel_sha256
    ]


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
    return [
        violation(repository, _RULE, 'sources.lock.json',
                  f'sources.lock.json records wheel sha256 {digest or "missing"}; '
                  f'policy approves {policy.wheel_sha256}')
        for digest in _source_digests(document, policy.wheel_filename)
        if digest != policy.wheel_sha256
    ]


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
        if path.is_symlink():
            findings.append(operational(repository, _RULE, relative, f'{relative} is a symlink and was not inspected'))
            continue
        if not path.exists():
            if required:
                findings.append(violation(repository, _RULE, relative, f'missing bootstrap shim {relative}'))
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            findings.append(operational(repository, _RULE, relative, str(error)))
            continue
        allowed = approved.get(name, frozenset()) | local.get(name, frozenset())
        if digest not in allowed:
            findings.append(violation(
                repository, _RULE, relative,
                f'{relative} sha256 {digest} is not an approved identity or declared local difference',
            ))
    return findings


def _entrypoints(root: Path, repository: Repository, entrypoints: list[str]) -> list[Finding]:
    findings = []
    for entry in entrypoints:
        relpath = Path(entry)
        if relpath.is_absolute() or '..' in relpath.parts:
            findings.append(violation(repository, _RULE, _POLICY,
                                      f'enrolled entrypoint {entry!r} must be repository-relative'))
        elif not (root / relpath).exists():
            findings.append(violation(repository, _RULE, entry, f'declared entrypoint {entry} does not exist'))
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
            expired = datetime.date.fromisoformat(condition) < datetime.date.today()
        except ValueError:
            expired = False
        if expired:
            findings.append(violation(repository, _RULE, _POLICY,
                                      f'exempt {name} expired on {condition}; reassess it against current conditions'))
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
    if len(classifications) > 1:
        findings.append(violation(repository, _RULE, _POLICY,
                                  f'{name} is classified more than once in the buildlib policy: '
                                  + ', '.join(classifications)))
        return findings
    if 'enrolled' in classifications:
        findings.extend(_enrolled(root, repository, policy.enrolled[name], policy))
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


def buildlib_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            'buildlib-usage',
            'Enforce the approved laputa-buildlib pin, bootstrap provenance, and declared entrypoints',
            TagPredicate(),
            _check,
            None,
            None,
            (),
        ),
    )
