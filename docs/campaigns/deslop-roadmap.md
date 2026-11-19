# Deslop resumption roadmap

The owner requested this stopping point on 2026-11-17. The full-fleet goal
remains open. This document accounts for the owner's six-part M2 request and
the subsequent Solid 2.0 upgrade request. It is a work queue, not a qualification
report. Use [Status](deslop.md#status) and the [scorecard](deslop-scorecard.md)
for the checked revisions. Earlier chronology is in
[historical status](deslop-status-20261117.md).

## Authority and stopping rules

CI repairs are authorized for existing pilots, calibration repositories and
already dispatched repositories. This includes platform-aware bounded mutation
jobs, whole-change accounting, behavioral negative controls, adopted typing and
lint checks, relevant browser checks, Makefiles, scripts and scoped retention
policy. Pushing, retriggering and merging verified changes are authorized on
resumption. Linux-only mutation is not a requirement for macOS-only behavior.

The owner approved the full campaign and delegated decisions, including
dispatch and hard-blocker deferral. Qualify M2 and record the evidence for
the next tier before dispatch. The grant covers repository work. Releases,
credentials, hardware and canonical checkouts retain their campaign boundaries.

## Reconcile before resuming implementation

1. Read current default branches and every active PR head. Fetch without
   switching or modifying canonical checkouts. Vault has a tag named `main`;
   fetch `refs/heads/main` explicitly.
2. Update each relevant `TODO-DESLOP.md` Report and the scorecard with the exact
   revision, completed stages, merged fixes, remaining conditions, CI and
   retention status, and one next action. Existing Reports are not all current.
   Preserve their historical measurements with source revisions.
3. Classify each pass as complete, active, blocked, not started, or outside the
   current dispatch scope. A seeded ticket, a local slice, or a lint invocation
   that skipped a repository proves no pass completion.
4. Correct stale PR descriptions and obsolete authorization or blocker claims.
   Resolve current main changes before reviewing a parked candidate again.

## Resumption receipts

- Stats [#25](https://github.com/joshuarli/stats/pull/25) merged as
  `be3742e` and closes the legacy fixture ticket. It bounds the initial
  Worker, Node and Rust components. Stats #26 and #27 fixed independently
  observed Linux CI failures in producer socket admission and shutdown.
  Both passed their hosted Node, dashboard and lint checks.
- Repomod [#68](https://github.com/laputa-systems/stuff/pull/68) caught 52
  of 60 selected catalog identities, compared with 39 on the base. All ten
  checks passed. The admission evidence documents eight identities in a
  case-folded collision branch and retains the broader gate.
- Pytest-parallel [#27](https://github.com/joshuarli/pytest-parallel/pull/27)
  caught the final worker report survivor, bringing the three-method
  selection to 60 caught. The exact active mutant changes a null
  diagnostic to the string `"None"`. All 157 local tests and hosted
  Linux/macOS checks passed. The whole-change gate remains open.
- Pytest-parallel [#28](https://github.com/joshuarli/pytest-parallel/pull/28)
  caught the reader's 121-character truncation mutation. All 158 local tests,
  lint and both hosted platforms passed. The five previously dispositioned
  identities yield no additional reachable output difference.
- fz [#44](https://github.com/laputa-systems/fz/pull/44) merged as
  `0ec537d`. Its two Linux mutation jobs covered disjoint partitions of the
  same 439 identities. The outcomes again totaled 423 caught and 16
  unviable with zero misses and timeouts. Hosted jobs took 6m 57s and
  7m 35s. The gate is within the ten-minute per-job target.
- Srv's follow-up branch `deslop/timeout-shard` at `7cd8627` catches both
  font MIME survivors in native singleton runs. Twenty-five missed
  identities remain in the earlier hosted receipt and 24 timeouts still
  need singleton confirmation. Keep #47 open.
- After the host recovery, direct GET requests returned 200 for the Cargo
  index and a crate blob, npm dashboard metadata and the exact Stats lock
  tarball, and the PyPI platformdirs wheel that had failed in Buildlib CI.
  Retrying failed jobs on pinned heads led to green merges for Stats #24,
  Stuff #64, Fastermod #28 and Ptytest #13. Fastermod #29 and Ptytest #14
  passed their hosted checks and merged after them.
- The owner excluded Discover from the campaign while rearchitecting it.
  Keep its earlier Solid test receipt for reference. Omit Discover from
  dispatch, CI retries and the campaign closeout.
- The owner excluded Chromium-build on November 19. Omit it from
  dispatch, cleanup, retries and closeout. Its completed offline APK
  checks remain in the [scorecard](deslop-scorecard.md#chromium-build-evidence-before-exclusion).
- Buildlib's retained workflow [#26](https://github.com/laputa-systems/buildlib/pull/26)
  merged as `a749bba`. Its 15 mutation jobs used 976 runner seconds in
  aggregate with a 50-second median. The hosted release, uncovered-branch,
  docs-only and deletion controls completed before merge. Stuff
  [#65](https://github.com/laputa-systems/stuff/pull/65) registered Buildlib
  and fz mutation retention on all ten checks.
- Diff-pretty [#31](https://github.com/laputa-systems/diff-pretty/pull/31)
  merged as `bb03d98` after 15 hosted checks and all four controls. The 12
  mutation jobs used 2,276 runner seconds in aggregate. Five interleaved
  quiet-host suite pairs against `49a1c97` had a median of 1.19 seconds for
  each revision. Every pair ran all 68 baseline and 89 candidate tests.
  Further renderer scopes and retention registration remain open.
- Buildlib [#20](https://github.com/laputa-systems/buildlib/pull/20) merged
  as `1838935` after 17 checks passed. The deletion and mixed controls each
  reopened four release identities across Linux x86-64, Linux arm64 and macOS
  arm64. The uncovered branch failed in all three `other` jobs. The docs-only
  control selected no identities and passed. The positive matrix used 976
  runner-seconds across 15 mutation jobs with a 50-second median. Buildlib
  [#26](https://github.com/laputa-systems/buildlib/pull/26) verifies the
  same gate through the Make entry point required by retention.
- Fz [#43](https://github.com/laputa-systems/fz/pull/43) merged as `89f7d9a`.
  Its hosted mutation job selected 439 identities, with 423 caught, 16
  unviable, and zero misses or timeouts. The single job used 13m 33s.
  The result qualifies the current scope and exceeds the ten-minute cost
  target. A shard split must preserve all five critical source files.
- Srv [#47](https://github.com/laputa-systems/srv/pull/47) passed ordinary CI
  and lint. Its initial unsharded job exhausted 900 seconds. Four round-robin
  shards at `ffaa487` accounted for all 376 identities in 612–642 seconds
  per shard, with 308 caught, 27 missed, 16 unviable and 25 provisional
  timeouts. Cargo-mutants 27.1.0 selected extra struct-field identities
  during timeout replays using `--re`. Branch `deslop/timeout-shard` at
  `a88c3b1` uses native singleton shards and confirmed one timeout locally.
  Resolve survivors and confirm the other timeouts before merging.
- Diff-pretty [#31](https://github.com/laputa-systems/diff-pretty/pull/31)
  now passes all 15 hosted checks. In
  [#36](https://github.com/laputa-systems/diff-pretty/pull/36), ordinary checks
  passed and the gate selected the changed source as well as the protected
  CLI region. Both CLI jobs found the expected `parse_paging` survivor.
  Deletion-only, uncovered-branch and docs-only controls are #37–39.
- Vault's Linux shard 0 expired at `0671858`. The artifact holds eight caught
  results and a passing baseline out of 11 selected identities. The gate
  printed zero because its final reader only ran when the child completed.
  `deslop/budget-receipt` at `e8c7931` fixes the accounting and passes all
  21 gate self-tests. The archive shows an expensive Linux unit baseline.
  The age passphrase path calibrates scrypt to CPU speed, so profile tuning
  alone has no established cost benefit. Gate cost and the remaining
  outcomes still require verification.

- Package delivery blocked hosted checks on 2026-11-17. The public Cargo
  index and the Cargo catalog returned HTTP 500 to a local probe and
  `stuff doctor --registry cargo`. The same index error stopped macOS jobs
  in [Ptytest #13](https://github.com/laputa-systems/ptytest/pull/13) and
  [diff-pretty #31](https://github.com/laputa-systems/diff-pretty/pull/31).
  The npm mirror returned HTTP 500 for locked assets in
  [Stats #24](https://github.com/joshuarli/stats/pull/24) and
  [Stuff #64](https://github.com/laputa-systems/stuff/pull/64). Stats built both
  legacy Workers on the Linux runner before the candidate install failed.
  On macOS the candidate ran all 41 local tests with no skips. Recheck the
  affected public endpoints before attempting failed jobs. Keep the locked
  package sources and all hosted acceptance conditions. At 23:54 UTC,
  the Cargo index, npm dashboard metadata and PyPI package endpoints all
  returned HTTP 502.
- Loc [#18](https://github.com/joshuarli/loc/pull/18) merged as `ac9ffed`.
  All 19 historical misses and the historical timeout mapped to current
  identities. Thirteen are now caught. Five survive and two timed out
  again at 90 seconds. The suite passed on macOS and both Linux musl
  architectures. The first-party critical union remains to be qualified.
- The fz workflow candidate `ci/retained-mutation-entry` at `4d8a43c`
  uses separate PR-only mutation and single-command Make steps. The
  Stuff candidate `policy/retain-fz-assurance` at `c5f8461c` detects
  loss of the workflow or coverage target in a local copy, including after
  removing `TODO-DESLOP.md`. Qualify the fz workflow remotely before
  merging the retention registration.
- Vault `deslop/cli-oracle` caught the bytes-to-MiB diagnostic mutation
  reported by hosted macOS shard 9. Its focused regression rejects the
  exact arithmetic fault. This advances the successor evidence and leaves
  the platform matrix unqualified.
- Srv `deslop/current-head-check` at `127cf80` passed the 87-test suite,
  Clippy and the gate self-tests on macOS. Both onefile dispatch mutants
  were caught. A surviving Mermaid environment mutation changed the SVG
  height from 798 to 777. The revised multiline-label witness caught that
  mutant, bringing the bounded five-identity run to five caught.

- Vault [#30](https://github.com/laputa-systems/vault/pull/30) advanced to
  `0671858badb1f1fb7fea852e35bbe8929f092afe`. The system Python 3.9 failed
  to import `tomllib`. The managed Python 3.15.2 passes 20 self-tests.
  Cargo-mutants 27.1.0 lists 260 Linux-only, 336 macOS-only and 54 Secure
  Enclave source identities in the configured per-file lists. Replaying the
  selector sends zero macOS or Secure Enclave source identities to Linux and
  zero Linux source identities to macOS. The shared-store selection includes
  51 Linux and 43 macOS identities. This is selection evidence. The [hosted
  matrix](https://github.com/laputa-systems/vault/actions/runs/44177303366)
  owns execution proof. Ordinary tests passed on macOS and both Linux musl
  architectures. The Linux mutation jobs found survivors and exceeded budget.
  Shard 6 recorded nine caught, one unviable and one unresolved identity in
  its artifact. The old gate reported zero completed outcomes. Successor
  `deslop/cli-oracle` at `d7ec9932b6ddcc33b040ad7bef92b801fb5adaa9` validates
  partial receipts while keeping the budget failure. It also catches the
  surplus-name survivor with an isolated CLI test and injected fault.
  The shard 6 baseline spent 115.72 seconds on its 47 unit tests and
  10.14 seconds on its eight terminal tests. Investigate that repeat cost
  before retrying the full Linux matrix. Fourteen finished Linux shards
  consumed 16,676 runner seconds in total, with a median of 1,223 seconds.
  Twelve failed. This excludes two unfinished Linux shards, the macOS
  shards and setup jobs. Both platform unions and the remaining survivors
  still need qualification. The successor backlog and proofs are at
  `6f83ee6bf3d08548f9195a752ba0896e9418f7f8`.
- Buildlib [#20](https://github.com/laputa-systems/buildlib/pull/20) runs
  `175c98796220821b53ef328cc0761a232c5fb28b`. All five x86-64 Linux jobs
  passed. Linux ARM64 test, lint and four mutation jobs timed out fetching
  several distinct locked wheels. A host request to the same platformdirs
  wheel returned HTTP 200, so runner reachability still needs proof. The
  [mixed control](https://github.com/laputa-systems/buildlib/pull/21) at
  `7bef43e` passes all 206 ordinary tests and both lint checks locally.
  Hosted x86-64 and ARM64 release shards reopened the four expected release
  survivors and selected the unrelated targets module. The targets shard
  also found that the exception assertion missed a missing diagnostic.
  [#22](https://github.com/laputa-systems/buildlib/pull/22) merged the literal
  diagnostic assertion as `890b5bd088a0b71f3436a6da1b2265a5a88720e7`.
  The exact injected fault fails all three cases. With the #22 assertion
  added locally to the mixed-change fixture, `make mutants-diff
  BASE=175c98796220821b53ef328cc0761a232c5fb28b SHARD=other` catches all 28
  targets mutations. Re-run the complete hosted control with that
  assertion and retain separate evidence for test-only deletion, a new
  uncovered branch and documentation.
- Diff-pretty [#31](https://github.com/laputa-systems/diff-pretty/pull/31)
  kept main's superset of CLI assertions when integrating the draft. All
  eight CLI tests and nine gate self-tests passed locally. GitHub rejected
  the first workflow before creating jobs. The [replacement
  run](https://github.com/laputa-systems/diff-pretty/actions/runs/44178066822)
  at `acdf7a90bcbbad044fb2ce4f791af99585743294` created the jobs, but GNU
  Make treated `export` as a prerequisite and stopped before selection.
  At `872ae4c9e41dbeacb37515da32c820670ce668df`, the gate entry point
  successfully reports an irrelevant comparison against HEAD. Follow the
  [current run](https://github.com/laputa-systems/diff-pretty/actions/runs/44179199958)
  for both platform executions.
- Extensions [#15](https://github.com/joshuarli/extensions/pull/15) merged
  the type-aware lint and Linux installed-Chromium jobs. Both jobs also
  passed on the later default head `1ad499ed4b3e8201eb54a09a8cdbae6493959b8a`.
  Temporarily removing `TODO-DESLOP.md` from the #15 worktree kept
  `pnpm run lint` and its one installed-browser case green. Fleet retention
  registration, whole-change mutation and the wider browser inventory remain
  open.

## Finish the current passes

Keep one implementation owner per repository. Use the
[M2 evidence](deslop-m2.md#successor-results) for exact revisions and
[scorecard](deslop-scorecard.md) for the current disposition.

| Repository | Verified scope | Remaining acceptance |
| --- | --- | --- |
| Vault | Ordinary macOS and both musl jobs and the two-Mac owner ticket. | Platform mutation budget, Linux keyring and two-Mac recovery. |
| Buildlib | Merged control matrix, release serialization review and fleet retention. | Recheck the retained guarantees at the tier checkpoint. |
| Extensions | Type-aware lint, installed Chromium, and parser and storage trials with hosted controls. | Archive decisions and remaining browser effects. |
| pytest-parallel | Native subtest replay through an installed wheel and twelve hosted mutation lanes. | Coordinator lifecycle, loopback and exact aggregate retention. |
| Diff-pretty | Retained changed-source and protected-region workflows on both platforms. | Remaining renderer and live terminal scopes. |
| Loc | Shebang selection on macOS and both Linux musl targets. | Hosted repeat of the native mixed union, wider SIMD and file-selection inventory, and paired cost. |
| Stats | Legacy upgrade, mixed ACKs in Workerd, and separate hosted Workerd and Rust mutation lanes. | Producer timeout dispositions, wider runtime scope and retention. |
| Stuff, repomod | Types and Dead code complete. Checkout, upstream, workflow matrix and snapshot trial passed. Publication caught 121 of 127 locally. | Hosted publication scope, remaining inventory and whole-file fallback. |
| Fastermod | Saved-plan revalidation, source warning and JSON ignore witnesses, hosted source retention. | Review output, wider plan decisions and paired suite cost. |
| Ptytest | Hosted terminal mutation retention, deadline and cursor traces, focused lz, e and ish consumers. | Lifecycle, replay and remaining consumers. |
| Tm | Fixture repairs merged. | Quiet-host Ground cost and component pass. |
| Toolbox | Native media and fio checks, two-worker coverage and all 750 tests passed locally. | GitHub Actions must be able to schedule #15. |

Srv and fz have completed pass Reports at their checked default heads.
Srv's successor mutation job exceeded the ten-minute target twice.
Keep its remaining misses and confirmed hangs in the owning scope.

All ten Tier A repositories have a tracked deslop backlog. Fz, Pi-build
and FFmpeg-build passed check-up. The Tier A checkpoint admits
Tier B. All seven in-scope Tier B repositories have seeded backlogs
and supported Make entry points.
Defuddle-rs closed Ground. Continue with the owning tickets and
apply F3 retention as each repository qualifies its guarantees.
Keep the remaining Tier A passes active.
[Tier A checkpoint](deslop-scorecard.md#tier-a-checkpoint)

## Bound every open Tests ticket

Use `todo --file TODO-DESLOP.md edit --json -` to update the existing DSLP-4,
rather than adding another overlapping Tests investigation. Its Report must
name the following finite inventory before further mutations:

- Public contracts and the tests guarding them, with explicit remaining gaps.
- Critical decision regions and supported platform/runtime shapes.
- Acceptance commands, source revisions and named consumers.
- Each unresolved survivor, unrun region, timeout and platform disposition.
- The remaining coverage, suite-cost, CI and retention conditions.

Finish that inventory, then proceed to Dead code, P1/P2 Findings, cumulative
review and Report. A newly demonstrated P1/P2 may interrupt it. Lower-priority
discoveries become explicit follow-ups unless they invalidate named acceptance.
Keep historical and current counts separate. Equivalent mutants, accepted
risks, untested code and unsupported environments are distinct dispositions.

### Repomod calibration inventory

The current boundary map covers `repomod/` at
`1753a059ba256990779aa6d7f10e852e4652b621`. Inspect these clusters when
selecting the serial mutation run. Use existing tests with local Git
repositories, fake GitHub responses, or synthetic registry documents.

| Boundary | Critical decisions | Existing checks |
| --- | --- | --- |
| Fleet catalog and CLI | Closed tags, repository identity and path collisions, command dispatch and exit status | `test_catalog.py`, `test_cli.py` |
| Checkout and removal | Upstream merge bases, preservation of dirty or detached checkouts, archives, canonical identity | `test_sync_upstream.py`, `test_sync_cleanup.py`, `test_gc.py` |
| Fix plans and publication | Path admission, copy isolation, concurrent checkout changes, branch movement, publication refusal | `test_fix_safety.py`, `test_fix_command.py`, `test_fix_push.py` |
| Workflow checks | Matrix includes, check-name expansion, retries, partial GraphQL responses | `test_github_policy.py`, `test_ci_workflow.py` |
| Inventory consumers | Dependency and LOC snapshot consistency, mirror-catalog validation, dashboard adapter | `test_deps_snapshot.py`, `test_loc_snapshot.py`, `test_deps_world.py`, `test_dashboard_preview.py` |

First-party coverage at [#60](https://github.com/laputa-systems/stuff/pull/60)
exercised 22,053 of 25,752 statements and 8,064 of 10,618 branches. The earlier
parallel coverage run used a candidate pytest-parallel wheel at a different
revision. To reproduce the serial result, install the mirrored coverage.py
7.17.3 wheel in an isolated environment for the pinned repo. Set branch
coverage, `parallel = True`, `patch = subprocess`, and absolute `source`
and fresh data paths. Run `python -m coverage run -m pytest -p no:parallel
tests/repomod -q`, then `coverage combine` and `coverage json`. The run
passed 1,430 tests with three skips. The OSV fixture repair was necessary
after the first serial run reached the live advisory service. The focused
transport refusal reproduced the old failure and passes after the repair.
Name the still-unrun decision regions and disposition survivors before
adding the whole-change union. Run `make repomod-test` and
`make repomod-lint`. The suite-cost and hosted controls remain open.
Repomod's downstream dashboard render and `make deps` consume these outputs.
The live fleet and launcher integrations remain opt-in.

Two serial Scenarios now have named results. [Stuff #61](https://github.com/laputa-systems/stuff/pull/61)
covers matrix expansion with 55 caught and three equivalent identities from
58 selected. [Stuff #62](https://github.com/laputa-systems/stuff/pull/62)
catches all 25 upstream-fetch identities using real shallow and full local
Git fixtures. The base is `1753a059ba256990779aa6d7f10e852e4652b621` for
both. The PRs record the exact commands and hand-injected fault controls.
Other effect boundaries and the aggregate lane remain open. The
[#62 native wheel job](https://github.com/laputa-systems/stuff/actions/runs/44185508301/job/134400872685)
failed during Docker cache transfer with an unexpected EOF. Retrying that
job after the workflow completed passed. All ten checks passed and #62
merged as `a671b0fc`.

Ruff 0.17.4 at this revision reports 22 `ANN` diagnostics, including 17
`ANN401`, and 190 `TC` diagnostics, including 108 standard-library
type-only imports. The TC findings include import placement and quoting.
No behavioral witness supports adopting TC here. `PGH003`, `B` and
`RET` report zero findings. The configured ty 0.0.101 profile already
sets all rules to error and passes. The build-lock type candidate in
[Stuff #59](https://github.com/laputa-systems/stuff/pull/59) removes two
ANN401 diagnostics, and its checker witness fails before the change.
1,431 tests passed with three existing opt-in skips. Keep Types open for
the remaining dynamic boundaries.

## Qualify meaningful retained gates

Classify the whole change, including deletions and renames. Production changes
select changed lines or the file when necessary. Test, fixture, generated-input,
configuration, dependency and gate changes select the appropriate critical
scope. The final selection is their union. Print classes, identities, outcomes
and platform ownership. Unknown paths and unsupported selections fail visibly.

Qualify the actual workflow with executed controls demonstrating all of these:

1. Deleting a protective test fails the gate while ordinary checks still pass.
2. Adding an uncovered relevant branch fails.
3. Deleting a test plus changing unrelated, already-covered production cannot
   evade the protected critical selection. Require the reopened critical miss
   and evidence that the unrelated changed region was also selected.
4. Missing results, unexpectedly empty relevant selections and exhausted budgets
   fail. Confirm timeouts with a longer bound before counting detection.
5. A genuinely documentation-only change is explicitly irrelevant.

For every platform exclusion, name the executed job or separately verified
boundary exercising the behavior. Hardware and unsupported environments remain
visible. Structural policy checks complement behavioral controls. Keep the
existing recipes and pinned tools; build no generic workflow or shell interpreter.

Measure wall time and total runner-minutes, including every shard and retry.
Report the existing ten-minute CI p50 target, the measured sample count and any
exception. More shards or larger timeouts do not hide cost. Local component
receipts do not qualify the aggregate workflow.

Update `fleet/policy/retention.toml` only after the corresponding guarantee is
qualified. Prove that deleting `TODO-DESLOP.md` cannot remove the adopted typing,
test, browser or mutation guarantee. Resolve conflicts and run only checks
invalidated by the actual integration. Merge the reviewed head after all
applicable checks pass. Finish cumulative review and the campaign check-up.

## Produce the bounded M2 report

Use this fixed matrix. Each row must name one representative component or
workload, qualification result, exact evidence, tool cost, confirmed yield and
remaining limit:

| Required shape | Representative | Current gap to resolve |
| --- | --- | --- |
| Rust HTTP service | Srv | Recheck retained guarantees and actual CI cost. |
| Rust performance CLI | Fastermod | Calibration pass not started. |
| Rust corpus/SIMD CLI and musl/macOS | Loc | Finite Tests inventory and CI qualification. |
| Rust PTY library with consumers | Ptytest | Calibration and consumer proof not started. |
| Rust platform and hardware boundary | Vault | Platform union, actual CI and explicit hardware limits. |
| Python library and binary parsers | Buildlib | Actual whole-change workflow and controls. |
| Python pytest plugin and worker coverage | Pytest-parallel | Remaining named decisions and serial whole-change lane. |
| Python orchestration and effects | Repomod | Calibration Types, Tests and Dead code finish lines. |
| TypeScript Node/browser/MV3 | Extensions | Retained lint, browser job and whole-change gate. |
| TypeScript Worker and mixed Rust | Stats | Component qualification and legacy-upgrade CI. |
| Python external native tools | Toolbox | Billing and missing native-tool boundaries. |

An evidence substitution must explain which exact calibration question it
answers and which inputs match. Otherwise retain the gap. In particular, name
the remaining fastermod, ptytest, loc, stats and repomod questions explicitly.

The report must list completed passes, confirmed defects fixed, automated
guarantees, escaped regressions and their guards, test/CI cost changes,
unsupported and owner-dependent boundaries, and the recommended next dispatch
batch with prerequisites. Identify which shapes qualify and defer hard
blockers explicitly before moving to the next tier.

## Upgrade Solid consumers on resumption

STUF-91 tracks the stable Solid 2.0 upgrade. The [stable release][solid-release],
[pinned changelog][solid-changelog] and [migration guide][solid-migration]
confirm the runtime, renderer and compiler must agree. Current application
manifests already use Solid 2 RC imports and `@solidjs/web` for JSX. Check
for Solid 1 subpaths and lifecycle or effect differences before moving
each application. For Stats, the [Router 2 release][router-release] renames
or removes several legacy APIs. Its source already uses the `createRouter`
factory, `hashHistory` and plain anchors.

| Consumer | Verified state |
| --- | --- |
| Discover | Outside campaign scope during the owner's rearchitecture. Before exclusion, [#48](https://github.com/joshuarli/discover/pull/48) passed 342 Node and 50 browser tests, lint, type checks and the production build. Hosted attempt 3 stopped at account billing before runner allocation. |
| Stats | [#23](https://github.com/joshuarli/stats/pull/23) resolves Solid, Web and Router 2.0.0 and Vite plugin 3.0.1 through the existing registry. Type checks, lint, production builds and all 320 desktop and mobile browser cases passed. The local browser run uses one worker to stay within the two-core cap. All three hosted checks passed with the approved exact-version exemptions. The PR merged as `6de663387e742c4652b57d8c5096ed54b7b5a374`. |
| bctl | [#4](https://github.com/joshuarli/bctl/pull/4) passes type checking, production build, and session and clipboard browser fixtures with Node 26.12.1. Frozen install passes with the approved exact-version exemptions. The candidate and the pre-upgrade revision each passed four, failed the same six and skipped execution of one browser case with the same SmolVM image. The Nanos fixture stopped at display readiness. VM acceptance remains open. |
| laputa-ui-dashboard | The library's peer range admits stable Solid 2. Its development pins still resolve the RC from Stuff. Stuff's public catalog has no stable Solid, renderer or Vite plugin. Refresh those pins once the existing mirror serves the matching toolchain. |
| pi-build | The OpenCode companion lock mentions Solid in optional peer metadata. No installed Solid package entry is present. |

[solid-release]: https://github.com/solidjs/solid/releases/tag/solid-js%402.0.0
[solid-changelog]: https://github.com/solidjs/solid/blob/a8186e6738b3a6a3341c561f66e9325432d6759b/packages/solid/CHANGELOG.md
[solid-migration]: https://docs.solidjs.com/migration/from-solid-1/
[router-release]: https://github.com/solidjs/solid-router/releases/tag/v2.0.0

## Parked checkpoints and reboot audit

The three workers stopped and their worktrees are clean. These local commits
have not been pushed or accepted. Read the tracked proof from each named branch,
not a scratch log, before qualification. Preserve the branches even if their
optional build artifacts are rebuilt.

| Repository and branch | Local head | Qualification still required |
| --- | --- | --- |
| Buildlib `deslop/mutation-ci` | `175c98796220821b53ef328cc0761a232c5fb28b` | Final integration and remote platform jobs, actual PR controls, complete runner cost. Local release gate reports 317 killed and 14 dispositioned survivors; the mixed fixture reopens four release mutants. |
| Vault `deslop/platform-ci` | `6c92d26f23ee3df739438d4f750698590eef16f3` | Full Linux/macOS shard matrix, actual PR controls, aggregate cost and platform dispositions. One macOS shard log reports five caught and four unviable, but its controlling shell exit was not captured; that is not a passing aggregate receipt. |
| Diff-pretty `deslop/platform-ci` | `555aeaaf528df18b06431fe8287716f17c86d9f0` | Numeric component, final activation after gate/config edits, both platforms, tool-artifact checks and actual PR controls. Renderer has eight configured equivalences added after its last run; final gate acceptance remains unverified. |

Their tracked proof is `docs/deslop-mutation-ci.md` in Buildlib and
`docs/deslop-platform-ci.md` in Vault and diff-pretty. The local `cg` worktrees
are retained for resumed qualification, not as the sole copy of their work.
The existing Vault `deslop/store-gate` draft #30 remains at
`bf3dcd9b4d893dce12de453705ef0b73dae4e0bf`; diff-pretty `deslop/tests` draft #31
remains at `6f1719d8f0bb1ff9ab42ea0fcc91994ea9909ccb`.

Stuff's four published PR heads are preserved separately from the local pause:

| PR and branch | Reviewed source head | Pause disposition |
| --- | --- | --- |
| #55 `docs/deslop-accepted-slices` | `b9e1500727f016892472e3c63f9a54b3a62257c6` | Awaiting macOS Rust. Resolve its old Status against the current pause and roadmap before integrating. |
| #56 `deslop/enrichment-types` | `5cd93b80e9330e7e4f8c41059dc95af3c8ee35d2` | 1,428 local tests and lint pass; awaiting macOS Rust. |
| #57 `fix/workflow-matrix-includes` | `e69a4d919a2a1312ccfe3c5fbf7d886c2c767e8f` | 1,429 local tests and lint pass; awaiting macOS Rust. |
| #58 `chore/deslop-fix-cleanup` | `8c6d32492ee9b4aa39c772ce1658256081d040da` | Preservation-first cleanup receipt; awaiting macOS Rust. |

The waiting jobs are not assumed green or hung. A cancelled #55 macOS job was
restarted after its log showed steady passing fake-S3 tests with repeated
roughly 35-second delays. Do not repeat that cancellation as a diagnosis.
No application source from these pending PRs was merged during winddown.

Since the previous handoff, accepted default-branch work includes Stats #22
command-tree cancellation and #21 ingest-type evidence, Loc #17 filename
admission, diff-pretty #35 CLI assertions, and pytest-parallel #25 installed
worker network assertions. Each merged after all applicable checks passed.
Their exact default revisions are in the current scorecard.

Five completed Stuff repair/review worktrees (`fp`, `sp`, `mc`, `ur`, `fpr`)
were retired only after integration and idle checks. Eighteen useful logs were
preserved with byte-for-byte verification in private Git metadata; net scoped
space reclaimed was 192 MiB. The published #58 receipt records all hashes.
Preserved checkout archives and unrelated user work remain untouched.

The automatic closeout guard could not start: Git reports the tracked
`.gitignore` as the winning `.work/` rule, while the guard requires the rule to
come from `.git/info/exclude`. That file also contains `.work/`. The Stop hook
was inspected and invokes `codex-campaign-closeout.py hook`. Do not weaken Git
ignores or change unrelated tools during winddown to conceal this limitation.
The manual audit below is the stopping evidence; automatic allow registrations
could not be made. Recheck that guard prerequisite on resumption.

Local mutation runners and check-watch loops have stopped. The shared mutation
lock is absent and all three heavy slots are free. Already submitted remote CI
may finish; it does not authorize an automatic campaign continuation. No new
worker, schedule, measurement or Solid upgrade was started during winddown.

### Retained Stuff worktrees

The following exact paths remain. `accepted`, `rt`, `wm` and `clf` retain
pending PR integration contexts. The three `dr-*` trees retain optional
diagnosis witnesses until #55 is reconciled. `pycov` retains the existing
worker-coverage consumer proof. Other entries predate this bounded cleanup
and have separate or uncertain ownership; no source was discarded to remove
them. They must be reviewed by ownership before retirement. All resumable
implementation is committed on named branches; private raw archives are kept.

```text
worktree /Users/josh/d/stuff
worktree /Users/josh/d/stuff/.work/wt/accepted
worktree /Users/josh/d/stuff/.work/wt/actor-lifecycle
worktree /Users/josh/d/stuff/.work/wt/catalog-ui
worktree /Users/josh/d/stuff/.work/wt/clf
worktree /Users/josh/d/stuff/.work/wt/dependency-atlas
worktree /Users/josh/d/stuff/.work/wt/deslop-enforce
worktree /Users/josh/d/stuff/.work/wt/deslop-stuff
worktree /Users/josh/d/stuff/.work/wt/dr-core
worktree /Users/josh/d/stuff/.work/wt/dr-deps
worktree /Users/josh/d/stuff/.work/wt/dr-policy
worktree /Users/josh/d/stuff/.work/wt/engine-diagnosis
worktree /Users/josh/d/stuff/.work/wt/file-lock-drop
worktree /Users/josh/d/stuff/.work/wt/h12tiny-upstream
worktree /Users/josh/d/stuff/.work/wt/inventory-read-refusals
worktree /Users/josh/d/stuff/.work/wt/mycrates-red
worktree /Users/josh/d/stuff/.work/wt/nanoshop-ingress
worktree /Users/josh/d/stuff/.work/wt/oo-native-finish
worktree /Users/josh/d/stuff/.work/wt/oo-recovery
worktree /Users/josh/d/stuff/.work/wt/oo-stuff-dev-deploy
worktree /Users/josh/d/stuff/.work/wt/owned-tools
worktree /Users/josh/d/stuff/.work/wt/pycov
worktree /Users/josh/d/stuff/.work/wt/rivet-dashboard
worktree /Users/josh/d/stuff/.work/wt/rivet-explorer
worktree /Users/josh/d/stuff/.work/wt/rt
worktree /Users/josh/d/stuff/.work/wt/smoke-x86
worktree /Users/josh/d/stuff/.work/wt/sqlite-page-read-refusal
worktree /Users/josh/d/stuff/.work/wt/staged-sqlite-refusal
worktree /Users/josh/d/stuff/.work/wt/stats-runtime-hardening
worktree /Users/josh/d/stuff/.work/wt/stuf90-diagnosis
worktree /Users/josh/d/stuff/.work/wt/winddown-20261116
worktree /Users/josh/d/stuff/.work/wt/wm
worktree /Users/josh/d/stuff/.work/wt/zip-rule
```

### Unmerged Stuff branches

Every branch below is preserved. The PR branches are identified above.
`chore/d-overlap-inventory`, `chore/deslop-cleanup-resume`,
`chore/stuf89-cleanup-final`, `docs/deslop-current` and
`docs/deslop-direct-progress` preserve prior campaign/cleanup records.
The `fix/stuf89-*` branches preserve unfinished help work. The remaining
branches belong to prior infrastructure/deployment work and are retained
without advancing those campaigns. Do not delete them to satisfy closeout.

```text
  chore/d-overlap-inventory
  chore/deslop-cleanup-resume
+ chore/deslop-fix-cleanup
+ chore/h12tiny-upstream
  chore/stuf89-cleanup-final
+ deslop/enrichment-types
+ docs/deslop-accepted-slices
  docs/deslop-current
  docs/deslop-direct-progress
+ feat/stats-runtime-hardening
+ fix/actor-lifecycle
+ fix/inventory-read-refusals
+ fix/staged-sqlite-refusal
  fix/stuf89-help
  fix/stuf89-rust
+ fix/workflow-matrix-includes
```
