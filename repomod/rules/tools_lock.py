from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any, cast

from repomod import buildlib_pins, paths
from repomod.types import Finding, Repository, Rule, TagPredicate, operational, violation

_RULE = 'tools-lock'
_POLICY = 'fleet/policy/tools-lock.toml'
_LOCK_PATHS = ('tools.lock.json', '.github/tools.lock.json')
_ENTRY_KEYS = frozenset({'repository', 'tag', 'product', 'version', 'assets'})
_ASSET_KEYS = frozenset({'name', 'size', 'sha256'})
_SHA256_LENGTH = 64


def _policy_path() -> Path:
    return paths.POLICY / 'tools-lock.toml'


def _hex_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _SHA256_LENGTH
        and all(character in '0123456789abcdef' for character in value)
    )


def _approved_entry(raw: object, where: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f'{where} must be a table')
    entry = cast(dict[str, Any], raw)
    missing = sorted(_ENTRY_KEYS - set(entry))
    extra = sorted(str(key) for key in set(entry) - _ENTRY_KEYS)
    if missing or extra:
        parts = []
        if missing:
            parts.append(f'missing {", ".join(missing)}')
        if extra:
            parts.append(f'unexpected {", ".join(extra)}')
        raise ValueError(f'{where}: {"; ".join(parts)}')
    for key in ('repository', 'tag', 'product', 'version'):
        if not isinstance(entry[key], str):
            raise ValueError(f'{where}.{key} must be a string')
    assets = entry.get('assets')
    if not isinstance(assets, dict) or not assets:
        raise ValueError(f'{where}.assets must be a non-empty table')
    approved_assets: dict[str, Any] = {}
    for triple, pin_raw in assets.items():
        if not isinstance(triple, str) or not triple:
            raise ValueError(f'{where}.assets keys must be target triples')
        asset_where = f'{where}.assets.{triple}'
        if not isinstance(pin_raw, dict):
            raise ValueError(f'{asset_where} must be a table')
        pin = cast(dict[str, Any], pin_raw)
        asset_missing = sorted(_ASSET_KEYS - set(pin))
        asset_extra = sorted(str(key) for key in set(pin) - _ASSET_KEYS)
        if asset_missing or asset_extra:
            raise ValueError(f'{asset_where} must contain only name, size, and sha256')
        if not isinstance(pin['name'], str) or not pin['name']:
            raise ValueError(f'{asset_where}.name must be a non-empty string')
        if type(pin['size']) is not int or pin['size'] < 0:
            raise ValueError(f'{asset_where}.size must be a non-negative integer')
        if not _hex_digest(pin['sha256']):
            raise ValueError(f'{asset_where}.sha256 must be 64 lowercase hex digits')
        approved_assets[triple] = {
            'name': pin['name'],
            'size': pin['size'],
            'sha256': pin['sha256'],
        }
    return {
        'repository': entry['repository'],
        'tag': entry['tag'],
        'product': entry['product'],
        'version': entry['version'],
        'assets': approved_assets,
    }


def _load_policy() -> dict[str, dict[str, Any]]:
    path = _policy_path()
    if path.is_symlink():
        raise ValueError('tools-lock policy is a symlink')
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f'cannot load tools-lock policy: {error}') from error
    if set(data) - {'version', 'tools'} or data.get('version') != 1:
        raise ValueError('unknown or missing tools-lock policy, or invalid version')
    tools = data.get('tools')
    if not isinstance(tools, dict):
        raise ValueError('tools-lock policy needs a [tools] table')
    approved: dict[str, dict[str, Any]] = {}
    for name, raw in tools.items():
        if not isinstance(name, str) or not name:
            raise ValueError('tools-lock policy tool names must be non-empty strings')
        approved[name] = _approved_entry(raw, f'tools.{name}')
    return approved


def _lock_files(root: Path) -> list[tuple[str, Path]]:
    files = []
    for relative in _LOCK_PATHS:
        path = root / relative
        if path.is_symlink() or not path.exists():
            continue
        files.append((relative, path))
    return files


def _entry_findings(
    document: dict[str, Any],
    relative: str,
    repository: Repository,
    approved: dict[str, dict[str, Any]],
) -> list[Finding]:
    schema = document.get('schema')
    if type(schema) is not int or schema != 1:
        return [violation(
            repository, _RULE, relative,
            f'{relative} schema must be 1, found {schema!r}',
        )]
    tools = document.get('tools')
    if not isinstance(tools, dict):
        return [violation(
            repository, _RULE, relative,
            f'{relative} tools must be an object',
        )]
    findings: list[Finding] = []
    for tool, raw in tools.items():
        if tool not in buildlib_pins.TOOLS_LOCK_TOOLS:
            findings.append(violation(
                repository, _RULE, relative,
                f'{relative} records unknown tool {tool!r}',
            ))
            continue
        entry = approved.get(tool)
        if entry is None or raw == entry:
            continue
        tag = raw.get('tag') if isinstance(raw, dict) else None
        findings.append(violation(
            repository, _RULE, relative,
            f'{relative} pins {tool} at {tag!r}; policy approves {entry["tag"]!r}',
            fixable=True,
        ))
    return findings


def _check_file(
    path: Path, relative: str, repository: Repository, approved: dict[str, dict[str, Any]]
) -> list[Finding]:
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        return [operational(repository, _RULE, relative, f'cannot read {relative}: {error}')]
    try:
        document = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return [violation(
            repository, _RULE, relative,
            f'{relative} is not a valid JSON object: {error}',
        )]
    if not isinstance(document, dict):
        return [violation(
            repository, _RULE, relative,
            f'{relative} is not a valid JSON object: expected an object',
        )]
    return _entry_findings(document, relative, repository, approved)


def _check(root: Path, repository: Repository) -> list[Finding]:
    try:
        approved = _load_policy()
    except ValueError as error:
        return [operational(repository, _RULE, _POLICY, str(error))]
    findings: list[Finding] = []
    for relative, path in _lock_files(root):
        findings.extend(_check_file(path, relative, repository, approved))
    return findings


def _fix(root: Path, repository: Repository) -> dict[str, str]:
    try:
        approved = _load_policy()
    except ValueError:
        return {}
    plan: dict[str, str] = {}
    for relative, path in _lock_files(root):
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            continue
        try:
            document = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(document, dict):
            continue
        tools = document.get('tools')
        schema = document.get('schema')
        if type(schema) is not int or schema != 1 or not isinstance(tools, dict):
            continue
        changed = False
        updated = dict(document)
        tools_map = dict(tools)
        for tool, entry in approved.items():
            if tool not in tools_map or tools_map[tool] == entry:
                continue
            tools_map[tool] = {
                'repository': entry['repository'],
                'tag': entry['tag'],
                'product': entry['product'],
                'version': entry['version'],
                'assets': {
                    triple: dict(pin) for triple, pin in entry['assets'].items()
                },
            }
            changed = True
        if not changed:
            continue
        updated['tools'] = tools_map
        result = json.dumps(updated, indent=2, sort_keys=True) + '\n'
        if result != text:
            plan[relative] = result
    return plan


def tools_lock_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            _RULE,
            'Require consumer tools.lock.json entries to match the approved tool releases',
            TagPredicate(),
            _check,
            _fix,
            'build(tools): pin approved tool releases',
            _LOCK_PATHS,
        ),
    )
