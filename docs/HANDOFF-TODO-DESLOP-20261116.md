# Owner stop: TODO and direct deslop work

The owner stopped this work on 2026-11-16 and requested committed checkpoints.
Do not resume implementation, measurements, deployment or pending merges until
asked. The original scope was all stuff P1/P2 tickets except STUF-75, plus the
non-fleet-scale deslop queue. Fleet rollout remains excluded.

## Engine and stuff

- PR34 merged as `c2e7ad8e17af5f9dda662dc965e837bd54eb2317`: three staged-write
  repairs against the attested Rivet source. Production was unchanged.
- [PR38](https://github.com/laputa-systems/stuff/pull/38) merged after all ten
  checks passed on `ccd322fd3fa2a47c1965a5cc97d7d74712f74c62`; merge commit
  `f85d8d0a9c2c59a1199b69b3e7c8ef343349540c`. It closes STUF-86 with the
  natural idle/wake proof and stages the bounded inventory API retry patch.
- [PR39](https://github.com/laputa-systems/stuff/pull/39) remains open at
  `9510e79058a4b0269402d73775c816771c83afad`, mergeable, with macOS Rust CI
  pending at stop. Do not merge without checking all results on that exact head.
  It closes STUF-87 in its branch with the fourth SQLite patch: committed-page
  read refusals preserve stages only while filesystem ownership is valid.
  Eight dev/release regressions and three hand faults pass; independent source
  review found no demonstrated introduced defect. Fresh import verifies all
  203,950 rows, and three gated Engine-only recoveries preserve the exact summary
  in 3.919/3.847/5.780 seconds from shutdown to verified data. The sanitized proof
  and qualification limits are committed in that PR.
- Combined local Rivet source: `f68e0732f44c1d0ec64e96dc425f585eeef8c255` on
  `fix/sqlite-log-read-refusal` in
  `.work/tmp/stuf-engine-source/.work/wt/log-read-refusal`. The packaged patches
  reproduce its filesystem package. No upstream Rivet branch was pushed.
- Candidate binary SHA-256:
  `611b08f609d625ad5379c3b0801f23fc76ab4e17cc3ee0210ba608bf53ae1b01`.
  It also passes a read-only, network-isolated CLI linkage smoke in the deployed
  Engine base image, reporting Rivet 3.1.1. Production configuration and traffic
  were not exercised on this candidate.
- STUF-88 remains open. The short private import probe had 4,617 successful
  inventory requests; that is not 24-hour production availability acceptance.
  The separate diagnostic collector was stopped with TERM at the owner's stop.
  Its final receipt records 466 samples, 128 failed samples and 197 failed
  requests out of 4,170, over 27,918.922 seconds. `complete` and `zeroUnavailable`
  are false. Protected evidence remains on Lisa under
  `/home/josh/d/stuff/.work/tmp/stuf88-inventory-v2-20261116/`.
- All private Engine/import/recovery fixtures are stopped. Failed depots and
  rejected setup/timing/reference receipts remain preserved. Shared `oo-engine`,
  production applications, the original Stats sampler and tailscaled were not
  stopped or restarted. STUF-75 is untouched.

## Direct deslop checkpoints

Fz is fully settled (final Report PR40 merged). Loc's stdin-directory P1 fix
is merged in PR11; diff-pretty Types PR26 is merged. The remaining direct work
is unfinished, with these committed checkpoints:

| Repository | Branch and commit | Remaining verification |
| --- | --- | --- |
| vault | `deslop/store-gate`, `35fa554` | Draft PR30; Tests/Dead code/Report unfinished. The 98-case macOS cache component and Linux store gate are qualified. Owner stopped the complementary 232-case filesystem run after 173 completed: 102 caught, 65 missed, 6 unviable, zero timeouts, 59 untested. No survivor dispositions or fixes were made during this run. |
| diff-pretty | `deslop/tests`, `5834fe7` | Nine CLI process cases and lint passed. Hand faults, final full checks, paired cost and mutation qualification remain. The before workspace run exhausted 1,200 seconds with 109 untested and 48 unconfirmed timeouts; it is not a pass. |
| extensions | `fix/deslop-vite`, `c4a2edb` | Vitest/coverage-v8 5.0.5 candidate; frozen install with scripts disabled passed. Tests, coverage and Stryker unrun; inspect optional-package engine metadata changes in the regenerated lockfile. No ticket closed. |

All three branches are pushed. Their TODO-DESLOP reports record the stop and
verification gaps. Worktrees and ignored evidence remain in place. The Vault
mutation process was stopped through its CPU guard; its shared mutation lock
was released. No local measurement or delegated worker remains active.

Other authorized direct work remains: loc mutation/dead code; stats calibration
and macOS/CI findings; stuff repomod calibration; buildlib mutation qualification;
extensions calibration; tm's macOS flake. No additional repository work was
started during the Engine close-out. Resume the campaign from its owning
`docs/campaigns/deslop.md`, then verify current branches and PR heads; this
handoff is a stop record, not a claim that the backlog is complete.
