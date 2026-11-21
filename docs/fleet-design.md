# Design

repomod uses one curated catalog, canonical local Git checkouts, read-only GitHub status, and
explicit repair and topic writes. Git records source changes. repomod has no status database or
repair ledger. `repomod discover` deletes catalogued entries GitHub reports as archived, including
pending and `IGNORE` entries and their overrides, so the catalog reflects reality without manual
cleanup; only a confirmed `isArchived` result deletes, and remote errors never do.

## State and ownership

`fleet/catalog.toml` owns repository identity, pending and ignored entries, policy tags, checkout root, autofix overrides, and
per-repository ignored rule codes. Version 3 adds the `ignore` override for stable lint IDs and `mdtool:CODE` documentation findings,
with a required non-empty `ignore_reason` string that `repomod lint` prints for selected repositories.
`REPOMOD_ROOT` overrides the configured root for one process. The catalog does not record branch
state or lint results.

An empty tag array in `[repos."owner"]` marks a pending repository. Adding at least one primary
tag makes it managed. The `IGNORE` tag excludes a repository from management and discovery.

Personal-owner checkouts live directly under the root. Other owners use `OWNER/REPO`. The catalog
rejects symlink path components. repomod checks that a checkout's origin matches its GitHub
repository. New clones are staged beside their destination and moved into place after validation.

`git.py` owns Git subprocesses and repository locks. `github.py` owns GitHub reads, CI cache,
topics, and approved Action tag resolution. `sync.py` coordinates clones, fetches, safe
fast-forwards, and archived-repository untracking. `clean.py` owns checkout removal guards and
unreferenced-checkout collection. `catalog.py` owns catalog reads and edits. Command handlers live
under `cmd/`, one module per subcommand; `cli.py` only parses arguments and dispatches.
Policy rules live under `rules/`. See [policy development](policy-development.md).

## Synchronization and status

Sync reads current GitHub metadata for catalog entries. New clones are full-history, blobless
partial clones: complete commit history so rebases and ancestry queries work, with file contents
fetched on demand instead of up front. A checkout that is still shallow from an older clone is
unshallowed during sync; if that fails the sync for that repository fails loudly rather than
continuing on a shallow boundary. Sync skips fetch only when a clean checkout
is attached to the default branch and its HEAD matches GitHub's reported branch tip. Otherwise it
fetches that branch. It fast-forwards only a clean checkout on that branch when Git confirms the
move is safe. Dirty, detached, non-default, ahead, and divergent checkouts keep their files and
local commits. A fetch may update the matching remote-tracking ref. GitHub is the source of truth
for archival: when GitHub reports a catalogued repository as archived, sync removes its local
checkout instead of cloning or fetching it and adds `IGNORE` to its entry, preserving tags and overrides, so later
runs stop tracking it. The shared [checkout removal](#checkout-removal) inspection protects both
archived sync and unforced GC. A checkout that cannot be safely removed stays tracked.
Dry-run fetches GitHub metadata and inspects
remote publication for archived checkouts but does not
mutate checkouts; it reports what would be cloned, updated, removed, or untracked. For repositories that GitHub reports as forks of a parent, sync also
ensures a conventional `upstream` remote pointing at the parent and fetches the parent's default
branch, so fork-behind comparisons stay verifiable locally; a failing upstream fetch is reported
in the result without failing the sync.
Repointing an existing upstream changes its fetch URL in place, preserving branch tracking,
other remote configuration and existing refs. The subsequent fetch can update the selected
upstream branch as usual; repointing does not remove the remote or its other tracking refs.

Local status does not fetch. Ahead and behind counts compare the local branch with its last-fetched
upstream, so they are not current remote state. Text output lists only repositories that need
attention: local Git failures, non-passing CI or workflow states on the default branch, conflicting
pull requests, forks behind upstream, and releases at least 10 commits behind the default branch.
Passing repositories and passing workflow entries are omitted; `--json` still carries every
selected repository. Online status checks CI for GitHub's current default-branch commit. The CI
cache is keyed by repository and commit SHA and expires after five minutes. Offline status reads
cached CI without network calls. Online status also reports how many commits the default branch is
ahead of its latest published release (the last successful release) via a GitHub compare between
the release commit and the default-branch tip. The release is the newest non-draft GitHub Release
(stable or prerelease); a repository with no releases falls back to its newest version tag.
Workflow states cover only runs on the default branch. The release cache is keyed by repository
and default-branch commit SHA and expires after one hour. Offline status reads cached release
comparisons. For repositories that GitHub reports as forks, online status also compares the fork
default branch against its upstream parent and reports behind and ahead counts. The upstream cache
is keyed by repository and fork commit SHA and expires after one hour. Offline status reads cached
upstream comparisons. Online status also lists open pull requests with their mergeable and
merge-state status; `--failed` includes repositories with conflicting PRs and forks behind their
upstream. Offline status omits pull requests.

`lint` and `status` accept `--checkout PATH`, valid only with exactly one `--repo`. It replaces the
canonical checkout for that repository in policy rules, local Git state, and the TODO count, so a
worktree can be verified before it is fast-forwarded. The path must contain no symlink components,
be a Git work tree, and have an `origin` matching the catalogue, the same check sync applies. GitHub
data still follows catalog identity, and no other command accepts the option.

The local item also shows how old unpushed work is, derived only from Git data. When the branch is
ahead of its last-fetched upstream it adds `oldest unpushed Nd`, the age of the oldest commit not in
the upstream. When the checkout is on a non-default branch it adds `for Nd`, the time since HEAD's
reflog last switched onto that branch (omitted if the reflog has no such entry). An age of seven days
or more turns the item red and sets `stale_local_work` in `--json`, which also carries the raw
`branch_checked_out_at` and `oldest_unpushed_commit_at` timestamps.

## Checkout removal

Ordinary removal requires a verified path and catalogued origin, with no tracked changes,
nonignored untracked files, detached HEAD, unknown upstream, commits ahead of upstream, or stashes.
Every local branch and tag must match a ref currently advertised by origin. A local branch may
instead be an ancestor of that advertised branch when the remote object is available locally.
Every remote-tracking tip must be advertised by a configured remote or be an ancestor of an
advertised branch whose object is available locally. Remote errors and unknown publication state
refuse ordinary removal; stale remote-tracking refs alone do not prove publication.

Recovery and unrecognized refs block removal. Shared Git storage and another registered worktree
also block it; missing and locked worktrees still count. `gc --force` overrides dirty-checkout,
current-branch, stash, and publication checks and permits stray-file removal. It cannot override
shared-storage, registered-worktree, recovery-ref, symlink, path, or catalogued-origin protection.

`git.py` owns inspection and remote queries; `clean.py` owns the shared removal decision.
Mutating removal holds repomod's repository lock and rechecks checkout and Git-directory
identities, HEAD, refs, origin, worktrees, and status before deletion. The lock excludes cooperating
repomod commands. Other writers can race after the final check, and remote refs can change after
advertisement; the inspection guarantees neither atomic exclusion nor permanent remote retention.
Dry-run applies the same eligibility checks without deleting files.

Retiring a completed, integrated worktree uses
`worktree-retire <path> --into <sha> --discard-ignored`. Before retirement, verify that the
checkout is clean (`git status --short --untracked-files=all` is empty), its HEAD is an ancestor
of the integration commit (`git merge-base --is-ancestor <head> <sha>` exits 0), and no process
holds files in it (`lsof -nP +D <path>` reports no open files). Review ignored files before
discarding them: `--discard-ignored` removes rebuildable caches and artifacts, so preserve any
evidence that is needed before they are gone.

## Dependency inventory

`repomod/dependencies/` owns the tracked inventory at `fleet/dependencies/v1/`. Its module
layering, lazy import in `cmd/deps.py`, read-only policy boundary, and the "no database,
background worker, or generic workflow framework" rule are described in
[dependency inventory](dependency-inventory.md#layering). The inventory records `{path, blob}`
inputs and a fingerprint over their sorted list plus `PARSER_VERSION`; it never stores absolute
paths, timestamps, credentials, or unredacted URLs. The dashboard is static output under
`.work/dependencies/dashboard/` and needs no runtime data fetch or CDN; Explore uses the
vendored graph renderer described in [dependency dashboard](dependency-dashboard.md#source-and-verification).

## Repair and writes

Fix requires a clean, attached canonical checkout and a local default-branch ref matching
GitHub's observed tip. The canonical checkout may stay on another branch. Fixers run serially
on a dedicated fix branch based on the local default branch, with repositories processed in
parallel. Each fixer uses a disposable worktree and can change only its declared paths. Before a local commit,
validation must pass, the fixer must leave no fixable findings for its rule, and it must introduce
no policy errors. Every successful fixer gets its own commit on a new local
`repomod/fix/<id>` branch; the canonical default branch remains untouched. `fix` pushes
that branch and opens or reuses a pull request against the default branch. It enables GitHub
auto-merge only when the repository allows it and the default branch requires status checks. The
next fix run resumes its unmerged branch from the current default branch. Failed or interrupted
work remains on its branch or in its worktree.
Publication retains the canonical branch and HEAD observed before fixing. A change detected
during fixing prevents publication. The push path rechecks that identity before and after its
remote lookup. Refused publication leaves the fix branch available for inspection. These checks
do not exclude a non-cooperating writer after the final inspection.
A `repomod/fix/` branch that has diverged from the default branch blocks the next run unless
GitHub reports its pull request merged, or `git cherry` finds every one of its commits already on
the default branch, as happens after a squash or cherry-pick.

Fix pull requests are identified by their `repomod/fix/<id>` head branch. `merge` lists open pull
requests in selected repositories whose head branch matches that pattern and merges each with a
rebase commit pinned to the listed head SHA, so a branch that moved after listing is rejected
rather than merged unreviewed. Drafts are skipped and merge failures are reported per pull
request. `merge --dry-run` lists the matches without writing.

Push uses a normal fast-forward Git push and keeps local commits on failure. `push` pushes
each selected checkout's current branch when it is ahead of its origin upstream and skips
anything else with a reason. `topics apply`
replaces GitHub topics with the catalog's complete tag set.

`pins refresh`, the musl toolchain lock, and the canonical musl image are described in
[fleet](fleet.md#pins) and [policy development](policy-development.md#musl-toolchain-lock).
