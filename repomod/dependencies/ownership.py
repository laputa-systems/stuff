from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any, cast
from urllib.parse import parse_qsl, unquote, urlsplit

from repomod import substitutes
from repomod.dependencies import commands as commands_module
from repomod.dependencies.graph import Graph, is_first_party
from repomod.dependencies.model import Component, Ecosystem, Instance

CLASSES = ("owned", "mirrored", "substitutable", "upstream")
COMMAND_CLASSES = ("owned", "substitutable", "baseline", "external")
OWNED_OWNERS = frozenset({"joshuarli", "laputa-systems"})
EXCLUDED_ECOSYSTEMS = frozenset({Ecosystem.LOCAL, Ecosystem.SERVICE, Ecosystem.COMMAND})
_STUFF_REGISTRY_HOST = "17166969.xyz"
_COMMAND_EXTERNAL_TOP = 40


def _command_accepted_kinds(kind: str) -> bool:
    return kind == "label" or kind.startswith("package:")
_GITHUB_OWNER = re.compile(
    r"github\.com[:/]([A-Za-z0-9][A-Za-z0-9_.-]*)/", re.IGNORECASE
)
_NAMED_ECOSYSTEMS = frozenset(
    {Ecosystem.GITHUB, Ecosystem.DOCKER, Ecosystem.NPM, Ecosystem.GOLANG}
)
_UPSTREAM_TOP = 50


def ownership(
    graph: Graph, repositories: Iterable[str] | None = None
) -> dict[str, object]:
    selected = _selected(repositories)
    names = sorted(
        (
            name
            for name in graph.repositories
            if selected is None or name.casefold() in selected
        ),
        key=str.casefold,
    )
    producers: dict[str, str | None] = {}
    component_class: dict[tuple[Ecosystem, str], str] = {}
    component_repositories: dict[tuple[Ecosystem, str], set[str]] = defaultdict(set)
    by_repository: dict[str, Counter[str]] = defaultdict(Counter)
    excluded_components: dict[str, set[tuple[Ecosystem, str]]] = defaultdict(set)
    excluded_instances: Counter[str] = Counter()
    for repository in names:
        data = graph.repositories[repository]
        for instance in data.instances:
            component = graph.components.get(instance.component)
            if component is None:
                continue
            key = (component.ecosystem, component.name)
            if component.ecosystem in EXCLUDED_ECOSYSTEMS:
                excluded_components[component.ecosystem.value].add(key)
                excluded_instances[component.ecosystem.value] += 1
                continue
            found = _instance_class(graph, component, instance, producers)
            by_repository[repository][found] += 1
            component_repositories[key].add(repository)
            current = component_class.get(key)
            if current is None or CLASSES.index(found) < CLASSES.index(current):
                component_class[key] = found
    totals: Counter[str] = Counter()
    by_ecosystem: dict[str, Counter[str]] = defaultdict(Counter)
    for (ecosystem, _name), found in component_class.items():
        totals[found] += 1
        by_ecosystem[ecosystem.value][found] += 1
    return {
        "totals": _class_counts(totals),
        "ecosystems": {
            ecosystem: _class_counts(by_ecosystem[ecosystem])
            for ecosystem in sorted(by_ecosystem)
        },
        "repositories": {
            repository: _class_counts(by_repository[repository])
            for repository in sorted(by_repository, key=str.casefold)
        },
        "excluded": {
            ecosystem: {
                "components": len(excluded_components[ecosystem]),
                "instances": excluded_instances[ecosystem],
            }
            for ecosystem in sorted(excluded_components)
        },
        "substitutable": _substitutable_rows(component_class, component_repositories, producers),
        "upstream_top": _upstream_rows(component_class, component_repositories),
        "commands": _commands_section(graph, names),
    }


def ownership_text(value: Mapping[str, Any]) -> list[str]:
    lines = ["ownership (unique package names per ecosystem)", ""]
    ecosystems = _table(value.get("ecosystems"))
    names = sorted(ecosystems, key=str.casefold)
    header = (
        f"{'ecosystem':<12} {'owned':>7} {'mirrored':>9} "
        f"{'substitutable':>14} {'upstream':>8}"
    )
    lines.append(header)
    totals = _table(value.get("totals"))
    for ecosystem in names:
        counts = _table(ecosystems[ecosystem])
        lines.append(
            f"{ecosystem:<12} {_count(counts, 'owned'):>7} "
            f"{_count(counts, 'mirrored'):>9} "
            f"{_count(counts, 'substitutable'):>14} "
            f"{_count(counts, 'upstream'):>8}"
        )
    lines.append(
        f"{'total':<12} {_count(totals, 'owned'):>7} "
        f"{_count(totals, 'mirrored'):>9} "
        f"{_count(totals, 'substitutable'):>14} "
        f"{_count(totals, 'upstream'):>8}"
    )
    excluded = _table(value.get("excluded"))
    if excluded:
        lines.append("")
        lines.append(
            "excluded: "
            + ", ".join(
                f"{ecosystem} {_table(excluded[ecosystem])['components']} "
                f"components ({_table(excluded[ecosystem])['instances']} instances)"
                for ecosystem in sorted(excluded, key=str.casefold)
            )
        )
    commands = _table(value.get("commands"))
    if commands:
        totals = _table(commands.get("totals"))
        instances = _table(commands.get("instances"))
        lines.append("")
        lines.append("commands (unique command names / instances)")
        lines.append(
            f"{'class':<14} {'names':>7} {'instances':>10}"
        )
        lines.extend(
            f"{command_class:<14} {_count(totals, command_class):>7} "
            f"{_count(instances, command_class):>10}"
            for command_class in COMMAND_CLASSES
        )
        external = _list(commands.get("external_top"))
        if external:
            lines.append("")
            lines.append("top external commands (by repository count):")
            for row in external[:15]:
                record = _table(row)
                lines.append(f"  {record['name']} ({record['repositories']} repositories)")
    rows = _list(value.get("substitutable"))
    lines.append("")
    lines.append(f"substitutable ({len(rows)}):")
    for row in rows:
        record = _table(row)
        repositories = _list(record.get("repositories"))
        lines.append(
            f"  {record['ecosystem']} {record['name']} -> {record['producer']} "
            f"({len(repositories)} repositories)"
        )
    return lines


def _selected(repositories: Iterable[str] | None) -> set[str] | None:
    if repositories is None:
        return None
    return {repository.casefold() for repository in repositories}


def _instance_class(
    graph: Graph,
    component: Component,
    instance: Instance,
    producers: dict[str, str | None],
) -> str:
    if is_first_party(graph, instance) or _owned_reference(component, instance):
        return "owned"
    if _mirrored(instance):
        return "mirrored"
    if _producer(component.ecosystem, component.name, producers) is not None:
        return "substitutable"
    return "upstream"


_MATCH_KINDS: Mapping[Ecosystem, Callable[[str], bool]] = {
    Ecosystem.APK: lambda kind: kind == "package:apk",
    Ecosystem.CARGO: lambda kind: kind == "manifest:cargo",
    Ecosystem.PYPI: lambda kind: kind == "manifest:pypi",
    Ecosystem.NPM: lambda kind: kind == "manifest:npm",
    Ecosystem.GITHUB: lambda kind: kind == "action",
    Ecosystem.ARTIFACT: lambda kind: kind == "url",
    Ecosystem.DOCKER: lambda kind: kind == "label" or kind.startswith("package:"),
    Ecosystem.TOOLCHAIN: lambda kind: kind == "label" or kind.startswith("package:"),
}


def _producer(ecosystem: Ecosystem, name: str, cache: dict[str, str | None]) -> str | None:
    accepts = _MATCH_KINDS.get(ecosystem)
    if accepts is None:
        return None
    key = f"{ecosystem.value}\0{name}"
    if key not in cache:
        matches = substitutes.lookup(name, accepts)
        cache[key] = matches[0].producer if matches else None
    return cache[key]


def _mirrored(instance: Instance) -> bool:
    registry = instance.registry_url
    if registry is None:
        return False
    try:
        host = urlsplit(
            registry if "://" in registry else f"//{registry}"
        ).hostname
    except ValueError:
        return False
    if host is None:
        return False
    host = host.casefold().rstrip(".")
    return host == _STUFF_REGISTRY_HOST or host.endswith(f".{_STUFF_REGISTRY_HOST}")


def _owned_reference(component: Component, instance: Instance) -> bool:
    hints = [instance.vcs_url, instance.repository_url, instance.registry_url]
    hints.extend(_qualifiers(instance.purl))
    hints.extend(_qualifiers(component.purl))
    if any(value is not None and _names_owned(value) for value in hints):
        return True
    if component.ecosystem not in _NAMED_ECOSYSTEMS:
        return False
    return _owned_name(component.name) or _owned_name(component.display_name)


def _qualifiers(purl: str) -> list[str]:
    try:
        query = urlsplit(purl).query
    except ValueError:
        return []
    return [value for _key, value in parse_qsl(query, keep_blank_values=True)]


def _names_owned(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    match = _GITHUB_OWNER.search(text)
    if match is not None and match.group(1).casefold() in OWNED_OWNERS:
        return True
    candidate = text if "://" in text or text.startswith("//") else f"//{text}"
    try:
        path = urlsplit(candidate).path
    except ValueError:
        return False
    first = next((segment for segment in path.split("/") if segment), "")
    return first.casefold() in OWNED_OWNERS


def _owned_name(name: str) -> bool:
    parts = [
        part for part in unquote(name).strip().strip("/").split("/") if part
    ]
    if len(parts) < 2:
        return False
    if "." in parts[0] or ":" in parts[0]:
        return len(parts) > 1 and parts[1].lstrip("@").casefold() in OWNED_OWNERS
    return parts[0].lstrip("@").casefold() in OWNED_OWNERS


def _class_counts(counts: Counter[str]) -> dict[str, int]:
    return {name: counts[name] for name in CLASSES}


def _substitutable_rows(
    component_class: Mapping[tuple[Ecosystem, str], str],
    component_repositories: Mapping[tuple[Ecosystem, str], set[str]],
    producers: Mapping[str, str | None],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key in sorted(component_class, key=lambda item: (item[0].value, item[1])):
        if component_class[key] != "substitutable":
            continue
        rows.append(
            {
                "ecosystem": key[0].value,
                "name": key[1],
                "producer": producers.get(f"{key[0].value}\0{key[1]}"),
                "repositories": sorted(component_repositories[key], key=str.casefold),
            }
        )
    return rows


def _upstream_rows(
    component_class: Mapping[tuple[Ecosystem, str], str],
    component_repositories: Mapping[tuple[Ecosystem, str], set[str]],
) -> list[dict[str, object]]:
    keys = [key for key in component_class if component_class[key] == "upstream"]
    keys.sort(key=lambda key: (-len(component_repositories[key]), key[1], key[0].value))
    return [
        {
            "ecosystem": key[0].value,
            "name": key[1],
            "repositories": len(component_repositories[key]),
        }
        for key in keys[:_UPSTREAM_TOP]
    ]


def _commands_section(graph: Graph, names: Sequence[str]) -> dict[str, object]:
    owned = commands_module.owned_commands()
    baseline = commands_module.baseline_commands()
    substitutes_cache: dict[str, tuple[str, str | None] | None] = {}
    per_name: dict[str, dict[str, dict[str, object]]] = {}
    for repository in names:
        data = graph.repositories[repository]
        for instance in data.instances:
            component = graph.components.get(instance.component)
            if component is None or component.ecosystem is not Ecosystem.COMMAND:
                continue
            name = component.name
            repositories = per_name.setdefault(name, {})
            record = repositories.setdefault(
                repository, {"instances": 0, "kinds": set()}
            )
            record["instances"] = cast(int, record["instances"]) + 1
            cast(set[str], record["kinds"]).add(instance.context)
    name_rows: dict[str, dict[str, object]] = {}
    totals: Counter[str] = Counter()
    instance_totals: Counter[str] = Counter()
    repository_totals: dict[str, Counter[str]] = defaultdict(Counter)
    for name in sorted(per_name):
        command_class, producer = _command_class(name, owned, baseline, substitutes_cache)
        repositories = {
            repository: {
                "instances": cast(int, record["instances"]),
                "kinds": sorted(cast(set[str], record["kinds"])),
            }
            for repository, record in sorted(
                per_name[name].items(), key=lambda item: item[0].casefold()
            )
        }
        instances = sum(
            cast(int, record["instances"]) for record in per_name[name].values()
        )
        name_rows[name] = {
            "class": command_class,
            "producer": producer,
            "repository_count": len(repositories),
            "repositories": repositories,
        }
        totals[command_class] += 1
        instance_totals[command_class] += instances
        for repository, record in per_name[name].items():
            repository_totals[repository][command_class] += cast(int, record["instances"])
    external = [
        name
        for name in sorted(name_rows)
        if name_rows[name]["class"] == "external"
    ]
    external.sort(
        key=lambda name: (
            -cast(int, name_rows[name]["repository_count"]),
            name,
        )
    )
    return {
        "totals": {command_class: totals[command_class] for command_class in COMMAND_CLASSES},
        "instances": {
            command_class: instance_totals[command_class]
            for command_class in COMMAND_CLASSES
        },
        "repositories": {
            repository: {
                command_class: repository_totals[repository][command_class]
                for command_class in COMMAND_CLASSES
            }
            for repository in sorted(repository_totals, key=str.casefold)
        },
        "names": name_rows,
        "external_top": [
            {
                "name": name,
                "repositories": name_rows[name]["repository_count"],
            }
            for name in external[:_COMMAND_EXTERNAL_TOP]
        ],
    }


def _command_class(
    name: str,
    owned: Mapping[str, str],
    baseline: frozenset[str],
    cache: dict[str, tuple[str, str | None] | None],
) -> tuple[str, str | None]:
    if name in owned:
        return "owned", owned[name]
    if name not in cache:
        matches = substitutes.lookup(name, _command_accepted_kinds)
        cache[name] = (
            (matches[0].producer, matches[0].matched) if matches else None
        )
    found = cache[name]
    if found is not None:
        return "substitutable", found[0]
    if name in baseline:
        return "baseline", None
    return "external", None


def _table(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], value)
    return {}


def _list(value: object) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _count(counts: Mapping[str, Any], name: str) -> int:
    value = counts.get(name, 0)
    return value if isinstance(value, int) else 0
