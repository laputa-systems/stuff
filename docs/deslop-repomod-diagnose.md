# Repomod calibration review

This review covers the `repomod/` calibration component at
`40112564521758ad14bc9ed697c66d3ae08c44f7`. Three independent lanes reviewed
command and Git ownership, dependency inventory, and policy and fixer boundaries.
The integrator checked the candidate findings with owned local fixtures.
The other Stuff components were not reviewed by this pass.

The locked Python 3.15 environment passes `make repomod-lint` and all 1,410
repomod tests with the three existing opt-in skips. Commands used
`TMPDIR=$PWD/.work/tmp`, `PYTHON_CPU_COUNT=2` and `cpu-guard --cores 2`.
No live fleet command, registry refresh, publication or production operation ran.
Reviewing workflow source did not authorize workflow or mutation-gate repairs.

## Findings

Priorities are assumed from demonstrated impact and likelihood. Four P2 findings
have separate repairs; their source changes are not part of this review.

| Priority | Finding and evidence | Reproduction and repair |
| --- | --- | --- |
| P2 | A detected canonical change still permits fix publication. `repomod/fix.py:509` reports a refusal while `repomod/cmd/fix.py:154` still selects the branch. | Commit on a canonical feature branch from a fixer callback, then run the real command against a local bare origin and fake GitHub. The base prints the refusal, pushes the branch and calls the PR fake. [Repair #51](https://github.com/laputa-systems/stuff/pull/51) contains the retained regression. |
| P2 | Index validation follows repository-record writes. `repomod/dependencies/snapshot.py:203` changes data before line 208 rejects the index. | Snapshot a real checkout, commit a changed package input, corrupt the index parser version, schema or JSON, and compare every inventory file after rejection. All three base cases change a record. [Repair #52](https://github.com/laputa-systems/stuff/pull/52) retains the controls. |
| P2 | Malformed mirror records become a successful partial refresh. `repomod/audit.py:1494` skips invalid records or substitutes empty versions; `dependencies/enrich.py:378` accepts the result. | Seed a valid mirror cache, return a non-array versions field or malformed version record from the actual reader, and refresh. The base reports no error and replaces the prior data. [Repair #53](https://github.com/laputa-systems/stuff/pull/53) verifies full-map and timestamp preservation. |
| P2 | Repointing upstream removes tracking state. `repomod/git.py:393` removes and recreates the remote. | Create an upstream-only commit ref, track it from the current branch, add a push URL, then repoint through sync. The base removes the ref, branch tracking and push URL. [Repair #54](https://github.com/laputa-systems/stuff/pull/54) updates the URL in place and verifies preservation through the parent fetch. |
| P2 | Matrix includes can crash policy lint or produce incorrect required-check names. `repomod/workflow_checks.py:106` indexes an axis missing from an appended include; line 111 retains earlier additional values. | An `os`/`python` matrix with includes `[{os: windows}, {python: '3.15', extra: yes}]` raises `KeyError: 'python'` through the existing fake policy caller. A later `color: pink` include retains `green`. Keep original combinations distinct from appended includes and apply updates according to GitHub's documented semantics. |
| P3 | A post-commit interruption removes the recovery branch. `repomod/fix.py:486` records the commit after the fixer returns; cleanup at line 491 sees an empty recorded list. | Wrap `_commit_paths` to call the real implementation and then raise `KeyboardInterrupt`. The completed commit remains readable by SHA, but no fix branch refers to it. Eventual object collection and permanent loss were not tested. |
| P3 | A filtered line-count snapshot drops unselected index entries. `repomod/loc.py:66` writes an index built from selected inspections. | Snapshot repositories A and B, then snapshot only A with `filtered=True`. B's record remains but its index entry disappears. The dashboard reads retained files directly, so a missing dashboard row was not demonstrated. |

GitHub's [matrix include contract](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations#expanding-or-adding-matrix-configurations)
confirms that later includes may replace additional values on original
combinations, while newly appended combinations remain separate.

Fix with `lifecycle-concurrency` for canonical publication, upstream state and
interrupted commits. Use `durable-state` for snapshot preflight and the filtered
line-count index, `typing-audit` and `error-model` for mirror parsing, and
`root-cause` for matrix expansion.

The matrix failure is reproducible without GitHub or workflow execution:

```python
from repomod.workflow_checks import _matrix_combinations
_matrix_combinations({"matrix": {
    "os": ["linux"], "python": ["3.15"],
    "include": [{"os": "windows"}, {"python": "3.15", "extra": "yes"}],
}})
```

Use an isolated worktree at the base revision with the locked dev environment
to reproduce pre-repair behavior. For the upstream witness, create a real local
checkout with `tests/repomod/git_helpers.py`, add an upstream remote and a
`refs/remotes/upstream/preserved` commit, and set the current branch's upstream
to it. `sync_one` with a local fake parent exercises both reconfiguration and
fetch. For the filtered line-count witness, supply two `loc.Inspection` records
through `_inspect_all`, then one, and compare `index.json` with retained files.
These fixtures need no private repository or service.

## Rejected leads and limits

Sync rechecks branch, HEAD and cleanliness before fast-forwarding. The removal
contract already documents the residual race with non-cooperating writers
after final inspection. No separate defect was established in either path.
The inspected fixer boundary rejects traversal and symlinks and validates the
file plan and policy result before committing. This is not an exhaustive proof
of every rule, adapter, fixer or concurrency interleaving.

The review does not qualify Types, Tests, Dead code, whole-change CI, live
services or the rest of Stuff. Preserve canonical user work, explicit validated
fix plans, read-only rules, and the separation between published inventory and
canonical checkout state.
