"""Generate and verify the owned-tools image inputs under `docker/owned-tools/`.

`tools.lock.json` is rendered from `fleet/policy/tools-lock.toml` for the tools
that publish a Linux musl asset for every supported image architecture, and
`bootstrap/` mirrors the vendored buildlib shim in
`fleet/policy/buildlib-bootstrap/`. `--write` refreshes both; the default check
mode exits nonzero when either drifts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

from repomod import buildlib_pins, paths, substitutes
from repomod.rules import tools_lock

IMAGE_DIR = paths.ROOT / "docker" / "owned-tools"
LOCK_PATH = IMAGE_DIR / "tools.lock.json"
BOOTSTRAP_DIR = IMAGE_DIR / "bootstrap"
IMAGE_POLICY_PATH = paths.POLICY / "owned-tools-image.toml"
DOCKERFILE_PATH = IMAGE_DIR / "Dockerfile"
MUSL_TRIPLES = ("aarch64-unknown-linux-musl", "x86_64-unknown-linux-musl")


def image_tools() -> list[str]:
    """The tools `owned-tools-image.toml` lists, each approved with a musl asset per image architecture."""
    raw = image_policy().get("tools")
    if not isinstance(raw, list) or not all(isinstance(tool, str) for tool in raw):
        raise ValueError("owned-tools image policy needs a tools list of names")
    listed = [str(tool) for tool in raw]
    approved = tools_lock._load_policy()
    for tool in listed:
        entry = approved.get(tool)
        if entry is None or not all(triple in entry["assets"] for triple in MUSL_TRIPLES):
            raise ValueError(f"owned-tools image tool {tool} has no approved musl asset for every architecture")
    return sorted(listed)


def render_lock() -> str:
    """The `tools.lock.json` text for the owned-tools image."""
    approved = tools_lock._load_policy()
    tools = {tool: approved[tool] for tool in image_tools()}
    return json.dumps({"schema": 1, "tools": tools}, indent=2, sort_keys=True) + "\n"


def bootstrap_sources() -> dict[str, str]:
    """Vendored buildlib shim files by name, from fleet policy."""
    return buildlib_pins.vendored_shims()


def planned_files() -> dict[Path, str]:
    """Every generated file under `docker/owned-tools/`, by path."""
    files = {LOCK_PATH: render_lock()}
    for name, content in bootstrap_sources().items():
        files[BOOTSTRAP_DIR / name] = content
    return files


def drift() -> list[str]:
    """Human-readable mismatches between the shipped files and their sources."""
    problems: list[str] = []
    for path, content in planned_files().items():
        try:
            existing = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            problems.append(f"{path}: cannot read ({error})")
            continue
        if existing != content:
            problems.append(
                f"{path}: differs from fleet policy; "
                "run `uv run python -m repomod.owned_tools_image --write`"
            )
    return problems


def image_policy() -> dict[str, Any]:
    """The parsed `fleet/policy/owned-tools-image.toml`."""
    path = paths.POLICY / "owned-tools-image.toml"
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"owned-tools image policy is missing or not a regular file: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"cannot load owned-tools image policy: {error}") from error
    return data


_PACKAGE_MANAGERS = frozenset({"apk", "apt", "brew", "dnf", "pacman"})


def package_map() -> dict[str, dict[str, str]]:
    """Upstream package to image tool, per package manager, from `owned-tools-image.toml`.

    A key starting with `^` is a regular expression matched against the whole
    package name; every other key is a literal package name. Every value must
    name a tool the image ships.
    """
    raw = image_policy().get("packages", {})
    if not isinstance(raw, dict):
        raise ValueError("owned-tools image policy packages must be a table")
    tools = frozenset(image_tools())
    result: dict[str, dict[str, str]] = {}
    for manager, entries in raw.items():
        normalized = substitutes.MANAGER_ALIASES.get(str(manager), str(manager))
        if normalized not in _PACKAGE_MANAGERS:
            raise ValueError(f"owned-tools image policy packages names an unknown manager {manager!r}")
        if normalized in result:
            raise ValueError(f"owned-tools image policy packages lists manager {normalized} more than once")
        if not isinstance(entries, dict):
            raise ValueError(f"owned-tools image policy packages.{manager} must be a table")
        mapped: dict[str, str] = {}
        for package, tool in entries.items():
            label = f"packages.{manager}.{package}"
            if not isinstance(package, str) or not package.strip():
                raise ValueError(f"{label} must be a non-empty package name")
            package = package.strip()
            if package.startswith("^"):
                try:
                    re.compile(package)
                except re.error as error:
                    raise ValueError(f"{label} is not a valid package pattern: {error}") from error
            if not isinstance(tool, str) or tool not in tools:
                raise ValueError(f"{label} names {tool!r}, which is not an owned-tools image tool")
            mapped[package] = tool
        result[normalized] = mapped
    return result


def dockerfile_text() -> str:
    if DOCKERFILE_PATH.is_symlink() or not DOCKERFILE_PATH.is_file():
        raise ValueError(f"owned-tools Dockerfile is missing or not a regular file: {DOCKERFILE_PATH}")
    return DOCKERFILE_PATH.read_text(encoding="utf-8")


def _write() -> int:
    for path, content in planned_files().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path}")
    return 0


def _check() -> int:
    problems = drift()
    for problem in problems:
        print(f"repomod: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"owned-tools image inputs match fleet policy ({len(image_tools())} tools)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="regenerate tools.lock.json and bootstrap/ from fleet policy",
    )
    args = parser.parse_args(argv)
    return _write() if args.write else _check()


if __name__ == "__main__":
    raise SystemExit(main())
