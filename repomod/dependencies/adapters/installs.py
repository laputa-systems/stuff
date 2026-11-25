from __future__ import annotations

import posixpath
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from repomod import install_parse
from repomod.dependencies.adapters.containers import ContainersAdapter
from repomod.dependencies.model import (
    AdapterResult,
    Component,
    Ecosystem,
    Edge,
    Evidence,
    InputContent,
    Instance,
    Project,
    Relation,
    Resolution,
    Scope,
    SourceKind,
    project_key,
    purl,
)

_CONTAINERS = ContainersAdapter()


@dataclass(frozen=True, slots=True)
class InstallsAdapter:
    name: ClassVar[str] = "installs"

    def matches(self, path: str) -> bool:
        return install_parse.install_surface(path) is not None

    def extract(self, inputs: Sequence[InputContent]) -> AdapterResult:
        projects: dict[str, Project] = {}
        drafts: dict[str, _Ref] = {}
        edges: list[Edge] = []
        for content in inputs:
            directory = posixpath.dirname(content.path) or "."
            project_id = project_key(directory, Ecosystem.GENERIC)
            skip_apk = _CONTAINERS.matches(content.path)
            env = install_parse.assignments(content.text)
            for number, line in install_parse.logical_lines(content.text):
                for manager, name in install_parse.system_package_installs(line, env):
                    if manager == "apk" and skip_apk:
                        continue
                    ecosystem = Ecosystem.APK if manager == "apk" else Ecosystem.SYSTEM
                    component_name = name if manager == "apk" else f"{manager}/{name}"
                    ref = _Ref(
                        component_name,
                        ecosystem,
                        SourceKind.VENDORED if content.vendored else SourceKind.REGISTRY,
                    )
                    drafts.setdefault(ref.instance_id, ref)
                    if project_id not in projects:
                        projects[project_id] = Project(
                            project_id, Ecosystem.GENERIC, directory
                        )
                    edges.append(
                        Edge(
                            from_id=project_id,
                            to_id=ref.instance_id,
                            relation=Relation.DIRECT,
                            scope=Scope.SYSTEM,
                            optional=False,
                            constraint=None,
                            resolved_version=None,
                            condition=None,
                            source_kind=ref.source_kind,
                            resolution=Resolution.DECLARED_ONLY,
                            evidence=(Evidence(content.path, f"L{number}"),),
                        )
                    )
        components: dict[str, Component] = {}
        instances: list[Instance] = []
        for ref in drafts.values():
            component = Component(ref.component, ref.ecosystem, ref.name, ref.name)
            components.setdefault(component.purl, component)
            instances.append(
                Instance(
                    id=ref.instance_id,
                    purl=ref.purl,
                    component=ref.component,
                    version=ref.version,
                    source_kind=ref.source_kind,
                )
            )
        return AdapterResult(
            projects=tuple(projects.values()),
            components=tuple(components.values()),
            instances=tuple(instances),
            edges=tuple(edges),
        )


@dataclass(frozen=True, slots=True)
class _Ref:
    name: str
    ecosystem: Ecosystem
    source_kind: SourceKind
    version: str | None = None

    @property
    def purl(self) -> str:
        return purl(self.ecosystem, self.name, self.version)

    @property
    def component(self) -> str:
        return purl(self.ecosystem, self.name)

    @property
    def instance_id(self) -> str:
        return f"{self.purl}#"
