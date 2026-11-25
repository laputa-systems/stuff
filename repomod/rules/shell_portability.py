from __future__ import annotations

import bisect
import fnmatch
import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString, LiteralScalarString

from repomod import fs_index, paths
from repomod.catalog import load_catalog_cached
from repomod.dependencies import commands as commands_module
from repomod.dependencies.commands import CallSite, SurfaceFile
from repomod.run_cache import cached
from repomod.types import Finding, RepoId, Repository, Rule, TagPredicate, operational, violation

RULE = "shell-portability"
_POLICY = "fleet/policy/shell-portability.toml"
_PLATFORM_DIRS = frozenset({"darwin", "macos", "linux", "alpine"})
_PLATFORM_GLOBS = ("*_linux.*", "*_darwin.*", "*_macos.*", "*-linux", "*-macos")
_SHORT_OPTION = re.compile(r"^-[A-Za-z0-9]")
_ALNUM_WORD = re.compile(r"[A-Za-z0-9]+")
_IGNORED_DIRS = frozenset({
    ".git", ".work", "work", "node_modules", "vendor", "dist", "build", "target",
    ".venv", "venv", "__pycache__", ".zig-cache", "zig-cache", "zig-pkg", ".next",
    ".nuxt", "third_party", ".cache", "coverage", ".tox", "eggs", ".direnv",
    "result", "Pods", "DerivedData", ".cargo-home", ".idea", ".vscode",
})


@dataclass(frozen=True, slots=True)
class PortabilityRule:
    commands: frozenset[str]
    arguments: tuple[str, ...]
    options: tuple[str, ...]
    patterns: tuple[re.Pattern[str], ...]
    use: str
    letters: str


@dataclass(frozen=True, slots=True)
class Exemption:
    name: str
    reason: str
    reassess: str
    paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Policy:
    rules: tuple[PortabilityRule, ...]
    exempt: dict[str, Exemption]


def _string_list(value: object, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list of non-empty strings")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return tuple(item.strip() for item in value if isinstance(item, str))


def _load_rule(index: int, raw: object) -> PortabilityRule:
    label = f"rule[{index}]"
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a table")
    unknown = set(raw) - {"commands", "arguments", "options", "patterns", "use", "letters"}
    if unknown:
        raise ValueError(f"{label} has unknown keys: {', '.join(sorted(str(k) for k in unknown))}")
    commands = _string_list(raw.get("commands"), f"{label}.commands")
    if not commands:
        raise ValueError(f"{label}.commands must name at least one command")
    use = raw.get("use")
    if not isinstance(use, str) or not use.strip():
        raise ValueError(f"{label}.use must be a non-empty replacement description")
    patterns: list[re.Pattern[str]] = []
    for item in _string_list(raw.get("patterns"), f"{label}.patterns"):
        try:
            patterns.append(re.compile(item))
        except re.error as error:
            raise ValueError(f"{label}.patterns entry {item!r} is not a valid regex: {error}") from error
    letters = raw.get("letters", "")
    if not isinstance(letters, str):
        raise ValueError(f"{label}.letters must be a string")
    return PortabilityRule(
        frozenset(commands),
        _string_list(raw.get("arguments"), f"{label}.arguments"),
        _string_list(raw.get("options"), f"{label}.options"),
        tuple(patterns),
        use.strip(),
        letters,
    )


def _load_exemptions(raw: object) -> dict[str, Exemption]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("[exempt] must be a table of OWNER/REPO entries")
    entries: dict[str, Exemption] = {}
    for name, value in raw.items():
        if not isinstance(name, str):
            raise ValueError("[exempt] keys must be OWNER/REPO strings")
        try:
            RepoId.parse(name)
        except ValueError as error:
            raise ValueError(f"exempt.{name} is not an OWNER/REPO catalog key") from error
        if not isinstance(value, dict):
            raise ValueError(f"exempt.{name} must be a table with reason and reassess")
        unknown = set(value) - {"reason", "reassess", "paths"}
        if unknown:
            raise ValueError(
                f"exempt.{name} has unknown keys: {', '.join(sorted(str(k) for k in unknown))}"
            )
        reason = value.get("reason")
        reassess = value.get("reassess")
        if (
            not isinstance(reason, str)
            or not reason.strip()
            or not isinstance(reassess, str)
            or not reassess.strip()
        ):
            raise ValueError(f"exempt.{name} needs non-empty reason and reassess strings")
        raw_paths = value.get("paths", [])
        if not isinstance(raw_paths, list) or any(not isinstance(item, str) or not item.strip() for item in raw_paths):
            raise ValueError(f"exempt.{name}.paths must be a list of non-empty glob strings")
        paths = tuple(item.strip() for item in raw_paths if isinstance(item, str))
        entries[name.casefold()] = Exemption(name, reason.strip(), reassess.strip(), paths)
    return entries


def _load_policy() -> Policy:
    target = paths.POLICY / "shell-portability.toml"
    return cached(("shell-portability-policy", target), lambda: _read_policy(target))


def _read_policy(target: Path) -> Policy:
    try:
        data = tomllib.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"cannot load shell-portability policy: {error}") from error
    if not isinstance(data, dict) or set(data) - {"version", "rule", "exempt"} or data.get("version") != 1:
        raise ValueError("shell-portability.toml needs version = 1 and known keys only")
    raw_rules = data.get("rule", [])
    if not isinstance(raw_rules, list) or not raw_rules:
        raise ValueError("shell-portability.toml needs a non-empty [[rule]] list")
    return Policy(
        tuple(_load_rule(index, item) for index, item in enumerate(raw_rules)),
        _load_exemptions(data.get("exempt")),
    )


def _known_repositories() -> frozenset[str]:
    return frozenset(
        str(repository.id) for repository in load_catalog_cached(paths.CATALOG).repositories
    )


def _surface_files(root: Path) -> list[SurfaceFile]:
    files: list[SurfaceFile] = []
    for dirpath, dirnames, filenames in fs_index.walk(root):
        base = Path(dirpath)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in _IGNORED_DIRS and not (base / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = base / filename
            if path.is_symlink() or not path.is_file():
                continue
            relative = PurePosixPath(path.relative_to(root).as_posix())
            if not commands_module.candidate_path(relative.as_posix()):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            item = commands_module.surface_file(relative.as_posix(), text)
            if item is not None:
                files.append(item)
    return files


def _scan_words(words: Sequence[str]) -> Sequence[str]:
    for index, word in enumerate(words):
        if word == "--":
            return words[:index]
    return words


def _option_hit(words: Sequence[str], spec: str, letters: str = "") -> bool:
    if " " in spec:
        parts = tuple(spec.split(" "))
        size = len(parts)
        return any(
            tuple(words[index : index + size]) == parts
            for index in range(len(words) - size + 1)
        )
    if spec.startswith("--"):
        return any(word == spec or word.startswith(spec + "=") for word in words)
    if len(spec) == 2:
        option = spec[1]
        allowed = frozenset(letters)
        for word in words:
            if not _SHORT_OPTION.match(word) or word.startswith("--"):
                continue
            body = word[1:]
            if not body:
                continue
            if _ALNUM_WORD.fullmatch(body):
                if allowed and not allowed.issuperset(body):
                    continue
                if option in body:
                    return True
            elif body.startswith(option):
                return True
        return False
    return spec in words


def _rule_hits(rule: PortabilityRule, words: Sequence[str]) -> list[str]:
    scan = _scan_words(words)
    hits: list[str] = []
    if not (rule.arguments or rule.options or rule.patterns):
        hits.append("")
    if rule.arguments and list(scan[: len(rule.arguments)]) == list(rule.arguments):
        hits.append(" ".join(rule.arguments))
    hits.extend(
        spec for spec in rule.options if _option_hit(scan, spec, rule.letters)
    )
    for pattern in rule.patterns:
        for word in scan:
            if pattern.search(word):
                hits.append(f"argument {word!r}")
                break
    return hits


def _platform_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if any(part in _PLATFORM_DIRS for part in parts[:-1]):
        return True
    name = parts[-1]
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in _PLATFORM_GLOBS)


def _os_family(label: str) -> str | None:
    lowered = label.casefold()
    if "macos" in lowered or "xcode" in lowered or "mac-os" in lowered:
        return "macos"
    if "windows" in lowered or "win-" in lowered:
        return "windows"
    if "alpine" in lowered:
        return "alpine"
    if any(
        token in lowered
        for token in (
            "ubuntu", "debian", "linux", "fedora", "centos", "rocky",
            "almalinux", "amzn", "amazon", "suse", "opensuse",
        )
    ):
        return "linux"
    return None


def _single_os(value: object) -> bool:
    if isinstance(value, str):
        return "${{" not in value and _os_family(value) is not None
    if isinstance(value, (list, tuple)):
        families: set[str] = set()
        for item in value:
            if not isinstance(item, str) or "${{" in item:
                return False
            family = _os_family(item)
            if family is None:
                return False
            families.add(family)
        return len(families) == 1
    return False


def _run_first_line(node: object, key: object, value: object) -> int | None:
    data = getattr(getattr(node, "lc", None), "data", None)
    entry = data.get(key) if isinstance(data, dict) else None
    if not (
        isinstance(entry, list)
        and len(entry) >= 4
        and all(type(item) is int for item in entry[:4])
    ):
        return None
    key_line = int(entry[0])
    _key_column = entry[1]
    value_line = int(entry[2])
    _value_column = entry[3]
    if isinstance(value, (LiteralScalarString, FoldedScalarString)):
        return key_line + 2
    if value_line > key_line:
        return value_line + 1
    return key_line + 1


def _collect_run_lines(node: object, out: list[int]) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key == "run" and isinstance(value, str):
                line = _run_first_line(node, key, value)
                if line is not None:
                    out.append(line)
            else:
                _collect_run_lines(value, out)
    elif isinstance(node, list):
        for item in node:
            _collect_run_lines(item, out)


def _workflow_os_map(text: str) -> dict[int, bool]:
    try:
        document = YAML(typ="rt").load(text)
    except (YAMLError, AttributeError, ValueError, RecursionError):
        return {}
    exempt: dict[int, bool] = {}
    jobs = document.get("jobs") if isinstance(document, Mapping) else None
    if isinstance(jobs, Mapping):
        for job in jobs.values():
            if not isinstance(job, Mapping):
                continue
            lines: list[int] = []
            _collect_run_lines(job, lines)
            for line in lines:
                exempt[line] = _single_os(job.get("runs-on"))
    all_lines: list[int] = []
    _collect_run_lines(document, all_lines)
    return {line: exempt.get(line, False) for line in all_lines}


def _site_exempt(
    site: CallSite,
    kinds: Mapping[str, str],
    texts: Mapping[str, str],
    cache: dict[str, dict[int, bool]],
) -> bool:
    kind = kinds.get(site.path)
    if kind == commands_module.KIND_DOCKERFILE:
        return True
    if _platform_path(site.path):
        return True
    if kind == commands_module.KIND_WORKFLOW:
        mapping = cache.get(site.path)
        if mapping is None:
            mapping = _workflow_os_map(texts.get(site.path, ""))
            cache[site.path] = mapping
        keys = sorted(mapping)
        index = bisect.bisect_right(keys, site.line) - 1
        if index >= 0:
            return mapping[keys[index]]
    return False


def _evaluate(
    repository: Repository,
    policy: Policy,
    files: Sequence[SurfaceFile],
    sites: Sequence[CallSite],
) -> list[Finding]:
    kinds = {item.path: item.kind for item in files}
    texts = {item.path: item.text for item in files}
    cache: dict[str, dict[int, bool]] = {}
    findings: list[Finding] = []
    for site in sites:
        if _site_exempt(site, kinds, texts, cache):
            continue
        for rule in policy.rules:
            if site.name not in rule.commands:
                continue
            for hit in _rule_hits(rule, site.arguments):
                label = site.name if not hit else f"{site.name} {hit}"
                findings.append(
                    violation(
                        repository,
                        RULE,
                        site.path,
                        f"{label} is not portable in shared shell; {rule.use}",
                        line=site.line,
                    )
                )
    return sorted(
        findings,
        key=lambda finding: (finding.file or "", finding.line or 0, finding.message),
    )


def _exemption_for(policy: Policy, repository: Repository) -> Exemption | None:
    return policy.exempt.get(str(repository.id).casefold())


def _exempt_key_findings(
    repository: Repository, policy: Policy, known: frozenset[str]
) -> list[Finding]:
    if known and str(repository.id) != min(known, key=str.casefold):
        return []
    return [
        violation(
            repository,
            RULE,
            _POLICY,
            f"exempt.{item.name} is not an active catalog repository",
        )
        for item in policy.exempt.values()
        if str(RepoId.parse(item.name)) not in known
    ]


def _check(root: Path, repository: Repository) -> list[Finding]:
    try:
        policy = _load_policy()
    except ValueError as error:
        return [operational(repository, RULE, _POLICY, str(error))]
    findings: list[Finding] = []
    if policy.exempt:
        try:
            known = _known_repositories()
        except ValueError as error:
            return [operational(repository, RULE, _POLICY, str(error))]
        findings.extend(_exempt_key_findings(repository, policy, known))
    files = _surface_files(root)
    try:
        sites = commands_module.call_sites(files)
    except (commands_module.CommandToolError, ValueError) as error:
        return [*findings, operational(repository, RULE, None, str(error))]
    reported = _evaluate(repository, policy, files, sites)
    exempt = _exemption_for(policy, repository)
    if exempt is not None and exempt.paths:
        covered = [
            item for item in reported
            if any(fnmatch.fnmatchcase(item.file or "", pattern) for pattern in exempt.paths)
        ]
        remaining = [item for item in reported if item not in covered]
        if covered:
            return [*findings, *remaining]
        return [
            *findings,
            *remaining,
            violation(
                repository,
                RULE,
                _POLICY,
                f"stale exemption for {exempt.name}: its paths match no shell-portability "
                f"finding in this repository ({exempt.reason}); remove it",
            ),
        ]
    if exempt is not None:
        if reported:
            return findings
        return [
            *findings,
            violation(
                repository,
                RULE,
                _POLICY,
                f"stale exemption for {exempt.name}: it matches no shell-portability "
                f"finding in this repository ({exempt.reason}); remove it or restore "
                "the portable spelling it was granted for",
            ),
        ]
    return [*findings, *reported]


def shell_portability_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            RULE,
            "Require portable shell commands and options on macOS, glibc, and Alpine",
            TagPredicate(),
            _check,
            None,
            None,
            (),
        ),
    )
