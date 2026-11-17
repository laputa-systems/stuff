# Preserve cached mirror data after malformed catalog input

At base `40112564521758ad14bc9ed697c66d3ae08c44f7`, `read_mirror_catalog`
silently skips malformed package and version records. A non-array `versions`
field becomes an empty served-version set. Enrich accepts that partial result
as a successful refresh and replaces its previously valid mirror catalog.

The reader now raises `MirrorCatalogError` for malformed required package
names, version arrays or version records. Enrich already handles that error by
retaining its cached catalog and reporting a failed lookup. Empty catalogs,
empty version arrays, unknown fields and duplicate-name version unions retain
their behavior. Published catalog formats do not change, and the reader adds
no ecosystem-specific package-name or version normalization.

Five malformed-record regressions and two actual enrich refreshes failed on
the base. The latter incorrectly reported success for malformed version data.
After the repair, the refreshes report an error and preserve the complete
previous mirror map and its timestamp. Valid empty records remain accepted.
Existing CLI coverage verifies that an unresolved mirror lookup exits 2.

On macOS arm64, Python 3.15, 44 focused world/enrich tests, the full 1,419-test
repomod suite, Ruff 0.17.4 and ty 0.0.101 pass. The full suite retains three
existing opt-in skips. Reproduce from the repository root:

```sh
mkdir -p .work/tmp
export TMPDIR="$PWD/.work/tmp" PYTHON_CPU_COUNT=2
cpu-guard --cores 2 -- uv sync --locked --group dev
cpu-guard --cores 2 -- uv run pytest -q tests/repomod/test_deps_world.py tests/repomod/test_deps_enrich.py
cpu-guard --cores 2 -- make repomod-test
cpu-guard --cores 2 -- make repomod-lint
```

These tests use synthetic documents and local cache files. No live registry or
production refresh was run. The declared dashboard-render and OCI serving
workloads are unaffected; no speed claim follows.
