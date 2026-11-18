# Repomod mutation trial

The trial replays the checkout refusal, upstream fetch and workflow
matrix decisions on a committed snapshot. Changes to Repomod tests
or settings select all three protected functions. A production edit
selects the full supported file. Its selection is included alongside
the protected functions when the change includes a test edit. A
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
