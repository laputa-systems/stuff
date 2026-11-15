"""The fleet's line counts, as a dashboard page.

`fleet/loc/v1` is written by `repomod loc snapshot`. The counts describe the
checkout each repository was at when the snapshot ran; the commit recorded in
the index says which one. Forks and hidden repositories are counted like
every other repository but the page decides which to show.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from repomod import paths
from repomod.dependencies import ui
from repomod.dependencies.ui import Column, Mark, Segment, Tile
from repomod.dependencies.ui import escape as _e

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

LOC = paths.LOC


@dataclass(frozen=True, slots=True)
class Language:
    name: str
    files: int
    code: int
    comment: int
    blank: int
    shebang: int


@dataclass(frozen=True, slots=True)
class Repository:
    name: str
    commit: str | None
    state: str
    languages: tuple[Language, ...]
    error: str | None

    @property
    def code(self) -> int:
        return sum(language.code for language in self.languages)

    @property
    def comment(self) -> int:
        return sum(language.comment for language in self.languages)

    @property
    def blank(self) -> int:
        return sum(language.blank for language in self.languages)

    @property
    def files(self) -> int:
        return sum(language.files for language in self.languages)


@dataclass(frozen=True, slots=True)
class Data:
    repositories: tuple[Repository, ...]
    version: str
    missing: bool


def load(root: Path = LOC) -> Data:
    try:
        index_source = json.loads((root / "index.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
        return Data((), "unknown", True)
    version = index_source.get("loc_version") if isinstance(index_source, dict) else None
    version = version if isinstance(version, str) else "unknown"
    repositories: list[Repository] = []
    repos_root = root / "repos"
    if repos_root.is_dir():
        for owner_dir in sorted(repos_root.iterdir()):
            if owner_dir.is_symlink() or not owner_dir.is_dir():
                continue
            for file in sorted(owner_dir.iterdir()):
                repository = _load_repository(file, owner_dir.name)
                if repository is not None:
                    repositories.append(repository)
    return Data(tuple(sorted(repositories, key=lambda item: item.name)), version, False)


def _load_repository(file: Path, owner: str) -> Repository | None:
    if file.is_symlink() or file.suffix != ".json":
        return None
    try:
        source = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    if not isinstance(source, dict):
        return None
    name = source.get("repository")
    if not isinstance(name, str) or name != f"{owner}/{file.stem}":
        return None
    commit = source.get("commit")
    state = source.get("state")
    if state not in {"complete", "failed", "unavailable"}:
        return None
    loc = source.get("loc")
    languages: list[Language] = []
    if isinstance(loc, dict) and isinstance(loc.get("languages"), list):
        for language in loc["languages"]:
            parsed = _load_language(language)
            if parsed is not None:
                languages.append(parsed)
    error = source.get("error")
    return Repository(
        name,
        commit if isinstance(commit, str) else None,
        state,
        tuple(languages),
        error if isinstance(error, str) else None,
    )


def _load_language(value: object) -> Language | None:
    if not isinstance(value, dict):
        return None
    name = value.get("name")
    files = value.get("file_count")
    lines = value.get("lines")
    if not isinstance(name, str) or not isinstance(files, int) or not isinstance(lines, dict):
        return None
    numbers: list[int] = []
    for key in ("total", "code", "comment", "blank", "shebang"):
        number = lines.get(key)
        if not isinstance(number, int):
            return None
        numbers.append(number)
    _total, code, comment, blank, shebang = numbers
    return Language(name, files, code, comment, blank, shebang)


def _visible(repositories: Iterable[Repository], forks: Sequence[str], hidden: Sequence[str]) -> list[Repository]:
    excluded = {*forks, *hidden}
    return [
        repository
        for repository in repositories
        if repository.name not in excluded and repository.state == "complete"
    ]


def _excluded_counts(
    repositories: Iterable[Repository], forks: Sequence[str], hidden: Sequence[str]
) -> tuple[int, int, int]:
    repository_list = list(repositories)
    excluded_forks = sum(1 for item in repository_list if item.name in set(forks))
    excluded_hidden = sum(1 for item in repository_list if item.name in set(hidden))
    visible_excluded = {*forks, *hidden}
    failed = sum(1 for item in repository_list if item.state != "complete" and item.name not in visible_excluded)
    return excluded_forks, excluded_hidden, failed


class Kind(Enum):
    """What a language's lines are: code someone wrote, documentation, or data and configuration."""

    CODE = "code"
    DOCS = "docs"
    DATA = "data"


# Lockfiles, fixtures, manifests and generated listings inflate raw line counts;
# they are reported separately so "lines of code" means code.
_DATA = frozenset({
    "JSON", "JSON with Comments", "JSON5", "XML", "YAML", "TOML", "INI", "CSV", "TSV", "SVG",
    "Protocol Buffers", "Plain Text", "Text", "Lockfile", "Nix",
})
_DOCS = frozenset({"Markdown", "reStructuredText", "AsciiDoc", "Org", "TeX", "Typst", "Groff", "Man"})
_PALETTE = (Mark.SERIES_0, Mark.SERIES_1, Mark.SERIES_2, Mark.SERIES_3, Mark.SERIES_4)
_SHOWN_LANGUAGES = 8
_SHOWN_REPOSITORY_LANGUAGES = 6


def kind_of(language: str) -> Kind:
    if language in _DATA:
        return Kind.DATA
    if language in _DOCS:
        return Kind.DOCS
    return Kind.CODE


@dataclass(frozen=True, slots=True)
class LanguageTotal:
    name: str
    kind: Kind
    files: int
    code: int
    comment: int
    blank: int
    repositories: int


def language_totals(repositories: Sequence[Repository]) -> tuple[LanguageTotal, ...]:
    """Every language across the repositories, largest code count first."""
    rows: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0, 0])
    for repository in repositories:
        for language in repository.languages:
            row = rows[language.name]
            row[0] += language.files
            row[1] += language.code
            row[2] += language.comment
            row[3] += language.blank
            row[4] += 1 if language.code else 0
    totals = (
        LanguageTotal(name, kind_of(name), files, code, comment, blank, used)
        for name, (files, code, comment, blank, used) in rows.items()
    )
    return tuple(sorted(totals, key=lambda item: (-item.code, item.name.casefold())))


def palette(repositories: Sequence[Repository]) -> dict[str, Mark]:
    """One color per language that makes up most of the repositories, fixed across the page.

    Languages are ranked by their summed share of each repository's code, so a
    language that dominates a small repository outranks one that is a sliver of
    a large one; the rest share "other".
    """
    shares: dict[str, float] = defaultdict(float)
    for repository in repositories:
        languages = _code(repository)
        total = sum(language.code for language in languages)
        for language in languages:
            shares[language.name] += language.code / total
    leading = sorted(shares, key=lambda name: (-shares[name], name))[: len(_PALETTE)]
    return dict(zip(leading, _PALETTE, strict=False))


def _count(value: int) -> str:
    return f"{value:,}"


def _short(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 10_000:
        return f"{value / 1_000:.0f}k"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def _code(repository: Repository) -> list[Language]:
    return sorted(
        (language for language in repository.languages if kind_of(language.name) is Kind.CODE and language.code),
        key=lambda language: (-language.code, language.name),
    )


def _kind_lines(repository: Repository, kind: Kind) -> int:
    return sum(language.code for language in repository.languages if kind_of(language.name) is kind)


def _parts(languages: Sequence[Language], colors: dict[str, Mark]) -> tuple[Segment, ...]:
    """Colored segments for the leading languages, then one "other" segment."""
    shown = [
        Segment(language.name, language.code, colors[language.name])
        for language in languages
        if language.name in colors
    ]
    other = sum(language.code for language in languages if language.name not in colors)
    if other:
        shown.append(Segment("other languages", other, Mark.GHOST))
    return tuple(shown)


def _repositories(count: int) -> str:
    return f"{count} {'repository' if count == 1 else 'repositories'}"


def _files(count: int) -> str:
    return f"{_count(count)} {'file' if count == 1 else 'files'}"


def _note(content: str) -> str:
    return f'<p class="note">{content}</p>'


def _mix(languages: Sequence[Language], total: int) -> str:
    """The composition in words: the three largest languages with their share."""
    if not total:
        return "no code"
    named = [f"{_e(language.name)} {round(100 * language.code / total)}%" for language in languages[:3]]
    if len(languages) > 3:
        named.append(f"{len(languages) - 3} more")
    return " · ".join(named)


def page(
    data: Data,
    forks: Sequence[str],
    hidden: Sequence[str],
) -> str:
    title = "Lines"
    if data.missing:
        return "\n".join(
            (
                ui.page_header(title, "lines of code, by language and repository"),
                ui.panel(
                    "Lines of code",
                    ui.empty_state(
                        "No line counts",
                        "Run <span class=\"mono\">uv run repomod loc snapshot</span> and re-render the dashboard.",
                    ),
                    flush=True,
                ),
            )
        )
    visible = _visible(data.repositories, forks, hidden)
    excluded_forks, excluded_hidden, failed = _excluded_counts(data.repositories, forks, hidden)
    if not visible:
        body = ui.empty_state("Nothing to count", "Every repository is a fork or hidden by privacy settings.")
        return "\n".join(
            (
                ui.page_header(title, "lines of code, by language and repository"),
                ui.panel("Lines of code", body, flush=True),
            )
        )

    totals = language_totals(visible)
    colors = palette(visible)
    code_totals = [total for total in totals if total.kind is Kind.CODE and total.code]
    code = sum(total.code for total in code_totals)
    docs = sum(total.code for total in totals if total.kind is Kind.DOCS)
    data_lines = sum(total.code for total in totals if total.kind is Kind.DATA)
    comment = sum(total.comment for total in code_totals)
    notes = [f"{len(visible)} repositories", f"counted by {data.version}"]
    if excluded_forks:
        notes.append(f"{excluded_forks} forks left out")
    if excluded_hidden:
        notes.append(f"{excluded_hidden} private repositories hidden")
    if failed:
        notes.append(f"{failed} not counted")
    tiles = (
        Tile(_count(code), "Code", f"lines in {len(code_totals)} languages", "#languages"),
        Tile(
            f"{round(100 * comment / code) if code else 0}%",
            "Commented",
            f"{_count(comment)} comment lines beside the code",
            "#languages",
        ),
        Tile(_count(docs), "Docs", "lines of Markdown and other prose", "#formats"),
        Tile(_count(data_lines), "Data and config", "JSON, YAML, TOML, lockfiles", "#formats"),
    )

    language_bars = [
        ui.Bar(
            _e(total.name),
            (Segment(total.name, total.code, colors.get(total.name, Mark.GHOST)),),
            note=f"{_repositories(total.repositories)} · {_files(total.files)}",
            value=_short(total.code),
            tip=f"{total.name}: {_count(total.code)} code lines, {_count(total.comment)} comment lines, "
            f"{_count(total.blank)} blank",
        )
        for total in code_totals[:_SHOWN_LANGUAGES]
    ]
    rest = code_totals[_SHOWN_LANGUAGES:]
    rest_note = (
        _note(" · ".join(f"{_e(total.name)} {_short(total.code)}" for total in rest))
        if rest
        else ""
    )
    ranked = sorted(
        visible, key=lambda repository: (-sum(language.code for language in _code(repository)), repository.name)
    )
    repository_bars = []
    for repository in ranked:
        languages = _code(repository)
        total = sum(language.code for language in languages)
        extra = [
            f"{_short(lines)} {label}"
            for label, lines in (
                ("docs", _kind_lines(repository, Kind.DOCS)),
                ("data", _kind_lines(repository, Kind.DATA)),
            )
            if lines
        ]
        repository_bars.append(
            ui.Bar(
                _e(repository.name),
                _parts(languages, colors),
                note=_mix(languages, total) + (f" · + {', '.join(extra)}" if extra else ""),
                value=_short(total),
                href=f"repos/{_e(repository.name)}/index.html",
                tip=f"{repository.name}: {_count(total)} code lines",
            )
        )
    legend_items = [(name, mark) for name, mark in colors.items()] + [("other languages", Mark.GHOST)]
    formats = [total for total in totals if total.kind is not Kind.CODE and total.code]
    format_bars = [
        ui.Bar(
            _e(total.name),
            (Segment(total.name, total.code, Mark.GHOST),),
            note=f"{'docs' if total.kind is Kind.DOCS else 'data'} · {total.repositories} "
            f"{'repository' if total.repositories == 1 else 'repositories'}",
            value=_short(total.code),
            tip=f"{total.name}: {_count(total.code)} lines in {_files(total.files)}",
        )
        for total in formats[:_SHOWN_LANGUAGES]
    ]
    format_rest = formats[_SHOWN_LANGUAGES:]
    format_note = (
        _note(" · ".join(f"{_e(total.name)} {_short(total.code)}" for total in format_rest)) if format_rest else ""
    )
    language_rows = [
        (
            _e(total.name),
            total.kind.value,
            _count(total.files),
            _count(total.code),
            _count(total.comment),
            _count(total.blank),
        )
        for total in totals
    ]
    return "\n".join(
        (
            ui.page_header(title, " · ".join(notes)),
            ui.status_strip(tiles),
            ui.panel(
                "What the fleet is written in",
                ui.bar_list(language_bars, code_totals[0].code if code_totals else 0, "Code lines by language")
                + rest_note,
                meta="code lines, docs and data excluded",
                panel_id="languages",
            ),
            ui.panel(
                "Repositories by size",
                ui.legend(legend_items, "each bar is one repository's code; its size is on the right")
                + ui.bar_list(repository_bars, None, "Repositories by code lines"),
                meta=f"{len(ranked)} repositories, largest first",
                panel_id="repositories",
            ),
            ui.panel(
                "Docs and data",
                ui.bar_list(format_bars, formats[0].code if formats else 0, "Lines by documentation and data format")
                + format_note,
                meta="counted apart from code: lockfiles, fixtures, manifests and prose",
                panel_id="formats",
            ),
            ui.group(
                "Every language",
                ui.scope(
                    ui.static_table(
                        (
                            Column("Language"),
                            Column("Kind"),
                            Column("Files", numeric=True),
                            Column("Code", numeric=True),
                            Column("Comment", numeric=True),
                            Column("Blank", numeric=True),
                        ),
                        language_rows,
                        label="Every language in the fleet",
                    ),
                    search="Filter languages",
                ),
                count=len(language_rows),
                note="exact counts, for lookup",
                group_id="all-languages",
            ),
        )
    )


def repository_panel(repository: Repository, _prefix: str = "") -> str:
    if repository.state != "complete":
        detail = _e(repository.error or "not counted")
        return ui.panel("Code", f'<p class="unknown">not counted: {detail}</p>', panel_id="code")
    languages = _code(repository)
    total = sum(language.code for language in languages)
    colors = dict(zip([language.name for language in languages][: len(_PALETTE)], _PALETTE, strict=False))
    extra = [
        f"{_count(lines)} {label}"
        for label, lines in (
            ("docs lines", _kind_lines(repository, Kind.DOCS)),
            ("data and config lines", _kind_lines(repository, Kind.DATA)),
        )
        if lines
    ]
    bars = [
        ui.Bar(
            _e(language.name),
            (Segment(language.name, language.code, colors.get(language.name, Mark.GHOST)),),
            note=f"{round(100 * language.code / total) if total else 0}% · {_files(language.files)}",
            value=_short(language.code),
            tip=f"{language.name}: {_count(language.code)} code lines",
        )
        for language in languages[:_SHOWN_REPOSITORY_LANGUAGES]
    ]
    hidden = languages[_SHOWN_REPOSITORY_LANGUAGES:]
    more = (
        _note(
            " · ".join(f"{_e(language.name)} {_short(language.code)}" for language in hidden)
            + f' · <a href="{_prefix}lines.html#all-languages">every language</a>'
        )
        if hidden
        else ""
    )
    body = (
        ui.segments(_parts(languages, colors), total)
        + ui.bar_list(bars, languages[0].code if languages else 0, "Code lines by language")
        + more
        + (_note(" · ".join(extra)) if extra else "")
    )
    return ui.panel("Code", body, meta=f"{_count(total)} code lines", panel_id="code")
