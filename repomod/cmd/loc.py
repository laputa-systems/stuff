from __future__ import annotations

import argparse
import shutil
import sys

from repomod import loc as loc_module
from repomod.cmd import common


def _loc(args: argparse.Namespace) -> int:
    if args.operation == "snapshot":
        if shutil.which("loc") is None:
            print(
                "repomod loc: `loc` is required; build it with `cargo install --path .` in ~/repos/loc "
                "(see https://github.com/joshuarli/loc)",
                file=sys.stderr,
            )
            return 2
        catalog = common.default_catalog()
        repositories = common.select_repositories(
            catalog, getattr(args, "repo", []), getattr(args, "tag", [])
        )
        filtered = bool(getattr(args, "repo", []) or getattr(args, "tag", []))
        result = loc_module.snapshot(
            catalog,
            repositories,
            filtered=filtered,
            workers=args.workers,
        )
        counts = dict.fromkeys(("complete", "failed", "unavailable"), 0)
        for item in result.repositories:
            counts[item.state] = counts.get(item.state, 0) + 1
        print(
            f"{len(result.repositories)} repositories: "
            f"complete {counts['complete']}, failed {counts['failed']}, "
            f"unavailable {counts['unavailable']}"
        )
        for item in result.repositories:
            if item.state != "complete":
                print(f"{item.repository}: {item.error}")
        if result.written:
            print(f"wrote {len(result.written)} files")
        else:
            print("line counts are current")
        if result.deleted:
            print(f"deleted {len(result.deleted)} stale files")
        if args.strict and (counts["failed"] or counts["unavailable"]):
            return 1
        return 0
    raise ValueError(f"unknown operation: {args.operation}")
