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

Releases, production, credentials, hardware operations and canonical user
checkouts retain their existing boundaries. Broader deslop dispatch waits for
the concrete M2 report and owner approval. Winddown starts no new implementation
or measurement. Its new checkpoints are committed locally without pushing.

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

## Finish the current passes

Keep one implementation owner per repository. Review and finish existing work
before opening further investigations. The three parked gate implementations
are local candidates, not qualified CI lanes.

| Repository | Finite next deliverable | Remaining acceptance |
| --- | --- | --- |
| Vault | Review the parked platform selector and qualify the production-plus-critical union on Linux and macOS. | Prove that Linux does not receive macOS-only functions. Execute all selected regions and lane controls, account for total runner cost, and preserve explicit Secure Enclave, two-Mac recovery and Linux keyring limits. Finish existing Tests before adding rare-error scenarios. |
| Buildlib | Review `deslop/mutation-ci` and qualify `make mutants-diff` through actual PR jobs. | Reuse the four accounted critical scenarios and worker-inclusive coverage. Execute positive jobs and all negative controls. Reproduce the local mixed control remotely. Verify runner labels, locked dev dependencies, cumulative checks and cost before retention eligibility. |
| Extensions | Retain the adopted unsafe-argument lint rule in CI and add a bounded supported browser job for the demonstrated boundary. | Reuse archive, context recovery, strict reads, storage/state and installed-MV3 evidence at matching inputs. Finish first-party coverage, the TypeScript whole-change gate, negative controls and test cost. Keep Node and browser qualification distinct. The unproven X response-ordering finding needs a captured fixture, not a claim of failure. |
| pytest-parallel | Finish the bounded whole-change gate using serial mutmut and the established worker-coverage witness. | Reconcile scheduling, event stream, reporting and network boundaries to current head. Disposition remaining named critical decisions, verify activation, preserve hook-error repair and installed-wheel controls, and qualify the actual lane. The empty-address bind defect remains a separate demonstrated runtime finding requiring regression and consumer proof. |
| Diff-pretty | Reconcile main with draft #31 and review `deslop/platform-ci`. | Reuse the sanitizer receipt while its runtime inputs match: the recorded source passed the existing rule, and its subsequent change was documentation-only. Resolve test integration conflicts, finish numeric and final gate activation, confirm renderer equivalences, execute both platforms and negative controls, and finish test-cost qualification. |
| Loc | Close the existing critical inventory and qualify its bounded lane. | Reuse literal CLI output, masks and filename/detection witnesses. Reconcile the historical sample to current source where identities exist; retain unavailable mapping as an explicit gap. Finish named counting, detection, file-selection and config regions, cost, platforms and controls. |
| Stats | Finish component-mode Types, Tests and the legacy-upgrade CI prerequisite. | Reuse ingest type-candidate measurements and merged command-cancellation/sandbox repairs. Prepare the pinned baseline so the legacy upgrade test executes. Name the TypeScript/Worker and Rust components, browser/runtime checks, critical scope, cost and remaining settings. Other deployment and performance campaigns remain untouched. |
| Stuff, repomod | Integrate verified PRs #55–58, then finish the bounded calibration inventory. | Preserve four merged P2 fixes, the type-boundary witness and matrix-include regression. Finish strict-candidate accounting, effect-boundary coverage/mutation, serial mutation recipe, retained CI and dead-code checks. Other Stuff components remain outside this calibration slice. |
| Fastermod | Start its actual calibration pass at current main. | Ground, Diagnose, Types, Tests, Dead code, Findings and Report are not started. Establish its own rustybench performance evidence. Loc's corpus result does not by itself qualify fastermod. |
| Ptytest | Start its actual library calibration pass at current main. | Ground and the remaining stages are not started. Verify real library consumers against the candidate. Vault and diff-pretty PTY fixtures do not by themselves establish ptytest's API and consumer acceptance. |
| Tm | Finish Ground after the merged fixture repairs. | Reuse repeat, short-socket and pipe-output/exit evidence. Establish quiet-host cost and continue the named component pass. Do not resume a broader source investigation during winddown. |
| Toolbox | Remains blocked by Actions billing and host-tool qualification. | Recheck billing before dispatch. Missing ffmpeg/fio coverage and the historical worker-coverage statement must be reconciled; a skipped media suite is not a pass. |

Srv and fz have completed pass Reports and green default-branch CI at the checked
heads. Recheck those heads and guarantees during the campaign check-up. Do not
reopen their inventories without a changed input or demonstrated risk.

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
batch with prerequisites. Recommend no broader dispatch while required shapes
remain unexplained. Approval applies to the concrete report, not seeded TODOs.

## Upgrade Solid consumers on resumption

STUF-91 tracks the owner's request to upgrade every Solid consumer to stable
2.0. The owner reports that 2.0 left RC on 2026-11-17. Verify the official stable
release, changelog and migration guide before selecting exact versions.
Inventory all affected repositories and direct/transitive Solid dependencies,
then record each relevant breaking change and required migration before edits.
Check associated JSX/compiler, router, testing and SSR integrations where used.
Use supported pinned dependencies and preserve registry policy. Run each
consumer's type/lint, build, relevant tests and browser/SSR checks, with source
activation evidence. Open focused PRs and merge only verified heads. No releases
or production deployment are included. This is planned work; no Solid version
was changed during winddown.
