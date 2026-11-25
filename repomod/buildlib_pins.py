from __future__ import annotations

import hashlib
import tomllib

from repomod import paths

_SHIMS = ("buildlib-run", "python.lock")


def vendored_shims() -> dict[str, str]:
    """The released bootstrap files `fleet/policy/buildlib-bootstrap/` holds, by shim name; absent files are omitted."""
    directory = paths.POLICY / "buildlib-bootstrap"
    return {name: (directory / name).read_text(encoding="utf-8") for name in _SHIMS if (directory / name).is_file()}


def wheel_url() -> str:
    """The wheel URL the vendored `python.lock` pins."""
    for line in vendored_shims()["python.lock"].splitlines():
        if line.startswith("wheel "):
            return line.split()[1]
    raise ValueError("fleet/policy/buildlib-bootstrap/python.lock has no wheel record")


def wheel_size() -> int:
    """The approved wheel's byte size from `fleet/policy/buildlib.toml`."""
    size = tomllib.loads((paths.POLICY / "buildlib.toml").read_text(encoding="utf-8"))["artifact"]["wheel_size"]
    if not isinstance(size, int) or isinstance(size, bool):
        raise ValueError("fleet/policy/buildlib.toml artifact wheel_size must be an integer")
    return size


TOOLS_LOCK_TOOLS = frozenset({
    "gluon",
    "rg",
    "fd",
    "jaq",
    "git",
    "ssh",
    "oxish",
    "cmake",
    "node",
    "cpython",
    "llvm",
    "llvm-dev",
    "ffmpeg-runtime",
    "ffmpeg-tools",
    "ffmpeg-play-sdk",
    "ffmpeg-fixtures",
    "mold",
})


def approved_shim(name: str, digests: frozenset[str]) -> str | None:
    content = vendored_shims().get(name)
    if content is None or hashlib.sha256(content.encode("utf-8")).hexdigest() not in digests:
        return None
    return content
