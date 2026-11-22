# Fleet settlement and cleanup, 2026-11-22

The [fleet source audit](fleet-audit.md) is the review of all 72 managed repositories. This record covers branch settlement in Stuff and worktrees retired during the audit.

Stuff integrated 23 branch tips and pushed the integration through `4829a21f8364`. GitHub shows [PR 92](https://github.com/laputa-systems/stuff/pull/92) merged at `899c1b378d`. Repomod Ruff and ty passed, and the integration suite passed 1,565 tests with three skips. The follow-up checks passed 74 retention and musl policy tests and six OpenOrange readiness, tailnet, and fixture tests. The follow-up history merges kept the verified source tree. Asterinas [CI](https://github.com/laputa-systems/asterinas/actions/runs/45078012858) and [lint](https://github.com/laputa-systems/asterinas/actions/runs/45078012782) passed on `635c97e1118a`.

## Integrated history

- `3408e1a04d` chore/deslop-cleanup-apps
- `68f6f77b8c` chore/deslop-cleanup-builds
- `427a0f04d3` chore/deslop-cleanup-cli
- `16162d7084` chore/deslop-cleanup-systems
- `c1f446f08e` chore/managed-cleanup-inventory
- `536ffc1e4d` feat/coordinator-handoff
- `9215688b84` feat/primary-route
- `aeb88332ab` feat/stuff-primary-vm
- `712f4f2f01` fix/mutants-gate-per-file-critical
- `b89dcad32b` repomod/fix/7f449b1e0c184eb68f49327738a553f1
- `899c1b378d` ci/deslop-repomod-mutation (also ci/deslop-repomod-snapshot-shard at the PR head)
- `6dc6c9d3ab` feat/stats-runtime-hardening
- `354f3246d0` docs/router-refresh
- `3a5d243130` policy/retain-fz-assurance
- `07fbc1fc24` fix/stats-campaign-blockers
- `65093ac9e7` fix/inventory-read-refusals
- `3d3749e581` feat/stuff-handoff
- `c036cf9e07` chore/h12tiny-upstream
- `23c8070408` fix/stable-cmake-fleet-policy
- `72d7a1cdd8` docs/deslop-managed-cleanup-wave-two
- `bd83684625` fix/actor-lifecycle
- `69012aa804` fix/openorange-boot-tailnet
- `4829a21f83` fix/replica-current-generation

## Branches preserved on GitHub

These tips still have distinct patches outside the default branch. Branches with only patch-equivalent commits already have their changes in main.

| Branch | Tip | Reason |
| --- | --- | --- |
| `build/linux-dev-setup` | `3a4d0ca7c660` | Historical setup and campaign snapshot conflicts with the current command reference and retired campaign index. |
| `deslop/controller-alignment` | `61f18b891143` | Older controller policy and ticket layout conflict with current fleet rules and campaign closure. |
| `deslop/repomod-finish` | `14904fe1b988` | Snapshot revises the retired test and benchmark notes and conflicts with the current ticket ledger. |
| `deslop/stuff-publisher` | `248d3df6fa69` | Earlier diagnosis and typing notes use the retired campaign ticket ledger. |
| `deslop/stuff-publisher-tests` | `b19099e7eefa` | Earlier publisher test and dead-code findings use the retired campaign ticket ledger. |
| `docs/deslop-stable-alpine-checkpoint` | `89892c11244f` | Pre-closure scorecard and policy would replace newer retention decisions. |
| `docs/deslop-tier-a-settlement` | `f716efa95bb7` | Status snapshot includes the retired roadmap and an older scorecard. |
| `feat/buildlib-usage-rule` | `0e43f9e04dc0` | PR 192 carries the current rule and tests. This earlier policy conflicts with current repository dispositions. |
| `feat/registry-failover` | `e7a091f02ac5` | PR 181 shipped failover. This pre-deployment version conflicts with the later replica tests and deployment contract. |
| `fix/staged-sqlite-refusal` | `a690f5bf50d4` | PR 34 shipped the refusal repair. The private diagnostic sequence conflicts with the current patch index, diagnosis and backlog. |
| `parked/deslop-managed-cleanup-20261119` | `2a628dd927eb` | Read-only inventory retains pre-retirement decisions that differ from the dated final receipt. |
| `test/deslop-repomod-deletion` | `0c67aa31dee2` | Mutation trial control removes test coverage. |
| `test/deslop-repomod-docs` | `87374f4f3ee3` | Documentation-only mutation trial control. |
| `test/deslop-repomod-mixed` | `0a50e824a899` | Mutation trial control alters source and removes coverage. |
| `test/deslop-repomod-region-mixed` | `d5d77f713d2d` | Source-region trial control alters source and removes coverage. |
| `test/deslop-repomod-region-uncovered` | `dac988911e07` | Source-region trial control alters cleanup behavior. |
| `test/deslop-repomod-uncovered` | `193c3b3b56d2` | Mutation trial control alters cleanup behavior. |

## Local cleanup

The clean Stuff lanes `.work/wt/stuff-primary-vm` and `.work/wt/settle` were ancestors of the kept default branch and are gone. The clean Asterinas lane `.work/wt/reject-empty-test` was integrated at the pushed Asterinas revision and is gone. The retirement tool deleted all three lane branches. Stuff also pruned the local branches below after verifying reachability from `origin/main`. System-volume availability was 163 GiB before the cleanup and 169 GiB after retirement, rounded down. APFS availability also changes with unrelated disk activity.

| Kept Stuff worktree | Integration or ownership evidence |
| --- | --- |
| `.work/wt/build-main` | Detached checkout with build contexts. The owner and live consumers were unverified. |
| `.work/wt/coordinator-handoff` | Integrated and clean. Kept the ignored source snapshot and development state. |
| `.work/wt/envoy-storm` | Checked-out lane with a nested Rivet tree and worktree data of unverified ownership. |
| `.work/wt/oo-native-finish` | Local Worker migration source and tests need attribution before integration. |
| `.work/wt/oo-recovery` | Local backup and rehearsal source and tests need attribution before integration. |
| `.work/wt/oo-stuff-dev-deploy` | Local development deployment source and test need attribution before integration. |
| `.work/wt/primary-route` | Integrated and clean. Kept the ignored fixture and check scripts. |
| `.work/wt/stats-campaign-blockers` | Integrated committed tip. Kept the local ticket proposal. |
| `.work/wt/stuff-handoff` | Integrated and clean. The lane owner and live consumers were unverified. |

The unpublished files in the dirty lanes include `crates/stuff-worker/orange.jsonc`, `crates/stuff-worker/scripts/dev.mjs`, `crates/stuff-worker/src/runtime-types.ts`, `crates/stuff-worker/test/dev-orange.test.mjs`, `deploy/openorange/tests/test_backup_recovery.py`, `deploy/openorange/tests/test_restore_rehearsal.py`, `crates/stuff-worker/orange/deploy.sh`, and `crates/stuff-worker/test/deploy-orange.test.mjs`. Stash `stash@{0}` remains based on Stuff main at `6c2df3e25` and changes one line in `Cargo.toml`.

### Pruned local Stuff branches

- `chore/deslop-cleanup-apps`
- `chore/deslop-cleanup-builds`
- `chore/deslop-cleanup-cli`
- `chore/deslop-cleanup-systems`
- `chore/h12tiny-upstream`
- `chore/managed-cleanup-inventory`
- `ci/deslop-repomod-mutation`
- `ci/deslop-repomod-snapshot-shard`
- `ci/deslop-repomod-source-regions`
- `deslop/f2-test-workflow`
- `docs/buildlib-close`
- `docs/deslop-calibration-results`
- `docs/deslop-contract-results`
- `docs/deslop-current-results`
- `docs/deslop-managed-cleanup-wave-two`
- `docs/deslop-module-results`
- `docs/release-archives-status`
- `docs/resolve-stuf-82`
- `docs/resolve-stuf-84`
- `docs/router-refresh`
- `docs/stuf89-progress`
- `docs/todo-2026-11-16-review`
- `feat/owned-tool-support`
- `feat/stats-runtime-hardening`
- `fix/actor-lifecycle`
- `fix/archive-fixer-keeps-comments`
- `fix/doctor-mirror-file-name`
- `fix/inventory-read-refusals`
- `fix/mutants-gate-per-file-critical`
- `fix/r2-upload-timeout`
- `fix/replica-current-generation`
- `fix/runner-amd64-on-arm`
- `fix/stable-cmake-fleet-policy`
- `fix/stats-campaign-blockers`
- `fix/worker-miniflare-response-owners`
- `fleet/scoped-clean`
- `policy/retain-fz-assurance`
- `repomod/fix/7f449b1e0c184eb68f49327738a553f1`
