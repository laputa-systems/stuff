from __future__ import annotations

import posixpath
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from repomod.dependencies.adapters.cloudflare import _bindings, _load
from repomod.dependencies.model import (
    AdapterResult,
    Component,
    Ecosystem,
    Edge,
    Evidence,
    InputContent,
    Instance,
    Issue,
    Project,
    Relation,
    Resolution,
    Scope,
    SourceKind,
    project_key,
    purl,
)


@dataclass(frozen=True, slots=True)
class OrangeAdapter:
    name: ClassVar[str] = "orange"

    def matches(self, path: str) -> bool:
        return (
            path == "openorange/apps.toml"
            or path.endswith("/openorange/apps.toml")
            or path.rsplit("/", 1)[-1] == "orange.jsonc"
        )

    def extract(self, inputs: Sequence[InputContent]) -> AdapterResult:
        issues: list[Issue] = []
        projects: dict[str, Project] = {}
        components: dict[str, Component] = {}
        instances: dict[str, Instance] = {}
        edges: list[Edge] = []
        for content in inputs:
            document = _load(content.path, content.text, issues)
            if document is None:
                continue
            directory = posixpath.dirname(content.path) or "."
            project = Project(project_key(directory, Ecosystem.GENERIC), Ecosystem.GENERIC, directory)
            bindings: list[tuple[str, str, str, str]] = []
            if content.path == "openorange/apps.toml" or content.path.endswith("/openorange/apps.toml"):
                apps = document.get("apps", {})
                if isinstance(apps, dict):
                    for app, config in apps.items():
                        if not isinstance(config, dict) or config.get("kind") != "orange":
                            continue
                        for field, kind in (("namespace", "namespace"), ("buckets", "r2"),
                                            ("hostnames", "private-host"), ("public_hostnames", "public-host")):
                            value = config.get(field)
                            values = value if isinstance(value, list) else [value]
                            for index, item in enumerate(values):
                                if isinstance(item, str) and item:
                                    suffix = f"[{index}]" if isinstance(value, list) else ""
                                    bindings.append((kind, f"{app}/{item}", item, f"apps.{app}.{field}{suffix}"))
            else:
                bindings.extend(_bindings(document))
            if bindings:
                projects[project.id] = project
            for kind, binding, identifier, locator in bindings:
                name = f"orange-{kind}/{binding}"
                component = purl(Ecosystem.SERVICE, name)
                instance = f"{component}#"
                components[component] = Component(component, Ecosystem.SERVICE, name, name)
                instances[instance] = Instance(instance, component, component, None, SourceKind.REGISTRY)
                edges.append(Edge(project.id, instance, Relation.DIRECT, Scope.SERVICE, False,
                                  identifier, None, None, SourceKind.REGISTRY, Resolution.RESOLVED,
                                  (Evidence(content.path, locator),)))
        return AdapterResult(projects=tuple(projects.values()), components=tuple(components.values()),
                             instances=tuple(instances.values()), edges=tuple(edges), issues=tuple(issues))
