# Repomod dead-code review

Vulture 2.16 reported eight findings in `repomod/` at `c71dee1d`, all at
60% confidence. Run it from the Stuff root with the pinned Python environment.

```sh
mkdir -p .work/tmp
TMPDIR="$PWD/.work/tmp" uvx \
  --default-index https://pypi.17166969.xyz/current/simple/ \
  --from vulture==2.16 vulture repomod tests/repomod --min-confidence 60
```

The dependency model's `Index` dataclass and `TagPredicate.describe` had
no callers in source, tests, scripts or other fleet checkouts. The snapshot
writer builds the serialized index from `IndexEntry` records. Rule selection
uses `TagPredicate.matches`. The unused class and method were removed.

The other six production findings still serve callers:

| Finding | Consumer |
| --- | --- |
| `Resolution.UNSUPPORTED` | The graph reader accepts the documented persisted `unsupported` value through `Resolution(value)`. |
| `Mark.OTHER` | The dependency weight view builds its legend from `LANGUAGES`, including the `other` key, through `Mark(language.key)`. |
| `BanMatch.EXACT` | Dependency policy loads `exact` from role configuration through `BanMatch(value)`. |
| `whitespace_split` and `commenters` in `rules/formatters.py` | `shlex` reads these attributes when the rule tokenizes formatter commands. |
| `whitespace_split` in `rules/typescript_standard.py` | `shlex` reads this attribute when the rule tokenizes TypeScript commands. |

The scan also reports pytest fixture parameters, callback parameters and
HTML parser overrides in test files. Pytest injects the fixtures by name and
the fake transports and parser call those methods through their interfaces.
The campaign's effect-boundary Tests qualification remains open.

## Runtime-only and dependency scans

At `4eabeae6`, a second Vulture run over `repomod/` alone exposed six
names whose references came only from tests. Remove two maintenance
wrappers. The vendored path predicate had no production caller, and
the tests for Cargo, JavaScript, Python, Swift and Zig still exercise
real vendored provenance. The static ELF wrapper returned the script
constant unchanged. The checked-in verifier test now compares directly
against that constant and still checks its executable mode. Release
workflow generation continues to use the same script body. Searches
of the tracked files and local fleet checkouts found only the two
Stuff test call sites.

The later passes moved the Musl refresh tests to the shipped pins
command and removed the test-only writer in [#84](https://github.com/laputa-systems/stuff/pull/84).
The dashboard and role reports read `RoleUse.options`,
`off_preferred` and `overlapping`. `RoleUse.excepted` had only one
test caller across the tracked files and local fleet checkouts.
The test now verifies both of the dashboard inputs that matter for
exceptions. The repository is counted under its actual dependency
and excluded from the migration count.

The `add_repository` writer had no command or external caller. Catalog
discovery writes pending entries, and adding tags in the catalog
promotes them. Removing the unused writer leaves the tests for manual
promotion and catalog validation in place. The shipped pending writer
still has concurrent update, comment preservation and idempotence
coverage.

The unused `audit_repositories` batch and its private worker duplicated
the shipped audit rules, version lookup and fork status paths. Tracked
fleet checkouts only referenced the batch from the old Stuff audit tests.
The tests now verify an advisory and cache through the shipped rule,
and a stale-version cache through the shared resolver. Fork status and
comparison errors are covered by the GitHub policy tests.

Deptry 0.25.1 reported zero dependency issues across 112 files after
mapping the `ruamel.yaml` distribution to its import root and identifying
`mutants_gate` as the local source of the copied gate self-test:

```sh
TMPDIR="$PWD/.work/tmp" uvx \
  --default-index https://pypi.17166969.xyz/current/simple/ \
  --from deptry==0.25.1 deptry --no-ansi --config pyproject.toml \
  --known-first-party repomod --known-first-party mutants_gate \
  --package-module-name-map ruamel.yaml=ruamel repomod
```

Ruff F401 and F841 passed across the component and tests. The three
runtime dependencies have executable consumers. `packaging` parses
requirements, versions and names in the inventory and mirror,
`ruamel.yaml` parses and edits workflows, and `tomlkit` preserves
Cargo manifest formatting in the upgrade rule. The dev entries are
CLI tools or pytest and its plugin.
