# repomod

repomod checks repository policy across the `fleet/catalog.toml` fleet and opens pull requests for safe fixes.

## Get started

Use Python 3.15, [`uv`](https://docs.astral.sh/uv/), and Git. Install `gh` and authenticate with
`gh auth login`. Keep `pinact` on `PATH` for GitHub Actions checks and fixes, and provide the
read-only documentation auditor at `~/.local/bin/mdtool`.

From the stuff checkout:

```sh
uv sync
uv run repomod --help
```

## Catalog and checkouts

`uv run repomod` and `uv run repomod -h` print the complete command reference,
including nested command options and an example for each command. Command-specific
help remains available, for example `uv run repomod deps why -h`.

`fleet/catalog.toml` selects repositories and policy tags. Checkouts live under `~/repos` by default.
Set `REPOMOD_ROOT` to use another absolute path. Personal-owner repositories use a flat path.
Other owners use `OWNER/REPO`.

## Discover and add repositories

`repomod discover` compares active GitHub repositories against `fleet/catalog.toml`. It removes
catalogued entries GitHub reports as archived (including pending and `IGNORE` entries and any
overrides), adds new repositories with empty tag arrays, and lists pending repositories and
tracked entries missing from GitHub. Only entries confirmed archived are deleted; remote errors
leave the catalog untouched. It checks every owner in the catalog unless you pass `--owner`.
The command writes the catalog.

```sh
uv run repomod discover
uv run repomod discover --owner joshuarli
```

Add tags to a pending entry in its `[repos."owner"]` section to manage it. For example,
change `example = []` to `example = ["tool"]`. Include at least one primary tag. Add `"IGNORE"`
to exclude a repository from management and discovery; other tags can stay for later. See
[tagging semantics](tagging.md) for tag meanings. Then fetch checkouts:

Discovery's JSON output includes `pending`, `uncatalogued`
(entries added in this run), `removed` (archived entries deleted in this run), and `missing`.
If your catalog has a `[pending]` table from an earlier version, move each entry to its
owner's `[repos."owner"]` table and remove the `[pending]` table.
Move entries from an older `[ignored]` table to their owner sections and add `"IGNORE"` to their tags.

```sh
uv run repomod sync --dry-run
uv run repomod sync
```

Sync also removes archived checkouts when its removal guard passes, then marks their catalog
entries `IGNORE`. Removal verifies publication of retained refs against live remotes and protects
nonignored untracked files, recovery refs, and shared worktree storage. See the
[removal contract](fleet-design.md#checkout-removal).

Tag edits need a separate publish step: `sync` only manages checkouts and never
touches GitHub topics. Preview the difference with `topics diff`, then publish
the catalog tag set with `topics apply`:

```sh
uv run repomod topics diff --repo joshuarli/stuff
uv run repomod topics apply --repo joshuarli/stuff
```

When a repository leaves the catalog (for example after a rename), its old
checkout stays on disk. Preview the leftovers with `gc --dry-run`, then remove
them with `gc`. Ordinary removal requires a clean checkout, verified publication of all retained
refs, and no stashes or other registered worktrees. Unknown remote state blocks removal.
`--force` overrides checkout-state and publication checks and permits stray-file removal.
Recovery refs, shared worktrees, symlinks, unverified paths, and catalogued origins remain protected:

```sh
uv run repomod gc --dry-run
uv run repomod gc
```

## Status and lint

`repomod status` shows only what needs attention: repositories with local Git work, CI or workflow
failures, conflicting pull requests, forks behind their upstream, or 10 or more commits since the last
successful release (latest published GitHub Release, or newest version tag when the
repository has no releases). Passing repositories and passing workflow entries are omitted.
`--json` still reports every selected repository. `status --offline` reads cached CI, upstream,
and release data without network calls. `--failed` narrows the report to CI failures, conflicting
pull requests, and forks behind their upstream.

```sh
uv run repomod status --offline
uv run repomod status --failed
```

`repomod lint` reports policy findings. Use `--tag` or `--repo`
to select repositories. See [tagging semantics](tagging.md) for catalog tag meanings.

`lint` and `status` accept `--checkout PATH` with exactly one `--repo` to evaluate a Git worktree
(for example a fix branch) instead of the canonical checkout, so a fix can be verified before it is
fast-forwarded. The path must be a real directory with no symlink components, a Git work tree
whose `origin` matches the catalogued repository. It is only read.

```sh
uv run repomod lint --repo acme/tool --checkout .work/wt/fix
```

## Owned tools

`repomod tools which COMMAND` resolves an installed command to its maintained repository without
running it. It reads the catalog, `fleet/policy/owned-tools.toml`, `PATH`, and the consumer's
install evidence, and checks the canonical checkout's `origin`. It writes nothing and makes no
network request. `--json` returns the repository, upstream, owned source forks, backlog and
procedure links, checkout, and executable.

The executable's `evidence` says what associates the file on `PATH` with the producer:

| Evidence | Established by |
| --- | --- |
| `source-link` | The managed launcher is a symlink to a tracked file in a Git work tree whose `origin` is the producer |
| `installer-manifest` | usr's `install_manifest` (schema 1) fingerprint still matches the launcher and, for a symlinked launcher, the recorded file or directory that contains its target |
| `install-record` | The command's `record` lists a sha256 (`<digest>  <command>` after the first line) that matches the resolved file |

`revision` is reported separately and is `null` when unknown: the work tree's `HEAD` for an
unmodified source link, or a `release-<sha>` read from the install record. A record value, a
`releases` directory name, or a record without a matching digest is not evidence.

Exit 0 means `status` is `owned`: the checkout is present and the executable is `verified`.
Otherwise `status` is one of:

| Status | Meaning |
| --- | --- |
| `unknown` | No owned producer declares the command |
| `ambiguous` | More than one producer declares it |
| `missing-checkout`, `uncatalogued` | The producer has no checkout at its catalog path, or no catalog entry |
| `origin-mismatch` | The checkout's `origin` is not the producer |
| `not-installed` | The command is not on `PATH` |
| `shadowed` | An unmanaged executable precedes the managed launcher |
| `unverified` | No evidence associates the executable with the producer; `detail` says why |
| `upstream-install` | Verified, but usr installs the upstream build, not the owned fork |

`repomod tools coverage` lists every owned repository as `implemented`, `gap`, `not-applicable`,
`missing`, or `error`, and exits 1 until all are implemented or not applicable. See
[owned-tool support](policy-development.md#owned-tool-support).

```sh
uv run repomod tools which kache --json
uv run repomod tools coverage
```

`repomod/which.py` is the same lookup without the project environment. It imports only the
standard library, so any Python 3.15 runs it with no `uv` synchronization or network, including
when the development tools are broken:

```sh
python3 -I "${REPOMOD_ROOT:-$HOME/repos}/laputa-systems/stuff/repomod/which.py" kache --json
```

## Fix

`repomod fix` syncs the selected repositories, repairs policy violations, and opens a pull
request per repository. Each successful fixer gets one local commit on a `repomod/fix/*` branch,
which is pushed and opened (or reused) as a pull request.
Use `--rule` to select fixers and `--repo`/`--tag` to select repositories.

```sh
uv run repomod fix --rule audit-upgrades
```

See [policy development](policy-development.md) for rule behavior. Report problems in the
[repomod issue tracker](https://github.com/joshuarli/repomod/issues).

See [GitHub Actions integration](policy-development.md#github-actions-with-pinact) for the
Pinact checker, approved catalog, and fix-plan flow.

## Pins

`repomod pins refresh` updates the approved pin files from their upstream sources:
`fleet/policy/actions.toml`, `fleet/policy/python-tools.toml`, `fleet/policy/typescript-tools.toml`, and `fleet/policy/musl-toolchain.toml`.
`--only` restricts the run to `actions`, `python`, `typescript`, or `musl`. `--check`
fetches and compares without writing, prints the files that would change, and exits 1 on
drift; a failed fetch or malformed source exits 2 and writes nothing. Pin bumps that select
a new toolchain version, such as LLVM, mold, or rustup, are manual, checksum-verified edits.
`repomod lint --rule linux-musl-toolchain` enforces the lock across the conventional Rust
builders, tansu, and the bespoke musl builder adapters.

```sh
uv run repomod pins refresh
uv run repomod pins refresh --check
uv run repomod pins refresh --only musl
```

## Canonical musl image

`docker/musl/Dockerfile` builds the shared musl toolchain image. `repomod musl build`
validates its build arguments and package pins against `fleet/policy/musl-toolchain.toml`, builds one
platform with the lock's values, and writes a local OCI layout. It prints the layout's
manifest digest and has no push path. Publishing uses Docker Buildx separately; see
[publication and migration](policy-development.md#publication-and-migration).

```sh
uv run repomod musl build --platform linux/amd64 --output .work/oci/musl
```

## Dependency inventory

`repomod deps` keeps a deterministic, Git-tracked inventory of every catalogued repository's
dependency inputs in `fleet/dependencies/v1`. It records projects, package instances, edges, and
typed coverage issues for Cargo, uv, pnpm/npm, Go, Swift, Zig, GitHub Actions, containers,
toolchains, submodules, CMake, Wrangler, and vendored trees. `snapshot`, `enrich`, and `render`
write; the other commands do not change the tracked inventory. `enrich` queries registries and
OSV and writes a local cache. `why`, `report`, and `render` also consult GitHub visibility, which
may use the network; `render --status` adds live repository status.

```sh
uv run repomod deps snapshot
uv run repomod deps check --strict
uv run repomod deps why tokio
uv run repomod deps report
uv run repomod deps diff --from HEAD~1
uv run repomod deps enrich
uv run repomod deps render
```

Install the dashboard's pinned CSS package once with `pnpm install --frozen-lockfile`.
For a local server, `make deps` syncs the checkouts, re-snapshots the tracked inventory
(committing any changes under `fleet/dependencies/v1/` and `fleet/loc/v1/`), renders with live status, and serves the
dashboard at `http://127.0.0.1:8765` with `srv`; use `make deps PORT=9000` for another port.

See [dependency inventory](dependency-inventory.md) for the data layout, coverage kinds,
update flow, and limits. Open `.work/dependencies/dashboard/index.html` in your browser;
see [dependency dashboard](dependency-dashboard.md). The repo-local
[`upgrade-the-world`](../.agents/skills/upgrade-the-world/SKILL.md) skill upgrades every public,
non-fork repository and loops until CI is green.

## Push

`repomod push` pushes each selected checkout's current branch when it is ahead of
its origin upstream. It reports `pushed`, skips clean or non-pushable checkouts
with a reason, and fails loudly without rewriting remote history when the remote
has moved. Use `--repo`/`--tag` to select repositories.

```sh
uv run repomod push
```

## Merge

`repomod merge` merges open pull requests whose head branch is a `repomod/fix/*` branch, which is
how `fix` identifies its pull requests. It pins each merge to the head commit listed before the
merge, so a branch that moves is rejected instead of merging unreviewed commits. Drafts are
skipped and merge failures are reported; both leave the pull request open. `--dry-run` lists what
would merge. The command reports listing progress and a final summary, including when no pull
requests are found. Use `--repo`/`--tag` to select repositories.

```sh
uv run repomod merge --dry-run
uv run repomod merge
```

## Release

`repomod release` dispatches a recognized release or prerelease workflow on each selected
repository's default branch and polls its run. It reuses a matching existing run and skips
repositories without a recognized workflow. A published `release-<sha>` already at the observed
head is reported as present. This command writes to GitHub and may publish release artifacts.
Use `--repo` or `--tag` to select repositories:

```sh
uv run repomod release --repo acme/tool
```

## Dependency upgrades

The `audit-upgrades` rule reports locked direct dependencies that lag their registry.
`repomod fix --rule audit-upgrades` puts the upgrades up as pull requests.
Upgrades that need manifest edits stay manual. See [dependency audit](audit.md)
for rule behavior.

The stuff registries serve only versions that some lockfile asked for, so a new upstream release
is invisible to `audit-upgrades` until it is mirrored. `repomod deps mirror` closes that loop: it
relocks each selected repository against crates.io, npm, and PyPI in a disposable copy, compares
the current and upgraded lockfiles and the approved Python tool pins with the stuff catalogs, and
publishes what is missing through `stuff publish cargo --lockfile`, `stuff publish npm --lockfile`,
and `stuff publish pypi`. It then waits until the catalogs list the new versions and drops the
cached latest versions it resolved from stuff. It mirrors the ecosystems a repository resolves
from stuff, and those still on the public registries that `registry-sources` will move to stuff;
an ecosystem on another registry, or in a repository exempt from `registry-sources`, is left
alone. Private repositories, forks, and repositories that ignore `audit-upgrades` are skipped. `--dry-run` lists what is missing without publishing. The command writes to the stuff
R2 buckets, so the `stuff` CLI on `PATH` must be able to publish
(see [publishing](PUBLISHING.md)).

`repomod fix` runs the mirror first whenever `audit-upgrades` or `python-standard` is among its
fixers, so one command upgrades to the newest upstream releases. A mirror failure is reported and
makes the command exit 1, but the fixers still run against what stuff serves. Pass `--no-mirror`
to skip it.

```sh
uv run repomod deps mirror --dry-run
uv run repomod fix --rule audit-upgrades
```

## Quality standard

The 2026-11 deslop campaign set the bar every in-scope repository keeps. The usr `deslop` skill is
the procedure for bringing a repository up to it; its tool recipes live in the skill's tools
reference. In scope are first-party Rust, Python and TypeScript repositories and the
`fork-diverged` forks, limited to their changes against upstream. Effectively-upstream forks,
pristine vendored trees and owner-excluded repositories are out. The rules that check it are in
[policy development](policy-development.md#other-policy-rules).

- **CI runs the tests.** A pull-request workflow runs `make test` or `make test-ci`
  (`gha-test-workflow`), and the repository's adopted strict typing settings stay on
  (`strict-typing-profile`).
- **Mutation guards a small critical scope.** Blocking mutation covers only an important
  contract: archive admission, cache integrity, atomic publication, success and failure
  reporting, cleanup, or an authorization decision (`mutants-diff-lane`). A survivor fails unless
  the repository's mutation config lists it with a reason, and weakening a protecting test
  reopens that scope. A new or wider mutation trial gets 10 aggregate runner-minutes unless it
  names an unresolved important behavior first. Broad sweeps are advisory. Coverage is measured
  and reported, never gated.
- **Tests stay cheap.** A change may raise warm `make test` time by at most 20% or 30 seconds,
  whichever is larger.
- **Performance does not regress.** Perf-sensitive repositories (fastermod, lz, loc, e, ish, and
  any repository that declares a workload) gate refactors on the declared workload's path with
  at least five interleaved baseline and candidate pairs of the shipped profile. On a quiet host a
  median regression larger than the observed spread and 2% blocks the change; on a busy host use
  the busy-host rules in usr's `performance.md`. Benchmarks follow the `bench-pyramid` skill, and
  only the owner runs the Full tier.
- **Dead-code tools and strict settings join on evidence.** A dead-code tool joins `make lint`
  only when the repository is clean under it with at most five allowlisted entries, each with a
  reason. A strict typing setting joins the fleet profile only after it rejected a real defect
  or removed an escape hatch, at no more than one suppression per 5k lines.
- **Removals of live behavior are the owner's.** Behavior-preserving cuts land on their own.
  Removing a CLI flag, public API, compatibility path or format is filed as a `Needs owner ·`
  ticket in the repository's `TODO.md`.
- **Library changes run their consumers.** A change to a published or consumed library (smolith,
  ptytest, hi-lite, rustybench, laputa-ui-dashboard, buildlib, pytest-parallel) also runs its
  known consumers' tests against the candidate; `repomod deps` finds them.
- **Shared build tooling** follows [build repositories](build-repos.md#shared-build-tooling-across-the-fleet).

The per-repository record of the campaign, with each repository's closing revision, is the
[deslop scorecard](campaigns/deslop-scorecard.md).
