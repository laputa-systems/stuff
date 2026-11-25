from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from pathlib import Path
from threading import Lock

from repomod.run_cache import cached


class _Entry:
    __slots__ = ("is_symlink", "name")

    def __init__(self, name: str, is_symlink: bool) -> None:
        self.name = name
        self.is_symlink = is_symlink


class _Node:
    __slots__ = ("dirs", "files")

    def __init__(self, dirs: list[_Entry], files: list[str]) -> None:
        self.dirs = dirs
        self.files = files


class _Index:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._nodes: dict[str, _Node | OSError] = {}
        self._lock = Lock()

    def _scan(self, directory: Path) -> _Node | OSError:
        try:
            with os.scandir(directory) as iterator:
                entries = list(iterator)
        except OSError as error:
            return error
        dirs: list[_Entry] = []
        files: list[str] = []
        for entry in entries:
            try:
                is_dir = entry.is_dir()
            except OSError:
                is_dir = False
            if is_dir:
                dirs.append(_Entry(entry.name, entry.is_symlink()))
            else:
                files.append(entry.name)
        return _Node(dirs, files)

    def _node(self, directory: Path) -> _Node | OSError:
        key = str(directory)
        with self._lock:
            node = self._nodes.get(key)
        if node is not None:
            return node
        scanned = self._scan(directory)
        with self._lock:
            self._nodes.setdefault(key, scanned)
        return scanned

    def walk(
        self, onerror: Callable[[OSError], object] | None
    ) -> Iterator[tuple[Path, list[str], list[str]]]:
        stack = [self._root]
        while stack:
            directory = stack.pop()
            node = self._node(directory)
            if isinstance(node, OSError):
                if onerror is not None:
                    onerror(node)
                continue
            names = [entry.name for entry in node.dirs]
            files = list(node.files)
            yield directory, names, files
            known = {entry.name: entry for entry in node.dirs}
            for name in reversed(names):
                entry = known.get(name)
                if entry is None or entry.is_symlink:
                    continue
                stack.append(directory / name)


def walk(
    root: Path,
    *,
    onerror: Callable[[OSError], object] | None = None,
) -> Iterator[tuple[Path, list[str], list[str]]]:
    index = cached(("fs-index", root), lambda: _Index(root))
    yield from index.walk(onerror)
