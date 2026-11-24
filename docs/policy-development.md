# Policy development

Rules live in `repomod/rules/` and are registered in `rules/__init__.py`. Each rule has a
stable ID, a read-only check, and an explicit tag predicate. See [tagging semantics](tagging.md)
for tag classification and repository filters.

Return structured `Finding` values with concrete messages and deterministic ordering. Report
unavailable tools, unreadable files, and failed API calls as operational findings, not policy
violations.

Lint IDs are durable catalog policy codes. Catalog version 3 supports per-repository
`[overrides."OWNER/REPO"]` entries with `ignore = ["rule-id"]` and a required `ignore_reason`
string. Validate each code against the
registered rule IDs. An entry of the form `mdtool:R005` ignores one `mdtool` finding code in that
repository and keeps the rest of the documentation audit. An entry of the form
`audit-upgrades:crates:NAME` (ecosystem `pypi`, `npm`, `crates`, or `go`) exempts one dependency
from `audit-upgrades`. An entry of the form `audit-banned:transitive:NAME` exempts one transitive
Rust crate from `audit-banned` without allowing it as a direct dependency. `audit-banned:direct:NAME`
exempts one direct Rust dependency and its lockfile entry. An entry of the form
`registry-sources:git:NAME` silences the `registry-sources` warning for one
git-sourced package named `NAME`. `rust-project:lockfile:DIR` stops `rust-project` from asking
for a `Cargo.lock` at the workspace root `DIR` (relative to the repository root) and keeps its other
checks. Document policy changes alongside the rule.

## Fixers

A fixer returns complete UTF-8 file contents keyed by repository-relative path. It does not edit,
stage, or commit files. Declare the smallest safe `allowed_paths` and a rule-specific
Conventional Commit subject. Add a validator when the plan needs a rule-specific check.

The runner rejects out-of-scope paths, invalid plans, new policy errors, and remaining fixable
findings for that rule. A changed fixer gets one local commit. Use fixers only for deterministic
repairs. Keep human release choices out of automatic fixes. Do not generate placeholder README,
license, or agent files.

## Dependency inventory boundary

The dependency inventory is derived data, not policy. `dependencies/` and `cmd/deps.py` read
Git objects and the tracked inventory; they do not edit checkouts, rules, or fix plans. Policy
rules stay read-only, and fixers keep their explicit file plans. `snapshot` and `render` write
only the inventory or dashboard, and `enrich` writes only the local cache. Do not add a
database, background worker, or generic workflow framework to support the inventory. See
[dependency inventory](dependency-inventory.md).

## Release policy

The [shared build-tooling policy](build-repos.md#shared-build-tooling-across-the-fleet) also
applies outside `build`-tagged repositories. `buildlib-usage` is implemented in
`rules/buildlib.py` with its admission data in `fleet/policy/buildlib.toml`. That policy owns the
approved wheel version, filename and sha256, the approved bootstrap shim identities, and each
active repository's classification: `enrolled` declares entrypoints, whether the bootstrap is
required, and any declared local shim difference; `assess` marks an eligible repository that is
reported informationally; `exempt` requires a reason and a reassessment condition. An active
catalog repository outside the policy is reported as an informational `unclassified` finding.
For enrolled consumers the rule checks the exact `laputa-buildlib==<approved>` pin in the
`[project]`, optional-dependency, and dependency-group sections, agreement on the approved wheel
identity and digest in `uv.lock` and `sources.lock.json` when present, required bootstrap files and
their approved or declared digests, and declared entrypoints that exist as regular files reached
without symlinks. A consumer that requires the bootstrap and has no `pyproject.toml` (play) is
pinned by the shim's approved `python.lock` alone. The rule reads files only: it never executes consumer scripts, fetches artifacts, starts containers or publishes. Keep
consumer behavior proof separate from static lint, reconcile existing lock-validator semantics,
and preserve stuff's ability to build while its own registries are unavailable.

`fleet/policy/actions.toml` owns approved GitHub Action channels, versions, and commit SHAs.
`fleet/policy/release-policy.toml` owns package release conventions and the `[binary]` native
prerelease target contract (portable and single-OS target sets plus forbidden glibc
markers). Publishing checks require the matching catalog opt-in tag. Update these
policy files when changing approved release rules.

`build-make-targets`, `build-locks`, and `build-release-standard` apply to public repositories
tagged `build` and check the [build repository contract](build-repos.md). `build-make-targets`
requires the root Makefile to define `build`, `verify`, `lint`, and `clean`. `build-locks` requires a
valid `sources.lock.json` and validates `release-budgets.json` and `bootstrap.lock.json` when they
exist. `build-release-standard` requires `.github/workflows/release.yml` to be dispatch-only with a
default-branch preflight, a `release-${{ github.sha }}` tag, the shared release-notes step, a
`gh release create` with `--prerelease`, `--verify-tag`, `--target "$GITHUB_SHA"` and the notes file,
a `sha256sum -c` check of `SHA256SUMS`, and `.tar.xz` archives with `.manifest.json` manifests. `release-archive-format` checks release workflows and their invoked packaging code for nonstandard archives; named ecosystem-format exemptions live in `fleet/policy/release-policy.toml`. The `binary-release-standard` fixer converts the ish packaging template to deterministic `.tar.xz` archives; other shapes require manual changes.

`binary-release-static` checks public tool prereleases that publish Linux ELF files, including fork
workflows. It skips private repositories and tools tagged `macos`. Its release-job smoke runs
after artifact download and before packaging. The ELF checks live once in
`repomod/rules/static_elf.py`: ELF64 with the x86-64 or AArch64 machine, no `PT_INTERP`, and
no `DT_NEEDED`. When the smoke scans an artifact directory it also requires at least one artifact
per Linux architecture; explicit artifact paths are checked individually. The checked-in
`docker/musl/verify-static-elf` and the workflow step are rendered from the same script text, and
a test keeps the image copy byte-identical. The fixer inserts the step when the workflow downloads
artifacts in its prerelease job before publication.

`binary-release-notes` requires every public tool prerelease to publish a changelog. The
notes list each commit from the newest non-draft release to the triggering SHA, oldest first, as
`- <12-hex sha> <subject>`, and end with a compare link. The step builds them from the GitHub
compare API, so the release job does not need a checkout. With no earlier release, the notes
record an initial release. When the triggering SHA is not ahead of the previous release, the step
fails, because a diverged history has no single changelog. GitHub's `--generate-notes` is not
used because it lists merged pull requests, and these repositories commit directly to the default
branch. The fixer inserts the step text from `repomod/rules/release_notes.py` before the
`gh release create` step and adds the `--notes-file` flag. A drifted copy of the step is reported
and replaced. Publishers that use `softprops/action-gh-release` are manual findings.

An image-mode builder, whose Dockerfile starts from the published canonical image by digest, must
pass `--trace "$RUNNER_TEMP/linker-trace"` to the verifier. The trace must name the builder's
`/usr/lib/libc.a` and CRT objects, and it must not contain a rustup self-contained path, a
`rustlib` path, or a glibc path. Pinned-mode builders may omit the trace until they migrate. The
verifier never executes a release artifact; the owner-run canary runs each repository's own smoke
command on the target instead.

Action checks and fixes live in `rules/actions.py`. Package checks live in `rules/release.py`.
Rules inspect repository files but do not install dependencies, build projects, or execute release
scripts. Use offline fixtures under `tests/` for policy behavior. Tests use local Git repositories
and fake GitHub responses. Follow the commands in [AGENTS.md](../AGENTS.md).

`gha-settings` requires the shared concurrency group (G001), cancellation
(G002), and `bash -euo pipefail {0}` defaults (G003) in every GitHub workflow.
Its fixer inserts or corrects those root blocks and validates the result with Pinact.
Findings carry the file, line, column, and code; `lint` prints the
`file line:col CODE` format and each code's description as a legend. `gha-triggers`
requires `push` to scope branches to the local default branch whenever `pull_request`
is present, so a commit pushed to a PR branch runs CI once. Its fixer resolves the
default branch from local Git and leaves an unactionable manual finding when it cannot.
`gha-macos` requires GitHub Actions macOS runners to use the `xcode-27` image
(`xcode-27` or `xcode-27-xlarge`); it flags `macos-latest`, version-pinned macOS labels, and
other `xcode-*` labels in runner declarations and matrix values. Its fixer rewrites them to
`xcode-27`, mapping an `-xlarge` suffix to `xcode-27-xlarge`. Intel labels have no
`xcode-27` image (the image is Apple Silicon only), so they stay unchanged. `gha-ubuntu` requires
`ubuntu-26.04` or `ubuntu-26.04-arm`; `ubuntu-latest` is banned so a job never silently moves
between Ubuntu releases. Its fixer rewrites `ubuntu-latest` and ARM labels to
`ubuntu-26.04-arm`, and older x86 labels to `ubuntu-26.04` for jobs that need x86. A
`ubuntu-latest` job or matrix entry that mentions `linux/amd64` also needs x86 and gets
`ubuntu-26.04`, because an ARM runner cannot execute those images.
`gha-syntax` validates GitHub Actions files offline with Pinact's default profile and the
explicit `fleet/policy/actions.toml` catalog. Its fixer returns a catalog-backed Pinact plan from a disposable
worktree; repomod keeps validation and repository writes.
`no-formatters` rejects formatter
commands, formatter dependencies, and formatter configuration files. Ruff lint commands such as
`ruff check` remain allowed. Ruff's format command and format configuration are banned. The rule
also bans SwiftLint commands, configuration, and `Package.swift` dependencies. Use
[swift-bylaws](https://github.com/joshuarli/swift-bylaws) for Swift project rules. `mdtool`
runs the read-only documentation audit at `~/.local/bin/mdtool` for each repository,
except repositories tagged `fork`, which are exempt. Both rules skip paths under directories
excluded from the Cargo workspace, since vendored fork crates are not maintained documentation.
mdtool's consumer advisories (C001, C002, C003) say that code reads or embeds a document, so they
are not repository defects and `mdtool` does not report them. A README title that is the repository's own name is not a developer-topic
heading (T003), so `node-build` is not flagged for containing "build".
`workflow-redundancy` flags a workflow other than `lint.yml` or `lint.yaml` that runs `make lint` as a
`run` command when the lint workflow also runs it and the two workflows share a trigger event. Lookalikes such as
a `lint-fix` target, `echo make lint`, or step names do not count, and a workflow whose triggers cannot be read is
skipped. The finding is not fixable because choosing which workflow keeps the step is a human decision.
`mirrored-docs` compares `.agents/skills` with `.claude/skills`, and the `agents` directories under `.agents/` and `.claude/`.
For each path that is a regular file in both trees with identical bytes it reports the `.claude` copy; the
owner makes one tree a symlink to the other. Symlinks, files present in only one tree, and files that differ
are not reported, and repositories tagged `fork` are skipped. The finding is not fixable.
`generated-artifacts` reports tracked build outputs and requires ignore coverage for
language artifact directories. Operating-system metadata files such as `.DS_Store` and
`Thumbs.db` are environment noise covered by the global ignore file, so the rule does not
require in-repository patterns for them. Its fixer appends missing language patterns to the end of
a regular or absent root `.gitignore`, preserving existing content; a symlinked `.gitignore` and
tracked outputs stay manual findings.

## GitHub Actions with Pinact

Keep `pinact` on `PATH` when running repomod checks and fixes. `gha-syntax` runs
`pinact lint --profile=default --format=json --catalog actions.toml` on workflow and action
metadata files. The other GitHub Actions fixers validate their planned changes with
`pinact lint --profile=correctness --format=json --catalog actions.toml`. The catalog path is explicit; repomod's `fleet/policy/actions.toml` owns approval policy, and
catalog-backed linting and fixing make no network requests.
The former `gha-pin` and `gha-version` rule IDs are consolidated into `gha-syntax`.

The `gha-syntax` fixer selects only workflow and action metadata files. It runs Pinact's
catalog-backed `fix` in a detached worktree under the repository's `.work/tmp` directory by
default, honoring an explicitly set `TMPDIR`, and returns changed file contents as a normal
repomod file plan. Repomod checks the plan's allowed paths and policy postconditions, then owns
per-rule commits, push decisions, pull requests, and cleanup. The canonical checkout is not the
Pinact write target.
`gha-lint-workflow` requires every repository to have `.github/workflows/lint.yml` (or
`lint.yaml`) that runs `make lint`. Its fixer creates the workflow from a template pinned to the
current `fleet/policy/actions.toml` checkout when it is missing, provisioning the lint toolchain from the
approved pins (`astral-sh/setup-uv` with the approved uv and Python 3.15 for Python sources,
`pnpm/setup` with the approved pnpm and Node for TypeScript sources; Rust resolves its pinned
toolchain file via rustup with no setup step). A present workflow that does not run
`make lint` is a manual finding. `make-lint-target` requires a root `Makefile` that defines a
`lint` target, and pins the linter by detected language: `cargo clippy` for Rust, `ruff`
for Python (never `flake8`), and `oxlint` (or a `pnpm`/`npm` `lint`/`check` script, which
`typescript-standard` already pins to Oxlint) for TypeScript. The rest of the lint command
stays a per-repository human choice, so a missing Makefile or a missing target is always
manual: add the target running the repository's linters as a non-mutating check.
`make-lint-target` rejects `--fix` in the lint recipe. Linter versions ride the existing
pins: the `rust-toolchain` nightly for clippy, `fleet/policy/python-tools.toml` for ruff, and
`fleet/policy/typescript-tools.toml` for oxlint. `make-clean-target` checks for a root
Makefile `clean` target. Each repository defines which generated outputs the command owns.
In a disposable checkout, prove that `make clean` removes those outputs, preserves tracked
fixtures and unrelated local state, and succeeds when repeated. Recipe safety needs that
behavioral check. Repomod only inspects the entrypoint and has no generic clean fixer.
`make-test-target` checks for a declared root `test` rule across the catalog,
including repositories with local-only verification. A `.PHONY` entry alone
does not satisfy it. Choose the native tests for each repository and verify
that the target exercises its bounded Change suite.

Catalog-backed fixes preserve action subpaths, refuse major changes and downgrades, and do not
treat an unlabeled SHA as approval. The bounded checker is not a complete implementation of
GitHub's workflow validator; dynamic and unsupported syntax remain outside its coverage claims.
See the [Pinact guide](https://github.com/joshuarli/usr/blob/main/tools/pinact/README.md) and its
[compatibility report](https://github.com/joshuarli/usr/blob/main/tools/pinact/docs/compatibility.md).

`pins refresh` fetches stable releases and commit SHAs for `fleet/policy/actions.toml`. Pinact's catalog-backed
fixer updates references and version comments only within an identifiable major; major changes and
unlabeled SHAs still need review. `--only actions|python|typescript|musl` restricts the run to one
pin domain, and `--check` reports the files that would change without writing them (exit 1 on
drift). A failing fetch or malformed source exits 2 and writes nothing.

## Musl toolchain lock

`fleet/policy/musl-toolchain.toml` is the single approved lock for musl Linux build inputs. It owns:

- the upstream musl release and release date;
- the `stable` Alpine channel, with the approved `image` tag, index digest,
  per-architecture (`amd64`, `arm64`) manifest digests, and Alpine release;
- the exact direct `apk` versions per architecture (`x86_64`, `aarch64`);
- the LLVM, mold, and rustup version and archive pins with SHA256 checksums;
- the bespoke builder adapters (`python-build`, `cmake-build`, `chromium-build`,
  `node-build`, `git-build`, and `zzz`);
- an optional `[image]` reference and digest for the published canonical builder.

Alpine edge is not approved. Edge keeps only the newest revision of each package, so exact
pins against it break whenever a package is rebuilt. Builders use the stable channel.
Start from the approved Alpine base and add the packages the build commands
need with their dependency closure. Keep qualification-only packages scoped
to the tests that use them.
The shared contract pins base digests, direct APK versions, and toolchain archive checksums.
It does not guarantee the complete transitive APK closure or offline installation. Bespoke
builders retain their own closure and qualification machinery.

The loader rejects a lock whose version is not `1`, whose only channel is not `stable`, whose
digests are not `sha256:` values with 64 lowercase hex characters, whose
`musl` and `musl-dev` versions differ within a channel and architecture, whose musl package
does not match the upstream release, whose adapter kind or fields are unknown, or whose
adapter paths escape the repository. The `stable` branch is an Alpine major/minor line.

`pins refresh --only musl` reads the musl release page, the stable main and
community `APKINDEX` files for both architectures, and the Docker image metadata for the
approved image. It parses `P:`/`V:`/`S:` records directly rather than shelling out to
`apk`, keeps the approved package set, and verifies that each package still exists. Unrelated
packages that appear more than once in an index do not affect the approved set. A missing
package, a malformed index, a failed fetch, a Docker failure, or a rendered lock that does not
round-trip fails the refresh without writing.

The refresh updates the upstream release, channel digests, manifests, Alpine releases, and
package versions. It preserves the manually owned LLVM, mold, and rustup versions and
checksums; those bumps are explicit, checksum-verified edits. The stable channel
approves one immutable patch, so `pins refresh --only musl` prints the current release of the
moving `alpine:<branch>` tag as an observation but does not write it. A newer branch patch
does not fail `--check`; a newer musl package revision, a changed channel digest, or a stale
approved image does. To approve a newer patch, update `image` and `index_digest`, refresh,
build the canonical image, and run its smoke test. The package table covers every package the
conventional builders, tansu, and `git-build` install directly; add a package only when a
real builder uses it, with its live index version.

`linux-musl-toolchain` enforces the lock at error severity. It applies to every repository,
returns no findings when no musl builder exists, and skips private, `fork`, and
`macos` repositories. It scans regular `Dockerfile`, `Dockerfile.*`, `*.Dockerfile`, and
`docker/*.Dockerfile` files outside build, vendor, and fixture trees, plus builders named by
release or CI workflows that build a Linux musl target. A Dockerfile is in scope when its raw
text mentions musl or when its referencing workflow step mentions musl or the file does.
An Alpine Edge base or an Edge APK repository in an `apk add` override or a shell redirect to
`/etc/apk/repositories` also puts the Dockerfile in scope. The check resolves Dockerfile build
argument defaults. A workflow that declares Alpine Edge as a job container, service image,
or `docker://` step gets a manual finding at the corresponding image field.

For every in-scope Dockerfile, each Alpine base must carry the approved stable digest
(the index digest, or the per-architecture manifest for a `--platform` stage). An
`alpine:edge` base is a manual finding; the fixer does not move it to stable, because the
stable package set can differ. `ARG` defaults are resolved, so a build
argument that controls a base image or package version must carry an approved default.
Every `apk add` package must be an exact `name=version`; `musl` and `musl-dev` must equal the
channel, other packages must equal the lock when it records them, and an unrecorded package
requires an exact pin plus a manual finding to add it to the table. Architecture-specific
versions require an architecture-conditional argument. A non-approved `--repository` or a
direct `.apk` URL is a finding. CMake's controller supplies local, hash-verified APKs to
an offline Docker build. Its adapter checks the Dockerfile's base and requires stable
repository URLs, sizes, and SHA-256 digests for the locked APKs on both architectures.
The OpenSSL CLI used by qualification must also come from the approved stable branch.
Musl builders must not use `apt-get`, a Debian or Ubuntu
final stage, or an `unknown-linux-gnu` target; `chromium-build` may keep its digest-pinned
Debian compiler-host stage and its documented `x86_64-unknown-linux-gnu` compiler-layout
symlink. Remote installers must be versioned archives with SHA256 verification. A binary
prerelease that builds Linux musl targets on `ubuntu-*` must use a container or Docker; the
`zzz` adapter is exempt once its Zig archive is checksum-pinned.

The full Rust release-builder contract applies when a Rust repository has a binary
prerelease contract. It keeps the versioned rustup and `llvm-prebuilt-musl` archives with
checksums, both musl targets, `rust-src`, `musl-cargo`, the CRT stubs, and `libutil.a`, and
requires the root Makefile's `release` or `dist` recipe to build std with `-Z build-std=std`
and `-Z build-std-features=`. The LLVM, mold, and rustup versions in `ARG` defaults or
literal archive URLs must equal the lock. The canonical image builds musl libc from the
locked source with clang and installs no `gcc` package, so released Linux ELFs carry no GCC
runtime dependency and no `GCC:` `.comment` entry; the shared `verify-static-elf` step enforces
both. `libgcc` stays installed only because the host `rustc`, `cargo`, and `mold` binaries link
`libgcc_s.so.1`, and the Rust sysroot symlinks it for host proc-macro dylibs. A Rust builder without that contract, such as a
CI check image or benchmark image, is checked only for its base digest and package pins.

Each adapter has its own check. `python-build` validates the `bootstrap.lock.json` release,
index and image digests, and both architectures' musl and musl-dev closure entries.
`chromium-build` checks the headless AMD64 package lock, the approved Alpine
`BASE_IMAGE` digest, and the compiler-host stage digest. For archive-backed
installs, the Dockerfile must install from the named APK context with networking
disabled, and the lock must record the approved `musl` and `musl-dev` APKs
with stable URLs, hashes, and sizes.
`node-build` validates `ALPINE_AMD64` and the workflow's `apk add` versions. `git-build`
requires exact package pins. `zzz` requires the approved Zig version and a verified archive
checksum. Adapter mismatches are manual findings that name the repository's own refresh
command; none of them rewrites a generated lock.

The fixer rewrites the base digest and exact package versions in conventional builders and
tansu, preserving formatting, comments, and multi-stage structure. It only edits packages when
every package in the file has an approved version. It may rewrite the `node-build` workflow's
`apk add` line when every package there is approved, and it adds the approved checksum to the
`zzz` download. Bespoke lock mismatches stay manual.

## Canonical musl image

`docker/musl/Dockerfile` is the canonical builder source for the conventional Rust builders.
Its `BASE_IMAGE`, LLVM, mold, and rustup `ARG` defaults must equal `fleet/policy/musl-toolchain.toml`, and
its direct `apk` packages must equal the approved stable versions for both architectures.
`repomod musl build --platform linux/amd64|linux/arm64 --output PATH` validates those
defaults and the image's `rust-toolchain.toml`, builds with the lock's build arguments, and
writes a local OCI layout. It prints the layout's manifest digest and has no push path. A
failed build or a Dockerfile/lock mismatch exits nonzero without replacing the output.

When `[image]` records a published reference and digest, a conventional builder may start from
that image by digest; the rule accepts the stage and exempts it from package and toolchain
checks because the image owns them. A different digest is a finding. Until `[image]` is
present, pinned Alpine mode is the only accepted form: a musl builder must use an approved
Alpine base, not an unpublished canonical reference. The fixer never switches a builder to
image mode; that migration is an owner-run step after publication.

### Publication and migration

Refresh stays manual; do not recreate a scheduled refresh without an owner request.
Review pin changes, rebuild and publish the image, qualify canaries, then update consumer digests.
The local platform-manifest digest printed by `repomod musl build` is not the published
multi-architecture index digest.

After refreshing pins, synchronize the Dockerfile's `ARG` defaults, direct APK pins, and
`docker/musl/rust-toolchain.toml` with `fleet/policy/musl-toolchain.toml`. Complete at least one local
`repomod musl build`; it validates the image definition against the lock. Stop if that build
fails, and use the same validated sources for publication. Choose a registry reference and
tag, then publish the multi-architecture image with Docker Buildx:

```sh
uv run repomod musl build --platform linux/amd64 --output .work/musl-amd64
REPOMOD_IMAGE=ghcr.io/OWNER/musl-toolchain:VERSION
docker buildx build --platform linux/amd64,linux/arm64 --push \
  -t "$REPOMOD_IMAGE" -f docker/musl/Dockerfile docker/musl
docker buildx imagetools inspect "$REPOMOD_IMAGE"
```

Record the published reference and index digest in `[image]` of `fleet/policy/musl-toolchain.toml`.
Run `uv run repomod pins refresh --check --only musl` and the image-mode policy fixtures.
Qualify the `srv`, `tm`, and `fdu` canaries on both Linux architectures: verify asset checksums,
run the shared ELF verifier, and execute each repository's runtime smoke command on its target.
Current verifier defects are tracked in [TODO.md](../TODO.md); a green directory scan alone is
not sufficient qualification while that defect is open.

Migrate a conventional Rust builder to `[image].reference@[image].digest`, remove duplicated
toolchain setup, and have its release workflow supply the required linker trace. Recheck the
canaries before broader migration. Bespoke Python, Chromium, Node, Git, and Zig adapters retain
their own build systems; policy coverage does not require moving them to the shared Rust image.
Run their heavy qualification on an appropriate Linux host and confirm commands against their
current documentation.

The owner has declined migrating conventional Rust builders to the shared image; each keeps its
own musl toolchain under this rule and the static ELF verifier. The image and procedure above
remain for a future owner-run migration.

## Owned-tool support

`fleet/policy/owned-tools.toml` maps owned repositories in the `joshuarli` and `laputa-systems`
namespaces to their commands, declaring for each a help source and test, a `gap`, or an `exempt`
reason, plus install evidence (`install_manifest`, `record`, `launcher_dir`, `installed_from`) and
`[not_applicable]` entries. The read-only `owned-tool-support` rule checks that data against
manifests and installers. The lookup contract, evidence table, and status meanings live in
[owned tools](fleet.md#owned-tools).

`fleet/policy/owned-substitutes.toml` backs the read-only `owned-tool-substitution` rule, which
implements [owned tools first](fleet.md#owned-tools-first). Per producer it lists the upstream
package names per package manager (`apk`, `apt`, `brew`, `dnf`, `pacman`; a leading `^` marks a
regular expression matched against the whole package name, so `clang-19` and `clang22` match
clang while `clang-format` does not), the setup actions it replaces, and the download URL
prefixes it replaces. The rule scans `.github/workflows/*.yml|yaml`, `Dockerfile*`/`*.Dockerfile`/
`Containerfile*`, files under `docker/`, `Makefile`/`*.mk`, files under `scripts/`, and
`flake.nix`, joining `\` continuations and expanding simple `NAME=value` variables in install
arguments. It flags `apk add`, `apt`/`apt-get`/`aptitude install`, `brew install`,
`dnf`/`yum install`, and `pacman -S`-family commands, `uses:` references to the mapped actions,
matching download URLs, and `uv python install` (which always maps to the producer that owns
`astral-sh/setup-uv`). `astral-sh/setup-uv` itself is flagged only when its `with:` block sets
`python-version` or a later step runs `uv python install`, because uv is not an owned tool and
only those uses provide Python. Package names match whole tokens after stripping `=version`,
`<`/`>`/`!`/`~`/`^` specifiers and `:arch` suffixes, so `git` is flagged only as a package
argument, never as a command. `[exempt."owner/repo".producers."producer/id"]` entries carry
`reason` (one of the grounds in [owned tools first](fleet.md#owned-tools-first)) and `reassess`;
they suppress that producer's findings in that repository, and an exemption matching no finding
is stale and reported. Exemptions for producers or repositories the substitutes or catalog
policies do not know are findings. Findings are violations naming the file, line, upstream
package or action, and the owned producer to use through `buildlib.tools` or the
`laputa-systems/buildlib/setup` action.

## Other policy rules

`gha-test-workflow` requires a workflow triggered by `pull_request` to run `make test` or
`make test-ci` as a command, so CI and local verification share the repository's own test entry
point. Other `make test-*` targets do not count. A pull request workflow that calls a test runner
directly (`cargo test`, `pytest`, `vitest`, a package-manager test script, `node --test`, or
`go test`) is reported per workflow for manual repair, because its setup or matrix is
repository-specific. Without any test step, a repository that has a `test` target and no `ci.yml`
gets a fixer that writes `.github/workflows/ci.yml` from the lint workflow
template with a `make test` step; one without a `test` target, or with an existing `ci.yml`, is a
manual finding. The rule covers every managed fork and reports unreadable workflows or
undeterminable triggers as operational findings.

`fork-workflow-names` checks the names of all workflow files in a managed fork. GitHub
status and workflow policy recognize the same names in
`repomod/workflow_policy.py`. For forks, `gha-syntax` checks the test and lint workflow
files. Release workflows follow the release rules. Compare workflow changes with the
upstream merge base to catch files with the same name that carry upstream jobs.

The supported `gha-test-workflow` shape uses an unrestricted `pull_request` trigger, or
`branches` including the known default branch and `types` including opened, synchronize and
reopened. Path filters and `branches-ignore` are unsupported. The test job has no `if`, reusable
workflow call, or enabled `continue-on-error`; its test step has no `if` or enabled
`continue-on-error`, uses bash or sh, and runs a single `make test` or `make test-ci` command.
Make variable assignments may appear before or after the target. Put container execution in a
Make target and call that target in its own step.

`fleet/policy/retention.toml` lists repositories holding mutation, coverage, and strict-profile
guarantees. `mutation-lane`, `coverage-target`, and `strict-profile` check those guarantees
without fixers. Eligibility is independent of repository files so deleting a campaign record,
target, workflow, or configuration cannot disable its own check.
Rust workspace settings are checked against each discovered member's
effective lints, including explicit inheritance from `workspace.lints`.
The target check reads literal Make rules. It also accepts conditionals whose
branches contain only simple variable assignments. Conditional rules or
recipes, included Makefiles, and dynamic rules require separate inspection.

Python-only repositories retain a pull-request `make mutants-diff` job with
full checkout history, pinned setup-uv, and a matching exact mutmut development
pin in `pyproject.toml` and `uv.lock`.

`fleet/policy/rust-tools.toml` records the approved cargo-mutants release;
`mutants-diff-lane` pins the job to it.

`strict-typing-profile` checks the adopted settings in the same retention policy for eligible
Rust repositories. Register a setting only after its qualification passes.

`make-coverage-target` and `mutants-diff-lane` extend the same guarantees to Rust repositories that
`fleet/policy/retention.toml` registers explicitly (`[coverage-target]` and `[mutation-lane]`);
campaign records, Makefile targets and other repository files never select them. Plain forks are
excluded unless they are tagged `fork-diverged`. `mutants-diff-lane`
additionally requires the pull-request workflow job to pin cargo-mutants at the approved
release, to check out with full history, and to pass `BASE_REF` through `env`
(`github.base_ref`). Its fixer writes the reference gate
(`scripts/mutants_gate.py` and its test, vendored byte-identically from `repomod/fixers/`),
the `BASE ?= origin/main`, `mutants-selftest`, and `mutants-diff` Makefile block, and the srv job
inserted as the first job after the workflow's `jobs:` key; a repository without a
pull_request workflow keeps the tooling but needs a test workflow first (`gha-test-workflow`).

The fixer never writes a mutation scope. Blocking mutation covers a small scope around an
important contract, so the repository declares it in `.cargo/mutants-gate.toml`: `scope`, an
explicit list of `.rs` files (no directory or glob), and `critical`, a regex over mutant names
that selects the important functions. A repository whose own gate script reads per-file
`[[critical]]` tables (each an explicit `.rs` `file` and an optional function `regex`, as
diff-pretty's does) declares its scope that way instead. A missing or invalid declaration is a
non-fixable `mutants-diff-lane` finding. The gate selects by change: production changes mutate their
changed lines only; a change to tests, fixtures, build configuration, the gate, or test code
inside a production file (including deleting a protecting test) also mutates `scope` filtered
by `critical`; a mixed change selects both; documentation-only changes select nothing. A timeout
is replayed at 3x on exactly one mutant (a one-line `--in-diff` plus an exact-name `--re`,
because cargo-mutants 27.1.0 lists struct-field deletions regardless of `--re`); a replay that
cannot select exactly that mutant leaves an unresolved timeout, which fails the gate. Broad audits
stay advisory.
Neither rule fixes Python or TypeScript repositories.

`github-protection` requires zero approving reviews on protected branches so owner-only
automation never waits on reviews. It also reports required GitHub Actions status checks that no workflow produces, expanding job
`name:` templates over `strategy.matrix` (including `include` and `exclude`) and falling back to
the job id; a workflow whose names cannot be determined statically (for example a matrix from
`fromJSON`, or a reusable-workflow job) suppresses the check for that repository.
GitHub applies each `include` to the original combinations without overwriting original values;
a later include can overwrite values added by an earlier one, and an unmatched include becomes a
separate combination that later includes do not match
([GitHub's include semantics](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations#expanding-or-adding-matrix-configurations)).
Repositories without branch protection are skipped. It has no fixer; change protection with explicit API calls.

`rust-release-profiles` rule for binary-shipping Rust repositories. `[profile.release]`
is for performant testing and CI: `opt-level = 3`, `lto = "thin"`,
`panic = "abort"`, `strip = false`, and no `codegen-units` cap, so debug
and test builds link fast while staying optimized. Final prerelease binaries
are built with `--profile dist`, never `--release`:

```toml
[profile.dist]
inherits = "release"
lto = "fat"
codegen-units = 1
strip = true
```

CI workflows build and test the `release` profile; prerelease workflows package
`target/<triple>/dist/`. Libraries without shipped binaries need no `dist` profile.

`rust-toolchain` requires Rust repositories to pin `nightly-2026-11-09` in the root
`rust-toolchain.toml` and include `rust-src` and `clippy`. Its fixer preserves other toolchain
settings and extra components. It leaves malformed TOML, symlinks, non-table `toolchain` values,
invalid component arrays, and toolchain settings declared outside `[toolchain]` for manual repair.

`python-standard` requires Python 3.15 and exact uv, Ruff, and ty pins. `fleet/policy/python-tools.toml` records
the approved releases. `pins refresh` updates them from PyPI, and the fixer regenerates `uv.lock` in
a disposable copy before returning its file plan. It updates `.python-version` pins and explicit
GitHub Actions Python versions below 3.15, and removes matrix rows made identical by that update.
Block-style workflow version lists remain manual findings. When a repository has no
`pyproject.toml`, the fixer creates an unpackaged project (`[tool.uv] package = false`, version
`0.0.0`, no runtime dependencies, repository name as project name, approved dev pins) and its
`uv.lock`; it never replaces or merges an existing file.

`typescript-stack` applies to TypeScript repositories. `fleet/policy/typescript-tools.toml` records the latest
stable Node.js and the newest stable pnpm release in the approved major (including `next-12`
when it leads `latest`); `pins refresh` updates those approvals. The rule checks
runtime pins offline, requires `tsrs` 0.23.0 or newer built as TypeScript 7 or newer, strict
type checking, Oxlint 1.92 or newer with type-aware linting from that `tsrs` package, and Vitest 5
or Node test commands (including Node suite launchers).
A direct `oxlint-tsgolint` dependency is a finding. It also
removes Deno configuration and npm, Bun, or Vite+ script commands. Apps also use Effect 4. Frontend
apps use Vite 8 and Solid 2. An app counts as a frontend when it depends on a UI framework
(React or Solid) or contains JSX sources; a plain Vite bundle of vanilla TypeScript does not.
Nested package manifests are inspected, and a pnpm workspace coordinator without its own TypeScript
source or configuration is checked as a package authority rather than a TypeScript package.
The package check script can call Oxlint and `tsrs --noEmit` directly or invoke their scripts.

`fleet/policy/frontend-toolchain.toml` owns the tested frontend package versions for its
listed repositories. The rule checks existing direct dependency, dev-dependency, and optional
dependency declarations in every inspected manifest against those exact pins. It does not
require unused tools or constrain published library peer ranges. Upgrade coupled packages
together, verify frozen installs, type checks, lint, production builds and applicable browser
tests, then update the policy and consumers. Cloudflare SDK/runtime packages remain a separate
compatibility group. Existing Node tests and project-specific build configurations remain valid.
`audit-upgrades` excludes these approved packages from independent latest-version checks and
pnpm upgrades; the frontend policy check owns their alignment.

Rust dependency choices and bans are owned by `fleet/dependency-roles.toml` and the
[audit rules](audit.md), not an additional `rust-deps` rule.

`rust-collections` bans `std::collections::BTreeMap` and `std::collections::BTreeSet` in
first-party Rust source. It reports every usage with its file, line, and column. Use a hash
collection instead: `rustc-hash` 2.x for small integer-heavy maps and sets, `rapidhash::fast`
for general-purpose performance, and `foldhash::fast` when using `hashbrown` without a
compelling reason to override its default. Hash collections are unordered, so code that
depends on sorted iteration must sort explicitly. The rule skips repositories tagged `fork`
and paths excluded from the Cargo workspace, ignores comments and string literals, and has no
fixer because the replacement and ordering behavior are per-site decisions.

`conventional-commits` requires Conventional Commit subjects (`type[(scope)][!]: description`
with one of `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `revert`)
on open pull requests; drafts are skipped and overlong subjects warn. It is lint-only with no
fixer: rename the PR explicitly. It needs the network, so it is excluded from offline checks.

`audit-upgrades` reports locked direct dependencies that lag their registry's latest stable
release as fixable findings. It resolves against the repository's configured Cargo source, npm
registry, and default Python index, so a version the mirror does not carry is not reported;
repositories without an override use the public registries. Its check refreshes the shared audit
cache over the network, so it
is excluded from offline checks. Its fixer runs the native upgraders (`uv lock --upgrade`,
per-project `pnpm update --latest`, recursive in a pnpm workspace, `cargo update`, `go get -u ./...` plus `go mod tidy`) in a
disposable copy and returns the changed lockfiles and manifests as its file plan. For Cargo it
updates simple caret requirements to admit newer incompatible releases before running `cargo update`.
Explicit pins, ranges, conflicting pins and incompatible Rust versions stay manual.

`registry-sources` requires non-fork repositories to resolve Cargo, npm/pnpm, and Python
dependencies from the private `stuff` registry. `fleet/registries.toml` also allows the Sentry work npm
proxy. The catalog exempts `stuff` itself so it can be rebuilt when its registry is unavailable.
`fleet/registries.toml` owns the approved URLs
and the `enforce` switch; the fleet is migrated, so `enforce = true` and the rule checks, per project directory holding a
lockfile (and the root `package.json` or `pyproject.toml`), that the configuration is present in that
directory or an ancestor: `.cargo/config.toml` replacing `crates-io` with the approved sparse
source, `.npmrc` with `registry=` set to the stuff registry or the allowed work proxy and no other registry key (and no
`registry` or `registries` in `pnpm-workspace.yaml`), and a `default = true` uv index at the approved
URL in `pyproject.toml` or `uv.toml`. It also scans lockfiles. `Cargo.lock` keeps crates.io source
ids under replacement, so those are accepted along with `cargo.source` and `cargo.native`; other
registries are findings. pnpm and npm lock
tarball URLs must start with the stuff registry or the allowed work proxy, and `uv.lock` registry sources must equal the
approved index. Git sources are findings unless the repository's catalog override ignores
`registry-sources:git:NAME` with an `ignore_reason`; a `path` or `link` source outside the
repository is ignored the same way with `registry-sources:path:NAME`. Path, `link:`, `file:`, and workspace sources
are allowed while they stay inside the repository. Unapproved registry sources are reported once
per lockfile and source, listing the first packages.

`laputa-rustix` prefers `laputa-rustix`, the laputa-systems fork of `rustix` with
Windows support removed, over the crates.io `rustix` crate. It reports a direct
dependency on `rustix` in tracked `Cargo.toml` files and rewrites its version requirement into
an inline table carrying `package = "laputa-rustix", registry = "mycrates"` plus the version.
The dependency key stays the same so `rustix::` paths in dependent code remain unchanged, but
the manifest gains a `mycrates` registry source. Dependencies that rename a different package, that point
at a `path` or `git` source, and fixtures, snapshots, vendored trees, and the
`workspace.exclude` subtrees are left alone, as is anything that already resolves to
`laputa-rustix`. The fixer rewrites the manifest and refreshes each affected
`Cargo.lock` with `cargo metadata` in a disposable copy; it fails rather than writing a
lockfile that does not resolve. `stuff` itself is exempt (it builds against crates.io),
and the fork is published from the `laputa-systems/rustix` repository with
`make publish`.

The fixer adds the missing configuration and leaves every other finding manual. It writes
`.cargo/config.toml` at the repository root (Cargo merges parent configuration), `registry=` into
each npm project's `.npmrc` (npm and pnpm read only the project's own file), and, per uv project, the
default `[[tool.uv.index]]` plus `[tool.uv] environments` for darwin and linux, then runs `uv lock` in
a disposable copy so `uv.lock` records the stuff index. Windows-only packages leave the lock because
`environments` excludes Windows, and stuff publishes macOS and Linux wheels only. A file that already
sets a different cargo source, npm registry, or uv index fails the fixer and needs a manual edit.

`audit-upgrades` skips private repositories and forks, including when explicitly selected for fixes.
It resolves npm scopes and named Cargo registries using the repository configuration.

`audit-vuln` and dependency enrichment exclude RustSec informational advisories after fetching their OSV details.
A failed detail lookup fails the check. Run `deps enrich` to refresh older dashboard cache entries.
