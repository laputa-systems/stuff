# Campaign: every release archive is a .tar.xz

Goal: every release we publish, and stuff's static artifact mirror, ships archives as `.tar.xz`. A
repomod rule keeps it that way, and every consumer reads them. Owner request, 2026-11-15.

## Status

- **State:** started. Phases 1 and 2 and the mirror lane are in progress.
- **Already `.tar.xz`:** the build and toolchain repos (via buildlib) and llvm-prebuilt-musl.
- **To switch from zip:** the ish-template tool family (ish, loc, kache, lz, ctrs, soulseek-rs,
  syncthing, mactop, e, fz, fastermod, diff-pretty, srv, vault, tm, rage, zzz), gluon, gh, fd, rg,
  jaq, img, git-build and ssh-build (rawzip `make-archive`), and stuff's mirror (`<id>.zip`).
- **To switch from other tar formats:** play's Linux `.tar.gz`, img's source `.tar.gz`, and
  rust-fontconfig's `.tar.gz`.
- **Already broken:**
  - usr's `zzz` installer fetches a raw binary that zzz no longer publishes.
  - laputa's oxish recipe expects a `.tar.xz` that ssh-build no longer publishes.
- **Needs you:** approve each producer's first `.tar.xz` release and the mirror publish. These
  are remote-write publishes.

## Decisions (owner, 2026-11-15)

1. **Format:** `.tar.xz` everywhere, chosen over zip for minimal software and universality on
   our macOS and Linux targets.
   - tar is in every base image.
   - Symlinks and modes are native.
   - Solid compression suits toolchains.
   - Zip's random access only helped small tools.
2. **Scope:** every release we publish. That covers tool repos, build and toolchain repos, bctl,
   play, xsh's core archive, our forks' release configs, and stuff's static artifact mirror.
3. **Exempt by name:** formats another tool requires. Each exemption sits in fleet policy with its
   reason.
   - python-build's `cpython-…-install_only_stripped.tar.gz` (the `uv python install` layout).
   - npm-pack `.tgz` (pi-build's agent-intercom companions).
   - Wheels.

   Registry formats (`.crate`, npm, wheels, OCI layers) and non-archives (raw binaries, `.dmg`,
   manifests, `SHA256SUMS`) are not release archives.
4. **Archives are deterministic:** sorted entries, fixed mtimes, uid and gid 0. Consumers reject
   symlinks and paths that escape the extraction root.

## Sequence

Consumers accept `.tar.xz` before any producer publishes it, so no user of a current release
breaks.

1. **Rule (stuff).** `release-archive-format` reports every release archive that is not
   `.tar.xz`, apart from the exemptions. `binary-release-standard` requires `.tar.xz` for tools,
   and a fixer rewrites the ish-template packaging step. `build-release-standard` keeps `.tar.xz`.
2. **Consumers accept `.tar.xz`** alongside today's zip.
   - usr's installer: the ish family, img and lz, zzz, kache, and the bundles.
   - Repos that fetch tool zips: ssh-build's `fetch-ish`, play's `fetch-gluon`, img's kache,
     mactop's swift-bylaws, and the laputa recipes.
   - Symlink-escape checks in both extractors.
3. **Mirror (stuff).** `stuff publish mirror` writes `<id>.tar.xz`. The usr mirror consumer and its
   pins move after the owner approves a publish.
4. **Producers switch.** Run `repomod fix` with the packaging fixer for the template family, and
   change the rest by hand. Each release needs the owner's approval.
5. **Consumers drop zip** once each producer's `.tar.xz` release exists.

## Not in scope

- `joshuarli/mold` and `joshuarli/ghostty`, which are `IGNORE` in the catalog.
- Third-party archives we only consume.
