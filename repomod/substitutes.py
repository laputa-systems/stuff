from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

from repomod import paths
from repomod.types import RepoId

MANAGER_ALIASES = {"apt-get": "apt", "yum": "dnf"}
_MANAGERS = frozenset({"apk", "apt", "apt-get", "brew", "dnf", "yum", "pacman"})
_MANIFEST_ECOSYSTEMS = frozenset({"cargo", "npm", "pypi"})
_ACTION_REF = re.compile(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@[^/\s]+$")
_LABEL_STOPWORDS = frozenset({"a", "and", "an", "for", "of", "or", "the"})
GENERATED_BEGIN = "<!-- generated: owned-substitutes -->"
GENERATED_END = "<!-- end generated -->"
DOCS = paths.ROOT / "docs" / "fleet.md"


@dataclass(frozen=True, slots=True)
class ProducerSub:
    packages: dict[str, tuple[str, ...]]
    actions: frozenset[str]
    urls: tuple[str, ...]
    manifests: dict[str, tuple[str, ...]]
    label: str


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
class SubstituteMatch:
    producer: str
    kind: str
    matched: str


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
    unknown = set(raw) - {"label", "packages", "actions", "urls", "manifests"}
    if unknown:
        raise ValueError(f"{label} has unknown keys: {', '.join(sorted(str(k) for k in unknown))}")
    display = raw.get("label")
    if not isinstance(display, str) or not display.strip():
        raise ValueError(f"{label}.label must be a non-empty string")
    display = display.strip()
    if any(character in display for character in "\r\n|"):
        raise ValueError(f"{label}.label must be a single-line table label")
    raw_packages = raw.get("packages", {})
    if not isinstance(raw_packages, dict):
        raise ValueError(f"{label}.packages must be a table of manager package lists")
    packages: dict[str, tuple[str, ...]] = {}
    for manager, items in raw_packages.items():
        if not isinstance(manager, str) or manager not in _MANAGERS:
            raise ValueError(f"{label}.packages names an unknown manager {manager!r}")
        normalized = MANAGER_ALIASES.get(manager, manager)
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
    raw_manifests = raw.get("manifests", {})
    if not isinstance(raw_manifests, dict):
        raise ValueError(f"{label}.manifests must be a table of ecosystem package lists")
    manifests: dict[str, tuple[str, ...]] = {}
    for ecosystem, items in raw_manifests.items():
        if not isinstance(ecosystem, str) or ecosystem not in _MANIFEST_ECOSYSTEMS:
            raise ValueError(f"{label}.manifests names an unknown ecosystem {ecosystem!r}")
        names = _string_list(items, f"{label}.manifests.{ecosystem}")
        for name in names:
            if any(character.isspace() for character in name):
                raise ValueError(
                    f"{label}.manifests.{ecosystem} entry {name!r} must not contain whitespace"
                )
        manifests[ecosystem] = names
    if not packages and not actions and not urls and not manifests:
        raise ValueError(f"{label} must declare packages, actions, urls, or manifests")
    return ProducerSub(packages, actions, urls, manifests, display)


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


def load_policy() -> Policy:
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


def _package_match(entry: str, wanted: str) -> str | None:
    if entry.startswith("^"):
        try:
            if re.fullmatch(entry, wanted, re.IGNORECASE) is not None:
                return wanted
        except re.error:
            return None
        return None
    return entry if entry.casefold() == wanted else None


def _action_name(name: str) -> str:
    match = _ACTION_REF.fullmatch(name.strip())
    if match is None:
        return name.strip().casefold()
    return cast(str, match.group(1)).casefold()


def _url_forms(name: str) -> set[str]:
    raw = name.strip().rstrip("/")
    forms = {raw.casefold()}
    try:
        parts = urlsplit(raw if "://" in raw else f"//{raw}")
    except ValueError:
        return forms
    hostname = parts.hostname
    if hostname is None:
        return forms
    path = (parts.path or "").lstrip("/")
    form = f"{hostname.casefold()}/{path}" if path else hostname.casefold()
    forms.add(form.removesuffix(".git").rstrip("/"))
    return forms


def _label_words(label: str) -> set[str]:
    return {
        word.casefold()
        for word in re.findall(r"[A-Za-z0-9]+", label)
        if word.casefold() not in _LABEL_STOPWORDS
    }


def _label_match(label: str, wanted: str) -> bool:
    wanted_words = {
        word.casefold()
        for word in re.findall(r"[A-Za-z0-9]+", wanted)
        if word.casefold() not in _LABEL_STOPWORDS
    }
    return bool(wanted_words) and wanted_words <= _label_words(label)


def manifest_key(ecosystem: str, name: str) -> str:
    if ecosystem == "npm":
        return name.strip()
    if ecosystem == "cargo":
        return name.strip().replace("_", "-").casefold()
    return re.sub(r"[-_.]+", "-", name.strip()).casefold()


def manifest_match(name: str, ecosystem: str, sub: ProducerSub) -> str | None:
    key = manifest_key(ecosystem, name)
    for entry in sub.manifests.get(ecosystem, ()):
        if manifest_key(ecosystem, entry) == key:
            return entry
    return None


def manifest_producer(
    name: str, ecosystem: str, producers: dict[str, ProducerSub]
) -> tuple[str, str] | None:
    for producer_id, sub in producers.items():
        matched = manifest_match(name, ecosystem, sub)
        if matched is not None:
            return producer_id, matched
    return None


def _producer_matches(name: str, producer: str, sub: ProducerSub) -> Iterator[SubstituteMatch]:
    wanted = name.strip().casefold()
    for manager, entries in sub.packages.items():
        for entry in entries:
            matched = _package_match(entry, wanted)
            if matched is not None:
                yield SubstituteMatch(producer, f"package:{manager}", matched)
                break
    action = _action_name(name)
    for declared in sorted(sub.actions, key=str.casefold):
        if declared.casefold() == action:
            yield SubstituteMatch(producer, "action", declared)
            break
    forms = _url_forms(name)
    for prefix in sub.urls:
        wanted_prefix = prefix.casefold().rstrip("/")
        if any(form == wanted_prefix or form.startswith(f"{wanted_prefix}/") for form in forms):
            yield SubstituteMatch(producer, "url", prefix)
            break
    for ecosystem in sorted(sub.manifests):
        matched = manifest_match(name, ecosystem, sub)
        if matched is not None:
            yield SubstituteMatch(producer, f"manifest:{ecosystem}", matched)
    if _label_match(sub.label, wanted):
        yield SubstituteMatch(producer, "label", sub.label)


def lookup(name: str, kinds: Callable[[str], bool] | None = None) -> list[SubstituteMatch]:
    """One match per producer: its first match kind, or its first kind that `kinds` accepts."""
    policy = load_policy()
    matches = []
    for producer, sub in policy.producers.items():
        match = next(
            (found for found in _producer_matches(name, producer, sub) if kinds is None or kinds(found.kind)),
            None,
        )
        if match is not None:
            matches.append(match)
    return matches


def render_substitution_table(policy: Policy | None = None) -> str:
    policy = load_policy() if policy is None else policy
    lines = [
        GENERATED_BEGIN,
        "",
        "| Upstream tool | Owned producer |",
        "| --- | --- |",
    ]
    lines.extend(f"| {sub.label} | `{producer}` |" for producer, sub in policy.producers.items())
    lines.extend(["", GENERATED_END])
    return "\n".join(lines)


def substitution_table(text: str) -> str:
    begin = text.find(GENERATED_BEGIN)
    end = text.find(GENERATED_END)
    if begin == -1 or end == -1 or end < begin:
        raise ValueError("docs/fleet.md lacks a generated owned-substitutes block")
    if text.find(GENERATED_BEGIN, begin + len(GENERATED_BEGIN)) != -1:
        raise ValueError("docs/fleet.md has more than one generated owned-substitutes block")
    return text[begin : end + len(GENERATED_END)]


def update_fleet_doc(path: Path | None = None) -> bool:
    target = DOCS if path is None else path
    if target.is_symlink():
        raise ValueError(f"{target} is a symlink and is not rewritten")
    text = target.read_text(encoding="utf-8")
    substitution_table(text)
    begin = text.index(GENERATED_BEGIN)
    end = text.index(GENERATED_END) + len(GENERATED_END)
    rendered = render_substitution_table()
    updated = text[:begin] + rendered + text[end:]
    if updated == text:
        return False
    target.write_text(updated, encoding="utf-8")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m repomod.substitutes",
        description="Regenerate the owned-substitutes table in docs/fleet.md from fleet/policy/owned-substitutes.toml.",
    )
    parser.add_argument("--write-docs", action="store_true", help="rewrite docs/fleet.md")
    args = parser.parse_args(argv)
    if not args.write_docs:
        parser.error("the only supported operation is --write-docs")
    try:
        changed = update_fleet_doc()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"repomod: {error}", file=sys.stderr)
        return 2
    print("docs/fleet.md: updated" if changed else "docs/fleet.md: unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
