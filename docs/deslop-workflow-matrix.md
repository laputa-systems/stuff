# Matrix include reproduction

GitHub applies each include to original matrix combinations without overwriting
original values. A later include can overwrite values added by an earlier include.
Unmatched includes become separate combinations and are not candidates for later
includes. See [GitHub's matrix include example](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations#expanding-or-adding-matrix-configurations).

The retained tests call `lint_repositories` with fake branch protection and assert
the complete produced check-name sets and stale-check findings. Run them with:

```sh
TMPDIR="$PWD/.work/tmp" PYTHON_CPU_COUNT=2 cpu-guard --cores 2 uv run --group dev --quiet pytest -q tests/repomod/test_github_policy.py -k 'keeps_appended_matrix_includes_separate or matrix_include_overwrites_added_values'
```

On base `c14465ec50232d029a4fdbaf3588bb25fc6442aa`, the command exits 1:

- The Windows include lacks `python`. The next include indexes that missing axis
  and raises `KeyError: 'python'` through policy lint.
- The color example reports the two pink cat checks as stale and accepts the
  green cat checks. The later pink include should replace the added green value.

With the repair, the command exits 0 with `2 passed`. The first matrix produces
`test (linux, 3.15, yes)` and `test (windows)`. The color matrix produces
`test (apple, cat, pink, circle)`, `test (apple, dog, green, circle)`,
`test (pear, cat, pink)`, and `test (pear, dog, green)`.

## Matrix test qualification

The Scenario at `1753a059ba256990779aa6d7f10e852e4652b621` exercises
`_matrix_combinations` through workflow files and the policy caller.
Required-check handling already covered appended includes. Literal names
now also cover excludes before axes, missing keys compared with null,
includes without axes, and malformed axis names and values. Five
hand-made changes fail the matching literal assertions.

On macOS arm64 and Python 3.15.2, mutmut 3.8.1 selects 58 identities.
The baseline catches 48. The new assertions catch seven of the remaining
ten. The three equivalents, 26, 29 and 30, remove or disable the zip length
check. Every product tuple has exactly one value for each axis, so all
three variants receive equal-length inputs. The 55 caught and three
equivalent outcomes cover this function. The whole-change workflow and
remaining repomod decision regions still need qualification.

To reproduce in a fresh snapshot, set mutmut's `source_paths` to
`["repomod"]`, `only_mutate` to `["repomod/workflow_checks.py"]`,
`also_copy` to `["fleet"]`, pytest arguments to `["-p", "no:parallel"]`,
and test selection to `["tests/repomod/test_github_policy.py"]`. Use
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and run
`python -m mutmut run --max-children 1 'repomod.workflow_checks.x__matrix_combinations__mutmut_*'`.
Inspect the selected identities and exit codes in
`mutants/repomod/workflow_checks.py.meta`.
