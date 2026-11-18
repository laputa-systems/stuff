# M2 calibration evidence

This checkpoint records qualification by workload. The [roadmap](deslop-roadmap.md#qualify-meaningful-retained-gates) defines acceptance, and the [scorecard](deslop-scorecard.md) records repository pass state. M2 remains open.

| Shape and workload | Result and exact evidence | Cost and remaining boundary |
| --- | --- | --- |
| Rust HTTP service, Srv request dispatch and rendering | Earlier pass and retained mutation gate on `c9965411`. Draft [#47](https://github.com/laputa-systems/srv/pull/47) accounted for all 376 identities on `289a8fe`. | The hosted shard run caught 322, missed 25, found 17 unviable and confirmed 12 hangs. The 10-minute target and remaining behavioral witnesses are open. |
| Rust performance CLI, Fastermod saved plans and text search | Ground, Diagnose and Types are complete through [#33](https://github.com/laputa-systems/fastermod/pull/33). [#31](https://github.com/laputa-systems/fastermod/pull/31) fixed terminal plan routing. [#32](https://github.com/laputa-systems/fastermod/pull/32) repaired source read diagnostics and merged as `a4040a1a`. | The [paired workload](https://github.com/laputa-systems/fastermod/blob/a4040a1a3b85053397ba4c3d1338e534f74d6f63/docs/deslop-text-source-perf.md) qualifies the repair across all seven named benchmarks, with five pairs inside the observed spread. Both outputs matched. General mutation and the rest of the Tests step remain open. |
| Rust corpus and SIMD CLI, Loc | [#19](https://github.com/joshuarli/loc/pull/19) added a child deadline and caught both previously hanging CLI mutations. [#20](https://github.com/joshuarli/loc/pull/20) at `b45c6f2e` exercises XDG precedence and fallback on both Linux musl architectures. All five hosted checks passed. | The sample retains three comparison alternatives and two counting-helper misses. Finish the critical inventory, cost and whole-change lane. |
| Rust PTY library, Ptytest cleanup and consumers | [#15](https://github.com/laputa-systems/ptytest/pull/15) preserved diagnostics through cleanup and passed focused fz, tm and lz consumers. Diagnose and Types completed through [#17](https://github.com/laputa-systems/ptytest/pull/17). [#19](https://github.com/laputa-systems/ptytest/pull/19) repaired a hosted fixture race, and [#18](https://github.com/laputa-systems/ptytest/pull/18) retains coverage. [#20](https://github.com/laputa-systems/ptytest/pull/20) at `fcb35843` verifies output wait results. | The output wait sample caught five of eight identities, up from two. Two guards are equivalent and one timing-sensitive case remains. All 67 instrumented tests passed at #18. Focused e and ish failures also occur with the pre-repair library. The nightly corpus and whole-change mutation remain separate. |
| Rust platform and hardware, Vault | Linux x86-64 musl, Linux ARM64 musl and macOS ordinary jobs passed on draft [#30](https://github.com/laputa-systems/vault/pull/30) at `0671858b`. The platform union remains unqualified. | Fourteen Linux shards failed and many exhausted the roughly 20-minute job budget. A successor records partial outcomes. Secure Enclave, two-Mac recovery and Linux keyring remain separately scoped. |
| Python library and binary parsers, Buildlib | Qualified bounded workflow and four hosted controls in [#20](https://github.com/laputa-systems/buildlib/pull/20) and [#26](https://github.com/laputa-systems/buildlib/pull/26). Cumulative review caught inconsistent release-manifest serialization from a changing mapping. [#27](https://github.com/laputa-systems/buildlib/pull/27) fixed it at `1497970d` and passed all 17 checks plus five release consumers. | The retained 15-job mutation matrix on #26 used 963 job seconds in one run. Its longest job took 167 seconds. The refreshed release shard caught 319 of 333 selected identities, with the other 14 dispositioned in the release receipt. |
| Python pytest plugin and worker coverage, Pytest-parallel | The installed wheel passed Stuff's consumer suite after [#26](https://github.com/joshuarli/pytest-parallel/pull/26) fixed empty-address bind handling. [#27](https://github.com/joshuarli/pytest-parallel/pull/27) caught all 60 report-emission identities. [#28](https://github.com/joshuarli/pytest-parallel/pull/28) catches an observable truncated-event diagnostic fault. [#29](https://github.com/joshuarli/pytest-parallel/pull/29) at `45b45492` records the remaining active decisions. | The coverage target verified separate worker measurements and passed all 158 tests, covering 1,545 of 1,759 statements and 586 of 718 branches. Linux and macOS ordinary checks passed. The serial whole-change union and its cost and controls remain open. |
| Python orchestration and effects, Repomod | Types and Dead code complete. The [focused dead-code review](../deslop-repomod-dead-code.md) removed two unused items. Workflow expansion caught 55 of 58 with three equivalent cases in [#61](https://github.com/laputa-systems/stuff/pull/61). Real local fetch caught all 25 in [#62](https://github.com/laputa-systems/stuff/pull/62). Catalog admission caught 52 of 60 versus 39 on the base in [#68](https://github.com/laputa-systems/stuff/pull/68). [#74](https://github.com/laputa-systems/stuff/pull/74) repaired snapshot drift handling. | The [snapshot scenario](../deslop-repomod-snapshot.md) caught 110 of 123 in the full selection, six targeted survivors in the follow-up and two filename mutations on a case-sensitive filesystem. The retained whole-change union remains open. [Serial first-party coverage](deslop-roadmap.md#repomod-calibration-inventory). |
| TypeScript Node, browser and MV3, Extensions | Type-aware unsafe-argument lint and installed Chromium landed in [#15](https://github.com/joshuarli/extensions/pull/15). [#17](https://github.com/joshuarli/extensions/pull/17) retains first-party coverage. [#18](https://github.com/joshuarli/extensions/pull/18) keeps nine capture fixtures and the extension lifecycle in one Chromium job. [#20](https://github.com/joshuarli/extensions/pull/20) at `fc55127a` verifies exact parser diagnostics. | The parser caught 178 of the same 179 mutations, up from 139 on the base and 167 at #19. The final survivor is equivalent. The final local run took 7m 34s. TypeScript whole-change mutation and controls remain open. |
| TypeScript Worker and Rust agent, Stats ingest and local stack | [#24](https://github.com/joshuarli/stats/pull/24) verified legacy migration with 41 local passes and all hosted checks. [#26](https://github.com/joshuarli/stats/pull/26) and [#27](https://github.com/joshuarli/stats/pull/27) fixed a producer port collision and SIGTERM shutdown. [#28](https://github.com/joshuarli/stats/pull/28) adds a shared ACK case that catches miscounting in both decoders. [#29](https://github.com/joshuarli/stats/pull/29) at `da022e8b` records the Rust wire type audit. | Ten wire unit tests, five conformance tests and all three hosted checks passed #29. Component-scale TypeScript and Rust critical selection, browser/Worker cost and retained gates remain open. |
| Python and external native tools, Toolbox | Local native-tool and worker coverage passed on [#15](https://github.com/joshuarli/toolbox/pull/15) at `ad9a480`, with FFmpeg 9.0.2, fio 3.42 and the repaired Pytest-parallel wheel. | All 750 tests and five fio subtests passed with zero skips. Both workers recorded native branch coverage. Actions billing blocked the hosted jobs before setup. |

The cross-repository controls in Buildlib, fz and Diff-pretty support retaining their proven Make entry points. When qualifying a successor, record the actual checked head, selected regions, missed identities and total runner cost. Keep incomplete platform and consumer boundaries in the owning Tests ticket.

## Successor results

- Fastermod [#34](https://github.com/laputa-systems/fastermod/pull/34)
  verifies the source warning by its diagnostic and path. The same
  nine-identity inventory moved from six to seven caught, with two
  unviable. All 46 tests and hosted checks passed.
  [#35](https://github.com/laputa-systems/fastermod/pull/35) exercised
  JSON apply with five ignore sources and hidden files. It caught all
  six viable identities on unchanged source, up from zero. Tests,
  Clippy and both hosted checks passed. [#36](https://github.com/laputa-systems/fastermod/pull/36)
  verified saved identifier plan application through separate CLI
  invocations, including edited and unedited inputs, added and removed
  paths, and duplicate plan basenames in separate directories. The
  same eight read-set mutations were caught before and after. All
  48 ordinary tests and both hosted checks passed.
  [#37](https://github.com/laputa-systems/fastermod/pull/37) retained
  the source mutation scope. The
  [positive trial](https://github.com/laputa-systems/fastermod/actions/runs/44277884233)
  caught all seven viable identities at `d34b68c`, with two unviable.
  Both hosted jobs used 425 runner seconds. The documentation,
  warning-test deletion, mixed change and uncovered branch controls
  behaved as expected on both platforms and passed ordinary CI.
  The mixed control reopened the warning mutation and caught all
  three viable discovery mutations. Terminal review and the wider
  saved-plan inventory remain open.
  [#42](https://github.com/laputa-systems/fastermod/pull/42) at
  `d99400a` runs the Make selector on every pull request.
- Ptytest [#23](https://github.com/laputa-systems/ptytest/pull/23)
  verifies timeout diagnostics and the deadline under continuous output.
  The scope moved from 11 to 13 caught of 18, with five unviable.
  All 68 local tests and the hosted Linux and macOS jobs passed.
  [#24](https://github.com/laputa-systems/ptytest/pull/24) verifies
  cursor coordinates in both the PTY response and the recorded input.
  It caught all 13 viable terminal identities, up from 12 in the
  same 18-identity selection. Both platform jobs passed.
  [#25](https://github.com/laputa-systems/ptytest/pull/25) passed the
  [hosted terminal trial](https://github.com/laputa-systems/ptytest/actions/runs/44276455149)
  with 13 caught and five unviable on each platform, using 238 runner
  seconds. [Documentation](https://github.com/laputa-systems/ptytest/pull/26)
  selected no mutations. [Deletion](https://github.com/laputa-systems/ptytest/pull/27)
  reopened four cursor identities. The revised
  [mixed change](https://github.com/laputa-systems/ptytest/pull/28)
  reopened the same four and caught both changed size-accessor
  identities. The [uncovered branch](https://github.com/laputa-systems/ptytest/pull/29)
  left seven of 11 selected identities alive. The ordinary suite and
  lint passed each control. Lifecycle, replay and the wider consumer
  inventory remain open. #25 merged at `a9b3108`. The
  [fleet-compatible entry point](https://github.com/laputa-systems/ptytest/pull/30)
  at `606027b` classifies every pull request and retains the bounded
  terminal selection without a GitHub path filter.
- Ptytest [#21](https://github.com/laputa-systems/ptytest/pull/21) caught
  all four remaining output-wait mutations after removing two redundant
  deadline checks. Linux and macOS hosted checks passed. Focused lz, e
  and ish tests passed with the candidate. Xsh failed to compile on
  macOS at both the baseline and candidate revisions. [#22](https://github.com/laputa-systems/ptytest/pull/22)
  records the remaining PTY and consumer scope.
- Pytest-parallel [#31](https://github.com/joshuarli/pytest-parallel/pull/31)
  raised coordinator file-planning detection from 33 to 67 of the same
  83 identities. After removing an unreachable guard the final inventory
  has 79 identities, with 67 caught and 12 surviving. All 173 local tests
  and three hosted checks passed. Draft
  [#32](https://github.com/joshuarli/pytest-parallel/pull/32) at `41891aa`
  passed local standalone option and scheduling shards. The earlier
  aggregate at `f7c2795` exhausted 1,200 seconds after processing 130 of
  559 coordinator identities. [#33](https://github.com/joshuarli/pytest-parallel/pull/33)
  caught all 79 file-planning identities. [#38](https://github.com/joshuarli/pytest-parallel/pull/38)
  removed redundant worker-pin and worker-limit paths, leaving 51
  identities, all caught. All 188 ordinary tests passed and the three
  hosted checks passed. [#40](https://github.com/joshuarli/pytest-parallel/pull/40)
  raised report event detection from 68 to 107 of the same 111
  identities. After removing redundant state operations all 105
  remaining identities were caught. The 207 local tests and three
  hosted checks passed. Draft #32's
  [six-scope trial](https://github.com/joshuarli/pytest-parallel/actions/runs/44276369341)
  at `4d29d37` passed all twelve mutation jobs, including both
  105-identity report lanes. The jobs used 907 runner seconds, with an
  89.5-second median and a 166-second maximum. The uncovered
  coordinator lifecycle and loopback decisions stay outside that matrix.
- Pytest-parallel's [positive run](https://github.com/joshuarli/pytest-parallel/actions/runs/44257362822)
  at `80cce01` passed eight jobs, covering options, scheduling,
  file planning and report emission on Linux ARM64 and macOS. Total
  runner time was 668 seconds, with a 76.5-second median and a
  170-second maximum. The uncovered decision in
  [#34](https://github.com/joshuarli/pytest-parallel/pull/34) left
  plan-parser identities 19–22 alive. Deletion in
  [#35](https://github.com/joshuarli/pytest-parallel/pull/35) and the
  mixed change in [#37](https://github.com/joshuarli/pytest-parallel/pull/37)
  reopened identity 18 on both platforms. The mixed scheduling change
  passed its own shard. All eight jobs in the
  [documentation control](https://github.com/joshuarli/pytest-parallel/pull/36)
  reported no relevant changes. Ordinary checks passed all four controls.
  The broader coordinator and socket scopes still need witnesses, and
  the socket trial reported misses. The expanded
  [positive run](https://github.com/joshuarli/pytest-parallel/actions/runs/44262334863)
  at `23937c8` added the worker-pin and limit shard. All ten mutation
  jobs and three ordinary checks passed. The ten mutation jobs used
  786 runner seconds, with a 72-second median and a 174-second maximum.
  [#39](https://github.com/joshuarli/pytest-parallel/pull/39) repaired
  native subtest replay. All 191 local tests and the three hosted
  checks passed. The installed wheel passed the focused cases on pytest
  9.0.0 and 9.2.0 and the Toolbox consumer below.
- Stats [#30](https://github.com/joshuarli/stats/pull/30) records
  1,112 of 1,128 TypeScript ingest lines and 820 of 855 branches in the
  Node selection, 21 Worker cases, and 608 of 625 Rust wire lines and
  126 of 146 branches. [#31](https://github.com/joshuarli/stats/pull/31)
  corrected a stale target-policy test and wired its denial assertion to
  the tested loopback origin. [#32](https://github.com/joshuarli/stats/pull/32)
  caught 113 of 115 TypeScript ACK mutations in 14 seconds, up from
  104 on the same source. The two survivors are equivalent. Both
  implementations passed the expanded corpus, and all three hosted
  checks passed. [#33](https://github.com/joshuarli/stats/pull/33)
  caught all 42 Rust ACK identities, up from 41 on the same source, by
  distinguishing an ACK at the byte limit from one byte over. All 109
  Rust unit tests, five wire conformance cases and three hosted checks
  passed. [#34](https://github.com/joshuarli/stats/pull/34) removed
  four assertions in producer ACK processing. The producer and
  bridge typechecks passed, the local integration suite passed 24
  cases with one opt-in skip, and all three hosted checks passed.
  [#35](https://github.com/joshuarli/stats/pull/35) raised producer ACK
  stream detection from 14 to 30 of 68 on unchanged source. Three
  equivalents and 35 repeated tool timeouts remain. The PR also fixed
  the persisted-state assertion after the hosted fixture exceeded its
  45-second online window. All three checks passed the reviewed head.
  Wider ingest and whole-change results remain open.
- Loc [#22](https://github.com/joshuarli/loc/pull/22) caught 16 of 19
  search-sweep identities, up from eight. Two timeouts repeated in
  longer native singleton runs, and the remaining identity is
  equivalent. All five hosted checks passed. The broader Loc gate
  and cost still need qualification. [#23](https://github.com/joshuarli/loc/pull/23)
  verifies a matching first-line interpreter, a foreign interpreter
  and a matching directive later in the file. It caught all five
  viable shebang identities, up from four on unchanged source.
  The 551 local tests and all five hosted checks passed.
  Draft [#24](https://github.com/joshuarli/loc/pull/24) passed the
  [positive shebang trial](https://github.com/joshuarli/loc/actions/runs/44278389932)
  at `0ee7305a` on macOS, x86-64 musl and ARM64 musl. The three
  jobs used 771 runner seconds. Ordinary CI and LineJudge passed
  all four controls. On all three targets the mixed trial at its
  initial head reopened one shebang survivor, caught seven changed
  preprocessor identities and recorded two unviable builds. A
  second macOS mixed run exhausted the 600-second budget rebuilding
  for its second phase. A native union retained all 25 planned
  identities in one local run with the same outcomes. Hosted
  verification of that runner and the wider SIMD inventory remain open.
- Repomod [#83](https://github.com/laputa-systems/stuff/pull/83) removed
  two test-only helpers and recorded the clean dependency scan.
  [#84](https://github.com/laputa-systems/stuff/pull/84) moved Musl lock
  transition tests to the shipped pins command and removed its test-only
  writer. [#85](https://github.com/laputa-systems/stuff/pull/85) caught
  all 19 checkout refusal identities on unchanged source. All 55 local
  removal tests and the ten hosted checks passed. The retained union
  stays open.
  [#88](https://github.com/laputa-systems/stuff/pull/88) removed the
  test-only role exception accessor and asserted the rendered migration
  result through the remaining API. [#90](https://github.com/laputa-systems/stuff/pull/90)
  removed the unused direct catalog writer. Its tests cover comment
  preservation, repeat discovery and concurrent additions through the
  live pending writer. [#91](https://github.com/laputa-systems/stuff/pull/91)
  removed the unused audit batch worker and moved its witnesses to the
  shipped advisory rule and version cache. All 1,481 local tests and
  the ten hosted checks passed, with three opt-in local skips.
  [#98](https://github.com/laputa-systems/stuff/pull/98) closed the
  Dead code step after 98 CLI, catalog, inventory and dashboard tests,
  a 31-page preview and the dependency scans. Draft
  [#92](https://github.com/laputa-systems/stuff/pull/92) verified 102
  identities across three protected effects. Six hosted jobs at
  `43b4b515` used 273 runner seconds. The bounded successor at
  `3a61cccd` passed all six mutation jobs in 353 runner seconds. The
  [four-scope run](https://github.com/laputa-systems/stuff/actions/runs/44274517903)
  at `2647a2ea` added 23 Git-backed snapshot entries, all caught on
  both platforms. Eight passing jobs used 380 runner seconds. A
  separate publication probe exhausted 360 seconds after reporting
  90 caught and five surviving identities in its progress output.
  [#103](https://github.com/laputa-systems/stuff/pull/103) completed
  the 127-identity publication selection. The three diagnostic
  cases moved detection from 118 to 121 without production edits.
  The other six have exact equivalence dispositions. All 22 focused
  cases, lint and the ten hosted checks passed. The publication
  shard is included in the next #92 trial.
- Extensions [draft #22](https://github.com/joshuarli/extensions/pull/22)
  passed local parser and storage gate invocations, with 178 caught and
  one equivalent in 7m 30s, and 112 caught and two equivalents in 15s.
  The deletion, mixed and uncovered-decision controls failed as intended
  after ordinary type checking and focused tests passed. A docs-only
  change selected no jobs. The [hosted positive run](https://github.com/joshuarli/extensions/actions/runs/44253162875)
  passed both mutation jobs in 8m 43s and 1m 34s, using 617 aggregate
  runner seconds. The existing check and Chromium jobs also passed.
  The [uncovered decision](https://github.com/joshuarli/extensions/pull/23)
  reopened IDs 30 and 31. The
  [deletion](https://github.com/joshuarli/extensions/pull/24) and
  [mixed](https://github.com/joshuarli/extensions/pull/25) runs each
  reopened IDs 115 and 116 and passed ordinary checks. The
  [documentation control](https://github.com/joshuarli/extensions/pull/26)
  passed and selected no jobs. [#27](https://github.com/joshuarli/extensions/pull/27)
  moved stored ZIP archive detection from 26 to 35 caught of 44.
  Three of seven survivors are equivalent, with two other identities
  still uncovered. All three hosted checks passed.
- Srv [run 44249399368](https://github.com/laputa-systems/srv/actions/runs/44249399368)
  at `7cd8627` caught 310 of 376, with 25 misses and 16 unviable.
  Five timeouts repeated as exact singletons before the four jobs
  exhausted their 900-second budgets. Another 20 remain provisional.
  The completed retries each spent 110–129 seconds building before
  their 30-second tests. The first cache-reuse candidate at `d785317`
  used incompatible flags. [#47](https://github.com/laputa-systems/srv/pull/47)
  at `289a8fe` uses the native serial invocation. Two local singleton
  runs confirmed the timeouts and preserved the original file bytes.
  The first local build took 77.2s and the second 4.8s with the same
  target directory. The [hosted rerun](https://github.com/laputa-systems/srv/actions/runs/44254842182)
  accounted for all 376 identities. The remaining 25 provisional
  timeouts resolved to 12 caught, one unviable and 12 confirmed hangs
  relative to the earlier run's counts. The four gate walls were 844.7,
  854.9, 884.2 and 888.6 seconds, and the jobs used 3,541 runner seconds.
  [#48](https://github.com/laputa-systems/srv/pull/48) caught one
  retained miss locally through a CLI startup warning, and ordinary
  CI and lint passed. Its existing unsharded mutation check exhausted
  900 seconds. The witness and receipt are now on draft #47 at
  `601451a`, and #48 is closed. The
  [second full run](https://github.com/laputa-systems/srv/actions/runs/44264082122)
  accounted for 323 caught, 24 missed, 17 unviable and 12 confirmed
  hangs. Its four jobs used 3,462 runner seconds, with a median gate
  wall of 850.3 seconds. The 600-second target remains open.

## Retained Rust scopes

Ptytest and Fastermod now use an unfiltered pull-request workflow
with the scope decision in their checked Make entry point. The
fleet check requires the full checkout, the approved mutator pin
and the base ref passed as an environment value. In isolated
checkouts of both candidate heads, `mutation-lane` and
`mutants-diff-lane` passed after removing `TODO-DESLOP.md`.
Removing the workflow then failed both checks. The two repositories
are registered for mutation retention.

## Worker and Rust acknowledgment trial

Stats [#36](https://github.com/joshuarli/stats/pull/36) merged at
`ec5993b` after all three ordinary checks passed. The mixed request
checks a binary acknowledgment across acceptance, retry and all three
rejection reasons, and verifies the durable rows. The focused
Workerd suite ran all 22 tests. It caught 25 of 27 Stryker identities
before and after the new case. Two variants affect an unreachable
empty rejection list under the nonempty frame contract.

Draft [#37](https://github.com/joshuarli/stats/pull/37)
passed its [hosted two-lane trial](https://github.com/joshuarli/stats/actions/runs/44283893296)
at `7d2aacf`. The Worker lane had 25 caught and two equivalent.
The actual Rust fixtures caught all 42 identities. The jobs used
322 runner seconds, with a 227-second maximum. The doc-only control
selected nothing. The Rust deletion and mixed controls reopened
the exact body-length comparison, and the mixed Workerd edit
passed its independent selection. The uncovered Worker branch left
three new identities alive. Wider producer, storage and coverage
scopes remain open.

## Toolbox native and worker coverage

The published 0.4.0 Pytest-parallel wheel and a wheel from `c260153`
both rejected native fio subtests as duplicate call phases. The
repaired wheel from `3e513b8` has SHA-256
`8e518a881812ad21c192ca7c63e6b0efb8c789d125439dba0f36ae388930af87`.
An isolated Toolbox environment installed this wheel with the tracked
dependency pins intact. FFmpeg's real loudness filter ran against
generated audio, and native fio 3.42 at `ab776430` ran against
disposable regular files. The lavfi device-table check brought the
last skipped audio test into the suite.

The complete two-worker run passed 750 tests and five fio subtests in
59.60 seconds. Each worker wrote a raw branch-coverage file with
executed lines from 46 Toolbox source files before combination.
The combined data covered 5,420 of 7,313 statements and 1,572 of
2,428 branches. Use the
[installed-wheel procedure](https://github.com/joshuarli/pytest-parallel/blob/3ee78f514411bc808167b0a8eeaeecdfe8f07b88/docs/deslop-coverage.md)
with Toolbox's locked coverage.py 7.16.1, `source = TOOLBOX/src/tool`,
`pytest -q -rs -j 2` and the raw worker guard set to check
`/src/tool/` paths. Keep instrumented data in a fresh scratch
directory. The hosted jobs still require Actions billing recovery.

## Deferred environment gates

- Vault [#36](https://github.com/laputa-systems/vault/pull/36) records
  the unresolved Secure Enclave, two-Mac recovery and Linux session
  keyring boundaries. Two-Mac recovery requires both devices and
  owner authentication. The ordinary hosted platform results and the
  failed mutation union are recorded separately.
- Dashboard library pins still require `solid-js` 2.0.0, `@solidjs/web`
  2.0.0 and `@solidjs/vite-plugin` 3.0.1 from the configured npm mirror.
  All three metadata requests succeeded, and their version maps lack those
  exact keys. The pinned candidates can resume when the mirror serves them.
