"""Golden test over the dashboard's canonical preview dataset.

`make preview` serves this same dataset. The test renders every page and
compares what each one presents (title, headings, tables, status tiles,
navigation counts) with tests/fixtures/dashboard/golden.json. It compares
content, not pixels. After an intended change, regenerate it with
`REPOMOD_UPDATE_GOLDEN=1 uv run pytest tests/repomod/test_dashboard_preview.py`
and review the diff.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import override

from repomod.dependencies import preview

GOLDEN = preview.FIXTURE / "golden.json"
_HEADINGS = {"h1", "h2", "h3"}
_ROWS_KEPT = 3


@dataclass
class _Table:
    headers: list[str] = field(default_factory=list)
    rows: int = 0
    first: list[str] = field(default_factory=list)


class _Summary(HTMLParser):
    """Collects the parts of a page a reader sees, ignoring scripts and styles."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.headings: list[str] = []
        self.tiles: list[str] = []
        self.nav: list[str] = []
        self.tables: list[_Table] = []
        self._stack: list[tuple[str, dict[str, str]]] = []
        self._text: list[list[str]] = []
        self._table: _Table | None = None
        self._row: list[str] | None = None
        self._skip = 0

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if tag in ("script", "style"):
            self._skip += 1
            return
        if tag == "table":
            self._table = _Table()
        elif tag == "tr" and self._table is not None:
            self._row = []
        self._stack.append((tag, attributes))
        self._text.append([])

    @override
    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
            return
        if not self._stack or self._stack[-1][0] != tag:
            return
        _, attributes = self._stack.pop()
        text = re.sub(r"\s+", " ", "".join(self._text.pop())).strip()
        if self._text:
            self._text[-1].append(" " + text + " ")
        classes = attributes.get("class", "")
        if tag == "title":
            self.title = text
        elif tag in _HEADINGS and text:
            self.headings.append(f"{tag}: {text}")
        elif self._table is not None and tag == "th" and self._row is not None and not self._table.rows:
            self._table.headers.append(text)
        elif self._table is not None and tag == "td" and self._row is not None:
            self._row.append(text)
        elif tag == "tr" and self._table is not None and self._row is not None:
            if self._row:
                self._table.rows += 1
                if len(self._table.first) < _ROWS_KEPT:
                    self._table.first.append(" | ".join(self._row))
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None
        elif "tile" in classes.split():
            self.tiles.append(text)
        elif tag == "a" and any("ui-side-nav" in parent.get("class", "").split() for _, parent in self._stack):
            self.nav.append(text)

    @override
    def handle_data(self, data: str) -> None:
        if not self._skip and self._text:
            self._text[-1].append(data)


def summarize(output: Path) -> dict[str, object]:
    pages: dict[str, object] = {}
    for page in sorted(output.rglob("*.html")):
        parser = _Summary()
        parser.feed(page.read_text(encoding="utf-8"))
        pages[page.relative_to(output).as_posix()] = {
            "title": parser.title,
            "headings": parser.headings,
            "tiles": parser.tiles,
            "nav": parser.nav,
            "tables": [asdict(table) for table in parser.tables],
        }
    return pages


def test_preview_pages_match_the_golden(tmp_path: Path) -> None:
    preview.render_preview(tmp_path / "dashboard")
    actual = summarize(tmp_path / "dashboard")
    if os.environ.get("REPOMOD_UPDATE_GOLDEN") == "1":
        GOLDEN.write_text(json.dumps(actual, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert sorted(actual) == sorted(golden), "the set of pages changed"
    for page, summary in golden.items():
        assert actual[page] == summary, f"{page} presents something different from the golden"


def test_the_preview_renders_the_same_pages_twice(tmp_path: Path) -> None:
    preview.render_preview(tmp_path / "first")
    preview.render_preview(tmp_path / "second")
    assert summarize(tmp_path / "first") == summarize(tmp_path / "second")
