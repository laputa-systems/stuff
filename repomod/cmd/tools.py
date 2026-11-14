from __future__ import annotations

import argparse
import json
import os

from repomod.owned_tools import coverage, coverage_json, load_owned_tools, usr_installed, which

from . import common

_OWNED = {"owned"}
_COVERED = {"implemented", "not-applicable"}


def _which(args: argparse.Namespace) -> int:
    catalog = common.default_catalog()
    result = which(args.command_name, catalog, load_owned_tools(), os.environ)
    if args.json:
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
    return 0 if result["status"] in _OWNED else 1


def _coverage(args: argparse.Namespace) -> int:
    catalog = common.default_catalog()
    policy = load_owned_tools()
    installed, error = usr_installed(catalog, policy)
    entries = coverage(catalog, policy, installed)
    if args.json:
        print(coverage_json(entries))
    else:
        for entry in entries:
            print(f"{entry.repository}: {entry.state}: {entry.detail}")
        if error is not None:
            print(f"installer inventory unavailable: {error}")
    return 0 if error is None and all(entry.state in _COVERED for entry in entries) else 1


def _tools(args: argparse.Namespace) -> int:
    return {"which": _which, "coverage": _coverage}[args.operation](args)
