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

## Publication diagnostics

The fixer publication tests now exercise stderr, stdout and the
fallback message when the push command fails. Real local Git
preflight and refs are used throughout. Only the final subprocess
result is supplied by the test. Every case checks the preserved
local refs and the unchanged disposable bare remote.

Mutmut 3.8.1 selected the same 127 `push_fix_branch` identities at
source blob `a1a7e6e7ecd0dd512c5f66cfab3e34eb997ba28d`. The original
suite caught 118. With the diagnostic table, 121 were caught and
IDs 122, 124 and 125 moved from surviving to caught. No identity
was unrun in either completed run. All 22 publication tests and
repomod lint passed.

The six remaining identities have bounded equivalence dispositions:

- IDs 29 and 30 change the fallback for a checkout with a bad origin.
  Every present, valid checkout with an invalid origin carries an
  explicit error from `GitStatus`.
- IDs 46, 67 and 111 pass `None` where `run_git` receives `False`.
  The subprocess wrapper tests the value only for truthiness.
- ID 55 changes the disjunction on the return code and output of
  `git rev-parse --verify` for one full ref. The command either prints
  one object ID and succeeds or fails with empty stdout.

Use the same isolated setup as the path witness, select
`tests/repomod/test_fix_push.py`, and run
`python -m mutmut run --max-children 2 'repomod.fix.x_push_fix_branch__mutmut_*'`.
Each test process runs pytest serially. The separate hosted
whole-change recipe still needs this scope and its cost validated.
