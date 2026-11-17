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
