# M2 calibration evidence

This checkpoint records qualification by workload. The [roadmap](deslop-roadmap.md#qualify-meaningful-retained-gates) defines acceptance, and the [scorecard](deslop-scorecard.md) records repository pass state. M2 remains open.

| Shape and workload | Result and exact evidence | Cost and remaining boundary |
| --- | --- | --- |
| Rust HTTP service, Srv request dispatch and rendering | Earlier pass and retained mutation gate on `c9965411`. Draft [#47](https://github.com/laputa-systems/srv/pull/47) exercised 376 identities across four jobs, including 308 caught, 27 missed, 16 unviable and 25 provisional timeouts. | Separate native singleton selection reproduced one timeout. Finish the current candidate's decisions and confirm any further timeouts before counting them. |
| Rust performance CLI, Fastermod saved plans and text search | Ground, Diagnose and Types are complete through [#33](https://github.com/laputa-systems/fastermod/pull/33). [#31](https://github.com/laputa-systems/fastermod/pull/31) fixed terminal plan routing. [#32](https://github.com/laputa-systems/fastermod/pull/32) repaired source read diagnostics and merged as `a4040a1a`. | The [paired workload](https://github.com/laputa-systems/fastermod/blob/a4040a1a3b85053397ba4c3d1338e534f74d6f63/docs/deslop-text-source-perf.md) qualifies the repair across all seven named benchmarks, with five pairs inside the observed spread. Both outputs matched. General mutation and the rest of the Tests step remain open. |
| Rust corpus and SIMD CLI, Loc | [#19](https://github.com/joshuarli/loc/pull/19) added a child deadline and caught both previously hanging CLI mutations. [#20](https://github.com/joshuarli/loc/pull/20) at `b45c6f2e` exercises XDG precedence and fallback on both Linux musl architectures. All five hosted checks passed. | The sample retains three comparison alternatives and two counting-helper misses. Finish the critical inventory, cost and whole-change lane. |
| Rust PTY library, Ptytest cleanup and consumers | [#15](https://github.com/laputa-systems/ptytest/pull/15) preserved diagnostics through cleanup and passed focused fz, tm and lz consumers. Diagnose and Types completed through [#17](https://github.com/laputa-systems/ptytest/pull/17). [#19](https://github.com/laputa-systems/ptytest/pull/19) repaired a hosted fixture race, and [#18](https://github.com/laputa-systems/ptytest/pull/18) retains coverage. [#20](https://github.com/laputa-systems/ptytest/pull/20) at `fcb35843` verifies output wait results. | The output wait sample caught five of eight identities, up from two. Two guards are equivalent and one timing-sensitive case remains. All 67 instrumented tests passed at #18. Focused e and ish failures also occur with the pre-repair library. The nightly corpus and whole-change mutation remain separate. |
| Rust platform and hardware, Vault | Linux x86-64 musl, Linux ARM64 musl and macOS ordinary jobs passed on draft [#30](https://github.com/laputa-systems/vault/pull/30) at `0671858b`. The platform union remains unqualified. | Fourteen Linux shards failed and many exhausted the roughly 20-minute job budget. A successor records partial outcomes. Secure Enclave, two-Mac recovery and Linux keyring remain separately scoped. |
| Python library and binary parsers, Buildlib | Qualified bounded workflow and four hosted controls in [#20](https://github.com/laputa-systems/buildlib/pull/20) and [#26](https://github.com/laputa-systems/buildlib/pull/26). Cumulative review caught inconsistent release-manifest serialization from a changing mapping. [#27](https://github.com/laputa-systems/buildlib/pull/27) fixed it at `1497970d` and passed all 17 checks plus five release consumers. | The retained 15-job mutation matrix on #26 used 963 job seconds in one run. Its longest job took 167 seconds. The refreshed release shard caught 319 of 333 selected identities, with the other 14 dispositioned in the release receipt. |
| Python pytest plugin and worker coverage, Pytest-parallel | The installed wheel passed Stuff's consumer suite after [#26](https://github.com/joshuarli/pytest-parallel/pull/26) fixed empty-address bind handling. [#27](https://github.com/joshuarli/pytest-parallel/pull/27) caught all 60 report-emission identities. [#28](https://github.com/joshuarli/pytest-parallel/pull/28) catches an observable truncated-event diagnostic fault. [#29](https://github.com/joshuarli/pytest-parallel/pull/29) at `45b45492` records the remaining active decisions. | The coverage target verified separate worker measurements and passed all 158 tests, covering 1,545 of 1,759 statements and 586 of 718 branches. Linux and macOS ordinary checks passed. The serial whole-change union and its cost and controls remain open. |
| Python orchestration and effects, Repomod | Types complete. The [focused dead-code review](../deslop-repomod-dead-code.md) removed two unused items. Workflow expansion caught 55 of 58 with three equivalent cases in [#61](https://github.com/laputa-systems/stuff/pull/61). Real local fetch caught all 25 in [#62](https://github.com/laputa-systems/stuff/pull/62). Catalog admission caught 52 of 60 versus 39 on the base in [#68](https://github.com/laputa-systems/stuff/pull/68). [#74](https://github.com/laputa-systems/stuff/pull/74) repaired snapshot drift handling. | The [snapshot scenario](../deslop-repomod-snapshot.md) caught 110 of 123 in the full selection, six targeted survivors in the follow-up and two filename mutations on a case-sensitive filesystem. The retained whole-change union and full Dead code acceptance remain open. [Serial first-party coverage](deslop-roadmap.md#repomod-calibration-inventory). |
| TypeScript Node, browser and MV3, Extensions | Type-aware unsafe-argument lint and installed Chromium landed in [#15](https://github.com/joshuarli/extensions/pull/15). [#17](https://github.com/joshuarli/extensions/pull/17) retains first-party coverage. [#18](https://github.com/joshuarli/extensions/pull/18) keeps nine capture fixtures and the extension lifecycle in one Chromium job. [#20](https://github.com/joshuarli/extensions/pull/20) at `fc55127a` verifies exact parser diagnostics. | The parser caught 178 of the same 179 mutations, up from 139 on the base and 167 at #19. The final survivor is equivalent. The final local run took 7m 34s. TypeScript whole-change mutation and controls remain open. |
| TypeScript Worker and Rust agent, Stats ingest and local stack | [#24](https://github.com/joshuarli/stats/pull/24) verified legacy migration with 41 local passes and all hosted checks. [#26](https://github.com/joshuarli/stats/pull/26) and [#27](https://github.com/joshuarli/stats/pull/27) fixed a producer port collision and SIGTERM shutdown. [#28](https://github.com/joshuarli/stats/pull/28) adds a shared ACK case that catches miscounting in both decoders. [#29](https://github.com/joshuarli/stats/pull/29) at `da022e8b` records the Rust wire type audit. | Ten wire unit tests, five conformance tests and all three hosted checks passed #29. Component-scale TypeScript and Rust critical selection, browser/Worker cost and retained gates remain open. |
| Python and external native tools, Toolbox | Deferred. The installed Pytest-parallel wheel and the baseline both reproduced the FFmpeg failure. The hosted lint retry also ended before any step. | Requires Actions billing recovery and positive FFmpeg and fio execution evidence before the worker-coverage result can qualify this shape. [Lint retry](https://github.com/joshuarli/toolbox/actions/runs/43933600029/attempts/2). |

The cross-repository controls in Buildlib, fz and Diff-pretty support retaining their proven Make entry points. When qualifying a successor, record the actual checked head, selected regions, missed identities and total runner cost. Keep incomplete platform and consumer boundaries in the owning Tests ticket.

## Successor results

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
  559 coordinator identities. The mixed negative control completed
  selection. It still needs to execute both scopes through the gate.
- Stats [#30](https://github.com/joshuarli/stats/pull/30) records
  1,112 of 1,128 TypeScript ingest lines and 820 of 855 branches in the
  Node selection, 21 Worker cases, and 608 of 625 Rust wire lines and
  126 of 146 branches. [#31](https://github.com/joshuarli/stats/pull/31)
  corrected a stale target-policy test and wired its denial assertion to
  the tested loopback origin. [#32](https://github.com/joshuarli/stats/pull/32)
  caught 113 of 115 TypeScript ACK mutations in 14 seconds, up from
  104 on the same source. The two survivors are equivalent. Both
  implementations passed the expanded corpus, and all three hosted
  checks passed. Wider ingest and whole-change results remain open.
- Loc [#22](https://github.com/joshuarli/loc/pull/22) caught 16 of 19
  search-sweep identities, up from eight. Two timeouts repeated in
  longer native singleton runs, and the remaining identity is
  equivalent. All five hosted checks passed. The broader Loc gate
  and cost still need qualification.
- Repomod [#83](https://github.com/laputa-systems/stuff/pull/83) removed
  two test-only helpers and recorded the clean dependency scan.
  [#84](https://github.com/laputa-systems/stuff/pull/84) moved Musl lock
  transition tests to the shipped pins command and removed its test-only
  writer. [#85](https://github.com/laputa-systems/stuff/pull/85) caught
  all 19 checkout refusal identities on unchanged source. All 55 local
  removal tests and the ten hosted checks passed. The retained union
  and remaining dead-code decisions stay open.
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
  passed and selected no jobs. Other critical source witnesses remain
  open.
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
  target directory. The hosted rerun is in progress.

## Deferred environment gates

- Dashboard library pins still require `solid-js` 2.0.0, `@solidjs/web`
  2.0.0 and `@solidjs/vite-plugin` 3.0.1 from the configured npm mirror.
  All three metadata requests succeeded, and their version maps lack those
  exact keys. The pinned candidates can resume when the mirror serves them.
