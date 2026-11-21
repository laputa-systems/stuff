# Fleet dependency friction

This campaign removes the dependency failures that cost the fleet the most during the deslop
winddown on 2026-11-21. The owner asked for all of them; this page sets the order, the ruling
for each item, and what counts as done.

## Status

Active 2026-11-21. Resume by reading this section.

- F1: done 2026-11-21. The failover Worker routes all eight registry hostnames and
  `oo-replica-sync` keeps the R2 replica current; the origin-down drill passed its acceptance
  ([deploy](../registry-failover.md#deploy)).
- F2: usr#49 merged: kache and clang are optional under usr's cargo config and glibc hosts get
  CPython through uv. The clean-clone capsule rerun waits on a kache release that contains
  kache#104; kache and usr now belong to other sessions, so that release is theirs.
- F3: done 2026-11-21 (STUF-101 closed). Eight consumers are enrolled in `buildlib-usage` on
  buildlib 0.2.0, the other 58 active entries have reviewed exemptions, and each shim consumer
  records both cold Linux capsule paths ([scorecard](deslop-scorecard.md#buildlib-adoption-lane)).
- F4: one pair carried through on 2026-11-21. laputa-ptytest 0.5.0 (crates.io) reached tm's
  `Cargo.lock` through `uv run repomod sync`, then
  `uv run repomod fix --repo laputa-systems/tm --rule audit-upgrades --no-mirror`, then
  `uv run repomod merge --repo laputa-systems/tm`. That produced tm#47 (merged as `b2fdb027`, CI
  green on Linux and macOS). `--no-mirror` respected the Cargo publish hold; lint reports only
  versions the configured registry already serves. Two gaps outside the inventory showed up:
  - the fixer upgrades every outdated direct dependency, so the hand-off also carried
    rustybench 0.5 → 0.6 and cannot be limited to the released crate;
  - tm requires no status checks, so `fix` skipped auto-merge and the merge was a separate step.

  Still outstanding from the inventory: gap 1 (no trigger) and the remaining ptytest consumers
  (fz, xsh, e and defuddle-rs on `0.4`, soulseek-rs on `0.3`, lz's git pin).
- F5 and F6: not started.

## Items

| ID | Friction | Ruling | Done when |
| --- | --- | --- | --- |
| F1 | One host serves every registry. On 2026-11-21 Lisa's Engine overload (STUF-102, owned by the stats session) turned crates, npm, pypi and the mirror into HTTP 500, then 530. | Owner chose a second origin first: serve each registry's current R2 generation from a static origin and fail over to it when the Engine is down. Upstream fallback comes later only where it adds value. | With the Engine stopped, `cargo fetch --locked`, `pnpm install --frozen-lockfile` and `uv sync --frozen` succeed against a tansu, a pnpm and a uv consumer, and usr's mirror downloads verify. |
| F2 | Owner tools are hard requirements: the global cargo config forces `kache` and `kache clang`; python-build and the FFmpeg runtime are musl-only. | Keep them the default where installed; make cargo work without them, and give glibc hosts a verified CPython. | A fresh `ubuntu:24.04` with only rustup builds a crate under usr's linked config with and without kache; `sh sync` gives a working `python3` there. |
| F3 | Toolchain pins and bootstrap are repeated per repository. | STUF-101's buildlib lane, BLD-0 to BLD-5 ([policy](../build-repos.md#shared-build-tooling-across-the-fleet)), including both Linux capsule interpreter paths. | BLD-5's close criteria. |
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
