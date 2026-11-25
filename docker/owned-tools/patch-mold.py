"""Repoint mold's `libgcc_s.so.1` NEEDED entry at the copy shipped in the image.

mold's musl release links libgcc dynamically, but no fleet base image ships
libgcc_s, and the dynstr slot for the name is exactly 13 bytes, so the library
is installed at `/opt/laputa/g` and the in-place rewrite fits. The script runs
under the buildlib-bootstrapped Python inside the image build.
"""

from __future__ import annotations

import sys
from pathlib import Path

OLD = b"libgcc_s.so.1"
NEW = b"/opt/laputa/g"


def patch(path: Path) -> int:
    if len(OLD) != len(NEW):
        raise ValueError("in-place NEEDED rewrite requires equal lengths")
    data = path.read_bytes()
    patched = bytearray(data)
    count = 0
    start = 0
    while True:
        index = data.find(OLD, start)
        if index < 0:
            break
        start = index + 1
        if index + len(OLD) >= len(data) or data[index + len(OLD)] != 0:
            continue
        patched[index : index + len(NEW)] = NEW
        count += 1
    if count == 0:
        print(f"patch-mold: no NUL-terminated {OLD!r} in {path}", file=sys.stderr)
        return 1
    path.write_bytes(bytes(patched))
    print(f"patch-mold: repointed {count} {OLD!r} NEEDED string(s) in {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: patch-mold.py <mold-binary>", file=sys.stderr)
        return 2
    return patch(Path(args[0]))


if __name__ == "__main__":
    raise SystemExit(main())
