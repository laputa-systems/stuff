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

To opt a private repository into fleet management, assign its role and language tags and remove
`IGNORE` if present. Use `repomod lint --repo OWNER/REPO` to run its policy checks locally and
`make deps PRIVATE=1` to include managed private repositories in the dashboard. Local checks and
inventory collection use no GitHub Actions minutes. The public `stuff` checkout tracks repository
names, dependency metadata and line counts for managed private repositories.

Tag edits need a separate publish step: `sync` only manages checkouts and never
touches GitHub topics. Preview the difference with `topics diff`, then publish
the catalog tag set with `topics apply`:

```sh
uv run repomod topics diff --repo joshuarli/stuff
uv run repomod topics apply --repo joshuarli/stuff
```

When a repository leaves the catalog (for example after a rename), its old
checkout stays on disk. Preview the leftovers with `gc --dry-run`, then remove
them with `gc`. The same [removal contract](fleet-design.md#checkout-removal) applies: `--force`
overrides checkout-state and publication checks and permits stray-file removal, but never
recovery refs, shared worktrees, symlinks, unverified paths, or catalogued origins:

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

Shared shell must run unchanged on macOS, glibc Linux, and Alpine. The `shell-portability`
lint rule enforces the owner's portability standard mechanically: it rejects the standard's
nonportable commands and options (and the GNU regex escapes in `sed`/`grep`) in workflow
`run:` steps, Makefile recipes, shell scripts, and Dockerfile `RUN` lines, honors its
platform-named path exemptions, and names the portable replacement in each finding. See
[policy development](policy-development.md#shell-portability).

## Owned tools first

The fleet is one system. When a repository needs a tool that an owned producer supplies, it uses
the producer's release, not the upstream package, distribution package or setup action. A
consumer that meets a missing feature or a bug files or fixes it in the producer (see the usr
owned-tool procedure linked from `fleet/policy/owned-tools.toml`); it does not fall back to the
upstream build. Each consumer is then also a test of the producer, and a fix lands once for every
repository.

<!-- generated: owned-substitutes -->

| Upstream tool | Owned producer |
| --- | --- |
| Meson, Ninja | `laputa-systems/gluon` |
| FFmpeg runtime and libraries | `laputa-systems/ffmpeg-build` |
| CMake | `laputa-systems/cmake-build` |
| Clang and LLVM toolchains | `laputa-systems/llvm-prebuilt-musl` |
| Node.js | `laputa-systems/node-build` |
| CPython | `laputa-systems/python-build` |
| Git | `laputa-systems/git-build` |
| OpenSSH | `laputa-systems/ssh-build` |
| ripgrep | `laputa-systems/rg` |
| fd | `laputa-systems/fd` |
| jaq | `laputa-systems/jaq` |
| mold | `joshuarli/mold` |
| ShellCheck | `joshuarli/shck` |
| sccache, ccache | `joshuarli/kache` |
| pytest-xdist | `joshuarli/pytest-parallel` |
| criterion, divan | `laputa-systems/rustybench` |

<!-- end generated -->

The producer list in `fleet/policy/owned-tools.toml` is authoritative; the table above is generated
from `fleet/policy/owned-substitutes.toml` by `uv run python -m repomod.substitutes --write-docs`.
`repomod tools substitute NAME` prints the owned producer for an upstream package, action, URL, or
label. A consumer keeps the upstream tool only for a stated reason: the producer publishes
no release for the consumer's platform, the consumer is an effectively upstream fork whose
inherited build must stay unchanged, or the substitution is deferred until a named producer gap
is fixed. Record that reason next to the install and file the producer gap in the producer's
`TODO.md`. A producer's own repository may install the upstream tool it reproduces, for example
as a parity oracle or build reference; the rule does not report that. Build repositories acquire owned tools the same way they acquire other inputs; see
[build repositories](build-repos.md#owned-toolchain-inputs).

The `owned-tool-substitution` repomod rule enforces this table. It reads
`fleet/policy/owned-substitutes.toml`, which maps each producer to the distribution packages
(`apk`, `apt`, `brew`, `dnf`, `pacman`), setup actions (`actions/setup-node`,
`actions/setup-python`, and `astral-sh/setup-uv` when it provides Python), download URLs and
dependency-manifest names it replaces, and scans `.github/workflows`, Dockerfiles, Makefiles,
`scripts/`, `docker/` and `flake.nix` plus `Cargo.toml`, `pyproject.toml`, `package.json`,
`requirements*.txt` and `.cargo/config.toml`. Manifest ecosystems are `cargo`, `pypi` and `npm`;
the rule also flags `pip install`, `uv add`, `uv pip install` and `cargo install` commands and
`RUSTC_WRAPPER`/`rustc-wrapper` assignments. An unexempted upstream install is a blocking finding that names the producer to use
instead and points at buildlib's setup action and `buildlib.tools`. To exempt a repository,
add `[exempt."owner/repo".producers."producer/id"]` entries with a `reason` drawn from the
grounds above and a `reassess` condition; an exemption that matches no finding is itself a
finding. Each shipped exemption names its producer gap in a `TODO.md` ticket.

### Acquiring owned tools

A consumer pins the owned tools it needs in a `tools.lock.json` and installs them with buildlib.
`python -m buildlib tools lock TOOL --tag release-<sha>` adds or replaces an entry with each
target's asset name, size and SHA-256. In GitHub Actions, add one step:

```yaml
- uses: laputa-systems/buildlib/setup@1cd9d482a684e72c68ac6fea7f4ee3a3e9c4a161 # v0.3.1
  with:
    tools: gluon cmake
```

The action reads `tools.lock.json` (input `lock`), restores a cache keyed by exactly those pins,
installs whatever is missing, and puts each tool's bin directory on `PATH`; its `cache-hit` output
reports a restore. Outside Actions, run `python -m buildlib tools install TOOL... --lock
tools.lock.json` through the vendored `bootstrap/buildlib-run` shim, which needs no installed
Python. Both paths verify size and SHA-256 before extraction and need no other tool. The tool
names, layouts and cache format are in buildlib's
[tools reference](https://github.com/laputa-systems/buildlib/blob/main/docs/tools.md); the action
pin lives in `fleet/policy/actions.toml`.

A uv-based workflow acquires the owned interpreter by setting `UV_PYTHON_DOWNLOADS: never` and
`UV_PYTHON_PREFERENCE: only-system` at workflow level and adding the
`laputa-systems/buildlib/setup` step with `tools: cpython` before `astral-sh/setup-uv`, dropping
`uv python install`. `never` blocks uv's managed downloads outright, and `only-system` stops uv
preferring an existing managed interpreter, so uv resolves the interpreter buildlib installed.
The `owned-tool-substitution` fixer performs this rewrite for the uniform `setup-uv` +
`uv python install` shape and writes `.github/tools.lock.json`.

`fleet/policy/tools-lock.toml` approves one release per tool, in the same shape as a
`tools.lock.json` entry. The `tools-lock` rule reports a consumer's `tools.lock.json` or
`.github/tools.lock.json` entry that differs from its approval, and an unknown tool name; tools
the policy does not list are not compared. After a producer release, approve it there and run
`uv run repomod fix --rule tools-lock` to open the bump pull requests. The buildlib wheel itself
is approved in `fleet/policy/buildlib.toml` and moved by
[`buildlib-usage`'s fixer](build-repos.md#enforcement).

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

Install the dashboard's pinned CSS package once with `pnpm install --frozen-lockfile`;
`make deps` serves the local dashboard — see [dependency dashboard](dependency-dashboard.md).

See [dependency inventory](dependency-inventory.md) for the data layout, coverage kinds,
update flow, and limits. Open `.work/dependencies/dashboard/index.html` in your browser;
see [dependency dashboard](dependency-dashboard.md). The repo-local
[`upgrade-the-world`](../.agents/skills/upgrade-the-world/SKILL.md) skill upgrades every public,
non-fork repository and loops until CI is green.

## CI timings

`make ci-report` backfills GitHub Actions timings for every catalog repository with
[github-actions-report](https://github.com/joshuarli/github-actions-report), then serves an offline
report from `.work/ci-report`. Set `DAYS` for the first backfill; the default is 90. The collector
pauses when 1,500 GitHub API requests remain. The report contains private repository names, so
keep it local.

Later runs resume the saved date range and do not add newer days. To collect a new range, move
`.work/ci-report/data` aside first. Rankings use default-branch runs for durations and all branches
for runner minutes.

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

These source rules apply to first-party Rust, Python and TypeScript repositories and to
the maintained changes in `fork-diverged` forks. Managed forks also follow the fleet CI
standard. Use the usr `deslop` skill for source conformance and see the
[policy rules](policy-development.md#other-policy-rules).

Apply `test-pyramid`, `bench-pyramid`, `test-audit`, and `typing-audit` to the maintained
code of every managed repository. A conformance assessment records the applicable native
commands, behavioral evidence, and open gaps for that repository.

- **Every managed repository exposes a Change test command.** The root Makefile
  defines `make test` (`make-test-target`), including for local-only verification.
- **CI runs the tests.** A pull-request workflow runs `make test` or `make test-ci`
  (`gha-test-workflow`), and the repository's adopted strict typing settings stay on
  (`strict-typing-profile`).
- **Forks own their CI.** Keep a fork-owned PR test and lint gate, with pinned actions,
  read-only GitHub permissions, `persist-credentials: false`, and the fleet shell and
  concurrency settings. Retire inherited
  workflows when importing upstream changes. Review changes in `.github/workflows`,
  including files that share a name with upstream. Check that existing required job
  names still resolve before merging. Keep fork-owned releases and platform builds.
- **Mutation guards a small critical scope.** Blocking mutation covers only an important
  contract: archive admission, cache integrity, atomic publication, success and failure
  reporting, cleanup, or an authorization decision (`mutants-diff-lane`). A survivor fails unless
  the repository's mutation config lists it with a reason, and weakening a protecting test
  reopens that scope. A new or wider mutation trial gets 10 aggregate runner-minutes unless it
  names an unresolved important behavior first. Broad sweeps are advisory. Coverage is measured
  and reported, never gated.
- **Tests stay cheap.** A change may raise warm `make test` time by at most 20% or 30 seconds,
  whichever is larger.
- **Test tiers and assertions have evidence.** Use `test-pyramid` to keep `make test` a bounded
  Change gate and to keep Full workloads manual. Use `test-audit` to trace tests to the failures
  they catch and prove any replacement detects those failures before deleting coverage.
- **Types describe runtime values.** Use `typing-audit` on the contracts under change. A tightening
  must eliminate an unchecked assumption or demonstrate a bad program that the checker now rejects.
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

The mutation, coverage, and strict-profile guarantees are registered per repository in
`fleet/policy/retention.toml` and checked as described in
[policy development](policy-development.md#other-policy-rules).
