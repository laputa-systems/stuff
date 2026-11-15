Prefix: DSLP
Next: 6

Deslop campaign backlog ([plan](https://github.com/laputa-systems/stuff/blob/main/docs/campaigns/deslop.md), tier Calibration). One agent works this file with the `deslop` skill: take the lowest-numbered open ticket whose area does not start with `Needs owner ·`. After DSLP-5, work the open P1 and P2 findings, then fill in `## Report` below.

## Report

Ground: base `6257776`. PR CI already ran `make test` (the seeded fact was stale). Warm `make test` 163s, `make repomod-test` 60s (1,348 passed, 3 skipped), `make lint` 19s on macOS. stats-producer is pristine and minisearch is modified; both record their upstream. DSLP-3 to DSLP-5 are scoped to the `repomod/` component with named contracts and acceptance commands.

## Tickets


### DSLP-2 · P2 · Diagnose: ultrareview into this backlog

- **Area:** deslop · diagnose
- **Where:** whole repository
- **Problem:** No review has ranked this repository's risks for the deslop pass.
- **Recommendation:** Run the deslop Diagnose step. Accept: the diff touches only docs, comments, and this file, and every finding names its Fix with.
- **Fix with:** deslop
- **Effort:** M

### DSLP-3 · P2 · Types: strict profile and typing findings

- **Area:** deslop · types
- **Where:** repomod/ (ty and Ruff config in pyproject.toml)
- **Problem:** Scope: the repomod/ component only (calibration); the other components follow in tier D as their own bounded tasks. Contracts: the repomod CLI (commands, flags, exit codes, JSON output), fleet/catalog.toml, fleet/dependencies/v1/ and fleet/loc/v1/, and the catalog.json reader. Consumers: the dashboard render (tests/repomod/test_dashboard_preview.py golden) and make deps; no other repository imports repomod. Python strict candidates: ty rules at error, Ruff ANN, ANN401, PGH003, TC, B, RET. Accept: make repomod-lint and make repomod-test.
- **Recommendation:** Run the deslop Types step. Accept: clean at the adopted profile, escape hatches not increased, witnesses recorded.
- **Fix with:** deslop
- **Effort:** M

### DSLP-4 · P2 · Tests: coverage, boundary gaps, mutation

- **Area:** deslop · tests
- **Where:** repomod/ and tests/repomod/
- **Problem:** Scope: the repomod/ component only (calibration); the other components follow in tier D as their own bounded tasks. Contracts: the repomod CLI (commands, flags, exit codes, JSON output), fleet/catalog.toml, fleet/dependencies/v1/ and fleet/loc/v1/, and the catalog.json reader. Consumers: the dashboard render (tests/repomod/test_dashboard_preview.py golden) and make deps; no other repository imports repomod. Effect-heavy code (Git, GitHub, filesystem) behind fakes; tests run under pytest-parallel, which cannot collect coverage across workers, so coverage runs serially. Mutation scope: rules and fixers (repomod/rules/), sync and removal safety (repomod/sync.py, gc), catalog parsing. Accept: make repomod-test within the cost budget (60s warm).
- **Recommendation:** Run the deslop Tests step. Accept: no undispositioned survivor in critical code, the test cost budget holds, and the lane is green where the tools are mirrored.
- **Fix with:** deslop
- **Effort:** L

### DSLP-5 · P2 · Dead code: tools and debloat

- **Area:** deslop · dead code
- **Where:** repomod/
- **Problem:** Scope: the repomod/ component only (calibration); the other components follow in tier D as their own bounded tasks. Contracts: the repomod CLI (commands, flags, exit codes, JSON output), fleet/catalog.toml, fleet/dependencies/v1/ and fleet/loc/v1/, and the catalog.json reader. Consumers: the dashboard render (tests/repomod/test_dashboard_preview.py golden) and make deps; no other repository imports repomod. Tools: Ruff F401/F841, vulture, deptry. Accept: make repomod-lint and make repomod-test.
- **Recommendation:** Run the deslop Dead code step. Accept: tools clean or allowlisted with reasons; walk-backs filed as Needs owner tickets.
- **Fix with:** deslop
- **Effort:** M

