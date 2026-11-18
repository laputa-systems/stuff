# Deslop scorecard

One row per in-scope repository for the [deslop campaign](deslop.md). The campaign agent fills each
row from the repo's `## Report` at check-up. Cells hold `before → after`. Coverage is recorded but
never gated.

## Current checkpoint, 2026-11-17

Default heads and active PRs were checked again on resumption. M2 remains open. Each Report refresh and remaining acceptance condition
is assigned in the [resumption roadmap](deslop-roadmap.md). Historical values
below retain their original scope. The owner has approved broader dispatch.
M2 and the tier checkpoints still require qualification evidence. Discover is
outside scope during the owner's rearchitecture.

| Repository | Default revision | Pass state and completed work | CI and retention | One next action |
| --- | --- | --- | --- | --- |
| srv | `c9965411d80a8b02d8b8c4cac2492ecc973ee296` | Complete pass Report at the earlier head. #47 checks onefile dispatch and Mermaid label geometry. | Ordinary checks passed. Four hosted shards accounted for 376 identities, with 308 caught, 27 missed, 16 unviable and 25 provisional timeouts. | Resolve survivors and apply the tested singleton rerun before qualifying #47 |
| fz | `0ec537d53eca0a12af07687250111a48023ee8d3` | Complete Report through cumulative review | #43 passed and Stuff #65 registered retention. The two #44 jobs preserved all 439 identities and both passed within ten minutes. | Check up at the next tier checkpoint |
| buildlib | `1497970d9454a6a9875b1f201cbaad71fd92a010` | Ground, Diagnose, Types, Tests and dead-code evidence. #27 fixed a release manifest serialization defect found during cumulative review. | All 17 checks passed. Four controls demonstrated the expected results across the applicable jobs. Strict typing, mutation and coverage retention registered. | Check up on the retained guarantees at the next tier checkpoint |
| extensions | `97363237bff4e669196f48b90068e431fc0a7eff` | Active. Type-aware lint, Node coverage, installed MV3 and nine Onefile browser cases merged. #19 adds bookmark folder and timeline parser checks. | Node checks and Linux Chromium passed. The coverage target is registered. The bounded parser selection caught 167 of 179 at #19, up from 139. | Qualify TypeScript whole-change mutation and the remaining retention checks |
| pytest-parallel | `e54d5b2fd9ff6b29bb53dbac9b658ced61d1f8e8` | Active. Ground, Diagnose, Types and worker coverage merged. #26 fixed empty-address binds. #27 completed the report-emission scenario with 60 of 60 caught. #28 catches the remaining observable reader survivor. | #26–28 passed lint and Linux/macOS tests. Installed-wheel consumer runs passed in Stuff and reproduced a baseline FFmpeg failure in Toolbox. Whole-change retention unfinished. | Bound the remaining Tests inventory and qualify the serial gate |
| vault | `0e72b21112b840aa5b7fa373eeeab79e63ed59bb` | Active; Ground/Diagnose/Types and runtime repairs merged; Tests draft #30 at `0671858` | Ordinary CI green on macOS and both Linux musl architectures; Linux mutation has misses and exhausted shards | Diagnose Linux unit test cost, then verify the successor accounting and remaining decisions |
| diff-pretty | `ef8a276e40a990a52ff4354dc0ee7500d7757c38` | Active; Ground, Diagnose, Types, sanitizer repair and first Tests slice merged | #31 passed 15 checks and four hosted controls. Five interleaved suite pairs had equal medians. #40 passed the retained Make path on both platforms. Stuff #70 registered it. | Bound the remaining renderer and live terminal scopes |
| loc | `b45c6f2eda622f3e3b538e824e2cf47a8c818fdf` | Active. #19 caught both former timeouts with the child deadline. #20 exercised Linux XDG config precedence and fallback. | Lint, macOS, both Linux musl jobs and LineJudge passed #20. Mutation retention remains open. | Finish the existing critical inventory and cost and CI requirements |
| stats | `da022e8b867cb1d15e2de9dc1120e58a8d71e89f` | Active. Legacy migration, dev port admission and shutdown, shared ACK corpus and Rust wire type evidence merged. | All three hosted checks passed #29. Both decoders reject a valid repeated-sequence acknowledgment under the counting fault control. | Finish component-mode Types and Tests |
| stuff, repomod | `981f3de0ae5b0c5f33e314b9483b4e4f61b53d7f` | Active. Types and dead-code review complete. #74, #77 and #78 establish snapshot cache recovery and filtered index contracts. | All ten checks passed on #78. The snapshot scenario caught 110 of 123 and all six targeted survivors on rerun. | Exercise the platform-specific controls and qualify the whole-change union |
| fastermod | `181697963fe51229f3f1d76c0beb5f3ce8aae3ff` | Active. Ground, Diagnose and Types complete. #31 fixed terminal plan routing. #32 is the text source read-error candidate. | Hosted tests and lint passed for #30–33. #32 needs the paired workload on a quiet host. | Qualify the remaining P2 repair and bound Tests |
| ptytest | `6a31b119629da3e902911222ad00393a6f9d9536` | Active. Ground, Diagnose and Types complete. #15 fixed a diagnostic overwrite during Drop. #19 repaired flood fixture readiness. | Linux and macOS PTY acceptance and lint passed. All 67 instrumented tests passed after #19. Stuff #76 registered the coverage target. | Bound the remaining Tests inventory |
| tm | `6cf0b949c2593c0959268a3d1995b972b05f58b6` | Active; fixture repairs merged, Ground and later stages open | Recent repair CI green; quiet-host cost unresolved | Finish Ground cost and component scope |
| toolbox | `8d2cd08c71ff00d311212d85940f95c8359aa76f` | Deferred; historical partial calibration only | The lint retry on the calibration branch at `8ca3dd59` stopped before any step. The installed-wheel comparison reproduced the baseline FFmpeg failure. | Reopen after Actions recovery and bring positive FFmpeg and fio execution evidence |

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
