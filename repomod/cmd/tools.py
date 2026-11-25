from __future__ import annotations

import argparse
import sys

from repomod import substitutes
from repomod.owned_tools import coverage, coverage_json, load_owned_tools, usr_installed
from repomod.which import run as run_which

from . import common

_COVERED = {"implemented", "not-applicable"}


def _which(args: argparse.Namespace) -> int:
    return run_which(args.command_name, args.json)


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


def _substitute(args: argparse.Namespace) -> int:
    matches = substitutes.lookup(args.name)
    if args.json:
        common.print_json(
            [{"producer": match.producer, "kind": match.kind, "matched": match.matched} for match in matches]
        )
    else:
        for match in matches:
            print(f"{match.producer}\t{match.kind}\t{match.matched}")
    if matches:
        return 0
    print(f"repomod: no owned substitute for {args.name!r}", file=sys.stderr)
    return 1


def _tools(args: argparse.Namespace) -> int:
    return {"which": _which, "coverage": _coverage, "substitute": _substitute}[args.operation](args)
