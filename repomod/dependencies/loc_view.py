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
from pathlib import Path
from typing import TYPE_CHECKING

from repomod import paths
from repomod.dependencies import ui
from repomod.dependencies.ui import Column, Line, Mark, Segment, Tile
from repomod.dependencies.ui import escape as _e

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

LOC = paths.LOC
_TOP_SEGMENTS = 11
_LANGUAGE_ROWS = 40
_MARKS = (Mark.ACCENT, Mark.GHOST, Mark.OK, Mark.WARN, Mark.BAD, Mark.UNKNOWN)


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


def _language_totals(repositories: Sequence[Repository]) -> dict[str, list[int]]:
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0, 0])
    for repository in repositories:
        for language in repository.languages:
            row = totals[language.name]
            row[0] += language.files
            row[1] += language.code
            row[2] += language.comment
            row[3] += language.blank
            row[4] += language.shebang
    return totals


def _count(value: int) -> str:
    return f"{value:,}"


def page(
    data: Data,
    forks: Sequence[str],
    hidden: Sequence[str],
) -> str:
    if data.missing:
        return "\n".join(
            (
                ui.page_header("Lines", "lines of code, by language and repository"),
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
        body = ui.empty_state(
            "Nothing to count",
            "Every repository is a fork or hidden by privacy settings.",
        )
        return "\n".join(
            (
                ui.page_header("Lines", "lines of code, by language and repository"),
                ui.panel("Lines of code", body, flush=True),
            )
        )
    code = sum(repository.code for repository in visible)
    comment = sum(repository.comment for repository in visible)
    files = sum(repository.files for repository in visible)
    language_totals = _language_totals(visible)
    languages = sorted(language_totals.items(), key=lambda item: (-item[1][1], item[0].casefold()))
    segments = _segments(languages, code)
    tiles = (
        Tile(_count(code), "Code", "lines across the fleet", "#languages"),
        Tile(_count(comment), "Comment", "lines in comments", "#languages"),
        Tile(_count(files), "Files", "text files counted", "#repositories"),
        Tile(str(len(language_totals)), "Languages", "distinct languages", "#languages"),
    )
    notes = [f"counted by {data.version}"]
    if excluded_forks:
        notes.append(f"{excluded_forks} forks left out")
    if excluded_hidden:
        notes.append(f"{excluded_hidden} private repositories hidden")
    if failed:
        notes.append(f"{failed} not counted")
    subtitle = " · ".join([f"{len(visible)} repositories", *notes])
    language_rows = [
        (
            _e(name),
            _count(row[0]),
            _count(row[1]),
            _count(row[2]),
            _count(row[3]),
        )
        for name, row in languages[:_LANGUAGE_ROWS]
    ]
    language_rows.append(
        ("Total", _count(files), _count(code), _count(comment), _count(sum(repository.blank for repository in visible)))
    )
    repository_rows = [
        (
            f'<a href="repos/{_e(repository.name)}/index.html">{_e(repository.name)}</a>',
            _count(repository.code),
            _count(repository.comment),
            _count(repository.files),
            _e(_top_language(repository)),
        )
        for repository in sorted(visible, key=lambda item: (-item.code, item.name))
    ]
    return "\n".join(
        (
            ui.page_header("Lines", subtitle),
            ui.status_strip(tiles),
            ui.panel(
                "Where the code lives",
                ui.segments(segments, code)
                + ui.legend([(part.label, part.mark) for part in segments], "share of fleet code lines"),
                panel_id="share",
            ),
            ui.group(
                "By language",
                ui.scope(
                    ui.static_table(
                        (
                            Column("Language"),
                            Column("Files", numeric=True),
                            Column("Code", numeric=True),
                            Column("Comment", numeric=True),
                            Column("Blank", numeric=True),
                        ),
                        language_rows,
                        label="Languages in the fleet",
                    ),
                    search="Filter languages",
                ),
                group_id="languages",
            ),
            ui.group(
                "By repository",
                ui.scope(
                    ui.static_table(
                        (
                            Column("Repository"),
                            Column("Code", numeric=True),
                            Column("Comment", numeric=True),
                            Column("Files", numeric=True),
                            Column("Leading language"),
                        ),
                        repository_rows,
                        label="Repositories in the fleet",
                    ),
                    search="Filter repositories",
                ),
                group_id="repositories",
            ),
        )
    )


def _segments(languages: Sequence[tuple[str, list[int]]], total: int) -> tuple[Segment, ...]:
    top = languages[:_TOP_SEGMENTS]
    rest = languages[_TOP_SEGMENTS:]
    parts = [
        Segment(name, row[1], _MARKS[index % len(_MARKS)]) for index, (name, row) in enumerate(top)
    ]
    other = sum(row[1] for _, row in rest)
    if other:
        parts.append(Segment(f"{len(rest)} more", other, Mark.GHOST))
    if not parts and total > 0:
        parts.append(Segment("none", 0, Mark.GHOST))
    return tuple(parts)


def _top_language(repository: Repository) -> str:
    if not repository.languages:
        return "—"
    return max(repository.languages, key=lambda language: language.code).name


def repository_panel(repository: Repository, _prefix: str = "") -> str:
    if repository.state != "complete":
        detail = _e(repository.error or "not counted")
        return ui.panel("Code", f'<p class="unknown">not counted: {detail}</p>', panel_id="code")
    top = sorted(repository.languages, key=lambda language: (-language.code, language.name))[:5]
    body = ui.lines(
        [
            Line(_e(language.name), f"{_count(language.code)} code · {_count(language.files)} files")
            for language in top
        ]
    )
    return ui.panel("Code", body, panel_id="code")
