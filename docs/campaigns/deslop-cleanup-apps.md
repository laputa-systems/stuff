# Deslop cleanup inventory: apps

## PROOF RECORD

**Changed paths:** `docs/campaigns/deslop-cleanup-apps.md` only. No physical checkout, scratch path, or branch was removed. No commit was made.

**Scope:** personal checkouts `extensions`, `stats`, `ctrs`, `img`, `ish`, `play`, `tansu`, `usr`, `kache`; organization checkouts `laputa-systems/laputa-ui-dashboard` and `laputa-systems/gluon`. Discover was excluded. `realpath` resolved every named root to its exact `/Users/josh/repos/...` path. All ten `git worktree list --porcelain` invocations exited 0. The checkout roots and latest observed state were:

| Physical checkout | HEAD | State observed |
| --- | --- | --- |
| `/Users/josh/repos/extensions` | `66259229057b34e7405bc334f4d421f301a8431e` | clean, `main...origin/main` |
| `/Users/josh/repos/stats` | `aa2d20ea8db04f7a72d325713f00d584da4d1fec` | clean, `master...origin/master` on final inventory |
| `/Users/josh/repos/ctrs` | `9ec111ed003ff9c87a45d82899ee4be38c9b31fc` | dirty: untracked `resume.md`; preserved |
| `/Users/josh/repos/img` | `ab663fe2b08972f8d70f4bebf01ce9bb48bbb327` | clean, `master...origin/master` |
| `/Users/josh/repos/ish` | `fc62468e2428f9aea6fcd611b0820ab709ce0c65` | clean, `master...origin/master` |
| `/Users/josh/repos/play` | `bae10f91b7003e208964eab030ba024d9b6c1a49` | clean, `main...origin/main` |
| `/Users/josh/repos/tansu` | `1bf0a0dd9cd76e505ff6a607b01fd5319b34e421` | clean, `master...origin/master` |
| `/Users/josh/repos/usr` | `a9673083571e0d041d97cba199c0be8ed04c02c6` | clean, `main...origin/main [behind 1]`; preserved |
| `/Users/josh/repos/kache` | `4401c7a09498d2225ab22e7d1e74bef20211ca8f` | clean, `main...origin/main` |
| `/Users/josh/repos/laputa-systems/laputa-ui-dashboard` | `b37d7eb4894f7fb149b9e20c460859a65623b3d3` | clean, `master...origin/master` |
| `/Users/josh/repos/laputa-systems/gluon` | `ff0d5c60ffea6d361b3152a1115539207e4ec5ef` | clean, `main...origin/main` |

Stats was inventory-only. Its HEAD changed while being read: initial `rev-parse` reported `1892c42b8d4e52d024a4af44d2e38e0db9e578d4`, the first worktree listing reported `bd699309bfbe2c5018082ff070d18c19bbab8f6f`, and final `rev-parse` plus `worktree list` reported `aa2d20ea8db04f7a72d325713f00d584da4d1fec`. The earlier status also showed untracked `deploy/orange/recovery/`; the final status was clean. This concurrent change was left untouched. Its final worktree listing showed the two external `/Users/josh/d/stuff/.work/wt/stats-*` targets plus repo-local `asb`, `btree`, `ci-pnpm`, `ct`, `ctr`, `dg`, `it`, `sd`, `solid2`, `upgrade-npm-deps`, `upgrade-stats`, and `upgrade-todos`; none were retired.

## Candidate decisions

The applicable root instructions were read at `AGENTS.md` in each named checkout that has one (`extensions`, `stats`, `ctrs`, `ish`, `play`, `tansu`, `usr`, `kache`, `laputa-ui-dashboard`, and `gluon`). `img` has no root `AGENTS.md`; `/Users/josh/repos/AGENTS.md` and `/Users/josh/repos/laputa-systems/AGENTS.md` were absent. The cleanup skill was read before inspection. No code, tests, builds, release steps, remote writes, global caches, or canonical source files were changed.

Six deslop worktrees in `extensions` had clean status and their HEADs were ancestors of the verified default integration revision `origin/HEAD = 66259229057b34e7405bc334f4d421f301a8431e`. The first four were directly named by the lane records; `mvci` and `mvreport` were checked as deslop branches listed in the porcelain inventory.

| Exact physical worktree | HEAD | Allocated KiB (`du -sk`) | `worktree-retire ... --dry-run` | Decision |
| --- | --- | ---: | --- | --- |
| `/Users/josh/repos/extensions/.work/wt/br` | `fc01edf3f221912aeb7fcf964028d24cc8568bbc` | 173580 | exit 1: keep; ignored `.work/`, `build/`, `node_modules/` | Preserve ignored data and lane checkout |
| `/Users/josh/repos/extensions/.work/wt/fs` | `63377d7439bcebbd0af6ab32cbad8238f0570d8c` | 293168 | exit 1: keep; ignored `.work/`, `node_modules/` | Preserve ignored data; lane record leaves the broader Tests scenario open (`extensions/docs/deslop-filesystem-store.md:120-123,150`) |
| `/Users/josh/repos/extensions/.work/wt/mv` | `513c05c42fe9b84d076a440d29112dd6fc4a41e9` | 177100 | exit 1: keep; ignored `.work/`, `build/`, `node_modules/` | Preserve ignored data and lane checkout; broader Tests and lifecycle work remain open (`extensions/docs/deslop-mv3-runtime.md:76`) |
| `/Users/josh/repos/extensions/.work/wt/st` | `f541ebd820fb474a8a773473332c6c732760c700` | 169736 | exit 1: keep; ignored `.work/`, `node_modules/` | Preserve ignored data and lane checkout |
| `/Users/josh/repos/extensions/.work/wt/mvci` | `2d1832ceacc00cbdfb8b9942d5bd89ff9345122f` | 171156 | exit 1: keep; ignored `.work/`, `build/`, `node_modules/` | Preserve ignored data and lane checkout |
| `/Users/josh/repos/extensions/.work/wt/mvreport` | `37281161b1d0143c473e55ae2a357326a2ac9ad5` | 1620 | exit 0: would remove as ancestor; would delete branch `deslop/retention-report` | Candidate for parent’s independent review and retirement; left in place |

The first `mvci` and `mvreport` dry-run attempts exited 127 because `worktree-retire` could not find `python3` on PATH. They were rerun with `PATH=/usr/bin:/bin:/usr/sbin:/sbin:/Users/josh/.local/bin`; both results above are from those successful reruns. `git worktree list --porcelain` showed no locked flag for these six trees, and each `git status --short --branch` had no changes. `git merge-base --is-ancestor HEAD 66259229057b34e7405bc334f4d421f301a8431e` exited 0 for all six. `lsof +D /Users/josh/repos/extensions/.work/wt/mvreport` returned no open files (exit 1, no matches); process inspection found no process under the extensions checkout. The only passing retirement dry-run was not acted on because worktree retirement belongs to the parent.

No repo-local ignored scratch directory met all cleanup conditions: exact deslop ownership, supersession, no consumer, no live/open use, and staleness after establishing the live set. The campaign records point to unique mutation reports and prepared inputs under `extensions/.work/tmp`; those were preserved as evidence. Lane-local `.work`, build, and dependency trees reported by the retirement tool were also preserved. The other named roots’ `.work` trees and non-deslop worktrees were retained because no scoped deslop record established ownership and staleness. The `img` porcelain output included a prunable metadata entry pointing to `/Users/josh/repos/rimage/.work/wt/discover-img`; that external, out-of-scope path was not followed or touched. A live process `/Users/josh/repos/kache/.work/wt/chromium-flags/target/debug/kache-engine daemon run` was visible during inventory; its checkout was preserved. No cleanup was performed, so there is no cleared scratch path requiring `test ! -e EXACT_PATH`; reclaimed space is 0 KiB.

## Commands and disk evidence

- `git -C /Users/josh/repos/<name> worktree list --porcelain` (also the two `laputa-systems` paths): exit 0 for every named root. The full inventories showed no locked worktree. Other worktrees were retained; none had a scoped deslop completion record plus an eligible dry run.
- `git -C /Users/josh/repos/extensions rev-parse origin/HEAD`: exit 0, `66259229057b34e7405bc334f4d421f301a8431e`.
- `git -C <candidate> status --short --branch`, `git -C /Users/josh/repos/extensions merge-base --is-ancestor HEAD 66259229057b34e7405bc334f4d421f301a8431e`, and the six dry-run commands in the table supplied cleanliness, integration, and retirement evidence.
- `du -sk <exact extensions worktree path>` exited 0 for each of the six candidates; sizes are in the table.
- `ps -axo pid,etime,command` filtered to the scoped checkout roots showed the live Kache daemon above and no process under `extensions`. No process was stopped.
- `df -k /Users/josh/repos` before inspection: 1024-blocks `1948404040`, used `1588837392`, available `318940264`.
- `df -k /Users/josh/repos` after inspection: 1024-blocks `1948404040`, used `1588985264`, available `318792392`.

Disk usage increased by 147872 KiB during the inventory despite no deletion; unrelated concurrent activity was present. The earlier intermediate `df` also showed increasing usage. No disk reduction is claimed.

**Unverified:** ownership and live-use status of ignored data in the five refused deslop worktrees; cleanup eligibility of other unnamed repo-local `.work` contents; why the stats checkout changed during this inventory. These cases remain preserved. There is no blocker requiring broader scope.

ACCEPTANCE: met
