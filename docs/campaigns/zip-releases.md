# Campaign: every release archive is a zip

Goal: every release we publish ships its archives as `.zip`, a repomod rule keeps it that way, and
every consumer reads the zips. Owner request, 2026-11-15.

## Status

- **State:** started. Phases 1 and 2 are in progress.
- **Already zip:** the ish-template tool family (ish, loc, kache, lz, ctrs, soulseek-rs,
  syncthing, mactop, e, fz, fastermod, diff-pretty, srv, vault, tm, rage, zzz), gluon, gh, fd, rg,
  jaq, img binaries, git-build, and ssh-build.
- **Already broken:**
  - usr's `zzz` installer fetches a raw binary that zzz no longer publishes.
  - laputa's oxish recipe expects a `.tar.xz` that ssh-build no longer publishes.
- **Needs you:** approve each producer's first zip release, which is a remote-write publish.

## Decisions (owner, 2026-11-15)

1. **Scope:** every release we publish. That covers tool repos, the build and toolchain repos
   (buildlib, cmake-, node-, ffmpeg-, python-, chromium-, and pi-build, llvm-prebuilt-musl), bctl,
   play, xsh's core archive, and the release configuration of our forks (oxish's cargo-dist
   `unix-archive`, rust-fontconfig). Toolchain archives grow, because deflate compresses less than
   xz.
2. **Exempt by name:** formats another tool requires. Each exemption sits in fleet policy with its
   reason.
   - python-build's `cpython-…-install_only_stripped.tar.gz`, the layout `uv python install`
     reads.
   - pi-build's `agent-intercom-*.tgz`, which are npm pack tarballs.
   - pytest-parallel's `.whl`.

   Registry formats (`.crate`, npm `.tgz`, wheels, OCI layers) and non-archives (raw binaries,
   `.dmg`, manifests, `SHA256SUMS`) are not release archives.
3. **Archives keep symlinks and permissions.** git-build's rawzip-based `tools/make-archive`
   already writes symlink members and unix modes deterministically, and usr's `extract_zip`
   restores both. Producers use a writer with the same contract. Consumers must not create a link
   that escapes the extraction root.

## Sequence

Consumers accept zip before any producer publishes one, so no user of a current release breaks.

1. **Rule (stuff).** `release-archive-zip`: release workflows and packaging scripts in catalogued
   repos produce only `.zip` archives, except the policy exemptions. `build-release-standard`
   requires `.zip` instead of `.tar.xz`. `_build_repository_release` and `_NATIVE_ASSET` stop
   treating tar as a release signal. Accept: negative fixtures for each tar shape, and the live
   lint lists exactly the producers in phase 3.
2. **Consumers accept zip.**
   - usr's installer handles zip for node-build, ffmpeg-runtime, pi, helium, and bctl, fixes
     zzz, and rejects escaping symlinks.
   - The musl Dockerfiles and laputa recipes need an unzip that keeps symlinks (Info-ZIP).
3. **Producers switch.**
   - buildlib's `archive_name` and `create_archive` first, since six build repos inherit them.
   - Then llvm-prebuilt-musl, pi-build, bctl, play's Linux archive, xsh's core, chromium-build's
     helium and rust-toolchain archives, and the fork configs.
   - Each release needs the owner's approval.
4. **Consumers drop tar.** Do this once each producer's zip release exists. The policy pins move
   to the zip URLs: `fleet/policy/musl-toolchain.toml` and the build-repo locks.

## Not in scope

- `joshuarli/mold` and `joshuarli/ghostty`, which are `IGNORE` in the catalog. Their tarballs are
  consumed but not catalogued.
- Third-party tarballs we only consume (uv, Zig, binaryen).
