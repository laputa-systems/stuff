from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest
from deps_fixtures import instance, repository, write_inventory

from repomod import substitutes
from repomod.dependencies import graph as graph_module
from repomod.dependencies import ownership
from repomod.dependencies.model import Ecosystem, RepositoryData, SourceKind


def _graph(root: Path, repositories: Sequence[RepositoryData]) -> graph_module.Graph:
    inventory = write_inventory(root, repositories)
    return graph_module.build_graph(graph_module.load_inventory(inventory))


def _fleet(root: Path) -> graph_module.Graph:
    return _graph(
        root,
        [
            repository(
                "acme/one",
                (
                    instance(Ecosystem.CARGO, "serde", "1.0.0"),
                    instance(Ecosystem.CARGO, "criterion", "0.5.1"),
                    instance(
                        Ecosystem.NPM,
                        "lodash",
                        "4.17.21",
                        registry_url="https://npm.17166969.xyz/current/",
                    ),
                    instance(
                        Ecosystem.CARGO,
                        "first-flag",
                        "1.0.0",
                        first_party=True,
                    ),
                    instance(
                        Ecosystem.CARGO,
                        "vcs-dep",
                        "0.2.0",
                        source_kind=SourceKind.GIT,
                        vcs_url="https://github.com/laputa-systems/vcs-dep",
                    ),
                    instance(
                        Ecosystem.GITHUB,
                        "joshuarli/my-action",
                        "v1",
                        source_kind=SourceKind.GIT,
                        vcs_url="https://github.com/joshuarli/my-action",
                    ),
                    instance(
                        Ecosystem.DOCKER,
                        "joshuarli/musl-toolchain",
                        "1.0.0",
                        source_kind=SourceKind.IMAGE,
                    ),
                    instance(
                        Ecosystem.LOCAL,
                        "workspace-crate",
                        "0.1.0",
                        source_kind=SourceKind.PATH,
                    ),
                    instance(Ecosystem.SERVICE, "svc/thing", "1.0.0"),
                ),
            ),
            repository(
                "acme/two",
                (
                    instance(Ecosystem.CARGO, "serde", "1.0.0"),
                    instance(
                        Ecosystem.NPM,
                        "lodash",
                        "4.17.21",
                        registry_url="https://registry.npmjs.org/",
                    ),
                    instance(Ecosystem.APK, "git", "2.54.1-r0"),
                    instance(
                        Ecosystem.NPM,
                        "@laputa-systems/ui-dashboard",
                        "0.9.1",
                        source_kind=SourceKind.URL,
                        repository_url="https://npm.17166969.xyz/current/",
                    ),
                ),
            ),
        ],
    )


def _dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _rows(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list)
    return cast(list[dict[str, object]], value)


def _counts(value: object) -> dict[str, int]:
    return {str(key): cast(int, item) for key, item in _dict(value).items()}


def test_classifies_each_class_and_counts(tmp_path: Path) -> None:
    value = ownership.ownership(_fleet(tmp_path))

    assert _counts(value["totals"]) == {
        "owned": 5,
        "mirrored": 1,
        "substitutable": 2,
        "upstream": 1,
    }
    ecosystems = _dict(value["ecosystems"])
    assert _counts(ecosystems["cargo"]) == {
        "owned": 2,
        "mirrored": 0,
        "substitutable": 1,
        "upstream": 1,
    }
    assert _counts(ecosystems["npm"]) == {
        "owned": 1,
        "mirrored": 1,
        "substitutable": 0,
        "upstream": 0,
    }
    assert _counts(ecosystems["github"])["owned"] == 1
    assert _counts(ecosystems["docker"])["owned"] == 1
    assert _counts(ecosystems["apk"])["substitutable"] == 1


def test_repository_counts_instances_per_class(tmp_path: Path) -> None:
    value = ownership.ownership(_fleet(tmp_path))

    repositories = _dict(value["repositories"])
    assert _counts(repositories["acme/one"]) == {
        "owned": 4,
        "mirrored": 1,
        "substitutable": 1,
        "upstream": 1,
    }
    assert _counts(repositories["acme/two"]) == {
        "owned": 1,
        "mirrored": 0,
        "substitutable": 1,
        "upstream": 2,
    }


def test_excluded_ecosystems_are_counted_separately(tmp_path: Path) -> None:
    value = ownership.ownership(_fleet(tmp_path))

    excluded = _dict(value["excluded"])
    assert _dict(excluded["local"]) == {"components": 1, "instances": 1}
    assert _dict(excluded["service"]) == {"components": 1, "instances": 1}


def test_substitutable_and_upstream_rows(tmp_path: Path) -> None:
    value = ownership.ownership(_fleet(tmp_path))

    substitutable = {
        (str(row["ecosystem"]), str(row["name"])): row
        for row in (_dict(item) for item in cast(list[object], value["substitutable"]))
    }
    assert substitutable[("cargo", "criterion")]["producer"] == "laputa-systems/rustybench"
    assert substitutable[("cargo", "criterion")]["repositories"] == ["acme/one"]
    assert substitutable[("apk", "git")]["producer"] == "laputa-systems/git-build"
    assert substitutable[("apk", "git")]["repositories"] == ["acme/two"]

    rows = [
        _dict(item) for item in cast(list[object], value["upstream_top"])
    ]
    assert rows == [
        {"ecosystem": "cargo", "name": "serde", "repositories": 2}
    ]


def test_substitute_lookup_supplies_the_producer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_lookup(name: str, kinds: object = None) -> list[substitutes.SubstituteMatch]:
        if name == "sub-me":
            return [
                substitutes.SubstituteMatch("acme/producer", "manifest:cargo", "sub-me")
            ]
        return []

    monkeypatch.setattr(substitutes, "lookup", fake_lookup)
    graph = _graph(
        tmp_path,
        [repository("acme/one", (instance(Ecosystem.CARGO, "sub-me", "1.0.0"),))],
    )

    value = ownership.ownership(graph)

    assert _counts(value["totals"])["substitutable"] == 1
    assert value["substitutable"] == [
        {
            "ecosystem": "cargo",
            "name": "sub-me",
            "producer": "acme/producer",
            "repositories": ["acme/one"],
        }
    ]


def test_substitutes_match_only_their_own_ecosystem(tmp_path: Path) -> None:
    graph = _graph(
        tmp_path,
        [
            repository(
                "acme/one",
                (
                    instance(Ecosystem.CARGO, "cmake", "0.1.54"),
                    instance(Ecosystem.APK, "cmake", "4.1.2-r0"),
                    instance(Ecosystem.NPM, "js", "1.0.0"),
                ),
            )
        ],
    )

    value = ownership.ownership(graph)

    rows = {(row["ecosystem"], row["name"]): row["producer"] for row in _rows(value["substitutable"])}
    assert rows == {("apk", "cmake"): "laputa-systems/cmake-build"}
    assert _counts(_dict(value["ecosystems"])["cargo"])["upstream"] == 1
    assert _counts(_dict(value["ecosystems"])["npm"])["upstream"] == 1


def test_owned_precedence_over_mirrored_and_substitutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_lookup(name: str, kinds: object = None) -> list[substitutes.SubstituteMatch]:
        return [substitutes.SubstituteMatch("acme/producer", "package:apk", name)]

    monkeypatch.setattr(substitutes, "lookup", fake_lookup)
    graph = _graph(
        tmp_path,
        [
            repository(
                "acme/one",
                (
                    instance(
                        Ecosystem.NPM,
                        "mirror-me",
                        "1.0.0",
                        registry_url="https://npm.17166969.xyz/current/",
                        vcs_url="https://github.com/laputa-systems/mirror-me",
                    ),
                ),
            )
        ],
    )

    value = ownership.ownership(graph)

    assert _counts(value["totals"])["owned"] == 1
    assert _counts(value["totals"])["mirrored"] == 0
    assert value["substitutable"] == []


def test_mirrored_requires_a_stuff_registry_host(tmp_path: Path) -> None:
    graph = _graph(
        tmp_path,
        [
            repository(
                "acme/one",
                (
                    instance(
                        Ecosystem.PYPI,
                        "upstream-pkg",
                        "1.0.0",
                        registry_url="https://pypi.org/simple",
                    ),
                    instance(
                        Ecosystem.PYPI,
                        "stuff-pkg",
                        "2.0.0",
                        registry_url="https://pypi.17166969.xyz/current/simple/",
                    ),
                ),
            )
        ],
    )

    value = ownership.ownership(graph)

    assert _counts(value["totals"])["upstream"] == 1
    assert _counts(value["totals"])["mirrored"] == 1
    assert _counts(_dict(value["ecosystems"])["pypi"]) == {
        "owned": 0,
        "mirrored": 1,
        "substitutable": 0,
        "upstream": 1,
    }


def test_repo_selection_limits_the_fleet(tmp_path: Path) -> None:
    graph = _fleet(tmp_path / "fleet")
    value = ownership.ownership(graph, ["acme/two"])

    assert set(_dict(value["repositories"])) == {"acme/two"}
    assert _counts(value["totals"]) == {
        "owned": 1,
        "mirrored": 0,
        "substitutable": 1,
        "upstream": 2,
    }


def test_output_is_deterministic(tmp_path: Path) -> None:
    graph = _fleet(tmp_path)
    first = ownership.ownership(graph)
    second = ownership.ownership(graph)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert ownership.ownership_text(first) == ownership.ownership_text(second)


def test_text_prints_per_ecosystem_table_and_substitutable(tmp_path: Path) -> None:
    value = ownership.ownership(_fleet(tmp_path))
    lines = ownership.ownership_text(value)
    text = "\n".join(lines)

    assert "ecosystem" in lines[2]
    assert "owned" in lines[2]
    assert "mirrored" in lines[2]
    assert "substitutable" in lines[2]
    assert "upstream" in lines[2]
    assert any(line.startswith("total") for line in lines)
    assert "cargo" in text
    assert "npm" in text
    assert "substitutable (" in text
    assert "criterion" in text
    assert "laputa-systems/rustybench" in text
    assert "excluded:" in text
