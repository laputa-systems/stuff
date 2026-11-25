from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from repomod import (
    fs_index,
    install_parse,
    owned_dockerfile,
    owned_python,
    owned_tools_image,
    paths,
    substitutes,
)
from repomod.catalog import load_catalog_cached
from repomod.owned_tools import load_owned_tools
from repomod.run_cache import cached
from repomod.substitutes import Exemption, Policy, ProducerSub
from repomod.types import Finding, RepoId, Repository, Rule, TagPredicate, operational, violation

RULE = "owned-tool-substitution"
_POLICY = "fleet/policy/owned-substitutes.toml"
_OWNED_POLICY = "fleet/policy/owned-tools.toml"
_IMAGE_POLICY = "fleet/policy/owned-tools-image.toml"
_BUILDLIB_HINT = "buildlib.tools or the laputa-systems/buildlib/setup action"
_PYTHON_VERSION = re.compile(r"^\s*python-version\s*:")
_WITH = re.compile(r"^\s*with\s*:")
_UV_PYTHON = re.compile(r"\buv\s+python\s+install\b")
_PIP_INSTALL = re.compile(r"(?<![\w.])(?<!uv )(?:pip3?|python[\d.]*\s+-m\s+pip)\s+install\b")
_UV_ADD = re.compile(r"\buv\s+add\b")
_UV_PIP_INSTALL = re.compile(r"\buv\s+pip\s+install\b")
_CARGO_INSTALL = re.compile(r"\bcargo\s+install\b")
_WRAPPER_ASSIGN = re.compile(r"\b(?:RUSTC_WRAPPER|rustc-wrapper)\s*[:=]\s*[\"']?([^\s\"']+)")
_COMPILER_SETTING = re.compile(
    r"(?:(?<![\w-])|(?<=-D))"
    r"(CC|CXX|HOSTCC|HOSTCXX|CMAKE_C_COMPILER|CMAKE_CXX_COMPILER)"
    r"[ \t]*(?:[:?+]?=|:[ \t])[ \t]*[\"']?"
    r"((?:[\w.]+-)*(?:gcc|g\+\+)(?:-\d+)?)"
    r"(?=[\"'\s;)]|$)"
)
_COMPILER_PROBE = "gcc"
_DEP_SECTIONS = ("dependencies", "dev-dependencies", "build-dependencies")
_IGNORED_DIRS = install_parse._IGNORED_DIRS
_WORKFLOW_SUFFIXES = install_parse._WORKFLOW_SUFFIXES
_MAKE_NAMES = install_parse._MAKE_NAMES
_SEPARATORS = install_parse._SEPARATORS


@dataclass(frozen=True, slots=True)
class Hit:
    line: int
    label: str
    producer: str
    manager: str | None = None
    package: str | None = None


def _load_policy() -> Policy:
    return cached(("owned-substitutes-policy",), substitutes.load_policy)


def _owned_producers() -> frozenset[str]:
    policy = cached(("owned-tools-policy",), load_owned_tools)
    owned = {str(producer.repo).casefold() for producer in policy.producers}
    owned.update(
        str(repository.id).casefold()
        for repository in load_catalog_cached(paths.CATALOG).repositories
        if policy.owned(repository.id)
    )
    return frozenset(owned)


def _known_repositories() -> frozenset[str]:
    return frozenset(str(repository.id) for repository in load_catalog_cached(paths.CATALOG).repositories)


def _surface_kind(relative: PurePosixPath) -> str | None:
    return install_parse.surface_kind(relative)


def _surface_files(root: Path) -> list[tuple[str, str, str]]:
    files: list[tuple[str, str, str]] = []
    for dirpath, dirnames, filenames in fs_index.walk(root):
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


def _logical_lines(text: str) -> list[tuple[int, str]]:
    return install_parse.logical_lines(text)


def _assignments(text: str) -> dict[str, str]:
    return install_parse.assignments(text)


def _expand(token: str, env: dict[str, str], depth: int = 0) -> list[str]:
    return install_parse.expand(token, env, depth)


def _package_name(token: str) -> str:
    return install_parse.package_name(token)


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
    for manager, name in install_parse.system_package_installs(line, env):
        normalized = substitutes.MANAGER_ALIASES.get(manager, manager)
        producer_id = _package_hits(name, normalized, producers)
        if producer_id is not None:
            hits.append(
                Hit(0, f"package '{name}' installed by {manager}", producer_id,
                    manager=normalized, package=name)
            )
    return hits


def _url_hits(line: str, producers: dict[str, ProducerSub]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for raw, combined in install_parse.download_urls(line):
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
    for lineno, raw_action in install_parse.action_references(text):
        index = lineno - 1
        action = raw_action.rstrip(".")
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


def _compiler_producer(producers: dict[str, ProducerSub]) -> str | None:
    for manager in ("apk", "apt", "dnf", "pacman"):
        producer_id = _package_hits(_COMPILER_PROBE, manager, producers)
        if producer_id is not None:
            return producer_id
    return None


def _compiler_hits(line: str, producers: dict[str, ProducerSub]) -> list[Hit]:
    producer_id = _compiler_producer(producers)
    if producer_id is None:
        return []
    return [
        Hit(0, f"compiler setting '{match.group(1)}={match.group(2)}'", producer_id)
        for match in _COMPILER_SETTING.finditer(line)
    ]


def _cargo_linker_hits(data: dict[str, object], text: str, producers: dict[str, ProducerSub]) -> list[Hit]:
    producer_id = _compiler_producer(producers)
    targets = data.get("target")
    if producer_id is None or not isinstance(targets, dict):
        return []
    hits: list[Hit] = []
    for table in targets.values():
        linker = table.get("linker") if isinstance(table, dict) else None
        if not isinstance(linker, str):
            continue
        name = PurePosixPath(linker.strip()).name
        if re.fullmatch(r"(?:[\w.]+-)*gcc(?:-\d+)?", name):
            hits.append(Hit(_dep_line(text, linker), f"Cargo linker '{name}'", producer_id))
    return hits


def _cargo_config_hits(text: str, producers: dict[str, ProducerSub]) -> list[Hit]:
    try:
        data = tomllib.loads(text)
    except ValueError:
        return []
    linker_hits = _cargo_linker_hits(data, text, producers)
    build = data.get("build")
    wrapper = build.get("rustc-wrapper") if isinstance(build, dict) else None
    if not isinstance(wrapper, str) or not wrapper.strip():
        return linker_hits
    raw = wrapper.strip().strip("'\"")
    name = PurePosixPath(raw).name.removesuffix(".exe")
    if not name:
        return linker_hits
    found = substitutes.manifest_producer(name, "cargo", producers)
    if found is None:
        return linker_hits
    producer_id, _ = found
    return [Hit(_dep_line(text, name, raw), f"rustc-wrapper '{name}'", producer_id), *linker_hits]


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
            Hit(number, hit.label, hit.producer, hit.manager, hit.package)
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
            Hit(number, hit.label, hit.producer)
            for hit in _compiler_hits(line, producers)
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


def _is_dockerfile(relative: PurePosixPath) -> bool:
    lowered = relative.name.casefold()
    return (
        lowered.startswith(("dockerfile", "containerfile"))
        or lowered.endswith(".dockerfile")
    )


def _image_context(
    repository: Repository, policy: Policy
) -> tuple[tuple[str, ...], str, Callable[[str], bool]] | None:
    data = cached(("owned-tools-image",), owned_tools_image.image_policy)
    packages = cached(("owned-tools-image-packages",), owned_tools_image.package_map)
    reference = data.get("reference")
    digest = data.get("digest")
    apk = packages.get("apk") or {}
    if (
        not isinstance(reference, str)
        or not reference.strip()
        or not isinstance(digest, str)
        or not digest.strip()
        or not apk
    ):
        return None
    exemptions = _exemptions_for(policy, repository)

    def keep(name: str) -> bool:
        producer = _package_hits(name, "apk", policy.producers)
        if producer is None:
            return True
        folded = producer.casefold()
        return (
            folded == str(repository.id).casefold() or folded in exemptions
        )

    return tuple(apk), f"{reference.strip()}@{digest.strip()}", keep


def _dockerfile_rewrite(
    text: str, repository: Repository, policy: Policy
) -> owned_dockerfile.Rewrite | None:
    context = _image_context(repository, policy)
    if context is None:
        return None
    entries, image, keep = context
    return owned_dockerfile.rewrite(text, entries, image, keep)


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


def _workflow_fix(root: Path, repository: Repository) -> dict[str, str]:
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


def _dockerfile_fix(root: Path, repository: Repository) -> dict[str, str]:
    try:
        policy = _load_policy()
    except ValueError:
        return {}
    plan: dict[str, str] = {}
    for relative, kind, payload in _surface_files(root):
        if kind != "text" or not _is_dockerfile(PurePosixPath(relative)):
            continue
        try:
            rewrite = _dockerfile_rewrite(payload, repository, policy)
        except ValueError:
            continue
        if rewrite is not None and rewrite.text != payload:
            plan[relative] = rewrite.text
    return plan


def _fix(root: Path, repository: Repository) -> dict[str, str]:
    plan = _workflow_fix(root, repository)
    plan.update(_dockerfile_fix(root, repository))
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
    image_error = False
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
        docker_rewrite = None
        if kind == "workflow" and context is not None:
            rewrite = owned_python.rewrite_workflow(payload, context[0], context[1])
        elif kind == "text" and _is_dockerfile(PurePosixPath(relative)):
            try:
                docker_rewrite = _dockerfile_rewrite(payload, repository, policy)
            except ValueError as error:
                if not image_error:
                    findings.append(
                        operational(repository, RULE, _IMAGE_POLICY, str(error))
                    )
                    image_error = True
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
            if rewrite is not None:
                fixable = hit.line in (
                    rewrite.install_lines | rewrite.setup_lines
                )
            elif docker_rewrite is not None:
                fixable = (
                    hit.manager == "apk"
                    and hit.package is not None
                    and (hit.line, hit.package.casefold()) in docker_rewrite.removed
                )
            else:
                fixable = False
            reported.append(violation(
                repository, RULE, relative,
                f"{hit.label} duplicates owned producer {canonical}; {remedy}",
                line=hit.line,
                fixable=fixable,
            ))
        if docker_rewrite is not None:
            reported.extend(
                violation(
                    repository, RULE, relative,
                    "ENV PATH puts /opt/laputa/bin before the base image's PATH, so the owned-tools "
                    "image shadows packages the stage still installs; append it with "
                    "ENV PATH=$PATH:/opt/laputa/bin",
                    line=line,
                    fixable=True,
                )
                for line in sorted(docker_rewrite.prepended)
            )
            reported.extend(
                violation(
                    repository, RULE, relative,
                    "COPY takes the owned-tools image at a digest fleet policy no longer approves; "
                    "repin it to the digest in fleet/policy/owned-tools-image.toml",
                    line=line,
                    fixable=True,
                )
                for line in sorted(docker_rewrite.stale)
            )
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
                "*Dockerfile*",
                "*dockerfile*",
                "*DOCKERFILE*",
                "*Containerfile*",
                "*containerfile*",
                "*CONTAINERFILE*",
            ),
        ),
    )
