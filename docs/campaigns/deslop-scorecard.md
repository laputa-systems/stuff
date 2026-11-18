# Deslop scorecard

One row per in-scope repository for the [deslop campaign](deslop.md). The campaign agent fills each
row from the repo's `## Report` at check-up. Cells hold `before → after`. Coverage is recorded but
never gated.

## Current checkpoint, 2026-11-18

M2 qualified representative workloads with explicit deferrals. Tier A repo passes
have started. The [resumption roadmap](deslop-roadmap.md) records the remaining
acceptance conditions. Historical values below retain their original scope.
Later tier checkpoints still require qualification evidence. Discover is
outside scope during the owner's rearchitecture.

| Repository | Default revision | Pass state and completed work | CI and retention | One next action |
| --- | --- | --- | --- | --- |
| srv | `c9965411d80a8b02d8b8c4cac2492ecc973ee296` | The #47 sharded candidate includes the archive startup warning. Earlier Report complete. | All 376 identities accounted for twice. The latest run caught 323, missed 24, found 17 unviable and confirmed 12 hangs. Its gate median was 850.3 seconds. | Resolve misses and qualify the ten-minute target |
| fz | `091617def63fbf364afea068513a2b5dfa748720` | Earlier Report complete. Local check-up passed 66 Rust cases and caught an injected CLI success exit. #46 records the current release comparison as deferred in DSLP-10. | Both default checks passed. #44 preserved 439 mutation identities across two jobs. The third hosted timing attempt exited 75 at its readiness check after sampling started. | Repeat the paired runtime workload on a quiet host |
| buildlib | `1497970d9454a6a9875b1f201cbaad71fd92a010` | Ground through Dead code and cumulative review complete. Fresh check-up passed all 208 tests and reproduced the manifest filename mismatch with an injected fault. | All 17 checks passed #27. Default CI and lint passed. Test workflow, mutation, coverage and strict typing policy checks returned no findings. | Retain the checked guarantees |
| extensions | `10f6101eba8916aa0f4b4aed07d91f6178ff525b` | Active. Coverage, type-aware lint and installed Chromium are retained. Draft #22 covers parser and storage. #27 verifies ZIP metadata and CRC. | The parser and storage jobs passed in 617 aggregate runner seconds with four hosted controls. #27 caught 35 of 44 selected identities. | Qualify the remaining archive and browser effects |
| pytest-parallel | `25e57a1e460d030fab8385c48657ef672a7f2d1c` | Active. #39 preserves native subtest reports. #40 verifies report validation and removes redundant state operations. | All 207 local tests and three hosted checks passed #40. Draft #32 caught all 105 report identities in both lanes, with twelve passing jobs and 907 total runner seconds. | Qualify the remaining coordinator lifecycle and socket decisions |
| vault | `553fb720046e360cd9f62beeaef007ad398978db` | Active. #36 records the platform trial and defers two-Mac recovery to an owner-run check. | Ordinary draft CI passed macOS and both Linux musl architectures. Mutation failed on 14 Linux and 13 macOS shards. | Qualify the platform union and obtain the separate hardware and keyring evidence |
| diff-pretty | `9ce6235e70a3ad9d2174912a9808730dcc27f651` | Active. #41 adds workspace branch coverage. #42 and #43 cover SIGTERM, terminal keys, EOF, raw modes and restored handlers. #44 covers session finish and scroll clamping. | All 15 checks passed on each PR. The #43 local suite passed 94 tests and one doctest. The two focused audits caught 22 of 23 terminal identities and two of two session identities. Stuff #70 retains the mutation workflow. | Bound wider live-loop and renderer mutation and paired cost |
| loc | `341cbeef5a07088ff33153d0244db01443178c02` | Active. #24 retained the shebang gate. #29 routes normal CI through Make. | #29 passed all eight checks. The mixed control counted the same 25 identities on macOS and both musl targets. Stuff #107 registered retention. | Finish broader SIMD and file-selection Tests |
| stats | `ec5993b6f02644cbc18f4fc0706fae21a0d37b63` | Active. #36 exercises mixed binary ACKs through Workerd. Draft #37 runs Workerd and Rust. | Ordinary #36 checks passed. #37 caught all 42 Rust identities and 25 Workerd identities with two equivalents in 322 runner seconds. | Finish component coverage and the producer timeout dispositions |
| stuff, repomod | `17845f5237d045838ba8678e1b795e4256cae139` | Active. Types and Dead code complete through #98. #103 verifies fixer push diagnostics. | Draft #92 passed ten jobs across five scopes, accounting for 252 identities per platform in 740 runner seconds. #103 caught 121 of 127, with six equivalents. | Qualify the wider inventory and whole-file fallback |
| fastermod | `d99400a71800b2be31b0f1f95a832147d1c00125` | Active. #36 verifies the saved-plan read set. #37 retained text source mutation, and #42 classifies every pull request. | All ordinary checks and both retained mutation jobs passed. Four hosted controls qualify the source scope. Earlier paired acceptance covered all seven performance workloads. | Qualify terminal review and wider saved-plan mutation |
| ptytest | `606027bb32999fa3e1bb960285384a89081a957a` | Active. #25 retained the terminal mutation scope. #30 makes the workflow classify each pull request. | Both platforms and four controls confirmed the bounded selection. The same macOS Xsh compile failure occurred at baseline and with the candidate. | Qualify lifecycle, replay and remaining consumer Tests inventory |
| tm | `6cf0b949c2593c0959268a3d1995b972b05f58b6` | Active; fixture repairs merged, Ground and later stages open | Recent repair CI green; quiet-host cost unresolved | Finish Ground cost and component scope |
| toolbox | `8d2cd08c71ff00d311212d85940f95c8359aa76f` | Local native and coverage evidence complete on #15. Hosted qualification deferred for Actions billing. | The repaired installed wheel passed all 750 tests and five native fio subtests. Separate branch data exists for both workers. | Resume hosted checks when Actions can start the jobs |
| ffmpeg-build | `0de54ca9a1dbe17f393912ea4774a71363c1c8ce` | Ground, Diagnose and Types complete. #35 records all ten native artifact checks. #38 rejects malformed stage records and #39 exercises the shared audit against fixture files. | 118 ordinary tests and lint passed. The shared audit selected all 696 exact identities and caught 376, with 320 surviving. | Qualify whole-change coverage |
| pi-build | `266f21b5c010ed1775a7698db0dd72e9f53b14d4` | Both artifact profiles reproduced on Linux x86-64 and ARM64. #42 retains the whole-change Python gate, #43 fixes vendor rollback, and #44 records two-host Intercom as an owner-environment dependency. | Default CI and lint passed. #43 ran 77 Python tests, four companion fixtures and accounted for 1,434 mutation identities. | Obtain two-host Intercom evidence before settling the pass |
| node-build | `ff3448ff2264decfdbb38a8e9ba3c7037f5394fc` | Ground, Diagnose and Types complete. #36 verifies malformed lock fields. #38 records native qualification for Node 26.12.1. #39 validates byte ceilings. | All 52 Doctor identities and 78 of 81 archive budget identities were caught. Native x86-64 musl and macOS ARM64 each passed 18 smoke cases and both size budgets. Default CI and lint passed. | Qualify wider controller mutation and the whole-change gate |
| hi-lite | `e91982b29261e89218b92d738de1fe8e3b524964` | Ground, Diagnose and Types complete. #19 pins the XSH vocabulary. #20 fixes full-range diff previews. #21 covers wider diff behavior. | Both ordinary platforms and lint passed. The native ARM64 diff trial passed with equal allocations. The diff census and survivor rerun caught 137 of 148 identities. | Qualify lexer coverage, allocation-only cases and the whole-change gate |
| doas-rs | `af1b7d4e91750b3748d226835197ae6118aff5d2` | Ground, Diagnose and Types complete. #13 reports failed approval clears. #14 removed nine unwraps and #15 retains branch coverage. | The stable-builder suite passed 166 tests. The coverage run measured 3,113 of 4,323 lines and 500 of 1,006 branches. Native x86-64 KVM passed all four installed-operation markers. | Qualify critical mutation scopes, live password entry and ARM64 guest effects |
| mdevd-rs | `0405d2df21b646d787ba6846753e980d2d5312b7` | Ground, Diagnose and Types complete. Native guest and consumer evidence landed. #24 fixes malformed arguments and #25 adds sysfs decision cases. | Default CI passed. The matched 44-identity engine audit caught 40. The native ARM64 fixture verified both CLI entry points. | Resolve remaining mutations and verify physical coldplug |
| cmake-build | `a645b17bf4b25ef500b99f53ddc439cf4041b9cb` | Ground, Diagnose and Types complete. #41 records sealed controller coverage and #42 verifies bootstrap metadata. | The sealed run passed 137 cases across 21 modules. The matched bootstrap parser scope caught 99 of 99 identities, up from 81. Both stable archives passed native qualification. | Obtain the compatible mirrored coverage wheel and qualify the whole-change checks |


Fz check-up at `0ec537d53eca0a12af07687250111a48023ee8d3` used a fresh macOS ARM64 worktree, the
repo's pinned nightly, fzy commit `34b88869d022e861da4846c4463aea3ddfb3ff30`,
`CARGO_BUILD_JOBS=2`, `RUST_TEST_THREADS=2`, kache, and
`cpu-guard --cores 3 -- make test`. Cold and warm attempts took 21.15 and
14.82 seconds. `make lint` took 3.31 seconds. For the CLI control, change
the parse-error exit from 1 to 0 in `src/cli.rs` and run
`cargo test --locked --test cli invalid_lines_and_positional_arguments_fail_without_stdout -- --exact`.
It exits 101 with 0 observed where 1 is expected. Reverting the fault restores
the pass. Local release timings overlapped a CPU-intensive workload. The last
hosted attempt failed its readiness check after sampling had started.
[Hosted attempt](https://github.com/laputa-systems/fz/actions/runs/44348670074) ·
[DSLP-10](https://github.com/laputa-systems/fz/pull/46)

The Buildlib check-up at `1497970d` measured 901 of 902 Python statements and
291 of 292 branches. In a disposable copy, removing `manifest = dict(manifest)`
from `write_manifest` made
`pytest tests/test_release.py::test_manifest_name_and_body_use_the_same_product`
fail on the filename. Restoring the snapshot restored the test. The suite
timing overlapped another workload and was discarded. Buildlib does not
declare a runtime performance workload.

## Historical measurements

The following table preserves earlier observations, including unreconciled
whole-package mutation totals. Empty cells and seeded rows are not evidence
of completion. Refresh measurements only when changed inputs or a named risk
invalidate their existing receipts.

| Repo | Tier | Base | Settled | Src lines | Test lines | Warm test | Line/branch cov | Mutants c/m/u/t | Escape hatches | Dead removed | Findings P1-P2 filed/fixed | Perf | Escapes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| srv | Pilot | dcc7921 | 2026-11-15 | 1,020 → 1,058 | 29 → 182 (`tests/`) | <1s → 0.4s | 89.5/66.8% → 95.5/87.9% | 162/61/8/8 → 192/0/8/12 | 3 → 0 | 1 helper, 1 guard, 1 separator rewrite | 4/4 P2 | none (no workload) | 0 product; 1 process (#29 merged on a red lane, fixed by #30) |
| buildlib | Pilot | 6ef86b9 | no (DSLP-4 open) |  |  | 6s → 5.5s |  | mutmut 1437/235/0/0 → 1456/216/0/0 | 16 → 11 | none (vulture over consumers clean) | 0/0 P2; P3 DSLP-6, -7, -8 fixed | none (no workload) | 0 |
| extensions | Pilot |  |  |  |  |  |  |  |  |  |  |  |  |
| fastermod | Calibration |  |  |  |  |  |  |  |  |  |  |  |  |
| pytest-parallel | Calibration |  |  |  |  |  |  |  |  |  |  |  |  |
| ptytest | Calibration |  |  |  |  |  |  |  |  |  |  |  |  |
| pi-build | A |  |  |  |  |  |  |  |  |  |  |  |  |
| ffmpeg-build | A |  |  |  |  |  |  |  |  |  |  |  |  |
| node-build | A |  |  |  |  |  |  |  |  |  |  |  |  |
| fz | A |  |  |  |  |  |  |  |  |  |  |  |  |
| doas-rs | A |  |  |  |  |  |  |  |  |  |  |  |  |
| mdevd-rs | A |  |  |  |  |  |  |  |  |  |  |  |  |
| diff-pretty | A |  |  |  |  |  |  |  |  |  |  |  |  |
| vault | A |  |  |  |  |  |  |  |  |  |  |  |  |
| cmake-build | A |  |  |  |  |  |  |  |  |  |  |  |  |
| hi-lite | A |  |  |  |  |  |  |  |  |  |  |  |  |
| lz | B |  |  |  |  |  |  |  |  |  |  |  |  |
| rustybench | B |  |  |  |  |  |  |  |  |  |  |  |  |
| loc | Calibration | e533792 | no |  |  | 2s (13s cold) | 93.0/84.5% (calibration) | 2,433 mutants listed |  |  |  | rustybench baseline |  |
| laputa-ui-dashboard | B |  |  |  |  |  |  |  |  |  |  |  |  |
| tinyland | B |  |  |  |  |  |  |  |  |  |  |  |  |
| chromium-build | B |  |  |  |  |  |  |  |  |  |  |  |  |
| toolbox | Calibration | fcc8ec6 | no |  |  | 24s (parallel) | 68% line+branch, serial run (calibration) |  |  |  |  |  |  |
| e | B |  |  |  |  |  |  |  |  |  |  |  |  |
| defuddle-rs | B |  |  |  |  |  |  |  |  |  |  |  |  |
| gluon | B |  |  |  |  |  |  |  |  |  |  |  |  |
| ctrs | C |  |  |  |  |  |  |  |  |  |  |  |  |
| usr | C |  |  |  |  |  |  |  |  |  |  |  |  |
| img | C |  |  |  |  |  |  |  |  |  |  |  |  |
| tm | C |  |  |  |  |  |  |  |  |  |  |  |  |
| stats | Calibration |  |  |  |  |  |  |  |  |  |  |  |  |
| ish | D |  |  |  |  |  |  |  |  |  |  |  |  |
| smolith | D |  |  |  |  |  |  |  |  |  |  |  |  |
| play | D |  |  |  |  |  |  |  |  |  |  |  |  |
| tansu | D |  |  |  |  |  |  |  |  |  |  |  |  |
| stuff (repomod) | Calibration | | | | | | | | | | | | |
| stuff (rest) | D |  |  |  |  |  |  |  |  |  |  |  |  |
| kache | D |  |  |  |  |  |  |  |  |  |  |  |  |
| jaq | E |  |  |  |  |  |  |  |  |  |  |  |  |
| rust-fontconfig | E |  |  |  |  |  |  |  |  |  |  |  |  |
| rustix | E |  |  |  |  |  |  |  |  |  |  |  |  |
| rage | E |  |  |  |  |  |  |  |  |  |  |  |  |
| fd | E |  |  |  |  |  |  |  |  |  |  |  |  |
| oxish | E |  |  |  |  |  |  |  |  |  |  |  |  |
| crabtables | E |  |  |  |  |  |  |  |  |  |  |  |  |
| soulseek-rs | E |  |  |  |  |  |  |  |  |  |  |  |  |
