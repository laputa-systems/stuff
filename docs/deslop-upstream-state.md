# Preserve tracking state when repointing upstream

At base `40112564521758ad14bc9ed697c66d3ae08c44f7`,
`ensure_upstream_remote` removes an existing remote and creates it again when
the URL differs. Git removes its tracking refs, branch upstream configuration
and other remote settings during that operation. A synthetic upstream-only
commit lost its normal ref in the review witness; permanent object loss was
not demonstrated.

The repair uses `git remote set-url` and retains the existing configuration
steps. Sync still reports that upstream was repointed and fetches the intended
parent branch. The subsequent fetch may update that selected branch as before.
Other tracking refs and branch settings survive remote reconfiguration.

The existing sync regression now creates an upstream-only commit reference,
sets the canonical branch to track it, and adds a custom push URL. It asserts
that all survive a real local-parent fetch, the intended parent branch is
present, and canonical HEAD and branch remain unchanged. The base fails
because only `refs/remotes/upstream/main` remains. The repaired test passes.

On macOS arm64 with Python 3.15, all 29 sync tests and the full 1,410-test
repomod suite pass, with three existing opt-in skips. Ruff 0.17.4 and ty
0.0.101 pass. Reproduce using the locked dev environment:

```sh
mkdir -p .work/tmp
export TMPDIR="$PWD/.work/tmp" PYTHON_CPU_COUNT=2
cpu-guard --cores 2 -- uv sync --locked --group dev
cpu-guard --cores 2 -- uv run pytest -q tests/repomod/test_sync_upstream.py tests/repomod/test_git_sync.py tests/repomod/test_sync_cleanup.py
cpu-guard --cores 2 -- make repomod-test
cpu-guard --cores 2 -- make repomod-lint
```

The tests use local repositories and fake parent metadata, with no live fleet
sync or remote service writes. CLI and inventory formats remain unchanged.
The declared dashboard-render and OCI serving workloads are unaffected.

## Upstream fetch test qualification

At `1753a059ba256990779aa6d7f10e852e4652b621`, the `_sync_upstream`
Scenario selects 25 identities with mutmut 3.8.1. The baseline catches 17.
The fixture checks the parent repository sent to URL resolution and
verifies that full checkouts stay full. Partial parent metadata must
leave upstream untouched. A real shallow checkout fetches only the tip
of a three-commit upstream. All 25 identities are caught after those
assertions. Four separate changes fail the assertions for metadata,
parent identity and both fetch-depth decisions.

Reproduce the serial Scenario with Python 3.15.2 and mutmut 3.8.1.
In a fresh snapshot, set mutmut's `source_paths` to `["repomod"]`,
`only_mutate` to `["repomod/sync.py"]`, `also_copy` to `["fleet"]`,
pytest arguments to `["-p", "no:parallel"]`, and test selection to
`["tests/repomod/test_sync_upstream.py"]`. Use
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and run
`python -m mutmut run --max-children 1 'repomod.sync.x__sync_upstream__mutmut_*'`.
Check the selected results in `mutants/repomod/sync.py.meta`.
The whole-change workflow and other sync regions remain open.
