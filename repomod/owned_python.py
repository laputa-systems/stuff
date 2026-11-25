from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOCK_PATH = ".github/tools.lock.json"
ENVIRONMENT = (
    ("UV_PYTHON_DOWNLOADS", "never"),
    ("UV_PYTHON_PREFERENCE", "only-system"),
)
_UV_SETUP_USES = re.compile(r"^(?P<indent>[ ]*)-[ ]+uses:[ ]+astral-sh/setup-uv@")
_UV_INSTALL_RUN = re.compile(
    r"^(?P<indent>[ ]*)-[ ]+run:[ ]+uv[ ]+python[ ]+install[ ]+"
    r"(?P<version>[0-9]+(?:\.[0-9]+){1,2})[ \t]*(?:#.*)?$"
)
_UV_PYTHON = re.compile(r"\buv\s+python\s+install\b")
_PYTHON_VERSION_INPUT = re.compile(r"^[ \t]*python-version[ \t]*:")
_ENV_KEY = re.compile(r"^env[ \t]*:")
_TOP_KEY = re.compile(r"^(?:defaults|jobs)[ \t]*:")
_ENV_NAME = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)[ \t]*:")


@dataclass(frozen=True, slots=True)
class Site:
    setup: int
    install: int
    indent: str


@dataclass(frozen=True, slots=True)
class Rewrite:
    text: str
    install_lines: frozenset[int]
    setup_lines: frozenset[int]


def approved_cpython() -> dict[str, Any]:
    from repomod.rules.tools_lock import _load_policy

    entry = _load_policy().get("cpython")
    if entry is None:
        raise ValueError("tools-lock policy has no approved cpython entry")
    return entry


def cpython_minor(entry: dict[str, Any]) -> str:
    version = entry.get("version")
    if not isinstance(version, str):
        raise ValueError("approved cpython entry has no version")
    parts = version.split(".")
    if len(parts) < 2 or not all(part.isdigit() for part in parts[:2]):
        raise ValueError(f"approved cpython version {version!r} has no major.minor")
    return f"{parts[0]}.{parts[1]}"


def buildlib_setup_pin() -> Any:
    from repomod.rules.actions import load_pins

    pin = load_pins().get("laputa-systems/buildlib")
    if pin is None:
        raise ValueError("actions.toml has no laputa-systems/buildlib pin")
    return pin


def setup_step_lines(indent: str, pin: Any) -> list[str]:
    return [
        f"{indent}- uses: laputa-systems/buildlib/setup@{pin.sha} # {pin.version}",
        f"{indent}  with:",
        f"{indent}    tools: cpython",
        f"{indent}    lock: {LOCK_PATH}",
    ]


def environment_lines() -> list[str]:
    return ["env:", *(f"  {name}: {value}" for name, value in ENVIRONMENT)]


def _eol(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith(("\n", "\r")):
        return line[-1:]
    return "\n"


def _body(line: str) -> str:
    return line.rstrip("\r\n")


def _version_minor(spec: str) -> str | None:
    parts = spec.split(".")
    if not 2 <= len(parts) <= 3 or not all(part.isdigit() for part in parts):
        return None
    return f"{parts[0]}.{parts[1]}"


def _step_end(lines: list[str], start: int, indent: int) -> int:
    index = start
    while index < len(lines):
        body = _body(lines[index])
        if not body.strip():
            index += 1
            continue
        if len(body) - len(body.lstrip(" ")) <= indent:
            return index
        index += 1
    return index


def _sites(lines: list[str], minor: str) -> list[Site]:
    sites: list[Site] = []
    for index, raw in enumerate(lines):
        body = _body(raw)
        match = _UV_SETUP_USES.match(body)
        if match is None:
            continue
        indent = match.group("indent")
        end = _step_end(lines, index + 1, len(indent))
        if any(
            _PYTHON_VERSION_INPUT.match(_body(line))
            for line in lines[index + 1 : end]
            if _body(line).strip()
        ):
            continue
        if end >= len(lines):
            continue
        following = _body(lines[end])
        if len(following) - len(following.lstrip(" ")) != len(indent):
            continue
        install = _UV_INSTALL_RUN.match(following)
        if install is None or _version_minor(install.group("version")) != minor:
            continue
        run_end = _step_end(lines, end + 1, len(indent))
        if any(_body(line).strip() for line in lines[end + 1 : run_end]):
            continue
        sites.append(Site(setup=index, install=end, indent=indent))
    return sites


def _resolved_setup_lines(lines: list[str], removed: frozenset[int]) -> frozenset[int]:
    uv_lines = {
        index + 1
        for index, line in enumerate(lines)
        if _UV_PYTHON.search(_body(line))
    }
    remaining = uv_lines - removed
    resolved: set[int] = set()
    for index, raw in enumerate(lines):
        body = _body(raw)
        match = _UV_SETUP_USES.match(body)
        if match is None:
            continue
        number = index + 1
        end = _step_end(lines, index + 1, len(match.group("indent")))
        if any(
            _PYTHON_VERSION_INPUT.match(_body(line))
            for line in lines[index + 1 : end]
            if _body(line).strip()
        ):
            continue
        if any(line > number for line in remaining):
            continue
        resolved.add(number)
    return frozenset(resolved)


def _merge_existing_env(lines: list[str], index: int) -> list[str] | None:
    after = _body(lines[index]).split(":", 1)[1].strip()
    if after and not after.startswith("#"):
        return None
    child_indent: str | None = None
    present: set[str] = set()
    last_child = index
    cursor = index + 1
    while cursor < len(lines):
        body = _body(lines[cursor])
        if not body.strip():
            cursor += 1
            continue
        stripped = body.lstrip(" ")
        if len(body) - len(stripped) == 0:
            break
        if child_indent is None:
            child_indent = " " * (len(body) - len(stripped))
        name = _ENV_NAME.match(stripped)
        if name is not None:
            present.add(name.group(1))
        last_child = cursor
        cursor += 1
    missing = [
        (name, value) for name, value in ENVIRONMENT if name not in present
    ]
    if not missing:
        return lines
    indent = child_indent if child_indent is not None else "  "
    eol = _eol(lines[last_child]) if last_child > index else _eol(lines[index])
    inserted = [f"{indent}{name}: {value}{eol}" for name, value in missing]
    return [*lines[: last_child + 1], *inserted, *lines[last_child + 1 :]]


def _insert_env(lines: list[str]) -> list[str] | None:
    anchor = -1
    for index, line in enumerate(lines):
        if _TOP_KEY.match(_body(line)):
            anchor = index
            break
    if anchor < 0:
        return None
    eol = _eol(lines[anchor])
    block = ["env:" + eol]
    block.extend(f"  {name}: {value}{eol}" for name, value in ENVIRONMENT)
    insert_at = anchor
    if insert_at > 0 and not _body(lines[insert_at - 1]).strip():
        insert_at -= 1
        return [*lines[:insert_at], eol, *block, *lines[insert_at:]]
    return [*lines[:insert_at], eol, *block, eol, *lines[insert_at:]]


def _merge_env(text: str) -> str | None:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if _ENV_KEY.match(_body(line)):
            merged = _merge_existing_env(lines, index)
            return None if merged is None else "".join(merged)
    inserted = _insert_env(lines)
    return None if inserted is None else "".join(inserted)


def rewrite_workflow(text: str, minor: str, pin: Any) -> Rewrite | None:
    lines = text.splitlines(keepends=True)
    sites = _sites(lines, minor)
    if not sites:
        return None
    removed = frozenset(site.install + 1 for site in sites)
    inserts = {site.setup: site.indent for site in sites}
    output: list[str] = []
    for index, line in enumerate(lines):
        number = index + 1
        if number in removed:
            continue
        indent = inserts.get(index)
        if indent is not None:
            eol = _eol(line)
            output.extend(f"{step}{eol}" for step in setup_step_lines(indent, pin))
        output.append(line)
    merged = _merge_env("".join(output))
    if merged is None:
        return None
    return Rewrite(
        text=merged,
        install_lines=removed,
        setup_lines=_resolved_setup_lines(lines, removed),
    )


def _lock_document(existing: str | None, entry: dict[str, Any]) -> dict[str, Any] | None:
    if existing is None:
        return {"schema": 1, "tools": {}}
    try:
        document = json.loads(existing)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(document, dict):
        return None
    if type(document.get("schema")) is not int or document.get("schema") != 1:
        return None
    tools = document.get("tools")
    if not isinstance(tools, dict):
        return None
    document = dict(document)
    document["tools"] = dict(tools)
    return document


def lock_content(existing: str | None, entry: dict[str, Any]) -> str | None:
    document = _lock_document(existing, entry)
    if document is None:
        return None
    tools = document["tools"]
    approved = {
        "repository": entry["repository"],
        "tag": entry["tag"],
        "product": entry["product"],
        "version": entry["version"],
        "assets": {
            triple: dict(pin) for triple, pin in entry["assets"].items()
        },
    }
    tools["cpython"] = approved
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def render_lock(root: Path) -> tuple[str | None, str] | None:
    try:
        entry = approved_cpython()
    except ValueError:
        return None
    path = root / LOCK_PATH
    if path.is_symlink() or (path.exists() and not path.is_file()):
        return None
    existing: str | None = None
    if path.is_file():
        try:
            existing = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return None
    content = lock_content(existing, entry)
    if content is None:
        return None
    return existing, content


def lock_plan(root: Path) -> dict[str, str]:
    rendered = render_lock(root)
    if rendered is None:
        return {}
    existing, content = rendered
    if content == existing:
        return {}
    return {LOCK_PATH: content}
