"""The dashboard's canonical preview dataset.

`make preview` renders the dashboard from it and serves it; the golden test
renders the same dataset and compares what every page shows. The dataset is a
frozen slice of the real fleet (public repositories only): their inventory,
line counts, the enrichment entries they reference, their status as last
collected, and a fixed render time, so the pages do not drift as the live fleet
or the clock moves. `freeze` rebuilds it deliberately from the current fleet.

    uv run python -m repomod.dependencies.preview render [--out DIR]
    uv run python -m repomod.dependencies.preview freeze
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from repomod import paths
from repomod.dependencies import diff as diff_module
from repomod.dependencies import enrich, graph, loc_view, render
from repomod.types import StatusArea, StatusItem, StatusLevel

FIXTURE = paths.ROOT / "tests" / "fixtures" / "dashboard"
OUTPUT = paths.WORK / "preview" / "dashboard"

# Public repositories that between them exercise every page: vulnerable owned
# packages (python-build, xsh), vulnerable forks (gh, syncthing, rage), many
# upgrades (xsh, python-build), clean repositories, complete scans, and Rust,
# Go, TypeScript, Swift, Python, Zig and C code.
REPOSITORIES = (
    "joshuarli/ctrs",
    "joshuarli/extensions",
    "joshuarli/gh",
    "joshuarli/img",
    "joshuarli/kache",
    "joshuarli/lz",
    "joshuarli/mactop",
    "joshuarli/pytest-parallel",
    "joshuarli/syncthing",
    "laputa-systems/doas-rs",
    "laputa-systems/laputa-ui-dashboard",
    "laputa-systems/mdevd-rs",
    "laputa-systems/python-build",
    "laputa-systems/rage",
    "laputa-systems/srv",
    "laputa-systems/ssh-build",
    "laputa-systems/xsh",
    "laputa-systems/zzz",
)

# The previous snapshot the Changes page compares against: these packages were
# at the listed version, and the `added` ones did not exist yet.
PREVIOUS_VERSIONS = (
    ("laputa-systems/xsh", "serde", "1.0.210"),
    ("laputa-systems/xsh", "regex", "1.11.1"),
    ("joshuarli/lz", "libc", "0.2.160"),
    ("laputa-systems/srv", "rustix", "1.0.8"),
    ("joshuarli/extensions", "vite", "7.1.4"),
    ("laputa-systems/doas-rs", "bitflags", "2.14.0"),
)
ADDED = (("laputa-systems/xsh", "anyhow"),)


@dataclass(frozen=True, slots=True)
class Dataset:
    inventory: graph.Inventory
    graph: graph.Graph
    enrichment: enrich.Enrichment
    loc: loc_view.Data
    status: dict[str, tuple[StatusItem, ...]]
    diff: diff_module.Diff
    rendered_at: float


def load(fixture: Path = FIXTURE) -> Dataset:
    meta = json.loads((fixture / "meta.json").read_text(encoding="utf-8"))
    inventory = graph.load_inventory(fixture / "inventory")
    built = graph.build_graph(inventory)
    status = {
        repository: tuple(
            StatusItem(
                StatusArea(item["area"]),
                item["label"],
                StatusLevel(item["level"]),
                item.get("url"),
                bool(item.get("running")),
            )
            for item in items
        )
        for repository, items in json.loads((fixture / "status.json").read_text(encoding="utf-8")).items()
    }
    return Dataset(
        inventory,
        built,
        enrich.load_cache(fixture / "enrichment.json"),
        loc_view.load(fixture / "loc"),
        status,
        diff_module.diff_inventories(_previous(inventory), inventory, source="previous snapshot", target="preview"),
        float(meta["rendered_at"]),
    )


def render_preview(output: Path = OUTPUT, fixture: Path = FIXTURE) -> render.Dashboard:
    data = load(fixture)
    return render.render(
        data.inventory,
        data.graph,
        output,
        diff_value=data.diff,
        status=data.status,
        enrichment=data.enrichment,
        loc=data.loc,
        rendered_at=data.rendered_at,
    )


def _previous(inventory: graph.Inventory) -> graph.Inventory:
    """The current inventory with the scripted packages rewound, for the Changes page."""
    rewound = {(repository, component): version for repository, component, version in PREVIOUS_VERSIONS}
    added = set(ADDED)
    repositories = {}
    for name, data in inventory.repositories.items():
        names = {component.purl: component.name for component in data.components}
        instances = []
        for instance in data.instances:
            component = names.get(instance.component, "")
            if (name, component) in added:
                continue
            version = rewound.get((name, component))
            if version is not None and instance.version is not None:
                instance = replace(instance, version=version, purl=instance.purl.rsplit("@", 1)[0] + "@" + version)
            instances.append(instance)
        repositories[name] = replace(data, instances=tuple(instances))
    return graph.Inventory(inventory.path, repositories, inventory.entries)


def freeze(fixture: Path = FIXTURE) -> None:
    """Rebuilds the dataset from the current fleet. Run deliberately, then review the golden diff."""
    import time

    from repomod import catalog as catalog_module
    from repomod.cmd import status as status_module

    if fixture.exists():
        shutil.rmtree(fixture)
    for kind, source in (("inventory", paths.INVENTORY), ("loc", paths.LOC)):
        index = json.loads((source / "index.json").read_text(encoding="utf-8"))
        index["repositories"] = {
            name: entry for name, entry in index["repositories"].items() if name in REPOSITORIES
        }
        _write(fixture / kind / "index.json", index)
        for name in REPOSITORIES:
            document = json.loads((source / "repos" / f"{name}.json").read_text(encoding="utf-8"))
            _write(fixture / kind / "repos" / f"{name}.json", document)

    inventory = graph.load_inventory(fixture / "inventory")
    built = graph.build_graph(inventory)
    purls = {instance.purl for instance in built.instances.values()}
    bases = {purl.split("@", 1)[0] for purl in purls}
    names = {component.name for component in built.components.values()}
    cache = json.loads(enrich.cache_file(enrich.CACHE_NAME).read_text(encoding="utf-8"))
    cache["results"] = {purl: entry for purl, entry in cache["results"].items() if purl in purls}
    cache["sources"] = {purl: urls for purl, urls in cache["sources"].items() if purl in bases}
    for catalog in cache.get("mirror", {}).values():
        packages = catalog.get("packages", {})
        catalog["packages"] = {name: versions for name, versions in packages.items() if name in names}
    _write(fixture / "enrichment.json", cache)

    catalog = catalog_module.load_catalog(paths.CATALOG)
    selected = tuple(repository for repository in catalog.repositories if str(repository.id) in REPOSITORIES)
    report = status_module.collect_status(catalog, selected, {}, offline=True, refresh=False)
    status: dict[str, list[dict[str, Any]]] = {}
    for row in report.rows:
        name = str(row["repository"])
        status[name] = [
            {
                "area": item.area.value,
                "label": item.label,
                "level": item.level.value,
                "url": item.url,
                "running": item.running,
            }
            for item in status_module.status_items(row, report.ci[name])
        ]
    _write(fixture / "status.json", dict(sorted(status.items())))
    _write(fixture / "meta.json", {"rendered_at": round(time.time()), "repositories": list(REPOSITORIES)})


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="repomod.dependencies.preview")
    commands = parser.add_subparsers(dest="command", required=True)
    rendering = commands.add_parser("render", help="render the dashboard from the preview dataset")
    rendering.add_argument("--out", type=Path, default=OUTPUT)
    commands.add_parser("freeze", help="rebuild the preview dataset from the current fleet")
    args = parser.parse_args(argv)
    if args.command == "freeze":
        freeze()
        print(f"froze {len(REPOSITORIES)} repositories into {FIXTURE.relative_to(paths.ROOT)}")
        return 0
    result = render_preview(args.out)
    print(f"wrote {len(result.pages)} pages to {result.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
