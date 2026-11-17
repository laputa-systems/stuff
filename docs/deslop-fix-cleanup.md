# Repomod fix lanes cleanup

Cleanup ran from `/Users/josh/d/stuff/.work/wt/clf` at integration SHA
`c14465ec50232d029a4fdbaf3588bb25fc6442aa`. All five supplied lane heads were
ancestors of that SHA, each checkout was clean, and the coordinator confirmed
the workers and reviewer had finished. `lsof -nP +D <exact-path>` returned no
open files for each candidate (exit 1, empty output).

| Candidate | Lane head | Result | Evidence |
| --- | --- | --- | --- |
| `/Users/josh/d/stuff/.work/wt/fp` | `eb47b6f433c37d8ff669d92321ac5ab06368065b` | Removed; helper deleted `fix/canonical-publication` | [test_fix_command.py](../tests/repomod/test_fix_command.py#L15) |
| `/Users/josh/d/stuff/.work/wt/sp` | `0d0504f3209fa42224d88351bcf5e5ed73f7b485` | Removed; helper deleted `fix/snapshot-preflight` | [test_deps_snapshot.py](../tests/repomod/test_deps_snapshot.py#L606) |
| `/Users/josh/d/stuff/.work/wt/mc` | `44b16efdfd99b226aca3b24118bdb78863028b7f` | Removed; helper deleted `fix/mirror-catalog-validation` | [test_deps_world.py](../tests/repomod/test_deps_world.py#L304), [cache failure coverage](../tests/repomod/test_deps_world.py#L321) |
| `/Users/josh/d/stuff/.work/wt/ur` | `ae984c76a253136531847e0e12b789c547163e7c` | Removed; helper deleted `fix/preserve-upstream-state` | [test_sync_upstream.py](../tests/repomod/test_sync_upstream.py#L50) |
| `/Users/josh/d/stuff/.work/wt/fpr` | `eb47b6f433c37d8ff669d92321ac5ab06368065b` | Removed; helper deleted `review/canonical-publication` | Independent read-only review lane; no ignored files |

There were no retained candidates among the five eligible paths. The other
worktrees, including `accepted`, `rt`, `wm`, `dr-core`, `dr-deps`, `dr-policy`,
the primary checkout, preserved checkouts, and `.git/deslop-evidence/`, were
outside the eligible set and left untouched.

## Preserved ignored evidence

Before discarding ignored files, copied 18 task logs from `fp`, `sp`, `mc`, and
`ur` to private repo-local
`.git/deslop-evidence/20261117-repomod-fixes/` (directory mode `700`, files
mode `600`). Every archive copy passed byte-for-byte `cmp` against its source.
The only other ignored contents were rebuildable pytest/ruff caches, Python
bytecode, and empty uv lock files. The regression tests and source remain
tracked at the paths above. No target directory, environment, or build cache
was archived. The following SHA-256 values identify the preserved logs:

| Archive file | SHA-256 |
| --- | --- |
| `fp-fail-first.log` | `4d5317831cb49705686176489db54256dafca0422fc8200db30846285dc4c692` |
| `fp-focused.log` | `c9e21dfd09530a990dc2a6f9b5117d6ffe93f68fd69fff610562493efc7591a5` |
| `fp-full-tests.log` | `afebb522443a5cdaed0b1c506dc613508097b60f5ccd0757e5a8a1f550e64939` |
| `fp-lint-no-pythonpath.log` | `d63ab3df51a50c66f9c57056288c7d4faf9dce413552d89215714320ac2b748e` |
| `fp-lint.log` | `e6c980f7edcc2e9b140ce6cb629b947e11e61f4523391a4fee61df8acac7b15c` |
| `sp-fail-first.log` | `c015efa0962946d5e5ec7bc0554bd3091dfdb643eb07be50637d214baa73b866` |
| `sp-focused.log` | `dda4530b8dbf72bc118d1cfbcb8e2e03ab0dae252beffc68d9e0e8ac6a02f65c` |
| `sp-full-tests.log` | `ec9703c5b6dd2ba77dbc5863a748e665b9535f81f725b2527591a95ff6b53e43` |
| `sp-lint.log` | `d63ab3df51a50c66f9c57056288c7d4faf9dce413552d89215714320ac2b748e` |
| `mc-fail-first.log` | `3b8f03785fc1d97ced06eaa7f03eb52cc7b53232d532d70068366e13efb43bef` |
| `mc-focused.log` | `2e05b6c630a14908c41ddc7e6288f801c876377d8b86ca27ead59a79e357f759` |
| `mc-full-tests.log` | `f90d1d6eedb830ddf84976e116dc638ea32b3bfe860c54f64ba2ac560f86ff64` |
| `mc-lint-final.log` | `d63ab3df51a50c66f9c57056288c7d4faf9dce413552d89215714320ac2b748e` |
| `mc-lint.log` | `c81d3d87c7ad77e0a2c597a556837bce7b55ab7116dea515a0aab1f8b7e78162` |
| `ur-fail-first.log` | `d5fc395bf52ce363e95ecd4953ab8cdd01973c5c65b0a55d31b98d6080ec3f1c` |
| `ur-focused.log` | `78a2f170ed50e427bfee2d000bb31341deb8e8705fed23eada9c028f74414024` |
| `ur-full-tests.log` | `da00a78bc0e9a6e706885d6d95dbfc23717b1df65fc8c1aa07205a52df8d0032` |
| `ur-lint.log` | `d63ab3df51a50c66f9c57056288c7d4faf9dce413552d89215714320ac2b748e` |

## Commands and disk evidence

For each candidate, `git status --short --untracked-files=all` was empty,
`git rev-parse HEAD` matched the table, and
`git merge-base --is-ancestor <lane-head>
c14465ec50232d029a4fdbaf3588bb25fc6442aa` exited 0. The coordinator supplied
the merged PR and green CI verdicts; this pass did not rerun tests or CI.

Each preview initially returned exit 1 only to require review of ignored paths;
after review, the exact removal commands below each exited 0 and reported the
lane head as an ancestor of the pinned integration SHA:

```text
worktree-retire /Users/josh/d/stuff/.work/wt/fp --into c14465ec50232d029a4fdbaf3588bb25fc6442aa --discard-ignored
worktree-retire /Users/josh/d/stuff/.work/wt/sp --into c14465ec50232d029a4fdbaf3588bb25fc6442aa --discard-ignored
worktree-retire /Users/josh/d/stuff/.work/wt/mc --into c14465ec50232d029a4fdbaf3588bb25fc6442aa --discard-ignored
worktree-retire /Users/josh/d/stuff/.work/wt/ur --into c14465ec50232d029a4fdbaf3588bb25fc6442aa --discard-ignored
worktree-retire /Users/josh/d/stuff/.work/wt/fpr --into c14465ec50232d029a4fdbaf3588bb25fc6442aa --discard-ignored
```

Post-removal `git worktree list --porcelain` and filesystem checks confirmed all
five exact paths absent; no other entry was removed. The cleanup checkout stayed
clean at the pinned SHA. `du -sk` measured the five candidates at 196,696 KiB
before retirement and the preserved archive at 88 KiB after retirement: the
combined measured allocation went from 196,784 KiB (201,506,816 bytes) to
88 KiB (90,112 bytes). This is scoped path usage, not a filesystem-wide delta.
