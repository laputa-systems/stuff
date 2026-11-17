# Deslop scorecard

One row per in-scope repository for the [deslop campaign](deslop.md). The campaign agent fills each
row from the repo's `## Report` at check-up. Cells hold `before → after`. Coverage is recorded but
never gated.

## Current checkpoint, 2026-11-17

Default heads and active PRs were checked again on resumption. M2 remains open. Each Report refresh and remaining acceptance condition
is assigned in the [resumption roadmap](deslop-roadmap.md). Historical values
below do not override these states. Broader tiers are outside the current
dispatch authorization until M2 approval, while remaining in the full-fleet goal.

| Repository | Default revision | Pass state and completed work | CI and retention | One next action |
| --- | --- | --- | --- | --- |
| srv | `c9965411d80a8b02d8b8c4cac2492ecc973ee296` | Complete pass Report at the earlier head; default now includes onefile serving | Default lint passed; the direct onefile change has no hosted test or mutation receipt | Check the changed paths against retained guarantees and runner cost |
| fz | `eebed611362d5d2b9b1e430633fbf0ab86be23e0` | Complete Report through cumulative review | Default CI green; retained-policy eligibility needs check-up | Verify retained checks survive removal of the campaign TODO |
| buildlib | `890b5bd088a0b71f3436a6da1b2265a5a88720e7` | Active. Ground, Diagnose, Types, dead-code scan and host diagnostic witness merged | Strict profile registered. Mixed control reopened four release survivors on both Linux architectures. Full hosted qualification remains open | Re-run the whole-change matrix and controls with #22 |
| extensions | `1471899618d3cad9dde7ea7b5f3d4bfc5c73d2c6` | Active; Node, archive/recovery/storage and installed MV3 witnesses merged | #15–16 passed Node with type-aware lint and the Linux installed Chromium job | Complete retention proof and the TypeScript whole-change gate |
| pytest-parallel | `c07dceb0a5e52971ac9cb6512eaa6e475d687fee` | Active. Ground, Diagnose, Types, worker coverage and scheduling, event, report and network witnesses merged. #26 fixed empty-address listener binds. | #26 passed lint and Linux/macOS tests. Installed-wheel consumer runs passed in Stuff and reproduced a baseline FFmpeg failure in Toolbox. Whole-change retention unfinished. | Bound the remaining Tests inventory and qualify the serial gate |
| vault | `0e72b21112b840aa5b7fa373eeeab79e63ed59bb` | Active; Ground/Diagnose/Types and runtime repairs merged; Tests draft #30 at `0671858` | Ordinary CI green on macOS and both Linux musl architectures; Linux mutation has misses and exhausted shards | Diagnose Linux unit test cost, then verify the successor accounting and remaining decisions |
| diff-pretty | `02f0723400c584078b42290ceddecc9521353231` | Active; Ground/Diagnose/Types, sanitizer repair and CLI assertions merged; Tests draft #31 at `872ae4c` | Main integrated, nine gate and eight CLI tests pass locally; hosted gate startup fixes pushed | Check numeric and renderer results and complete hosted controls |
| loc | `897131f0948931480008d9b4363a4fb5bfc6ca85` | Active; Ground/Diagnose/Types, stdin-selection fix and masks/CLI/detection witnesses merged | PR17 macOS and both musl platforms green; mutation retention unfinished | Finish the existing critical inventory and cost/CI requirements |
| stats | `6de663387e742c4652b57d8c5096ed54b7b5a374` | Active. Diagnose, sandbox and command fixes, bounded ingest type inventory and Solid 2 upgrade merged. | #23 passed all three checks. Legacy upgrade CI and Types and Tests are incomplete. | Exercise the pinned legacy-upgrade baseline |
| stuff, repomod | `af40c440e1a2d5b398954361a0db0b402057128b` | Active. #55–60 and #62–63 merged, including the matrix P2, type witness and upstream oracle. | Ten checks passed for each merge. #61 awaits macOS Rust. Fresh serial coverage and two bounded mutation Scenarios are recorded. | Select the bounded effect and publication decisions for mutation |
| fastermod | `e4d8be692d0ef3497447e027222cf6e04b2f374b` | Active. #27 merged the Ground boundary map and local test and lint baseline. | #27 passed Linux arm64 tests and lint. The current-revision rustybench baseline remains pending. | Finish the own-workload baseline and start Diagnose |
| ptytest | `3fd48afe94e3f8dd5a145a64afe7061a9830529a` | Active. Ground reproduced a deadline equality bug. #13 has a deterministic witness. | #13 passed Linux and lint. macOS CI and consumer proof are in progress. | Finish the deadline repair and merge the shared Make/CI entry point |
| tm | `6cf0b949c2593c0959268a3d1995b972b05f58b6` | Active; fixture repairs merged, Ground and later stages open | Recent repair CI green; quiet-host cost unresolved | Finish Ground cost and component scope |
| toolbox | `8d2cd08c71ff00d311212d85940f95c8359aa76f` | Blocked; pass not started; historical partial calibration only | Actions billing and missing native tools; no pass claimed | Recheck billing and which media/fio boundaries actually execute |

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
| discover | C |  |  |  |  |  |  |  |  |  |  |  |  |
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
