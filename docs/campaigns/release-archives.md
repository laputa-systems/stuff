# Campaign: every release archive is a .tar.xz

Goal: every release we publish, and stuff's static artifact mirror, ships archives as `.tar.xz`. A
repomod rule keeps it that way, and every consumer reads them. Owner request, 2026-11-15.

## Status

- **State:** phases 1 to 4 are done for every in-scope producer except the four held items below.
  Phase 5 (consumers drop zip) has not started.
- **Rule:** `release-archive-format` and the `binary-release-standard` packaging fixer
  (stuff#17, fixer repaired in stuff#21) are live.
- **Consumers:** usr's installer reads `.tar.xz` for the ish family, img, lz, kache, gluon, and
  Player (usr#38, usr#40) and for the mirror (usr#41).
- **Released as `.tar.xz` (2026-11-15):**
  - By hand: lz, git-build, gh, mactop, syncthing, img, ssh-build, gluon, fd, rg, jaq, rage, and
    soulseek-rs.
  - By the fixer: ish, kache, loc, diff-pretty, e, srv, tm, and vault.
  - Each release was checked by downloading one archive and its `SHA256SUMS`.
- **Mirror:** generation `591a1e…` serves `<id>.tar.xz`. `stuff doctor --registry mirror` passes
  after stuff#24. Large uploads needed stuff#23's size-scaled request deadline.
- **Release fixes found on the way:**
  - The five forks (fd, rg, jaq, rage, soulseek-rs) build Linux releases in the llvm musl
    toolchain image. Their bare-runner builds linked rust-std's GCC-built CRT objects, which
    `verify-static-elf` rejects.
  - gluon pins the nightly-2026-11-09 image (gluon#12).
  - The `gha-ubuntu` rule reports ARM runners on `linux/amd64` jobs (stuff#22). The earlier
    runner fixer had put seven template repos' x86_64 builds on ARM.
- **Held:**
  - ctrs: its canonical checkout has 20 unpushed commits.
  - fastermod: its canonical checkout has uncommitted work.
  - fz: an earlier repomod fix PR (fz#27) is still open. All three also need the gha-ubuntu fix.
  - xsh: its core archive is in scope, but `binary-release-standard` also wants its tag,
    preflight, and target rewrites. The archive change waits for that work.
- **Known gaps:**
  - Template archives store binaries as mode `0644`. The zips did too, and usr's installer sets
    the execute bit, but a hand-extracted binary is not executable.
  - fd, rg, and jaq publish no `SHA256SUMS`.
- **Phase 5 next:** pinned consumers move at their pin bumps (ssh-build's `ish.lock.json`, img's
  kache, play's `fetch-gluon`, the laputa recipes). Then usr drops its zip fallback, except
  for zzz.

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
5. **zzz is out** (owner, 2026-11-15): it keeps its zip archives. The catalog ignores
   `release-archive-format` and `binary-release-standard` for it.

## Sequence

Consumers accept `.tar.xz` before any producer publishes it, so no user of a current release
breaks.

1. **Rule (stuff).** `release-archive-format` reports every release archive that is not
   `.tar.xz`, apart from the exemptions. `binary-release-standard` requires `.tar.xz` for tools,
   and a fixer rewrites the ish-template packaging step. `build-release-standard` keeps `.tar.xz`.
2. **Consumers accept `.tar.xz`** alongside today's zip.
   - usr's installer: the ish family, img and lz, kache, gluon, Player, and the bundles.
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
- `laputa-systems/zzz` (decision 5).
- Third-party archives we only consume.
