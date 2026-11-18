# Repomod mutation trial

The trial replays the checkout refusal, upstream fetch and workflow
matrix decisions on a committed snapshot. Changes to Repomod tests
or settings select all three protected functions. A production edit
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
to `removal`, `upstream` or `matrix` to run one shard. Use
`uv run --no-sync python tests/repomod/mutation_gate.py BASE --plan`
to list the committed selection. The command archives the tested
revision under `.work/tmp` and rejects links in the archive. It
uses a 600-second shared budget for a full local run and a separate
budget in each hosted shard. The runner terminates the subprocess
group on timeout or handled cancellation and reaps it before
removing the snapshot.

The draft attempts all three shards on Linux ARM64 and macOS. The
snapshot, catalog and wider policy decisions, hosted controls and
whole-file scope are still open. Keep this trial outside the
retention configuration until those boundaries are verified.

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
selection. The hosted successor still needs qualification.
