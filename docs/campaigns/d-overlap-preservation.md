# Preserve duplicate development checkouts

The owner requested moving the repositories in the [overlap inventory](d-overlap-inventory.md)
to macOS Trash after preserving their changes. `/Users/josh/repos` is canonical.
The twelve inventoried nonoverlap or explicitly retained directories, including
`/Users/josh/d/stuff`, stay in place. This operation does not merge experimental branches or
discard canonical checkout changes.

## Preservation

Batch `d-overlap-20261116T185745-linear` keeps each source repository's refs under
`refs/preserved/d-overlap-20261116T185745-linear/<repository>/` in its canonical
repository. The suffix retains the original ref name after `refs/`, including
heads, tags, remote refs and stash refs. Additional refs preserve every registered
worktree HEAD, create-only working snapshots, and reflog tips. No preservation
refs or private archives are pushed.

Fz's complete batch has the suffix `-fz`:
`d-overlap-20261116T185745-linear-fz`. Its preservation refs and archive directory
use that full name. An earlier check caught Git refreshing source index metadata
while comparing a dirty worktree. Staged entries were byte-for-byte identical;
the original raw index is retained in the incomplete batch. The corrected
controller performs these comparisons against a copied index. A stale-stat
fixture fails before that correction and passes after it, retaining staged,
unstaged, untracked, ignored, symlink and hardlink data. The final fixture and
verifier also preserve FIFO entries without opening them as ordinary files.

Private files live at
`<canonical-git-common-dir>/preserved-checkouts/d-overlap-20261116T185745-linear/`.
This is outside disposable `.work/`. Each directory contains:

- `receipt.json`, with original refs, worktree paths and HEADs, working snapshot
  refs, archive manifests and checksums, and the canonical primary checkout's
  original state.
- `COMPLETE`, the SHA-256 of the verified receipt.
- `files-NN.tar.gz`, containing modified, untracked and ignored files for worktree
  `NN`. Unchanged tracked files are omitted only when their exact blob and mode
  match the index and the blob is physically present in the canonical repository.
- `git-admin.tar.gz`, the original Git administrative files apart from the main
  object directory. This includes original worktree indexes and configuration;
  do not extract it over a canonical `.git` directory.
- Original indexes and binary patches for dirty tracked worktrees, plus the
  preservation controller used for the batch.

All physically available source Git objects are copied into canonical object
storage. New packs have `.keep` files, retaining objects that had no ordinary
branch reference. Explicit object packing avoids the partial-clone negotiation
failures caught in the first preservation attempt. Incomplete earlier attempts
were retained, not overwritten; this batch's `COMPLETE` receipts are authoritative.

The fixture exercised source-only commits, conflicting tags, detached HEADs,
different staged and unstaged versions of one file, binary untracked data,
ignored evidence, symlinks, an orphan object, and a missing canonical base blob.
It verified preservation and that a dirty canonical checkout stayed unchanged.
Archive readback checks each member in sequence, avoiding repeated searches
through Fz's roughly 200,000-entry root archive. The final verifier checks receipt
and archive hashes, original source refs,
worktree states, working snapshots, every current source file against its archive
or preserved Git blob, and the canonical primary checkout's state.

This includes Diff's dirty `.gitignore` and benchmark file, Fz's eight dirty
probe files and untracked profile, every parked branch, and the stopped Vault
and Diff mutation receipts. Empty host indexes are intentional no-checkout
artifacts; their apparent staged deletions are not converted into deletion commits.

## Recover a worktree

Read the matching `receipt.json` with `jaq`. Find the worktree's `head_ref`,
optional `working_snapshot`, and archive. Add a fresh isolated worktree from
`head_ref`. For a dirty tracked worktree, apply its preserved create-only stash
snapshot with `git stash apply --index <working_snapshot>` inside that fresh
worktree. Inspect the archive listing, then extract that worktree's `files-NN`
archive there to recover its raw modified, untracked and ignored files, including
permissions and symlinks. Never extract an archive into the canonical primary
checkout. Existing build artifacts can contain old absolute paths; rebuild for
new verification instead of reusing them.

The original clones also remain recoverable from macOS Trash. Do not empty Trash
or remove preservation refs, kept packs or archives as part of ordinary campaign
scratch cleanup.

## Outcome

All 29 inventoried overlaps were moved with `/usr/bin/trash --stopOnError
--verbose` after preservation and final verification. The native command
returned success and reported each destination as `/Users/josh/.Trash/<name>`.
Every original path is absent. macOS privacy controls blocked direct enumeration
of `.Trash`; destination reporting comes from the native command, not a separate
inode check. Trash was not emptied.

The authoritative copies cover 59 checkout roots and registered worktrees,
including the 29 empty-index host roots. Their compressed file and Git-admin
archives total 3,288,422,316 bytes. All three dirty tracked worktrees have
create-only snapshots. After the move, the ten dirty tracked files recovered
from those Git snapshots matched the archived raw-file SHA-256 values. Archive
checksums and preservation refs passed another readback from their canonical
locations. Fz's untracked profile and the ignored mutation evidence are archived.

All twelve retained directories remain present. The 29 canonical primary
checkouts retain their recorded HEADs and status. No pre-existing canonical ref
was changed, no experimental branch was merged, and no service was stopped or
restarted. The only open overlap paths before the move were four idle bridge
owner sockets; all their jobs had finished. The live nonoverlap Niceforge
services were left in place.

Both active worktrees are clean and use branch `resume/deslop-tests-20261116`:

| Repository | Worktree | HEAD |
| --- | --- | --- |
| Diff | `/Users/josh/repos/laputa-systems/diff-pretty/.work/wt/ds` | `49a1c97d1f60932c3d860318672ecdcc545a0986` |
| Vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds` | `0561a3e34828db0164d2a2baedfad2c1a7b3a611` |

The private operation index at
`/Users/josh/d/stuff/.git/preserved-checkouts/d-overlap-20261116T185745-linear/`
contains the full inventory, per-repository verification report, native Trash
log, exact recovery receipt paths, dirty-file recovery hashes, fixture/controller
copies and final `outcomes.json`. Its `COMPLETE` file hashes `outcomes.json`.
The per-repository receipts remain the authority for each archive's contents.

The inventory helper worktree was retired after its two commits were confirmed
patch-equivalent to primary head `4a56ee4`. It was clean and had no open-file
consumer. Its 144 KiB of ignored inventory scratch was copied into the private
operation index before `worktree-retire --discard-ignored`; the helper checkout
is absent. The tool retained `chore/d-overlap-inventory` because its two commits
are patch-equivalent rather than ancestors of the primary head. Other Stuff
worktrees were outside this cleanup scope.
