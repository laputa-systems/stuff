from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from repomod import paths
from repomod.catalog import PRIMARY_TAGS, CatalogError, repository_path
from repomod.git import (
    GitError,
    expected_origin,
    head,
    is_git_checkout,
    matches_head,
    origin_url,
    tracked_paths,
    work_tree_root,
)
from repomod.types import Catalog, RepoId, Repository

RULE_ID = "owned-tool-support"
_KEYS = frozenset({"version", "maintainer", "procedure", "owners", "install_manifest", "producers", "not_applicable"})
_PRODUCER_KEYS = frozenset({"upstream", "sources", "commands", "installer", "bin"})
_COMMAND_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]*\Z")
_REPO_CONSTANT = re.compile(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)\Z")
_GITHUB_REPO = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
_COMMAND_KEYS = frozenset({"help", "gap", "exempt", "record", "launcher_dir", "installed_from"})
type SupportStatus = Literal["help", "gap", "exempt"]
_SUPPORT: dict[str, SupportStatus] = {"help": "help", "gap": "gap", "exempt": "exempt"}
_EXECUTABLE_TAGS = PRIMARY_TAGS - {"library", "data"}


@dataclass(frozen=True, slots=True)
class HelpIntegration:
    source: str
    test: str


@dataclass(frozen=True, slots=True)
class Command:
    name: str
    support: HelpIntegration | str
    status: SupportStatus
    record: str | None = None
    launcher_dir: str = ".local/bin"
    installed_from: RepoId | None = None


@dataclass(frozen=True, slots=True)
class Producer:
    repo: RepoId
    commands: tuple[Command, ...]
    upstream: RepoId | None = None
    sources: tuple[RepoId, ...] = ()
    installer: str | None = None
    bin: tuple[str, ...] = ()

    @property
    def url(self) -> str:
        return github_url(self.repo)


@dataclass(frozen=True, slots=True)
class OwnedTools:
    maintainer: str
    procedure: str
    owners: frozenset[str]
    install_manifest: str
    producers: tuple[Producer, ...]
    not_applicable: Mapping[RepoId, str]

    def footer(self, repo: RepoId) -> str:
        return f"Maintained by {self.maintainer}: {github_url(repo)}"

    def producer(self, repo: RepoId) -> Producer | None:
        key = str(repo).casefold()
        return next((value for value in self.producers if str(value.repo).casefold() == key), None)

    def exemption(self, repo: RepoId) -> str | None:
        key = str(repo).casefold()
        return next((reason for value, reason in self.not_applicable.items() if str(value).casefold() == key), None)

    def owned(self, repo: RepoId) -> bool:
        return repo.owner.casefold() in self.owners


def github_url(repo: RepoId) -> str:
    return f"https://github.com/{repo}"


def policy_file() -> Path:
    return paths.POLICY / "owned-tools.toml"


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value:
        raise ValueError(f"owned-tools.toml {label} must be a nonempty single-line string")
    return value


def _repo(value: object, label: str) -> RepoId:
    try:
        return RepoId.parse(_text(value, label))
    except ValueError as error:
        raise ValueError(f"owned-tools.toml {label}: {error}") from error


def _relative(value: object, label: str) -> str:
    text = _text(value, label)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts or text != path.as_posix():
        raise ValueError(f"owned-tools.toml {label} must be a normalized repository-relative path")
    return text


def _command(repo: RepoId, name: str, raw: Any) -> Command:
    label = f"producers.{repo}.commands.{name}"
    if not _COMMAND_NAME.fullmatch(name):
        raise ValueError(f"owned-tools.toml {label} is not a valid command name")
    if not isinstance(raw, dict) or set(raw) - _COMMAND_KEYS:
        raise ValueError(f"owned-tools.toml {label} accepts only " + ", ".join(sorted(_COMMAND_KEYS)))
    chosen = [key for key in _SUPPORT if key in raw]
    if len(chosen) != 1:
        raise ValueError(f"owned-tools.toml {label} must declare exactly one of help, gap, or exempt")
    status = _SUPPORT[chosen[0]]
    record = None if "record" not in raw else _relative(raw["record"], f"{label}.record")
    launcher_dir = _relative(raw.get("launcher_dir", ".local/bin"), f"{label}.launcher_dir")
    installed_from = None if "installed_from" not in raw else _repo(raw["installed_from"], f"{label}.installed_from")
    if status == "help":
        value = raw["help"]
        if not isinstance(value, dict) or set(value) != {"source", "test"}:
            raise ValueError(f"owned-tools.toml {label}.help must contain exactly source and test")
        support: HelpIntegration | str = HelpIntegration(
            _relative(value["source"], f"{label}.help.source"),
            _relative(value["test"], f"{label}.help.test"),
        )
    else:
        support = _text(raw[status], f"{label}.{status}")
    return Command(name, support, status, record, launcher_dir, installed_from)


def load_owned_tools(path: Path | None = None) -> OwnedTools:
    target = policy_file() if path is None else path
    if target.is_symlink():
        raise ValueError(f"owned-tools policy is a symlink: {target}")
    try:
        parsed: dict[str, Any] = tomllib.loads(target.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"cannot read owned-tools policy at {target}: {error}") from error
    if set(parsed) != _KEYS:
        raise ValueError("owned-tools.toml must contain exactly " + ", ".join(sorted(_KEYS)))
    if parsed["version"] != 1:
        raise ValueError("owned-tools.toml version must be 1")
    owners = parsed["owners"]
    if not isinstance(owners, list) or not owners or not all(isinstance(value, str) for value in owners):
        raise ValueError("owned-tools.toml owners must be a nonempty list of strings")
    owner_set = frozenset(value.casefold() for value in owners)
    raw_producers = parsed["producers"]
    if not isinstance(raw_producers, dict):
        raise ValueError("owned-tools.toml [producers] must be a table")
    producers = []
    for key in sorted(map(str, raw_producers)):
        repo = _repo(key, f"producer {key!r}")
        if repo.owner.casefold() not in owner_set:
            raise ValueError(f"owned-tools.toml producer {repo} is outside the owned namespaces")
        raw = raw_producers[key]
        if not isinstance(raw, dict) or set(raw) - _PRODUCER_KEYS or "commands" not in raw:
            raise ValueError(
                f"owned-tools.toml producers.{repo} needs commands and accepts only "
                + ", ".join(sorted(_PRODUCER_KEYS))
            )
        raw_commands = raw["commands"]
        if not isinstance(raw_commands, dict) or not raw_commands:
            raise ValueError(f"owned-tools.toml producers.{repo}.commands must be a nonempty table")
        raw_sources = raw.get("sources", [])
        if not isinstance(raw_sources, list):
            raise ValueError(f"owned-tools.toml producers.{repo}.sources must be a list")
        raw_bin = raw.get("bin", [])
        if not isinstance(raw_bin, list):
            raise ValueError(f"owned-tools.toml producers.{repo}.bin must be a list")
        producers.append(
            Producer(
                repo,
                tuple(_command(repo, name, raw_commands[name]) for name in sorted(map(str, raw_commands))),
                None if "upstream" not in raw else _repo(raw["upstream"], f"producers.{repo}.upstream"),
                tuple(_repo(value, f"producers.{repo}.sources") for value in raw_sources),
                None if "installer" not in raw else _relative(raw["installer"], f"producers.{repo}.installer"),
                tuple(_relative(value, f"producers.{repo}.bin") for value in raw_bin),
            )
        )
    raw_exempt = parsed["not_applicable"]
    if not isinstance(raw_exempt, dict):
        raise ValueError("owned-tools.toml [not_applicable] must be a table")
    exempt = {
        _repo(key, f"not_applicable {key!r}"): _text(value, f"not_applicable.{key}")
        for key, value in raw_exempt.items()
    }
    overlap = {str(producer.repo) for producer in producers} & {str(repo) for repo in exempt}
    if overlap:
        raise ValueError("owned-tools.toml lists producers as not applicable: " + ", ".join(sorted(overlap)))
    return OwnedTools(
        _text(parsed["maintainer"], "maintainer"),
        _text(parsed["procedure"], "procedure"),
        owner_set,
        _relative(parsed["install_manifest"], "install_manifest"),
        tuple(producers),
        exempt,
    )


def needs_coverage(repository: Repository) -> bool:
    return bool(set(repository.tags) & _EXECUTABLE_TAGS)


def installer_repositories(source: str, owners: Iterable[str]) -> tuple[RepoId, ...]:
    owner_set = {value.casefold() for value in owners}
    found: set[RepoId] = set()

    def add(owner: str, name: str) -> None:
        if owner.casefold() in owner_set:
            found.add(RepoId(owner, name.removesuffix(".git")))

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            whole = _REPO_CONSTANT.fullmatch(node.value)
            if whole is not None:
                add(whole.group(1), whole.group(2))
            for match in _GITHUB_REPO.finditer(node.value):
                add(match.group(1), match.group(2))
        if isinstance(node, ast.FunctionDef):
            names: dict[str, str] = {}
            renames: dict[str, str] = {}
            for inner in ast.walk(node):
                if isinstance(inner, ast.DictComp) and isinstance(inner.value, ast.Constant):
                    owner = inner.value.value
                    iterable = inner.generators[0].iter
                    if isinstance(owner, str) and isinstance(iterable, ast.Tuple):
                        names.update(
                            (element.value, owner)
                            for element in iterable.elts
                            if isinstance(element, ast.Constant) and isinstance(element.value, str)
                        )
                if isinstance(inner, ast.Dict):
                    for key, value in zip(inner.keys, inner.values, strict=True):
                        if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                            continue
                        if not (isinstance(value, ast.Constant) and isinstance(value.value, str)):
                            continue
                        target = names if value.value.casefold() in owner_set else renames
                        target[key.value] = value.value
            for name, owner in names.items():
                add(owner, renames.get(name, name))
    return tuple(sorted(found))


def tracked_commands(root: Path, directories: Iterable[str]) -> tuple[str, ...]:
    commands = set()
    for directory in directories:
        base = root / directory
        if not base.is_dir() or base.is_symlink():
            continue
        for entry in base.iterdir():
            if entry.is_file() and not entry.is_symlink() and os.access(entry, os.X_OK):
                commands.add(entry.name)
    return tuple(sorted(commands))


CoverageState = Literal["implemented", "gap", "not-applicable", "missing", "error"]


@dataclass(frozen=True, slots=True)
class CoverageEntry:
    repository: str
    state: CoverageState
    detail: str
    commands: tuple[str, ...] = ()


def _catalog_entries(catalog: Catalog) -> dict[str, tuple[Repository, bool]]:
    values = {str(repo.id).casefold(): (repo, True) for repo in catalog.repositories}
    values.update({str(repo.id).casefold(): (repo, False) for repo in catalog.ignored})
    return values


def coverage(catalog: Catalog, policy: OwnedTools, installed: Iterable[RepoId] = ()) -> tuple[CoverageEntry, ...]:
    entries: list[CoverageEntry] = []

    def add(repo: object, state: CoverageState, detail: str, commands: tuple[str, ...] = ()) -> None:
        entries.append(CoverageEntry(str(repo), state, detail, commands))

    catalogued = _catalog_entries(catalog)
    installed_keys = {str(repo).casefold() for repo in installed}
    blanket = {str(repo.id).casefold() for repo in catalog.repositories if RULE_ID in repo.ignored_rules}
    owners: dict[str, list[str]] = {}
    for producer in policy.producers:
        for command in producer.commands:
            owners.setdefault(command.name, []).append(str(producer.repo))
    handled: set[str] = set()
    for producer in policy.producers:
        key = str(producer.repo).casefold()
        handled.add(key)
        names = tuple(command.name for command in producer.commands)
        duplicates = sorted(name for name in names if len(owners[name]) > 1)
        gaps = [f"{command.name}: {command.support}" for command in producer.commands if command.status == "gap"]
        if key not in catalogued:
            add(producer.repo, "error", "producer is not in fleet/catalog.toml", names)
        elif duplicates:
            add(producer.repo, "error", "ambiguous commands: " + ", ".join(duplicates), names)
        elif key in blanket:
            add(producer.repo, "error", f"catalog override ignores {RULE_ID}", names)
        elif gaps:
            add(producer.repo, "gap", "; ".join(gaps), names)
        else:
            helped = [command.name for command in producer.commands if command.status == "help"]
            exempt = [command.name for command in producer.commands if command.status == "exempt"]
            detail = "help declared for " + (", ".join(helped) or "no commands")
            if exempt:
                detail += "; exempt: " + ", ".join(exempt)
            add(producer.repo, "implemented", detail + " (static; built help is proven by the tool's tests)", names)
    for repo, reason in sorted(policy.not_applicable.items()):
        key = str(repo).casefold()
        handled.add(key)
        if key not in catalogued:
            add(repo, "error", "not-applicable entry is not in fleet/catalog.toml")
        elif key in installed_keys:
            add(repo, "error", "usr installs it, so it cannot be not applicable")
        else:
            add(repo, "not-applicable", reason)
    for key, (repo, managed) in sorted(catalogued.items()):
        if key in handled or not policy.owned(repo.id):
            continue
        if key in installed_keys:
            add(repo.id, "missing", "usr installs it but owned-tools.toml has no producer entry")
        elif not managed:
            add(repo.id, "not-applicable", "ignored in the catalog and not installed by usr")
        elif not needs_coverage(repo):
            add(repo.id, "not-applicable", "library without an executable")
        else:
            add(repo.id, "missing", "declare its commands or a not_applicable reason")
    entries.extend(
        CoverageEntry(str(repo), "missing", "usr installs it but it is not in fleet/catalog.toml")
        for repo in sorted(installed)
        if str(repo).casefold() not in catalogued and str(repo).casefold() not in handled
    )
    return tuple(sorted(entries, key=lambda entry: entry.repository.casefold()))


def usr_installed(catalog: Catalog, policy: OwnedTools) -> tuple[tuple[RepoId, ...], str | None]:
    for producer in policy.producers:
        if producer.installer is None:
            continue
        entry = _catalog_entries(catalog).get(str(producer.repo).casefold())
        if entry is None:
            return (), f"{producer.repo} is not catalogued"
        try:
            source = (repository_path(catalog, entry[0]) / producer.installer).read_text(encoding="utf-8")
        except (OSError, UnicodeError, CatalogError) as error:
            return (), f"cannot read {producer.repo} installer: {error}"
        return installer_repositories(source, policy.owners), None
    return (), None


ExecutableState = Literal["verified", "upstream-install", "unverified", "shadowed", "not-installed"]
CheckoutState = Literal["present", "missing", "origin-mismatch", "uncatalogued"]
_RELEASE_TAG = re.compile(r"release-[0-9a-f]{40}")
_RECORDED_RELEASE = re.compile(r"(?:^|:)(release-[0-9a-f]{40})(?::|$)")
_DIGEST_LINE = re.compile(r"([0-9a-f]{64})  (\S+)")


@dataclass(frozen=True, slots=True)
class Evidence:
    """What associates an executable with its producer, and the revision that association proves."""

    kind: Literal["source-link", "installer-manifest", "install-record"] | None
    detail: str
    revision: str | None = None
    revision_source: str | None = None
    work_tree: Path | None = None


def _which_all(command: str, path_value: str) -> list[Path]:
    found = []
    for directory in path_value.split(os.pathsep):
        if not directory:
            continue
        candidate = Path(directory) / command
        if candidate.is_file() and os.access(candidate, os.X_OK) and candidate not in found:
            found.append(candidate)
    return found


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def manifest_fingerprint(path: Path, kind: str) -> str | None:
    """Mirror usr's ownership fingerprint (tools/sync/ownership.py, manifest schema 1)."""
    if not path.is_symlink() and not path.exists():
        return None
    if kind == "D" and (not path.is_dir() or path.is_symlink()):
        return None
    if kind in ("F", "K") and path.is_dir() and not path.is_symlink():
        return None
    digest = hashlib.sha256()

    def visit(item: Path, label: str) -> None:
        info = item.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISLNK(info.st_mode):
            digest.update(f"L {label} {mode:o} {os.readlink(item)}\n".encode())
        elif stat.S_ISREG(info.st_mode):
            digest.update(f"F {label} {mode:o} {info.st_size}\n".encode())
            with item.open("rb") as stream:
                for part in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(part)
        elif stat.S_ISDIR(info.st_mode):
            digest.update(f"D {label} {mode:o}\n".encode())
            for child in sorted(item.iterdir(), key=lambda value: value.name):
                visit(child, label + "/" + child.name)
        else:
            raise ValueError(f"unverifiable special file: {item}")

    visit(path, ".")
    return digest.hexdigest()


def _read_manifest(path: Path) -> dict[str, dict[str, str]] | str:
    if path.is_symlink():
        return f"install manifest {path} is a symlink"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return f"no install manifest at {path}"
    except (OSError, UnicodeError, ValueError) as error:
        return f"cannot read install manifest {path}: {error}"
    entries = value.get("entries") if isinstance(value, dict) else None
    if not isinstance(value, dict) or value.get("schema") != 1 or not isinstance(entries, dict):
        return f"install manifest {path} is not schema 1"
    if any(
        not isinstance(entry, dict) or set(entry) != {"kind", "fingerprint"} or not all(
            isinstance(item, str) for item in entry.values()
        )
        for entry in entries.values()
    ):
        return f"install manifest {path} has invalid entries"
    return {
        str(key): {"kind": str(entry["kind"]), "fingerprint": str(entry["fingerprint"])}
        for key, entry in entries.items()
    }


def _matches_entry(entries: Mapping[str, Mapping[str, str]], path: Path) -> bool | None:
    entry = entries.get(str(path))
    if entry is None:
        return None
    try:
        return manifest_fingerprint(path, entry["kind"]) == entry["fingerprint"]
    except (OSError, ValueError):
        return False


def _source_link(launcher: Path, resolved: Path, repo: RepoId) -> Evidence | None:
    if not launcher.is_symlink() or not resolved.is_file():
        return None
    try:
        root = work_tree_root(resolved.parent)
        if root is None:
            return None
        root = root.resolve()
        origin = origin_url(root)
        if origin is None or not expected_origin(repo, origin):
            return None
        relative = resolved.relative_to(root).as_posix()
        if tracked_paths(root, (relative,)) != (relative,):
            return Evidence(None, f"{resolved} is not tracked in {root}")
        if matches_head(root, relative):
            return Evidence("source-link", f"tracked {relative} in {root}", head(root), "work-tree-head", root)
        return Evidence("source-link", f"tracked {relative} in {root} differs from HEAD", work_tree=root)
    except (GitError, ValueError):
        return None


def _install_record(path: Path, command: str, resolved: Path) -> Evidence:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return Evidence(None, f"no install record at {path}")
    digests = {
        match.group(2): match.group(1)
        for line in lines[1:]
        if (match := _DIGEST_LINE.fullmatch(line))
    }
    if command not in digests:
        return Evidence(None, f"install record {path} lists no sha256 for {command}")
    try:
        actual = _sha256(resolved)
    except OSError as error:
        return Evidence(None, f"cannot read {resolved}: {error}")
    if actual != digests[command]:
        return Evidence(None, f"{resolved} does not match the sha256 in {path}")
    revision = lines[0] if lines and _RELEASE_TAG.fullmatch(lines[0]) else None
    source = None if revision is None else "install-record"
    return Evidence("install-record", f"sha256 matches {path}", revision, source)


def _installer_manifest(manifest: Path, launcher: Path, resolved: Path, record: Path) -> Evidence:
    entries = _read_manifest(manifest)
    if isinstance(entries, str):
        return Evidence(None, entries)
    launcher_match = _matches_entry(entries, launcher)
    if launcher_match is None:
        return Evidence(None, f"{launcher} is not in the install manifest")
    if not launcher_match:
        return Evidence(None, f"{launcher} changed since it was installed")
    if resolved != launcher:
        covering = {
            Path(key): Path(key).parent.resolve() / Path(key).name for key in entries if Path(key) != launcher
        }
        owners = [key for key, real in covering.items() if real == resolved or real in resolved.parents]
        if not owners:
            return Evidence(None, f"{resolved} is not covered by the install manifest")
        owner = max(owners, key=lambda value: len(covering[value].parts))
        if _matches_entry(entries, owner) is not True:
            return Evidence(None, f"{owner} changed since it was installed")
    try:
        match = _RECORDED_RELEASE.search(record.read_text(encoding="utf-8").strip())
    except (OSError, UnicodeError):
        match = None
    revision = None if match is None else match.group(1)
    return Evidence(
        "installer-manifest",
        f"fingerprint matches {manifest}",
        revision,
        None if revision is None else "install-record",
    )


def which(
    command: str,
    catalog: Catalog,
    policy: OwnedTools,
    environ: Mapping[str, str],
) -> dict[str, Any]:
    matches = [
        (producer, entry)
        for producer in policy.producers
        for entry in producer.commands
        if entry.name == command
    ]
    if not matches:
        return {"command": command, "status": "unknown", "detail": "no owned producer declares this command"}
    if len(matches) > 1:
        return {
            "command": command,
            "status": "ambiguous",
            "producers": sorted(str(producer.repo) for producer, _ in matches),
        }
    producer, entry = matches[0]
    result: dict[str, Any] = {
        "command": command,
        "repository": str(producer.repo),
        "url": producer.url,
        "upstream": None if producer.upstream is None else str(producer.upstream),
        "sources": [str(source) for source in producer.sources],
        "backlog": f"{producer.url}/blob/HEAD/TODO.md",
        "agents": f"{producer.url}/blob/HEAD/AGENTS.md",
        "procedure": policy.procedure,
        "help": entry.status,
    }
    catalogued = _catalog_entries(catalog).get(str(producer.repo).casefold())
    checkout: dict[str, Any]
    checkout_state: CheckoutState
    if catalogued is None:
        checkout_state = "uncatalogued"
        checkout = {"state": checkout_state, "path": None}
    else:
        path = repository_path(catalog, catalogued[0])
        if not is_git_checkout(path):
            checkout_state = "missing"
            checkout = {"state": checkout_state, "path": str(path)}
        else:
            origin = origin_url(path)
            matches = origin is not None and expected_origin(producer.repo, origin)
            checkout_state = "present" if matches else "origin-mismatch"
            checkout = {"state": checkout_state, "path": str(path), "origin": origin}
    result["checkout"] = checkout
    home = Path(environ.get("HOME", "~")).expanduser()
    managed_bin = home / entry.launcher_dir
    found = _which_all(command, environ.get("PATH", ""))
    executable: dict[str, Any]
    executable_state: ExecutableState
    if not found:
        executable_state = "not-installed"
        executable = {"state": executable_state}
    else:
        first = found[0]
        resolved = first.resolve()
        managed = [candidate for candidate in found if candidate.parent == managed_bin]
        evidence: Evidence | None = None
        if first.parent != managed_bin:
            executable_state = "shadowed" if managed else "unverified"
            if not managed:
                evidence = Evidence(None, f"{first} is outside the managed {managed_bin}")
        else:
            if entry.record is not None:
                evidence = _install_record(home / entry.record, command, resolved)
            else:
                evidence = _source_link(first, resolved, producer.repo)
                if evidence is None:
                    state_home = Path(environ.get("XDG_STATE_HOME") or home / ".local/state")
                    evidence = _installer_manifest(
                        home / policy.install_manifest, first, resolved, state_home / "dl" / command
                    )
            if evidence.kind is None:
                executable_state = "unverified"
            else:
                executable_state = "upstream-install" if entry.installed_from is not None else "verified"
        executable = {
            "state": executable_state,
            "path": str(first),
            "resolved": str(resolved),
            "candidates": [str(candidate) for candidate in found],
            "evidence": None if evidence is None else evidence.kind,
            "detail": None if evidence is None else evidence.detail,
            "work_tree": None if evidence is None or evidence.work_tree is None else str(evidence.work_tree),
            "revision": None if evidence is None else evidence.revision,
            "revision_source": None if evidence is None else evidence.revision_source,
            "installed_from": None if entry.installed_from is None else str(entry.installed_from),
        }
    result["executable"] = executable
    if checkout_state in {"origin-mismatch", "missing", "uncatalogued"}:
        result["status"] = {"missing": "missing-checkout"}.get(checkout_state, checkout_state)
    elif executable_state != "verified":
        result["status"] = executable_state
    else:
        result["status"] = "owned"
    return result


def coverage_json(entries: Iterable[CoverageEntry]) -> str:
    return json.dumps(
        [
            {
                "repository": entry.repository,
                "state": entry.state,
                "detail": entry.detail,
                "commands": list(entry.commands),
            }
            for entry in entries
        ],
        indent=2,
    )
