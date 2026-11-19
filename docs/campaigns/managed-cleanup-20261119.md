# Managed checkout cleanup inventory, 2026-11-19

Read-only mechanic inventory for the repeat disk cleanup. No worktree or scratch was removed.
The November 18 receipt already covers 106 completed retirements and 15.46 GiB of path allocation
(`managed-cleanup-20261118.md:1-4`). This pass used `/Users/josh/repos`, the root named by
`fleet/catalog.toml:4`, and checked the catalogued Gluon, Rustybench, CMake-build, Node-build, and
Defuddle-rs repositories (`fleet/catalog.toml:8, 84, 87, 93, 122`).

## Ranked current candidates

These five CMake lanes are the highest allocation candidates still present at the final inventory.
Their pull requests are merged, their campaign worktrees map to the PR head branches, their tracked
trees are clean, no open/cwd handles appeared in the one lsof query, and the retirement tool's
`--dry-run --discard-ignored` accepted each as patch-equivalent to the exact PR merge commit. The
ignored data is lane-local `.work/cache/objects`, `.work/tmp` baseline/candidate/final trees, a
`.venv`, and small Python caches. The `.work/tmp` directory names identify completed test runs; the
allocation column is `du -sk` path allocation and is not a promise of equal volume recovery.

| Rank | Exact worktree path | PR / exact integration SHA | Allocation, KiB | Dry-run verdict |
| ---: | --- | --- | ---: | --- |
| 1 | `/Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-release-command-dispatch` | [#117](https://github.com/laputa-systems/cmake-build/pull/117) / `58ac607c6c1a9d38052d96a20d5295831a66e23c` | 391,696 | Exit 0; would remove, patch-equivalent |
| 2 | `/Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-release-admission` | [#115](https://github.com/laputa-systems/cmake-build/pull/115) / `00aac26be28ed8d928489ab0878b4d6e9109a742` | 391,640 | Exit 0; would remove, patch-equivalent |
| 3 | `/Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-inner-phases` | [#121](https://github.com/laputa-systems/cmake-build/pull/121) / `6b7e8342b13d760464a84f11f019e5601ecbb3f8` | 289,096 | Exit 0; would remove, patch-equivalent |
| 4 | `/Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-inner-prepare` | [#123](https://github.com/laputa-systems/cmake-build/pull/123) / `ecdfa5d2ab0863a9e3ee37eeb2c5f81ea3594a4a` | 289,060 | Exit 0; would remove, patch-equivalent |
| 5 | `/Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-fetch-doctor` | [#119](https://github.com/laputa-systems/cmake-build/pull/119) / `560404225053f235702e9e8bbc2df99f7ac4f6b0` | 288,984 | Exit 0; would remove, patch-equivalent |

Combined path allocation: 1,650,476 KiB (about 1.57 GiB). These are recommendations for the
parent's removal pass after it reviews the listed ignored scratch. No branch would be deleted by the
dry run: each branch is not an ancestor of the squash merge, although its content is patch-equivalent.

## Retained and no-longer-present paths

- `/Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-benchmark-median` remains registered
  and clean, but `worktree-retire --dry-run --discard-ignored ... --into
  32092554e2bf5f78255cf12e7448bf98b2d8a6e1` exited 1: `731e4b03415f is not integrated`. The
  corresponding PR #120 is merged on GitHub, but the tool and `git cherry` report an unmatched
  change (`+ 731e4b03415f...`). Keep it for reconciliation; do not infer removability from PR state.
- The four Gluon lanes for merged #30–33 (`gluon-validate-declared-inputs`,
  `gluon-clean-dyndep-producers`, `gluon-declared-input-freshness`, `gluon-stale-dyndep`) were
  present in the first registration snapshot but absent by final check. Gluon's current registered
  worktrees are `gluon-archive-symbols`, `gluon-dry-run-readiness`, `gluon-dry-run-review`, and
  `gluon-macos-parity`. Preserve all four; the last three are explicitly protected by the task.
- The Rustybench #20 lane (`rustybench-duplicate-comparisons`), six Node-build lanes for #79–84,
  three Defuddle-rs lanes for #30–32, and the other initially observed CMake PR lanes #116, #114,
  #118, #122, #124–126 were absent by final check. Their registrations were also absent in the
  final `git worktree list` for Rustybench, Node-build, and Defuddle-rs. They are not active
  recommendations; no removal is attributed to this inventory. Node #79 initially showed ignored
  `build/` data, the unclassified category retained in the November 18 receipt (`managed-cleanup-20261118.md:44-47`).
- The final snapshots retain other in-flight, detached, or unclear lanes in each repository. No
  canonical checkout was changed. Chromium `macos-helium`, parked Python-build output, Stats
  recovery, Ctrs, Discover, and any other known retained work were outside candidate scope, as
  required by the campaign exclusions (`deslop.md:399-401`) and previous receipt
  (`managed-cleanup-20261118.md:36-50`).

## Proof record

Base checkout was `/Users/josh/d/stuff/.work/wt/managed-cleanup-20261119` at
`0779fabc0c9322f24d9bb346e98b161bae02220`; initial `git status --short` was empty.

- `git rev-parse HEAD && git status --short && pwd` — exit 0; base SHA matched and worktree was
  clean.
- `cat docs/campaigns/deslop.md docs/campaigns/deslop-scorecard.md docs/campaigns/managed-cleanup-20261118.md`
  — exit 0; confirmed the prior 106-retirement receipt and campaign scope. `rg -n -i
  'gluon|rustybench|cmake|node-build|defuddle|chromium|python-build|stats|ctrs|discover|worktree|merged'
  ... fleet/catalog.toml` — exit 0; catalogued repos and exclusions found.
- `git -C <root> worktree list --porcelain` — exit 0 for the five roots; initial snapshots identified
  PR branch names and heads. Final snapshots confirmed the absent-path status and listed remaining
  Gluon/Rustybench/Node/Defuddle lanes.
- Read-only GitHub queries:
  `gh pr list -R laputa-systems/gluon --state merged --limit 8 --json number,title,headRefName,headRefOid,mergeCommit,mergedAt`,
  `gh pr list -R laputa-systems/cmake-build --state merged --limit 14 --json number,title,headRefName,headRefOid,mergeCommit,mergedAt`,
  `gh pr list -R laputa-systems/node-build --state merged --limit 8 --json number,title,headRefName,headRefOid,mergeCommit,mergedAt`, and
  `gh pr list -R joshuarli/defuddle-rs --state merged --limit 6 --json number,title,headRefName,headRefOid,mergeCommit,mergedAt` plus the equivalent Rustybench query — all exit 0. Decisive rows: Gluon #30–33;
  CMake #115, #117, #119, #121, #123; Rustybench #20; Node #79–84; Defuddle #30–32 all report
  merged, with the SHAs recorded above or in the exact command arguments below.
- One open-file/current-working-directory query, run once:
  `lsof -nP +D /Users/josh/repos/laputa-systems/gluon/.work/wt +D /Users/josh/repos/laputa-systems/rustybench/.work/wt +D /Users/josh/repos/laputa-systems/cmake-build/.work/wt +D /Users/josh/repos/laputa-systems/node-build/.work/wt +D /Users/josh/repos/defuddle-rs/.work/wt`
  — exit 1 and no rows; no open handles were reported in these roots at query time.
- For each ranked candidate, `git -C <exact path> status --short` — exit 0 with empty output;
  `du -sk <exact path>` returned the allocation in the table. The initial
  `worktree-retire --dry-run <exact path> --into <merge SHA>` exited 1 only because the tool listed
  ignored files and required explicit review. After inspecting the ignored paths, the exact
  successful commands were:

  ```text
  worktree-retire --dry-run --discard-ignored /Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-release-command-dispatch --into 58ac607c6c1a9d38052d96a20d5295831a66e23c
  worktree-retire --dry-run --discard-ignored /Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-release-admission --into 00aac26be28ed8d928489ab0878b4d6e9109a742
  worktree-retire --dry-run --discard-ignored /Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-inner-phases --into 6b7e8342b13d760464a84f11f019e5601ecbb3f8
  worktree-retire --dry-run --discard-ignored /Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-inner-prepare --into ecdfa5d2ab0863a9e3ee37eeb2c5f81ea3594a4a
  worktree-retire --dry-run --discard-ignored /Users/josh/repos/laputa-systems/cmake-build/.work/wt/cmake-fetch-doctor --into 560404225053f235702e9e8bbc2df99f7ac4f6b0
  ```

  Every command exited 0 and printed `would remove ... (patch-equivalent of <SHA>)`; each also
  printed `would keep branch ... (not an ancestor ...)`.
- `git -C /Users/josh/repos/laputa-systems/cmake-build cherry 32092554e2bf5f78255cf12e7448bf98b2d8a6e1 731e4b03415ffabb5e7021660c580de6574e6aaf` — exit 0, one `+` entry for the benchmark median head. Its dry run exited 1 with the unintegrated reason above.
- `du -sk <candidate>/.venv <candidate>/.work ...` and `find <candidate>/.work -mindepth 1 -maxdepth 2 -type d -print` — exit 0 for the five ranked candidates; confirmed `.work/cache/objects` and the named baseline/candidate/final trial trees. No files were modified.
- An early inventory loop used the zsh special parameter name `path`, overwriting `PATH` and causing
  exit 127 for utility commands. It made no changes. The loop was rerun with `candidate_path`; all
  findings above use the successful rerun and later final snapshots.

## Unverified cases and blockers

Most initially registered candidates disappeared from disk between snapshots. I did not remove
them; which concurrent owner action changed them is unknown. They have no live candidate path to
dry-run now. The five ranked CMake paths are verified recommendations, not removals. The median
worktree, all active/parked/dirty/unknown work, and protected paths remain retained. No required
acceptance command failed for the ranked candidates; no source changes or Git mutations were made.
