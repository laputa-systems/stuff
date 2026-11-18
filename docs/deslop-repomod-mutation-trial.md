# Repomod mutation trial

The trial replays the checkout refusal, upstream fetch, workflow
matrix, snapshot entry and fixer publication decisions on a committed snapshot. Changes
to Repomod tests or settings select all five protected functions. A production edit
confined to one of those functions selects that function. Other
edits select the full supported file. The production selection runs
alongside the protected functions when the change includes a test edit. A
deletion or rename cannot drop the protected scope. A Python
production file without a witness, unclassified path, empty
inventory or incomplete result fails.

The first serial pass at `134043be` on macOS arm64 caught all 19
checkout refusal identities and all 25 upstream fetch identities.
Workflow expansion caught 55 of 58 and retained the three previously
verified equal-length tuple cases. The exception requires both the
exact source digest and the generated mutation's digest. The trial
currently fails on every timeout.

With the locked Python environment and mutmut 3.8.1 installed, run
`BASE=origin/main make repomod-mutants`. Set `REPOMOD_MUTATION_SHARD`
to `removal`, `upstream`, `matrix`, `snapshot-entries` or `fix-publish` to run one shard. Use
`uv run --no-sync python tests/repomod/mutation_gate.py BASE --plan`
to list the committed selection. The command archives the tested
revision under `.work/tmp` and rejects links in the archive. It
uses a 600-second shared budget for a full local run and a separate
budget in each hosted shard. The runner terminates the subprocess
group on timeout or handled cancellation and reaps it before
removing the snapshot.

The draft attempts all five shards on Linux ARM64 and macOS. Wider
snapshot, catalog and policy decisions and whole-file scope are
still open. Keep this trial outside retention until those boundaries
are verified.

## Hosted controls

The [first hosted run](https://github.com/laputa-systems/stuff/actions/runs/44265802547)
at `43b4b515` passed all six mutation jobs. The jobs used 273 runner
seconds with a 37-second median and a 79-second maximum.

[The documentation control](https://github.com/laputa-systems/stuff/pull/94)
reported no selection in all six jobs. [Deleting the removal table](https://github.com/laputa-systems/stuff/pull/97)
left all 19 protected identities alive on both platforms.
[The uncovered branch](https://github.com/laputa-systems/stuff/pull/95)
left four new decision mutations alive on Linux. Its full-file macOS
job reached the 600-second limit. [The mixed control](https://github.com/laputa-systems/stuff/pull/96)
reopened the removal misses and also selected the changed sync file.
Linux caught all 25 upstream-function identities inside that selection.
Other file results failed, and the full-file macOS job ran out of time.
Ordinary checks passed all four controls.

With the function-level selection at `3e467fc9`, local runs selected
24 checkout decisions for the uncovered branch, with four surviving,
and all 25 caught upstream decisions for the mixed change. The driver
checks exact bytes before and after the function in both revisions.
This keeps edits to decorators or surrounding code in the full-file
selection.

The [bounded hosted run](https://github.com/laputa-systems/stuff/actions/runs/44271866892)
at `3a61cccd` passed all six jobs in 353 runner seconds.
[The bounded mixed control](https://github.com/laputa-systems/stuff/pull/99)
caught all 25 changed upstream-function identities, and the deletion
left all 19 removal identities alive on both platforms.
[The bounded uncovered control](https://github.com/laputa-systems/stuff/pull/100)
left IDs 2–5 alive out of 24 selected on both platforms. Ordinary
checks passed both controls.

The snapshot entry shard at `c13e2502` caught all 23 identities
locally through the real Git fixture, using snapshot source SHA-256
`5cc6294699c74e8b40ee9445ef5f0fb6a578375bb5d00f6523a33fbeb1d25cf1`.
The [four-scope hosted run](https://github.com/laputa-systems/stuff/actions/runs/44274517903)
at `2647a2ea` passed every mutation job. The snapshot shard caught all
23 on both platforms. Eight jobs used 380 runner seconds with a
36-second median and a 92-second maximum.

A separate serial run of the native `repomod.fix.x_push_fix_branch__mutmut_*`
selection against `tests/repomod/test_fix_push.py` reached its
360-second local probe limit with 90 caught and five surviving
identities in its last progress report. The incomplete run neither
qualifies publication nor changes the protected trial selection.

The complete two-child publication runs finished within the same
600-second local limit, with 118 caught before and 121 of 127
caught after the diagnostic cases merged in
[#103](https://github.com/laputa-systems/stuff/pull/103). The six
remaining identities have [bounded dispositions](deslop-fixer-paths.md#publication-diagnostics).
The new publication shard matches each against the same source
and exact native body digest. Each child runs the tests serially.

The [five-scope hosted run](https://github.com/laputa-systems/stuff/actions/runs/44284964354)
at `2e41e923` passed all ten jobs. It accounted for 252 identities
per platform, with 243 caught and nine proved equivalent. The
publication scopes took 59 seconds on Linux ARM64 and 271 seconds
on macOS. The matrix used 740 runner seconds, with a 54-second
median. The remaining whole-file and inventory decisions stay in
the existing Tests scope.
