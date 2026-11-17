# Validate a filtered inventory before writing records

At base `40112564521758ad14bc9ed697c66d3ae08c44f7`, `snapshot` writes each
repository record before `_index_payload` validates the existing index. A
filtered run against an obsolete parser version therefore raises an error
after changing repository data. The old index still describes the old data.
Invalid schema and malformed JSON have the same ordering defect.

The repair computes the index payload before writing repository records.
The three regressions create a real local checkout and initial inventory,
commit a changed package input, and corrupt the existing index. Each case
requires the intended rejection and byte-identical inventory files afterward.
All three failed on the base because `repos/acme/tool.json` had changed.

The 34 snapshot tests, full 1,412-test repomod suite and lint pass on macOS
arm64 with Python 3.15, Ruff 0.17.4 and ty 0.0.101. The full suite retains
three existing opt-in skips. Reproduce with the locked dev environment:

```sh
mkdir -p .work/tmp
export TMPDIR="$PWD/.work/tmp" PYTHON_CPU_COUNT=2
cpu-guard --cores 2 -- uv sync --locked --group dev
cpu-guard --cores 2 -- uv run pytest -q tests/repomod/test_deps_snapshot.py
cpu-guard --cores 2 -- make repomod-test
cpu-guard --cores 2 -- make repomod-lint
```

The file formats, filtering semantics and successful snapshot output do not
change. This preflight prevents writes on invalid-index rejection; it does not
provide a transaction across files or concurrent-writer exclusion. No declared
runtime performance workload changes, and no speed claim follows.
