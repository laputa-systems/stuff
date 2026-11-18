# Fixer path admission

Repomod checks every fixer plan before applying it to a disposable Git
worktree. `tests/repomod/test_fix_safety.py` exercises absolute paths, empty
normalized paths, parent traversal, Windows separators, noncanonical spelling,
paths outside a rule's allowed scope, and symbolic links. The tests check the
rejection diagnostic and verify the canonical checkout's commit and bytes.

At `0d15d8ef`, mutmut 3.8.1 selected 29 identities in `_validate_path`.
The original invalid-plan and symlink test caught 15. The candidate selects
that test, the new path-admission cases, and the existing canonical-change
test, which applies a valid plan. The candidate catches 27 identities.
The survivors are `__mutmut_27`, where `strict=None` behaves like
`strict=False` on the supported Python, and `__mutmut_29`, which removes the
final containment error text. No current fixture reaches that error after
the symlink walk. Keep that race-sensitive diagnostic unqualified.

Run from a fresh snapshot with Python 3.15.2 and mutmut 3.8.1. Set
`source_paths` to `["repomod"]`, `only_mutate` to `["repomod/fix.py"]`,
`also_copy` to `["fleet"]`, and `pytest_add_cli_args` to `["-p", "no:parallel"]`.
Set `pytest_add_cli_args_test_selection` to these three pytest selectors.

- `tests/repomod/test_fix_safety.py::test_invalid_plan_and_symlink_target_are_rejected`
- `tests/repomod/test_fix_safety.py::test_fixer_rejects_invalid_paths_before_writing`
- `tests/repomod/test_fix_safety.py::test_canonical_change_during_fix_preserves_commits_on_fix_branch`

Set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and run
`python -m mutmut run --max-children 1 'repomod.fix.x__validate_path__mutmut_*'`.
Read the results for that pattern with `python -m mutmut results --all true`.
This is one Scenario. The fix-plan and publication union still needs
whole-change qualification.
