from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from repomod import paths
from repomod.catalog import load_catalog
from repomod.owned_tools import load_owned_tools
from repomod.types import Finding, RepoId, Repository, Rule, TagPredicate, operational, violation

RULE = "owned-tool-substitution"
_POLICY = "fleet/policy/owned-substitutes.toml"
_OWNED_POLICY = "fleet/policy/owned-tools.toml"
_BUILDLIB_HINT = "buildlib.tools or the laputa-systems/buildlib/setup action"
_MANAGERS = frozenset({"apk", "apt", "apt-get", "brew", "dnf", "yum", "pacman"})
_MANAGER_ALIASES = {"apt-get": "apt", "yum": "dnf"}
_ACTION_USES = re.compile(r"^\s*-?\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@")
_UV_PYTHON = re.compile(r"\buv\s+python\s+install\b")
_PYTHON_VERSION = re.compile(r"^\s*python-version\s*:")
_WITH = re.compile(r"^\s*with\s*:")
_ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
_VARIABLE = re.compile(r"^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?$")
_URL = re.compile(r"https?://[^\s'\"`<>()\[\]{}|\\^]+")
_COMMENT = re.compile(r"(^|\s)#.*$")
_INSTALL_VERBS = {
    "apk": re.compile(r"\bapk\s+add\b"),
    "apt": re.compile(r"\b(?:apt|apt-get|aptitude)\s+install\b"),
    "brew": re.compile(r"\bbrew\s+install\b"),
    "dnf": re.compile(r"\b(?:dnf|yum)\s+install\b"),
}
_PACMAN = re.compile(r"\bpacman(?![\w-])")
_PACMAN_SYNC = re.compile(r"^-[a-zA-Z]*S[a-zA-Z]*$")
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
_SEPARATORS = frozenset({"&&", "||", ";", "|"})


@dataclass(frozen=True, slots=True)
class ProducerSub:
    packages: dict[str, tuple[str, ...]]
    actions: frozenset[str]
    urls: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Exemption:
    producer: str
    reason: str
    reassess: str


@dataclass(frozen=True, slots=True)
class Policy:
    producers: dict[str, ProducerSub]
    exempt: dict[str, tuple[Exemption, ...]]


@dataclass(frozen=True, slots=True)
class Hit:
    line: int
    label: str
    producer: str


def _policy_path() -> Path:
    return paths.POLICY / "owned-substitutes.toml"


def _string_list(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return tuple(item.strip() for item in value if isinstance(item, str))


def _load_producer(name: str, raw: object) -> ProducerSub:
    label = f"producers.{name}"
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a table")
    unknown = set(raw) - {"packages", "actions", "urls"}
    if unknown:
        raise ValueError(f"{label} has unknown keys: {', '.join(sorted(str(k) for k in unknown))}")
    raw_packages = raw.get("packages", {})
    if not isinstance(raw_packages, dict):
        raise ValueError(f"{label}.packages must be a table of manager package lists")
    packages: dict[str, tuple[str, ...]] = {}
    for manager, items in raw_packages.items():
        if not isinstance(manager, str) or manager not in _MANAGERS:
            raise ValueError(f"{label}.packages names an unknown manager {manager!r}")
        normalized = _MANAGER_ALIASES.get(manager, manager)
        if normalized in packages:
            raise ValueError(f"{label}.packages lists manager {normalized} more than once")
        packages[normalized] = _string_list(items, f"{label}.packages.{manager}")
    actions = frozenset(_string_list(raw.get("actions", []), f"{label}.actions"))
    for action in actions:
        try:
            RepoId.parse(action)
        except ValueError as error:
            raise ValueError(f"{label}.actions entry {action!r} is not OWNER/REPO") from error
    urls = _string_list(raw.get("urls", []), f"{label}.urls")
    for url in urls:
        host = url.split("/", 1)[0]
        if "://" in url or not host or "." not in host:
            raise ValueError(f"{label}.urls entry {url!r} must name a host or host/path prefix")
    if not packages and not actions and not urls:
        raise ValueError(f"{label} must declare packages, actions, or urls")
    return ProducerSub(packages, actions, urls)


def _load_exemption(repo: str, producer: str, raw: object) -> Exemption:
    label = f"exempt.{repo}.producers.{producer}"
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a table")
    unknown = set(raw) - {"reason", "reassess"}
    if unknown:
        raise ValueError(f"{label} has unknown keys: {', '.join(sorted(str(k) for k in unknown))}")
    reason = raw.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError(f"{label} needs a non-empty reason")
    reassess = raw.get("reassess")
    if not isinstance(reassess, str) or not reassess.strip():
        raise ValueError(f"{label} needs a non-empty reassessment condition")
    return Exemption(producer, reason.strip(), reassess.strip())


def _load_policy() -> Policy:
    path = _policy_path()
    if path.is_symlink():
        raise ValueError("owned-substitutes policy is a symlink")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"cannot load owned-substitutes policy: {error}") from error
    if set(data) - {"version", "producers", "exempt"} or data.get("version") != 1:
        raise ValueError("unknown or missing owned-substitutes policy, or invalid version")
    raw_producers = data.get("producers", {})
    if not isinstance(raw_producers, dict):
        raise ValueError("[producers] must be a table")
    producers = {str(name): _load_producer(str(name), entry) for name, entry in raw_producers.items()}
    raw_exempt = data.get("exempt", {})
    if not isinstance(raw_exempt, dict):
        raise ValueError("[exempt] must be a table")
    exempt: dict[str, tuple[Exemption, ...]] = {}
    for repo, entry in raw_exempt.items():
        if not isinstance(entry, dict) or set(entry) - {"producers"}:
            raise ValueError(f"exempt.{repo} must be a table containing only [exempt.{repo}.producers]")
        raw_map = entry.get("producers", {})
        if not isinstance(raw_map, dict):
            raise ValueError(f"exempt.{repo}.producers must be a table")
        exempt[str(repo)] = tuple(
            _load_exemption(str(repo), str(producer), value)
            for producer, value in raw_map.items()
        )
    return Policy(producers, exempt)


def _owned_producers() -> frozenset[str]:
    return frozenset(str(producer.repo).casefold() for producer in load_owned_tools().producers)


def _known_repositories() -> frozenset[str]:
    return frozenset(str(repository.id) for repository in load_catalog(paths.CATALOG).repositories)


def _surface_kind(relative: PurePosixPath) -> str | None:
    parts = relative.parts
    name = relative.name
    lowered = name.casefold()
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


def _surface_files(root: Path) -> list[tuple[str, str, str]]:
    files: list[tuple[str, str, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in _IGNORED_DIRS and not (base / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = base / filename
            if path.is_symlink() or not path.is_file():
                continue
            relative = PurePosixPath(path.relative_to(root).as_posix())
            kind = _surface_kind(relative)
            if kind is None:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeError:
                continue
            except OSError as error:
                files.append((relative.as_posix(), "error", str(error)))
                continue
            files.append((relative.as_posix(), kind, text))
    return files


def _strip_comment(line: str) -> str:
    return _COMMENT.sub("", line)


def _logical_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    pending = ""
    pending_start = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        piece = pending + _strip_comment(raw)
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


def _assignments(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        match = _ASSIGNMENT.match(_strip_comment(raw))
        if match is None:
            continue
        name, value = match.group(1), match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[name] = value
    return values


def _expand(token: str, env: dict[str, str], depth: int = 0) -> list[str]:
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
        words.extend(_expand(word, env, depth + 1))
    return words


def _package_name(token: str) -> str:
    token = token.strip().strip("'\"")
    for marker in ("=", "<", ">", "!", "~", "^"):
        index = token.find(marker)
        if index > 0:
            token = token[:index]
            break
    if ":" in token:
        token = token.split(":", 1)[0]
    return token


def _package_hits(name: str, manager: str, producers: dict[str, ProducerSub]) -> str | None:
    for producer_id, sub in producers.items():
        for entry in sub.packages.get(manager, ()):
            if entry.startswith("^"):
                if re.fullmatch(entry, name):
                    return producer_id
            elif entry == name:
                return producer_id
    return None


def _install_hits(line: str, env: dict[str, str], producers: dict[str, ProducerSub]) -> list[Hit]:
    hits: list[Hit] = []
    for manager, verb in _INSTALL_VERBS.items():
        normalized = _MANAGER_ALIASES.get(manager, manager)
        for match in verb.finditer(line):
            packages: list[str] = []
            for token in line[match.end():].split():
                bare = token.strip("'\"")
                if bare in _SEPARATORS:
                    break
                if bare.startswith("-"):
                    continue
                packages.extend(_expand(bare, env))
            for raw_name in packages:
                name = _package_name(raw_name)
                if not name:
                    continue
                producer_id = _package_hits(name, normalized, producers)
                if producer_id is not None:
                    hits.append(Hit(0, f"package '{name}' installed by {manager}", producer_id))
    pacman = _PACMAN.search(line)
    if pacman is not None:
        syncing = False
        packages = []
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
            packages.extend(_expand(bare, env))
        if syncing:
            for raw_name in packages:
                name = _package_name(raw_name)
                if not name:
                    continue
                producer_id = _package_hits(name, "pacman", producers)
                if producer_id is not None:
                    hits.append(Hit(0, f"package '{name}' installed by pacman", producer_id))
    return hits


def _url_hits(line: str, producers: dict[str, ProducerSub]) -> list[tuple[str, str]]:
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
        for producer_id, sub in producers.items():
            for prefix in sub.urls:
                wanted = prefix.casefold().rstrip("/")
                if combined == wanted or combined.startswith(wanted + "/"):
                    found.append((producer_id, raw))
                    break
    return found


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _with_block(lines: list[str], index: int) -> list[str]:
    stripped = lines[index].lstrip()
    key_indent = _indent(lines[index]) + (len(stripped) - len(stripped.lstrip("- ")))
    for j in range(index + 1, len(lines)):
        raw = lines[j]
        text = raw.strip()
        if not text:
            continue
        indent = _indent(raw)
        if indent < key_indent or (indent == key_indent and text.startswith("- ")):
            return []
        if indent == key_indent and _WITH.match(raw):
            block: list[str] = []
            for k in range(j + 1, len(lines)):
                inner = lines[k]
                if inner.strip() and _indent(inner) <= key_indent:
                    break
                block.append(inner)
            return block
    return []


def _action_hits(text: str, producers: dict[str, ProducerSub]) -> list[Hit]:
    hits: list[Hit] = []
    lines = text.splitlines()
    action_map = {
        action.casefold(): producer_id
        for producer_id, sub in producers.items()
        for action in sub.actions
    }
    for index, line in enumerate(lines):
        match = _ACTION_USES.match(line)
        if match is None:
            continue
        action = match.group(1).rstrip(".")
        producer_id = action_map.get(action.casefold())
        if producer_id is None:
            continue
        if action.casefold() == "astral-sh/setup-uv":
            block = _with_block(lines, index)
            provides_python = any(_PYTHON_VERSION.match(entry) for entry in block) or any(
                _UV_PYTHON.search(following)
                for following in lines[index + 1:]
            )
            if not provides_python:
                continue
        hits.append(Hit(index + 1, f"action '{action}'", producer_id))
    return hits


def _file_hits(kind: str, text: str, producers: dict[str, ProducerSub]) -> list[Hit]:
    env = _assignments(text)
    hits: list[Hit] = []
    if kind == "workflow":
        hits.extend(_action_hits(text, producers))
    uv_producer = next(
        (
            producer_id
            for producer_id, sub in producers.items()
            if "astral-sh/setup-uv" in {action.casefold() for action in sub.actions}
        ),
        "laputa-systems/python-build",
    )
    for number, line in _logical_lines(text):
        hits.extend(
            Hit(number, hit.label, hit.producer)
            for hit in _install_hits(line, env, producers)
        )
        hits.extend(
            Hit(number, f"URL '{url}'", producer_id)
            for producer_id, url in _url_hits(line, producers)
        )
        if _UV_PYTHON.search(line):
            hits.append(Hit(number, "command 'uv python install'", uv_producer))
    deduped: dict[tuple[int, str, str], Hit] = {}
    for hit in hits:
        deduped.setdefault((hit.line, hit.label, hit.producer), hit)
    return sorted(deduped.values(), key=lambda hit: (hit.line, hit.label))


def _exemptions_for(policy: Policy, repository: Repository) -> dict[str, Exemption]:
    folded = {key.casefold(): value for key, value in policy.exempt.items()}
    entries = folded.get(str(repository.id).casefold())
    if entries is None:
        return {}
    return {item.producer.casefold(): item for item in entries}


def _semantic_policy_findings(
    repository: Repository,
    policy: Policy,
    known: frozenset[str],
    owned: frozenset[str],
) -> list[Finding]:
    if known and str(repository.id) != min(known, key=str.casefold):
        return []
    findings: list[Finding] = []
    producer_keys = {key.casefold() for key in policy.producers}
    findings.extend(
        violation(
            repository, RULE, _POLICY,
            f"owned-substitutes producer {name} is not an owned-tools producer",
        )
        for name in policy.producers
        if name.casefold() not in owned
    )
    for name, items in policy.exempt.items():
        try:
            repo = RepoId.parse(name)
        except ValueError:
            findings.append(violation(
                repository, RULE, _POLICY,
                f"exempt {name!r} is not an OWNER/REPO catalog key",
            ))
            continue
        if known and str(repo) not in known:
            findings.append(violation(
                repository, RULE, _POLICY,
                f"owned-substitutes exempts {repo}, which is not an active catalog repository",
            ))
        findings.extend(
            violation(
                repository, RULE, _POLICY,
                f"exempt.{name} names unknown producer {item.producer}",
            )
            for item in items
            if item.producer.casefold() not in producer_keys
        )
    return findings


def _check(root: Path, repository: Repository) -> list[Finding]:
    try:
        policy = _load_policy()
    except ValueError as error:
        return [operational(repository, RULE, _POLICY, str(error))]
    try:
        owned = _owned_producers()
        known = _known_repositories()
    except ValueError as error:
        return [operational(repository, RULE, _OWNED_POLICY, str(error))]
    findings = _semantic_policy_findings(repository, policy, known, owned)
    exemptions = _exemptions_for(policy, repository)
    suppressed: set[str] = set()
    reported: list[Finding] = []
    for relative, kind, payload in _surface_files(root):
        if kind == "error":
            findings.append(operational(repository, RULE, relative, payload))
            continue
        for hit in _file_hits(kind, payload, policy.producers):
            key = hit.producer.casefold()
            canonical = next(
                (name for name in policy.producers if name.casefold() == key),
                hit.producer,
            )
            if key in exemptions:
                suppressed.add(key)
                continue
            reported.append(violation(
                repository, RULE, relative,
                f"{hit.label} duplicates owned producer {canonical}; "
                f"acquire it through {_BUILDLIB_HINT} instead of the upstream install",
                line=hit.line,
            ))
    for key, item in exemptions.items():
        if key not in suppressed:
            reported.append(violation(
                repository, RULE, _POLICY,
                f"stale exemption for producer {item.producer}: it matches no finding in this repository; "
                "remove it or restore the install it was granted for",
            ))
    findings.extend(reported)
    return findings


def owned_substitution_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            RULE,
            "Block upstream installs of tools an owned producer ships",
            TagPredicate(),
            _check,
            None,
            None,
            (),
        ),
    )
