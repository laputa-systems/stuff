"""`repomod tools which` without the project environment.

Owned-tool recovery runs this file with any Python 3.15 interpreter and no synchronization:
`python3 -I repomod/which.py COMMAND [--json]`. Keep its imports to the standard library and
repomod modules that import only the standard library.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json
import os

from repomod import paths
from repomod.catalog import load_catalog
from repomod.owned_tools import load_owned_tools, which


def run(command: str, as_json: bool) -> int:
    result = which(command, load_catalog(paths.CATALOG), load_owned_tools(), os.environ)
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['command']}: {result['status']}")
        for key in ("repository", "url", "upstream", "backlog", "procedure"):
            if result.get(key):
                print(f"  {key}: {result[key]}")
        if "producers" in result:
            print("  producers: " + ", ".join(result["producers"]))
        for key in ("checkout", "executable"):
            value = result.get(key)
            if isinstance(value, dict):
                details = ", ".join(f"{name}={item}" for name, item in value.items() if item not in (None, [], ""))
                print(f"  {key}: {details}")
    return 0 if result["status"] == "owned" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="repomod-which",
        description="Resolve a command to its producer, checkout, and installed executable without running it.",
    )
    parser.add_argument("command_name", metavar="COMMAND")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return run(args.command_name, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
