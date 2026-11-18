# Repomod checkout removal diagnostics

The existing removal fixtures run against disposable local Git repositories.
They prove that archive sync and garbage collection preserve dirty checkouts,
stash entries, unpublished refs and linked worktrees. The additional
table tests the first diagnostic for a checkout whose Git status rules out
removal. Cases include a detached HEAD, a missing branch or upstream, an
unknown ahead count, unpublished commits, and singular and plural stashes.
Cases with multiple blockers verify which one takes precedence.

At `7a62fcdf`, mutmut 3.8.1 generated 19 identities in
`_checkout_removal_blocker`. The existing removal-preservation tests
caught none of those 19. Adding the diagnostic table caught all 19 in
the same selection on CPython 3.15.2, pytest 9.2.0 and macOS arm64.
The production blob remained `a5dbe6cd624f37524c5e59d3d75065703f1d22fa`.
Neither run reported a timeout or uncovered identity. The filesystem,
ref recheck and removal side effects have separate integration cases.

Use the [snapshot mutation scratch setup](deslop-repomod-snapshot.md#reproduction)
with `only_mutate = ["repomod/clean.py"]` and test selection
`tests/repomod/test_removal_safety.py`. Set
`pytest_add_cli_args = ["-p", "no:parallel", "-k", "first_checkout_blocker or removal_preserves_repository_state"]`.
Run the serial selector:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m mutmut run --max-children 1 \
  'repomod.clean.x__checkout_removal_blocker__mutmut_*'
```

Inspect the complete selected results. To reproduce the baseline,
run without the diagnostic table. The retained whole-change gate and
other removal decisions still need qualification.
