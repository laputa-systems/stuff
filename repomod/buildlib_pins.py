from __future__ import annotations

import hashlib
import tomllib
from types import MappingProxyType

from repomod import paths

_BOOTSTRAP_DIR = paths.POLICY / "buildlib-bootstrap"

VENDORED_SHIMS = MappingProxyType({
    name: (_BOOTSTRAP_DIR / name).read_text(encoding="utf-8")
    for name in ("buildlib-run", "python.lock")
})

WHEEL_URL = next(
    line.split()[1]
    for line in VENDORED_SHIMS["python.lock"].splitlines()
    if line.startswith("wheel ")
)

_WHEEL_SIZE = tomllib.loads((paths.POLICY / "buildlib.toml").read_text(encoding="utf-8"))["artifact"]["wheel_size"]
if not isinstance(_WHEEL_SIZE, int):
    raise ValueError("fleet/policy/buildlib.toml artifact wheel_size must be an integer")
WHEEL_SIZE: int = _WHEEL_SIZE

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


def shim_sha256(name: str) -> str:
    return hashlib.sha256(VENDORED_SHIMS[name].encode("utf-8")).hexdigest()


def approved_shim(name: str, digests: frozenset[str]) -> str | None:
    content = VENDORED_SHIMS.get(name)
    if content is None or shim_sha256(name) not in digests:
        return None
    return content
