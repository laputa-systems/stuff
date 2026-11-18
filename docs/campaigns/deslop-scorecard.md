# Deslop scorecard

One row per in-scope repository for the [deslop campaign](deslop.md). The campaign agent fills each
row from the repo's `## Report` at check-up. Cells hold `before → after`. Coverage is recorded but
never gated.

## Current checkpoint, 2026-11-18

Default heads and active PRs were checked again on resumption. M2 remains open. Each Report refresh and remaining acceptance condition
is assigned in the [resumption roadmap](deslop-roadmap.md). Historical values
below retain their original scope. The owner has approved broader dispatch.
M2 and the tier checkpoints still require qualification evidence. Discover is
outside scope during the owner's rearchitecture.

| Repository | Default revision | Pass state and completed work | CI and retention | One next action |
| --- | --- | --- | --- | --- |
| srv | `c9965411d80a8b02d8b8c4cac2492ecc973ee296` | Complete earlier Report. Draft #47 exercises onefile dispatch, Mermaid labels and font types. It now includes the startup warning witness from #48. | The hosted run at `289a8fe` accounted for all 376 identities, with 322 caught, 25 missed, 17 unviable and 12 confirmed hangs. The four jobs took 3,541 runner seconds. | Review the updated sharded run and the ten-minute target |
| fz | `0ec537d53eca0a12af07687250111a48023ee8d3` | Complete Report through cumulative review | #43 passed and Stuff #65 registered retention. The two #44 jobs preserved all 439 identities and both passed within ten minutes. | Check up at the next tier checkpoint |
| buildlib | `1497970d9454a6a9875b1f201cbaad71fd92a010` | Ground, Diagnose, Types, Tests and dead-code evidence. #27 fixed a release manifest serialization defect found during cumulative review. | All 17 checks passed. Four controls demonstrated the expected results across the applicable jobs. Strict typing, mutation and coverage retention registered. | Check up on the retained guarantees at the next tier checkpoint |
| extensions | `10f6101eba8916aa0f4b4aed07d91f6178ff525b` | Active. Coverage, type-aware lint and installed Chromium are retained. Draft #22 covers parser and storage. #27 verifies ZIP metadata and CRC. | The parser and storage jobs passed in 617 aggregate runner seconds with four hosted controls. #27 caught 35 of 44 selected identities. | Qualify the remaining archive and browser effects |
| pytest-parallel | `c260153eed1e45d5ded531ed058629821520f007` | Active. #33 caught all 79 planner identities. #38 simplified worker-pin and worker-limit decisions and caught all 51 final identities. | Draft #32 passed ten hosted mutation jobs with the new pin scope. Four earlier controls passed their expected outcomes on both platforms. | Qualify the remaining coordinator and socket decisions |
| vault | `0e72b21112b840aa5b7fa373eeeab79e63ed59bb` | Active; Ground/Diagnose/Types and runtime repairs merged; Tests draft #30 at `0671858` | Ordinary CI green on macOS and both Linux musl architectures; Linux mutation has misses and exhausted shards | Diagnose Linux unit test cost, then verify the successor accounting and remaining decisions |
| diff-pretty | `ef8a276e40a990a52ff4354dc0ee7500d7757c38` | Active; Ground, Diagnose, Types, sanitizer repair and first Tests slice merged | #31 passed 15 checks and four hosted controls. Five interleaved suite pairs had equal medians. #40 passed the retained Make path on both platforms. Stuff #70 registered it. | Bound the remaining renderer and live terminal scopes |
| loc | `69275cc9a60f82269c5f690cc730cd79bffb6374` | Active. #22 covers marker and EOF boundaries. #23 verifies the interpreter and first-line classification. | All five hosted checks passed both. #22 caught 16 of 19, with two confirmed timeouts and one equivalent. #23 caught all five viable shebang identities. | Finish the critical inventory and hosted whole-change gate |
| stats | `9b8f0b30c99790b812f3bc18a5e84fe8dfad7dd9` | Active. #33 caught all 42 Rust ACK identities. #34 removed assertions in producer ACK decoding and recorded bridge typing findings. | All three hosted checks passed. The TypeScript wire ACK decoder caught 113 of 115 identities with two equivalents. Both wire implementations passed conformance. | Finish component-mode Types and Tests |
| stuff, repomod | `2940843c7b7e5a2e5cd036925fa45127cf2b1a35` | Active. Types complete. #85 covers checkout refusal precedence. #88, #90 and #91 removed the unused role, catalog and audit paths. | All ten checks passed #91. The local suite passed 1,481 tests with three opt-in skips. The removal table caught all 19 identities on unchanged source. | Qualify the whole-change trial and complete the cumulative review |
| fastermod | `1468b653a0f140d9dd68d946e5473db6523148a6` | Active. Ground, Diagnose and Types complete. #31 fixed terminal plan routing, #32 repaired source diagnostics and #34 verifies the source warning. | Hosted CI and lint passed. Five paired runs accepted #32 across seven workloads. #34 caught all seven viable source identities. | Bound and qualify the Tests step |
| ptytest | `24bf3904d8acb7dedfd6f74fdde0ebd476feda47` | Active. #23 covers continuous-output deadlines and #24 verifies nonconstant cursor replies. | Hosted Linux and macOS passed. #23 caught 13 of 18 deadline identities and #24 caught 13 of 18 terminal identities. Five in each scope were unviable. The same macOS Xsh compile failure occurred at baseline and with the candidate. | Qualify the remaining I/O and consumer Tests inventory |
| tm | `6cf0b949c2593c0959268a3d1995b972b05f58b6` | Active; fixture repairs merged, Ground and later stages open | Recent repair CI green; quiet-host cost unresolved | Finish Ground cost and component scope |
| toolbox | `8d2cd08c71ff00d311212d85940f95c8359aa76f` | Deferred; historical partial calibration only | The third lint attempt on `8ca3dd59` stopped before any step. The installed-wheel comparison reproduced the baseline FFmpeg failure. | Reopen after Actions recovery and bring positive FFmpeg and fio execution evidence |

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
