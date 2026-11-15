from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

import pytest
from deps_fixtures import instance, issue, project, repository, write_inventory

from repomod.dependencies import atlas, graph, render
from repomod.dependencies.model import (
    CoverageKind,
    Ecosystem,
    Edge,
    Evidence,
    Relation,
    RepositoryData,
    Resolution,
    Scope,
    SourceKind,
)

HOSTILE_PURL = "pkg:cargo/evil</script><script>alert(1)</script>"


def _payload(text: str) -> dict[str, Any]:
    return json.loads(text[text.index("=") + 2 : text.rindex(";")])


def _graph(tmp_path: Path, repositories: list[RepositoryData]) -> graph.Graph:
    inventory = write_inventory(tmp_path, repositories)
    return graph.build_graph(graph.load_inventory(inventory))


def _shared_graph(tmp_path: Path) -> graph.Graph:
    serde = instance(Ecosystem.CARGO, "serde", "1.0.0")
    serde_new = instance(Ecosystem.CARGO, "serde", "1.0.1")
    one_edge = (
        Edge(
            ".:cargo",
            serde.id,
            Relation.DIRECT,
            Scope.RUNTIME,
            False,
            "^1.0",
            "1.0.0",
            None,
            SourceKind.REGISTRY,
            Resolution.RESOLVED,
            (Evidence("Cargo.toml", "dependencies.serde"),),
        ),
    )
    one = repository(
        "acme/one",
        (serde,),
        projects=(project(".", Ecosystem.CARGO),),
        edges=one_edge,
    )
    two = repository(
        "acme/two",
        (serde, serde_new),
        projects=(project(".", Ecosystem.CARGO),),
        edges=(
            Edge(
                ".:cargo",
                serde.id,
                Relation.DIRECT,
                Scope.DEV,
                True,
                "^1.0",
                "1.0.0",
                "cfg(dev)",
                SourceKind.REGISTRY,
                Resolution.CONDITIONAL,
                (),
            ),
            Edge(
                serde.id,
                serde_new.id,
                Relation.TRANSITIVE,
                Scope.RUNTIME,
                False,
                None,
                "1.0.1",
                None,
                SourceKind.REGISTRY,
                Resolution.RESOLVED,
                (),
            ),
        ),
    )
    return _graph(tmp_path, [one, two])


def test_atlas_payload_is_deterministic(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    assert atlas.build(built, hidden=frozenset()) == atlas.build(built, hidden=frozenset())


def test_shared_instance_is_one_global_node(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    payload = _payload(atlas.build(built, hidden=frozenset()))
    serde_ids = [item[0] for item in payload["instances"] if item[0].startswith("pkg:cargo/serde@")]
    assert serde_ids == ["pkg:cargo/serde@1.0.0#", "pkg:cargo/serde@1.0.1#"]
    one, two = payload["repositories"]
    def indices(entry: dict[str, Any]) -> set[int]:
        found: set[int] = set()
        for edge in entry["e"]:
            if edge[0] == 1:
                found.add(edge[1])
            if edge[2] == 1:
                found.add(edge[3])
        return found
    shared = next(index for index, item in enumerate(payload["instances"]) if item[0] == "pkg:cargo/serde@1.0.0#")
    assert shared in indices(one)
    assert shared in indices(two)


def test_edges_never_cross_repositories(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    payload = _payload(atlas.build(built, hidden=frozenset()))
    for entry in payload["repositories"]:
        project_count = len(entry["p"])
        for edge in entry["e"]:
            for marker, reference in ((edge[0], edge[1]), (edge[2], edge[3])):
                if marker == 0:
                    assert 0 <= reference < project_count
                else:
                    assert 0 <= reference < len(payload["instances"])


def test_multiple_versions_are_not_collapsed(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    payload = _payload(atlas.build(built, hidden=frozenset()))
    versions = {
        item[2]
        for item in payload["instances"]
        if item[0].startswith("pkg:cargo/serde@")
    }
    assert versions == {"1.0.0", "1.0.1"}


def test_optional_and_conditional_transitive_edges_survive(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    payload = _payload(atlas.build(built, hidden=frozenset()))
    two = next(entry for entry in payload["repositories"] if entry["n"] == "acme/two")
    optional_direct = next(edge for edge in two["e"] if edge[4] == payload["relations"].index("direct"))
    assert optional_direct[6] == 1
    assert payload["resolutions"][optional_direct[7]] == "conditional"
    assert optional_direct[10] >= 0
    transitive = next(edge for edge in two["e"] if edge[4] == payload["relations"].index("transitive"))
    assert payload["scopes"][transitive[5]] == "runtime"
    assert payload["relations"][transitive[4]] == "transitive"


def test_hostile_values_are_escaped(tmp_path: Path) -> None:
    hostile = instance(Ecosystem.CARGO, HOSTILE_PURL, None)
    built = _graph(
        tmp_path,
        [
            repository(
                "acme/hostile",
                (hostile,),
                projects=(project(".", Ecosystem.CARGO),),
                edges=(
                    Edge(
                        ".:cargo",
                        hostile.id,
                        Relation.DIRECT,
                        Scope.RUNTIME,
                        False,
                        "<script>alert(1)</script>",
                        None,
                        None,
                        SourceKind.REGISTRY,
                        Resolution.RESOLVED,
                        (),
                    ),
                ),
            )
        ],
    )
    text = atlas.build(built, hidden=frozenset())
    assert "</script>" not in text
    assert "\\u003c" in text


def test_unavailable_is_not_reported_as_empty(tmp_path: Path) -> None:
    built = _graph(
        tmp_path,
        [repository("acme/broken", (), issues=(issue(CoverageKind.CHECKOUT_MISSING, path="Cargo.toml"),))],
    )
    payload = _payload(atlas.build(built, hidden=frozenset()))
    entry = payload["repositories"][0]
    assert entry["s"] == "unavailable"
    assert entry["r"] == 1
    assert entry["c"] == 1
    assert payload["summary"]["states"]["unavailable"] == 1


def test_complete_zero_is_distinct_from_unknown(tmp_path: Path) -> None:
    built = _graph(
        tmp_path,
        [repository("acme/empty", (), projects=(project(".", Ecosystem.GENERIC),))],
    )
    payload = _payload(atlas.build(built, hidden=frozenset()))
    entry = payload["repositories"][0]
    assert entry["s"] == "complete"
    assert entry["e"] == []
    assert entry["d"] == 0
    assert entry["x"] == 0


def test_hidden_repositories_are_counted_not_rendered(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    payload = _payload(atlas.build(built, hidden=frozenset({"acme/secret"})))
    assert payload["summary"]["hidden"] == 1
    text = atlas.build(built, hidden=frozenset({"acme/secret"}))
    assert "private-thing" not in text
    names = [entry["n"] for entry in payload["repositories"]]
    assert names == ["acme/one", "acme/two"]


def test_render_rejects_a_hidden_repository_in_the_graph(tmp_path: Path) -> None:
    inventory = write_inventory(
        tmp_path,
        [
            repository(
                "acme/secret",
                (instance(Ecosystem.PYPI, "private-thing", "0.1"),),
                projects=(project(".", Ecosystem.PYPI),),
            )
        ],
    )
    graph_value = graph.load_inventory(inventory)
    built = graph.build_graph(graph_value)
    with pytest.raises(ValueError, match="hidden"):
        render.render(
            graph_value,
            built,
            tmp_path / "dashboard",
            hidden=frozenset({"acme/secret"}),
        )


def test_consumers_count_is_scoped_to_visible_repositories(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    payload = _payload(atlas.build(built, hidden=frozenset()))
    serde = next(item for item in payload["instances"] if item[0] == "pkg:cargo/serde@1.0.0#")
    assert serde[5] == 2


def test_aggregates_match_exact_edges(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    payload = _payload(atlas.build(built, hidden=frozenset()))
    relations = payload["relations"]
    for entry in payload["repositories"]:
        counted: dict[int, list[int]] = {}
        for edge in entry["e"]:
            component = payload["components"][payload["instances"][edge[3]][1]]
            eco = component[1]
            bucket = counted.setdefault(eco, [0, 0])
            bucket[0 if relations[edge[4]] == "direct" else 1] += 1
        expected = [[eco, pair[0], pair[1]] for eco, pair in sorted(counted.items()) if pair[0] or pair[1]]
        assert entry["a"] == expected
        direct = sum(1 for edge in entry["e"] if relations[edge[4]] == "direct")
        transitive = sum(1 for edge in entry["e"] if relations[edge[4]] == "transitive")
        assert entry["d"] == direct
        assert entry["x"] == transitive


def test_totals_match_edges(tmp_path: Path) -> None:
    built = _shared_graph(tmp_path)
    payload = _payload(atlas.build(built, hidden=frozenset()))
    assert payload["summary"]["edges"] == sum(len(entry["e"]) for entry in payload["repositories"])
    direct = sum(
        1
        for entry in payload["repositories"]
        for edge in entry["e"]
        if payload["relations"][edge[4]] == "direct"
    )
    assert payload["summary"]["direct"] == direct


@pytest.fixture(autouse=True)
def ui_dashboard(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Path:
    dist = tmp_path_factory.mktemp("ui-dashboard")
    for sheet in render.UI_SHEETS:
        (dist / sheet).parent.mkdir(parents=True, exist_ok=True)
        (dist / sheet).write_text(f".ui-{Path(sheet).stem} {{}}\n", encoding="utf-8")
    monkeypatch.setattr(render, "UI_DASHBOARD", dist)
    return dist


def test_explore_page_and_assets_render(tmp_path: Path) -> None:
    repositories = [
        repository(
            "acme/one",
            (instance(Ecosystem.CARGO, "serde", "1.0.0"),),
            projects=(project(".", Ecosystem.CARGO),),
            edges=(
                Edge(
                    ".:cargo",
                    "pkg:cargo/serde@1.0.0#",
                    Relation.DIRECT,
                    Scope.RUNTIME,
                    False,
                    None,
                    "1.0.0",
                    None,
                    SourceKind.REGISTRY,
                    Resolution.RESOLVED,
                    (),
                ),
            ),
        )
    ]
    inventory = write_inventory(tmp_path, repositories)
    built = graph.build_graph(graph.load_inventory(inventory))
    result = render.render(graph.load_inventory(inventory), built, tmp_path / "dashboard")
    page = (result.output / "explore.html").read_text(encoding="utf-8")
    assert 'data-page="explore"' in page
    assert 'href="explore.html"' in page
    assert '<link rel="stylesheet" href="assets/atlas.css">' in page
    assert "assets/vendor/atlas.vendor.js" in page
    assert "assets/atlas-data.js" in page
    assert "assets/atlas.js" in page
    assert "assets/search.js" not in page
    other = (result.output / "repositories.html").read_text(encoding="utf-8")
    assert "assets/search.js" in other
    data = (result.output / "assets" / "atlas-data.js").read_text(encoding="utf-8")
    assert data.startswith("/* atlas.js")
    assert "</script>" not in data
    assert (result.output / "assets" / "atlas.js").is_file()
    assert "fetch(" not in (result.output / "assets" / "atlas.js").read_text(encoding="utf-8")
    assert "fetch(" not in (result.output / "assets" / "atlas-data.js").read_text(encoding="utf-8")
    assert "fetch(" not in (result.output / "assets" / "atlas.css").read_text(encoding="utf-8")
    assert (result.output / "assets" / "vendor" / "atlas.vendor.js").is_file()
    assert (result.output / "assets" / "vendor" / "VENDORED.md").is_file()


def test_render_does_not_open_sockets_for_atlas(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repositories = [
        repository(
            "acme/one",
            (instance(Ecosystem.CARGO, "serde", "1.0.0"),),
            projects=(project(".", Ecosystem.CARGO),),
        )
    ]
    inventory = write_inventory(tmp_path, repositories)

    def blocked(*arguments: object, **keywords: object) -> None:
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)

    built = graph.build_graph(graph.load_inventory(inventory))
    render.render(graph.load_inventory(inventory), built, tmp_path / "dashboard")
