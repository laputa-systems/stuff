# Repomod mutation testing

The repomod mutation check replays the checkout refusal, upstream fetch,
workflow matrix, snapshot entry and fixer publication decisions on a
committed snapshot. Changes to repomod tests or settings select all five
protected functions. A production edit confined to one of those functions
selects that function; other edits select the full supported file. The
production selection runs alongside the protected functions when the change
includes a test edit. A deletion or rename cannot drop the protected scope. A
Python production file without a witness, an unclassified path, an empty
inventory or an incomplete result fails. Every timeout fails. The driver
checks exact bytes before and after a function in both revisions, so edits to
decorators or surrounding code keep the full-file selection.

## Running it

With the locked Python environment and mutmut 3.8.1 installed, run
`BASE=origin/main make repomod-mutants`. Set `REPOMOD_MUTATION_SHARD` to
`removal`, `upstream`, `matrix`, `snapshot-entries` or `fix-publish` to run
one shard. `uv run --no-sync python tests/repomod/mutation_gate.py BASE --plan`
lists the committed selection.

The command archives the tested revision under `.work/tmp` and rejects links
in the archive. A full local run shares a 600-second budget; each hosted shard
has its own. The runner terminates the subprocess group on timeout or handled
cancellation and reaps it before removing the snapshot.

The hosted workflow (`.github/workflows/repomod-mutation-trial.yml`) runs all
five shards on Linux ARM64 and macOS only for pull requests from or into the
`ci/deslop-repomod-mutation` branch. It is not registered for retention.
