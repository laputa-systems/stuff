Prefix: DSLP
Next: 9

Deslop campaign backlog ([plan](https://github.com/laputa-systems/stuff/blob/main/docs/campaigns/deslop.md), tier Calibration). One agent works this file with the `deslop` skill: take the lowest-numbered open ticket whose area does not start with `Needs owner ·`. After DSLP-5, work the open P1 and P2 findings, then fill in `## Report` below.

## Report

Ground: base `6257776`. PR CI already ran `make test` (the seeded fact was stale). Warm `make test` 163s, `make repomod-test` 60s (1,348 passed, 3 skipped), `make lint` 19s on macOS. stats-producer is pristine and minisearch is modified; both record their upstream. DSLP-3 to DSLP-5 are scoped to the `repomod/` component with named contracts and acceptance commands.

Diagnose covers the repomod calibration component at `40112564`, with five
confirmed P2 findings and two P3 findings. Four P2 findings have separate repair
PRs (#51–54); DSLP-6 remains open under the CI work authorized on 2026-11-17,
and DSLP-7/8 remain P3.
The baseline passes 1,410 tests with three existing opt-in skips and lint.
Evidence, reproduction and review limits are in [the component review](docs/deslop-repomod-diagnose.md).
Other Stuff components remain separate tier D work. Types, Tests and Dead code
are still open.

## Tickets



### DSLP-3 · P2 · Types: strict profile and typing findings

- **Area:** deslop · types
- **Where:** repomod/ (ty and Ruff config in pyproject.toml)
- **Problem:** Scope: the repomod/ component only (calibration); the other components follow in tier D as their own bounded tasks. Contracts: the repomod CLI (commands, flags, exit codes, JSON output), fleet/catalog.toml, fleet/dependencies/v1/ and fleet/loc/v1/, and the catalog.json reader. Consumers: the dashboard render (tests/repomod/test_dashboard_preview.py golden) and make deps; no other repository imports repomod. Python strict candidates: ty rules at error, Ruff ANN, ANN401, PGH003, TC, B, RET. Accept: make repomod-lint and make repomod-test.
- **Recommendation:** Run the deslop Types step. Accept: clean at the adopted profile, escape hatches not increased, witnesses recorded.
- **Fix with:** deslop
- **Effort:** M

### DSLP-4 · P2 · Tests: coverage, boundary gaps, mutation

- **Area:** deslop · tests
- **Where:** repomod/ and tests/repomod/. Bounded contracts and test files are listed in docs/campaigns/deslop-roadmap.md under Repomod calibration inventory.
- **Problem:** Repomod is the only Stuff component in M2 calibration. Fresh serial coverage exercised 22,053 of 25,752 statements and 8,064 of 10,618 branches with 1,430 passing tests and three opt-in skips after the OSV fixture repair in #60. Matrix expansion and upstream fetch have bounded mutation Scenarios. The remaining scope includes catalog identity and tag validation, checkout and removal safety, fix-plan admission and publication, and snapshot and registry adapter decisions. The dashboard render and make deps consume these outputs. Use local Git and fake GitHub and registry endpoints.
- **Recommendation:** Resolve the listed unrun decisions and remaining survivors. Select the whole-change union through real CI and qualify the negative controls. Run make repomod-test and make repomod-lint and measure suite cost on a ready host. Keep coverage, mutation, and retention verdicts separate.
- **Fix with:** deslop
- **Effort:** L

### DSLP-5 · P2 · Dead code: tools and debloat

- **Area:** deslop · dead code
- **Where:** repomod/
- **Problem:** Scope: the repomod/ component only (calibration); the other components follow in tier D as their own bounded tasks. Contracts: the repomod CLI (commands, flags, exit codes, JSON output), fleet/catalog.toml, fleet/dependencies/v1/ and fleet/loc/v1/, and the catalog.json reader. Consumers: the dashboard render (tests/repomod/test_dashboard_preview.py golden) and make deps; no other repository imports repomod. Tools: Ruff F401/F841, vulture, deptry. Accept: make repomod-lint and make repomod-test.
- **Recommendation:** Run the deslop Dead code step. Accept: tools clean or allowlisted with reasons; walk-backs filed as Needs owner tickets.
- **Fix with:** deslop
- **Effort:** M


### DSLP-6 · P2 · Matrix include expansion can abort policy lint or misname checks

- **Area:** repomod · CI policy
- **Where:** repomod/workflow_checks.py:102-111; repomod/policy.py:188; docs/deslop-repomod-diagnose.md
- **Problem:** Confirmed on `40112564`. An os/python matrix with includes [{os:windows},{python:'3.15',extra:yes}] appends an incomplete combination, then indexes its missing python axis and raises KeyError through lint_repositories. Successive additional color values also retain green instead of GitHub's documented pink. A valid repository can abort the lint batch or receive false required-check findings. The parent reproduced both expansion defects, and the review lane reproduced the batch exception with fake GitHub. The owner explicitly authorized the deslop CI work on 2026-11-17.
- **Recommendation:** Expand includes against original matrix combinations and keep appended combinations separate. Permit later includes to overwrite only additional values. Preserve indeterminate handling for unsupported expressions and add fake-policy-caller regressions for complete check-name sets and batch completion.
- **Fix with:** root-cause
- **Effort:** M


### DSLP-7 · P3 · An interruption after a fixer commit can delete its recovery branch

- **Area:** repomod · lifecycle
- **Where:** repomod/fix.py:486-493; docs/deslop-repomod-diagnose.md
- **Problem:** Confirmed on `40112564` with a local Git fixture: wrapping _commit_paths to complete the real commit and immediately raise KeyboardInterrupt leaves outcome.commits empty. Cleanup deletes the newly created fix branch although its tip contains the completed change. The object remains readable by SHA; permanent loss or later object collection was not demonstrated.
- **Recommendation:** Before deleting a newly created fix branch, inspect its actual tip against the base and preserve any completed commit independently of the recorded outcome list. Cover the precise post-commit interruption window with a real local commit and no remote writes.
- **Fix with:** lifecycle-concurrency
- **Effort:** S


### DSLP-8 · P3 · A filtered line-count snapshot drops unselected index entries

- **Area:** repomod · inventory
- **Where:** repomod/loc.py:63-75; docs/deslop-repomod-diagnose.md
- **Problem:** Confirmed on `40112564`: snapshot two mocked real Inspection records A and B, then snapshot A with filtered=True. repos/B.json remains, but B disappears from index.json because _entries returns only selected repositories. The dashboard reads retained files directly, so missing dashboard rows were not established. The filtered metadata index no longer describes every retained repository.
- **Recommendation:** Merge selected line-count entries into the existing index for filtered snapshots while retaining full-snapshot deletion behavior. Assert the full index and unselected record bytes across a filtered refresh, including unchanged commit stamping.
- **Fix with:** durable-state
- **Effort:** S

