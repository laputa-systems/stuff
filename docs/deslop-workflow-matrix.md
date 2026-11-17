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
