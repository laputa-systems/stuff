# Build repositories

A repository tagged `build` produces release archives of upstream software (CPython, Node.js,
CMake, FFmpeg, Git, OpenSSH, Chromium, Pi). This document is the contract those repositories share.
repomod checks it with the `build-release-standard`, `build-make-targets`, and `build-locks` rules.

## Shared build tooling across the fleet

Owner policy, 2026-11-24: every catalog repository adopts `laputa-buildlib`, at least to acquire
owned tools (see [owned tools first](fleet.md#owned-tools-first)); the `assess` and `exempt`
dispositions below are migration states, not end states.

Owner policy, 2026-11-20: use `laputa-buildlib` for material first-party build tooling that
duplicates its verified acquisition, lock readers, release manifests, reproducible archives,
checksums, supported target mapping or binary inspection. This applies beyond `build`-tagged
repositories. Judge custom build behavior, not product language or codebase size. Native
compilers, package managers, product policy and existing user entrypoints keep their roles.

### Dispositions

Every active catalog entry has exactly one entry in `fleet/policy/buildlib.toml`:

- `enrolled`: the repository uses shared helpers. The entry names the entrypoints that call them
  and whether it vendors the bootstrap shim.
- `assess`: the repository is eligible but not yet migrated. Lint reports it as pending and
  blocks nothing.
- `exempt`: native tooling is sufficient, the repository is an effectively-upstream fork, or the
  work is deferred. Each exemption has a `reason` and a `reassess` condition.

Simple native commands and established smaller implementations justify an exemption; an unused
import never satisfies enrollment. Keep pristine upstream and vendor code outside migration. Add
an upstream buildlib abstraction only when two consumers demonstrate it. stuff stays exempt: its
registries must build while its own package registries are unavailable, so it cannot fetch the
stuff-hosted wheel. Add a new catalog entry to the policy when it is admitted, or lint reports it
as unclassified.

### Pins and the bootstrap

Consumers pin `laputa-buildlib==<version>` and its wheel digest in `pyproject.toml` and `uv.lock`,
with the wheel identity also agreeing in `sources.lock.json` when that file is present.
`fleet/policy/buildlib.toml` owns the approved wheel and bootstrap shim identities; see
[policy development](policy-development.md#release-policy) for the exact checks. A repository that
uses buildlib or needs a newer Python than its distribution ships vendors
buildlib's `bootstrap/buildlib-run` and `bootstrap/python.lock` unchanged at the revision the
policy approves, and runs Python through it (`PYTHON ?= sh bootstrap/buildlib-run --`). The shim
checks the size and SHA-256 of the python-build or uv archive before extracting it and pins the
wheel's SHA-256. On a glibc host without musl 1.2.5 or newer, such as Ubuntu 24.04, it falls back
to the pinned uv and uv's upstream CPython, whose trust path is uv's own metadata.

The shim provisions only Python and the wheel. Each repository keeps a small idempotent
`scripts/setup-dev` for its distribution packages, pinned toolchains and locked development tools,
and a development doc listing each package's consumer. Keep native-only commands usable without
an interpreter download.

### Owned toolchain inputs

Build tools are inputs like sources. When an owned producer supplies one (gluon for Meson and
Ninja, cmake-build, llvm-prebuilt-musl, python-build, node-build), a build repository pins that
producer's release and digest in its locks instead of installing the distribution package, and
reports a producer gap in the producer's backlog rather than switching back. See
[owned tools first](fleet.md#owned-tools-first) for the substitutions and the allowed reasons to
keep an upstream tool.

### Migration proof

A migration replaces a local implementation; it does not add a dependency beside one.

1. Record the base revision, the entrypoint, the local code replaced and the buildlib API used.
   Keep public Make and CLI entrypoints, compiler flags and consumer-specific lock fields.
2. Exercise the installed wheel through the ordinary user path, and check import provenance so a
   local source tree or `PYTHONPATH` cannot mask it.
3. Keep consumer boundary tests for changed behavior: wrong digest, size or target, incomplete
   downloads, cache reuse, failure propagation and archive layout. buildlib tests its own
   internals once.
4. For changed release code, compare target identity, layout, manifests, checksums and hardening
   on generated artifacts without publishing them.
5. Pass cold `linux-capsule` runs from a clean clone of the delivered commit: `ubuntu:24.04`
   (the uv fallback) and Debian 13 or Ubuntu 26.04 with `musl` (the python-build path). Keep the
   supported macOS checks. Record the selected interpreter branch, commands, exit codes and cold
   cost in the repository's own buildlib adoption doc.
6. Land through the repository's required checks, then enroll it in the policy against the merged
   default branch.

### Enforcement

`buildlib-usage` (`repomod/rules/buildlib.py`) reads the policy. For enrolled repositories it
checks the exact pin and its agreement across `pyproject.toml`, `uv.lock` and the shim's
`python.lock`, the vendored shim's digests, and the declared entrypoints. A repository whose
only consumer is the shim, with no `pyproject.toml`, is pinned by `bootstrap/python.lock`. The
rule never runs consumer scripts, fetches artifacts or starts containers. File presence cannot
prove reuse; the consumer's behavior tests do. Adoption does not extend the build-repository
release format to unrelated product releases.

Its fixer moves an enrolled repository to the approved wheel: the `pyproject.toml` pin, the
`laputa-buildlib` entry in `uv.lock`, the buildlib entry in `sources.lock.json`, and the vendored
shims, copied from `fleet/policy/buildlib-bootstrap/`, the released buildlib bootstrap whose
digests the policy approves. To approve a new buildlib release, update `[artifact]` (version,
filename, sha256, size and bootstrap revision), replace the two files in
`fleet/policy/buildlib-bootstrap/` with that release's `bootstrap/`, and run
`uv run repomod fix --rule buildlib-usage`; it opens one pull request per consumer.

## Make targets

The root `Makefile` defines `build`, `verify`, `lint`, and `clean`. `build` produces the release
archives for one target, `verify` checks them, `lint` runs the repository's static checks, and
`clean` removes build output. Optional steps use these names when they exist: `fetch` downloads
and verifies pinned inputs, `package` assembles archives from a finished build, and `repro`
rebuilds and compares archives byte for byte.

`TARGET` selects the target as a Rust target triple: `aarch64-apple-darwin`,
`x86_64-unknown-linux-musl`, or `aarch64-unknown-linux-musl`. No glibc targets are released.

## Pinned inputs

All three lock files are JSON objects with an integer `schema_version` of `1`.

`sources.lock.json` pins every upstream input the build downloads:

```json
{
  "schema_version": 1,
  "inputs": [
    {
      "name": "cpython",
      "version": "3.15.1",
      "url": "https://www.python.org/ftp/python/3.15.1/Python-3.15.1.tar.xz",
      "sha256": "673ae7232d84c894729882c8257d300ef2d26523911bfd3917ec8ce7f526f99b",
      "size": 35789408,
      "role": "source",
      "license": "Python-2.0",
      "purpose": "The distributed interpreter"
    }
  ]
}
```

Each input has a unique `name`, a `version`, a lowercase hex `sha256`, and either `url` (a string)
or `urls` (a non-empty list of mirrors serving identical bytes). `size`, `role`, `target`,
`license`, and `purpose` are optional; repositories may add other fields. Every build repository
has a `sources.lock.json`.

`release-budgets.json`, when present, has a `targets` object keyed by target triple; each value
holds that target's size or resource limits. `bootstrap.lock.json`, when present, pins the
toolchain used to build, and its other keys belong to the repository.

The shared Python package `laputa-buildlib` (repository `laputa-systems/buildlib`, published to
the stuff PyPI registry) reads and validates these files. Python build repositories depend on it
instead of keeping their own readers.

## Releases

`.github/workflows/release.yml` publishes a release. It runs only on `workflow_dispatch` and
starts with a preflight job that rejects any ref other than the default branch.

Each product and target produces two assets:

- `<product>-<version>-<target>.tar.xz`, the archive.
- `<product>-<version>-<target>.manifest.json`, with at least `schema_version` (1), `product`,
  `version`, `target`, `source_revision` (the full commit SHA), and `sources_lock_sha256` (the
  SHA-256 of `sources.lock.json` at that commit).

A repository whose consumers need another layout publishes those assets beside the standard ones
and names the consumer in its README. python-build keeps its python-build-standalone layout
(`cpython-<version>+<date>-<target>-install_only_stripped.tar.gz`) because `uv python install`
reads it.

A `SHA256SUMS` file covers every other asset, sorted by file name, and the workflow checks it with
`sha256sum -c` before publishing.

The tag is `release-${{ github.sha }}`. The workflow refuses to run when the tag exists, creates it
at `$GITHUB_SHA` through the GitHub API, writes notes with the shared `Write release notes` step,
and publishes with:

```sh
gh release create "$RELEASE_TAG" --target "$GITHUB_SHA" --prerelease --verify-tag \
  --notes-file "$RUNNER_TEMP/release-notes.md" <assets>
```

Linux archives are built in a musl builder that passes `linux-musl-toolchain`.

Other workflows (lint, tests, qualification, benchmarks) may exist. A workflow that mirrors a build
input, such as a bootstrap toolchain, publishes outside this contract and never uses a `release-` tag. `lint.yml` runs `make lint`.
