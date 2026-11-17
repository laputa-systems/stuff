# Campaign: deslop the fleet

Goal: every in-scope repository has truthful strict types, tests that detect real defects at its
public boundaries, no dead code, and structure that its review findings no longer fault. No repo
loses correctness, functionality, or performance on the way. CI enforces what the work
established, so the slop cannot return.

## Status

- **Resumed (2026-11-16):** the owner resumed
  `docs/HANDOFF-TODO-DESLOP-20261116.md` in parallel with STUF-89. Direct
  Vault and diff-pretty Tests work now runs in each canonical repository's
  `.work/wt/ds`, on branch `resume/deslop-tests-20261116`, carrying its stopped
  checkpoint plus current main. Original branches, dirty files and partial
  mutation evidence were [preserved before the overlapping clones moved to
  Trash](d-overlap-preservation.md). Review saved survivors and
  qualify boundary assertions first. Host constraints defer timing/cost
  acceptance; bounded correctness, coverage and Scenario counts use CPU guards
  and the shared mutation lock. No fleet rollout or STUF-75 work is authorized.
- **Resumed results:** Extensions [#5](https://github.com/joshuarli/extensions/pull/5)
  merged as `a45dcdc`, closing DSLP-6: matching Vitest/coverage 5.0.5, frozen
  scripts-disabled install, typecheck, 199 Node tests and coverage, plus Node 22
  CI pass. Optional binding engine metadata is preserved. This does not qualify
  its broader Ground/Tests, Stryker or browser lane.
  Its next functional Ground slice, [#6](https://github.com/joshuarli/extensions/pull/6),
  merged as `4137136`: CI now uses `make test` with the existing typecheck and
  all 213 Node cases. `make lint` runs the existing typechecker, and AGENTS.md
  maps current public boundaries. Parent evaluation of the actual
  `gha-test-workflow` rule returns no findings; Node 22 CI passes. DSLP-1 stays
  open for cold/warm cost measurements on a ready host.
  Tm's separate [#37](https://github.com/laputa-systems/tm/pull/37) merged as
  `7fd4994`, closing DSLP-6's repeat-fixture finding. Independent input batches
  preserve nine full-state observations and add literal window states; the
  expiry barrier catches a five-second fault missed by the old test. Controlled
  delayed probes fail before and pass after. Short exclusive fixture paths
  pass a real Unix-socket regression. Full native tests, lint and both platform
  CI jobs pass on `6a36076`. Historical CI lacks timestamps; this repairs the
  demonstrated fixture dependency without claiming its exact old trace.
- **Engine checkpoint:** [stuff#39](https://github.com/laputa-systems/stuff/pull/39)
  passed all ten checks on the stopped head `9510e790` and merged as `511cf18`,
  closing STUF-87's private import/recovery repair. Production is unchanged.
  STUF-88 remains open; the completed independent review of its full inventory
  patch found no supported source-level defect. Natural-refusal runtime and full production
  availability proof remain outstanding.
- **State:** assurance hardening (decision 13) landed or is in review. The owner dispatched
  diff-pretty, vault, and fz. Every in-scope repository has `TODO-DESLOP.md`. toolbox is out of
  scope (decision 12).
- **Current goal (2026-11-16):** finish the entire deslop campaign. Finish the
  direct queue and calibration, pilot and harness qualifications first. The
  prescribed M2 calibration review still gates tier-by-tier rollout; prepare
  that concrete report before seeking its approval. Canonical
  checkouts were synchronized before this work; dirty and nondefault branches
  were preserved.
- **Method:** usr's `deslop` skill is the one procedure (usr#34, merged: pre-merge contract, consumer and
  perf evidence, ticket revalidation, bounded component tasks; typing and mutation lessons). usr#39
  adds a `test-pyramid` audit before the Tests step's measurements, caps mutation at the Scenario
  tier (a larger run needs the owner's request), and draws Types candidates from the
  `refactor-python` and `refactor-ts` profiles. This doc holds only scope, decisions, sequencing,
  and status.
- **Repaired pilot defects:**
  - buildlib#8: `is_sha256` claimed `TypeIs[str]` but rejects most strings, so ty accepted a
    caller that raised `TypeError`. Now `TypeGuard[str]`, with a checker witness that fails lint
    if the narrowing turns unsound again. This was an escaped regression from buildlib#4. No other
    custom narrowing predicate appears in any deslop PR.
  - srv#38: the mutation gate diffed only `*.rs`, used the whole crate only as a fallback, and
    passed exit 3 unread. It now classifies the whole change, selects a union, reads the results,
    confirms timeouts by rerun, and fails on missing or empty evidence. `mime` is contract-tested
    instead of excluded: 21 more mutants, all caught. Two Content-Types that disagree with their
    registrations went to the owner (srv TODO-DESLOP).
  - buildlib#9: DSLP-9 no longer treats the open-ended `ELFHeader.kind` as a closed set.
  - buildlib DSLP-10 done: node-build#15 dropped its never-firing ELF `is_64` check (with a test
    that a 32-bit image still fails `elf-arch`), then buildlib#11 removed `elf_class` and `is_64`.
- **Negative controls:**
  - srv#39: a failing test fails `CI`. srv#40: a test deletion plus an unrelated production
    change fails `mutants` with 19 missed. The old gate passed the same tree in 5s.
  - Local controls: a docs-only change passes as irrelevant, Cargo.toml selects the scope,
    budget exhaustion fails, and a deletion-only hunk goes whole-file.
  - stuff#12: `gha-test-workflow` rejects `if: false`, impossible job conditions,
    `continue-on-error`, `|| true`, `make -n`, path filters, and wrapped commands, each by name.
- **Retention:** stuff#12 keeps eligibility in `fleet/policy/retention.toml` (srv's mutation lane
  and coverage target; srv and buildlib strict settings). Removing `TODO-DESLOP.md` leaves verdicts
  unchanged; removing a target, the job, a step condition, or a strict setting is reported. The
  rules are read-only, and none is rolled out.
- **Readiness by language and shape** (macOS arm64 unless CI):

  | Shape | Recipe | Measured | Verdict |
  | --- | --- | --- | --- |
  | Rust, small single crate (srv, 2k) | srv#38 gate | 235 mutants, 9m43s in CI; controls fail as intended | Qualified |
  | Rust, large crate (loc, 12k) | same gate, bounded scope | critical scope is 916 of 2,433 mutants (about 50 min on 4 jobs). Its counting core (229) left 29 survivors. Timeout reruns held about 10 cores each and were stopped. | Not a lane yet: needs sharding, a CPU cap (`cpu-guard`, usr#36), and suite threads capped in mutation runs |
  | Python, plain pytest (buildlib) | mutmut 3.8.1 (mirrored by STUF-83) | earlier pilot: 235 → 216 survivors | Mirrored, lane not qualified: needs the whole-change gate and CI negative controls |
  | Python, pytest-parallel consumers (stuff `repomod/`) | mutmut | rejected by pytest-parallel before workers start; serial (`-p no:parallel`) is the only route, and pytest-parallel's own repo also hits its TMPDIR defect | Mirrored; serial-only recipe, lane not qualified |
  | TypeScript, Node Vitest (extensions) | Stryker 10.1.1 (mirrored) | needs `typescript` and an explicit runner plugin; critical scope 345/199/147 (killed/survived/no coverage) in 657s; scoped run 5s | Mirrored, lane not qualified; Vitest/coverage mismatch fixed in extensions #5; the browser runtime remains unqualified |

- **Calibration landed:**
  - loc: Ground #5, Diagnose #6, and Types (#7; no setting adopted).
    The DSLP-6 P1 stdin double count is fixed in [loc#11](https://github.com/joshuarli/loc/pull/11),
    merged as `dd84c9c`: canonical paths are counted once across direct entries,
    directory walks and tracked-only walks. Native checks and Linux/macOS CI
    pass; five paired release workloads remain within their observed spread.
    The critical mutation lane and Dead code remain open.
  - stats: Ground #16 (CI runs `make test-ci`, an interrupted-import test repaired, and macOS
    `make test` red from setuid `ps` in `sandbox-exec`, DSLP-7).
  - stuff: Ground #11.
- **Known red:**
  - ish, loc, and lz get new `gha-test-workflow` findings for container-wrapped `make test` once
    stuff#12 lands.
  - oxish upstream workflows. Tm's demonstrated repeat-fixture dependency is
    repaired in #37; its broader deslop pass remains open.
- **Dispatched batch** (diff-pretty, vault, fz; tier-A Rust under 10k lines):
  - Ground, Diagnose, and Types are merged in all three. diff-pretty
    [Types #26](https://github.com/laputa-systems/diff-pretty/pull/26) merged
    as `251c68ae`: five interleaved pairs for renderer and pager workloads,
    including filtered streaming at three sizes, satisfy the idle-host gate;
    allocation counts and binary sizes are unchanged, and RSS ranges overlap.
  - **fz complete through Report:** [#32](https://github.com/laputa-systems/fz/pull/32)
    fixes controlling-TTY setup; [#33](https://github.com/laputa-systems/fz/pull/33)
    reaps selectors after driver death; [#34](https://github.com/laputa-systems/fz/pull/34)
    qualifies core boundaries; [#37](https://github.com/laputa-systems/fz/pull/37)
    qualifies terminal and signal boundaries. The combined Linux lane selects
    448 mutants: 432 caught, 16 unviable, zero missed or timed out, with exact
    exclusions and rejected harness runs retained. Native macOS coverage is
    90.94% lines / 77.49% branches. Pinned fzy runs in both CI platforms.
    [#38](https://github.com/laputa-systems/fz/pull/38) closes DSLP-4 with test-cost,
    ish consumer and five paired release terminal workload checks. No latency
    regression exceeds both observed spread and 2%. DSLP-6/7/8/9 are closed;
    [#39](https://github.com/laputa-systems/fz/pull/39) removes five unread
    benchmark lines and completes Dead code; no walk-back was established.
    [#40](https://github.com/laputa-systems/fz/pull/40), merged as `202a211b`,
    records the cumulative review and final scorecard with no open findings.
    Ish's library-only importer is repaired in
    [ish#30](https://github.com/joshuarli/ish/pull/30). Its fresh full consumer
    run separately timed out in unchanged input framing; worker contracts and
    Clippy pass with final fz loaded, and the earlier full run covers identical
    shipped Rust. [ish#29](https://github.com/joshuarli/ish/issues/29) retains
    the timeout with cause unproven.
  - **vault Tests in progress:** original `f871e81` is preserved. Draft
    [#30](https://github.com/laputa-systems/vault/pull/30) targets accept refusal
    without starving daemon startup, isolates stale-socket creation from
    concurrent forks, requires checksum-pinned rage 0.12.1 in CI and adds native
    macOS checks plus auditable mutation logs. Native macOS and Linux ARM64
    musl checks pass, including rage interoperability; two Linux keyring checks
    and two Secure Enclave tests remain unverified. The first CI store baseline
    exhausted 60 seconds before terminal tests finished and tested no mutants.
    A measured continuation retains every test with a 180-second timeout and
    twenty-minute total budget. The Linux store lane at `a0337e2` selects 51:
    45 caught, six unviable, zero missed or timed out. Closed, unmerged control
    [#31](https://github.com/laputa-systems/vault/pull/31) deletes a real test
    and adds an uncovered branch: ordinary checks pass, mutations fail with
    12 misses of 55. A native process probe now exercises actual cache startup
    and cached secret operations without hardware prompts. Its bounded
    98-case component run found one seed-validation survivor; the new process
    assertion catches that mutant; the final 98-case cache selection is qualified.
    A broader macOS run was interrupted, and a six-worker attempt exceeded
    `cpu-guard`; neither establishes qualification. Final coverage, test-cost
    and remaining platform/decision-region dispositions stay open. The stopped
    complementary 232-case filesystem selection completed 173: 102 caught,
    65 missed, six unviable, zero timeouts and 59 untested. Resume by reviewing
    those survivors; this partial run does not qualify the filesystem scope.
    Resumed head `0561a3e` adds listing-process and literal metadata-policy
    assertions. The complete 21-mutant directory-policy Scenario is qualified:
    21 caught, zero missed, unviable or timed out, every identity reconciled and
    every caught log failing a new policy assertion. This covers all seven
    saved survivors in that region. Three hand faults fail their intended
    assertions. An isolated-target native suite passes 44 unit, 28 integration
    and four terminal cases, with two hardware cases ignored, plus lint. The
    first final run reused the last mutant's shared-target artifact and was
    rejected; ordinary verification now has a separate target. All six checks
    pass on `0561a3e`, including the fresh 51-case Linux store gate (45 caught,
    six unviable, zero missed or timed out). That single CI scenario took
    thirteen minutes; it does not establish the ten-minute p50 target.
    That checkpoint left 58 original survivors and 59 untested cases; current
    reconciliation is below. Quiet-host cost and remaining decision regions
    keep PR30 draft and DSLP-4 open. The old filtered filesystem
    driver still must not be restarted unchanged.
    Current Tests head `10d38f5` adds independent filename/UTF-8 byte-limit
    oracles, a pure data-home table, private-file admission/read witnesses,
    directory opening and lock/mode repair. Filename selection: 31
    caught, four equivalent misses, one unviable and no timeouts across all 36
    cases; every equivalence follows the remaining guards, and no exclusion
    was added. Data-home has three caught; private-file has 30 caught/three
    equivalent/one unviable; directory opening has 19 caught/seven equivalent/
    two unviable; lock/mode has 13 caught/four equivalent/two unviable. Each
    complete selection has a fresh baseline, zero final timeouts and no new
    exclusions. Mapping original sites through the private production-used
    metadata helpers resolves 56 saved misses (38 caught, 18 equivalent),
    leaving nine. Seven formerly untested identities map to five caught/two
    unviable, leaving 52 unreconciled. Historical raw 232-case counts remain
    unchanged. Atomic-write/temp-file qualification is the next active slice.
    ARM64's passphrase-echo failure at `8dc8fa8` led to
    [PR34](https://github.com/laputa-systems/vault/pull/34), merged as `6a4b7d5`:
    prompt publication and input now share one hidden terminal session. A
    deterministic ordering witness fails before and passes after; native macOS
    and ARM64 Linux tests/lint, all four CI checks and independent review pass.
    Linux container keyring restrictions remain explicit skips. The fix is
    integrated into the Tests branch: 53 native unit tests, 28 integration and
    four terminal tests pass, with two hardware tests ignored and no optional
    skips. Latest-head CI is pending. Corrected branch coverage captures eight
    profiles previously lost when fixtures cleared the child environment:
    2,454/3,173 lines and 295/446 branches. The real file-operation order,
    flags, mode repair and error priorities remain intact; hardware, Linux and
    other OS-error/race decisions stay explicit. Exact proof is committed in Vault's
    `docs/deslop-filesystem.md`, readable from the canonical repository with
    `git show 10d38f5:docs/deslop-filesystem.md`; prompt evidence is in
    `docs/deslop-terminal-echo.md` at the same revision.
  - **Stuff lock repair:** [PR43](https://github.com/laputa-systems/stuff/pull/43)
    merged as `0d325ff` after all ten CI checks and independent review pass.
    Dropping `FileLock` now explicitly unlocks it even when a duplicate file
    descriptor remains open. The deterministic regression fails before and
    passes after; 23 store tests, 21 transaction tests and targeted clippy pass.
    This addresses the observed failure shape without claiming a retained
    descriptor was traced in the earlier docs-PR CI failure.
  - **diff-pretty Tests:** [PR31](https://github.com/laputa-systems/diff-pretty/pull/31)
    head `7b2a67e` includes the real bare-control repair `f17f82f`. Uncolored
    hunks previously retained NUL and C1 controls because stripping required
    ESC. A shared predicate fixes that path, retaining tabs and Unicode;
    literal public-API and owned-child CLI oracles fail before and pass after.
    The current twelve process cases, release workspace tests and lint pass;
    Linux/macOS/lint CI pass on `7b2a67e`. The complete final sanitizer selection
    has 70 caught, eight equivalent misses, one unviable and no timeouts, with
    no exclusions and every caught log failing the new CLI oracle. It includes
    the new predicate and one tool-selected plain-file field; its inventory
    differs from the earlier 79-case test-only comparison (4 caught before,
    57 after). The earlier CLI 24-case component records 22 caught/two unviable;
    numeric layout records 37 caught/one confirmed hang, retaining raw
    Timeout/exit 3. Release binaries both occupy 855,480 bytes; five alternating
    RSS observations per side on each of two real corpus inputs show no increase
    in those samples and identical outputs. Perf gate deferred: host busy.
    Current workspace coverage passes all 70 cases: 3,246/4,308 lines and
    593/924 branches. It identifies the unexercised public pager adapter and
    live lifecycle decisions; an owned PTY entry/source slice is active.
    The timing/test-cost gates, other renderer/pager decisions and
    whole-change CI lane keep the draft unmerged. The old Full run's 109 untested
    and 48 unconfirmed timeouts remain incomplete. Exact commands, dispositions
    and limits are committed in Diff's `docs/deslop-cli-tests.md`, readable with
    `git show 7b2a67e:docs/deslop-cli-tests.md` from its canonical repository.
  - **Resume order:** finish vault Tests and diff-pretty Tests directly, then
    their Dead code/Findings/Report steps. Fz is settled. Retain the owner-only
    hardware recovery and fleet-rollout boundaries below.
  - Mutation and coverage runs still take the shared host lock
    (`mkdir .work/tmp/mutation.lock` in stuff) and use `--timeout` at about 4x the baseline test
    phase.
  - Python and TypeScript mutation steps wait until their lanes qualify (STUF-83 mirrored the
    tools); those repos may still run Ground, Diagnose, Types, and Dead code.
- **Find campaign PRs:** `gh search prs --label deslop --owner laputa-systems --owner joshuarli`.
- **Needs you:**
  1. toolbox: fix Actions billing to bring it back in scope.
  2. M2 requires review of the concrete calibration report before broader fleet dispatch.
- **Resume prompt:** `Execute docs/campaigns/deslop.md from its Status. Follow its Charter.` After
  the dispatched batch, the next direct slices are loc's sharded lane under
  `cpu-guard` and the remaining calibration/pilot harness qualifications.
  Fleet fixer application waits for the prescribed qualification and M2 review.

## How the campaign runs

The campaign has two kinds of workers.

- **The campaign agent** runs from this doc in `stuff`. It owns every shared file: repomod rules and
  fleet policy in `stuff`, and the skills and `todo` tool in `usr`. It runs the foundations, the
  pilots, the seeding of tickets, the check-ups, and the method revisions.
- **Repo agents** are dispatched by the owner, one per repository. Each works that repository's
  `TODO-DESLOP.md` with the `deslop` skill and touches nothing outside that repository. Repositories
  are disjoint, so any number of repo agents can run at once.

The method is proven at small scale, then on complex repos, before it is handed out. Phases 1 and 2
are run by the campaign agent itself. Phase 3 starts only when the owner approves the calibration
report. From phase 3, the campaign agent seeds one size tier at a time. It checks up on the
settled repositories and folds what they learned into the skill before it seeds the next, larger
tier.

## Charter

- Decide and keep going. Record a decision here only when a later slice depends on it.
- Every campaign PR carries the `deslop` label (owner request, 2026-11-15). Create it first with
  `gh label create deslop -R <repo> --color 5319e7 --force`.
- Work inside the grant in **Execution boundary**. A plan does not supply missing permission. Park
  an item that needs authority outside the grant and list it under **Needs you** in Status.
- Fix the cause before you retry. A failing item gets two attempts after `root-cause`. Then park it
  with its cause and a retry condition.
- Fix egregious problems met on the way in their own commit, and record everything else as a
  ticket. Egregious means: an existing test suite that CI never runs, a test that fails on the
  default branch, or a `make test` slower than 5 minutes warm that has a clear drag cause.
- Correctness before cleanup. The method orders types and tests ahead of dead code and refactors.
  The perf gate applies from the first refactor slice.
- Shared files have one writer, the campaign agent: `repomod/`, `fleet/`, `docs/tagging.md`, the
  `usr` skills, and `usr/tools/todo`. Repo agents report gaps in those files in their `## Report`.
- Lanes the campaign agent delegates follow `orchestrate`, in worktrees under `.work/wt/<lane>`.
- Commits are Conventional Commits. The scope is the component, and the body carries the item ID
  (`deslop F2`, or `DSLP-4` in a repo). Code comments never cite this doc or a ticket.

## Decisions

### Owner (2026-11-14)

1. **Scope.** Rust, Python, and TypeScript code in the in-scope repositories (Reference). Vendored
   code counts, but only code we have modified is deslopped. Pristine vendored trees and pristine
   upstream code in forks are left alone.
2. **Excluded:** xsh, laputa, python-build, and bctl (under heavy development elsewhere), and deser.
   Also excluded are the forks that are effectively upstream: rg, rawzip, zlib-rs, lexopt, rustls, and
   webpki.
3. **Forks in scope,** limited to our changes against their upstream merge base: jaq, rust-fontconfig,
   rustix, rage, fd, oxish, crabtables, soulseek-rs. They get a new `fork-diverged` catalog tag (F1).
4. **Enforcement is mutation on the diff.** CI runs `make test` in every in-scope repository, plus a
   mutation lane scoped to the changed lines. A surviving mutant fails the lane unless the repo's
   mutation config lists it with a reason. Coverage is measured and reported, but it is never a gate
   or a threshold.
5. **Merging.** One PR per slice. The agent merges it when required CI is green and the slice's
   acceptance command passed. Work parked for the owner stays unmerged.
6. **Removals.** Behavior-preserving cuts land on their own. Removing live behavior or a public
   contract (a CLI flag, a public API, a compatibility path, a format) is a walk-back. It is filed as
   a ticket whose area starts with `Needs owner ·`, and the owner reviews those at each tier
   checkpoint.
7. **Fan-out through tickets.** After the method works, the remaining work is filed as tickets in a
   per-repo `TODO-DESLOP.md`, separate from `TODO.md`, so the owner can dispatch repo agents. The
   campaign checks each repository after its tickets settle.
8. **Fan-out needs approval.** Phase 3 starts only after the owner approves the calibration report
   (Phase 2). Until then the tooling must be proven on complex repos, not only small ones.
9. **Mirroring (2026-11-15).** The campaign agent may mirror the assurance dev tools to the stuff
   registries with `stuff publish mirror`: mutmut, cosmic-ray, vulture, deptry,
   `@stryker-mutator/core`, `@stryker-mutator/vitest-runner`, knip, and `@vitest/coverage-v8`,
   at pinned versions after vetting license and transitive dependencies. Nothing else is published.
10. **Unattended to the end (2026-11-15).** The owner is away and expects the campaign to finish
    with tickets filed in every applicable repository. Filing tickets is not fanning out:
    dispatching repo agents stays the owner's act. The campaign agent therefore finishes the
    pilots, extracts the `deslop` skill, runs as much complex calibration as it can, and then seeds
    `TODO-DESLOP.md` in every in-scope repository without waiting for approval. Status records how
    far calibration got, so the owner can judge when to dispatch. This supersedes decision 8's
    approval gate for seeding, not for dispatch.
11. **Skills.** Skill development in `usr` is in scope. The skills are where the campaign's lessons
   end up. Repo agents follow them, and they outlive the campaign. `test-audit` changes its position
   on line coverage first (K1).
12. **toolbox is out of scope (2026-11-15).** It is private, and GitHub starts no Actions job there
    (the account's payments or spending limit), so no PR can merge on green. Its `TODO-DESLOP.md`
    stays; an unpushed local branch in `~/d/toolbox` fixes its Linux ffmpeg install condition.
13. **Assurance hardening before broader dispatch (2026-11-15).** Repair the pilot defects, qualify
    the enforcement and mutation gates with negative controls, keep retention eligibility in fleet
    policy, make the `deslop` skill the one procedure, and measure readiness per language before the
    next dispatch batch.

### Prescribed

- **Fan out by size tier, not all at once.** The method must work at each scale before larger repos
  get it. Seeding tier N+1 waits until three repos of tier N have settled (or all of them, if the
  tier has fewer) and their feedback is in the skill. Stragglers keep working.
  *Reversed if* the tier B checkpoint changes nothing in the skill. Then seed C, D, and E together.
- **Repos over 50k lines are worked by component.** Ground and Diagnose cover the whole repo. Types,
  Tests, and Dead code run per component (a crate, a package, or a subsystem of at most about 20k
  lines), one PR each. The Ground ticket lists the components.
- **Tool recipes** (mutation, coverage, dead code, strict-profile candidates, escape-hatch counts)
  live in the deslop skill's [tools reference](https://github.com/joshuarli/usr/blob/main/dotfiles/base/.agents/skills/deslop/references/tools.md).
- **Joining `make lint`:** a dead-code tool joins a repo's lint only when the repo is clean under it
  with an allowlist of at most 5 entries, each with a reason.
- **A strict-profile setting joins the fleet profile only on evidence.** On pilot repos it must have
  rejected at least one real defect or deleted at least one escape hatch, while needing at most one
  false-positive suppression per 5k lines.
- **The perf gate covers perf-sensitive repos.** These are the rustybench repos (fastermod, lz, loc,
  e, ish) and any repo whose Ground ticket declares a workload. The gate runs on every refactor
  slice and on the repo's final state. Measure only when `perf-gate-ready` passes, with at least 5
  interleaved baseline/candidate pairs of the shipped profile.
  - **Within bound:** the median delta is under the observed spread or under 2%.
  - **Material regression:** the slice parks.
  - **Deferred (host busy):** the slice stays unmerged. It never passes by default.
- **Test cost budget.** A Tests step may raise warm `make test` time by at most 20% or 30 seconds,
  whichever is larger. Repos already slower than 5 minutes warm fix their drag first.
- **The mutation lane runs on Linux only,** on PRs that change source. Its CI-time p50 target is
  10 minutes or less. Its selection and result contract is the test-audit mutation reference.
- **Libraries.** Changes to a published or consumed library (smolith, ptytest, hi-lite, rustybench,
  laputa-ui-dashboard, buildlib, pytest-parallel) also run their known consumers' tests against the
  candidate, using `repomod deps` to find consumers. Repos stay disjoint because consumers pin
  released versions. The campaign publishes nothing.

### Delegated

- **Merge style.** Follow each repo's recent merged PRs. Pin the merge to the head SHA
  (`gh pr merge --match-head-commit`).
- **Combined PRs.** Ground and Diagnose may share one PR in repos under 5k lines.
- **Per-repo perf workloads.** A repo agent declares one only for a user-visible hot path (a CLI's
  main operation, a server route, a parser). It records "none" with a reason otherwise.
- **Where pins live.** Assurance tool pins go in the existing `fleet/policy/python-tools.toml` and
  `typescript-tools.toml`. Add `fleet/policy/rust-tools.toml` only for the cargo tools.

## Baseline

Measured 2026-11-14 on this host, in disposable clones under `.work/tmp/deslop-baseline`, with
`TMPDIR=.work/tmp`.

| Repo | Base | `make test` cold / warm | `make lint` | Known red |
| --- | --- | --- | --- | --- |
| srv | `dcc7921` | 5s / 0s | 1s | none |
| fastermod | `64cdc84` | 8s / 1s | 2s | none |
| buildlib | `6ef86b9` | 6s / 6s | 0s | none |
| pytest-parallel | `b94019e` | 9s / 7s | 1s | `tests/test_campaign.py::test_hooks_weights_groups_and_pin_via_plan` fails when `TMPDIR` is under a repo's `.work/tmp` and passes with the system `TMPDIR`. This is an isolation defect, and the fleet convention requires that `TMPDIR`. |
| extensions | `ac4f9d4` | 10s / 6s | none | No `lint` target and no lint workflow |

Fleet facts the plan relies on:

- The fleet standard requires a lint workflow running `make lint` (`repomod/rules/lint.py`). No rule
  requires CI to run the tests.
- stuff's CI never runs the repomod pytest suite. `make test` includes `repomod-test`
  (`Makefile:17`), but CI calls `cargo test --locked` directly (`.github/workflows/ci.yml:39`).
- stuff's CI run 43684749647 took 35m40s for the Rust test step on macOS (`xcode-27`) and 2m13s on
  Linux.
- No assurance tool is installed on this host: none of cargo-llvm-cov, cargo-mutants, cargo-machete,
  cargo-udeps, vulture, mutmut, or knip.
- Mutation prior art exists only in kache, as a local target: `make mutants-diff` with cargo-mutants
  27.1.0 and `.cargo/mutants.toml`. Its comment at `Makefile:95` says CI runs it, but no workflow
  references it.
- Five repos keep a rustybench baseline in `benches/baseline.json`: fastermod, lz, loc, e, and ish.
- extensions already depends on `@vitest/coverage-v8`. stuff and toolbox run Python tests through
  `pytest-parallel`, which has no coverage support.
- The `todo` CLI only finds `TODO.md` (`usr/tools/todo/src/todo.py:22`).
- The catalog tag set is closed (`repomod/catalog.py:47`).
- Canonical checkouts are blob-less partial clones. Fetching upstream into a local clone needs
  `--refetch`.

## Sequence

### Phase 0: foundations (campaign agent, serial)

| ID | Repo | Owns | Deliverable | Acceptance |
| --- | --- | --- | --- | --- |
| F1 | stuff | `repomod/catalog.py`, `docs/tagging.md`, `tests/repomod/`, `fleet/catalog.toml` (the tag only) | The `fork-diverged` tag is valid only together with `fork`. Tag the eight in-scope forks and run `topics apply` for them. | `make repomod-test`. `uv run repomod lint --rule topics --tag fork-diverged` lists exactly the eight forks with no findings. A catalog entry with `fork-diverged` but no `fork` is rejected. |
| F2 | stuff | `repomod/rules/workflows.py` or a new `rules/test_workflow.py`, `docs/policy-development.md`, `.github/workflows/ci.yml`, tests | Rule `gha-test-workflow`: some workflow runs `make test` or `make test-ci` on pull requests. It applies to non-fork repos and to `fork-diverged` forks. Its fixer adds a test workflow, the same way the lint fixer does. stuff's own CI starts running `make repomod-test`. | `make repomod-test` passes, with a fixture where the workflow calls `cargo test` directly and gets a finding. stuff's CI shows a passing repomod pytest step. |
| K0 | usr | `tools/todo/` | `todo --file PATH` works for every subcommand. Without it, the tool still finds `TODO.md` as before. | usr's todo tests cover `add`, `list`, and `check` against `TODO-DESLOP.md` while a `TODO.md` exists beside it, and each file keeps its own `Prefix`/`Next`. `make skills-check` passes. |
| K1 | usr | `test-audit/SKILL.md` and new `test-audit/references/mutation.md` | Rewrite the Coverage section. Coverage is measured routinely with `make coverage` and used to find unprotected boundaries and dead-code candidates. It is never a gate or a target. Add mutation testing: the result classes (caught, missed, unviable, timeout, budget exhausted), how to disposition a survivor, how to justify an equivalent mutant, test-only diff selection, and fault injection for each new boundary test. | `make skills-check`, with test-audit within the 8000-byte limit. The section says coverage is never a gate and no longer says to drop coverage reports. |

F1 and K0 may run in parallel because they touch different repositories. F2 follows F1. K1 may run
in parallel with F1 or F2.

### Phase 1: pilots (campaign agent; one lane per language, in parallel)

Run the full repo pass (below) on **srv** (Rust), **buildlib** (Python), and **extensions**
(TypeScript). Each pilot also qualifies its language's tools. Pin the tools in the repo, add
`make coverage` and `make mutants-diff`, add the CI mutation lane, and prove the lane with a
negative control: a throwaway PR that adds an unasserted branch must fail the lane. Close the
throwaway PR without merging.

**Checkpoint M1** (campaign agent):

- **F3.** Move the qualified pins into fleet policy. Add rules with fixers where the repair is
  deterministic:
  - `make-coverage-target`
  - `mutants-diff-lane`
  - `strict-typing-profile`, for the settings that met the evidence bar
- **K2.** Write the per-language tool recipes into `test-audit/references/` and
  `dead-code-archaeology`. Include the deletion record that `debloat` and `dead-code-archaeology`
  require.
- Score the pilots (see Checkpoints).

### Phase 2: calibration (campaign agent)

**2a, narrow.** Run the pass on three repos that each test one part of the method the pilots could
not:

- **fastermod:** the perf gate, against a rustybench baseline.
- **pytest-parallel:** coverage across parallel workers (this is new runner support, which unblocks
  stuff and toolbox), plus the known red above.
- **ptytest:** a library with consumers.

Then extract the repo pass into an explicit `deslop` skill in usr (**K3**). Replace the Repo pass
section here with a link to it, and write the ticket template into the skill.

**2b, complex.** Run the pass, using the `deslop` skill, on four repos that stress the tools at the
scale and shape of the larger tiers:

- **loc** (Rust, 12.5k): a real CLI with corpus semantics, a rustybench baseline, and musl and
  macOS artifacts.
- **toolbox** (Python, 18.9k): a pytest-parallel consumer. It proves coverage and mutmut through
  the runner on a real suite.
- **stats** (Rust and TypeScript, 68.4k): component mode, Stryker on a large TypeScript suite, a
  Cloudflare Worker runtime boundary, and cross-language fixtures.
- **stuff, the `repomod/` component** (Python): effect-heavy code (Git, GitHub, filesystem) behind
  fakes, so it proves mutation testing and dead-code tools on code that mostly orchestrates effects.
  The campaign agent already owns stuff's shared files, so this does not break disjointness.

2b's repos may run in parallel lanes, one per repo, after K3.

**Checkpoint M2** writes the **calibration report** into Status, then stops for the owner. The
report covers:

- For each tool: whether it ran on every calibration repo, its cost (wall time and CI minutes), its
  confirmed yield, and its false-positive rate.
- For each step: its yield against its cost.
- Escaped regressions, if any.
- The method changes made in response.
- A recommendation on whether to fan out, and which tier first.

The calibration repos count as settled for the scorecard. Phase 3 starts on the owner's approval.

### Phase 3: fan-out (campaign agent seeds; owner dispatches repo agents)

For each tier in order:

1. Sync with `uv run repomod sync`.
2. Roll out the F2/F3 rules to the tier with `repomod fix --repo` for each repo, and merge on green.
3. Seed each repo's `TODO-DESLOP.md` through one PR (Seeding, below), merged on green.
4. Report the tier as ready for dispatch.
5. Check up on each repo as its tickets settle (Check-up).
6. Run a checkpoint once the seeding condition for the next tier is met.

| Tier | Repos (Rust + Python + TS lines from `fleet/loc/v1`) |
| --- | --- |
| A, under 10k | pi-build (0.7k, `tools/` only), ffmpeg-build 2.8k, node-build 2.9k, fz 5.1k, doas-rs 5.4k, mdevd-rs 5.4k, diff-pretty 6.0k, vault 6.2k, cmake-build 7.0k, hi-lite 8.1k |
| B, 10k to 30k | lz 11.1k, rustybench 11.1k, laputa-ui-dashboard 13.8k, tinyland 14.1k, chromium-build 16.1k, e 20.1k, defuddle-rs 20.7k, gluon 28.7k |
| C, 30k to 80k | ctrs 32.7k, usr 42.2k, img 43.7k, tm 51.6k, discover 75.8k |
| D, over 80k, by component | ish 89.0k, smolith 118.1k, play 122.4k, tansu 123.2k, stuff 156.1k (components other than `repomod/`), kache 240.1k |
| E, forks (delta only) | jaq, rust-fontconfig, rustix, rage, fd, oxish, crabtables, soulseek-rs |

Two repos share files with the campaign agent and are never dispatched to a repo agent while it is
editing them. **usr** is worked only after K3 and between skill revisions. **stuff** is worked only
when no F item is open.

### Phase 4: close (campaign agent)

1. Check up on every in-scope repo.
2. Run `uv run repomod lint` over the in-scope set, which must be clean for F2/F3.
3. Finish the scorecard.
4. In each repo, move the open P3/P4 tickets from `TODO-DESLOP.md` into `TODO.md` with the `todo`
   tool, then delete `TODO-DESLOP.md`. Do this through one PR per repo, merged on green.
5. Run `ultrareview` on this doc's own deliverables in stuff, roll the lasting rules into
   `docs/fleet.md` and `docs/policy-development.md`, then delete this doc.

## Repo pass

The procedure is the `deslop` skill in usr ([SKILL.md](https://github.com/joshuarli/usr/blob/main/dotfiles/base/.agents/skills/deslop/SKILL.md)).
This doc does not restate its steps. Campaign-specific additions:

- Resolve each repository's canonical checkout under `~/repos` and work in an isolated
  `.work/wt/<step>` there. Keep its primary checkout, branch and existing changes untouched.
  Do not create duplicate host clones under `~/d`. The stuff integrator keeps its existing
  development checkout, as required by its own AGENTS.md.
- A repo agent works only its own repository and reports gaps in shared files in its `## Report`.

## Seeding

Seed each repo's `TODO-DESLOP.md` with `todo --file TODO-DESLOP.md`, using the prefix `DSLP`. The
seeded tickets are DSLP-1 through DSLP-5, one per step (Ground, Diagnose, Types, Tests, Dead code).
Each one carries:

- **Problem:** the repo-specific facts the campaign agent already has. These are the baseline times,
  the known reds, the components, the vendored trees, the consumers, and whether the perf gate
  applies.
- **Recommendation:** run the `deslop` skill's step, followed by its acceptance command.
- **Fix with:** `deslop`.

The file opens with three lines saying that one agent works the file and takes the lowest-numbered
open ticket whose area does not start with `Needs owner ·`, that steps 6 and 7 follow DSLP-5, and
that `## Report` sits in the header above `## Tickets`. Owner items use the area prefix instead of
a heading, and the Report stays in the header, because `todo fmt` reorders tickets around fixed
free text and `todo add` appends after the last ticket's trailing text. Findings that steps 2 to 5 discover are appended as DSLP-6 and later, so ticket order still
matches step order. Fleet-wide or shared-file work never becomes a repo ticket.

## Check-up

A repo is **settled** when all of these hold:

- DSLP-1 to DSLP-5 are closed.
- No P1 or P2 ticket is open, except owner items (area `Needs owner ·`).
- `## Report` is complete.
- CI is green on the default branch.
- `uv run repomod lint --repo <repo>` is clean for the F2/F3 rules.

The campaign agent then:

1. Re-measures Ground's numbers on the default branch in a fresh clone.
2. Runs the perf gate for perf-sensitive repos against the base SHA.
3. Spot-checks one boundary test with an injected fault.
4. Copies the Report into the scorecard.
5. Moves the repo's `Needs owner ·` items into Status.

A repo that fails a check-up gets a new ticket. It is not settled.

## Checkpoints

A checkpoint runs at M1, at M2, and before each tier after A is seeded. It reads the scorecard and
the Reports.

- **Yield versus cost, per step and per tool.** A step or tool with zero confirmed yield across
  three or more repos is narrowed or cut from the skill. A dead-code tool whose reviewed findings
  are more than half false positives drops to discovery-only. Confirmed yield means a defect found,
  an escape hatch deleted, a survivor killed, code deleted, or a finding fixed.
- **Escapes.** A regression later traced to a campaign PR gets `root-cause`, a guard (a test, a
  rule, or a skill rule), and a method change, all before the next tier is seeded.
- **Skill revision.** Each feedback item that recurs in two or more Reports becomes a rule in
  `deslop`, `test-audit`, `typing-audit`, `debloat`, or `dead-code-archaeology`. Each new rule cites
  the repo and PR where the slop got through. `make skills-check` must pass.
- **Owner batch.** Walk-backs and contract changes go into Status under **Needs you**, each with a
  recommendation. They do not block the next tier.

## Acceptance

| Deliverable | Proof |
| --- | --- |
| Every in-scope repo has completed the pass | A scorecard row for every repo, with after-values and a check-up date |
| CI runs the tests | `uv run repomod lint --rule gha-test-workflow` has no findings for the in-scope set |
| Mutation on the diff is enforced | `--rule mutants-diff-lane` is clean, and the pilot negative controls failed the lane as intended |
| Strict typing is enforced | `--rule strict-typing-profile` is clean for the in-scope set |
| Nothing regressed | Every perf-gated repo's final verdict is within bound, consumer tests are green, and escaped regressions number zero or each has a guard |
| The method outlives the campaign | The `deslop` skill exists, and `test-audit` contains the K1 coverage and mutation sections |
| The tickets are gone | No `TODO-DESLOP.md` remains in any in-scope repo |

## Needs environment

These are run by the owner or by CI, never assumed to pass:

- **Linux-only and macOS-only paths.** The CI matrix of each repo is the proof. Local runs here are
  macOS only.
- **Hardware or privileged tests:** doas-rs (setuid), mdevd-rs and tinyland (Linux devices). Repo agents record which boundaries only CI or the owner can exercise.
- **Browser suites:** extensions `test:browser` and tansu's Playwright tests need the pinned browsers.
- **Live services:** stuff's `make test-r2-live` and OpenOrange deployments stay opt-in.
- **Timing.** A perf gate deferred because the host is busy is re-run by the owner on an idle host.

## Execution boundary and non-goals

**Authorized** for the campaign agent, and for repo agents inside their one repository:

- Clones and worktrees under `.work/`.
- Branches, PRs, and merges on green, per owner decision 5.
- CI workflow edits that add the test job and the mutation lane.
- Pinned dev-only tool dependencies from the qualified list.
- `todo` edits to `TODO-DESLOP.md`.
- For the campaign agent only: repomod rule and fixer changes, `repomod fix --repo` for in-scope
  repos once the rule is merged and the canonical stuff checkout is synced, `topics apply` for the
  eight `fork-diverged` repos, and skill and `todo` tool changes in usr.

**Forbidden:**

- Releases and publishing (`repomod release`, `stuff publish`, crates.io, PyPI).
- Edits in canonical checkouts.
- Edits in excluded repos, or in pristine vendored or upstream code.
- Changing the pinned nightly.
- Formatters.
- Force pushes.
- Changes to branch protection or repository settings.
- Persisted or wire format changes.
- Weakening a correct test or a checker setting.
- `repomod fix` against the live catalog while repomod itself is being changed.
- Catalog edits other than F1's tag.

**Contract changes the owner has approved:**

- The new `fork-diverged` tag and its topic.
- The new fleet rules (F2, F3) that report findings on every in-scope repo.
- The test-audit position on coverage.
- `todo --file`.

Every other contract change is a walk-back.

**Non-goals:**

- Go, Swift, Zig, and shell code.
- Performance optimization beyond the bound: speedups are welcome, but they are not targets.
- Coverage percentages as goals.
- A database, dashboard, or workflow framework for tracking.
- Resyncing oxish's vendored copies in ssh-build and xsh.

## Reference

**Scorecard fields.** Each is recorded before and after:

- source lines and test lines
- warm `make test` time
- line and branch coverage
- mutation results on the critical scope (caught, missed, unviable, timeout)
- escape hatches
- dead code removed (lines and dependencies)
- findings filed and fixed, by priority
- perf verdict
- escaped regressions

**Fork divergence**, measured 2026-11-14 against fetched upstream. Code changes since the merge base:

| Fork | Code change |
| --- | --- |
| soulseek-rs | +11.5k/−3.9k |
| crabtables | +9.6k/−0.4k |
| oxish | +4.1k/−2.6k |
| fd | +3.1k/−1.7k (CLI ported to lexopt) |
| rage | +1.9k/−2.5k |
| rustix | +0.2k/−1.5k |
| rust-fontconfig | +0.5k |
| jaq | +55/−237 |
