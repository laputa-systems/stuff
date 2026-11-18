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
| fz | `0ec537d53eca0a12af07687250111a48023ee8d3` | Report complete. Local check-up passed 66 Rust test cases twice and lint. A nested Linux-only PTY case was skipped on macOS. The CLI invalid-argument test caught an injected success exit. | F2/F3 and both retention rules passed. The hosted default run passed on rerun after the macOS harness missed its timing window. #44 preserved 439 mutation identities across two jobs. | Repeat the paired runtime workload on a quiet host |
| buildlib | `1497970d9454a6a9875b1f201cbaad71fd92a010` | Ground, Diagnose, Types, Tests and dead-code evidence. #27 fixed a release manifest serialization defect found during cumulative review. | All 17 checks passed. Four controls demonstrated the expected results across the applicable jobs. Strict typing, mutation and coverage retention registered. | Check up on the retained guarantees at the next tier checkpoint |
| extensions | `10f6101eba8916aa0f4b4aed07d91f6178ff525b` | Active. Coverage, type-aware lint and installed Chromium are retained. Draft #22 covers parser and storage. #27 verifies ZIP metadata and CRC. | The parser and storage jobs passed in 617 aggregate runner seconds with four hosted controls. #27 caught 35 of 44 selected identities. | Qualify the remaining archive and browser effects |
| pytest-parallel | `25e57a1e460d030fab8385c48657ef672a7f2d1c` | Active. #39 preserves native subtest reports. #40 verifies report validation and removes redundant state operations. | All 207 local tests and three hosted checks passed #40. Draft #32 caught all 105 report identities in both lanes, with twelve passing jobs and 907 total runner seconds. | Qualify the remaining coordinator lifecycle and socket decisions |
| vault | `553fb720046e360cd9f62beeaef007ad398978db` | Active. #36 records the platform trial and defers two-Mac recovery to an owner-run check. | Ordinary draft CI passed macOS and both Linux musl architectures. Mutation failed on 14 Linux and 13 macOS shards. | Qualify the platform union and obtain the separate hardware and keyring evidence |
| diff-pretty | `b8a47c93a7664c51348fba7f9bdb1605affe8ff1` | Active. #41 adds the workspace branch coverage command. Native coverage passed 88 tests and one doctest. | All 15 checks passed #41. Stuff #70 retains the mutation workflow. | Bound the remaining renderer and live terminal scopes |
| loc | `341cbeef5a07088ff33153d0244db01443178c02` | Active. #24 retained the shebang gate. #29 routes normal CI through Make. | #29 passed all eight checks. The mixed control counted the same 25 identities on macOS and both musl targets. Stuff #107 registered retention. | Finish broader SIMD and file-selection Tests |
| stats | `ec5993b6f02644cbc18f4fc0706fae21a0d37b63` | Active. #36 exercises mixed binary ACKs through Workerd. Draft #37 runs Workerd and Rust. | Ordinary #36 checks passed. #37 caught all 42 Rust identities and 25 Workerd identities with two equivalents in 322 runner seconds. | Finish component coverage and the producer timeout dispositions |
| stuff, repomod | `17845f5237d045838ba8678e1b795e4256cae139` | Active. Types and Dead code complete through #98. #103 verifies fixer push diagnostics. | Draft #92 passed ten jobs across five scopes, accounting for 252 identities per platform in 740 runner seconds. #103 caught 121 of 127, with six equivalents. | Qualify the wider inventory and whole-file fallback |
| fastermod | `d99400a71800b2be31b0f1f95a832147d1c00125` | Active. #36 verifies the saved-plan read set. #37 retained text source mutation, and #42 classifies every pull request. | All ordinary checks and both retained mutation jobs passed. Four hosted controls qualify the source scope. Earlier paired acceptance covered all seven performance workloads. | Qualify terminal review and wider saved-plan mutation |
| ptytest | `606027bb32999fa3e1bb960285384a89081a957a` | Active. #25 retained the terminal mutation scope. #30 makes the workflow classify each pull request. | Both platforms and four controls confirmed the bounded selection. The same macOS Xsh compile failure occurred at baseline and with the candidate. | Qualify lifecycle, replay and remaining consumer Tests inventory |
| tm | `6cf0b949c2593c0959268a3d1995b972b05f58b6` | Active; fixture repairs merged, Ground and later stages open | Recent repair CI green; quiet-host cost unresolved | Finish Ground cost and component scope |
| toolbox | `8d2cd08c71ff00d311212d85940f95c8359aa76f` | Local native and coverage evidence complete on #15. Hosted qualification deferred for Actions billing. | The repaired installed wheel passed all 750 tests and five native fio subtests. Separate branch data exists for both workers. | Resume hosted checks when Actions can start the jobs |
| ffmpeg-build | `d1b6ee5bc264510f5847c1923fafc5f969db8ac1` | Ground, Diagnose and Types complete. Native x86-64 Linux runtime passed all 55 media workflows plus the shared-library consumer. | 112 ordinary tests and both default checks passed. Linux caught all 75 bootstrap and 152 of 155 collector identities with three equivalents. | Finish the other profiles and targets, then qualify whole-change coverage |
| pi-build | `0a4a78ed399a5c0d51e34e3805d2c4d5314d9f9b` | Both artifact profiles reproduced on Linux x86-64 and ARM64. #35 rejects mislabeled and duplicate companion packages. #36 adds the whole vendor controller proof. | #36 passed 74 Python tests, four companion fixtures and lint. Vendor caught 537 of 545 on macOS, with one exact Linux control and seven scoped equivalents. The archive trial detected a deletion in an actual mixed pull request. | Qualify the remaining whole-change and first-party shell and JS boundaries, and obtain two-host Intercom evidence |
| node-build | `597add72e9b3ea144819bc751876f1b221f30c97` | Ground, Diagnose and Types complete. #35 validates toolchain lock sections before host inspection, and #36 checks missing fields and schema errors. | 103 pinned Alpine tests and both default checks passed. All 52 Doctor identities and the assembly casefold fault were caught. Native artifact checks started in draft #37. | Qualify the wider controller and whole-change gate |
| hi-lite | `9ede5ab2cb27429b3d2b327dec7627a068273b0c` | Ground complete. #14 confirms the published install example with a fresh consumer. Diagnose filed the empty-input delimiter panic and continues. | All three #14 checks passed. 133 local tests and Clippy passed. | Complete the remaining lexer and fixture-tool review |
| doas-rs | `600023d11a6ca43b5341aaf10c4d9608f69a8d1c` | Ground complete. #6 verifies the public query outcomes and owned-tool help boundary. | Ordinary Linux and default checks passed. | Finish Diagnose and qualify the isolated privileged path |
| mdevd-rs | `dd4d59a5a0eb7a38aac973630f60ac768de0e03d` | Ground complete. #8 makes live publication exchange tests explicit and removes an unasserted smoke. | 64 ordinary tests passed with ten opt-in cases ignored. Both #8 checks and the default check passed. | Finish Diagnose and qualify the isolated guest and consumer exchange |
| cmake-build | `54ba25ecfa70efb36e82087fc4981038f5d32a70` | Ground complete. #18 rejects malformed RSS samples with the controller's budget diagnostic. The strict inventory fell from 65 to 44. | All 117 prepared Linux controller tests and lint passed on #18. The default controller job is running. | Finish Diagnose and the remaining strict typing work |


Fz check-up at the recorded revision used a fresh macOS ARM64 worktree, the
repo's pinned nightly, fzy commit `34b88869d022e861da4846c4463aea3ddfb3ff30`,
`CARGO_BUILD_JOBS=2`, `RUST_TEST_THREADS=2`, kache, and
`cpu-guard --cores 3 -- make test`. Cold and warm attempts took 21.15 and
14.82 seconds. `make lint` took 3.31 seconds. For the CLI control, change
the parse-error exit from 1 to 0 in `src/cli.rs` and run
`cargo test --locked --test cli invalid_lines_and_positional_arguments_fail_without_stdout -- --exact`.
It exits 101 with 0 observed where 1 is expected. Reverting the fault restores
the pass. The host's swap exceeds the performance preflight ceiling. Resume
the paired runtime gate when `perf-gate-ready` passes.

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
