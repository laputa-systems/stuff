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
| extensions | `cc3ee46d95ccd661683e963516157ff581002aea` | Active. The owning Tests report records the type-aware lint, installed MV3, coverage and parser work. | #20 caught 178 of 179 parser identities with one equivalent. Node and Chromium passed. | Qualify TypeScript whole-change mutation and the remaining retention checks |
| pytest-parallel | `8197c5937eedcf29ba04ca086cf8ad3b65358909` | Active. #30 qualifies option parsing, and #31 adds coordinator file-hook checks and removes an unreachable guard. | Linux, macOS and lint passed #31. Draft #32 passed standalone options and scheduling shards. The aggregate exhausted its budget in coordinator. | Resolve remaining coordinator decisions and qualify the complete workflow |
| vault | `0e72b21112b840aa5b7fa373eeeab79e63ed59bb` | Active; Ground/Diagnose/Types and runtime repairs merged; Tests draft #30 at `0671858` | Ordinary CI green on macOS and both Linux musl architectures; Linux mutation has misses and exhausted shards | Diagnose Linux unit test cost, then verify the successor accounting and remaining decisions |
| diff-pretty | `ef8a276e40a990a52ff4354dc0ee7500d7757c38` | Active; Ground, Diagnose, Types, sanitizer repair and first Tests slice merged | #31 passed 15 checks and four hosted controls. Five interleaved suite pairs had equal medians. #40 passed the retained Make path on both platforms. Stuff #70 registered it. | Bound the remaining renderer and live terminal scopes |
| loc | `b8164de5fa9f682917445c152085e889cb2a3606` | Active. #21 records the remaining Tests paths after CLI deadline and config precedence coverage. | Lint, macOS, both Linux musl jobs and LineJudge passed. Mutation retention remains open. | Finish the existing critical inventory and cost and CI requirements |
| stats | `37a857bc525d6db0ac9e87de6f07535e0886dd20` | Active. Ingest coverage, the runtime target-policy fixture repair and shared ACK boundary cases merged in #30–32. | All three hosted checks passed #32. The TypeScript ACK decoder caught 113 of 115 identities with two equivalents. Both implementations passed conformance. | Finish component-mode Types and Tests |
| stuff, repomod | `4eabeae6` | Active. Types complete. #75 removed two unused items. #79–81 consolidate snapshot evidence and owning Tests and Dead code scope. | All ten checks passed on #81. The snapshot scenario caught 110 of 123, six more on a targeted rerun and two filename mutants on a case-sensitive filesystem. | Qualify the whole-change union and finish the Dead code step |
| fastermod | `181697963fe51229f3f1d76c0beb5f3ce8aae3ff` | Active. Ground, Diagnose and Types complete. #31 fixed terminal plan routing. #32 is the text source read-error candidate. | Hosted tests and lint passed for #30–33. #32 needs the paired workload on a quiet host. | Qualify the remaining P2 repair and bound Tests |
| ptytest | `d60bf6dc5a3dcd401067c3220b5e4d7153c3c9b8` | Active. #21 removed two redundant deadline checks and caught all four remaining output-wait mutations. #22 records the Tests boundary. | Hosted Linux and macOS passed. Focused lz, e and ish consumers passed with the candidate. The macOS Xsh compile failure reproduced before and after it. | Qualify the remaining I/O and consumer Tests inventory |
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
| extensions | `cc3ee46d95ccd661683e963516157ff581002aea` | Active. The owning Tests report records the type-aware lint, installed MV3, coverage and parser work. | #20 caught 178 of 179 parser identities with one equivalent. Node and Chromium passed. | Qualify TypeScript whole-change mutation and the remaining retention checks |
| fastermod | Calibration |  |  |  |  |  |  |  |  |  |  |  |  |
| pytest-parallel | `8197c5937eedcf29ba04ca086cf8ad3b65358909` | Active. #30 qualifies option parsing, and #31 adds coordinator file-hook checks and removes an unreachable guard. | Linux, macOS and lint passed #31. Draft #32 passed standalone options and scheduling shards. The aggregate exhausted its budget in coordinator. | Resolve remaining coordinator decisions and qualify the complete workflow |
| ptytest | `d60bf6dc5a3dcd401067c3220b5e4d7153c3c9b8` | Active. #21 removed two redundant deadline checks and caught all four remaining output-wait mutations. #22 records the Tests boundary. | Hosted Linux and macOS passed. Focused lz, e and ish consumers passed with the candidate. The macOS Xsh compile failure reproduced before and after it. | Qualify the remaining I/O and consumer Tests inventory |
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
| loc | `b8164de5fa9f682917445c152085e889cb2a3606` | Active. #21 records the remaining Tests paths after CLI deadline and config precedence coverage. | Lint, macOS, both Linux musl jobs and LineJudge passed. Mutation retention remains open. | Finish the existing critical inventory and cost and CI requirements |
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
| stats | `37a857bc525d6db0ac9e87de6f07535e0886dd20` | Active. Ingest coverage, the runtime target-policy fixture repair and shared ACK boundary cases merged in #30–32. | All three hosted checks passed #32. The TypeScript ACK decoder caught 113 of 115 identities with two equivalents. Both implementations passed conformance. | Finish component-mode Types and Tests |
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
