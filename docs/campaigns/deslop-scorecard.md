# Deslop scorecard

One row per in-scope repository for the [deslop campaign](deslop.md). The campaign agent fills each
row from the repo's `## Report` at check-up. Cells hold `before → after`. Coverage is recorded but
never gated.

## Current checkpoint, 2026-11-18

M2 qualified representative workloads with explicit deferrals. Three
Tier A repositories have passed check-up, opening the Tier B passes. The
[resumption roadmap](deslop-roadmap.md) records the remaining acceptance
conditions. Discover is outside scope during the owner's rearchitecture.
Chromium-build is outside scope by owner decision on November 19.

| Repository | Default revision | Pass state and completed work | CI and retention | One next action |
| --- | --- | --- | --- | --- |
| srv | `c9965411d80a8b02d8b8c4cac2492ecc973ee296` | The #47 sharded candidate includes the archive startup warning. Earlier Report complete. | All 376 identities accounted for twice. The latest run caught 323, missed 24, found 17 unviable and confirmed 12 hangs. Its gate median was 850.3 seconds. | Resolve misses and qualify the ten-minute target |
| fz | `760d25d5fd11e4fe7f79cc81e60d85d491aea430` | Tier A pass settled after #48. The independent full timing repeat stayed within the bound and the immediate-interleaving trial resolved the small-input case. DSLP-10 is closed. | All five PR checks and both default checks passed. #44 preserved 439 mutation identities across two jobs. Four fleet rules returned no findings. The complete ish run passed 1,550 tests with eight ignored. | Retain the checked guarantees |
| buildlib | `6b2f4deb0a9afe024665863b6dd629fcfbd3c918` | Ground through Dead code and cumulative review complete. #28 shares the verified result reader used by the Node and CMake drafts. | Both default checks passed. A fresh clone passed 208 tests, both linters, four fleet rules and the manifest fault control. [Buildlib default](https://github.com/laputa-systems/buildlib/actions/runs/44448965470) | Recheck suite cost on an idle host |
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
| ffmpeg-build | `b9d9ce52ddc4cf171cc1f5aa707c8f1df6186474` | Tier A pass settled November 18. #74 removed an unreachable branch. #76 closed the empty-manifest finding. #77 merged the check-up report. | All 73 PR checks passed on #76, all ten on #77, and both default checks passed. The fresh clone passed 168 cases, lint, the four fleet rules and the empty-manifest control. | Retain the checked guarantees |
| pi-build | `235d3be03fc03dec6f217a3d9a2ff71a6f200c98` | Build-tools pass settled November 18 after #45. Both Linux profiles reproduced on x86-64 and ARM64. Two-host Intercom remains owner ticket DSLP-9. | Fresh check-up passed 77 Python tests, four companion fixtures, lint, four fleet checks and the negative control. The earlier gate accounted for 1,434 identities. Both default checks passed. | Run the separately enrolled Intercom procedure when the owner environment is available |
| node-build | `7c01c9477417b51e0144c2825e769d515868b779` | Ground, Diagnose and Types complete. #79–82 cover excluded payload entries, exact filesystem readback, malformed inspector responses and subprocess effects. | Both default checks passed. The locked Node binary rejected a same-length incorrect readback. The architecture and suite tests caught all 122 matched variants. Draft #61 passed 28 jobs across 14 earlier modules. [Node default](https://github.com/laputa-systems/node-build/actions/runs/44537497898) | Qualify the remaining smoke, product and build controller scopes |
| hi-lite | `d103040221466e47bc11a91ee120b160b5e52f21` | Ground, Diagnose and Types complete. #25 covers JSON token byte boundaries through the public highlighter. | The 150 ordinary tests passed with one existing opt-in XSH test. Both default checks passed. JSON caught 64 of 74, with two equivalents and eight timeouts. | Qualify remaining lexer coverage, allocation-only cases and the whole-change gate |
| doas-rs | `f424b9ecff6aa8ff6a2b4dc97d9f6c691e2f810a` | Ground, Diagnose and Types complete. #15 retains branch coverage, #17 verifies CLI admission and #18 reports config fragment paths and lines. | The stable-builder suite passed 170 tests. The CLI trial caught 43 of 53, with five recurring timeouts. Native x86-64 KVM passed all four installed-operation markers. | Qualify critical mutation scopes, live password entry and ARM64 guest effects |
| mdevd-rs | `5c323944d1179cd1bc9a41736e262226a065c004` | Ground, Diagnose and Types complete. Native guest and consumer evidence landed. #26 skips node operations when an event explicitly supplies an empty name. | Both PR builds and ordinary default CI passed. All 15 native ARM64 Alpine engine tests passed. The declared storm and idle workload passed its RSS, descriptor and CPU tick gates. | Resolve remaining mutations and verify physical coldplug |
| cmake-build | `ecdfa5d2ab0863a9e3ee37eeb2c5f81ea3594a4a` | Ground, Diagnose and Types complete. Default rejects invalid benchmark samples and keeps even sample medians finite. Tests cover release dispatch, fetch, doctor and inner build phases. | Both default checks passed. The earlier draft passed all 46 jobs in the 22-scope trial. [CMake default](https://github.com/laputa-systems/cmake-build/actions/runs/44537322457) · [Hosted trial](https://github.com/laputa-systems/cmake-build/actions/runs/44524202496) | Qualify the benchmark coordinator, ELF and `build.py` before promoting the gate |

CMake's new TLS scope caught 665 of 668 identities in both
the native x86-64 and ARM64 Linux jobs. The three remaining
variants are equivalent for the verified phase inputs and
locked loader paths. macOS had three additional case-only
survivors that Linux caught. The aggregate trial exposed an
x86-64 toolchain install mutation that the mixed file and
directory fixture could miss depending on enumeration order.
An added flat archive with two directories caught the variant
in both native jobs. All 28 trial jobs passed at
`d5c5cb4811efe9634d4cc065919a58e877d35672`.
[ARM64 TLS](https://github.com/laputa-systems/cmake-build/actions/runs/44505269102/job/135495202575) ·
[x86-64 TLS](https://github.com/laputa-systems/cmake-build/actions/runs/44505269102/job/135495202579) ·
[Toolchain result](https://github.com/laputa-systems/cmake-build/actions/runs/44505269102/job/135495202553) ·
[Order-independent fixture](https://github.com/laputa-systems/cmake-build/pull/87) ·
[Corrected aggregate](https://github.com/laputa-systems/cmake-build/actions/runs/44506684665)

The next native scopes covered sysroot, the upstream reference,
and Rust controller behavior. On each Linux architecture,
sysroot caught 424 of 436, reference caught all 118, and Rust
caught 684 of 686 identities. Exact dispositions account for
the 12 sysroot and two Rust equivalents. All 34 jobs at
`a85194452843337f1afdc47f2d19640e16e1407e` passed.
[Sysroot](https://github.com/laputa-systems/cmake-build/actions/runs/44509534627) ·
[Reference](https://github.com/laputa-systems/cmake-build/actions/runs/44510644785) ·
[Rust and aggregate](https://github.com/laputa-systems/cmake-build/actions/runs/44513348433)

The exact 18-scope trial used `make mutants-diff` locally and
through CI. All 38 jobs passed at `08d86c45b6086221fbb89a5f5248b07d2cc904cf`.
From the GitHub job timestamps, the 36 native executions had
a 33-second median and a 163-second maximum. The trial took
227 wall seconds and 1,648 runner seconds including the plan
and final job. These are one clean aggregate's timings. The
deliberate failure and documentation controls have separate runs.
[Native Make trial](https://github.com/laputa-systems/cmake-build/actions/runs/44517720657) ·
[Whole-change draft](https://github.com/laputa-systems/cmake-build/pull/54)

The 22-scope trial's first run failed when one stage job received
HTTP 520 while downloading the pinned Buildlib wheel. The retry
verified the wheel once in the planner and copied the same object
into every job's proof archive. Both patch jobs caught 137 of 139
identities with two exact equivalents. Both process-accounting jobs
caught 192 of 193 with one equivalent. The documentation control
skipped the wheel fetch and controller matrix.

The successful retry at `fe488f48c764621a221608f62b85d43bd4034d5c`
passed all 46 jobs. Its 44 native jobs had a median of 32 seconds
and a maximum of 146 seconds. The two exact runs used 3,588 runner
seconds in total, 1,749 for the failed run and 1,839 for the retry.
Their elapsed times were 253 and 222 seconds.
[Failed run](https://github.com/laputa-systems/cmake-build/actions/runs/44523600268) ·
[Verified retry](https://github.com/laputa-systems/cmake-build/actions/runs/44524202496) ·
[Documentation control](https://github.com/laputa-systems/cmake-build/actions/runs/44524454919)

## Tier A checkpoint

The November 18 checkpoint admits Tier B after Fz, Pi-build and
FFmpeg-build passed fresh check-up, default CI and F2/F3. The source
and test measurements below cover each report's stated scope.

| Step | Yield and cost |
| --- | --- |
| Ground | Fz established host and consumer boundaries. Pi-build split its build tools from the enrolled-host procedure. FFmpeg separated controller cost from native artifact qualification. |
| Diagnose and findings | The three reports recorded concrete boundary failures in terminal input, vendor restoration and staged manifests. FFmpeg's stale source-pin and empty-manifest fixtures both failed before the repairs and pass afterward. |
| Types | Pi-build resolved ten bare-mapping diagnostics without adding bypasses. FFmpeg resolved three unsound returns. Fz reported the scope of its compiler checks and existing test-only escape hatches. |
| Tests | Pi-build's retained gate checked 1,434 identities. Fz's retained gate split core from terminal jobs and verified the ish consumer. FFmpeg's final 22-scope native run took 539 wall seconds and 5,125 aggregate native runner seconds. |
| Dead code | Fz removed five lines from an unread benchmark field. Pi-build removed an uncalled normalization helper. FFmpeg removed the two-line unreachable devices branch. Vulture found one confirmed removal and at least six distinct dynamic-entry false positives across the three reports. Its tool recipe already limits it to discovery. |

FFmpeg's fresh check-up measured 2,333 to 2,693 first-party Python lines
and 944 to 3,987 Python test lines. Its typing escape-hatch count stayed
at three. The final controller, bootstrap and release collector covered
1,458 of 1,526 statements and 612 of 630 branches. The warm controller test
median was 5.52 seconds. The cold run took 6.58 seconds, and lint took
0.74 seconds after test setup. The report records the earlier paired
cost comparison, the exact artifact consumer checks and the fault that
made the empty-manifest regression fail. [FFmpeg-build report](https://github.com/laputa-systems/ffmpeg-build/pull/77)

The recurring case-only path aliases in FFmpeg and CMake now have a
case-sensitive replay rule in the mutation guidance. `make skills-check`
and the hosted skill policy passed. The completed reports identify
the dynamic names behind their Vulture findings and keep Ruff and
dependency checks in their language recipes. The reports establish
no other tool with three comparable zero-yield results.
[Mutation guidance](https://github.com/joshuarli/usr/pull/43)

Pi-build retains its P2 owner ticket for the enrolled two-host Intercom
procedure. Vault's recovery, Doas's privileged password and ARM64 guest
checks, and Mdevd's physical coldplug remain in their owning passes.
All seven in-scope Tier B repositories carry seeded backlogs and
supported test entry points. F3 retention applies as each repository
qualifies its guarantees.

## Tier B rollout

| Repository | Checked default revision | Hosted evidence |
| --- | --- | --- |
| Lz | `14edc95004ae141337a3c8bb8f299b08f8f9d8dd` | Ground recorded 169 ordinary tests and the separate Less parity gate. Both default workflows passed. [Lz #8](https://github.com/joshuarli/lz/pull/8) |
| Rustybench | `27c4d656986095b6a1bc6ed83d3b93869f3f21ca` | Baseline comparison rejects duplicate names and preserves the previous baseline on rejection. Diagnose reproduced malformed report encoding, a missing current-directory panic, and a macro option-order compile failure. The remaining library and macro review is open. Linux, macOS and lint passed on default. [Collector regression](https://github.com/laputa-systems/rustybench/pull/20) · [Diagnose findings](https://github.com/laputa-systems/rustybench/pull/21) |
| Laputa UI Dashboard | `c8c43870b5cbc14221fcb2fd77a07b9636643520` | Ground verified 68 unit and package cases and 338 Chromium cases. The pnpm metadata matches the existing pin. [Dashboard #14](https://github.com/laputa-systems/laputa-ui-dashboard/pull/14) |
| Tinyland | `109c6781ec88f92d6405d58ee15934d4e74b3cdc` | The pinned Alpine suite passed. Ground retains the Linux kache timings and lint gaps. [Tinyland #6](https://github.com/laputa-systems/tinyland/pull/6) |
| E | `74194303c4089f491f07b6085a7ddc2dbfa0b4fe` | Ground recorded 874 cases on both hosted platforms and locally with a short scratch path. DSLP-6 retains the reproduced long-path status-bar defect. Both default workflows passed. [E #30](https://github.com/laputa-systems/e/pull/30) |
| Defuddle-rs | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | Types passed the fixture-corpus gate. The CLI cases cover option forwarding, output preservation, terminal input and SingleFile admission. The latest fix preserves extraction from plain HTML that mentions both archive markers. Native tests, Node WASM tests and headless Chrome passed on default. [Defuddle-rs #32](https://github.com/joshuarli/defuddle-rs/pull/32) · [Default CI](https://github.com/joshuarli/defuddle-rs/actions/runs/44532927257) |
| Gluon | `d0348defb815e3999bd3d47e3762b0f0f86d4b7a` | Diagnose and Types complete. The five Ninja parity repairs passed the supported fixtures and the FFmpeg, Laputa and Play consumer checks. The restat type pairs every output with its observation. Eight packages inherit `unsafe_code = forbid`, and the strict fleet checks passed after profile registration. Both hosted checks passed on the Types report. Tests, Dead code and the remaining findings stay open. [Diagnose](https://github.com/laputa-systems/gluon/pull/36) · [Types](https://github.com/laputa-systems/gluon/pull/40) · [Fleet retention](https://github.com/laputa-systems/stuff/pull/168) |

Defuddle-rs measured branch coverage with cargo-llvm-cov.
The first CLI test change raised workspace coverage from 2,995
to 2,996 of 4,660 branches. Eight matched stdin and option
mutations went from five caught to six and then eight. A
regression test demonstrated that an invalid property could
truncate an existing output file and now checks its exact
bytes. The terminal test verified the diagnostic and exit
code, and disabling the guard failed within its deadline.
The owning backlog tracks wider extraction, metadata, archive,
output and WASM decisions and the retained gate.
[Coverage](https://github.com/joshuarli/defuddle-rs/pull/19) ·
[Option forwarding](https://github.com/joshuarli/defuddle-rs/pull/20) ·
[Output preservation](https://github.com/joshuarli/defuddle-rs/pull/21) ·
[Terminal input](https://github.com/joshuarli/defuddle-rs/pull/22)

Both extraction retries now keep document-wide pruning when
the initial parse removed content. The exact short-article
result excludes the footer the baseline restored. All 31
integration cases, four fixture-harness cases, and the default
workflows passed. Five interleaved corpus pairs left both
timing medians within baseline variation and peak live allocation
unchanged. Median cumulative allocated bytes rose by about
11 KiB per corpus pass.
[Retry pruning](https://github.com/joshuarli/defuddle-rs/pull/23)

The stored SingleFile fixture caught two controlled faults in
manifest index selection and explicit URL precedence. The
restored binary passed all 18 CLI cases and both default checks.
[SingleFile manifest](https://github.com/joshuarli/defuddle-rs/pull/24)

The shortcut favicon fixture reproduced the missing metadata
and verifies priority and origin fallback. The fixed source
caught all eight viable identities, and the five paired corpus
checks kept timing within baseline variation and peak allocation
unchanged. The Chromium fixture verified the generated WASM
bindings. Turning off iframe removal failed on the exact emitted
HTML. The source was restored and rebuilt.
[Favicon](https://github.com/joshuarli/defuddle-rs/pull/25) ·
[WASM runtime](https://github.com/joshuarli/defuddle-rs/pull/26)

The retained WASM job passed on the exact default after
merging the Make command and browser runner. The runner also
detected the known iframe-removal control locally and exited
nonzero with the browser diagnostic.
[Default WASM job](https://github.com/joshuarli/defuddle-rs/actions/runs/44517253477/job/135536367287)

### Chromium-build evidence before exclusion

At `1b58c7f81d9a299bab65f79750936525bda14fbc`, three hosted
Linux builders passed the offline install and controller suites.
[Chromium-build #24](https://github.com/laputa-systems/chromium-build/pull/24)

The stable v3.24 indexes retired Helium's pinned NSS and OpenSSL
revisions and Chromium's pinned Go, Node.js, and NSS revisions.
The old Go and Node.js archive URLs returned 404. Both products
now share the offline installation path, and the builder checks
the exact manifest after installation. Helium stages 314 APKs
for ARM64 and 316 for AMD64. Headless Chromium stages 226 for
AMD64. The native headless job checked all 241 manifest entries
and passed 36 controller cases.
[Helium native proof](https://github.com/laputa-systems/chromium-build/actions/runs/44484731201) ·
[Headless native proof](https://github.com/laputa-systems/chromium-build/actions/runs/44487063812/job/135433052753)


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
hashes agree across all ten results. The exact release comparison then
completed five more pairs with no row outside both 2% and baseline
spread. In the small-input wall-time row, Fz medians were 2.585 and
3.473 ms and fzy medians were 2.688 and 3.342 ms. The baseline Fz
range was 2.157–6.387 ms. A focused trial alternates the two release
binaries, a byte-identical baseline copy and fzy within each block.
[Control](https://github.com/laputa-systems/fz/actions/runs/44421140205) ·
[Repeat](https://github.com/laputa-systems/fz/actions/runs/44422469442) ·
[Focused trial](https://github.com/laputa-systems/fz/actions/runs/44423775482)

The focused trial passed five readiness-qualified blocks with 40
immediately interleaved rounds per block. The median of the five
paired wall-time medians was −0.23%, with block medians from −1.35%
to +1.92%. Total CPU was +0.19% and peak RSS +0.89%. The identical
baseline copy showed +2.85% median wall time. The complete consumer
run imported the exact Fz candidate into ish `fc62468e` and kept its
lockfile. All 1,550 top-level tests and workspace Clippy passed, with
eight cases ignored. The owning report records the commands and raw
run locations.
[Fz #48](https://github.com/laputa-systems/fz/pull/48)

Node's exact release census used Buildlib's pinned result reader on
native Ubuntu ARM64 and macOS. All 390 identities matched. Linux
caught nine path-case variants beyond the macOS result. The shared
survivors have concrete locale, equivalence or diagnostic dispositions.
Node's subsequent hosted input census also confirmed the reader rejects
unexercised identities. Its corrected selector includes normal JSON
receipt writers. Both hosts caught 41 of 49. The eight other outcomes
are equivalent defaults, equivalent encodings or diagnostic wording.
The matched package job caught 226 on Linux and 217 on macOS. Nine
path-case variants account for the difference.
[Release census](https://github.com/laputa-systems/node-build/pull/48) ·
[Native results](https://github.com/laputa-systems/node-build/pull/51) ·
[Package publication cases](https://github.com/laputa-systems/node-build/pull/52)

Node's whole-change draft uses Buildlib's pinned Git parser and
strict result reader. A mixed product and test change selected
the changed product module and six qualified modules. Forty
remaining ordinary release tests passed. The full 390-identity
release selection reopened five timeout-test identities. The result
verifier rejected them and separately rejected a symbolic-link
result file and a changed rendered-mutant digest.
[Whole-change controls](https://github.com/laputa-systems/node-build/pull/61) ·
[C-locale native accounting](https://github.com/laputa-systems/node-build/actions/runs/44440522088)

Buildlib #28 supplies the common reader for Node and CMake's trial
result files. The reader checks that the archived source and generated
receipts are regular files inside the trial checkout, then binds the
approved variants to the exact source and rendered mutation bodies.
CMake's positive control passed on native x86-64 and ARM64 Linux. The
mixed change preserved both input jobs and reopened phase read variant
4 on both architectures. The ordinary controller passed the mixed
change. The four CMake jobs passed again after pinning the shared reader.
[Buildlib verifier](https://github.com/laputa-systems/buildlib/pull/28) ·
[CMake positive](https://github.com/laputa-systems/cmake-build/actions/runs/44446845009) ·
[CMake deletion control](https://github.com/laputa-systems/cmake-build/actions/runs/44447078808)

FFmpeg's four-scope draft passed all twelve native jobs and its final
check. The receipt binds the approved outcome to the exact function
source and rendered mutant body. The runtime coordinator's subsequent
three-host inventory found 37 surviving identities on both Linux
architectures. Ten case-only path variants survived on the macOS
volume in addition to the same 37. The extended draft passed all
15 native jobs. A separate native run caught all 293 ELF and Mach-O
probe identities. With those probes included, a mixed control made
an equivalent ELF expression change and removed the tools audit
fixture. Ordinary CI passed and only the three tools jobs and the final
gate failed. The fixture was restored. Bootstrap has three native
results and still needs to join the draft.
[Whole-change trial](https://github.com/laputa-systems/ffmpeg-build/actions/runs/44455025702) ·
[Runtime census](https://github.com/laputa-systems/ffmpeg-build/actions/runs/44454562733) ·
[Binary probes](https://github.com/laputa-systems/ffmpeg-build/actions/runs/44455219408) ·
[Mixed control](https://github.com/laputa-systems/ffmpeg-build/actions/runs/44455548747) ·
[Bootstrap census](https://github.com/laputa-systems/ffmpeg-build/actions/runs/44455832326)

FFmpeg's ten-scope draft passed after adding bootstrap, dispatch, the
release collector and the build coordinator. The coordinator fixture
checks all three stage shapes, Linux linker responses, symlink
preservation, and replacement of a matching stamp over incomplete
output. It caught 317 of 336 on macOS. CMake's draft added the build
budget, Git reproduction, wheel cache and archive scopes. Both Linux
architectures passed all seven scopes and the final check.
[FFmpeg native trial](https://github.com/laputa-systems/ffmpeg-build/actions/runs/44459155229) ·
[CMake native trial](https://github.com/laputa-systems/cmake-build/actions/runs/44459720634)

FFmpeg's draft now selects stage and runtime policy scopes through the
same committed archive entry point in `make mutants-diff` and on the
native matrix. The stage filesystem scope caught all 150 identities on
Linux x86-64, Linux ARM64 and macOS ARM64. The runtime policy scope
caught 156 of 158 on each host, with two equivalent falsey parser
initializers. All 48 native jobs and the final check passed. The
separate local toolchain trial caught 179 of 186. Across three
interleaved macOS runs, warm test medians were 1.18 seconds for the
76-test baseline and 4.33 seconds for the 146-test candidate.
The candidate range was 3.29–4.34 seconds. Both load guard invocations
returned success. The guard also reported significant concurrent
activity, so these times describe observed test cost.
[FFmpeg native trial](https://github.com/laputa-systems/ffmpeg-build/actions/runs/44464833976) ·
[Stage and policy fixtures](https://github.com/laputa-systems/ffmpeg-build/pull/68) ·
[Toolchain fixtures](https://github.com/laputa-systems/ffmpeg-build/pull/69)

Node's draft refreshed through the command dispatch and staged command
fixtures and passed its planner and all 28 native jobs. The source
selection was the same 14 modules.
[Node native trial](https://github.com/laputa-systems/node-build/actions/runs/44464176862)

CMake's listener fix requires that the worker actually shut down
before the probe reports success. The controller test runs a real local
positive connection and deliberately reports the worker as still alive.
A separate reproduction holds a real listener and sees an open
descriptor after gateway discovery or worker startup raises. Its fix
is in normal hosted verification.
[CMake worker check](https://github.com/laputa-systems/cmake-build/pull/67) ·
[CMake setup cleanup](https://github.com/laputa-systems/cmake-build/pull/69)

The retained FFmpeg lane uses the locked dev environment and a
single `make mutants-diff` command per native shard. The scoped
fleet check passed the test workflow, coverage, strict profile and
mutation rules on `79b21eed`. On a disposable copy of the same
revision, replacing the Make mutation command with `make test`
reopened the mutation-lane finding. The 22-scope run passed all
66 Linux and macOS jobs and its final check.
[FFmpeg gate](https://github.com/laputa-systems/ffmpeg-build/pull/62) ·
[Native proof](https://github.com/laputa-systems/ffmpeg-build/actions/runs/44469226166)

CMake caught 880 of 900 sandbox variants locally and 885 of 900
on both native Linux hosts. Five additional catches cover
case-only paths. Node's checker previously accepted a ten-pass
TAP report as one pass. The corrected probe ran the existing test
successfully against the installed, pinned Node 26.12.1.
[CMake sandbox trial](https://github.com/laputa-systems/cmake-build/actions/runs/44469636774) ·
[Node smoke correction](https://github.com/laputa-systems/node-build/pull/77)

The Stuff #139 default macOS Rust job hit a reset after the 503
response in the connection-limit case. The exact retry passed.
#140 tests admission with a second idle connection and checks the
full response. All six local HTTP cases and twelve additional
refusal runs passed. The PR and default workflows passed.
[HTTP fixture](https://github.com/laputa-systems/stuff/pull/140)

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

The November 19 fresh-clone repeat at `6b2f4deb` passed all 208
Buildlib tests, Ruff and ty. Coverage repeated 901 of 902 statements and
291 of 292 branches. The same manifest fault failed and passed again after
byte-for-byte source restoration. Repomod returned an empty findings list
for `gha-test-workflow`, `make-coverage-target`, `mutants-diff-lane`, and
`strict-typing-profile` against that clone. The host readiness check
reported active workloads, so this repeat supplies correctness and
retention evidence and leaves suite timing deferred.

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
