# Canonical checkout changes prevent fix publication

Base `40112564521758ad14bc9ed697c66d3ae08c44f7` detects a canonical HEAD
change during fixing but still admits the resulting branch to publication.
The push path checks the default branch and cleanliness, so a clean commit on
a different canonical branch bypasses those checks. A local bare-repository
witness observed both the refusal diagnostic and a pushed branch with a PR call.

The command now excludes outcomes with a publication-safety failure. The fix
outcome carries the original canonical branch and HEAD into the push path.
That path rechecks both before and after its remote query. A branch switch to
the same commit also refuses publication. Valid partial fixer results retain
their existing handling. The public CLI, package formats and fleet policy do
not change. The internal `push_fix_branch` call requires the original identity.

The command regression uses real local Git repositories and fake GitHub
responses. It failed on the base because the fake received one PR call. The
repair preserves the user's feature commit and local fix branch, with no
remote fix ref or PR call. Its positive case publishes from an unchanged
non-default checkout. Four push regressions change the canonical commit or
branch before publication or during the remote query and verify refusal.
An existing test still verifies that the exact validated fix commit is pushed
when its fix-branch ref moves during the final check.

On macOS arm64, Python 3.15, the final repomod suite passes 1,416 tests with
the three existing opt-in skips. Ruff 0.17.4 and ty 0.0.101 pass. Reproduce from
the repository root using the existing locked dev environment:

```sh
mkdir -p .work/tmp
export TMPDIR="$PWD/.work/tmp" PYTHON_CPU_COUNT=2
cpu-guard --cores 2 -- uv sync --locked --group dev
cpu-guard --cores 2 -- uv run pytest -q tests/repomod/test_fix_command.py tests/repomod/test_fix_push.py tests/repomod/test_fix_safety.py
cpu-guard --cores 2 -- make repomod-test
cpu-guard --cores 2 -- make repomod-lint
```

The full run exercises the dashboard consumer through its existing golden
tests. This failure path does not touch the declared dashboard-render or OCI
performance workloads. No runtime speed claim, real GitHub publication,
production operation or atomic exclusion of non-cooperating writers is proved.

## Publication refusal coverage

At `fb4ff6c1`, the push fixture observes both branch tips on either side
of a failed non-fast-forward push. Separate cases assert the refusal and
preserved refs when the checkout is unavailable, the origin is wrong, the
tree is dirty, or a local or remote ref has changed.

On macOS arm64 with Python 3.15.2 and mutmut 3.8.1, the original tests
caught 78 of 127 `push_fix_branch` identities. Adding the admission cases
caught 113 of 127. A second run selected the nine remaining push-error
identities and caught five once the non-fast-forward fixture was present.
Activating `__mutmut_114` makes Git raise on rejection instead of returning
the expected failure status. The new test passes with the unmutated module.

Run the Scenario in a fresh snapshot. Set `source_paths = ["repomod"]`,
`only_mutate = ["repomod/fix.py"]`, `also_copy = ["fleet"]`,
`pytest_add_cli_args = ["-p", "no:parallel"]` and
`pytest_add_cli_args_test_selection = ["tests/repomod/test_fix_push.py", "tests/repomod/test_fix_command.py"]`
in `[tool.mutmut]`. Set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and run
`python -m mutmut run --max-children 1 'repomod.fix.x_push_fix_branch__mutmut_*'`.
Compare the generated identities and results before and after the test changes.

Of the remaining identities, 29 and 30 change fallback text for an invalid
origin that `status` already describes. 46, 67 and 111 pass `None` for the
`run_git` check flag, which is false in its error branch. 55 combines two
conditions already exercised for absent refs. A nonzero `rev-parse` that
also prints a ref is unverified. 122, 124 and 125 affect diagnostics for
push processes that provide only stdout or provide no output. Those
diagnostics remain unqualified. This Scenario leaves the whole-change gate open.
