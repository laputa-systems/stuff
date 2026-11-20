# Campaign: deslop the fleet

Goal: every in-scope repository has truthful strict types, tests that detect real defects at its
public boundaries, no dead code, and structure that its review findings no longer fault. No repo
loses correctness, functionality, or performance on the way. CI enforces what the work
established, so the slop cannot return.

## Status

Resumed 2026-11-19 under the selective mutation policy (decision 4,
**Mutation spending is bounded**) and the Bench step (decision 14).
Discover, Chromium-build, Vault and Pi-build are excluded.

Tier A passes completed through Report on resumption: Node-build
([#88](https://github.com/laputa-systems/node-build/pull/88)), CMake-build
([#130](https://github.com/laputa-systems/cmake-build/pull/130)), Doas-rs
([#22](https://github.com/laputa-systems/doas-rs/pull/22)), Mdevd-rs
([#30](https://github.com/laputa-systems/mdevd-rs/pull/30)), Hi-lite
([#30](https://github.com/laputa-systems/hi-lite/pull/30)) and Vault
([#42](https://github.com/laputa-systems/vault/pull/42)) and Diff-pretty
([#50](https://github.com/laputa-systems/diff-pretty/pull/50)). No completion review found a new defect; Doas-rs filed
DSLP-13 (P3). Each pass ran Tests, Dead code and Bench as separate merged
PRs before its Report.

Defects fixed and behaviors protected on resumption:

- Vault: tests from 11 stranded branches landed as 15 behavior groups, each
  proven by an injected fault ([#38](https://github.com/laputa-systems/vault/pull/38));
  secret commands reject surplus names before storage ([#37](https://github.com/laputa-systems/vault/pull/37));
  the rage interoperability test now fails in CI when rage is missing,
  with rage 0.12.1 pinned in the CI image ([#41](https://github.com/laputa-systems/vault/pull/41)).
- Diff-pretty: the critical contracts map to protecting tests with no new
  mutation runner time ([#46](https://github.com/laputa-systems/diff-pretty/pull/46));
  an unreachable buffered pager path and the unused `regex-lite` removed
  ([#47](https://github.com/laputa-systems/diff-pretty/pull/47)); CLI render
  and PTY pager journeys with a byte oracle ([#49](https://github.com/laputa-systems/diff-pretty/pull/49)).
- Pi-build: `make sizes` verifies archives and `make size-diff` compares
  against a reference directory; all 222 sizes mutants are caught
  ([#47](https://github.com/joshuarli/pi-build/pull/47)).
- Dead code removed in Node-build, Doas-rs, Mdevd-rs, Hi-lite and
  Diff-pretty; CMake-build and Vault had nothing to remove.
- Rustybench's option-expression fix ([#22](https://github.com/laputa-systems/rustybench/pull/22)).

Bench (decision 14) entrypoints, proven at Edit and one Change workload:
Node-build, CMake-build, Mdevd-rs, Hi-lite, Fz and Diff-pretty. Doas-rs,
Pi-build, FFmpeg-build and Vault have no benchmarks; their audits record
the outcome lists. Mutation spending on resumption stayed within the
10-minute trial budget; only Doas-rs ran a new bounded trial (1.87
runner-minutes).

Environment-blocked, open at P2: timing gates Node-build DSLP-9 and
CMake-build DSLP-7 need a quiet native host. The owner re-ranked
missing-evidence bench gaps without a demonstrated regression to P3
(Mdevd-rs DSLP-7 and DSLP-8, FFmpeg-build DSLP-7, Vault DSLP-9 to DSLP-11).
Parked on host readiness (`perf-gate-ready` reports a hot OrbStack
VM): Gluon [#39](https://github.com/laputa-systems/gluon/pull/39) and
[#41](https://github.com/laputa-systems/gluon/pull/41), Hi-lite
[#26](https://github.com/laputa-systems/hi-lite/pull/26) and Defuddle-rs
[#33](https://github.com/joshuarli/defuddle-rs/pull/33). The
[reboot inventory](deslop-roadmap.md#retained-stuff-worktrees) lists retained
checkouts and branches; [the .work cleanup](work-cleanup-20261119.md)
records what was reclaimed.

Tier B passes completed through Report: Rustybench
([#28](https://github.com/laputa-systems/rustybench/pull/28)), Laputa UI
Dashboard ([#20](https://github.com/laputa-systems/laputa-ui-dashboard/pull/20)),
Defuddle-rs ([#37](https://github.com/joshuarli/defuddle-rs/pull/37)), Tinyland
([#14](https://github.com/laputa-systems/tinyland/pull/14)), E
([#39](https://github.com/laputa-systems/e/pull/39)) and Gluon
([#54](https://github.com/laputa-systems/gluon/pull/54)) and Lz
([#16](https://github.com/joshuarli/lz/pull/16)). Tier B is complete. The
owner ruled Lz's `--help` divergence unintended: Lz parses options and emits
less's diagnostics first, and its own reference moved to `--lz-help`
([#14](https://github.com/joshuarli/lz/pull/14)). Lz had skipped the Bench
step; it landed before the Report ([#15](https://github.com/joshuarli/lz/pull/15)).

Defects fixed in Tier B include Gluon's failed-edge scheduling, missing
dependency records, `configure_file` failures and regeneration options
(#46 to #53), E's long-path status bar, xattr loss on atomic save and
fragmented escape sequences (#36 to #38), Tinyland's unbounded per-client
object counts (#13), and Lz's quit-on-escape, CSI overflow and broken-pipe
exit (#13). Lz #13 also introduced a help-mode escape regression that the
parity gate caught and #14 fixed. E's new split-escape test is timing-sensitive on hosted macOS
(E DSLP-11, P3).

The Tests step closes without a mutation CI lane where `cargo-mutants` and
`cargo-llvm-cov` are not on the crate mirror; that mirror gap is shared,
not per repository.

From November 19 the owner ruled that P3 findings are filed, not fixed,
for the rest of the campaign. Gluon DSLP-21 (the unused dependency-log
recompaction API) stays filed on that ruling.

shck (a hard fork of shuck, 337k Rust lines) joined on November 19 as a
tier D repository worked by component. Ground
([#2](https://github.com/joshuarli/shck/pull/2)) added its first test CI and
a split into about 30 components; Diagnose
([#3](https://github.com/joshuarli/shck/pull/3)) filed two P1 and two P2
findings. Both P1s are fixed: `format --minify` no longer writes unparsable
shell for heredocs inside compounds
([#4](https://github.com/joshuarli/shck/pull/4)), and the check cache
invalidates on transitive source changes
([#5](https://github.com/joshuarli/shck/pull/5)). Types runs per component
from a workspace census (`docs/deslop-types.md` in shck); each slice must
fix its component's cast and wildcard-match leads, not only adopt lints.

shck then completed through Report
([#34](https://github.com/joshuarli/shck/pull/34)). Steps and their PRs:

- P2 fixes: DSLP-9 ([#7](https://github.com/joshuarli/shck/pull/7)), and
  DSLP-10 with DSLP-15 ([#12](https://github.com/joshuarli/shck/pull/12)).
- Bench: tiers in `benches/driver.py`
  ([#14](https://github.com/joshuarli/shck/pull/14)).
- Types: 8 component slices.
- Tests: 7 slices (#17 to #29). Each new test was proven by an injected fault,
  and production behavior did not change.
- Dead code: 7 slices (#16 to #33), deleting about 2,350 lines.

The completion review found two defects in #12's resource-limit reporting,
both fixed in [#32](https://github.com/joshuarli/shck/pull/32):

- for stdin input, `check` dropped a limit error when lint diagnostics were
  present;
- running out of fuel between commands reported `Fatal`, not
  `LimitExceeded`.

shck items that need the owner, about public APIs and rule codes:

- DSLP-21: unused indexer and discover APIs;
- DSLP-22: parser public APIs with no workspace consumer;
- DSLP-23: `GlobPatternBehavior::sh_glob`;
- DSLP-25: `format_range`;
- DSLP-26: six registered rules (C065 to C068, C077, X077) are empty stubs.

Other P3 and P4 findings are filed per the November 19 ruling.

From November 19 the host stays busy with the owner's other work. Performance
and test-cost evidence therefore follows the busy-host rules in usr
`performance.md#busy-host-evidence`, so lanes no longer wait on
`perf-gate-ready`. Those rules cover scaling ratios, interleaved CPU-time pairs,
load-independent counters, and the runner's own `finished in` durations. The
disk-pressure threshold is now an absolute 16 GiB of free space, not a
percentage.

On November 20 the owner delegated every remaining decision and asked for the
campaign to finish. The inventory that day: 17 in-scope repositories had not
started their pass (ctrs, img, ish, kache, play, soulseek-rs, tansu, usr, tm,
smolith, and the forks crabtables, fd, jaq, oxish, rage, rust-fontconfig and
rustix). Seven more had Tests or Dead code open (extensions, loc,
pytest-parallel, stats, fastermod, ptytest, stuff). The rest were settled
apart from P3 and P4 tickets. The rulings taken under that delegation:

- **Environment-blocked acceptance does not hold a pass open.** The
  supported scope settles. Quiet-host timing, hosted-runner billing,
  hardware, two-host and mirror-gap checks become `Needs environment`
  tickets in the repository's `TODO.md`. This covers Node-build DSLP-9,
  CMake-build DSLP-7, Pi-build DSLP-9 and DSLP-10, and Vault's recovery
  checks.
- **Open Tests tickets close on the finite inventory** that
  [Bound every open Tests ticket](deslop-roadmap.md#bound-every-open-tests-ticket)
  names, with recorded dispositions. Wider mutation stays advisory.
- **shck owner items:** delete the unused public APIs (DSLP-21, -22, -23,
  -25) and the six stub rules (DSLP-26), once `repomod deps` shows no
  consumer outside the workspace.
- **Order:** forks first (their diverged scope is 0.5k to 15k changed
  lines), then the repositories under 100k lines, then img, play, tansu,
  smolith and kache by component.
- **Phase 4 runs per repository** as each one settles. Its open P3 and P4
  tickets move to `TODO.md` and `TODO-DESLOP.md` is deleted in one PR.
  The fleet-wide lint, the scorecard and this doc's retirement come last.

Next: fork passes, then per-repository Phase 4 for the settled set.

## Accepted work

The 2026-11-18 M2 checkpoint records qualified representative workloads
and explicit deferrals. Tier A repo passes have started. The
[roadmap](deslop-roadmap.md) gives the acceptance criteria and the
[scorecard](deslop-scorecard.md#current-checkpoint-2026-11-18) records the
checked revisions. [M2 calibration evidence](deslop-m2.md) records the
qualified workloads and remaining boundaries. Pi-build, Fz and
FFmpeg-build have settled in Tier A. The checkpoint admits
Tier B under the existing campaign approval. All seven in-scope Tier B
default branches already carry their seeded backlogs. The
remaining Tier A passes continue.

- All seven in-scope Tier B repositories have supported Make test entry points.
  Gluon, Rustybench, Lz, E, and Laputa UI Dashboard completed Ground.
  Defuddle-rs completed Diagnose and Types and verified CLI option
  forwarding, output preservation and terminal input. Both extraction
  retries now preserve document pruning. Default CI runs the WASM
  adapter in Node and the web bindings in headless Chrome. Tinyland's pinned suite
  passed, and its Ground ticket retains the lint and Linux kache
  timing gaps. [Tier B rollout](deslop-scorecard.md#tier-b-rollout)
- Gluon restored differential testing on macOS and stable Alpine,
  repaired five Ninja parity cases, and completed Diagnose and Types.
  The fleet retains the workspace-wide unsafe-code rule. Tests,
  Dead code and the remaining findings are open. Rustybench's CLI
  rejects duplicate names in baseline comparisons. Its review
  reproduced three additional CLI and macro failures.
  [Tier B rollout](deslop-scorecard.md#tier-b-rollout)
- Both Chromium products install verified APK archives with networking
  disabled on the digest-pinned Alpine 3.24.2 base. Helium's native
  ARM64 and AMD64 manifests have 326 and 328 packages. The headless
  AMD64 manifest has 241. Native builder tests passed for all three
  jobs. A cold cache still needs the exact upstream archive URLs.
  [Helium](https://github.com/laputa-systems/chromium-build/pull/23) ·
  [Headless Chromium](https://github.com/laputa-systems/chromium-build/pull/24)
- Four managed-checkout cleanup batches retired 106 completed
  worktrees with 15.46 GiB of measured path allocation.
  The next pass retired 72 with 17.99 GiB of measured path allocation.
  [November 18 receipt](managed-cleanup-20261118.md) ·
  [November 19 receipt](managed-cleanup-20261119.md)
- FFmpeg-build closed its final review finding after the native mutation
  workflow and both ordinary checks passed. Its fresh default check-up
  passed 168 tests, both linters, all four fleet rules and an injected-fault
  control. The checkpoint records the test cost and method changes.
  [FFmpeg-build report](https://github.com/laputa-systems/ffmpeg-build/pull/77) ·
  [Tier A checkpoint](deslop-scorecard.md#tier-a-checkpoint)

- CMake-build moved to the fleet's minimal Alpine 3.24.2 builder after
  Edge retired its locked OpenSSL APK. Both exact archives passed native
  qualification, size and memory budgets. Stuff removed CMake's Edge
  exemption and checks both the offline APK closure and the qualification
  OpenSSL APK. The general check detects explicit Edge bases and APK
  repository overrides in Dockerfiles without a musl marker. It also
  checks direct writes of Edge URLs to `/etc/apk/repositories` and Edge
  images declared in GitHub Actions job containers, services and Docker
  actions. The workflow check found no Edge images in 44 in-scope
  checkouts. The exact Doas default revision passed the builder rule.
  [Stable builder](https://github.com/laputa-systems/cmake-build/pull/24) ·
  [Exact qualification](https://github.com/laputa-systems/cmake-build/actions/runs/44354687939) ·
  [Fleet policy](https://github.com/laputa-systems/stuff/pull/117) ·
  [Edge detection](https://github.com/laputa-systems/stuff/pull/120) ·
  [Repository redirects](https://github.com/laputa-systems/stuff/pull/128) ·
  [Workflow images](https://github.com/laputa-systems/stuff/pull/143)
- CMake-build now checks three strict typing rules. The bootstrap parser
  returns the same 36 validated inputs in order for each architecture.
  The input suite caught all 172 selected parser mutations.
  [Controller types](https://github.com/laputa-systems/cmake-build/pull/27) ·
  [Bootstrap tests](https://github.com/laputa-systems/cmake-build/pull/28)
  The controller workflow now reuses native build phases across controller
  test edits. At the same revision, phase preparation took 541 seconds cold
  and 24 seconds after restoring the verified caches. Both runs passed all
  128 controller tests in 21 modules.
  [Cache trial](https://github.com/laputa-systems/cmake-build/pull/30)
  The phase-record suite caught 169 of the same 184 mutations, up from
  129. The default native job passed all 130 controller tests. CMake also
  removed three unused fields from the in-memory bootstrap record and
  retained the lock validation.
  [Phase records](https://github.com/laputa-systems/cmake-build/pull/32) ·
  [Bootstrap record](https://github.com/laputa-systems/cmake-build/pull/31) ·
  [Dead-code scan](https://github.com/laputa-systems/cmake-build/pull/33)
  The archive tests caught 291 of the same 327 mutations, up from 260.
  The latest controller and lint runs passed on main, including all 134
  controller cases.
  [Archive admission](https://github.com/laputa-systems/cmake-build/pull/34) ·
  [Deterministic metadata](https://github.com/laputa-systems/cmake-build/pull/35)
  The input and phase fixtures caught 455 of 568 input mutations. The
  tree digest cases independently change file mode, link target and
  nested paths. The whole-change trial proved mixed test deletion and
  source-change selection locally.
  [Whole-change trial](https://github.com/laputa-systems/cmake-build/pull/36) ·
  [Tree digest cases](https://github.com/laputa-systems/cmake-build/pull/37)
  Concurrent cache stores now stage separate copies. The overlapping
  publish fixture reproduced a failed rename on the previous revision.
  Both writes and the retry after changed source bytes pass.
  [Concurrent cache stores](https://github.com/laputa-systems/cmake-build/pull/38)
  The filesystem fixture caught 34 of 38 cache-store identities. It
  detects staging outside the destination filesystem.
  [Cache staging](https://github.com/laputa-systems/cmake-build/pull/39)
  The sealed controller coverage run passed all 137 cases and measured
  1,995 of 3,161 statements and 534 of 972 branches across 26 files.
  The retained `make coverage` command stages a verified CPython 3.15.2
  runtime and the mirrored musl Coverage.py wheel in the network-sealed
  native builder. On x86-64, all 146 tests passed and subprocess data
  contributed to the 2,003 of 3,158 statements and 541 of 968 branches
  measured. The focused ARM64 run passed all 36 input tests and covered
  104 of 106 input branches.
  [Retained command](https://github.com/laputa-systems/cmake-build/pull/51) ·
  [Native result](https://github.com/laputa-systems/cmake-build/actions/runs/44445064389)
  The bootstrap metadata cases caught all 99 identities in the matched
  parser scope, up from 81. A persisted tree digest fixture caught 70
  of 72 changes, up from 44. The two remaining edits preserve sibling
  ordering on the supported POSIX platforms.
  The matched input suite caught 518 of 571 after adding offline fetch,
  lock diagnostics and archive publication cases. A later failed-rename
  fixture verified staging cleanup and retry and caught two more
  publication changes in the focused selection.
  [Coverage baseline](https://github.com/laputa-systems/cmake-build/pull/41) ·
  [Bootstrap metadata](https://github.com/laputa-systems/cmake-build/pull/42) ·
  [Tree digest](https://github.com/laputa-systems/cmake-build/pull/43) ·
  [Input boundaries](https://github.com/laputa-systems/cmake-build/pull/44) ·
  [Extraction retry](https://github.com/laputa-systems/cmake-build/pull/45)
- Doas-rs moved its test and build image to the same stable base with four
  direct APKs and checksum-verified Rust tooling. All 166 tests passed on
  native ARM64 and on local emulated x86-64. Both release binaries were
  static and printed help offline. The follow-up scan of Dockerfiles,
  workflows, shell scripts and build locks found no explicit Edge
  references across the 46 campaign checkouts checked.
  [Doas-rs #7](https://github.com/laputa-systems/doas-rs/pull/7)
  Doas also adopted Clippy's redundant clone and needless pass-by-value
  checks. The baseline failed both checks. The candidate passed lint and
  all 166 ordinary tests offline on ARM64, and hosted CI passed on main.
  [Ownership checks](https://github.com/laputa-systems/doas-rs/pull/8)
  The native x86-64 KVM checks passed for restricted execution,
  unprivileged config checks, identity transitions, and clearing absent
  or unavailable approval state. Diagnose is complete. Live password
  entry and the ARM64 guest still need evidence.
  [Guest harness](https://github.com/laputa-systems/doas-rs/pull/10) ·
  [Diagnosis](https://github.com/laputa-systems/doas-rs/pull/11) ·
  [Clear status](https://github.com/laputa-systems/doas-rs/pull/13)
  Types is complete. The path check and C-string literals removed
  nine unwraps, and native x86-64 KVM passed all four guest markers.
  The ordinary ARM64 Alpine `make coverage` run passed all 166 tests
  and measured 3,113 of 4,323 lines and 500 of 1,006 branches.
  The CLI cases raised the matched catches from 37 to 43 of 53.
  Five repeated option-index timeouts remain open.
  Config-check errors now name the fragment and its local line.
  [Types](https://github.com/laputa-systems/doas-rs/pull/14) ·
  [Branch coverage](https://github.com/laputa-systems/doas-rs/pull/15) ·
  [CLI admission](https://github.com/laputa-systems/doas-rs/pull/17) ·
  [Fragment diagnostics](https://github.com/laputa-systems/doas-rs/pull/18)
- FFmpeg-build passed all seven supported Linux profile and target
  combinations and the three ARM64 macOS profiles. The local macOS
  check used Xcode 27.2. The report records the packaged consumer tests
  and all ten archive digests. The stage reader now diagnoses malformed
  toolchain and runtime library metadata. The expanded audit fixture
  caught 386 of 696 before the library-record cases.
  [FFmpeg-build #35](https://github.com/laputa-systems/ffmpeg-build/pull/35) ·
  [Stage metadata](https://github.com/laputa-systems/ffmpeg-build/pull/40) ·
  [Library metadata](https://github.com/laputa-systems/ffmpeg-build/pull/41)
- Pi-build rebuilt both profiles byte for byte on x86-64 and ARM64 Linux.
  Regular CI now verifies the companion inventory and package identities.
  Vendor tests exercised all 545 mutation identities, with 537 caught
  on macOS, one Linux casefold control and seven scoped equivalents.
  The retained changed-path Python gate accounted for all 1,427
  identities. Its actual mixed pull request caught the archive
  test-deletion fault. The build-tools pass settled on November 18 after
  a fresh 77-test check-up, all four companion fixtures and the fleet
  checks. Two-host Intercom remains in owner ticket DSLP-9.
  [Pi-build #34](https://github.com/joshuarli/pi-build/pull/34) ·
  [Pi-build #35](https://github.com/joshuarli/pi-build/pull/35) ·
  [Pi-build #36](https://github.com/joshuarli/pi-build/pull/36) ·
  [Pi-build #42](https://github.com/joshuarli/pi-build/pull/42) ·
  [Final check-up](https://github.com/joshuarli/pi-build/pull/45)
- Node-build caught all 52 selected Doctor mutations and the
  case-sensitive assembly fault. The native artifact trial exercises
  macOS ARM64 and Linux x86-64 with the existing release inputs. Both
  Node 26.12.1 archives passed 18 smoke cases and both size budgets.
  The Linux job took 1 h 54 min and the macOS job took 2 h 1 min.
  [Node-build #36](https://github.com/laputa-systems/node-build/pull/36) ·
  [Native qualification](https://github.com/laputa-systems/node-build/pull/38)
  The archive budget command now rejects malformed byte ceilings through
  its exit 2 diagnostic. Tests exercise archives at exact limits, and
  the revised scope caught 78 of 81 mutation identities on macOS. Two
  case-sensitive Linux controls caught two more. One tar mode is equivalent.
  The reference comparison now diagnoses a failed version probe.
  Its focused suite caught 132 of 177 changes.
  [Budget validation](https://github.com/laputa-systems/node-build/pull/39) ·
  [Case-sensitive controls](https://github.com/laputa-systems/node-build/pull/40) ·
  [Reference comparison](https://github.com/laputa-systems/node-build/pull/41)
  The release census caught 350 of 395 identities and identified the
  unused single-target wrapper. Both Git queries now report timeouts
  through assembly exit 2 before creating output. The assembly result
  declares the three fields used by the CLI.
  [Release census](https://github.com/laputa-systems/node-build/pull/42) ·
  [Git timeouts](https://github.com/laputa-systems/node-build/pull/43) ·
  [Assembly result](https://github.com/laputa-systems/node-build/pull/44)
- Mdevd-rs now selects live consumer exchange explicitly. All 64
  ordinary tests passed with ten opt-in cases ignored. Native KVM passed
  node creation, framed output, coldplug and shutdown. The pinned C consumer
  observed add, change and remove events in its private namespace. Added
  tests caught all 20 selected event and pipe mutations and all 14 selected
  node-path mutations on ARM64. The engine now warns and skips node
  operations for an explicit empty name. The storm and idle resource
  gates passed on stable ARM64 Alpine.
  [Event records](https://github.com/laputa-systems/mdevd-rs/pull/16) ·
  [Node path limits](https://github.com/laputa-systems/mdevd-rs/pull/17) ·
  [Native guest](https://github.com/laputa-systems/mdevd-rs/pull/19) ·
  [Consumer exchange](https://github.com/laputa-systems/mdevd-rs/pull/21) ·
  [Empty device names](https://github.com/laputa-systems/mdevd-rs/pull/26)
  The parser boundary cases caught three additional mutations. The report
  traces the two remaining early-capture identities through the parser
  table. [Parser boundary cases](https://github.com/laputa-systems/mdevd-rs/pull/23)
  Both binaries handle invalid UTF-8 through usage exit 100. The sysfs
  tests exercise complete device-number fallback and actual node decisions
  from unterminated device-name records. They caught two further mutations
  at the name limit.
  [CLI admission](https://github.com/laputa-systems/mdevd-rs/pull/24) ·
  [Sysfs cases](https://github.com/laputa-systems/mdevd-rs/pull/25)
- The cleanup follow-ups retired 22 more completed worktrees with
  4,927,332 KiB of measured allocation. The
  [cleanup record](deslop-cleanup-20261117.md) includes the
  shared-volume measurements and the retired paths.
- Stuff #111 retains Pi-build and Node-build's coverage recipes and
  qualified type settings. Hi-lite added coverage through Make and
  tested the public bracket scan limit and UTF-8 display mapping. Its
  pinned XSH vocabulary passed regeneration, the editor display suite
  and paired native Linux ARM64 timing.
  [Hi-lite #18](https://github.com/laputa-systems/hi-lite/pull/18) ·
  [Pinned XSH](https://github.com/laputa-systems/hi-lite/pull/19)
  The diff preview handles `usize::MAX` context and reinitializes the
  alignment-table boundaries when reusing scratch storage. Both measured
  ARM64 diff workloads passed. The diff tests caught 21 more mutations
  across the matched census and survivor rerun. The language detector
  cases caught six faults across shebangs and Objective-C suffixes.
  [Full-range preview](https://github.com/laputa-systems/hi-lite/pull/20) ·
  [Diff cases](https://github.com/laputa-systems/hi-lite/pull/21) ·
  [Language detection](https://github.com/laputa-systems/hi-lite/pull/22)
  The full language-module selection caught 25 of 30 identities.
  Five failed to compile with E0277. Rust token boundary cases caught
  five more in a separate matched selection.
  [Language-module census](https://github.com/laputa-systems/hi-lite/pull/23) ·
  [Rust token cases](https://github.com/laputa-systems/hi-lite/pull/24)
- Fz passed the scoped fleet checks and the CLI failure control. The
  first full hosted comparison had six timing rows outside baseline spread.
  The identical-binary control had one such row in a different workload.
  The independent repeat stayed within the bound. Immediate interleaving
  resolved the small-input row, and the exact release candidate passed
  the full ish suite. The default checks passed and DSLP-10 is closed.
  [Fz #47](https://github.com/laputa-systems/fz/pull/47) ·
  [Repeat](https://github.com/laputa-systems/fz/actions/runs/44422469442) ·
  [Focused trial](https://github.com/laputa-systems/fz/actions/runs/44423775482) ·
  [Settlement](https://github.com/laputa-systems/fz/pull/48)
  Diff-pretty added
  workspace branch coverage through Make. Its PTY tests exercise
  restoration on SIGTERM, raw-mode transitions and EOF. Terminal key
  and signal fixtures caught 22 of 23 targeted mutations. The workspace
  passed 94 tests and one doctest.
  Two later session cases caught both targeted changes to EOF handling
  and scroll clamping after a filter change. Search recentering and
  filtered input then caught five additional injected changes.
  [SIGTERM](https://github.com/laputa-systems/diff-pretty/pull/42) ·
  [Terminal tests](https://github.com/laputa-systems/diff-pretty/pull/43) ·
  [Session tests](https://github.com/laputa-systems/diff-pretty/pull/44) ·
  [Search selection](https://github.com/laputa-systems/diff-pretty/pull/45)
  Stuff
  [#106](https://github.com/laputa-systems/stuff/pull/106) checks qualified
  strict settings from policy, and
  [#107](https://github.com/laputa-systems/stuff/pull/107) retains Loc's
  shebang workflow after removal of the campaign backlog.
- Buildlib [#26](https://github.com/laputa-systems/buildlib/pull/26) and
  Diff-pretty [#31](https://github.com/laputa-systems/diff-pretty/pull/31)
  merged after their positive matrices and four hosted controls each.
  Stuff [#65](https://github.com/laputa-systems/stuff/pull/65) registered
  retention for Buildlib and fz. Vault
  [#30](https://github.com/laputa-systems/vault/pull/30) still has exhausted
  shards. A separate branch preserves partial outcomes on expiry.
- Stuff #55–67 merged on green. Repomod Types is complete. The
  [path admission witness](https://github.com/laputa-systems/stuff/pull/64)
  passed all ten hosted checks. The
  [fixer publication tests](https://github.com/laputa-systems/stuff/pull/67)
  check that refused pushes and PR creation failures preserve the expected
  local and remote Git state. The whole-change lane remains open.
- Pytest-parallel [#26](https://github.com/joshuarli/pytest-parallel/pull/26)
  fixed empty-address binds in a real worker. Its wheel passed Stuff's
  repomod tests and reproduced Toolbox's FFmpeg baseline failure.
  Fastermod's Ground evidence and saved-plan finding landed in
  [#28](https://github.com/laputa-systems/fastermod/pull/28) and
  [#29](https://github.com/laputa-systems/fastermod/pull/29). Ptytest's deadline
  repair and shared Make entry points both passed Linux and macOS and merged.
  [Ptytest #13](https://github.com/laputa-systems/ptytest/pull/13) ·
  [Ptytest #14](https://github.com/laputa-systems/ptytest/pull/14)
- Ptytest [#15](https://github.com/laputa-systems/ptytest/pull/15) preserves
  the original diagnostic bundle through cleanup. Hosted PTY acceptance and
  the focused fz, tm and lz consumer checks passed. The recorded e and ish
  failures reproduced before and after the patch.
- Loc [#18](https://github.com/joshuarli/loc/pull/18) merged its historical
  mutation follow-up after macOS, both musl architectures, lint and LineJudge
  passed. The wider Tests gate remains open.
- Extensions [#15](https://github.com/joshuarli/extensions/pull/15) merged
  the type-aware lint and installed Chromium checks on green. #16 updates DSLP-4.
- STUF-91 records Solid 2.0 candidates for Stats and bctl. The owner
  approved exact-version age exemptions for the locked Solid packages.
  Frozen installs pass, and Stats #23 merged on green. The dashboard library still needs stable versions
  in its configured mirror.
- Public Cargo, npm and PyPI reads recovered. Stats
  [#24](https://github.com/joshuarli/stats/pull/24) passed all three checks and
  merged. [#25](https://github.com/joshuarli/stats/pull/25) recorded the legacy
  migration outcome and bounded the component work. Linux reruns uncovered
  a dev-launcher shutdown race and a producer port collision. Both repairs
  merged after all hosted checks passed.
  [Stats #27](https://github.com/joshuarli/stats/pull/27) ·
  [Stats #26](https://github.com/joshuarli/stats/pull/26)
- Repomod's catalog tests caught 52 of 60 selected identities, up from 39.
  The eight survivor dispositions and reproduction commands are in the
  [catalog evidence](../deslop-catalog-admission.md). Stuff
  [#70](https://github.com/laputa-systems/stuff/pull/70) registered diff-pretty's
  hosted mutation gate after [diff-pretty #40](https://github.com/laputa-systems/diff-pretty/pull/40)
  verified the retained Make entry point on both platforms.
- Fastermod and Ptytest completed Diagnose. Fastermod fixed terminal
  `--plan` routing in [#31](https://github.com/laputa-systems/fastermod/pull/31).
  Its text source read error repair passed tests, lint and five paired
  workload checks before merging.
  [Fastermod #30](https://github.com/laputa-systems/fastermod/pull/30) ·
  [Fastermod #32](https://github.com/laputa-systems/fastermod/pull/32) ·
  [Ptytest #16](https://github.com/laputa-systems/ptytest/pull/16)
- The owner excluded Discover from deslop while rearchitecting it.
- The owner excluded Chromium-build on November 19. Its offline APK
  verification remains part of the campaign record.
- The owner excluded Vault and Pi-build on November 19, after Vault's
  Report and Pi-build's size check landed. Their open tickets stay in their
  backlogs without campaign work.
- The [checkout cleanup](deslop-cleanup-20261117.md) retired 18 integrated
  worktrees under `~/repos` and cleared verified stale build targets and
  fixtures.
- Pytest-parallel merged file-hook regressions and retained its whole-change
  trial in [draft #32](https://github.com/joshuarli/pytest-parallel/pull/32)
  after the aggregate exhausted the coordinator budget. The stop and
  cleanup fixtures caught 114 of 167 changes. The monitor now uses its
  deadline as the only stop state. The installed wheel passed 1,500
  repomod tests with three skips.
  [Stop and cleanup](https://github.com/joshuarli/pytest-parallel/pull/41) ·
  [Deadline state](https://github.com/joshuarli/pytest-parallel/pull/42)
  Stats merged
  coverage evidence, a target-policy fixture repair and shared decoder
  cases. See the [successor results](deslop-m2.md#successor-results).
- Extensions passed the two hosted scopes on
  [draft #22](https://github.com/joshuarli/extensions/pull/22). The
  remaining critical source and platform boundaries stay in its Tests
  scope.
- The owner approved the full campaign and unattended decisions. The
  tier checkpoints still require evidence during rollout. The roadmap records
  the remaining qualification conditions and deferred work.

[Historical status](deslop-status-20261117.md) preserves the pause chronology
and earlier results.

## How the campaign runs

The campaign has two kinds of workers.

- **The campaign agent** runs from this doc in `stuff`. It owns every shared file: repomod rules and
  fleet policy in `stuff`, and the skills and `todo` tool in `usr`. It runs the foundations, the
  pilots, the seeding of tickets, the check-ups, and the method revisions.
- **Repo agents** are dispatched by the owner, one per repository. Each works that repository's
  `TODO-DESLOP.md` with the `deslop` skill and touches nothing outside that repository. Repositories
  are disjoint, so any number of repo agents can run at once.

The method is proven at small scale, then on complex repos, before it is handed out. Phases 1 and 2
are run by the campaign agent itself. Phase 3 starts only when the owner approves the calibration
report. From phase 3, the campaign agent seeds one size tier at a time. It checks up on the
settled repositories and folds what they learned into the skill before it seeds the next, larger
tier.

## Charter

- Decide and keep going. Record a decision here only when a later slice depends on it.
- Every campaign PR carries the `deslop` label (owner request, 2026-11-15). Create it first with
  `gh label create deslop -R <repo> --color 5319e7 --force`.
- Work inside the grant in **Execution boundary**. A plan does not supply missing permission. Park
  an item that needs authority outside the grant and list it under **Needs you** in Status.
- Fix the cause before you retry. A failing item gets two attempts after `root-cause`. Then park it
  with its cause and a retry condition.
- Fix egregious problems met on the way in their own commit, and record everything else as a
  ticket. Egregious means: an existing test suite that CI never runs, a test that fails on the
  default branch, or a `make test` slower than 5 minutes warm that has a clear drag cause.
- Correctness before cleanup. The method orders types and tests ahead of dead code and refactors.
  The perf gate applies from the first refactor slice.
- Shared files have one writer, the campaign agent: `repomod/`, `fleet/`, `docs/tagging.md`, the
  `usr` skills, and `usr/tools/todo`. Repo agents report gaps in those files in their `## Report`.
- Lanes the campaign agent delegates follow `orchestrate`, in worktrees under `.work/wt/<lane>`.
- Commits are Conventional Commits. The scope is the component, and the body carries the item ID
  (`deslop F2`, or `DSLP-4` in a repo). Code comments never cite this doc or a ticket.

## Decisions

### Owner (2026-11-14)

1. **Scope.** Rust, Python, and TypeScript code in the in-scope repositories (Reference). Vendored
   code counts, but only code we have modified is deslopped. Pristine vendored trees and pristine
   upstream code in forks are left alone.
2. **Excluded:** xsh, laputa, python-build, and bctl (under heavy development elsewhere), and deser.
   Discover and Chromium-build are also outside the campaign by owner decision.
   Also excluded are the forks that are effectively upstream: rg, rawzip, zlib-rs, lexopt, rustls, and
   webpki.
3. **Forks in scope,** limited to our changes against their upstream merge base: jaq, rust-fontconfig,
   rustix, rage, fd, oxish, crabtables, soulseek-rs. They get a new `fork-diverged` catalog tag (F1).
4. **Enforcement is ordinary checks plus small critical mutation checks (revised 2026-11-19).**
   CI runs `make test`, typing and lint in every in-scope repository, plus the relevant native,
   browser, consumer and performance checks. Mutation is blocking only for a small, demonstrated
   scope around an important contract: archive admission, cache integrity, atomic publication,
   success and failure reporting, cleanup, or an authorization decision. Inside that scope a
   survivor fails the check unless the repo's mutation config lists it with a reason, and deleting
   or weakening a protecting test, including in a mixed source and test change, reopens that same
   small scope. A test or configuration change never expands to mutation of a whole package.
   Broad module sweeps, extra operators and wider platform matrices are advisory audits, run when
   invoked or when reviewing a risky change. Their results are evidence of test sensitivity, not
   a count of defects, and a pass needs no exhaustive mutation qualification. Records state which
   guarantees required checks enforce and, separately, which scope advisory audits investigated.
   Coverage is measured and reported, but it is never a gate or a threshold.
5. **Merging.** One PR per slice. The agent merges it when required CI is green and the slice's
   acceptance command passed. Work parked for the owner stays unmerged.
6. **Removals.** Behavior-preserving cuts land on their own. Removing live behavior or a public
   contract (a CLI flag, a public API, a compatibility path, a format) is a walk-back. It is filed as
   a ticket whose area starts with `Needs owner ·`, and the owner reviews those at each tier
   checkpoint.
7. **Fan-out through tickets.** After the method works, the remaining work is filed as tickets in a
   per-repo `TODO-DESLOP.md`, separate from `TODO.md`, so the owner can dispatch repo agents. The
   campaign checks each repository after its tickets settle.
8. **Fan-out needs approval.** Phase 3 starts only after the owner approves the calibration report
   (Phase 2). Until then the tooling must be proven on complex repos, not only small ones.
9. **Mirroring (2026-11-15).** The campaign agent may mirror the assurance dev tools to the stuff
   registries with `stuff publish mirror`: mutmut, cosmic-ray, vulture, deptry,
   `@stryker-mutator/core`, `@stryker-mutator/vitest-runner`, knip, and `@vitest/coverage-v8`,
   at pinned versions after vetting license and transitive dependencies. Nothing else is published.
10. **Unattended to the end (2026-11-15).** The owner is away and expects the campaign to finish
    with tickets filed in every applicable repository. Filing tickets is not fanning out:
    dispatching repo agents stays the owner's act. The campaign agent therefore finishes the
    pilots, extracts the `deslop` skill, runs as much complex calibration as it can, and then seeds
    `TODO-DESLOP.md` in every in-scope repository without waiting for approval. Status records how
    far calibration got, so the owner can judge when to dispatch. This supersedes decision 8's
    approval gate for seeding, not for dispatch.
11. **Skills.** Skill development in `usr` is in scope. The skills are where the campaign's lessons
   end up. Repo agents follow them, and they outlive the campaign. `test-audit` changes its position
   on line coverage first (K1).
12. **toolbox is out of scope (2026-11-15).** It is private, and GitHub starts no Actions job there
    (the account's payments or spending limit), so no PR can merge on green. Its `TODO-DESLOP.md`
    stays; an unpushed local branch in `~/d/toolbox` fixes its Linux ffmpeg install condition.
13. **Assurance hardening before broader dispatch (2026-11-15).** Repair the pilot defects, qualify
    the enforcement and mutation gates with negative controls, keep retention eligibility in fleet
    policy, make the `deslop` skill the one procedure, and measure readiness per language before the
    next dispatch batch.
14. **Benchmarks join the pass (2026-11-19).** Every in-scope repository runs the `bench-pyramid`
    skill as the deslop Bench step, after Dead code and before Findings. Where a repository has
    benchmarks, it gets the skill's entrypoint (`make bench`, `bench-check`, `bench-list`, tier
    and workload selectors, preflight) built on its existing harness. A repository without
    benchmarks records its outcome list and files the gaps as tickets, ranked by the risk of a
    missed regression. Agents never run the Full tier; it stays a manual owner request. Already
    settled repositories get a Bench ticket and settle again once it closes. Excluded
    repositories stay excluded.

### Prescribed

- **Fan out by size tier, not all at once.** The method must work at each scale before larger repos
  get it. Seeding tier N+1 waits until three repos of tier N have settled (or all of them, if the
  tier has fewer) and their feedback is in the skill. Stragglers keep working.
  *Reversed if* the tier B checkpoint changes nothing in the skill. Then seed C, D, and E together.
- **Repos over 50k lines are worked by component.** Ground and Diagnose cover the whole repo. Types,
  Tests, and Dead code run per component (a crate, a package, or a subsystem of at most about 20k
  lines), one PR each. The Ground ticket lists the components.
- **Tool recipes** (mutation, coverage, dead code, strict-profile candidates, escape-hatch counts)
  live in the deslop skill's [tools reference](https://github.com/joshuarli/usr/blob/main/dotfiles/base/.agents/skills/deslop/references/tools.md).
- **Joining `make lint`:** a dead-code tool joins a repo's lint only when the repo is clean under it
  with an allowlist of at most 5 entries, each with a reason.
- **A strict-profile setting joins the fleet profile only on evidence.** On pilot repos it must have
  rejected at least one real defect or deleted at least one escape hatch, while needing at most one
  false-positive suppression per 5k lines.
- **The perf gate covers perf-sensitive repos.** These are the rustybench repos (fastermod, lz, loc,
  e, ish) and any repo whose Ground ticket declares a workload. The gate runs on every refactor
  slice and on the repo's final state. Measure only when `perf-gate-ready` passes, with at least 5
  interleaved baseline/candidate pairs of the shipped profile.
  - **Within bound:** the median delta is under the observed spread or under 2%.
  - **Material regression:** the slice parks.
  - **Deferred (host busy):** the slice stays unmerged. It never passes by default.
- **Test cost budget.** A Tests step may raise warm `make test` time by at most 20% or 30 seconds,
  whichever is larger. Repos already slower than 5 minutes warm fix their drag first.
- **Mutation spending is bounded (2026-11-19).** A new or expanded mutation trial gets 10
  aggregate runner-minutes, counting every job, shard, platform and retry. Exceeding it needs a
  named important unresolved behavior, a finite experiment and its expected value, recorded
  before the run. Platform-specific behavior runs on its platform; portable mutation runs once
  unless a platform difference is demonstrated. Ordinary supported-platform CI is unchanged.
  After two successive bounded trials that protect no distinct important behavior, stop
  expanding the scope and record a short disposition in the existing report. Budget exhaustion,
  timeouts and unrun scopes are incomplete evidence, never passes. Known important defects and
  failures of required critical checks still block. Selection and result accounting follow the
  test-audit mutation reference.
- **Libraries.** Changes to a published or consumed library (smolith, ptytest, hi-lite, rustybench,
  laputa-ui-dashboard, buildlib, pytest-parallel) also run their known consumers' tests against the
  candidate, using `repomod deps` to find consumers. Repos stay disjoint because consumers pin
  released versions. The campaign publishes nothing.

### Delegated

- **Merge style.** Follow each repo's recent merged PRs. Pin the merge to the head SHA
  (`gh pr merge --match-head-commit`).
- **Combined PRs.** Ground and Diagnose may share one PR in repos under 5k lines.
- **Per-repo perf workloads.** A repo agent declares one only for a user-visible hot path (a CLI's
  main operation, a server route, a parser). It records "none" with a reason otherwise.
- **Where pins live.** Assurance tool pins go in the existing `fleet/policy/python-tools.toml` and
  `typescript-tools.toml`. Add `fleet/policy/rust-tools.toml` only for the cargo tools.

## Baseline

Measured 2026-11-14 on this host, in disposable clones under `.work/tmp/deslop-baseline`, with
`TMPDIR=.work/tmp`.

| Repo | Base | `make test` cold / warm | `make lint` | Known red |
| --- | --- | --- | --- | --- |
| srv | `dcc7921` | 5s / 0s | 1s | none |
| fastermod | `64cdc84` | 8s / 1s | 2s | none |
| buildlib | `6ef86b9` | 6s / 6s | 0s | none |
| pytest-parallel | `b94019e` | 9s / 7s | 1s | `tests/test_campaign.py::test_hooks_weights_groups_and_pin_via_plan` fails when `TMPDIR` is under a repo's `.work/tmp` and passes with the system `TMPDIR`. This is an isolation defect, and the fleet convention requires that `TMPDIR`. |
| extensions | `ac4f9d4` | 10s / 6s | none | No `lint` target and no lint workflow |

Fleet facts the plan relies on:

- The fleet standard requires a lint workflow running `make lint` (`repomod/rules/lint.py`). No rule
  requires CI to run the tests.
- stuff's CI never runs the repomod pytest suite. `make test` includes `repomod-test`
  (`Makefile:17`), but CI calls `cargo test --locked` directly (`.github/workflows/ci.yml:39`).
- stuff's CI run 43684749647 took 35m40s for the Rust test step on macOS (`xcode-27`) and 2m13s on
  Linux.
- No assurance tool is installed on this host: none of cargo-llvm-cov, cargo-mutants, cargo-machete,
  cargo-udeps, vulture, mutmut, or knip.
- Mutation prior art exists only in kache, as a local target: `make mutants-diff` with cargo-mutants
  27.1.0 and `.cargo/mutants.toml`. Its comment at `Makefile:95` says CI runs it, but no workflow
  references it.
- Five repos keep a rustybench baseline in `benches/baseline.json`: fastermod, lz, loc, e, and ish.
- extensions already depends on `@vitest/coverage-v8`. stuff and toolbox run Python tests through
  `pytest-parallel`, which has no coverage support.
- The `todo` CLI only finds `TODO.md` (`usr/tools/todo/src/todo.py:22`).
- The catalog tag set is closed (`repomod/catalog.py:47`).
- Canonical checkouts are blob-less partial clones. Fetching upstream into a local clone needs
  `--refetch`.

## Sequence

### Phase 0: foundations (campaign agent, serial)

| ID | Repo | Owns | Deliverable | Acceptance |
| --- | --- | --- | --- | --- |
| F1 | stuff | `repomod/catalog.py`, `docs/tagging.md`, `tests/repomod/`, `fleet/catalog.toml` (the tag only) | The `fork-diverged` tag is valid only together with `fork`. Tag the eight in-scope forks and run `topics apply` for them. | `make repomod-test`. `uv run repomod lint --rule topics --tag fork-diverged` lists exactly the eight forks with no findings. A catalog entry with `fork-diverged` but no `fork` is rejected. |
| F2 | stuff | `repomod/rules/workflows.py` or a new `rules/test_workflow.py`, `docs/policy-development.md`, `.github/workflows/ci.yml`, tests | Rule `gha-test-workflow`: some workflow runs `make test` or `make test-ci` on pull requests. It applies to non-fork repos and to `fork-diverged` forks. Its fixer adds a test workflow, the same way the lint fixer does. stuff's own CI starts running `make repomod-test`. | `make repomod-test` passes, with a fixture where the workflow calls `cargo test` directly and gets a finding. stuff's CI shows a passing repomod pytest step. |
| K0 | usr | `tools/todo/` | `todo --file PATH` works for every subcommand. Without it, the tool still finds `TODO.md` as before. | usr's todo tests cover `add`, `list`, and `check` against `TODO-DESLOP.md` while a `TODO.md` exists beside it, and each file keeps its own `Prefix`/`Next`. `make skills-check` passes. |
| K1 | usr | `test-audit/SKILL.md` and new `test-audit/references/mutation.md` | Rewrite the Coverage section. Coverage is measured routinely with `make coverage` and used to find unprotected boundaries and dead-code candidates. It is never a gate or a target. Add mutation testing: the result classes (caught, missed, unviable, timeout, budget exhausted), how to disposition a survivor, how to justify an equivalent mutant, test-only diff selection, and fault injection for each new boundary test. | `make skills-check`, with test-audit within the 8000-byte limit. The section says coverage is never a gate and no longer says to drop coverage reports. |

F1 and K0 may run in parallel because they touch different repositories. F2 follows F1. K1 may run
in parallel with F1 or F2.

### Phase 1: pilots (campaign agent; one lane per language, in parallel)

Run the full repo pass (below) on **srv** (Rust), **buildlib** (Python), and **extensions**
(TypeScript). Each pilot also qualifies its language's tools. Pin the tools in the repo, add
`make coverage` and `make mutants-diff`, add the CI mutation lane, and prove the lane with a
negative control: a throwaway PR that adds an unasserted branch must fail the lane. Close the
throwaway PR without merging.

**Checkpoint M1** (campaign agent):

- **F3.** Move the qualified pins into fleet policy. Add rules with fixers where the repair is
  deterministic:
  - `make-coverage-target`
  - `mutants-diff-lane`
  - `strict-typing-profile`, for the settings that met the evidence bar
- **K2.** Write the per-language tool recipes into `test-audit/references/` and
  `dead-code-archaeology`. Include the deletion record that `debloat` and `dead-code-archaeology`
  require.
- Score the pilots (see Checkpoints).

### Phase 2: calibration (campaign agent)

**2a, narrow.** Run the pass on three repos that each test one part of the method the pilots could
not:

- **fastermod:** the perf gate, against a rustybench baseline.
- **pytest-parallel:** coverage across parallel workers (this is new runner support, which unblocks
  stuff and toolbox), plus the known red above.
- **ptytest:** a library with consumers.

Then extract the repo pass into an explicit `deslop` skill in usr (**K3**). Replace the Repo pass
section here with a link to it, and write the ticket template into the skill.

**2b, complex.** Run the pass, using the `deslop` skill, on four repos that stress the tools at the
scale and shape of the larger tiers:

- **loc** (Rust, 12.5k): a real CLI with corpus semantics, a rustybench baseline, and musl and
  macOS artifacts.
- **toolbox** (Python, 18.9k): a pytest-parallel consumer. It proves coverage and mutmut through
  the runner on a real suite.
- **stats** (Rust and TypeScript, 68.4k): component mode, Stryker on a large TypeScript suite, a
  Cloudflare Worker runtime boundary, and cross-language fixtures.
- **stuff, the `repomod/` component** (Python): effect-heavy code (Git, GitHub, filesystem) behind
  fakes, so it proves mutation testing and dead-code tools on code that mostly orchestrates effects.
  The campaign agent already owns stuff's shared files, so this does not break disjointness.

2b's repos may run in parallel lanes, one per repo, after K3.

**Checkpoint M2** writes the **calibration report** into Status. The
report covers:

- For each tool: whether it ran on every calibration repo, its cost (wall time and CI minutes), its
  confirmed yield, and its false-positive rate.
- For each step: its yield against its cost.
- Escaped regressions, if any.
- The method changes made in response.
- A recommendation on whether to fan out, and which tier first.

Qualify each calibration workload or document its concrete blocker.
The owner has approved Phase 3. Continue in tier order once the
checkpoint records the evidence and dispatch prerequisites.

### Phase 3: fan-out (campaign agent coordinates the approved dispatch)

For each tier in order:

1. Sync with `uv run repomod sync`.
2. Roll out the F2/F3 rules to the tier with `repomod fix --repo` for each repo, and merge on green.
3. Seed each repo's `TODO-DESLOP.md` through one PR (Seeding, below), merged on green.
4. Report the tier as ready for dispatch.
5. Check up on each repo as its tickets settle (Check-up).
6. Run a checkpoint once the seeding condition for the next tier is met.

| Tier | Repos (Rust + Python + TS lines from `fleet/loc/v1`) |
| --- | --- |
| A, under 10k | pi-build (0.7k, `tools/` only), ffmpeg-build 2.8k, node-build 2.9k, fz 5.1k, doas-rs 5.4k, mdevd-rs 5.4k, diff-pretty 6.0k, vault 6.2k, cmake-build 7.0k, hi-lite 8.1k |
| B, 10k to 30k | lz 11.1k, rustybench 11.1k, laputa-ui-dashboard 13.8k, tinyland 14.1k, e 20.1k, defuddle-rs 20.7k, gluon 28.7k |
| C, 30k to 80k | ctrs 32.7k, usr 42.2k, img 43.7k, tm 51.6k |
| D, over 80k, by component | ish 89.0k, smolith 118.1k, play 122.4k, tansu 123.2k, stuff 156.1k (components other than `repomod/`), kache 240.1k |
| E, forks (delta only) | jaq, rust-fontconfig, rustix, rage, fd, oxish, crabtables, soulseek-rs |

Two repos share files with the campaign agent and are never dispatched to a repo agent while it is
editing them. **usr** is worked only after K3 and between skill revisions. **stuff** is worked only
when no F item is open.

### Phase 4: close (campaign agent)

1. Check up on every in-scope repo.
2. Run `uv run repomod lint` over the in-scope set, which must be clean for F2/F3.
3. Finish the scorecard.
4. In each repo, move the open P3/P4 tickets from `TODO-DESLOP.md` into `TODO.md` with the `todo`
   tool, then delete `TODO-DESLOP.md`. Do this through one PR per repo, merged on green.
5. Run `ultrareview` on this doc's own deliverables in stuff, roll the lasting rules into
   `docs/fleet.md` and `docs/policy-development.md`, then delete this doc.

## Repo pass

The procedure is the `deslop` skill in usr ([SKILL.md](https://github.com/joshuarli/usr/blob/main/dotfiles/base/.agents/skills/deslop/SKILL.md)).
This doc does not restate its steps. Campaign-specific additions:

- Resolve each repository's canonical checkout under `~/repos` and work in an isolated
  `.work/wt/<step>` there. Keep its primary checkout, branch and existing changes untouched.
  Do not create duplicate host clones under `~/d`. The stuff integrator keeps its existing
  development checkout, as required by its own AGENTS.md.
- A repo agent works only its own repository and reports gaps in shared files in its `## Report`.

## Seeding

Seed each repo's `TODO-DESLOP.md` with `todo --file TODO-DESLOP.md`, using the prefix `DSLP`. The
seeded tickets are DSLP-1 through DSLP-5, one per step (Ground, Diagnose, Types, Tests, Dead code).
Each one carries:

- **Problem:** the repo-specific facts the campaign agent already has. These are the baseline times,
  the known reds, the components, the vendored trees, the consumers, and whether the perf gate
  applies.
- **Recommendation:** run the `deslop` skill's step, followed by its acceptance command.
- **Fix with:** `deslop`.

The file opens with three lines saying that one agent works the file and takes the lowest-numbered
open ticket whose area does not start with `Needs owner ·`, that steps 6 and 7 follow DSLP-5, and
that `## Report` sits in the header above `## Tickets`. Owner items use the area prefix instead of
a heading, and the Report stays in the header, because `todo fmt` reorders tickets around fixed
free text and `todo add` appends after the last ticket's trailing text. Findings that steps 2 to 5 discover are appended as DSLP-6 and later, so ticket order still
matches step order. Fleet-wide or shared-file work never becomes a repo ticket.

## Check-up

A repo is **settled** when all of these hold:

- DSLP-1 to DSLP-5 and the Bench ticket are closed.
- No P1 or P2 ticket is open, except owner items (area `Needs owner ·`).
- `## Report` is complete.
- CI is green on the default branch.
- `uv run repomod lint --repo <repo>` is clean for the F2/F3 rules.

The campaign agent then:

1. Re-measures Ground's numbers on the default branch in a fresh clone.
2. Runs the perf gate for perf-sensitive repos against the base SHA.
3. Spot-checks one boundary test with an injected fault.
4. Copies the Report into the scorecard.
5. Moves the repo's `Needs owner ·` items into Status.

A repo that fails a check-up gets a new ticket. It is not settled.

## Checkpoints

A checkpoint runs at M1, at M2, and before each tier after A is seeded. It reads the scorecard and
the Reports.

- **Yield versus cost, per step and per tool.** A step or tool with zero confirmed yield across
  three or more repos is narrowed or cut from the skill. A dead-code tool whose reviewed findings
  are more than half false positives drops to discovery-only. Confirmed yield means a real defect
  fixed, a distinct important behavior newly protected, an escape hatch deleted, or a meaningful
  reduction in complexity. A killed mutant is evidence, not yield by itself. Mutants exposing the
  same missing assertion are one finding. Classify each result as a defect reproduced in the
  unmodified program, a meaningful test gap exposed by an injected fault, an equivalent,
  redundant, cosmetic or low-priority variation, or a harness, environment or infrastructure
  failure. Credit a product fix to mutation only when the record shows mutation found it.
- **Escapes.** A regression later traced to a campaign PR gets `root-cause`, a guard (a test, a
  rule, or a skill rule), and a method change, all before the next tier is seeded.
- **Skill revision.** Each feedback item that recurs in two or more Reports becomes a rule in
  `deslop`, `test-audit`, `typing-audit`, `debloat`, or `dead-code-archaeology`. Each new rule cites
  the repo and PR where the slop got through. `make skills-check` must pass.
- **Owner batch.** Walk-backs and contract changes go into Status under **Needs you**, each with a
  recommendation. They do not block the next tier.
- **Report briefly** in the existing scorecard: product defects fixed and important behaviors
  newly protected, simplifications delivered, mutation scopes retained, narrowed or made advisory
  and why, the actual aggregate runner cost of the trials used, and the remaining concrete risks
  and environment-dependent checks.

## Acceptance

| Deliverable | Proof |
| --- | --- |
| Every in-scope repo has completed the pass | A scorecard row for every repo, with after-values and a check-up date |
| CI runs the tests | `uv run repomod lint --rule gha-test-workflow` has no findings for the in-scope set |
| Critical contracts are mutation-checked | Each repo's required mutation scope names the contracts it protects; `--rule mutants-diff-lane` is clean where a lane is retained, and its negative controls failed as intended. Advisory audit scope is reported separately and is not required for acceptance. |
| Strict typing is enforced | `--rule strict-typing-profile` is clean for the in-scope set |
| Benchmarks answer real questions | Each in-scope repo's Report records its `bench-pyramid` audit; repos with benchmarks have a working `bench-check` and tiered `make bench` entrypoint proven at the Edit and Change tiers |
| Nothing regressed | Every perf-gated repo's final verdict is within bound, consumer tests are green, and escaped regressions number zero or each has a guard |
| The method outlives the campaign | The `deslop` skill exists, and `test-audit` contains the K1 coverage and mutation sections |
| The tickets are gone | No `TODO-DESLOP.md` remains in any in-scope repo |

## Needs environment

These are run by the owner or by CI, never assumed to pass:

- **Linux-only and macOS-only paths.** The CI matrix of each repo is the proof. Local runs here are
  macOS only.
- **Hardware or privileged tests:** doas-rs (setuid), mdevd-rs and tinyland (Linux devices). Repo agents record which boundaries only CI or the owner can exercise.
- **Browser suites:** extensions `test:browser` and tansu's Playwright tests need the pinned browsers.
- **Live services:** stuff's `make test-r2-live` and OpenOrange deployments stay opt-in.
- **Timing.** A perf gate deferred because the host is busy is re-run by the owner on an idle host.

## Execution boundary and non-goals

**Authorized** for the campaign agent, and for repo agents inside their one repository:

- Clones and worktrees under `.work/`.
- Branches, PRs, and merges on green, per owner decision 5.
- CI workflow edits that add the test job and the mutation lane.
- Pinned dev-only tool dependencies from the qualified list.
- `todo` edits to `TODO-DESLOP.md`.
- For the campaign agent only: repomod rule and fixer changes, `repomod fix --repo` for in-scope
  repos once the rule is merged and the canonical stuff checkout is synced, `topics apply` for the
  eight `fork-diverged` repos, and skill and `todo` tool changes in usr.

**Forbidden:**

- Releases and publishing (`repomod release`, `stuff publish`, crates.io, PyPI).
- Edits in canonical checkouts.
- Edits in excluded repos, or in pristine vendored or upstream code.
- Changing the pinned nightly.
- Formatters.
- Force pushes.
- Changes to branch protection or repository settings.
- Persisted or wire format changes.
- Weakening a correct test or a checker setting.
- `repomod fix` against the live catalog while repomod itself is being changed.
- Catalog edits other than F1's tag.

**Contract changes the owner has approved:**

- The new `fork-diverged` tag and its topic.
- The new fleet rules (F2, F3) that report findings on every in-scope repo.
- The test-audit position on coverage.
- `todo --file`.

Every other contract change is a walk-back.

**Non-goals:**

- Go, Swift, Zig, and shell code.
- Performance optimization beyond the bound: speedups are welcome, but they are not targets.
- Coverage percentages as goals.
- A database, dashboard, or workflow framework for tracking.
- Resyncing oxish's vendored copies in ssh-build and xsh.

## Reference

**Scorecard fields.** Each is recorded before and after:

- source lines and test lines
- warm `make test` time
- line and branch coverage
- mutation results on the critical scope (caught, missed, unviable, timeout)
- escape hatches
- dead code removed (lines and dependencies)
- findings filed and fixed, by priority
- perf verdict
- escaped regressions

**Fork divergence**, measured 2026-11-14 against fetched upstream. Code changes since the merge base:

| Fork | Code change |
| --- | --- |
| soulseek-rs | +11.5k/−3.9k |
| crabtables | +9.6k/−0.4k |
| oxish | +4.1k/−2.6k |
| fd | +3.1k/−1.7k (CLI ported to lexopt) |
| rage | +1.9k/−2.5k |
| rustix | +0.2k/−1.5k |
| rust-fontconfig | +0.5k |
| jaq | +55/−237 |
