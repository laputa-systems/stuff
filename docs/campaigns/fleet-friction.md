# Fleet dependency friction

This campaign removes the dependency failures that cost the fleet the most during the deslop
winddown on 2026-11-21. The owner asked for all of them; this page sets the order, the ruling
for each item, and what counts as done.

## Status

Paused 2026-11-21 so deslop can resume on a cloud Linux host. Resume by reading this section.

- F1: the failover Worker, replica sync and runbook merged in stuff#181 ([registry failover](../registry-failover.md)).
  Not deployed. Lisa holds the R2 credentials in `/etc/openorange/stuff-replica/r2.env`; the
  seed had copied stuff-oci and stuff-mypypi. Next: finish the seed, install `oo-replica-sync`,
  route one hostname, drill with the stats session, then route the rest. Needs the Mac or Lisa access.
- F2: usr#49 makes kache and clang optional and adds the uv CPython fallback. Next: release
  kache with kache#104, then rerun a cold `ubuntu:24.04` capsule and check `git status` is clean.
- F3: buildlib#31 fixes root-run tests and the Ubuntu 26.04 cache lock. Next: cut buildlib 0.2.0
  from tip and move the six consumers and ctrs's vendored bootstrap to it (BLD-1 onward).
- F4 to F6: not started; F4's inventory is below.

## Items

| ID | Friction | Ruling | Done when |
| --- | --- | --- | --- |
| F1 | One host serves every registry. On 2026-11-21 Lisa's Engine overload (STUF-102, owned by the stats session) turned crates, npm, pypi and the mirror into HTTP 500, then 530. | Owner chose a second origin first: serve each registry's current R2 generation from a static origin and fail over to it when the Engine is down. Upstream fallback comes later only where it adds value. | With the Engine stopped, `cargo fetch --locked`, `pnpm install --frozen-lockfile` and `uv sync --frozen` succeed against a tansu, a pnpm and a uv consumer, and usr's mirror downloads verify. |
| F2 | Owner tools are hard requirements: the global cargo config forces `kache` and `kache clang`; python-build and the FFmpeg runtime are musl-only. | Keep them the default where installed; make cargo work without them, and give glibc hosts a verified CPython. | A fresh `ubuntu:24.04` with only rustup builds a crate under usr's linked config with and without kache; `sh sync` gives a working `python3` there. |
| F3 | Toolchain pins and bootstrap are repeated per repository. | STUF-101's [buildlib plan](deslop-buildlib.md), BLD-0 to BLD-5, including both Linux capsule interpreter paths. | BLD-5's close criteria. |
| F4 | Cross-repository releases are manual hops (ptytest to ish, smolith's `h12tiny` to stuff, tansu's mirror upgrades). | Inventory the hops first; automate the hand-off in repomod's release and mirror flows. | A dependency release reaches its consumers' lockfiles through one documented command. |
| F5 | macOS host drift: Homebrew encoder upgrades break fixture hashes (play PLAY-55); `cargo-llvm-cov` and `cargo-mutants` are missing on the Darwin lane host. | Install the measurement tools through usr's sync; pin or decouple brew-dependent checks per repository. | Deslop component slices on the Mac record coverage and mutation numbers; PLAY-55 is closed. |
| F6 | CI runner economics: larger runner labels queue for minutes, and private repositories are refused for billing. | Move jobs that do not need larger runners to standard labels. Billing is the owner's. | Each workflow's runner choice is justified in the repository, and queued time on standard jobs drops. |

## F4 inventory, 2026-11-21

Eleven first-party producers publish to stuff or crates.io (smolith, ptytest, rustybench, hi-lite,
the deser/rg/rustix/rage forks, stats, defuddle-rs, laputa-ui-dashboard, buildlib, pytest-parallel).
Every hand-off from a release to its consumers is manual. The only partial automation is
`repomod fix --rule audit-upgrades`: for crates.io releases it mirrors and bumps caret pins in
public, non-fork consumers, but nothing runs it when a release lands. The gaps, in the order to
close them:

1. No trigger: a release never starts the consumer update, and producer scripts do not push.
2. Own-registry publishes do not clear audit-upgrades' 24-hour latest-version cache.
3. `=`/`==` and git pins are never fixable (xsh, laputa, e, tinyland, img, defuddle-rs, lz, ctrs,
   and all six buildlib consumers).
4. The fixer cannot write `sources.lock.json`, vendored copies (stats-producer in tansu, discover
   and stuff) or derived assets (stuff's `make catalog-css`).
5. deser, rg, rustix, defuddle-rs, ui-dashboard, buildlib and stats-producer have no bump or tag
   tooling; the published stats-producer 0.2.0 is behind its source.
6. Private repositories (bctl, discover, toolbox) are outside audit-upgrades and the mirror.

## Order

F1 first: it has the largest blast radius. F2 and F3 run alongside it, because they touch usr and
buildlib, not the serving path. F4 to F6 follow once F1's design lands.

## Out of scope

The Engine retry storm itself (STUF-102) stays with the stats session. Private repositories'
Actions billing is the owner's.
