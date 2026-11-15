from __future__ import annotations

import re
import shutil
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, quote, urlsplit

from packaging.version import InvalidVersion, Version

from repomod import dependency_roles, paths
from repomod.dependencies import (
    analysis,
    atlas,
    enrich,
    insights,
    jsdata,
    loc_view,
    migrations,
    triage,
    ui,
    weight,
    weight_view,
    world,
)
from repomod.dependencies import diff as diff_module
from repomod.dependencies.graph import Graph, Inventory
from repomod.dependencies.model import (
    CoverageKind,
    Ecosystem,
    Edge,
    IndexEntry,
    Instance,
    Issue,
    Relation,
    RepositoryData,
    SourceKind,
)
from repomod.dependencies.triage import ActionKind
from repomod.dependencies.ui import Bar, Block, Cell, Column, Line, Mark, NavGroup, NavLink, Segment, Tile, Tone
from repomod.dependencies.ui import escape as _e
from repomod.rules import actions as actions_rule
from repomod.rules.python_standard import PYTHON_TOOL_NAMES
from repomod.types import StatusItem, StatusLevel

MARKER = ".repomod-dashboard"
ASSETS = Path(__file__).with_name("assets")
LOC_DATA = paths.LOC
UI_DASHBOARD = paths.ROOT / "crates" / "stuff-catalog" / "assets" / "ui-dashboard"
UI_SHEETS = ("styles.css", "tokens.css", "layout.css", "data.css")
_LIST_ROWS = 25
_PREVIEW_ROWS = 8
_SHOWN_REPOSITORIES = 4
_STATUS_TONES = {
    StatusLevel.OK: Tone.OK,
    StatusLevel.ATTENTION: Tone.WARN,
    StatusLevel.FAILING: Tone.BAD,
    StatusLevel.MUTED: Tone.NEUTRAL,
}
_STATUS_RANK = {StatusLevel.MUTED: 0, StatusLevel.OK: 1, StatusLevel.ATTENTION: 2, StatusLevel.FAILING: 3}
_CLEAN_TIER = "Clean"
_TIERS = (
    ("Vulnerable", "vulnerable packages first"),
    ("Maintenance", "upgrades, version drift or role conflicts"),
)
_CONSUMER_ROWS = 20
_KIND_LABELS = {
    ActionKind.SECURITY: ("Security", Tone.BAD),
    ActionKind.UNREADABLE: ("Unreadable", Tone.BAD),
    ActionKind.LOCKFILE: ("Lockfile", Tone.WARN),
    ActionKind.TOOLING: ("Tooling", Tone.NEUTRAL),
    ActionKind.MIGRATE: ("Migrate", Tone.NEUTRAL),
    ActionKind.ROUTINE: ("Routine", Tone.NEUTRAL),
}


@dataclass(frozen=True, slots=True)
class Dashboard:
    output: Path
    pages: tuple[Path, ...]
    bytes: int


@dataclass(frozen=True, slots=True)
class _Site:
    graph: Graph
    inventory: Inventory
    entries: Mapping[str, IndexEntry]
    cache: enrich.Enrichment
    report: Mapping[str, Any]
    diff_value: diff_module.Diff | None
    index: tuple[dict[str, object], ...]
    now: float
    outdated: tuple[insights.Outdated, ...]
    migrations: tuple[tuple[migrations.Migration, insights.Outdated], ...]
    vulnerable: tuple[insights.Vulnerable, ...]
    drift: tuple[insights.Split, ...]
    roles: tuple[insights.RoleUse, ...]
    scorecards: tuple[insights.Scorecard, ...]
    forks: tuple[str, ...]
    actions: tuple[triage.Action, ...]
    status: Mapping[str, Sequence[StatusItem]] | None
    hidden: frozenset[str]
    world: world.World
    package_weight: tuple[weight.Repository, ...]
    code: loc_view.Data
    atlas: str


def render(
    inventory: Inventory,
    graph: Graph,
    output: Path,
    *,
    root: Path | None = None,
    diff_value: diff_module.Diff | None = None,
    status: Mapping[str, Sequence[StatusItem]] | None = None,
    hidden: frozenset[str] = frozenset(),
    unmanaged: frozenset[str] = frozenset(),
    enrichment: enrich.Enrichment | None = None,
    loc: loc_view.Data | None = None,
    rendered_at: float | None = None,
) -> Dashboard:
    missing = [sheet for sheet in UI_SHEETS if not (UI_DASHBOARD / sheet).is_file()]
    if missing:
        raise FileNotFoundError(
            f"the pinned @laputa-systems/ui-dashboard sheets are missing at {UI_DASHBOARD}; "
            f"run `make catalog-css`"
        )
    site = _site(inventory, graph, root, diff_value, status, hidden, unmanaged, enrichment, loc, rendered_at)
    if output.is_symlink():
        raise ValueError(f"refusing to write a dashboard through a symlink: {output}")
    if output.exists():
        if not output.is_dir() or not (output / MARKER).is_file():
            raise ValueError(f"refusing to replace a directory that is not a dashboard: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / MARKER).write_text("repomod deps render\n", encoding="utf-8")
    pages = [
        _write_page(output / f"{page}.html", _page(site, title, page, "", body(site)))
        for page, title, body in (
            ("index", "To do", _overview),
            ("repositories", "Repositories", _repositories),
            ("world", "World", _world),
            ("explore", "Explore", _explore),
            ("security", "Security", _security),
            ("outdated", "Upgrades", _outdated),
            ("alignment", "Alignment", _alignment),
            ("choices", "Choices", _choices),
            ("weight", "Weight", _weight),
            ("packages", "Packages", _packages),
            ("lines", "Lines", _lines),
            ("changes", "Changes", _changes),
            ("coverage", "Coverage", _coverage),
        )
    ]
    pages.extend(
        _write_page(
            output / "repos" / name / "index.html",
            _page(site, name, "repository", "../../../", _repository(site, name)),
        )
        for name in site.graph.repositories
    )
    _write_assets(output, site)
    total = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
    return Dashboard(output, tuple(pages), total)


def _site(
    inventory: Inventory,
    graph: Graph,
    root: Path | None,
    diff_value: diff_module.Diff | None,
    status: Mapping[str, Sequence[StatusItem]] | None,
    hidden: frozenset[str],
    unmanaged: frozenset[str],
    enrichment: enrich.Enrichment | None = None,
    loc: loc_view.Data | None = None,
    rendered_at: float | None = None,
) -> _Site:
    overlap = hidden & frozenset(graph.repositories)
    if overlap:
        raise ValueError(f"hidden repositories present in the visible graph: {len(overlap)}")
    cache = enrichment if enrichment is not None else enrich.load_cache()
    report_value = analysis.report(graph, cache=cache, now=rendered_at)
    index: list[dict[str, object]] = []
    for purl, component in sorted(graph.components.items()):
        index.append(
            {
                "purl": purl,
                "name": component.name,
                "ecosystem": component.ecosystem.value,
                "label": component.display_name,
            }
        )
    if diff_value is None and root is not None:
        try:
            diff_value = diff_module.diff_inventory(
                root, inventory.path, from_rev="HEAD~1"
            )
        except ValueError:
            diff_value = None
    if diff_value is not None:
        visible = tuple(
            change for change in diff_value.repositories if change.repository in graph.repositories
        )
        diff_value = replace(diff_value, repositories=visible)
    declared = insights.declarations(graph)
    mine = insights.owned(graph, declared)
    forks = insights.forks(graph)
    results = cache.results
    outdated = insights.outdated(mine, results)
    migration_rows, upgradable = migrations.split(outdated)
    vulnerable = insights.vulnerable(graph, declared, results)
    splits = insights.splits(
        mine, results, pins={name: pin.sha for name, pin in actions_rule.load_pins().items()}
    )
    drift = insights.drift(splits, upgradable)
    roles = insights.role_uses(dependency_roles.load_roles(), mine)
    owned_names = [name for name in graph.repositories if name not in forks]
    world_value = world.build(graph, owned_names, cache.sources, cache.mirror)
    return _Site(
        graph,
        inventory,
        inventory.entries,
        cache,
        cast(Mapping[str, Any], report_value),
        diff_value,
        tuple(index),
        time.time() if rendered_at is None else rendered_at,
        upgradable,
        migration_rows,
        vulnerable,
        drift,
        roles,
        insights.scorecards(
            [name for name in graph.repositories if name not in forks],
            outdated,
            vulnerable,
            drift,
            roles,
        ),
        forks,
        _triage(graph, vulnerable, outdated, forks),
        status,
        hidden,
        world_value,
        weight.build(graph, owned_names, cache.results, world_value),
        loc if loc is not None else loc_view.load(LOC_DATA),
        atlas.build(graph, hidden=hidden),
    )


def _triage(
    graph: Graph,
    vulnerable: Sequence[insights.Vulnerable],
    outdated: Sequence[insights.Outdated],
    forks: Sequence[str],
) -> tuple[triage.Action, ...]:
    unreadable = [
        name
        for name, data in graph.repositories.items()
        if data.state.value in ("failed", "unavailable")
    ]
    missing_locks = sorted(
        (
            name
            for name, data in graph.repositories.items()
            if name not in forks
            and any(issue.kind is CoverageKind.MISSING_LOCK for issue in data.issues)
        ),
        key=str.casefold,
    )
    return triage.actions(vulnerable, outdated, forks, unreadable, missing_locks, PYTHON_TOOL_NAMES)


def _page(site: _Site, title: str, page_id: str, prefix: str, body: str) -> str:
    active = "repositories" if page_id == "repository" else page_id
    stylesheets = (f"{prefix}assets/atlas.css",) if page_id == "explore" else ()
    return ui.shell(
        title, page_id, active, prefix, _navigation(site), body, search=page_id != "explore",
        stylesheets=stylesheets,
    )


def _navigation(site: _Site) -> tuple[NavGroup, ...]:
    return (
        NavGroup(
            "Main",
            (
                NavLink("index", "To do", len(site.actions)),
                NavLink("repositories", "Repositories"),
            ),
            heading=False,
        ),
        NavGroup("Overview", (NavLink("world", "World"), NavLink("explore", "Explore"))),
        NavGroup(
            "Review",
            (
                NavLink("security", "Security", len(_of_kind(site, ActionKind.SECURITY))),
                NavLink("outdated", "Upgrades", len(site.outdated)),
                NavLink("alignment", "Alignment", len(site.drift)),
                NavLink("choices", "Choices", len(_contested_roles(site))),
                NavLink("weight", "Weight"),
            ),
        ),
        NavGroup(
            "Inventory",
            (
                NavLink("coverage", "Coverage"),
                NavLink("changes", "Changes"),
                NavLink("packages", "Packages"),
                NavLink("lines", "Lines"),
            ),
        ),
    )


def _write_page(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_assets(output: Path, site: _Site) -> None:
    (output / "assets" / "ui-dashboard").mkdir(parents=True)
    for name in ("app.css", "app.js", "weight.js", "atlas.js", "atlas.css"):
        shutil.copyfile(ASSETS / name, output / "assets" / name)
    (output / "assets" / "vendor").mkdir()
    for item in sorted((ASSETS / "vendor").iterdir()):
        if item.is_file():
            shutil.copyfile(item, output / "assets" / "vendor" / item.name)
    (output / "assets" / "atlas-data.js").write_text(site.atlas, encoding="utf-8")
    for sheet in UI_SHEETS:
        shutil.copyfile(UI_DASHBOARD / sheet, output / "assets" / "ui-dashboard" / Path(sheet).name)
    template = (ASSETS / "search.js").read_text(encoding="utf-8")
    (output / "assets" / "search.js").write_text(
        template.replace("__DEPS_INDEX__", _json(list(site.index))), encoding="utf-8"
    )


def _of_kind(site: _Site, kind: ActionKind) -> list[triage.Action]:
    return [action for action in site.actions if action.kind is kind]


def _contested_roles(site: _Site) -> list[insights.RoleUse]:
    return [use for use in site.roles if use.overlapping or use.off_preferred]


def _checked(site: _Site) -> bool:
    return site.cache.fetched_at is not None


def _owned_count(site: _Site) -> int:
    return len(site.graph.repositories) - len(site.forks)


def _overview_tiles(site: _Site) -> tuple[Tile, ...]:
    checked = _checked(site)
    security = _of_kind(site, ActionKind.SECURITY)
    blocked = sum(1 for action in security if action.blocked)
    affected = len({name for action in security for name in action.repositories})
    locks = _of_kind(site, ActionKind.LOCKFILE)
    missing = len(locks[0].repositories) if locks else 0
    contested = _contested_roles(site)
    off_preferred = len({name for use in contested for name in use.off_preferred})
    return (
        Tile(
            str(len(security)) if checked else "—",
            "Security",
            f"{_plural(affected, 'repository', 'repositories')} · {blocked} with no clean upgrade"
            if checked
            else "not checked",
            "security.html",
            Tone.BAD if security else None,
        ),
        Tile(
            str(len(site.outdated)) if checked else "—",
            "Upgrades",
            "direct dependencies behind" if checked else "not checked",
            "outdated.html",
            None,
        ),
        Tile(
            str(missing),
            "No lockfile",
            "repositories with unknown versions",
            "coverage.html",
            Tone.WARN if missing else None,
        ),
        Tile(str(len(site.drift)), "Version drift", "packages upgrades will not align", "alignment.html"),
        Tile(
            str(len(contested)),
            "Role conflicts",
            f"{_plural(off_preferred, 'repository', 'repositories')} off preferred",
            "choices.html",
        ),
    )


def _fork_exposure(site: _Site) -> dict[str, int]:
    exposure = dict.fromkeys(site.forks, 0)
    for row in site.vulnerable:
        for repository in {*row.direct_in, *row.transitive_in}:
            if repository in exposure:
                exposure[repository] += 1
    return exposure


def _plural(count: int, noun: str, plural: str | None = None) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {plural or noun + 's'}"


def _short_ref(version: str) -> str:
    if "@sha256:" in version:
        tag, digest = version.split("@sha256:", 1)
        return f"{tag}@sha256:{digest[:12]}…"
    if len(version) == 40 and all(character in "0123456789abcdef" for character in version):
        return version[:12]
    return version


def _display_name(site: _Site, purl: str) -> str:
    component = site.graph.components.get(purl)
    return component.display_name if component is not None else purl


def _package_section(site: _Site, purl: str) -> str:
    component = site.graph.components[purl]
    instances = sorted(
        (item for item in site.graph.instances.values() if item.component == purl),
        key=lambda item: (item.version or "", item.id),
    )
    consumers = [
        (repository, edge)
        for instance in instances
        for repository in sorted(site.graph.instance_repositories.get(instance.id, ()))
        for edge in site.graph.incoming.get((repository, instance.id), ())
    ]
    identity = (
        f'<div class="package-identity"><span class="mono">{_e(purl)}</span>'
        f"{ui.copy_button(purl)}<span>{_e(component.ecosystem.value)}</span></div>"
    )
    versions = ui.static_table(
        (Column("Version", mono=True), Column("Source", wrap=True), Column("Registry", wrap=True)),
        [
            (_e(instance.version or "unknown"), _source_label(instance), _enrichment_cell(site, instance))
            for instance in instances
        ],
        label="Versions",
    )
    used_by = (
        ui.static_table(
            (Column("Repository"), Column("From", wrap=True, mono=True), Column("Relation"), Column("Scope")),
            [
                (
                    _repo_link(repository, ""),
                    _e(_edge_label(site.graph, edge)),
                    _e(edge.relation.value),
                    _e(edge.scope.value),
                )
                for repository, edge in consumers[:_CONSUMER_ROWS]
            ],
            label="Used by",
        )
        if consumers
        else '<p class="zero">no consumers</p>'
    )
    meta = f"showing {_CONSUMER_ROWS} of {len(consumers)}" if len(consumers) > _CONSUMER_ROWS else ""
    heading = f"Used by · {meta}" if meta else "Used by"
    return (
        f'<section class="package" data-purl="{_e(purl)}">'
        f"{ui.page_header(component.display_name)}{identity}"
        f"{ui.panel('Versions', f'{versions}<div class="package-heading">{heading}</div>{used_by}', flush=True)}"
        "</section>"
    )


def _change_group(title: str, items: Sequence[str]) -> str:
    if not items:
        return ""
    rendered = "".join(f"<li>{item}</li>" for item in items)
    return f'<div class="change-group">{title}</div><ul class="plain-list">{rendered}</ul>'


_KNOWN_LIMITS = {
    CoverageKind.UNSUPPORTED_FORMAT: "files in formats with no parser",
    CoverageKind.DYNAMIC_VALUE: "computed versions",
    CoverageKind.VENDORED_UNKNOWN: "vendored trees with no manifest",
    CoverageKind.SUBMODULE: "submodules not inspected",
}
_CHECKOUT_KINDS = frozenset(
    {
        CoverageKind.CHECKOUT_MISSING,
        CoverageKind.ORIGIN_MISMATCH,
        CoverageKind.DEFAULT_REF_MISSING,
        CoverageKind.GIT_FAILURE,
    }
)
_COVERAGE_ACTIONS = {
    CoverageKind.CHECKOUT_MISSING: ("No checkout", "Run `repomod sync`, or fix the path in the catalog."),
    CoverageKind.ORIGIN_MISMATCH: ("Wrong remote", "Fix the remote or the catalog entry, then re-sync."),
    CoverageKind.DEFAULT_REF_MISSING: ("Default branch missing", "Fetch the default branch and set `origin/HEAD`."),
    CoverageKind.GIT_FAILURE: ("Git read failed", "Run the git command in that checkout to see the raw error."),
    CoverageKind.PARSE_ERROR: ("File does not parse", "Fix the syntax. The repository page links the file."),
    CoverageKind.LOCK_MISMATCH: ("Manifest and lock disagree", "Regenerate the lockfile and commit it."),
    CoverageKind.MISSING_LOCK: ("No lockfile", "Generate the lockfile for the ecosystem in use and commit it."),
    CoverageKind.SYMLINK_SKIPPED: ("Symlinked file skipped", "Replace the symlink with the real file."),
    CoverageKind.NON_UTF8: ("Not UTF-8 text", "Convert the file to UTF-8."),
}


def _state_badge(data: RepositoryData) -> str:
    value = data.state.value
    tone = {"complete": Tone.OK, "partial": Tone.NEUTRAL}.get(value, Tone.BAD)
    return ui.badge(value, tone, dot=True)


def _overview(site: _Site) -> str:
    security = _of_kind(site, ActionKind.SECURITY)
    body = [
        ui.page_header(
            "To do",
            f"{_owned_count(site)} repositories · {_enrichment_stamp(site)} · {_changes_line(site)}",
        ),
        ui.status_strip(_overview_tiles(site)),
    ]
    if not _checked(site):
        body.append(
            ui.notice(
                'Vulnerabilities and upgrades are not checked yet. Run '
                '<span class="mono">uv run repomod deps enrich</span>, then render again.',
                Tone.WARN,
            )
        )
    if not site.actions:
        body.append(
            ui.panel(
                "Next",
                ui.empty_state(
                    "Nothing to fix",
                    "No vulnerabilities, unreadable checkouts, missing lockfiles, or pending upgrades.",
                ),
                flush=True,
            )
        )
    else:
        body.append(_work_panel(site))
        body.extend(_security_groups(security))
        body.append(_command_group(site))
    exposed = sum(1 for count in _fork_exposure(site).values() if count)
    if exposed:
        body.append(
            ui.notice(
                f"{len(site.forks)} forks keep upstream's dependency choices and are left out of "
                f'this list. <a href="security.html#forks">{exposed} carry vulnerable versions</a>.'
            )
        )
    return "\n".join(body)


def _work_parts(card: insights.Scorecard) -> tuple[Segment, ...]:
    return (
        Segment("Vulnerable", card.vulnerable, Mark.BAD),
        Segment("Upgrades", card.behind, Mark.GHOST),
    )


def _work_total(card: insights.Scorecard) -> int:
    return sum(part.value for part in _work_parts(card))


_WORK_LEGEND = (("Vulnerable", Mark.BAD), ("Upgrades", Mark.GHOST))


def _work_panel(site: _Site) -> str:
    working = [card for card in site.scorecards if _work_total(card)]
    cards = working[:_PREVIEW_ROWS]
    shown = (
        f"{len(cards)} of {len(working)} repositories with work · "
        if len(working) > len(cards)
        else f"{_plural(len(cards), 'repository', 'repositories')} with work · "
    )
    scale = max((_work_total(card) for card in cards), default=0)
    bars = [
        Bar(
            f'<a href="repos/{_e(card.repository)}/index.html">{_e(_short_repository(card.repository))}</a>',
            _work_parts(card),
        )
        for card in cards
    ]
    return ui.panel(
        "Where the work is",
        ui.legend(_WORK_LEGEND) + ui.bar_list(bars, scale, "Open work by repository"),
        meta=f'{shown}<a href="repositories.html">all repositories</a>',
    )


def _security_groups(actions: Sequence[triage.Action]) -> list[str]:
    ready = [action for action in actions if not action.blocked]
    blocked = [action for action in actions if action.blocked]
    groups = []
    if ready:
        groups.append(
            ui.group(
                "Fix now",
                ui.card_grid(_security_card(action) for action in ready),
                count=len(ready),
                note="Vulnerable, with a clean upgrade available",
            )
        )
    if blocked:
        groups.append(
            ui.group(
                "Decide",
                ui.card_grid(_security_card(action) for action in blocked),
                count=len(blocked),
                note="Vulnerable, with no clean upgrade. Replace the package or accept the risk.",
            )
        )
    return groups


def _security_card(action: triage.Action) -> str:
    if action.purl is None:
        raise ValueError(f"security action has no package: {action.subject}")
    return ui.card(
        _package_link(action.purl, "", action.subject),
        f'<div class="card-change">{_e(action.change)}</div>'
        f'<div class="card-foot">{_repository_names(action.repositories)} · {_e(action.step)}</div>',
        meta=ui.badge(_advisories_label(len(action.details)), Tone.BAD if not action.blocked else Tone.WARN),
    )


def _advisories_label(count: int) -> str:
    return f"{count} advisory" if count == 1 else f"{count} advisories"


def _repository_names(repositories: Sequence[str], prefix: str = "") -> str:
    shown = ", ".join(
        f'<a href="{prefix}repos/{_e(name)}/index.html">{_e(_short_repository(name))}</a>'
        for name in repositories[:_SHOWN_REPOSITORIES]
    )
    hidden = repositories[_SHOWN_REPOSITORIES:]
    if not hidden:
        return shown
    rest = ", ".join(
        f'<a href="{prefix}repos/{_e(name)}/index.html">{_e(_short_repository(name))}</a>' for name in hidden
    )
    return f"{shown} <details><summary>+{len(hidden)} more</summary>{rest}</details>"


def _short_repository(name: str) -> str:
    return name.rsplit("/", 1)[-1]


def _command_group(site: _Site) -> str:
    actions = [
        action
        for action in site.actions
        if action.kind
        in (ActionKind.UNREADABLE, ActionKind.LOCKFILE, ActionKind.TOOLING, ActionKind.MIGRATE, ActionKind.ROUTINE)
    ]
    if not actions:
        return ""
    return ui.group(
        "Clear in one pass",
        ui.card_grid((_command_card(action) for action in actions), wide=True),
        count=len(actions),
        note="Each of these is one task across many repositories",
    )


def _command_card(action: triage.Action) -> str:
    label, tone = _KIND_LABELS[action.kind]
    command = (
        f'<div class="command-line"><code>{_e(action.command)}</code>{ui.copy_button(action.command)}</div>'
        if action.command is not None
        else f'<div class="card-change">{_e(action.step)}</div>'
    )
    return ui.card(
        f"<span>{_e(action.subject)}</span>",
        f'{command}<div class="card-foot">{_plural(len(action.repositories), "repository", "repositories")}: '
        f"{_repository_names(action.repositories)}</div>",
        meta=ui.badge(label, tone, dot=True),
    )


def _tier(card: insights.Scorecard) -> str:
    if card.vulnerable:
        return "Vulnerable"
    if any(card.rank):
        return "Maintenance"
    return _CLEAN_TIER


def _plural_if(count: int, noun: str) -> str:
    return "" if not count else _plural(count, noun)


def _repository_chip(name: str, count: int) -> str:
    return ui.chip_link(_short_repository(name), f"repos/{name}/index.html", count, tip=name)


def _security(site: _Site) -> str:
    actions = _of_kind(site, ActionKind.SECURITY)
    blocked = sum(1 for action in actions if action.blocked)
    by_repository: dict[str, list[triage.Action]] = defaultdict(list)
    for action in actions:
        for repository in action.repositories:
            by_repository[repository].append(action)
    body = [ui.page_header("Security", f"Known vulnerable versions, by repository · {_enrichment_stamp(site)}")]
    if actions:
        body.append(
            ui.status_strip(
                (
                    Tile(str(len(actions)), "Packages", "with known advisories", "#repositories", Tone.BAD),
                    Tile(str(len(by_repository)), "Repositories", "need a change", "#repositories"),
                    Tile(
                        str(blocked),
                        "No clean upgrade",
                        "replace or accept",
                        "#repositories",
                        Tone.WARN if blocked else None,
                    ),
                )
            )
        )
        ordered = sorted(by_repository.items(), key=lambda item: (-len(item[1]), item[0].casefold()))
        body.append(
            ui.group(
                "Your repositories",
                ui.card_grid(_security_repository_card(name, items) for name, items in ordered),
                count=len(ordered),
                group_id="repositories",
            )
        )
    elif _checked(site):
        body.append(ui.panel("Your repositories", ui.empty_state("No known vulnerabilities"), flush=True))
    else:
        body.append(ui.panel("Your repositories", '<p class="unknown">not checked</p>', flush=True))
    body.append(_forks_panel(site))
    return "\n".join(body)


def _security_repository_card(name: str, actions: Sequence[triage.Action]) -> str:
    lines = [
        Line(
            _package_link(action.purl, "", action.subject) if action.purl is not None else _e(action.subject),
            f"{_e(action.change)} · {_e(action.step)}",
            ui.badge("Blocked", Tone.WARN) if action.blocked else "",
            ", ".join(action.details),
        )
        for action in actions
    ]
    return ui.card(
        f'<a href="repos/{_e(name)}/index.html">{_e(_short_repository(name))}</a>',
        ui.lines(lines),
        meta=ui.badge(_plural(len(actions), "package"), Tone.BAD),
    )


def _outdated(site: _Site) -> str:
    body = [ui.page_header("Upgrades", f"Direct dependencies behind the registry · {_enrichment_stamp(site)}")]
    if site.migrations:
        body.append(_migrations_panel(site))
    if not site.outdated:
        message = (
            (
                '<p class="zero">nothing left to upgrade; the migration candidates above supersede release bumps</p>'
                if site.migrations
                else '<p class="zero">every checked direct dependency is on its latest release</p>'
            )
            if _checked(site)
            else '<p class="unknown">not checked</p>'
        )
        body.append(ui.panel("Upgrades", message, flush=True))
        return "\n".join(body)
    counts = Counter(row.component.ecosystem for row in site.outdated)
    by_ecosystem = " · ".join(
        f"{count} {ecosystem.value}"
        for ecosystem, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].value))
    )
    body.append(
        ui.notice(
            f'Apply upgrades with <span class="mono">{triage.ROUTINE_COMMAND}</span>, which '
            "opens one pull request per repository."
        )
    )
    rows = "".join(_upgrade_row(row) for row in site.outdated)
    body.append(
        ui.panel(
            "Upgrades",
            ui.scope(f'<ul class="todo-columns upgrade-list">{rows}</ul>', search="Filter upgrades"),
            meta=f"{len(site.outdated)} direct dependencies · {by_ecosystem} · most repositories first",
            panel_id="upgrades",
        )
    )
    return "\n".join(body)


def _migrations_panel(site: _Site) -> str:
    cards = []
    for migration, row in site.migrations:
        versions = ", ".join(use.version for use in row.uses)
        target = migration.target or "remove"
        change = f"{versions} → {target}"
        names = sorted({name for use in row.uses for name in use.repositories}, key=str.casefold)
        foot = f"{_plural(row.repositories, 'repository', 'repositories')}: {_repository_names(names)}"
        command = (
            f'<div class="command-line"><code>{_e(migration.command)}</code>{ui.copy_button(migration.command)}</div>'
            if migration.command is not None
            else f'<div class="card-foot">{_e(migration.reason)}</div>'
        )
        cards.append(
            ui.card(
                _package_link(row.component.purl, "", row.component.display_name),
                f'<div class="card-change">{_e(change)}</div>'
                f'{command}<div class="card-foot">{foot}</div>',
                meta=ui.badge("Migrate", Tone.NEUTRAL, dot=True),
            )
        )
    return ui.group(
        "Migrate, don't bump",
        ui.card_grid(cards, wide=True),
        count=len(cards),
        note="The fleet replaces these; a release bump is not the fix",
        group_id="migrate",
    )


def _upgrade_row(row: insights.Outdated) -> str:
    versions = ", ".join(use.version for use in row.uses)
    names = sorted({_short_repository(name) for use in row.uses for name in use.repositories}, key=str.casefold)
    return (
        f"<li data-item>{_package_link(row.component.purl, '', row.component.display_name)} "
        f'<span class="line-detail">{_e(versions)} → {_e(row.latest)}</span>'
        f'<div class="line-detail">{_e(", ".join(names))}</div></li>'
    )


def _alignment(site: _Site) -> str:
    header = ui.page_header("Alignment", "Version drift that upgrading will not fix. Upgrades covers the rest.")
    if not site.drift:
        return header + ui.panel(
            "Version drift",
            '<p class="zero">no drift is left once pending upgrades are applied</p>',
            flush=True,
        )
    rows = sorted(site.drift, key=lambda row: (-len(set(row.off_target)), row.component.name.casefold()))
    return "\n".join(
        (
            header,
            ui.panel(
                "Version drift",
                ui.scope(
                    f'<ul class="change-list">{"".join(_drift_row(row) for row in rows)}</ul>', search="Filter packages"
                ),
                meta=f"{_plural(len(rows), 'package')} · most repositories off target first",
                flush=True,
            ),
        )
    )


def _lane_label(version: str) -> str:
    if "@sha256:" in version:
        tag, digest = version.split("@sha256:", 1)
        return f"{tag}@{digest[:7]}"
    if len(version) == 40 and all(character in "0123456789abcdef" for character in version):
        return version[:7]
    return version


def _weight(site: _Site) -> str:
    return (
        weight_view.page(
            site.package_weight, lambda purl, text: _package_link(purl, "", text), _duplicate_panel(site)
        )
        + '\n<script src="assets/weight.js"></script>'
    )


def _lines(site: _Site) -> str:
    return loc_view.page(site.code, site.forks, sorted(site.hidden))


def _duplicate_panel(site: _Site) -> str:
    duplicates = sorted(
        ((name, found) for name, data in site.graph.repositories.items() if (found := _duplicates(site, data))),
        key=lambda item: (-len(item[1]), item[0].casefold()),
    )
    widest = max((len(found) for _name, found in duplicates), default=0)
    return ui.collapsed_panel(
        "Duplicate versions",
        ui.scope(
            ui.bar_list(
                [_duplicate_bar(site, name, found) for name, found in duplicates],
                widest,
                "Duplicate versions",
            ),
            limit=_LIST_ROWS,
            total=len(duplicates),
        )
        if duplicates
        else '<p class="zero">no repository carries two versions of one package</p>',
        meta="Both versions are built",
    )


def _duplicate_bar(site: _Site, name: str, found: Sequence[tuple[str, list[str]]]) -> Bar:
    items = "".join(
        f"<li>{_package_link(purl, '', _display_name(site, purl))} "
        f'<span class="mono">{_e(", ".join(versions))}</span></li>'
        for purl, versions in found
    )
    return Bar(
        f'<a href="repos/{_e(name)}/index.html">{_e(_short_repository(name))}</a>',
        (Segment("Packages", len(found), Mark.ACCENT),),
        tail=f'<details class="ui-disclosure"><summary class="ui-disclosure-summary">Packages</summary>'
        f'<div class="ui-disclosure-body"><ul class="plain-list">{items}</ul></div></details>',
    )


_RISK_CATEGORIES = (
    ("git_sources", "Git sources", "A git ref can move or disappear; a registry is stable."),
    ("unpinned_actions", "Unpinned Actions", "A moving tag can change what CI runs."),
    ("floating_images", "Floating image tags", "A tag can point at a new image."),
    ("missing_locks", "Missing locks", "Dependencies can resolve differently over time."),
    ("unpinned_artifacts", "Unpinned artifacts", "A download can change without a version or checksum."),
    ("vendored", "Vendored code", "A vendored tree has no manifest to track its versions."),
)


def _risk_section(site: _Site) -> str:
    details = _table(_table(site.report["source_risk"]).get("details"))
    cards: list[str] = []
    counts: list[tuple[str, int]] = []
    for key, title, note in _RISK_CATEGORIES:
        items = details.get(key)
        if not isinstance(items, (tuple, list)) or not items:
            continue
        kept = _without_forks(site, key, items)
        if not kept:
            continue
        lines = _risk_lines(site, key, kept)
        if not lines:
            continue
        counts.append((title, len(lines)))
        cards.append(_risk_row(title, note, lines))
    if not cards:
        return ui.panel("Source risk", ui.empty_state("No source risk"), flush=True)
    return ui.panel(
        "Source risk",
        f'<ul class="change-list">{"".join(cards)}</ul>',
        meta=f"{_plural(sum(value for _label, value in counts), 'source')} that can change without a new commit",
        flush=True,
    )


def _without_forks(site: _Site, key: str, items: Sequence[object]) -> list[object]:
    if not site.forks:
        return list(items)
    if key == "missing_locks":
        return [
            item
            for item in items
            if not (isinstance(item, Mapping) and item.get("repository") in site.forks)
        ]
    return [
        item
        for item in items
        if isinstance(item, str)
        and any(
            repository not in site.forks
            for repository in site.graph.instance_repositories.get(item, ())
        )
    ]


def _risk_row(title: str, note: str, lines: Sequence[Line]) -> str:
    """One kind of source risk: what it is and why it matters, then every item, without a badge per item."""
    items = "".join(
        f'<li data-item>{line.primary} <span class="line-detail">{line.detail}</span></li>' for line in lines
    )
    body = f'<ul class="plain-list">{items}</ul>'
    if len(lines) > _LIST_ROWS:
        body = ui.scope(body, limit=_LIST_ROWS, total=len(lines))
    return (
        f'<li class="change-repo"><div><h3 class="row-title">{_e(title)} · {len(lines)}</h3>'
        f'<div class="note">{_e(note)}</div></div><div>{body}</div></li>'
    )

def _risk_lines(site: _Site, key: str, items: Sequence[object]) -> list[Line]:
    if key == "missing_locks":
        return _missing_lock_lines(items)
    return _instance_risk_lines(site, items)


def _instance_risk_lines(site: _Site, items: Sequence[object]) -> list[Line]:
    instances = [
        instance
        for item in items
        if isinstance(item, str) and (instance := site.graph.instances.get(item)) is not None
    ]
    instances.sort(key=lambda instance: (instance.purl.casefold(), instance.version or ""))
    return [_instance_risk_line(site, instance) for instance in instances]


def _instance_risk_line(site: _Site, instance: Instance) -> Line:
    component = site.graph.components.get(instance.component)
    name = component.display_name if component is not None else instance.component
    version = f"@{instance.version}" if instance.version is not None else ""
    repositories = sorted(
        (
            name
            for name in site.graph.instance_repositories.get(instance.id, ())
            if name not in site.forks
        ),
        key=str.casefold,
    )
    source = _risk_source(instance)
    detail = source + (" · " + _repository_names(repositories) if repositories else "")
    return Line(_package_link(instance.purl, "", f"{name}{version}"), detail, tip=source)


def _missing_lock_lines(items: Sequence[object]) -> list[Line]:
    locks: list[tuple[str, Mapping[str, object]]] = []
    for item in items:
        if isinstance(item, Mapping):
            name = item.get("repository")
            if isinstance(name, str):
                locks.append((name, cast(Mapping[str, object], item)))
    locks.sort(key=lambda entry: (entry[0].casefold(), str(entry[1].get("path") or "")))
    lines: list[Line] = []
    for name, item in locks:
        path = item.get("path")
        message = item.get("message")
        detail = _e(path) if isinstance(path, str) and path else _e(str(message or ""))
        lines.append(
            Line(
                f'<a href="repos/{_e(name)}/index.html">{_e(_short_repository(name))}</a>',
                detail,
                tip=name,
            )
        )
    return lines


def _risk_source(instance: Instance) -> str:
    if instance.source_kind is SourceKind.GIT:
        if instance.commit is not None:
            return f"commit {_lane_label(instance.commit)}"
        if instance.vcs_url is not None:
            return instance.vcs_url
        return "git source"
    if instance.source_kind is SourceKind.VENDORED:
        return "vendored tree"
    if instance.source_kind is SourceKind.URL:
        url = _download_url(instance.purl)
        return url if url is not None else "download"
    if instance.source_kind is SourceKind.IMAGE:
        return f"tag {instance.version or 'latest'}"
    if instance.version is not None:
        return f"ref {instance.version}"
    return instance.source_kind.value


def _download_url(purl: str) -> str | None:
    values = parse_qs(urlsplit(purl).query).get("download_url")
    return values[0] if values is not None else None


def _todo_panel(site: _Site, name: str) -> str:
    sections = _repository_todo(site, name)
    if not sections:
        return ui.panel("To do here", '<p class="zero">nothing flagged</p>', panel_id="todo", flush=True)
    body = "".join(
        f'<section class="todo-section"><div class="change-group">{_e(title)} · {len(lines)}</div>'
        '<ul class="todo-columns">'
        + "".join(f'<li>{line.primary} <span class="line-detail">{line.detail}</span></li>' for line in lines)
        + "</ul></section>"
        for title, _tone, lines in sections
    )
    return ui.panel(
        "To do here",
        body,
        meta=_plural(sum(len(lines) for _title, _tone, lines in sections), "item"),
        panel_id="todo",
    )


def _repository_todo(site: _Site, name: str) -> list[tuple[str, Tone, list[Line]]]:
    prefix = "../../../"
    data = site.graph.repositories[name]
    entry = site.entries.get(name)
    commit = entry.commit if entry is not None else None
    coverage = [
        Line(
            _evidence_path(name, commit, issue.path) or _e(_COVERAGE_ACTIONS[issue.kind][0]),
            f"{_e(_COVERAGE_ACTIONS[issue.kind][0])} · {_e(issue.message)}",
        )
        for issue in sorted(_actionable_issues(site, name, data), key=lambda item: (item.path or "", item.kind.value))
    ]
    security = [
        Line(
            _package_link(row.component.purl, prefix, f"{row.component.display_name}@{row.version}"),
            f"{'declared' if name in row.direct_in else 'locked'} · {_advisories_label(len(row.advisories))}",
            tip=", ".join(row.advisories),
        )
        for row in site.vulnerable
        if name in row.direct_in or name in row.transitive_in
    ]
    upgrades: list[Line] = []
    behind: set[str] = set()
    migrated: list[Line] = []
    for row in site.outdated:
        for use in row.uses:
            if name not in use.repositories:
                continue
            behind.add(row.component.purl)
            upgrades.append(
                Line(
                    _package_link(row.component.purl, prefix, row.component.display_name),
                    f"{_e(use.version)} → {_e(row.latest)}",
                )
            )
    for migration, row in site.migrations:
        for use in row.uses:
            if name not in use.repositories:
                continue
            target = migration.target or "remove"
            migrated.append(
                Line(
                    _package_link(row.component.purl, prefix, row.component.display_name),
                    f"{_e(use.version)} → {_e(target)}",
                )
            )
    drift = [
        Line(
            _package_link(split.component.purl, prefix, split.component.display_name),
            f"{_e(_short_ref(next(use.version for use in split.uses if name in use.repositories)))} → "
            f"{_e(_short_ref(split.target))}",
        )
        for split in site.drift
        if name in split.off_target and split.component.purl not in behind
    ]
    roles = [
        Line(
            f'<a href="{prefix}choices.html#role-{_e(use.role.name)}">{_e(use.role.name)}</a>',
            f"uses {_e(', '.join(option for option, owners in use.options.items() if name in owners))}"
            + (f" · preferred {_e(use.role.preferred)}" if use.role.preferred is not None else ""),
        )
        for use in site.roles
        if name in use.overlapping or name in use.off_preferred
    ]
    return [
        (title, tone, lines)
        for title, tone, lines in (
            ("Security", Tone.BAD, security),
            ("Coverage", Tone.WARN, coverage),
            ("Migrate", Tone.NEUTRAL, migrated),
            ("Role conflicts", Tone.NEUTRAL, roles),
            ("Version drift", Tone.NEUTRAL, drift),
            ("Upgrades", Tone.NEUTRAL, upgrades),
        )
        if lines
    ]


def _repositories(site: _Site) -> str:
    scale = max((_work_total(card) for card in site.scorecards), default=0)
    tiers: dict[str, list[insights.Scorecard]] = defaultdict(list)
    for card in site.scorecards:
        tiers[_tier(card)].append(card)
    for cards in tiers.values():
        cards.sort(key=lambda card: -_failing(site, card.repository))
    panels = [
        ui.panel(
            title,
            f'<ul class="change-list">{"".join(_repository_row(site, card, scale) for card in tiers[title])}</ul>',
            meta=f"{_plural(len(tiers[title]), 'repository', 'repositories')} · {note}",
            flush=True,
        )
        for title, note in (*_TIERS, (_CLEAN_TIER, "nothing to upgrade or align"))
        if tiers[title]
    ]
    exposure = _fork_exposure(site)
    exposed = sorted(
        (name for name in site.forks if exposure[name]), key=lambda item: (-exposure[item], item.casefold())
    )
    if exposed:
        panels.append(
            ui.panel(
                "Forks with vulnerable versions",
                ui.chip_links(_repository_chip(name, exposure[name]) for name in exposed),
                meta="tracked only; vulnerable packages per fork",
            )
        )
    collected = (
        ""
        if site.status is not None
        else ui.notice(
            "CI, releases, upstreams, and checkouts are not collected. Run "
            '<span class="mono">make deps</span> to include them.'
        )
    )
    return "\n".join(
        (
            ui.page_header(
                "Repositories",
                f"{_owned_count(site)} repositories · {len(tiers[_CLEAN_TIER])} clean · "
                f"{len(site.forks)} forks · {_enrichment_stamp(site)}"
                + (f" · {len(site.hidden)} private hidden" if site.hidden else ""),
            ),
            collected,
            ui.legend(_WORK_LEGEND, "open work per repository, one scale"),
            ui.scope("".join(panels), search="Filter repositories"),
        )
    )


def _failing(site: _Site, name: str) -> int:
    """How many of a repository's status checks are failing; a broken build ranks it first in its tier."""
    items = site.status.get(name, ()) if site.status is not None else ()
    return sum(1 for item in items if item.level is StatusLevel.FAILING)


def _repository_row(site: _Site, card: insights.Scorecard, scale: int) -> str:
    roles = len({*card.mixed_roles, *card.off_preferred})
    work = " · ".join(
        part
        for part in (
            _plural_if(card.vulnerable, "vulnerable package"),
            _plural_if(card.behind, "upgrade"),
            f"{card.off_target} off target" if card.off_target else "",
            _plural_if(roles, "role conflict"),
        )
        if part
    )
    items = site.status.get(card.repository, ()) if site.status is not None else ()
    status = _status_lines(items) if items else '<p class="note">nothing flagged</p>'
    bar = ui.segments(_work_parts(card), scale) if _work_total(card) else ""
    return (
        f'<li class="change-repo" data-item data-row data-href="repos/{_e(card.repository)}/index.html"><div>'
        f'<a href="repos/{_e(card.repository)}/index.html">{_e(card.repository)}</a>'
        f'<div class="note">{_e(work) or "clean"}</div>{bar}</div><div>{status}</div></li>'
    )


_HEX_ID = re.compile(r"\b([0-9a-f]{12})[0-9a-f]{28}\b")
_CACHED = re.compile(r"\(?cached (\d+)s\)?")
_RUN_STATES = {"RUN": "running", "FAIL": "failed", "PASS": "passed"}


def _age(seconds: int) -> str:
    if seconds < 120:
        return f"{seconds}s"
    if seconds < 7200:
        return f"{seconds // 60} min"
    if seconds < 172_800:
        return f"{seconds // 3600} h"
    return f"{seconds // 86_400} d"


def _status_text(label: str) -> str:
    """A status label from `repomod status` made readable: short commit ids, plain states and ages."""
    text = _HEX_ID.sub(lambda match: match.group(1), label)
    text = _CACHED.sub(lambda match: f"checked {_age(int(match.group(1)))} ago", text)
    state, _, rest = text.partition(" ")
    if state in _RUN_STATES and rest:
        text = f"{rest} {_RUN_STATES[state]}"
    return " ".join(text.split()).replace(" · checked", ", checked")


def _status_lines(items: Sequence[StatusItem]) -> str:
    areas: dict[str, list[StatusItem]] = defaultdict(list)
    for item in items:
        areas[item.area.value].append(item)
    rows = []
    for area, grouped in areas.items():
        worst = max(grouped, key=lambda item: _STATUS_RANK[item.level])
        rows.append(
            f"<dt>{ui.state(area, _STATUS_TONES[worst.level], running=any(item.running for item in grouped))}</dt>"
            f"<dd>{' · '.join(_status_label(item) for item in grouped)}</dd>"
        )
    return f'<dl class="status-rows">{"".join(rows)}</dl>'


def _status_label(item: StatusItem) -> str:
    text = _e(_status_text(item.label))
    if item.url is None or not item.url.startswith("https://"):
        return text
    return f'<a href="{_e(item.url)}">{text}</a>'


def _repository_status_panel(site: _Site, name: str) -> str:
    if site.status is None:
        return ""
    items = site.status.get(name, ())
    return ui.panel(
        "Status",
        _status_lines(items) if items else '<p class="zero">nothing flagged</p>',
        panel_id="status",
    )


def _forks_panel(site: _Site) -> str:
    exposure: dict[str, list[str]] = {name: [] for name in site.forks}
    for row in site.vulnerable:
        for repository in {*row.direct_in, *row.transitive_in}:
            if repository in exposure:
                exposure[repository].append(f"{row.component.display_name}@{row.version}")
    exposed = sorted(
        (name for name in site.forks if exposure[name]), key=lambda item: (-len(exposure[item]), item.casefold())
    )
    if not exposed:
        return ""
    chips = ui.chip_links(
        ui.chip_link(
            _short_repository(name),
            f"repos/{name}/index.html",
            len(exposure[name]),
            tip=", ".join(sorted(exposure[name])),
        )
        for name in exposed
    )
    return ui.collapsed_panel(
        "Forks",
        chips,
        meta=f"{len(exposed)} of {len(site.forks)} carry vulnerable versions",
        panel_id="forks",
    )


_TARGET_BASIS = {
    insights.TargetBasis.APPROVED_PIN: "approved pin",
    insights.TargetBasis.LATEST: "latest release",
    insights.TargetBasis.NEWEST_IN_USE: "newest in use; latest release not confirmed",
    insights.TargetBasis.MOST_COMMON: "most common ref; latest release not confirmed",
}


def _drift_row(row: insights.Split) -> str:
    """One package: the target first, then every other version with the repositories on it."""
    target = next((use for use in row.uses if use.version == row.target), insights.VersionUse(row.target, ()))
    others = sorted(
        (use for use in row.uses if use.version != row.target), key=lambda use: (-len(use.repositories), use.version)
    )
    def version_line(use: insights.VersionUse, tone: Tone, label: str) -> str:
        names = _e(", ".join(sorted((_short_repository(name) for name in use.repositories), key=str.casefold)))
        return (
            f'<li>{ui.state(_lane_label(use.version), tone)} <span class="line-detail">{label}'
            f"{' · ' + names if names else ''}</span></li>"
        )
    versions = version_line(target, Tone.OK, "target") + "".join(
        version_line(use, Tone.NEUTRAL, "move") for use in others
    )
    off_target = len(set(row.off_target))
    return (
        f'<li class="change-repo" data-item><div>{_package_link(row.component.purl, "", row.component.display_name)}'
        f'<div class="note">{_e(row.component.ecosystem.value)} · {_plural(off_target, "repository", "repositories")} '
        f"off target · target is the {_TARGET_BASIS[row.basis]}</div></div>"
        f'<ul class="plain-list">{versions}</ul></li>'
    )


def _choices(site: _Site) -> str:
    contested = _contested_roles(site)
    in_use = sum(1 for use in site.roles if use.in_use)
    body = [
        ui.page_header(
            "Choices",
            f"{len(contested)} roles need a change · {in_use - len(contested)} settled · forks left out",
        )
    ]
    if contested:
        ordered = sorted(
            contested,
            key=lambda item: (-len(item.off_preferred), -len(item.overlapping), item.role.name.casefold()),
        )
        body.append(
            ui.panel(
                "Roles to settle",
                ui.scope(
                    f'<ul class="change-list">{"".join(_role_row(use) for use in ordered)}</ul>',
                    search="Filter roles",
                ),
                meta="most repositories off the preferred option first",
                flush=True,
            )
        )
    else:
        body.append(ui.panel("Choices", ui.empty_state("Nothing to change"), flush=True))
    return "\n".join(body)


def _role_row(use: insights.RoleUse) -> str:
    preferred = use.role.preferred
    options = sorted(use.in_use, key=lambda option: (option != preferred, -len(use.options[option]), option))
    if preferred is not None and preferred not in options:
        options.insert(0, preferred)
    pressure = " · ".join(
        label
        for count, label in (
            (len(use.off_preferred), f"{len(use.off_preferred)} off preferred"),
            (len(use.overlapping), f"{len(use.overlapping)} mixed"),
        )
        if count
    )
    action = f"move to {preferred}" if preferred is not None else "pick one option"
    return (
        f'<li class="change-repo" data-item id="role-{_e(use.role.name)}"><div>'
        f'<h3 class="row-title">{_e(use.role.name)}</h3>'
        f'<div class="note">{_e(use.role.ecosystem.value)} · {_e(pressure)} · {_e(action)}</div></div>'
        f'<ul class="plain-list">{"".join(_role_option(use, option) for option in options)}</ul></li>'
    )


def _role_option(use: insights.RoleUse, option: str) -> str:
    repositories = sorted(use.options.get(option, ()), key=str.casefold)
    if option == use.role.preferred:
        tone, label = Tone.OK, "preferred"
    elif option in use.role.bans:
        tone, label = Tone.BAD, "banned"
    else:
        tone, label = Tone.WARN, "other option"
    packages = sorted(
        {
            package
            for repository in repositories
            for package in use.packages.get((repository, option), ())
            if package != option
        }
    )
    via = f" · via {', '.join(packages)}" if packages and option != use.role.preferred else ""
    if option == use.role.preferred:
        names = _plural(len(repositories), "repository", "repositories") if repositories else "not used yet"
    else:
        names = ", ".join(_repo_link(name, "") for name in repositories)
    return f'<li>{ui.state(option, tone)} <span class="line-detail">{label} · {names}{_e(via)}</span></li>'


def _packages(site: _Site) -> str:
    ecosystems = Counter(component.ecosystem for component in site.graph.components.values())
    bars = [
        Bar(_e(ecosystem.value), (Segment("Packages", count, Mark.ACCENT),))
        for ecosystem, count in ecosystems.most_common()
    ]
    mix = ui.panel(
        "Packages by ecosystem",
        ui.bar_list(bars, max(ecosystems.values(), default=0), "Packages by ecosystem"),
    )
    header = ui.page_header(
        "Packages",
        f"{len(site.graph.components)} packages in {len(ecosystems)} ecosystems. "
        'Press <span class="mono">/</span> to find one.',
    )
    sections = "".join(
        _package_section(site, purl) for purl in sorted(site.graph.components, key=str.casefold)
    )
    return f'<div id="package-index" class="ui-page-section">{header}{mix}</div>{sections}'


_CHANGE_KINDS: tuple[tuple[str, frozenset[str]], ...] = (
    ("Downgraded", frozenset({"downgrade"})),
    ("Changed, not comparable", frozenset({"changed"})),
    ("Upgraded", frozenset({"upgrade"})),
    ("Added", frozenset({"added"})),
    ("Removed", frozenset({"removed"})),
)
_NEEDS_A_LOOK = frozenset({"downgrade", "changed"})


def _version_change(item: diff_module.VersionChange) -> str:
    name = f'<span class="mono">{_e(item.name)}</span>'
    if item.old is None:
        return f"{name} {_e(item.new or '')}"
    if item.new is None:
        return f"{name} {_e(item.old)}"
    return f"{name} {_e(item.old)} → {_e(item.new)}"


def _source_change(item: diff_module.SourceChange) -> str:
    return f'<span class="mono">{_e(item.component)}</span> {_e(item.old.value)} → {_e(item.new.value)}'


def _issue_change(item: Issue) -> str:
    if item.path is None or not item.path:
        return _e(item.kind.value)
    return f'{_e(item.kind.value)} <span class="mono">{_e(item.path)}</span>'


def _changes(site: _Site) -> str:
    value = site.diff_value
    if value is None or not value.baseline:
        return ui.page_header("Changes") + (
            '<p class="unknown">no baseline: the previous revision has no dependency inventory</p>'
        )
    body = [ui.page_header("Changes", f"{_e(value.source)} → {_e(value.target)} · {_summary_metrics(value)}")]
    if not value.repositories:
        body.append(ui.panel("Changes", ui.empty_state("Nothing changed"), flush=True))
        return "\n".join(body)

    attention = [
        Line(_repo_link(change.repository, ""), text)
        for change in value.repositories
        for text in (
            *(
                f"{_version_change(item)} · {item.direction}"
                for item in change.versions
                if item.direction in _NEEDS_A_LOOK
            ),
            *(f"{_source_change(item)} · source changed" for item in change.sources),
            *(f"{_issue_change(item)} · new issue" for item in change.new_issues),
        )
    ]
    body.append(
        ui.panel(
            "Needs a look",
            ui.lines(attention) if attention else ui.empty_state("No downgrades, source changes or new issues"),
            meta="downgrades, source changes and new issues",
            flush=not attention,
        )
    )
    rows = []
    for change in value.repositories:
        groups = "".join(
            _change_group(f"{title} · {len(items)}", items)
            for title, items in (
                *(
                    (title, [_version_change(item) for item in change.versions if item.direction in directions])
                    for title, directions in _CHANGE_KINDS
                ),
                ("Sources changed", [_source_change(item) for item in change.sources]),
                ("New issues", [_issue_change(item) for item in change.new_issues]),
                ("Resolved issues", [_issue_change(item) for item in change.resolved_issues]),
            )
        )
        counted = len(change.versions) + len(change.sources) + len(change.new_issues) + len(change.resolved_issues)
        notes = [_plural(counted, "change", "changes")]
        if change.status != "changed":
            notes.append(f"repository {change.status}")
        if change.old_state != change.new_state:
            notes.append(f"scan {_e(change.old_state or 'absent')} → {_e(change.new_state or 'absent')}")
        rows.append(
            f'<li class="change-repo"><div>{_repo_link(change.repository, "")}'
            f'<div class="note">{" · ".join(notes)}</div></div>'
            f"<div>{groups or '<p class=\"note\">only the recorded commit moved</p>'}</div></li>"
        )
    body.append(
        ui.panel(
            "Every change",
            f'<ul class="change-list">{"".join(rows)}</ul>',
            meta=f"{_plural(len(value.repositories), 'repository', 'repositories')}, by name",
            flush=True,
        )
    )
    return "\n".join(body)


def _actionable_issues(site: _Site, name: str, data: RepositoryData) -> list[Issue]:
    return [
        issue
        for issue in data.issues
        if issue.kind not in _KNOWN_LIMITS and (name not in site.forks or issue.kind in _CHECKOUT_KINDS)
    ]


def _coverage(site: _Site) -> str:
    states: Counter[str] = Counter(data.state.value for data in site.graph.repositories.values())
    kinds: Counter[CoverageKind] = Counter(
        issue.kind for data in site.graph.repositories.values() for issue in data.issues
    )
    limits = " · ".join(f"{kinds[kind]} {label}" for kind, label in _KNOWN_LIMITS.items() if kinds[kind])
    subtitle = (
        f"{len(site.graph.repositories)} repositories · {states['complete']} complete · "
        f"{states['partial']} partial · {states['failed']} failed · {states['unavailable']} unavailable"
    )
    body = [ui.page_header("Coverage", f"{subtitle}<br>Known limits: {limits}" if limits else subtitle)]
    affected: dict[CoverageKind, set[str]] = defaultdict(set)
    for name, data in site.graph.repositories.items():
        for issue in _actionable_issues(site, name, data):
            affected[issue.kind].add(name)
    if affected:
        body.append(
            ui.group(
                "What to fix",
                ui.card_grid(
                    (
                        _coverage_card(kind, sorted(names, key=str.casefold))
                        for kind, names in sorted(affected.items(), key=lambda item: (item[0].severity, -len(item[1])))
                    ),
                    wide=True,
                ),
                count=len(affected),
            )
        )
    else:
        body.append(ui.panel("What to fix", ui.empty_state("Nothing to fix"), flush=True))
    body.append(_risk_section(site))
    return "\n".join(body)


def _coverage_card(kind: CoverageKind, repositories: Sequence[str]) -> str:
    label, action = _COVERAGE_ACTIONS[kind]
    tone = Tone.BAD if kind.severity == "error" else Tone.WARN
    return ui.card(
        f"<span>{_e(label)}</span>",
        f'<div class="card-change">{_e(action)}</div>'
        f'<div class="card-foot">{_repository_names(repositories)}</div>',
        meta=ui.badge(_plural(len(repositories), "repository", "repositories"), tone),
    )


def _repository(site: _Site, name: str) -> str:
    data = site.graph.repositories[name]
    card = next((item for item in site.scorecards if item.repository == name), None)
    fork = "fork, tracked only" if name in site.forks else ""
    body = [
        ui.breadcrumbs(
            (("Repositories", "../../../repositories.html"), ("To do", "../../../index.html")),
            name,
        ),
        ui.page_header(name, fork),
    ]
    if data.state.value in ("failed", "unavailable"):
        body.append(f'<div class="badges">{_state_badge(data)}</div>')
    if card is not None:
        body.append(
            ui.status_strip(
                (
                    Tile(
                        str(card.vulnerable),
                        "Vulnerable",
                        "packages",
                        "#todo",
                        Tone.BAD if card.vulnerable else None,
                    ),
                    Tile(str(card.behind), "Behind", "direct dependencies", "#todo"),
                    Tile(str(card.off_target), "Off target", "version drift", "#todo"),
                )
            )
        )
    body.append(_repository_status_panel(site, name))
    body.append(_todo_panel(site, name))
    held = next((row for row in site.package_weight if row.repository == name), None)
    if held is not None and held.total([language.key for language in weight.LANGUAGES]).packages:
        body.append(weight_view.repository_panel(held, "../../../"))
    counted = next((repository for repository in site.code.repositories if repository.name == name), None)
    if counted is not None:
        body.append(loc_view.repository_panel(counted, "../../../"))
    if not data.edges:
        body.append(
            '<p class="zero">complete: zero dependencies</p>'
            if data.state.value == "complete"
            else '<p class="unknown">no dependency edges recorded</p>'
        )
    return "\n".join(body)


def _enrichment_stamp(site: _Site) -> str:
    fetched = site.cache.fetched_at
    if fetched is None:
        return "no registry data"
    return f"registry data from {time.strftime('%Y-%m-%d', time.gmtime(fetched))}"


def _changes_line(site: _Site) -> str:
    value = site.diff_value
    if value is None or not value.baseline:
        return '<a href="changes.html">no change baseline</a>'
    return f'<a href="changes.html">changes: {_summary_metrics(value)}</a>'


def _duplicates(site: _Site, data: RepositoryData) -> list[tuple[str, list[str]]]:
    versions: dict[str, set[str]] = defaultdict(set)
    for instance in data.instances:
        if instance.version is not None:
            versions[instance.component].add(instance.version)
    return [
        (purl, sorted(found, key=lambda item: _version_sort_key(_ecosystem_of(purl), item)))
        for purl, found in sorted(versions.items())
        if len(found) > 1
    ]


def _enrichment_cell(site: _Site, instance: Instance) -> str:
    entry = site.cache.results.get(instance.purl)
    if entry is None or not isinstance(entry.get("vulns"), list):
        return '<span class="unknown">not checked</span>'
    if not enrich.is_fresh(entry, site.now):
        return '<span class="unknown">stale</span>'
    latest = entry.get("latest")
    vulns = entry.get("vulns")
    parts = []
    if isinstance(latest, str):
        parts.append(f"latest {_e(latest)}")
    if isinstance(vulns, list) and vulns:
        ids = ", ".join(
            str(item.get("id")) for item in vulns if isinstance(item, dict)
        )
        parts.append(f'<span class="finding">{len(vulns)} vulnerabilities: {_e(ids)}</span>')
    else:
        parts.append("no known vulnerabilities")
    return "; ".join(parts)


def _source_label(instance: Instance) -> str:
    label = instance.source_kind.value
    url = instance.registry_url or instance.vcs_url or instance.repository_url
    if url is not None:
        return f'{_e(label)} <span class="mono">{_e(url)}</span>'
    if instance.commit is not None:
        return f'{_e(label)} <span class="mono">{_e(instance.commit)}</span>'
    return _e(label)


def _evidence_path(
    repository: str, commit: str | None, path: str | None, locator: str | None = None
) -> str:
    if path is None:
        return ""
    label = _e(path) + (f" <span class=\"mono\">{_e(locator)}</span>" if locator is not None and locator != "" else "")
    if commit is None:
        return label
    url = (
        f"https://github.com/{quote(repository, safe='/')}/blob/{quote(commit, safe='')}/"
        f"{quote(path, safe='/')}"
    )
    return f'<a href="{_e(url)}">{label}</a>'


def _summary_metrics(value: diff_module.Diff) -> str:
    """What changed, in words: repositories touched, then each kind of change that happened."""
    if not value.repositories:
        return "no changes"
    directions = Counter(item.direction for change in value.repositories for item in change.versions)
    counts = (
        (directions["upgrade"], "upgraded"),
        (directions["downgrade"], "downgraded"),
        (directions["changed"], "changed"),
        (directions["added"], "added"),
        (directions["removed"], "removed"),
        (sum(len(change.sources) for change in value.repositories), "source changes"),
        (sum(len(change.new_issues) for change in value.repositories), "new issues"),
        (sum(len(change.resolved_issues) for change in value.repositories), "resolved issues"),
    )
    parts = [_plural(len(value.repositories), "repository", "repositories")]
    parts.extend(f"{count} {label}" for count, label in counts if count)
    return " · ".join(parts)


def _repo_link(name: str, prefix: str) -> str:
    return f'<a href="{prefix}repos/{_e(name)}/index.html" class="mono">{_e(name)}</a>'


def _package_link(purl: str, prefix: str, text: str) -> str:
    return f'<a href="{prefix}packages.html#pkg={_fragment(purl)}" class="mono">{_e(text)}</a>'


def _fragment(purl: str) -> str:
    return _e(quote(purl, safe=""))


def _edge_label(graph: Graph, edge: Edge) -> str:
    return f"{graph.label(edge.from_id)} → {graph.label(edge.to_id)}"


def _ecosystem_of(purl: str) -> Ecosystem:
    value = purl.removeprefix("pkg:").split("/", 1)[0]
    try:
        return Ecosystem(value)
    except ValueError:
        return Ecosystem.GENERIC


def _version_sort_key(ecosystem: Ecosystem, version: str) -> tuple[int, object]:
    if ecosystem is Ecosystem.PYPI:
        try:
            return (0, Version(version))
        except InvalidVersion:
            return (1, version)
    parts: list[int] = []
    for piece in version.split("."):
        digits = ""
        for character in piece:
            if not character.isdigit():
                break
            digits += character
        if not digits:
            break
        parts.append(int(digits))
    return (0, tuple(parts)) if parts else (1, version)


def _json(value: object) -> str:
    return jsdata.dump_js(value)


def _table(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], value)
    return {}


def _value(value: object) -> int:
    if isinstance(value, Mapping):
        item = cast(Mapping[str, Any], value).get("value", 0)
        return item if isinstance(item, int) else 0
    return value if isinstance(value, int) else 0


_ORIGIN_MARKS = {
    world.Origin.YOURS: Mark.ACCENT,
    world.Origin.THIRD_PARTY: Mark.GHOST,
    world.Origin.UNKNOWN: Mark.UNKNOWN,
}
_ORIGIN_LABELS = {
    world.Origin.YOURS: "Yours",
    world.Origin.THIRD_PARTY: "Third-party",
    world.Origin.UNKNOWN: "Owner unknown",
}
_MIRROR_MARKS = {
    world.Mirror.MIRRORED: Mark.ACCENT,
    world.Mirror.PARTIAL: Mark.WARN,
    world.Mirror.MISSING: Mark.GHOST,
}
_MIRROR_LABELS = {
    world.Mirror.MIRRORED: "On stuff",
    world.Mirror.PARTIAL: "Versions missing",
    world.Mirror.MISSING: "Not on stuff",
}
_REACH_BUCKETS = ((1, 1), (2, 2), (3, 5), (6, 10), (11, 20), (21, None))
_TREEMAP_SIZE = (1200, 760)


def _explore(site: _Site) -> str:
    graph = site.graph
    direct = sum(1 for edge in graph.edges if edge.edge.relation is Relation.DIRECT)
    transitive = len(graph.edges) - direct
    complete = sum(1 for data in graph.repositories.values() if data.state.value == "complete")
    partial = sum(1 for data in graph.repositories.values() if data.state.value == "partial")
    trouble = sum(
        1
        for data in graph.repositories.values()
        if data.state.value in ("failed", "unavailable")
    )
    hidden = len(site.hidden)
    coverage_tone = Tone.WARN if partial or trouble else None
    tiles = ui.status_strip(
        (
            Tile(
                str(len(graph.repositories)),
                "Repositories",
                " · ".join(
                    part
                    for part in (
                        f"{len(graph.repositories) - len(site.forks)} owned",
                        _plural_if(len(site.forks), "fork"),
                        f"{hidden} private hidden" if hidden else "",
                    )
                    if part
                ),
                "repositories.html",
            ),
            Tile(
                str(len(graph.components)),
                "Packages",
                f"{len(graph.instances)} recorded versions",
                "packages.html",
            ),
            Tile(
                str(len(graph.edges)),
                "Dependency edges",
                f"{direct} direct · {transitive} transitive",
                "packages.html",
            ),
            Tile(
                str(complete),
                "Fully covered",
                f"{partial} partial · {trouble} failed" if trouble else f"{partial} partial",
                "coverage.html",
                coverage_tone,
            ),
        )
    )
    options = "\n        ".join(
        f'<option value="{_e(name)}">{_e(name)}</option>' for name in atlas.ecosystems(graph)
    )
    zero = len(graph.edges) == 0
    notice = (
        ui.notice(
            "No dependency edges are recorded for the visible inventory. "
            "Check the <a href=\"coverage.html\">coverage</a> page for the inputs that could not be read.",
            Tone.WARN,
        )
        if zero
        else ""
    )
    subtitle = (
        "Actual dependency relationships across the fleet. Focus a repository to follow its "
        "direct and transitive dependencies."
    )
    header = ui.page_header("Explore", subtitle)
    stage = """
<div class="atlas" id="atlas">
  <div class="atlas-toolbar" role="toolbar" aria-label="Graph controls">
    <button type="button" id="atlas-fleet" class="atlas-fleet" hidden>← Fleet</button>
    <div class="atlas-searchbox">
      <label class="ui-search atlas-search" for="atlas-search">
        <span class="ui-sr-only">Search repositories and packages</span>
        <svg class="ui-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <circle cx="7" cy="7" r="4.5" stroke="currentColor" stroke-width="1.4"/>
          <path d="M10.5 10.5 14 14" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
        <input id="atlas-search" type="search" placeholder="Search repositories and packages  /"
               autocomplete="off" role="combobox" aria-expanded="false"
               aria-controls="atlas-search-results" aria-autocomplete="list">
      </label>
      <div class="atlas-search-results" id="atlas-search-results" role="listbox" hidden></div>
    </div>
    <label class="atlas-select" for="atlas-ecosystem"><span class="atlas-select-label">Ecosystem</span>
      <select id="atlas-ecosystem">
        <option value="all">All ecosystems</option>
        ECOSYSTEM_OPTIONS
      </select>
    </label>
    <div class="atlas-relation" id="atlas-relation" role="group" aria-label="Relation">
      <button type="button" data-relation="all" aria-pressed="true">All</button>
      <button type="button" data-relation="direct" aria-pressed="false">Direct</button>
      <button type="button" data-relation="transitive" aria-pressed="false">Transitive</button>
    </div>
    <button type="button" id="atlas-fit" class="atlas-button">Fit</button>
    <button type="button" id="atlas-reset" class="atlas-button">Reset view</button>
  </div>
  <div class="atlas-stage">
    <div class="atlas-canvas">
      <div id="atlas-graph" class="atlas-graph" role="img"
           aria-label="Fleet dependency graph. Use the search field to find and focus
           repositories and packages. Press Escape to clear a selection or return to the fleet overview."></div>
      <div id="atlas-loading" class="atlas-message" role="status">Rendering the dependency graph…</div>
      <noscript>
        <style>#atlas-loading{display:none}</style>
        <div class="atlas-message">
          <p><strong>The Explore graph needs JavaScript.</strong> The inventory is still readable
            without it:</p>
          <ul class="plain-list">
            <li><a href="repositories.html">Repositories</a> — every visible repository and its state</li>
            <li><a href="world.html">World</a> — who maintains the packages you reach</li>
            <li><a href="packages.html">Packages</a> — every package with versions and consumers</li>
          </ul>
        </div>
      </noscript>
      <div id="atlas-fallback" class="atlas-message atlas-message-fallback" hidden>
        <p><strong>The graph needs WebGL2.</strong> This browser did not provide a usable
          WebGL2 context (or the GPU context was lost). The dependency data is intact —
          browse it without the graph:</p>
        <ul class="plain-list">
          <li><a href="repositories.html">Repositories</a> — every visible repository and its state</li>
          <li><a href="world.html">World</a> — who maintains the packages you reach</li>
          <li><a href="packages.html">Packages</a> — every package with versions and consumers</li>
        </ul>
      </div>
      <div class="atlas-legend" aria-hidden="true">
        <span class="atlas-legend-item"><span class="atlas-dot" style="--dot:#2a78d6"></span>repository</span>
        <span class="atlas-legend-item"><span class="atlas-dot" style="--dot:#eb6834"></span>repository with
          coverage errors</span>
        <span class="atlas-legend-item"><span class="atlas-dot" style="--dot:#1c1c1a"></span>project</span>
        <span class="atlas-legend-item"><span class="atlas-dot" style="--dot:#d55e00"></span>cargo</span>
        <span class="atlas-legend-item"><span class="atlas-dot" style="--dot:#2a78d6"></span>npm</span>
        <span class="atlas-legend-item"><span class="atlas-dot" style="--dot:#009e73"></span>pypi</span>
        <span class="atlas-legend-item"><span class="atlas-dot" style="--dot:#e69f00"></span>golang</span>
        <span class="atlas-legend-item"><span class="atlas-dot" style="--dot:#9a9992"></span>other ecosystem</span>
        <span class="atlas-legend-item"><span class="atlas-line"></span>exact edge</span>
        <span class="atlas-legend-item"><span class="atlas-line atlas-line-strong"></span>aggregate
          (repository → ecosystem)</span>
      </div>
      <div id="atlas-empty" class="atlas-message" hidden>
        <p><strong>No repositories are visible.</strong> The catalog hides every repository from
          dashboards, or the inventory is empty.</p>
        <ul class="plain-list">
          <li><a href="coverage.html">Coverage</a> — why inputs could not be read</li>
        </ul>
      </div>
      <div class="atlas-caption" id="atlas-caption" aria-live="polite">Fleet overview</div>
    </div>
    <aside id="atlas-inspector" class="atlas-inspector" aria-label="Selection inspector" aria-live="polite">
      <h2 class="atlas-inspector-title">Inspector</h2>
      <p class="atlas-inspector-empty">Selection details appear here with JavaScript enabled.</p>
    </aside>
  </div>
  <p class="atlas-footnote">Aggregate edges between a repository and an ecosystem sum every edge whose
    target belongs to the ecosystem; they are not runtime linkage. Exact edges appear after you focus a
    repository. Records with unknown or declared-only resolution are called out in the inspector, not
    counted as zeros. The inventory excludes the repositories the catalog hides from dashboards.</p>
</div>
<script src="assets/vendor/atlas.vendor.js"></script>
<script src="assets/atlas-data.js"></script>
<script src="assets/atlas.js"></script>
""".replace("ECOSYSTEM_OPTIONS", options)
    return "\n".join(part for part in (header, tiles, notice, stage) if part)


def _world(site: _Site) -> str:
    value = site.world
    packages = value.packages
    forks = len(site.forks)
    header = ui.page_header(
        "World",
        f"Every package your {len(value.repositories)} repositories reach, by who maintains it. "
        + (f"{forks} forks are left out. " if forks else "")
        + f"Yours means {', '.join(sorted(world.display_owner(owner) for owner in value.owners))}.",
    )
    if not packages:
        return header + ui.empty_state("No packages", "No repository in this view declares a dependency.")
    origins = Counter(package.origin for package in packages)
    direct = sum(1 for package in packages if package.direct)
    in_repo = sum(1 for package in packages if package.in_repo)
    third_owners = {package.owner for package in packages if package.origin is world.Origin.THIRD_PARTY}
    tiles = (
        Tile(
            str(len(packages)),
            "Packages",
            f"{direct} declared directly · {len(packages) - direct} transitive only",
            "#map",
        ),
        Tile(
            str(origins[world.Origin.YOURS]),
            "Yours",
            f"{_percent(origins[world.Origin.YOURS], len(packages))} · {in_repo} built in your repositories",
            "#yours",
        ),
        Tile(
            str(origins[world.Origin.THIRD_PARTY]),
            "Third-party",
            f"{_percent(origins[world.Origin.THIRD_PARTY], len(packages))} · {len(third_owners)} owners",
            "#owners",
        ),
        Tile(
            str(origins[world.Origin.UNKNOWN]),
            "Owner unknown",
            f"{_percent(origins[world.Origin.UNKNOWN], len(packages))} · no source URL"
            if site.cache.sources
            else "run deps enrich to find owners",
            "#owners",
        ),
        _mirror_tile(value),
    )
    body = [header, ui.status_strip(tiles)]
    if not site.cache.sources:
        body.append(
            ui.notice(
                'Owners of registry packages are not looked up yet. Run '
                '<span class="mono">uv run repomod deps enrich</span>, then render again.'
            )
        )
    body.extend(
        (
            _ownership_panel(site, packages),
            _mirror_panel(value),
            _world_map(site),
            _yours_panel(packages),
            _reach_panel(value),
            _owners_panel(value),
        )
    )
    return "\n".join(body)


def _percent(part: int, total: int) -> str:
    return f"{round(100 * part / total)}%" if total else "0%"


def _origin_parts(packages: Sequence[world.Package], weight: Callable[[world.Package], int]) -> tuple[Segment, ...]:
    totals = Counter[world.Origin]()
    for package in packages:
        totals[package.origin] += weight(package)
    return tuple(Segment(_ORIGIN_LABELS[origin], totals[origin], _ORIGIN_MARKS[origin]) for origin in world.Origin)


def _origin_legend(caption: str = "") -> str:
    return ui.legend([(_ORIGIN_LABELS[origin], _ORIGIN_MARKS[origin]) for origin in world.Origin], caption)


_DRILLDOWN_ROWS = 30
_DRILLDOWN_VERSIONS = 3


def _ecosystem_drilldowns(site: _Site, groups: Mapping[Ecosystem, Sequence[world.Package]]) -> str:
    instances: dict[str, list[Instance]] = defaultdict(list)
    for item in site.graph.instances.values():
        instances[item.component].append(item)
    panels = []
    for ecosystem in sorted(groups, key=lambda item: (-len(groups[item]), item.value)):
        rows = sorted(
            groups[ecosystem],
            key=lambda package: (-len(package.repositories), package.component.purl.casefold()),
        )
        shown = rows[:_DRILLDOWN_ROWS]
        table = ui.static_table(
            (
                Column("Package", wrap=True, mono=True),
                Column("Versions", wrap=True),
                Column("Owner"),
                Column("Origin"),
                Column("Repos", numeric=True),
                Column("Direct"),
            ),
            [
                (
                    _package_link(
                        package.component.purl,
                        "",
                        package.component.display_name,
                    ),
                    _e(_version_summary(instances.get(package.component.purl, ()))),
                    _e("unknown" if package.owner is None else world.display_owner(package.owner)),
                    _e(package.origin.value),
                    str(len(package.repositories)),
                    "yes" if package.direct else "",
                )
                for package in shown
            ],
            label=f"Packages in {ecosystem.value}",
        )
        more = (
            f'<p class="change-group">+{len(rows) - _DRILLDOWN_ROWS} more — search them in '
            f'<a href="packages.html">Packages</a></p>'
            if len(rows) > _DRILLDOWN_ROWS
            else ""
        )
        yours = sum(1 for package in rows if package.origin is world.Origin.YOURS)
        meta = f"{yours} yours · {len(rows) - yours} third-party or unknown"
        panels.append(
            ui.collapsed_panel(
                f"{ecosystem.value} · {_plural(len(rows), 'package')}",
                table + more,
                meta=meta,
                panel_id=f"ecosystem-{ecosystem.value}",
                flush=True,
            )
        )
    return "".join(panels)


def _version_summary(instances: Sequence[Instance]) -> str:
    counts = Counter(instance.version or "unknown" for instance in instances)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    parts = [
        f"{_short_ref(version)} ({count})" if count > 1 else _short_ref(version)
        for version, count in ordered[:_DRILLDOWN_VERSIONS]
    ]
    if len(ordered) > _DRILLDOWN_VERSIONS:
        parts.append(f"+{len(ordered) - _DRILLDOWN_VERSIONS}")
    return ", ".join(parts)


def _ownership_panel(site: _Site, packages: Sequence[world.Package]) -> str:
    def uses(package: world.Package) -> int:
        return len(package.repositories)

    def one(_: world.Package) -> int:
        return 1

    totals = [
        Bar("Packages", _origin_parts(packages, one), note="each package counted once"),
        Bar(
            "Package uses",
            _origin_parts(packages, uses),
            note="each package counted once per repository that reaches it",
        ),
    ]
    by_ecosystem: dict[Ecosystem, list[world.Package]] = defaultdict(list)
    for package in packages:
        by_ecosystem[package.component.ecosystem].append(package)
    ordered = sorted(by_ecosystem.items(), key=lambda item: (-len(item[1]), item[0].value))
    ecosystems = [
        Bar(_e(ecosystem.value), _origin_parts(rows, one), href=f"#ecosystem-{ecosystem.value}")
        for ecosystem, rows in ordered
    ]
    body = (
        _origin_legend()
        + ui.bar_list(totals, max(sum(part.value for part in bar.parts) for bar in totals), "Ownership")
        + '<p class="change-group">Packages by ecosystem</p>'
        + ui.bar_list(ecosystems, max(len(rows) for _, rows in ordered), "Ownership by ecosystem")
        + _ecosystem_drilldowns(site, by_ecosystem)
    )
    return ui.panel("How much is yours", body)


def _world_map(site: _Site) -> str:
    vulnerable = {row.component.purl for row in site.vulnerable}
    by_ecosystem: dict[Ecosystem, dict[str | None, list[world.Package]]] = defaultdict(lambda: defaultdict(list))
    for package in site.world.packages:
        by_ecosystem[package.component.ecosystem][package.owner].append(package)
    blocks = []
    for ecosystem, owners in by_ecosystem.items():
        count = sum(len(rows) for rows in owners.values())
        children = []
        for owner, rows in owners.items():
            name = world.display_owner(owner)
            cells = [
                Cell(
                    package.component.display_name,
                    len(package.repositories),
                    f"packages.html#pkg={package.component.purl}",
                    f"{package.component.display_name} · {name} · {len(package.repositories)} "
                    f"{'repository' if len(package.repositories) == 1 else 'repositories'} · "
                    f"{'direct' if package.direct else 'transitive'}"
                    + (" · vulnerable" if package.component.purl in vulnerable else "")
                    + f" · {_mirror_tip(package)}",
                    " ".join(
                        (
                            f"tm-{package.origin.name.casefold().replace('_', '-')}",
                            "tm-direct" if package.direct else "tm-transitive",
                            f"tm-m-{package.mirror.name.casefold().replace('_', '-')}",
                            *(("tm-vulnerable",) if package.component.purl in vulnerable else ()),
                        )
                    ),
                )
                for package in rows
            ]
            children.append(Block(name, f"{name} · {len(rows)} packages", cells))
        blocks.append(Block(f"{ecosystem.value} · {count}", f"{ecosystem.value} · {count} packages", children))
    width, height = _TREEMAP_SIZE
    ownership = ui.legend(
        [
            ("Yours, direct", Mark.ACCENT),
            ("Third-party, direct", Mark.GHOST),
            ("Owner unknown", Mark.UNKNOWN),
            ("Vulnerable", Mark.BAD),
        ],
        "Area is repositories reached. Lighter cells are transitive only. Select a cell to open the package.",
    )
    mirror = ui.legend(
        [
            *((_MIRROR_LABELS[state], _MIRROR_MARKS[state]) for state in _MIRROR_MARKS),
            ("Not served or not checked", Mark.UNKNOWN),
        ],
        "Area is repositories reached. stuff serves Cargo, npm, and PyPI packages.",
    )
    modes = (
        '<div class="map-modes" role="radiogroup" aria-label="Color the map by">'
        '<label><input type="radio" name="map-mode" checked> Ownership</label>'
        '<label><input type="radio" name="map-mode" id="map-mirror"> Mirrored on stuff</label></div>'
    )
    chart = ui.treemap(blocks, width, height, f"{len(site.world.packages)} packages by ecosystem and owner")
    body = (
        f'<div class="world-map">{modes}<div class="legend-ownership">{ownership}</div>'
        f'<div class="legend-mirror">{mirror}</div><div class="treemap-frame">{chart}</div></div>'
        '<p class="note map-narrow">The map needs a wider screen. The ecosystem, owner and package lists on '
        "this page hold the same packages.</p>"
    )
    return ui.panel("Map", body, panel_id="map")


def _mirrorable(packages: Sequence[world.Package]) -> list[world.Package]:
    return [package for package in packages if package.mirror in _MIRROR_MARKS]


def _mirror_tip(package: world.Package) -> str:
    if package.mirror is world.Mirror.PARTIAL:
        return f"stuff lacks {', '.join(package.unmirrored_versions)}"
    if package.mirror is world.Mirror.MISSING:
        return "not on stuff"
    if package.mirror is world.Mirror.MIRRORED:
        return "on stuff"
    return f"stuff mirror {package.mirror.value}"


def _mirror_tile(value: world.World) -> Tile:
    eligible = _mirrorable(value.packages)
    if not value.mirrors:
        return Tile("—", "On stuff", "run deps enrich to read the stuff catalogs", "#mirror")
    states = Counter(package.mirror for package in eligible)
    partial = states[world.Mirror.PARTIAL]
    return Tile(
        str(states[world.Mirror.MIRRORED]),
        "On stuff",
        f"{_percent(states[world.Mirror.MIRRORED], len(eligible))} of {len(eligible)} Cargo, npm, and PyPI packages"
        + (f" · {partial} missing versions" if partial else ""),
        "#mirror",
    )


def _mirror_parts(packages: Sequence[world.Package], weight: Callable[[world.Package], int]) -> tuple[Segment, ...]:
    totals = Counter[world.Mirror]()
    for package in packages:
        totals[package.mirror] += weight(package)
    return tuple(Segment(_MIRROR_LABELS[state], totals[state], mark) for state, mark in _MIRROR_MARKS.items())


def _mirror_panel(value: world.World) -> str:
    if not value.mirrors:
        return ui.panel(
            "Mirrored on stuff",
            '<p class="unknown">not checked: run <span class="mono">uv run repomod deps enrich</span></p>',
            panel_id="mirror",
            flush=True,
        )
    eligible = _mirrorable(value.packages)
    if not eligible:
        return ui.panel("Mirrored on stuff", '<p class="zero">no Cargo, npm, or PyPI packages</p>', panel_id="mirror")

    def one(_: world.Package) -> int:
        return 1

    def uses(package: world.Package) -> int:
        return len(package.repositories)

    totals = [
        Bar("Packages", _mirror_parts(eligible, one), note="each package counted once"),
        Bar("Package uses", _mirror_parts(eligible, uses), note="once per repository that reaches it"),
        *(
            Bar(_ORIGIN_LABELS[origin], _mirror_parts(rows, one))
            for origin in world.Origin
            if (rows := [package for package in eligible if package.origin is origin])
        ),
        *(
            Bar(_e(ecosystem.value), _mirror_parts(rows, one))
            for ecosystem in sorted(world.MIRRORABLE, key=lambda item: item.value)
            if (rows := [package for package in eligible if package.component.ecosystem is ecosystem])
        ),
    ]
    gaps = [package for package in eligible if package.mirror is not world.Mirror.MIRRORED]
    bars = [
        Bar(
            f'<a href="packages.html#pkg={_e(package.component.purl)}">{_e(package.component.display_name)}</a>'
            + (" " + ui.badge("versions missing", Tone.WARN) if package.mirror is world.Mirror.PARTIAL else ""),
            (Segment("Repositories", len(package.repositories), _MIRROR_MARKS[package.mirror]),),
            note=_e(
                f"{package.component.ecosystem.value} · {world.display_owner(package.owner)}"
                + (
                    f" · missing {', '.join(package.unmirrored_versions)}"
                    if package.mirror is world.Mirror.PARTIAL
                    else ""
                )
            ),
            tip=", ".join(package.repositories),
        )
        for package in gaps
    ]
    checked = min(catalog.fetched_at for catalog in value.mirrors.values())
    body = (
        ui.legend([(_MIRROR_LABELS[state], mark) for state, mark in _MIRROR_MARKS.items()])
        + ui.bar_list(totals, max(sum(part.value for part in bar.parts) for bar in totals), "Mirror coverage")
    )
    if bars:
        body += (
            f'<p class="change-group">Not fully on stuff · {len(bars)}, by repositories reached</p>'
            + ui.scope(
                ui.bar_list(bars, max(len(package.repositories) for package in gaps), "Packages not fully on stuff"),
                search="Filter packages",
                limit=_LIST_ROWS,
                total=len(bars),
            )
        )
    return ui.panel(
        "Mirrored on stuff",
        body,
        meta=f"catalogs read {time.strftime('%Y-%m-%d %H:%M', time.gmtime(checked))} UTC",
        panel_id="mirror",
    )


def _yours_panel(packages: Sequence[world.Package]) -> str:
    reused = [package for package in packages if package.origin is world.Origin.YOURS and not package.in_repo]
    built = sum(1 for package in packages if package.in_repo)
    meta = f"{built} more are built inside your repositories"
    if not reused:
        empty = '<p class="zero">no repository consumes a package you publish</p>'
        return ui.panel("Your packages", empty, meta=meta, panel_id="yours")
    bars = [
        Bar(
            f'<a href="packages.html#pkg={_e(package.component.purl)}">{_e(package.component.display_name)}</a>',
            (Segment("Repositories", len(package.repositories), Mark.ACCENT),),
            note=_e(f"{package.component.ecosystem.value} · {world.display_owner(package.owner)}"),
            tip=", ".join(package.repositories),
        )
        for package in reused
    ]
    listing = ui.scope(
        ui.bar_list(bars, max(len(package.repositories) for package in reused), "Your packages"),
        search="Filter your packages",
        limit=_LIST_ROWS,
        total=len(bars),
    )
    return ui.panel(f"Your packages your repositories use · {len(reused)}", listing, meta=meta, panel_id="yours")


def _reach_panel(value: world.World) -> str:
    bars = []
    for low, high in _REACH_BUCKETS:
        if low > len(value.repositories):
            break
        top = len(value.repositories) if high is None else min(high, len(value.repositories))
        rows = [package for package in value.packages if low <= len(package.repositories) <= top]
        label = str(low) if low == top else f"{low} to {top}"
        bars.append(Bar(f"{label} {'repository' if top == 1 else 'repositories'}", _origin_parts(rows, lambda _: 1)))
    scale = max((sum(part.value for part in bar.parts) for bar in bars), default=0)
    return ui.panel(
        "Reach",
        _origin_legend("Packages by how many of your repositories reach them")
        + ui.bar_list(bars, scale, "Packages by reach"),
    )


def _owners_panel(value: world.World) -> str:
    packages = value.packages
    grouped: dict[str, list[world.Package]] = defaultdict(list)
    for package in packages:
        if package.owner is not None:
            grouped[package.owner].append(package)
    rows = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    bars = []
    for owner, owned in rows:
        reached = {repository for package in owned for repository in package.repositories}
        direct = sum(1 for package in owned if package.direct)
        ecosystems = sorted({package.component.ecosystem.value for package in owned})
        yours = owner in value.owners
        bars.append(
            Bar(
                _e(world.display_owner(owner)) + (" " + ui.badge("yours") if yours else ""),
                (
                    Segment("Direct", direct, Mark.ACCENT),
                    Segment("Transitive only", len(owned) - direct, Mark.GHOST),
                ),
                note=_e(f"{_plural(len(reached), 'repository', 'repositories')} · {', '.join(ecosystems)}"),
            )
        )
    unknown = sum(1 for package in packages if package.owner is None)
    listing = ui.scope(
        ui.bar_list(bars, max((len(owned) for _, owned in rows), default=0), "Owners"),
        search="Filter owners",
        limit=_LIST_ROWS,
        total=len(bars),
    )
    return ui.panel(
        f"Owners · {len(rows)}",
        ui.legend([("Direct", Mark.ACCENT), ("Transitive only", Mark.GHOST)], "Packages per owner") + listing,
        meta=f"{unknown} packages have no known owner",
        panel_id="owners",
    )
