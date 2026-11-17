# Historical deslop status through 2026-11-17

This is a preserved historical checkpoint, not current acceptance or authorization.
Use the campaign Status and roadmap for current state.

## Status

- **Resumed (2026-11-16):** the owner resumed
  `docs/HANDOFF-TODO-DESLOP-20261116.md` in parallel with STUF-89. Direct
  Vault and diff-pretty Tests work now runs in each canonical repository's
  `.work/wt/ds`, on branch `resume/deslop-tests-20261116`, carrying its stopped
  checkpoint plus current main. Original branches, dirty files and partial
  mutation evidence were [preserved before the overlapping clones moved to
  Trash](d-overlap-preservation.md). Review saved survivors and
  qualify boundary assertions first. Timing/cost acceptance requires actual
  pre/post gate exit 0; bounded correctness, coverage and Scenario counts use CPU guards
  and the shared mutation lock. No fleet rollout or STUF-75 work is authorized.
- **Resumed results:** Extensions [#5](https://github.com/joshuarli/extensions/pull/5)
  merged as `a45dcdc`, closing DSLP-6: matching Vitest/coverage 5.0.5, frozen
  scripts-disabled install, typecheck, 199 Node tests and coverage, plus Node 22
  CI pass. Optional binding engine metadata is preserved. This version repair
  does not qualify Tests, Stryker or the browser lane.
  Its next functional Ground slice, [#6](https://github.com/joshuarli/extensions/pull/6),
  merged as `4137136`: CI now uses `make test` with the existing typecheck and
  all 213 Node cases. `make lint` runs the existing typechecker, and AGENTS.md
  maps current public boundaries. Parent evaluation of the actual
  `gha-test-workflow` rule returns no findings; Node 22 CI passes.
  [#7](https://github.com/joshuarli/extensions/pull/7), merged as `acbedac`,
  closes Ground: current main passes 226 Node cases, cold/warm costs are
  50.49/48.34 s and lint 1.17 s under one CPU and one Vitest worker. All
  actual pre/test/immediate-post gates pass. These are bounded-worker costs,
  not CI's default concurrency. [#8](https://github.com/joshuarli/extensions/pull/8),
  merged as `a737ca1`, completes Diagnose with three assumed P2 findings and
  one P3. Parent probes confirm that a context-page completion can survive
  SIGKILL before its posts persist, and that EACCES reading an archive can
  become an empty collection before a successful replacement write. Timeline
  completion shared across operations remains an explicitly unproven risk;
  CLI help advertises rejected flag syntax. Findings are DSLP-7–10. Runtime
  code is unchanged by Diagnose. [#9](https://github.com/joshuarli/extensions/pull/9),
  merged as `f75b764`, completes Types: preserve caption element inference
  through the existing runtime array guard and remove one redundant Chrome
  storage assertion. The measured unsafe-argument rule has four real reports,
  zero false positives and zero final reports. Its matching compiler/lint
  provider is pinned from Stuff; independent compiler and adopted lint pass.
  The invalid-program control fails with TS2551; reverting the real guard
  produces four lint diagnostics. Hatch lines fall 379 to 378, all 226 Node
  cases and three CI checks pass, gated warm test/lint costs are 51.54/1.16 s.
  Existing CI exercises compiler/tests but not the separate lint command.
  Browser, appliance, live-service and broader Tests qualification remain open.
  [#10](https://github.com/joshuarli/extensions/pull/10), merged as `63377d7`,
  repairs DSLP-8: unreadable, invalid-UTF-8, malformed or non-array record
  snapshots fail before replacement. Eleven regressions fail on the original
  source; all fifteen component cases and 237 Node tests pass. The changed
  reader's 24 mutation identities are 22 killed and two equivalent; remaining
  storage decisions stay open. [#11](https://github.com/joshuarli/extensions/pull/11),
  merged as `aa120bb`, repairs DSLP-7 by saving ancestors before completion.
  An additive completion-validity column retries legacy false-ok rows only
  when needed. Real SIGKILL/reopen controls, 243 tests, lint, all 40 selected
  mutants and independent schema/restart review pass. Typed fixtures avoid
  casts. Whole-component storage, browser and whole-change CI qualification
  remain open; timeline ordering remains unproven.
  Tm's separate [#37](https://github.com/laputa-systems/tm/pull/37) merged as
  `7fd4994`, closing DSLP-6's repeat-fixture finding. Independent input batches
  preserve nine full-state observations and add literal window states; the
  expiry barrier catches a five-second fault missed by the old test. Controlled
  delayed probes fail before and pass after. Short exclusive fixture paths
  pass a real Unix-socket regression. Full native tests, lint and both platform
  CI jobs pass on `6a36076`. Historical CI lacks timestamps; this repairs the
  demonstrated fixture dependency without claiming its exact old trace.
- **Disk cleanup:** Stuff is on main at `9aaf94bc` after
  [#49](https://github.com/laputa-systems/stuff/pull/49) passed all ten checks.
  Retired the clean, idle, patch-equivalent `deslop-current` and
  `deslop-progress` worktrees after archiving useful ignored evidence.
  Removed one unused generated ctrs guest disk template from the old
  `repomod-mirror-x0_neb7j` scratch copy, reclaiming 64 GiB. Its source and
  other assets remain; unknown, dirty and parked worktrees, private clones,
  preservation refs and evidence archives were kept. Exact paths, provenance,
  hashes and before/after measurements are in canonical
  `.git/deslop-evidence/20261117-disk-cleanup/receipt.txt`.
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
  | Python, pytest-parallel consumers (stuff `repomod/`) | mutmut | rejected by pytest-parallel before workers start; serial (`-p no:parallel`) is the only qualified execution route; pytest-parallel's TMPDIR fixture prerequisite is now repaired | Mirrored; serial recipe still needs lane qualification |
  | TypeScript, Node Vitest (extensions) | Stryker 10.1.1 (mirrored) | needs `typescript` and an explicit runner plugin; critical scope 345/199/147 (killed/survived/no coverage) in 657s; scoped run 5s | Mirrored, lane not qualified; Vitest/coverage mismatch fixed in extensions #5; the browser runtime remains unqualified |

- **Calibration landed:**
  - loc: Ground #5, Diagnose #6, and Types (#7; no setting adopted).
    The DSLP-6 P1 stdin double count is fixed in [loc#11](https://github.com/joshuarli/loc/pull/11),
    merged as `dd84c9c`: canonical paths are counted once across direct entries,
    directory walks and tracked-only walks. Native checks and Linux/macOS CI
    pass; five paired release workloads remain within their observed spread.
    The critical mutation lane and Dead code remain open. Two bounded Tests
    slices now merge with all five checks green:
    [#12](https://github.com/joshuarli/loc/pull/12), `d0867b2`, catches both
    invalid-UTF-8 first-line survivors with four independent byte inputs;
    [#13](https://github.com/joshuarli/loc/pull/13), `92ffad1`, catches both
    assembly preprocessor-condition survivors with literal classifications.
    Complete function selections are two caught/one unviable and twelve
    caught/two unviable, respectively. Their hand faults fail the new
    assertions, and restored full suites and lint pass. Warm cost is 3.24 s
    before and 3.27 s after each slice, with actual pre/post gates passing.
    One ordinary run overlapped in-place mutation and is discarded; the final
    ordinary proof uses restored source and a fresh target. Other historical
    counting survivors and unconfirmed hangs remain unqualified. Exact proof
    is in `docs/deslop-invalid-utf8.md` and `docs/deslop-assembly.md` at `92ffad1`.
    [#14](https://github.com/joshuarli/loc/pull/14), merged as `f5603d8`,
    pins stopping positions and counts when markers change within a cached
    block. All 507 unit, 27 CLI and one fixture case, lint and five CI checks
    pass. The complete loader selection remains three caught and one unviable
    before and after; it does not qualify the remaining masks component.
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
    Current Tests head `d409423` adds independent filename/UTF-8 byte-limit
    oracles, a pure data-home table, private-file admission/read witnesses,
    directory opening and lock/mode repair. Filename selection: 31
    caught, four equivalent misses, one unviable and no timeouts across all 36
    cases; every equivalence follows the remaining guards, and no exclusion
    was added. Data-home has three caught; private-file has 30 caught/three
    equivalent/one unviable; directory opening has 19 caught/seven equivalent/
    two unviable; lock/mode has 13 caught/four equivalent/two unviable. Each
    complete selection has a fresh baseline, zero final timeouts and no new
    exclusions. Mapping original sites through the private production-used
    metadata helpers and completing atomic-file, staging/listing, identity-input
    and bootstrap-domain witnesses reconciles all 65 original misses:
    46 caught and 19 equivalent. All 59 original untested identities map to
    49 caught, four equivalent and six unviable. Historical raw 232-case counts
    remain unchanged; these mapped component results are not a fresh whole-run
    pass. Atomic-file's current generated selection has 20 caught/four
    equivalent/four unviable, plus six original match guards independently
    injected and caught. Staging/listing has 15 caught/four unviable;
    identity input nine caught/one equivalent/one unviable; bootstrap four
    caught. Fresh baselines and captured outer exits qualify these selections.
    ARM64's passphrase-echo failure at `8dc8fa8` led to
    [PR34](https://github.com/laputa-systems/vault/pull/34), merged as `6a4b7d5`:
    prompt publication and input now share one hidden terminal session. A
    deterministic ordering witness fails before and passes after; native macOS
    and ARM64 Linux tests/lint, all four CI checks and independent review pass.
    Linux container keyring restrictions remain explicit skips. The fix is
    integrated into the Tests branch: 65 native unit tests, 28 integration and
    four terminal tests pass, with two hardware tests ignored and no optional
    skips. At `6856af3`, macOS, both Linux musl suites and lint pass, but CI's
    mutation job fails its twenty-minute budget: the Linux job selects
    macOS-only changed functions, which it cannot exercise. Store's 51 cases
    still yield 45 caught/six unviable. A platform-correct bounded CI recipe
    remains required; native component receipts do not qualify that job.
    Native interposition tests now exercise
    write, file-sync, rename, directory-sync and compound cleanup failures,
    plus SIGKILL after file sync and after rename with clean retry. An injected
    skipped-cleanup fault fails the literal residue assertion. Process crashes
    do not prove physical power-loss durability. A non-UTF-8 filename witness
    remains unrun because this filesystem returns EILSEQ. Fresh branch coverage
    includes the child profiles previously lost when fixtures cleared their
    environment: 2,970/3,571 lines and 361/486 branches across four first-party
    Rust files, including inline tests. Three interleaved matched two-core,
    two-test-thread pairs pass every pre/test/post gate: median warm cost
    6.41 s before and 24.24 s after. The 17.83 s increase is within the 30 s
    allowance; serial exploratory receipts are retained separately. Short
    worktree names and fresh targets repair the path-only qualification failure.
    Independent review finds no supported defect in the filesystem refactors.
    Signal setup/restoration primitives now have controlled failure witnesses.
    A bounded owned-PTY child calls the real `read_passphrase` with empty and
    invalid UTF-8 input, verifies combined read/restore errors, signal handler
    ordering and terminal restoration, and cannot reach hardware. All five
    generated caller mutations are caught; a dropped-secondary-error hand
    fault fails the intended assertion. Fresh native coverage at `c68d9cc`
    passes 68 unit, 29 integration and four terminal cases: 3,235/3,779 lines
    and 423/544 branches including inline tests. Two hardware cases remain
    ignored. Warm cost is 23.17 s, within the 30 s increase allowance. Rare
    descriptor/syscall failures and the post-read signal window remain open.
    The CI mutation job selects macOS-only functions on Linux and exceeds its
    budget; platform-aware CI repair awaits explicit owner authorization.
    Separately, [#35](https://github.com/laputa-systems/vault/pull/35) merged
    as `0e72b21`: create stale sockets in an owned Rust test child and wait
    for exit, so parallel forks cannot inherit a listener. Controlled old/new
    overlap, ten stress runs with 1,000 process launches, native tests/lint
    and all four CI checks pass. The draft integrates this fixture locally
    as `c67f65f`, retaining its extra cache cases; the full native suite passes.
    The real file-operation order,
    flags, mode repair and error priorities remain intact; hardware, Linux and
    other OS-error/race decisions stay explicit. Exact proof is committed in Vault's
    `docs/deslop-filesystem.md`, readable from the canonical repository with
    `git show d409423:docs/deslop-filesystem.md`; caller proof is in
    `docs/deslop-passphrase-errors.md` at the same revision.
    Four integrated Vault worktrees were retired after private evidence archives
    passed readback and checksum checks; parked work and services were retained.
  - **Stuff lock repair:** [PR43](https://github.com/laputa-systems/stuff/pull/43)
    merged as `0d325ff` after all ten CI checks and independent review pass.
    Dropping `FileLock` now explicitly unlocks it even when a duplicate file
    descriptor remains open. The deterministic regression fails before and
    passes after; 23 store tests, 21 transaction tests and targeted clippy pass.
    This addresses the observed failure shape without claiming a retained
    descriptor was traced in the earlier docs-PR CI failure.
  - **diff-pretty Tests:** [PR31](https://github.com/laputa-systems/diff-pretty/pull/31)
    includes the real bare-control repair `f17f82f`. Uncolored
    hunks previously retained NUL and C1 controls because stripping required
    ESC. A shared predicate fixes that path, retaining tabs and Unicode;
    literal public-API and owned-child CLI oracles fail before and pass after.
    Current workspace tests and lint pass; exact-head platform checks continue
    after integration. The complete sanitizer selection
    has 70 caught, eight equivalent misses, one unviable and no timeouts, with
    no exclusions and every caught log failing the new CLI oracle. It includes
    the new predicate and one tool-selected plain-file field; its inventory
    differs from the earlier 79-case test-only comparison (4 caught before,
    57 after). The earlier CLI 24-case component records 22 caught/two unviable;
    numeric layout records 37 caught/one confirmed hang, retaining raw
    Timeout/exit 3. Release binaries both occupy 855,480 bytes; five alternating
    RSS observations per side on each of two real corpus inputs show no increase
    in those samples and identical outputs. Fresh matched shipping-profile
    measurements now establish a regression: five interleaved pairs across
    22 benchmark rows have all pre/benchmark/immediate-post exits 0, but corpus
    rendering rises from 4.871 ms to 5.259 ms, about 8%, exceeding spread and
    the 2% bound. Candidate stays draft. Both control-scan optimization attempts
    are rejected and source is restored: neither demonstrates a reproducible
    end-to-end benefit. A rotated three-side comparison puts unchanged current
    within 0.3% of baseline. Parent's higher-precision full 22-row repeat has
    no row beyond both spread and 2%, but corpus median is still 4.928 ms versus
    5.182 ms (+5.14%, below its 0.372 ms spread). The original regression's
    mechanism remains unresolved; no speedup or stable equality is claimed.
    Unstripped profiling is separate from timing. A separate five-pair shipped
    CLI process comparison has no regression beyond spread: 34.903 ms baseline
    versus 34.341 ms current, with the same production feature closure and output.
    That workload does not resolve the earlier library benchmark regression.
    Public draw/error witnesses now qualify all 14 selected mutations: 13
    caught and one allocation-only functional equivalent. All three new
    literal scenarios pass, with the complete selection and faults recorded.
    Alignment [PR33](https://github.com/laputa-systems/diff-pretty/pull/33)
    merged as `aa0e505`, closing DSLP-9: empty inputs no longer invent an
    operation, and one-sided runs retain every token. Independent enumeration
    checks 225 public input pairs; all 66 mutations are classified (62 caught,
    two unviable, two allocation-only equivalents). All 103 fixtures match,
    and five shipping-profile pairs across 22 workloads meet the declared
    performance bound with matching allocations and binary sizes. All three
    platform/lint checks pass, including the separate test-only Clippy repair.
    All 103 corpus fixture outputs match, with the intended bare-control
    correction separately checked against its literal oracle. Configuration,
    source/input hashes, spread and reproduction script are in
    `docs/deslop-tests-performance.json` at `f609068`. CLI rustybench 0.4.0
    wraps library 0.5.0; production-profile benches require
    `-Z panic-abort-tests` alongside build-std to avoid duplicate core graphs.
    Fresh integrated workspace coverage passes all 88 executable cases and
    one doctest: 3,681/4,529 lines and 648/930 branches, including inline tests.
    Public pager-entry PTY cases, output flush/error
    witnesses and fragmented streaming consumers now pass; complete adapter
    selection has seven caught, streaming nine caught/one unviable. Three
    literal Session navigation scenarios qualify the complete five-method
    selection: 43 caught/one unviable. No Session resize operation exists;
    other live-loop and renderer decisions remain open. No tests are ignored.
    Lint and workspace Clippy pass. Parent reran focused navigation and
    atomic-fault checks after integration.
    Matched warm release-suite costs are 1.18 s before and 1.17 s after,
    with both pre/test/immediate-post triples passing. These single observations
    establish the cost allowance, not a speedup. The unresolved runtime timing
    result, other renderer/pager decisions and
    whole-change CI lane keep the draft unmerged. The old Full run's 109 untested
    and 48 unconfirmed timeouts remain incomplete. Exact commands, dispositions
    and limits are committed in Diff's `docs/deslop-cli-tests.md`, readable with
    `git show 3653bb3:docs/deslop-cli-tests.md` from its canonical repository.
  - **pytest-parallel calibration:** [PR15](https://github.com/joshuarli/pytest-parallel/pull/15)
    merged as `4968f8e` after all three exact-head checks passed. A local
    pytest.ini isolates the plan fixture from ancestor configuration under
    repo-owned TMPDIR; the original failure is reproduced and the unchanged
    plan assertions now pass. Full 119-case tests pass twice, Ruff/ty pass,
    gated warm costs are 6.18 s and 6.13 s, lint 0.74 s. Existing CI already
    runs make test. Ground [PR16](https://github.com/joshuarli/pytest-parallel/pull/16)
    merged as `0ecb2b3`: cold/warm costs are 7.50/7.48 s, lint 1.18 s, and the
    CPU-trivial benchmark is explicitly insufficient for runtime performance
    acceptance. Diagnose [PR17](https://github.com/joshuarli/pytest-parallel/pull/17)
    merged as `60129d8`: scheduling-hook AttributeErrors silently discard
    grouping, weights or pins (DSLP-6), reproduced through a built wheel and
    independently confirmed by the parent. Types
    [PR18](https://github.com/joshuarli/pytest-parallel/pull/18) merged as
    `85ef2ff`: all strict candidates measured, no setting meets the adoption
    rule, 76 hatch-matching lines unchanged, current profile retained. Each PR
    has all three exact-head checks green. Native worker coverage
    [PR19](https://github.com/joshuarli/pytest-parallel/pull/19) merged as
    `eb2aa8e`; [PR20](https://github.com/joshuarli/pytest-parallel/pull/20)
    corrects wheel-size accounting and records the real Stuff consumer.
    An installed candidate runs all 1,410 repomod tests with three skips and
    two independently measured worker processes. The final wheel is 31,199 B
    (+205 B from README metadata); runtime package files are byte-identical.
    Scheduling [PR21](https://github.com/joshuarli/pytest-parallel/pull/21)
    merged as `ef73bbe` with six literal tests and a bounded serial mutation target: 264 killed,
    11 reviewed functional equivalents and one confirmed hang across all
    276 identities, independently repeated. Its 126 tests and lint pass;
    all three checks pass after integrating PR20's documentation. Whole-change
    mutation and CI qualification remain open.
    [PR22](https://github.com/joshuarli/pytest-parallel/pull/22), merged as
    `2c69571`, fixes DSLP-6: grouping, weight and pin hook implementation
    errors propagate before worker startup; failed JSON plans emit no plan.
    All three installed-base-wheel regressions fail as intended and the
    installed candidate passes them, normal custom hooks and missing defaults.
    All 130 tests, Ruff, ty and three CI checks pass. Five gated installed-wheel
    workload pairs have overlapping ranges; no speed difference is established.
  - **Buildlib calibration:** [PR12](https://github.com/laputa-systems/buildlib/pull/12)
    merged as `1a1132b` with independent public ELF header oracles. All 98
    header identities are classified: 90 killed and eight diagnostic-only
    survivors. A bounded real FIFO catches the read-until-EOF mutant while
    its producer remains open. [PR13](https://github.com/laputa-systems/buildlib/pull/13)
    merged as `dbc5e5a` with literal Mach-O dependency, install-name and rpath
    oracles. All 28 string identities are classified: 27 killed and one
    equivalent codec alias. Parent repeats recover complete mutation tool-cost
    receipts. These test-only slices leave runtime and dependencies unchanged.
    [PR14](https://github.com/laputa-systems/buildlib/pull/14), merged as
    `ba50980`, qualifies the complete ELF module: all 509 identities map to
    results, with 469 killed and 40 dispositioned survivors, zero untested
    identities or timeouts. The bounded selection takes about 21 s. This
    supersedes the narrower header scope rather than adding to its counts.
    The matching Mach-O review finds a real byte-order defect. Separate
    [PR15](https://github.com/laputa-systems/buildlib/pull/15), merged as
    `5a1852c`, retains byte order through a private parser without changing
    public raw commands or adding file reads, closing DSLP-11. The eight-case
    literal regression fails four big-endian inputs before and passes all
    cases after. All 166 tests and lint pass; Node-build's 19 and Python-build's
    24 affected tests print the candidate module path and pass. The affected
    147-mutant scope has 140 killed, six diagnostic-only survivors and one
    equivalent default. That repair changes the inventory from 405 to 401;
    it is not a fixed-identity score. Warm suite cost is 6.42 s, within its
    allowance; the pure-Python wheel grows by 40 B with no new dependencies.
    [PR16](https://github.com/laputa-systems/buildlib/pull/16), merged as
    `5450122`, completes the current Mach-O module: 383 killed and 18
    dispositioned survivors across 401 fixed identities, versus 359/42 before.
    Raw headers, signature ranges, strict bounded process invocation and a
    changing-file normalization boundary gain nine passing fault controls.
    The 193-test suite, lint and both CI checks pass; gated warm cost is 6.42 s.
    [PR17](https://github.com/laputa-systems/buildlib/pull/17), merged as
    `2c535f3`, qualifies release's 331 identities: 317 killed, nine equivalent
    and five diagnostic-only survivors, zero other classes. Complete manifest
    bytes, execute bits, invalid prefixes and unsafe checksum assets have
    independent oracles; a real changed-locale child catches default-encoding
    reads previously considered equivalent. All five hand faults fail; 201
    tests, lint and both CI checks pass, with gated warm cost 6.45 s.
    These qualification slices leave runtime and dependencies unchanged.
    [PR18](https://github.com/laputa-systems/buildlib/pull/18), merged as
    `87a248d`, qualifies all 388 locks identities: 378 killed, three equivalent
    and seven diagnostic-only survivors. Actual Unicode decoding under a
    changed locale and a bounded 1.5 MB HTTP download replace brittle argument
    and chunk-sequence assertions. Both faults fail; native tests/lint, parent
    integration checks and both CI checks pass. [PR19](https://github.com/laputa-systems/buildlib/pull/19),
    merged as `8d7e873`, adds informational branch coverage with a pinned
    development-only tool: 900/901 statements and 291/292 branches over all
    first-party files and child processes, zero excluded lines. The remaining
    negative-range guard is unreachable through public unsigned-field readers.
    Three added boundary faults fail, all 207 tests/lint and both CI checks
    pass, and the 910 parser identities exactly retain prior result classes.
    Gated warm suite/coverage costs are 7.48/7.46 s; wheels remain byte-identical
    at 25,126 B. Historical whole-package counts remain historical; whole-change
    selection, `make mutants-diff` and CI qualification remain open under DSLP-4.
    No mutation gate or workflow is implemented without the pending authorization.
    Exact reproduction and
    dispositions are in `docs/deslop-elf-header.md` and
    `docs/deslop-macho-strings.md`, `docs/deslop-elf-contracts.md` and
    `docs/deslop-macho-byte-order.md`, `docs/deslop-macho-contracts.md` and
    `docs/deslop-release-contracts.md`, `docs/deslop-locks-contracts.md` and
    `docs/deslop-coverage.md`, readable with `git show 8d7e873:PATH` from
    the canonical repository. The two accepted worktrees are retired after
    integration, idle-consumer and archive readback checks. Private raw evidence
    remains under canonical `.git/deslop-evidence/20261117/`.
  - **Resume order:** finish vault Tests and diff-pretty Tests directly, then
    their Dead code/Findings/Report steps. Fz is settled. Retain the owner-only
    hardware recovery and fleet-rollout boundaries below.
  - Mutation and coverage runs still take the shared host lock
    (`mkdir .work/tmp/mutation.lock` in stuff) and use `--timeout` at about 4x the baseline test
    phase.
  - Bounded local Python Scenarios now qualify module contracts while the
    whole-change lane stays open. Prefer a complete measured module when it
    fits the twenty-minute Scenario budget; do not restart manual Full runs.
    TypeScript mutation readiness and whole-change CI qualification remain
    separate gates. No workflow repairs occur without explicit authorization.
- **Find campaign PRs:** `gh search prs --label deslop --owner laputa-systems --owner joshuarli`.
- **Needs you:**
  1. toolbox: fix Actions billing to bring it back in scope.
  2. M2 requires review of the concrete calibration report before broader fleet dispatch.
  3. CI repairs require explicit authorization under the lean contract. The
     concrete pending request covers platform-aware bounded deslop mutation
     jobs and their whole-change selection and negative controls.
- **Resume prompt:** `Execute docs/campaigns/deslop.md from its Status. Follow its Charter.` After
  the dispatched batch, the next direct slices are loc's sharded lane under
  `cpu-guard` and the remaining calibration/pilot harness qualifications.
  Fleet fixer application waits for the prescribed qualification and M2 review.

## Repomod Diagnose and contemporaneous results

- **Current direct results (2026-11-17):** Extensions
  [#12](https://github.com/joshuarli/extensions/pull/12) qualifies the complete
  storage/state component: 112 killed and two equivalent reader guards across
  114 current identities, with 253 Node tests and lint passing. Pytest-parallel
  [#23](https://github.com/joshuarli/pytest-parallel/pull/23) rejects corrupt UTF-8
  worker reports; 152 tests, installed-wheel controls and all checks pass.
  Tm [#39](https://github.com/laputa-systems/tm/pull/39) repairs partial-output
  and asynchronous pane-exit fixtures without changing production. Stats
  [#18](https://github.com/joshuarli/stats/pull/18),
  [#19](https://github.com/joshuarli/stats/pull/19) and
  [#20](https://github.com/joshuarli/stats/pull/20) land the macOS sandbox repair,
  Diagnose and shutdown diagnostics. The intermittent shutdown cause remains
  unproven. Diff-pretty [#34](https://github.com/laputa-systems/diff-pretty/pull/34)
  repairs bare-control stripping with full tests and the recorded noisy-but-within-bound
  release workload checks. Their broader Tests and CI qualifications remain open.
  The repomod [component review](../deslop-repomod-diagnose.md) finds five P2 and
  two P3 defects; four separate runtime repairs are in stuff #51–54, with
  fail-before/pass-after controls and full repomod tests/lint. DSLP-6 records
  the remaining CI-policy finding. Assertion-only Loc and Onefile slices can
  integrate on green correctness checks while their broader Tests tickets stay
  open for quiet-host suite-cost qualification. Pytest worker-report assertions
  follow the same rule; no deferred qualification is counted as passed.

Four completed Extensions worktrees were also retired after private archive
  hash/readback checks, reclaiming 653,500 KiB (about 638 MiB). Their proof is
  preserved under that repository's `.git/deslop-evidence/20261117-completed-lanes/`.
