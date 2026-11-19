# Managed checkout cleanup inventory, 2026-11-18

## Result

No retirement candidate met the requested proof in this read-only pass. The
largest measured campaign worktree inspected is explicitly parked, contains
two commits absent from the local default branch, and has ignored build state
that the recorded campaign says is needed for unfinished qualification. It
must be retained.

The workspace root in `fleet/catalog.toml:3-4` is `~/repos`; `/Users/josh/repo`
does not exist, while `/Users/josh/repos` does. The survey used the latter,
excluded `discover`, and did not inspect or mutate canonical source content.
The catalog and prior cleanup record were read first. The prior record says
that Stats and Stuff recovery, Chromium's build, and retained performance
inputs remain active or parked (`docs/campaigns/deslop-cleanup-20261117.md:34-37`).
Those areas, including Ctrs performance, were excluded from retirement
consideration as required.

## Sized retain decision

| Exact path | Allocation (KiB) | State and integration proof | Durable receipt and decision |
| --- | ---: | --- | --- |
| `/Users/josh/repos/laputa-systems/python-build/.work/wt/jit-reference-init` | 7,774,668 | Tracked/untracked status is clean. Worktree HEAD is `e3cbf337da88d67b125db8f10be5ff55b4c4ae9e`; local `main` is `b1d8240f7d56d778b408a38c2f96ed47eef55f69`. `git merge-base --is-ancestor <HEAD> main` exits 1; `git cherry main <HEAD>` shows `+ eb7f262ee510c0c3eb06f6f59be24484ebfd99ce` and `+ e3cbf337da88d67b125db8f10be5ff55b4c4ae9e`. | Tracked `docs/CAMPAIGN-RUST-CPYTHON-JIT.md:4069-4070` calls this candidate parked and says native checks, focused suites, fuzzing, resource trials, export/disassembly proof, and final review remain. Lines 4073-4077 name retained trees and their consumers. The `worktree-retire --dry-run` exits 1 and lists ignored `.work/`, `rust-cpython/work/`, both perf stages, results, caches, and logs. Retain: the commits are unintegrated, the candidate is explicitly parked, and those ignored outputs have not been proven stale or durably replaced. |

The worktree's largest named generated subdirectories measured separately with
`du -sk`: `rust-cpython/work` 2,604,716 KiB,
`rust-cpython/stage-perf-jit-reference-init` 340,656 KiB,
`rust-cpython/stage-perf-jit-reference-init-noserc` 326,360 KiB, and
`rust-cpython/results` 32 KiB. These are included in the worktree allocation
above; do not add them again. The dry-run did not establish that any are
disposable. The tracked receipt's host note says historical receipts do not
apply to the re-derived slice (`docs/CAMPAIGN-RUST-CPYTHON-JIT.md:4045-4061`),
so the similar accepted ledger entry at line 4256 does not prove these exact
commits or generated outputs are integrated.

The prior Stuff campaign record identifies Smolith's old
`.work/tmp/protocol-target` as absent after its earlier cleanup
(`docs/campaigns/deslop-cleanup-20261117.md:15-19`); the path is still absent.
It is not a current reclaim candidate.

## Inventory and commands

The catalog says the managed workspace is `~/repos` (`fleet/catalog.toml:3-4`).
`/Users/josh/repo` was missing and `/Users/josh/repos` was present. A
read-only Python survey enumerated Git roots below `/Users/josh/repos` except
`discover`, plus repositories under `laputa-systems`, and ran
`git -C <repo> worktree list --porcelain` for each. It found 65 local Git
roots. The listing contains worktrees outside `/Users/josh/repos` (including
other task checkouts and temporary locations); those were excluded, not
proposed for cleanup. This was a registration census, not a clean/integration
audit of every registered path. Unknown, active, parked, dirty, locked,
orphaned, and outside-root paths remain untouched.

Candidate checks, all read-only:

```text
test -d /Users/josh/repos                         -> exit 0
test -e /Users/josh/repo                          -> exit 1
git -C /Users/josh/repos/laputa-systems/python-build/.work/wt/jit-reference-init rev-parse HEAD
  -> e3cbf337da88d67b125db8f10be5ff55b4c4ae9e (exit 0)
git -C /Users/josh/repos/laputa-systems/python-build rev-parse refs/heads/main
  -> b1d8240f7d56d778b408a38c2f96ed47eef55f69 (exit 0)
git -C /Users/josh/repos/laputa-systems/python-build/.work/wt/jit-reference-init status --porcelain=v1 -uall
  -> empty (exit 0)
git -C /Users/josh/repos/laputa-systems/python-build merge-base --is-ancestor e3cbf337da88d67b125db8f10be5ff55b4c4ae9e main
  -> exit 1 (not integrated as an ancestor)
git -C /Users/josh/repos/laputa-systems/python-build cherry main e3cbf337da88d67b125db8f10be5ff55b4c4ae9e
  -> + eb7f262ee510c0c3eb06f6f59be24484ebfd99ce
     + e3cbf337da88d67b125db8f10be5ff55b4c4ae9e (exit 0)
du -sk /Users/josh/repos/laputa-systems/python-build/.work/wt/jit-reference-init
  -> 7774668 /Users/josh/repos/laputa-systems/python-build/.work/wt/jit-reference-init (exit 0)
worktree-retire /Users/josh/repos/laputa-systems/python-build/.work/wt/jit-reference-init --into b1d8240f7d56d778b408a38c2f96ed47eef55f69 --dry-run
  -> exit 1; ignored files listed; no retirement performed
git -C /Users/josh/repos/laputa-systems/python-build ls-files --error-unmatch docs/CAMPAIGN-RUST-CPYTHON-JIT.md
  -> tracked receipt confirmed (exit 0)
```

The dry-run refusal is not a cleanup authorization. It listed ignored files;
the independent integration checks show two unique commits. No delete, fetch,
checkout switch, repository write, or commit was performed.

## Unverified cases and blockers

- The full registration census did not measure every worktree or inspect every
  worktree's status and integration. No claim is made that every registered
  path is clean, complete, or unused.
- No process/open-file check was made for a retirement because no path passed
  the completion and integration gates. Process-idle confirmation remains
  required before any future retirement.
- Stats recovery, Chromium lanes, Ctrs retained performance, active CI proof,
  canonical checkouts, dirty or locked checkouts, orphan commits, and paths
  outside `/Users/josh/repos` were retained or excluded without destructive
  action. Discover was excluded from the survey.
- No before/after volume-space measurement applies because nothing was
  removed.

Changed paths: `docs/campaigns/managed-cleanup-inventory.md` only.
