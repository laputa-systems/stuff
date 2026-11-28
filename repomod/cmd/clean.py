from __future__ import annotations

import argparse
import sys

from repomod.artifacts import clean_repositories

from . import common


def _clean(args: argparse.Namespace) -> int:
    if args.workers < 1:
        raise ValueError("--workers must be at least one")
    catalog = common.default_catalog()
    repositories = common.select_repositories(catalog, args.repo, args.tag)
    results = clean_repositories(
        catalog, repositories, dry_run=args.dry_run, jobs=args.workers
    )
    failed = False
    for result in results:
        line = f"{result.repository}: {result.action}: {result.message}"
        if result.failed:
            print(line, file=sys.stderr)
        else:
            print(line)
        failed |= result.failed
    if not results:
        print("no cached build artifacts")
    return 1 if failed else 0
