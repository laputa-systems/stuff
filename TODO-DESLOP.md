Prefix: DSLP
Next: 9

Deslop campaign backlog ([plan](https://github.com/laputa-systems/stuff/blob/main/docs/campaigns/deslop.md), tier Calibration). One agent works this file with the `deslop` skill: take the lowest-numbered open ticket whose area does not start with `Needs owner ·`. After DSLP-5, work the open P1 and P2 findings, then fill in `## Report` below.

## Report

Ground: base `6257776`. PR CI already ran `make test` (the seeded fact was stale). Warm `make test` 163s, `make repomod-test` 60s (1,348 passed, 3 skipped), `make lint` 19s on macOS. stats-producer is pristine and minisearch is modified; both record their upstream. DSLP-3 to DSLP-5 are scoped to the `repomod/` component with named contracts and acceptance commands.

Diagnose covers the repomod calibration component at `40112564`, with five
confirmed P2 findings and two P3 findings. All five P2 fixes merged in #51–54
and #57. DSLP-7 and DSLP-8 remain open at P3.
The baseline passes 1,410 tests with three existing opt-in skips and lint.
Evidence, reproduction and review limits are in [the component review](docs/deslop-repomod-diagnose.md).
Other Stuff components remain separate tier D work.

Types at `0d15d8ef` retains ty 0.0.101 with all rules at error and Ruff 0.17.4
with the existing Bugbear and return checks. `make repomod-lint` passes.
[DSLP-3 evidence](docs/deslop-repomod-types.md) records the strict candidates,
the two checker witnesses, and the reduction from 324 to 319 source lines
containing a typing escape hatch. The finite Tests inventory is recorded in [the tests review](docs/deslop-repomod-tests.md); hosted publication mutation qualification remains outstanding and wider sweeps are advisory.

Dead code is complete for Repomod. [The review](docs/deslop-repomod-dead-code.md)
records deleted paths and the six dynamic uses. All 98 CLI, catalog,
snapshot and dashboard checks passed. The canonical preview rendered
31 pages.

## Tickets

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

