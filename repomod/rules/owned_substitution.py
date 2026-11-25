from __future__ import annotations

import json
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast
from urllib.parse import urlsplit

from repomod import owned_python, paths, substitutes
from repomod.catalog import load_catalog
from repomod.owned_tools import load_owned_tools
from repomod.substitutes import Exemption, Policy, ProducerSub
from repomod.types import Finding, RepoId, Repository, Rule, TagPredicate, operational, violation

RULE = "owned-tool-substitution"
_POLICY = "fleet/policy/owned-substitutes.toml"
_OWNED_POLICY = "fleet/policy/owned-tools.toml"
_BUILDLIB_HINT = "buildlib.tools or the laputa-systems/buildlib/setup action"
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
_PIP_INSTALL = re.compile(r"(?<![\w.])(?<!uv )(?:pip3?|python[\d.]*\s+-m\s+pip)\s+install\b")
_UV_ADD = re.compile(r"\buv\s+add\b")
_UV_PIP_INSTALL = re.compile(r"\buv\s+pip\s+install\b")
_CARGO_INSTALL = re.compile(r"\bcargo\s+install\b")
_WRAPPER_ASSIGN = re.compile(r"\b(?:RUSTC_WRAPPER|rustc-wrapper)\s*[:=]\s*[\"']?([^\s\"']+)")
_DEP_SECTIONS = ("dependencies", "dev-dependencies", "build-dependencies")
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
class Hit:
    line: int
    label: str
    producer: str


def _load_policy() -> Policy:
    return substitutes.load_policy()


def _owned_producers() -> frozenset[str]:
    policy = load_owned_tools()
    owned = {str(producer.repo).casefold() for producer in policy.producers}
    owned.update(
        str(repository.id).casefold()
        for repository in load_catalog(paths.CATALOG).repositories
        if policy.owned(repository.id)
    )
    return frozenset(owned)


def _known_repositories() -> frozenset[str]:
    return frozenset(str(repository.id) for repository in load_catalog(paths.CATALOG).repositories)


def _surface_kind(relative: PurePosixPath) -> str | None:
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
        normalized = substitutes.MANAGER_ALIASES.get(manager, manager)
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


def _manifest_name(token: str) -> str:
    name = _package_name(token)
    bracket = name.find("[")
    if bracket > 0:
        name = name[:bracket]
    return name


def _command_args(text: str, env: dict[str, str]) -> list[str]:
    names: list[str] = []
    for token in text.split():
        bare = token.strip("'\"")
        if bare in _SEPARATORS:
            break
        if bare.startswith("-"):
            continue
        names.extend(_expand(bare, env))
    return names


def _manifest_install_hits(
    line: str, env: dict[str, str], producers: dict[str, ProducerSub]
) -> list[Hit]:
    hits: list[Hit] = []
    specs = (
        (_PIP_INSTALL, "pypi", "pip"),
        (_UV_ADD, "pypi", "uv add"),
        (_UV_PIP_INSTALL, "pypi", "uv pip install"),
        (_CARGO_INSTALL, "cargo", "cargo install"),
    )
    for pattern, ecosystem, label in specs:
        for match in pattern.finditer(line):
            for raw_name in _command_args(line[match.end():], env):
                name = _manifest_name(raw_name)
                if not name:
                    continue
                found = substitutes.manifest_producer(name, ecosystem, producers)
                if found is not None:
                    producer_id, _ = found
                    hits.append(Hit(0, f"package '{name}' installed by {label}", producer_id))
    return hits


def _wrapper_hits(line: str, producers: dict[str, ProducerSub]) -> list[Hit]:
    hits: list[Hit] = []
    for match in _WRAPPER_ASSIGN.finditer(line):
        raw = match.group(1).strip().strip("'\"")
        name = PurePosixPath(raw).name.removesuffix(".exe")
        if not name:
            continue
        found = substitutes.manifest_producer(name, "cargo", producers)
        if found is not None:
            producer_id, _ = found
            hits.append(Hit(0, f"rustc-wrapper '{name}'", producer_id))
    return hits


def _dep_line(text: str, *names: str) -> int:
    for name in names:
        if not name:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(rf"(?<![\w.-]){re.escape(name)}(?![\w.-])", line, re.IGNORECASE):
                return number
    return 1


def _pypi_requirement_name(requirement: object) -> str | None:
    if not isinstance(requirement, str):
        return None
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    return cast(str, match.group(1)) if match else None


def _collect_dependencies(table: object, names: list[str]) -> None:
    if not isinstance(table, dict):
        return
    for key, value in table.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, dict):
            package = value.get("package")
            names.append(package if isinstance(package, str) and package else key)
        else:
            names.append(key)


def _cargo_dependency_names(data: object) -> list[str]:
    names: list[str] = []
    if not isinstance(data, dict):
        return names
    for section in _DEP_SECTIONS:
        _collect_dependencies(data.get(section), names)
    target = data.get("target")
    if isinstance(target, dict):
        for entry in target.values():
            if isinstance(entry, dict):
                for section in _DEP_SECTIONS:
                    _collect_dependencies(entry.get(section), names)
    workspace = data.get("workspace")
    if isinstance(workspace, dict):
        _collect_dependencies(workspace.get("dependencies"), names)
    return names


def _pypi_list_names(value: object, names: list[str]) -> None:
    if not isinstance(value, list):
        return
    for item in value:
        name = _pypi_requirement_name(item)
        if name is not None:
            names.append(name)


def _pyproject_dependency_names(data: object) -> list[str]:
    names: list[str] = []
    if not isinstance(data, dict):
        return names
    project = data.get("project")
    if isinstance(project, dict):
        _pypi_list_names(project.get("dependencies"), names)
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            for value in optional.values():
                _pypi_list_names(value, names)
    groups = data.get("dependency-groups")
    if isinstance(groups, dict):
        for value in groups.values():
            _pypi_list_names(value, names)
    tool = data.get("tool")
    uv = tool.get("uv") if isinstance(tool, dict) else None
    if isinstance(uv, dict):
        _pypi_list_names(uv.get("dev-dependencies"), names)
    return names


def _requirements_dependency_names(text: str) -> list[str]:
    names: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-")):
            continue
        name = _pypi_requirement_name(line)
        if name is not None:
            names.append(name)
    return names


def _npm_dependency_names(data: object) -> list[str]:
    names: list[str] = []
    if not isinstance(data, dict):
        return names
    for key in ("dependencies", "devDependencies", "optionalDependencies"):
        table = data.get(key)
        if isinstance(table, dict):
            names.extend(entry for entry in table if isinstance(entry, str))
    return names


def _manifest_deps(kind: str, filename: str, text: str) -> list[str] | None:
    try:
        if kind == "manifest:cargo":
            return _cargo_dependency_names(tomllib.loads(text))
        if kind == "manifest:npm":
            return _npm_dependency_names(json.loads(text))
        if filename.casefold() == "pyproject.toml":
            return _pyproject_dependency_names(tomllib.loads(text))
        return _requirements_dependency_names(text)
    except ValueError:
        return None


def _manifest_hits(
    kind: str, filename: str, text: str, producers: dict[str, ProducerSub]
) -> list[Hit]:
    ecosystem = kind.split(":", 1)[1]
    deps = _manifest_deps(kind, filename, text)
    if deps is None:
        return []
    hits: list[Hit] = []
    for dep in deps:
        found = substitutes.manifest_producer(dep, ecosystem, producers)
        if found is None:
            continue
        producer_id, matched = found
        hits.append(
            Hit(_dep_line(text, dep, matched), f"dependency '{dep}' ({ecosystem})", producer_id)
        )
    deduped: dict[tuple[str, str], Hit] = {}
    for hit in hits:
        deduped.setdefault((hit.label, hit.producer), hit)
    return sorted(deduped.values(), key=lambda hit: (hit.line, hit.label))


def _cargo_config_hits(text: str, producers: dict[str, ProducerSub]) -> list[Hit]:
    try:
        data = tomllib.loads(text)
    except ValueError:
        return []
    build = data.get("build")
    wrapper = build.get("rustc-wrapper") if isinstance(build, dict) else None
    if not isinstance(wrapper, str) or not wrapper.strip():
        return []
    raw = wrapper.strip().strip("'\"")
    name = PurePosixPath(raw).name.removesuffix(".exe")
    if not name:
        return []
    found = substitutes.manifest_producer(name, "cargo", producers)
    if found is None:
        return []
    producer_id, _ = found
    return [Hit(_dep_line(text, name, raw), f"rustc-wrapper '{name}'", producer_id)]


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
            Hit(number, hit.label, hit.producer)
            for hit in _manifest_install_hits(line, env, producers)
        )
        hits.extend(
            Hit(number, hit.label, hit.producer)
            for hit in _wrapper_hits(line, producers)
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


def _fix_context(root: Path) -> tuple[str, object] | None:
    try:
        entry = owned_python.approved_cpython()
        minor = owned_python.cpython_minor(entry)
        pin = owned_python.buildlib_setup_pin()
    except ValueError:
        return None
    if owned_python.render_lock(root) is None:
        return None
    return minor, pin


def _uv_producer(policy: Policy) -> str:
    for name, sub in policy.producers.items():
        if "astral-sh/setup-uv" in sub.actions:
            return name
    return "laputa-systems/python-build"


def _workflow_files(root: Path) -> list[Path]:
    directory = root / ".github" / "workflows"
    if directory.is_symlink() or not directory.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(directory.iterdir()):
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.casefold() in {".yml", ".yaml"}:
            files.append(path)
    return files


def _fix(root: Path, repository: Repository) -> dict[str, str]:
    try:
        policy = _load_policy()
    except ValueError:
        return {}
    producer = _uv_producer(policy)
    folded = producer.casefold()
    if folded == str(repository.id).casefold() or folded in _exemptions_for(policy, repository):
        return {}
    context = _fix_context(root)
    if context is None:
        return {}
    minor, pin = context
    rendered = owned_python.render_lock(root)
    if rendered is None:
        return {}
    existing, content = rendered
    rewrites: dict[str, str] = {}
    for path in _workflow_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        rewrite = owned_python.rewrite_workflow(text, minor, pin)
        if rewrite is None or rewrite.text == text:
            continue
        rewrites[path.relative_to(root).as_posix()] = rewrite.text
    if not rewrites:
        return {}
    plan: dict[str, str] = dict(rewrites)
    if content != existing:
        plan[owned_python.LOCK_PATH] = content
    return plan


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
    context = _fix_context(root)
    for relative, kind, payload in _surface_files(root):
        if kind == "error":
            findings.append(operational(repository, RULE, relative, payload))
            continue
        if kind.startswith("manifest:"):
            hits = _manifest_hits(kind, PurePosixPath(relative).name, payload, policy.producers)
        elif kind == "cargo-config":
            hits = _cargo_config_hits(payload, policy.producers)
        else:
            hits = _file_hits(kind, payload, policy.producers)
        rewrite = None
        if kind == "workflow" and context is not None:
            rewrite = owned_python.rewrite_workflow(payload, context[0], context[1])
        for hit in hits:
            key = hit.producer.casefold()
            if key == str(repository.id).casefold():
                continue
            canonical = next(
                (name for name in policy.producers if name.casefold() == key),
                hit.producer,
            )
            if key in exemptions:
                suppressed.add(key)
                continue
            remedy = (
                f"depend on {canonical}'s package instead of the upstream one"
                if kind.startswith("manifest:")
                else f"acquire it through {_BUILDLIB_HINT} instead of the upstream install"
            )
            fixable = rewrite is not None and hit.line in (
                rewrite.install_lines | rewrite.setup_lines
            )
            reported.append(violation(
                repository, RULE, relative,
                f"{hit.label} duplicates owned producer {canonical}; {remedy}",
                line=hit.line,
                fixable=fixable,
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
            _fix,
            "fix(owned-tools): acquire python through the buildlib setup action",
            (
                ".github/workflows/*.yml",
                ".github/workflows/*.yaml",
                ".github/tools.lock.json",
            ),
        ),
    )
