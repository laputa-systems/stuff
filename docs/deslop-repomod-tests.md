# Repomod test inventory

Inventory reviewed at `96188b1038ac8bd8e26c0b50ce8a00240e93250a`; historical mutation results below retain their own revisions. Fixtures use local Git repositories, fake GitHub responses and synthetic registry documents. No new mutation trial or test was needed to disposition the recorded results.

| Boundary and critical decisions | Guarding tests | Remaining gap |
| --- | --- | --- |
| Catalog and CLI: closed tags, identity, path collisions, dispatch and exits | `test_catalog.py`, `test_cli.py` | Collision diagnostics below; other decisions not exhaustively mutated. |
| Checkout and removal: merge bases, dirty and detached state, archives and identity | `test_sync_upstream.py`, `test_sync_cleanup.py`, `test_gc.py`, `test_removal_safety.py` | Removal side effects and remaining sync decisions not exhaustively mutated. |
| Fix plans and publication: path admission, isolated copies, concurrent checkout and branch changes, refusal | `test_fix_safety.py`, `test_fix_command.py`, `test_fix_push.py` | Race-sensitive containment diagnostic and hosted qualification below; interruption after commit is DSLP-7. |
| Workflow: matrix includes and check names, retries and partial GraphQL responses | `test_github_policy.py`, `test_ci_workflow.py` | Decisions outside matrix expansion not exhaustively mutated. |
| Inventory: dependency and LOC snapshots, mirror catalog and dashboard adapter | `test_deps_snapshot.py`, `test_loc_snapshot.py`, `test_deps_world.py`, `test_dashboard_preview.py` | Filtered LOC index loses unselected entries (DSLP-8); remaining adapters not exhaustively mutated. |

The dashboard render and `make deps` consume snapshots; the preview golden test exercises the render using its canonical fixture. Acceptance is `TMPDIR="$PWD/.work/tmp" PYTHON_CPU_COUNT=2 cpu-guard --cores 2 -- make repomod-test` and the same invocation of `make repomod-lint`. `make deps` itself syncs and writes the live fleet and is not an isolated acceptance command. The suite's live-fleet and launcher cases are opt-in. The recorded mutation runs used macOS arm64 and CPython 3.15.2; other platforms and live integrations were not qualified by those runs.

## Mutation dispositions

- **Catalog identity:** eight case-fold collision identities survive because callers reject duplicate identities before the collision path; see [catalog admission](deslop-catalog-admission.md). They are unreachable through current callers, not a blanket platform claim.
- **Removal and upstream:** 19 removal blocker and 25 upstream-fetch identities were caught; other removal and sync regions remain unrun. See [removal](deslop-repomod-removal.md) and [upstream](deslop-upstream-state.md).
- **Path admission:** `_validate_path` 27 is equivalent on supported Python (`strict=None` and `False`); 29 removes a containment diagnostic that the fixtures do not reach after the symlink walk. The latter is unqualified, not equivalent. See [fixer paths](deslop-fixer-paths.md).
- **Publication:** six of 127 `push_fix_branch` identities survive: 29 and 30 change a fallback already supplied by status; 46, 67 and 111 replace false with `None`, also false to the wrapper; 55 changes a conjunction whose two `rev-parse` outcomes are coupled. These are bounded equivalence dispositions, not proof of arbitrary subprocess behavior. The latest run caught 121; earlier diagnostic survivors 122, 124 and 125 are now caught. See [fixer paths](deslop-fixer-paths.md).
- **Matrix:** 55 of 58 caught; 26, 29 and 30 remove equal-length zip checks on tuples constructed with one value per axis and are equivalent in that caller. See [matrix](deslop-workflow-matrix.md).
- **Snapshot index:** six targeted survivors were caught in follow-ups. UTF-8 spelling changes are codec aliases, a cast returns the same value, and default-encoding substitutions are equivalent for the canonical ASCII index fields. Case substitutions were caught on a case-sensitive volume. See [snapshot](deslop-repomod-snapshot.md).

The completed removal and catalog trials reported no timeouts; publication reported no unrun identities. No timeout was claimed caught. Other inventory, checkout, workflow and publication decision regions and whole-file fallback are advisory and unrun; lack of a recorded result is not a pass.

The intended required critical mutation check is the **hosted publication scope**, not a whole-file or whole-inventory sweep. This checkout does not yet contain that hosted job: its selection, negative controls, runner cost and retention remain unqualified. Adding or expanding CI is outside this lane. Coverage is informational: at #60, 22,053/25,752 statements and 8,064/10,618 branches were exercised in the serial run (1,430 passed, three skipped). The paired suite-cost and hosted controls have not been measured here; the historical baseline is not a current cost comparison.
