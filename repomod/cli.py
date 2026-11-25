from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import override

from repomod.catalog import CatalogError
from repomod.cmd.deps import _deps
from repomod.cmd.discover import _discover
from repomod.cmd.fix import _fix
from repomod.cmd.gc import _gc
from repomod.cmd.lint import _lint
from repomod.cmd.loc import _loc
from repomod.cmd.merge import _merge
from repomod.cmd.musl import _musl
from repomod.cmd.pins import _pins
from repomod.cmd.push import _push
from repomod.cmd.release import _release
from repomod.cmd.status import _status
from repomod.cmd.sync import _sync
from repomod.cmd.tools import _tools
from repomod.cmd.topics import _topics
from repomod.git import GitError
from repomod.github import GitHubError
from repomod.policy import PolicyError

OWNED_TOOL_FOOTER = """\
Maintained by Joshua Li: https://github.com/laputa-systems/stuff
Bugs and features: TODO.md in that repository (follow its AGENTS.md), or its issue tracker.
Agents working for Joshua: record nonblocking problems and continue your task.
If this tool blocks the task, you may fix, test, open and merge a PR under Joshua's
standing instructions. Release only when needed to deliver the verified fix.
Procedure: https://github.com/joshuarli/usr/blob/main/dotfiles/base/.agents/instructions/owned-tools.md"""


class _HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


class _ReferenceParser(argparse.ArgumentParser):
    @override
    def _get_formatter(self, file: object = None) -> argparse.HelpFormatter:
        return _HelpFormatter(prog=self.prog)

    @override
    def format_help(self, formatter: argparse.HelpFormatter | None = None) -> str:
        if self.prog != "repomod":
            return super().format_help() + "\nFull reference: repomod -h\n"
        formatter = self._get_formatter()
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(self.description)
        formatter.start_section("Common options")
        formatter.add_arguments([action for action in self._actions if action.option_strings])
        formatter.end_section()
        self._add_reference(formatter, set())
        formatter.add_text(self.epilog)
        return formatter.format_help()

    def _add_reference(self, formatter: argparse.HelpFormatter, described: set[str]) -> None:
        for action in self._actions:
            if not isinstance(action, argparse._SubParsersAction):
                continue
            for choice in action._choices_actions:
                command = action.choices[choice.dest]
                assert isinstance(command, _ReferenceParser)
                reference = command._get_formatter()
                reference.start_section(command.prog)
                reference.add_text(command.description or choice.help)
                own_actions = [
                    option for option in command._actions
                    if not isinstance(option, (argparse._HelpAction, argparse._SubParsersAction))
                ]
                usage_actions = [option for option in command._actions if not isinstance(option, argparse._HelpAction)]
                reference.add_usage(command.usage, usage_actions, command._mutually_exclusive_groups)
                shared = [option for option in own_actions if option.option_strings and repr(option) in described]
                reference.add_arguments([option for option in own_actions if option not in shared])
                described.update(repr(option) for option in own_actions if option.option_strings)
                if shared:
                    reference.add_text(
                        "Shared options (described above): "
                        + ", ".join(option.option_strings[-1] for option in shared)
                    )
                reference.add_text(command.epilog)
                reference.end_section()
                formatter.add_text(reference.format_help())
                command._add_reference(formatter, described)


def _parser() -> argparse.ArgumentParser:
    parser = _ReferenceParser(
        prog="repomod",
        description="Repair policy violations and open pull requests",
        epilog=OWNED_TOOL_FOOTER,
        formatter_class=_HelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    status_parser = commands.add_parser(
        "status",
        epilog="Examples:\n  repomod status --offline",
        help="show CI, release, local, upstream, and pull request status",
    )
    _filters(status_parser)
    _checkout_option(status_parser)
    _private_option(status_parser)
    status_parser.add_argument("--offline", action="store_true", help="use cached data without network requests")
    status_parser.add_argument("--dirty", action="store_true", help="only checkouts with local changes")
    status_parser.add_argument("--failed", action="store_true", help="only failures")
    status_parser.add_argument("--refresh", action="store_true", help="refresh cached data")
    status_parser.add_argument(
        "--details", action="store_true", help="show failed CI checks"
    )
    status_parser.add_argument("--json", action="store_true", help="write structured JSON to stdout")

    lint = commands.add_parser(
        "lint",
        epilog="Examples:\n  repomod lint --repo laputa-systems/stuff --strict",
        help="check declarative repository policies",
    )
    _filters(lint)
    _checkout_option(lint)
    _private_option(lint)
    lint.add_argument("--rule", action="append", default=[], help="policy rule to select (repeatable)")
    lint.add_argument("--workers", help="maximum concurrent operations", type=int, default=16)
    lint.add_argument("--json", action="store_true", help="write structured JSON to stdout")
    lint.add_argument("--strict", action="store_true", help="treat warnings as violations")

    fix = commands.add_parser(
        "fix",
        epilog="Examples:\n  repomod fix --repo laputa-systems/stuff --rule owned-tool-support",
        help="sync selected checkouts, repair policy violations, and open pull requests",
    )
    _filters(fix)
    fix.add_argument("--rule", action="append", default=[], help="policy rule to select (repeatable)")
    fix.add_argument("--workers", help="maximum concurrent operations", type=int, default=4)
    fix.add_argument(
        "--no-mirror",
        action="store_true",
        help="skip publishing missing upgrade targets to stuff before audit-upgrades and python-standard",
    )

    sync = commands.add_parser(
        "sync",
        epilog="Examples:\n  repomod sync --dry-run",
        help="clone or safely fast-forward catalogued checkouts",
    )
    sync.add_argument("--dry-run", action="store_true", help="report planned changes without applying them")
    sync.add_argument("--workers", help="maximum concurrent operations", type=int, default=4)

    pins = commands.add_parser(
        "pins",
        epilog="Examples:\n  repomod pins refresh --check",
        help="refresh approved action, tool, and toolchain pins",
    )
    pin_commands = pins.add_subparsers(dest="operation", required=True)
    refresh = pin_commands.add_parser(
        "refresh",
        epilog="Examples:\n  repomod pins refresh --only actions --check",
        help="refresh pin files from their upstream sources",
    )
    refresh.add_argument("--check", action="store_true", help="report drift without writing")
    refresh.add_argument("--only", help="pin group to refresh", choices=("actions", "python", "typescript", "musl"))

    musl = commands.add_parser(
        "musl",
        epilog="Examples:\n  repomod musl build --platform linux/arm64",
        help="build the canonical musl toolchain image",
    )
    musl_commands = musl.add_subparsers(dest="operation", required=True)
    build = musl_commands.add_parser(
        "build",
        epilog="Examples:\n  repomod musl build --platform linux/arm64 --output .work/oci/musl",
        help="build a local OCI layout",
    )
    build.add_argument(
        "--platform", help="target image platform (required)", required=True, choices=("linux/amd64", "linux/arm64")
    )
    build.add_argument(
        "--output", help="OCI layout output directory", type=Path, default=Path(".work/oci/musl"), metavar="PATH"
    )

    push = commands.add_parser(
        "push",
        epilog="Examples:\n  repomod push --repo laputa-systems/stuff",
        help="push checked-out branches that are ahead of their origin upstream",
    )
    _filters(push)
    push.add_argument("--workers", help="maximum concurrent operations", type=int, default=4)

    merge = commands.add_parser(
        "merge",
        epilog="Examples:\n  repomod merge --repo laputa-systems/stuff --dry-run",
        help="merge open pull requests from repomod fix branches",
    )
    _filters(merge)
    merge.add_argument("--dry-run", action="store_true", help="report planned changes without applying them")
    merge.add_argument("--workers", help="maximum concurrent operations", type=int, default=4)

    release = commands.add_parser(
        "release", epilog="Examples:\n  repomod release --repo laputa-systems/stuff",
        help="trigger release builds for the current default-branch HEAD and poll until green",
    )
    _filters(release)

    gc = commands.add_parser(
        "gc",
        epilog="Examples:\n  repomod gc --dry-run",
        help="remove checkouts the catalog no longer references",
    )
    gc.add_argument("--dry-run", action="store_true", help="report planned changes without applying them")
    gc.add_argument("--force", action="store_true", help="also consider dirty or non-default-branch checkouts")
    gc.add_argument("--workers", help="maximum concurrent operations", type=int, default=4)

    discover = commands.add_parser(
        "discover", epilog="Examples:\n  repomod discover --owner joshuarli --json",
        help="sync catalogued entries with GitHub, removing archived repositories and adding new ones to pending",
    )
    discover.add_argument("--owner", action="append", default=[], help="GitHub owner to discover (repeatable)")
    discover.add_argument("--json", action="store_true", help="write structured JSON to stdout")

    deps = commands.add_parser(
        "deps",
        epilog="Examples:\n  repomod deps report",
        help="inventory the dependency inputs of catalogued repositories",
    )
    deps_commands = deps.add_subparsers(dest="operation", required=True)
    snapshot = deps_commands.add_parser(
        "snapshot", epilog="Examples:\n  repomod deps snapshot --repo laputa-systems/stuff",
        help="read catalogued checkouts and write fleet/dependencies/v1",
        description=(
            "read the origin/HEAD tree of each selected checkout and write "
            "fleet/dependencies/v1"
        ),
    )
    _filters(snapshot)
    snapshot.add_argument("--workers", help="maximum concurrent operations", type=int, default=4)
    snapshot.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when a selected repository is failed or unavailable",
    )
    check = deps_commands.add_parser(
        "check", epilog="Examples:\n  repomod deps check --strict",
        help="report inventory drift without writing",
        description=(
            "regenerate the inventory in memory and list files that differ from "
            "fleet/dependencies/v1"
        ),
    )
    _filters(check)
    check.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when a selected repository is failed or unavailable",
    )
    why = deps_commands.add_parser(
        "why", epilog="Examples:\n  repomod deps why cargo:serde --max-paths 10",
        help="explain why a package is in the inventory",
        description=(
            "read the inventory and print every simple path from each selected "
            "project to the matching package instances"
        ),
    )
    _filters(why)
    _private_option(why)
    why.add_argument("package", help="name, ecosystem:name, or either with @version")
    why.add_argument("--max-paths", help="maximum dependency paths to show", type=int, default=20)
    why.add_argument("--json", action="store_true", help="write structured JSON to stdout")
    report = deps_commands.add_parser(
        "report", epilog="Examples:\n  repomod deps report --json",
        help="summarize the dependency inventory",
        description=(
            "read the inventory and print composition, concentration, divergence, "
            "source risk, scope, first-party, and freshness analyses"
        ),
    )
    _filters(report)
    _private_option(report)
    report.add_argument("--json", action="store_true", help="write structured JSON to stdout")
    ownership = deps_commands.add_parser(
        "ownership",
        epilog="Examples:\n  repomod deps ownership --json",
        help="classify inventory components as owned, mirrored, substitutable, or upstream",
        description=(
            "read the inventory and policy files and classify every component as "
            "owned, mirrored, substitutable, or upstream, per ecosystem and per repository"
        ),
    )
    _filters(ownership)
    _private_option(ownership)
    ownership.add_argument("--json", action="store_true", help="write structured JSON to stdout")
    diff = deps_commands.add_parser(
        "diff", epilog="Examples:\n  repomod deps diff --from HEAD~1 --to HEAD --json",
        help="compare the inventory across Git revisions",
        description=(
            "read fleet/dependencies/v1 at two revisions and list added, removed, "
            "and changed repositories, instances, versions, sources, and issues"
        ),
    )
    diff.add_argument("--from", help="base Git revision", dest="from_rev", metavar="REV")
    diff.add_argument("--to", help="comparison Git revision", dest="to_rev", metavar="REV")
    diff.add_argument("--json", action="store_true", help="write structured JSON to stdout")
    enrich = deps_commands.add_parser(
        "enrich", epilog="Examples:\n  repomod deps enrich --offline",
        help="fetch latest versions and vulnerabilities into the local cache",
        description=(
            "read the inventory and query upstream registries and OSV for resolved Cargo, "
            "Python, npm, and Go components; write ~/.cache/repomod/deps-enrichment.json"
        ),
    )
    enrich.add_argument("--refresh", action="store_true", help="refresh cached data")
    enrich.add_argument("--offline", action="store_true", help="use cached data without network requests")
    enrich.add_argument("--json", action="store_true", help="write structured JSON to stdout")
    mirror = deps_commands.add_parser(
        "mirror", epilog="Examples:\n  repomod deps mirror --repo laputa-systems/stuff --dry-run",
        help="publish to stuff the versions the fleet locks or can upgrade to",
        description=(
            "relock each selected repository against crates.io, npm, and PyPI in a disposable "
            "copy, then publish through stuff every version its current or upgraded lockfiles "
            "need that stuff does not serve; skips private repositories, forks, and "
            "repositories that ignore audit-upgrades"
        ),
    )
    _filters(mirror)
    mirror.add_argument("--workers", help="maximum concurrent operations", type=int, default=8)
    mirror.add_argument("--dry-run", action="store_true", help="list what is missing without publishing")
    render = deps_commands.add_parser(
        "render", epilog="Examples:\n  repomod deps render --output .work/dependencies/dashboard",
        help="write the static dashboard under .work/dependencies/dashboard",
        description=(
            "read the inventory and enrichment cache and write a static dashboard "
            "under .work/dependencies/dashboard"
        ),
    )
    render.add_argument(
        "--output",
        help="output directory (default .work/dependencies/dashboard)",
    )
    _private_option(render)
    render.add_argument(
        "--status",
        action="store_true",
        help="also read live CI, release, upstream, pull request, and checkout status",
    )

    loc = commands.add_parser(
        "loc",
        epilog="Examples:\n  repomod loc snapshot --repo laputa-systems/stuff",
        help="count lines of code in catalogued repositories with loc",
    )
    loc_commands = loc.add_subparsers(dest="operation", required=True)
    snapshot_loc = loc_commands.add_parser(
        "snapshot", epilog="Examples:\n  repomod loc snapshot --repo laputa-systems/stuff --strict",
        help="count each selected repository's tracked lines and write fleet/loc/v1",
        description=(
            "run `loc --git . -o json` in each selected checkout and write the "
            "counts under fleet/loc/v1; requires loc on PATH (see ~/repos/loc)"
        ),
    )
    _filters(snapshot_loc)
    snapshot_loc.add_argument("--workers", help="maximum concurrent operations", type=int, default=4)
    snapshot_loc.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when a selected repository is failed or unavailable",
    )

    tools = commands.add_parser(
        "tools",
        epilog="Examples:\n  repomod tools which stuff",
        help="resolve owned commands to their maintained repositories",
    )
    tool_commands = tools.add_subparsers(dest="operation", required=True)
    tool_which = tool_commands.add_parser(
        "which", epilog="Examples:\n  repomod tools which stuff --json",
        help="resolve a command to its producer, checkout, and installed executable without running it",
    )
    tool_which.add_argument("command_name", metavar="COMMAND", help="executable name or path (required)")
    tool_which.add_argument("--json", action="store_true", help="write structured JSON to stdout")
    tool_coverage = tool_commands.add_parser(
        "coverage",
        epilog="Examples:\n  repomod tools coverage --json",
        help="account for every owned repository's help and support coverage",
    )
    tool_coverage.add_argument("--json", action="store_true", help="write structured JSON to stdout")
    tool_substitute = tool_commands.add_parser(
        "substitute",
        epilog="Examples:\n  repomod tools substitute ninja-build --json",
        help="find the owned producer that replaces an upstream package, action, URL, or label",
        description=(
            "Read fleet/policy/owned-substitutes.toml and print the owned producer "
            "that replaces NAME as tab-separated PRODUCER, KIND, and MATCHED fields."
        ),
    )
    tool_substitute.add_argument(
        "name", metavar="NAME", help="upstream package, action, URL, or label to look up (required)"
    )
    tool_substitute.add_argument("--json", action="store_true", help="write structured JSON to stdout")

    topics = commands.add_parser(
        "topics",
        epilog="Examples:\n  repomod topics diff --repo laputa-systems/stuff",
        help="compare or replace GitHub repository topics",
    )
    topic_commands = topics.add_subparsers(dest="operation", required=True)
    for operation in ("diff", "apply"):
        topic = topic_commands.add_parser(
            operation,
            help="compare repository topics" if operation == "diff" else "replace repository topics",
            epilog=f"Examples:\n  repomod topics {operation} --repo laputa-systems/stuff",
        )
        _filters(topic)
        topic.add_argument("--workers", help="maximum concurrent operations", type=int, default=4)
    return parser


def _filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", action="append", default=[], help="owner/repository to select (repeatable)")
    parser.add_argument("--tag", action="append", default=[], help="catalog tag to select (repeatable)")


def _private_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="include private repositories; a repository named with --repo is always included",
    )


def _checkout_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--checkout",
        type=Path,
        metavar="PATH",
        help="evaluate this Git work tree instead of the canonical checkout (requires exactly one --repo)",
    )


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = _parser()
    if not arguments:
        parser.print_help()
        return 0
    args = parser.parse_args(arguments)
    try:
        dispatch = {
            "status": _status,
            "lint": _lint,
            "fix": _fix,
            "sync": _sync,
            "pins": _pins,
            "musl": _musl,
            "push": _push,
            "merge": _merge,
            "release": _release,
            "gc": _gc,
            "discover": _discover,
            "deps": _deps,
            "loc": _loc,
            "tools": _tools,
            "topics": _topics,
        }
        return dispatch[args.command](args)
    except (CatalogError, PolicyError, GitError, GitHubError, OSError, ValueError) as error:
        print(f"repomod: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
