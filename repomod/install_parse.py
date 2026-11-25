from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import PurePosixPath
from urllib.parse import urlsplit

_COMMENT = re.compile(r"(^|\s)#.*$")
_ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
_VARIABLE = re.compile(r"^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?$")
_ACTION_USES = re.compile(r"^\s*-?\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@")
_URL = re.compile(r"https?://[^\s'\"`<>()\[\]{}|\\^]+")
_INSTALL_VERBS = {
    "apk": re.compile(r"\bapk\s+add\b"),
    "apt": re.compile(r"\b(?:apt|apt-get|aptitude)\s+install\b"),
    "brew": re.compile(r"\bbrew\s+install\b"),
    "dnf": re.compile(r"\b(?:dnf|yum)\s+install\b"),
}
_PACMAN = re.compile(r"\bpacman(?![\w-])")
_PACMAN_SYNC = re.compile(r"^-[a-zA-Z]*S[a-zA-Z]*$")
_SEPARATORS = frozenset({"&&", "||", ";", "|"})
_IGNORED_DIRS = frozenset({
    ".git", ".work", "work", "node_modules", "vendor", "dist", "build", "target",
    ".venv", "venv", "__pycache__", ".zig-cache", "zig-cache", "zig-pkg", ".next",
    ".nuxt", "third_party", "fixtures", "generated", "tests", "test", "testing",
    "docs", "doc", "examples", "example", "samples", ".cache", "coverage", ".tox",
    "eggs", ".direnv", "result", "Pods", "DerivedData", ".cargo-home", ".idea",
    ".vscode",
})
_WORKFLOW_SUFFIXES = frozenset({".yml", ".yaml"})
_MAKE_NAMES = frozenset({"makefile", "gnumakefile"})
_INSTALL_SURFACES = frozenset({"workflow", "text"})


def strip_comment(line: str) -> str:
    return _COMMENT.sub("", line)


def surface_kind(relative: PurePosixPath) -> str | None:
    parts = relative.parts
    name = relative.name
    lowered = name.casefold()
    if lowered == "cargo.toml":
        return "manifest:cargo"
    if lowered == "pyproject.toml":
        return "manifest:pypi"
    if lowered.startswith("requirements") and lowered.endswith(".txt"):
        return "manifest:pypi"
    if lowered == "package.json":
        return "manifest:npm"
    if len(parts) >= 2 and parts[-2] == ".cargo" and lowered in {"config", "config.toml"}:
        return "cargo-config"
    if (
        len(parts) == 3
        and parts[0] == ".github"
        and parts[1] == "workflows"
        and PurePosixPath(name).suffix.casefold() in _WORKFLOW_SUFFIXES
    ):
        return "workflow"
    if lowered in _MAKE_NAMES or lowered.endswith(".mk") or lowered == "flake.nix":
        return "text"
    if lowered.startswith(("dockerfile", "containerfile")) or lowered.endswith(".dockerfile"):
        return "text"
    if "scripts" in parts[:-1] or "docker" in parts[:-1]:
        return "text"
    return None


def install_surface(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    if any(part in _IGNORED_DIRS for part in parts[:-1]):
        return None
    kind = surface_kind(PurePosixPath(path))
    return kind if kind in _INSTALL_SURFACES else None


def logical_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    pending = ""
    pending_start = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        piece = pending + strip_comment(raw)
        start = pending_start if pending else number
        if piece.rstrip().endswith("\\"):
            pending = piece.rstrip()[:-1] + " "
            pending_start = start
            continue
        pending = ""
        lines.append((start, piece))
    if pending:
        lines.append((pending_start, pending))
    return lines


def assignments(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        match = _ASSIGNMENT.match(strip_comment(raw))
        if match is None:
            continue
        name, value = match.group(1), match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[name] = value
    return values


def expand(token: str, env: Mapping[str, str], depth: int = 0) -> list[str]:
    if depth > 3:
        return []
    match = _VARIABLE.fullmatch(token)
    if match is None:
        return [token]
    value = env.get(match.group(1))
    if value is None:
        return []
    words: list[str] = []
    for word in value.split():
        words.extend(expand(word, env, depth + 1))
    return words


def package_name(token: str) -> str:
    token = token.strip().strip("'\"")
    for marker in ("=", "<", ">", "!", "~", "^"):
        index = token.find(marker)
        if index > 0:
            token = token[:index]
            break
    if ":" in token:
        token = token.split(":", 1)[0]
    return token


def system_package_installs(
    line: str, env: Mapping[str, str]
) -> list[tuple[str, str]]:
    installs: list[tuple[str, str]] = []
    for manager, verb in _INSTALL_VERBS.items():
        for match in verb.finditer(line):
            packages: list[str] = []
            for token in line[match.end():].split():
                bare = token.strip("'\"")
                if bare in _SEPARATORS:
                    break
                if bare.startswith("-"):
                    continue
                packages.extend(expand(bare, env))
            for raw_name in packages:
                name = package_name(raw_name)
                if name:
                    installs.append((manager, name))
    pacman = _PACMAN.search(line)
    if pacman is not None:
        syncing = False
        packages: list[str] = []
        for token in line[pacman.end():].split():
            bare = token.strip("'\"")
            if bare in _SEPARATORS:
                break
            if _PACMAN_SYNC.fullmatch(bare) or bare in {"--sync", "--sysupgrade"}:
                syncing = True
                continue
            if bare.startswith(("-", "+")):
                continue
            if not syncing:
                break
            packages.extend(expand(bare, env))
        for raw_name in packages:
            name = package_name(raw_name)
            if name:
                installs.append(("pacman", name))
    return installs


def action_references(text: str) -> list[tuple[int, str]]:
    references: list[tuple[int, str]] = []
    for index, line in enumerate(text.splitlines()):
        match = _ACTION_USES.match(line)
        if match is not None:
            references.append((index + 1, match.group(1)))
    return references


def download_urls(line: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for match in _URL.finditer(line):
        raw = match.group(0).rstrip(".,;:!?)\"'")
        try:
            parts = urlsplit(raw)
        except ValueError:
            continue
        hostname = parts.hostname
        if parts.scheme not in {"http", "https"} or hostname is None:
            continue
        host = hostname.casefold()
        path = (parts.path or "").lstrip("/")
        combined = f"{host}/{path}" if path else host
        combined = combined.removesuffix(".git")
        found.append((raw, combined))
    return found
