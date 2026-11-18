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
| fz | `71a3a48f5af9f1438e2dee36f3ebb4ee218d8af4` | Earlier Report complete. #47 records five qualified hosted pairs with six timing rows outside the baseline spread. DSLP-10 remains open. | All five PR checks and both default checks passed. #44 preserved 439 mutation identities across two jobs. The identical-binary timing control also showed one out-of-bound row in a different workload. | Independently repeat the exact release pair |
| buildlib | `1497970d9454a6a9875b1f201cbaad71fd92a010` | Ground through Dead code and cumulative review complete. Fresh check-up passed all 208 tests and reproduced the manifest filename mismatch with an injected fault. | All 17 checks passed #27. Default CI and lint passed. Test workflow, mutation, coverage and strict typing policy checks returned no findings. | Retain the checked guarantees |
| extensions | `10f6101eba8916aa0f4b4aed07d91f6178ff525b` | Active. Coverage, type-aware lint and installed Chromium are retained. Draft #22 covers parser and storage. #27 verifies ZIP metadata and CRC. | The parser and storage jobs passed in 617 aggregate runner seconds with four hosted controls. #27 caught 35 of 44 selected identities. | Qualify the remaining archive and browser effects |
| pytest-parallel | `eb11974795c1b2e5e26183c992ec021c80b007d6` | Active. #40 verifies report validation. #41 checks worker stop, drain and cleanup. #42 holds stop state in the deadline. | All 212 tests and three hosted checks passed. The reduced state has 111 catches of 162. Its installed wheel passed 1,500 repomod tests with three skips. | Qualify the remaining coordinator lifecycle and socket decisions |
| vault | `553fb720046e360cd9f62beeaef007ad398978db` | Active. #36 records the platform trial and defers two-Mac recovery to an owner-run check. | Ordinary draft CI passed macOS and both Linux musl architectures. Mutation failed on 14 Linux and 13 macOS shards. | Qualify the platform union and obtain the separate hardware and keyring evidence |
| diff-pretty | `b38628ec4c3e5b4bad92c1f41b31101e6bdc01b7` | Active. #42 and #43 cover signal and terminal effects. #44 covers session finish and scroll clamping. #45 preserves selection across filtered input. | All 15 checks passed on each PR. The #45 tests caught five injected changes. Stuff #70 retains the mutation workflow. | Bound wider live-loop and renderer mutation and paired cost |
| loc | `341cbeef5a07088ff33153d0244db01443178c02` | Active. #24 retained the shebang gate. #29 routes normal CI through Make. | #29 passed all eight checks. The mixed control counted the same 25 identities on macOS and both musl targets. Stuff #107 registered retention. | Finish broader SIMD and file-selection Tests |
| stats | `ec5993b6f02644cbc18f4fc0706fae21a0d37b63` | Active. #36 exercises mixed binary ACKs through Workerd. Draft #37 runs Workerd and Rust. | Ordinary #36 checks passed. #37 caught all 42 Rust identities and 25 Workerd identities with two equivalents in 322 runner seconds. | Finish component coverage and the producer timeout dispositions |
| stuff, repomod | `17845f5237d045838ba8678e1b795e4256cae139` | Active. Types and Dead code complete through #98. #103 verifies fixer push diagnostics. | Draft #92 passed ten jobs across five scopes, accounting for 252 identities per platform in 740 runner seconds. #103 caught 121 of 127, with six equivalents. | Qualify the wider inventory and whole-file fallback |
| fastermod | `d99400a71800b2be31b0f1f95a832147d1c00125` | Active. #36 verifies the saved-plan read set. #37 retained text source mutation, and #42 classifies every pull request. | All ordinary checks and both retained mutation jobs passed. Four hosted controls qualify the source scope. Earlier paired acceptance covered all seven performance workloads. | Qualify terminal review and wider saved-plan mutation |
| ptytest | `606027bb32999fa3e1bb960285384a89081a957a` | Active. #25 retained the terminal mutation scope. #30 makes the workflow classify each pull request. | Both platforms and four controls confirmed the bounded selection. The same macOS Xsh compile failure occurred at baseline and with the candidate. | Qualify lifecycle, replay and remaining consumer Tests inventory |
| tm | `6cf0b949c2593c0959268a3d1995b972b05f58b6` | Active; fixture repairs merged, Ground and later stages open | Recent repair CI green; quiet-host cost unresolved | Finish Ground cost and component scope |
| toolbox | `8d2cd08c71ff00d311212d85940f95c8359aa76f` | Local native and coverage evidence complete on #15. Hosted qualification deferred for Actions billing. | All 750 tests and five native fio subtests passed locally. The November 18 retry failed before runner allocation. | Resume hosted checks when Actions can start the jobs |
| ffmpeg-build | `a9ebce0aed380a8201ad5482c7b94f76864e8f89` | Ground, Diagnose and Types complete. #35 records all ten native artifact checks. #40 and #41 diagnose malformed toolchain and runtime library metadata. | All 118 ordinary tests, lint and both default checks passed. The shared audit caught 386 of the same 696 identities before #41. | Qualify whole-change coverage |
| pi-build | `235d3be03fc03dec6f217a3d9a2ff71a6f200c98` | Build-tools pass settled November 18 after #45. Both Linux profiles reproduced on x86-64 and ARM64. Two-host Intercom remains owner ticket DSLP-9. | Fresh check-up passed 77 Python tests, four companion fixtures, lint, four fleet checks and the negative control. The earlier gate accounted for 1,434 identities. Both default checks passed. | Run the separately enrolled Intercom procedure when the owner environment is available |
| node-build | `88e2d2f05b811157e297a538c88ca086a3b6bfd8` | Ground, Diagnose and Types complete. #38 records native qualification for Node 26.12.1. #41 diagnoses version-probe failures. #42 removes an unused wrapper and #43 diagnoses Git probe timeouts. | All 33 release cases and both default checks passed. The census at #41 caught 350 of 395 release identities and #42 removed the four uncovered wrapper identities. Both native artifacts passed 18 smoke cases and both size budgets. | Qualify the outstanding Git, record and wider controller decisions and the whole-change gate |
| hi-lite | `75eed701595361ae6fb7ff794c76bea833fd8474` | Ground, Diagnose and Types complete. #20 fixes full-range diff previews. #22 covers shebangs and case-sensitive extensions. #23 accounts for all 30 language-module identities. | Both ordinary platforms and lint passed. Language caught 25 with five compiler rejections. The diff census and survivor rerun caught 137 of 148 identities. | Qualify lexer coverage, allocation-only cases and the whole-change gate |
| doas-rs | `f424b9ecff6aa8ff6a2b4dc97d9f6c691e2f810a` | Ground, Diagnose and Types complete. #15 retains branch coverage, #17 verifies CLI admission and #18 reports config fragment paths and lines. | The stable-builder suite passed 170 tests. The CLI trial caught 43 of 53, with five recurring timeouts. Native x86-64 KVM passed all four installed-operation markers. | Qualify critical mutation scopes, live password entry and ARM64 guest effects |
| mdevd-rs | `5c323944d1179cd1bc9a41736e262226a065c004` | Ground, Diagnose and Types complete. Native guest and consumer evidence landed. #26 skips node operations when an event explicitly supplies an empty name. | Both PR builds and ordinary default CI passed. All 15 native ARM64 Alpine engine tests passed. The declared storm and idle workload passed its RSS, descriptor and CPU tick gates. | Resolve remaining mutations and verify physical coldplug |
| cmake-build | `2bf6fdb8f285399e5f9cd6c090666b8da2182f12` | Ground, Diagnose and Types complete. #45 verifies cleanup and retry after failed publication. #46 simplifies directory validation and exercises root and nested entries. | #44 caught 518 of 571 input identities. #45 caught 36 of 48 in publication. #46 passed the native controller and lint checks. Both stable archives passed native qualification. | Obtain a compatible mirrored coverage wheel and qualify the remaining extraction and whole-change checks |


Fz check-up at `0ec537d53eca0a12af07687250111a48023ee8d3` used a fresh macOS ARM64 worktree, the
repo's pinned nightly, fzy commit `34b88869d022e861da4846c4463aea3ddfb3ff30`,
`CARGO_BUILD_JOBS=2`, `RUST_TEST_THREADS=2`, kache, and
`cpu-guard --cores 3 -- make test`. Cold and warm attempts took 21.15 and
14.82 seconds. `make lint` took 3.31 seconds. For the CLI control, change
the parse-error exit from 1 to 0 in `src/cli.rs` and run
`cargo test --locked --test cli invalid_lines_and_positional_arguments_fail_without_stdout -- --exact`.
It exits 101 with 0 observed where 1 is expected. Reverting the fault restores
the pass. Local release timings overlapped a CPU-intensive workload. An
earlier hosted attempt failed readiness mid-run. The next hosted run
collected five complete pairs and exceeded baseline spread and 2% in six
rows, including three terminal redraw timings. The unchanged fzy oracle
also moved in the small-input wall row. The owning report records all
six ranges, binary sizes, RSS and reproduction.
[Fz #47](https://github.com/laputa-systems/fz/pull/47)

The identical-binary control completed five pairs with the same fixtures
and readiness checks on a separate hosted allocation. None of the
original six rows exceeded the bound. One different row exceeded it,
the default dense 100k-path user CPU median at 19.726 to 23.208 ms
with baseline range 19.337–22.641 ms. The identical Fz and fzy
hashes agree across all ten results. A repeat of the exact release
comparison is running.
[Control](https://github.com/laputa-systems/fz/actions/runs/44421140205) ·
[Repeat](https://github.com/laputa-systems/fz/actions/runs/44422469442)

The Pytest-parallel wheel built from `eb11974795c1b2e5e26183c992ec021c80b007d6`
passed `make repomod-test` at Stuff `ad43e917` with 1,500 passes and
three skips. Its SHA-256 was
`0ce642a3504425839bd93df47f8ec4d075150a1d04de5fed2aa9580a50140cec`.
Build it with `uv build --wheel`, run `uv sync --locked --group dev`
in an isolated Stuff environment, then install the wheel with
`uv pip install --no-deps --reinstall`. Verify that the imported
coordinator comes from that environment and that its stop condition
uses the drain deadline. Run `UV_NO_SYNC=1 make repomod-test`.
[Coordinator change](https://github.com/joshuarli/pytest-parallel/pull/42)

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
