# Deslop scorecard

One row per in-scope repository for the [deslop campaign](deslop.md). The campaign agent fills each
row from the repo's `## Report` at check-up. Cells hold `before → after`. Coverage is recorded but
never gated.

## Current checkpoint, 2026-11-17

These default heads and open PRs were checked during winddown. No complete
M2 report is claimed. Each Report refresh and remaining acceptance condition
is assigned in the [resumption roadmap](deslop-roadmap.md). Historical values
below do not override these states. Broader tiers are outside the current
dispatch authorization until M2 approval, while remaining in the full-fleet goal.

| Repository | Default revision | Pass state and completed work | CI and retention | One next action |
| --- | --- | --- | --- | --- |
| srv | `a37bcef633358d5b2da828c82c58a3329d5107e2` | Complete Report; all stages closed | Default CI green; mutation, coverage and strict profile registered | Recheck retained guarantees and runner cost for M2 |
| fz | `eebed611362d5d2b9b1e430633fbf0ab86be23e0` | Complete Report through cumulative review | Default CI green; retained-policy eligibility needs check-up | Verify retained checks survive removal of the campaign TODO |
| buildlib | `8d7e8739c8ce1d25454b346d431850841064f6a0` | Active; Ground, Diagnose, Types and dead-code scan merged; four critical scenarios accounted | Strict profile registered; new mutation CI is local, unqualified | Review and qualify `deslop/mutation-ci`, including actual PR controls |
| extensions | `513c05c42fe9b84d076a440d29112dd6fc4a41e9` | Active; Ground, Diagnose, Types and archive/recovery/storage/MV3 witnesses merged | Adopted lint retention, bounded browser job and whole-change gate unfinished | Wire the already demonstrated lint/browser guarantees and finish the TS gate |
| pytest-parallel | `56f608fbb05b99d8c9011f1af55c22b5188b25e4` | Active; Ground, Diagnose, Types, worker coverage and scheduling/event/report/network witnesses merged | PR25 lint and Linux/macOS tests green; whole-change retention unfinished | Bound the remaining Tests inventory and qualify the serial gate |
| vault | `0e72b21112b840aa5b7fa373eeeab79e63ed59bb` | Active; Ground/Diagnose/Types and runtime repairs merged; Tests draft #30 at `bf3dcd9` | Platform selector candidate is local; hardware/keyring limits remain | Qualify platform-correct whole-change selection before more scenarios |
| diff-pretty | `02f0723400c584078b42290ceddecc9521353231` | Active; Ground/Diagnose/Types, sanitizer repair and CLI assertions merged; Tests draft #31 at `6f1719d` | PR35 Linux/macOS tests and lint green; new gate unqualified | Reconcile draft/main, reuse valid sanitizer cost proof, finish named gate regions |
| loc | `897131f0948931480008d9b4363a4fb5bfc6ca85` | Active; Ground/Diagnose/Types, stdin-selection fix and masks/CLI/detection witnesses merged | PR17 macOS and both musl platforms green; mutation retention unfinished | Finish the existing critical inventory and cost/CI requirements |
| stats | `529cbdfc7649ffc1878bb723ac8ff114282db3dc` | Active; Diagnose, sandbox/command fixes and bounded ingest type inventory merged | PR21 and PR22 all checks green; legacy upgrade CI and Types/Tests incomplete | Name component finish lines and exercise the pinned legacy-upgrade baseline |
| stuff, repomod | `c14465ec50232d029a4fdbaf3588bb25fc6442aa` | Active; four P2 repairs merged; Diagnose record #55, type witness #56 and matrix fix #57 pending | #55–58 await macOS Rust at last check; no new retention claim | Integrate reviewed green heads and refresh Report before finishing bounded calibration |
| fastermod | `fda1e8fa0d1be5c8933f319d749c211b0c5f5fec` | Not started; five seeded steps open | No calibration/retention qualification established | Run Ground against this head and its own rustybench workload |
| ptytest | `3fd48afe94e3f8dd5a145a64afe7061a9830529a` | Not started; five seeded steps open | No calibration/consumer qualification established | Run Ground and establish real library consumer checks |
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
