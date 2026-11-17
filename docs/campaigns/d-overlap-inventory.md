# `~/d` overlap inventory

Inventory the immediate directories and symlinks under `/Users/josh/d` before preserving or trashing any duplicate checkout. This report records the read-only snapshot from 2026-11-16. No source or canonical repository was changed.

The subsequent [preservation and Trash operation](d-overlap-preservation.md)
completed for all 29 overlaps. This document retains the original inventory;
the linked record gives the current worktree and recovery locations.

## Method and result

The scan compared each Git repository under `/Users/josh/d` with canonical repositories below `/Users/josh/repos`. It matched normalized remote host and repository identities, including nested repositories under `laputa-systems`. It also compared Git top-level and common-dir paths. A matching basename alone did not count.

The scan found 29 identity overlaps, 12 retained directories, and no ambiguous identity matches. Every overlap root has an empty index. Its staged deletion count equals the tracked path count at `HEAD`, so those root deletions are intentional no-checkout artifacts, not user edits. The JSON inventory records the exact roots, identities, HEADs, local branches, tags, stash refs, registered worktrees, worktree HEADs, status paths, and ignored-directory evidence.

| Source | Canonical repository |
| --- | --- |
| `/Users/josh/d/buildlib` | `/Users/josh/repos/laputa-systems/buildlib` |
| `/Users/josh/d/diff-pretty` | `/Users/josh/repos/laputa-systems/diff-pretty` |
| `/Users/josh/d/extensions` | `/Users/josh/repos/extensions` |
| `/Users/josh/d/fd` | `/Users/josh/repos/laputa-systems/fd` |
| `/Users/josh/d/fz` | `/Users/josh/repos/laputa-systems/fz` |
| `/Users/josh/d/gh` | `/Users/josh/repos/gh` |
| `/Users/josh/d/git-build` | `/Users/josh/repos/laputa-systems/git-build` |
| `/Users/josh/d/gluon` | `/Users/josh/repos/laputa-systems/gluon` |
| `/Users/josh/d/img` | `/Users/josh/repos/img` |
| `/Users/josh/d/jaq` | `/Users/josh/repos/laputa-systems/jaq` |
| `/Users/josh/d/loc` | `/Users/josh/repos/loc` |
| `/Users/josh/d/lz` | `/Users/josh/repos/lz` |
| `/Users/josh/d/mactop` | `/Users/josh/repos/mactop` |
| `/Users/josh/d/node-build` | `/Users/josh/repos/laputa-systems/node-build` |
| `/Users/josh/d/play` | `/Users/josh/repos/play` |
| `/Users/josh/d/pytest-parallel` | `/Users/josh/repos/pytest-parallel` |
| `/Users/josh/d/rage` | `/Users/josh/repos/laputa-systems/rage` |
| `/Users/josh/d/rg` | `/Users/josh/repos/laputa-systems/rg` |
| `/Users/josh/d/rust-fontconfig` | `/Users/josh/repos/laputa-systems/rust-fontconfig` |
| `/Users/josh/d/soulseek-rs` | `/Users/josh/repos/soulseek-rs` |
| `/Users/josh/d/srv` | `/Users/josh/repos/laputa-systems/srv` |
| `/Users/josh/d/ssh-build` | `/Users/josh/repos/laputa-systems/ssh-build` |
| `/Users/josh/d/stats` | `/Users/josh/repos/stats` |
| `/Users/josh/d/syncthing` | `/Users/josh/repos/syncthing` |
| `/Users/josh/d/tm` | `/Users/josh/repos/laputa-systems/tm` |
| `/Users/josh/d/toolbox` | `/Users/josh/repos/toolbox` |
| `/Users/josh/d/usr` | `/Users/josh/repos/usr` |
| `/Users/josh/d/vault` | `/Users/josh/repos/laputa-systems/vault` |
| `/Users/josh/d/zzz` | `/Users/josh/repos/laputa-systems/zzz` |

## Preserve before trash

Preserve every source's local refs, every registered worktree, and every detached worktree `HEAD`. Preserve true modifications and untracked files in linked worktrees. The full ref OIDs and worktree status paths are in `.work/tmp/d-overlap-inventory.json` for the parent handoff.

Keep `/Users/josh/d/vault/.work` and `/Users/josh/d/diff-pretty/.work`, including the stopped mutation receipts at `/Users/josh/d/vault/.work/tmp/deslop-cleanup-salvage` and `/Users/josh/d/diff-pretty/.work/tmp/deslop-cleanup-salvage`. Keep all original parked branches and the active resumed branches:

- Vault: `refs/heads/deslop/tests-resume` at `0561a3e34828db0164d2a2baedfad2c1a7b3a611` is draft PR 30. Also preserve `refs/heads/deslop/gate-negative`, `refs/heads/deslop/store-gate`, and `refs/heads/deslop/tests`.
- Diff: `refs/heads/deslop/tests-resume` at `49a1c97d1f60932c3d860318672ecdcc545a0986` is draft PR 31. Also preserve `refs/heads/deslop/tests` and `refs/heads/deslop/types`.
- Tm: `refs/heads/fix/deslop-macos-repeat-flake` at `6a36076fcb903d9dea2f11bf0246b7817157940a` is PR 37 awaiting macOS CI. Its workers are stopped.

The Diff baseline worktrees have a modified `.gitignore` at `tests-baseline` and modified `scrl/benches/bench.rs` at `types-baseline`. The Fz `equivalent-probe` worktree has eight modified tracked paths; its `tests-baseline` worktree has an untracked `.profraw` file. Preserve these paths with their worktrees. Their exact locations and heads are in the JSON.

The process snapshot found a Node worker-bridge owner holding sockets under Vault, Diff, Tm, and Extensions. Confirm those consumers are stopped before removing their socket paths. The `niceforge` local runner, controller, and VM processes are live; retain `/Users/josh/d/niceforge` and `/Users/josh/d/niceforge-local`, and do not stop or restart them.

## Retain explicitly

Always retain `/Users/josh/d/stuff` as the active integration checkout and `/Users/josh/d/www` as an explicit nonoverlap. The other nonoverlap directories are `.cloudflare`, `.work`, `finances`, `gcsf`, `low-quality-transcripts`, `nanoshop`, `niceforge`, `niceforge-local`, `shadowdriver`, and `stonks`. The `finances` directory was not read.

The JSON is a nonsecret read-only inventory artifact, not a backup. The parent must complete preservation before any trash action. No trash, preservation, process, or canonical-repository mutation was performed for this inventory.
