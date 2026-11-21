# Fleet dependency friction

This campaign removes the dependency failures that cost the fleet the most during the deslop
winddown on 2026-11-21. The owner asked for all of them; this page sets the order, the ruling
for each item, and what counts as done.

## Status

Started 2026-11-21. F1 design in progress; F2 and F3 ready. Resume by reading this section and
each item's next step.

## Items

| ID | Friction | Ruling | Done when |
| --- | --- | --- | --- |
| F1 | One host serves every registry. On 2026-11-21 Lisa's Engine overload (STUF-102, owned by the stats session) turned crates, npm, pypi and the mirror into HTTP 500, then 530. | Owner chose a second origin first: serve each registry's current R2 generation from a static origin and fail over to it when the Engine is down. Upstream fallback comes later only where it adds value. | With the Engine stopped, `cargo fetch --locked`, `pnpm install --frozen-lockfile` and `uv sync --frozen` succeed against a tansu, a pnpm and a uv consumer, and usr's mirror downloads verify. |
| F2 | Owner tools are hard requirements: the global cargo config forces `kache` and `kache clang`; python-build and the FFmpeg runtime are musl-only. | Keep them the default where installed; make cargo work without them, and give glibc hosts a verified CPython. | A fresh `ubuntu:24.04` with only rustup builds a crate under usr's linked config with and without kache; `sh sync` gives a working `python3` there. |
| F3 | Toolchain pins and bootstrap are repeated per repository. | STUF-101's [buildlib plan](deslop-buildlib.md), BLD-0 to BLD-5, including both Linux capsule interpreter paths. | BLD-5's close criteria. |
| F4 | Cross-repository releases are manual hops (ptytest to ish, smolith's `h12tiny` to stuff, tansu's mirror upgrades). | Inventory the hops first; automate the hand-off in repomod's release and mirror flows. | A dependency release reaches its consumers' lockfiles through one documented command. |
| F5 | macOS host drift: Homebrew encoder upgrades break fixture hashes (play PLAY-55); `cargo-llvm-cov` and `cargo-mutants` are missing on the Darwin lane host. | Install the measurement tools through usr's sync; pin or decouple brew-dependent checks per repository. | Deslop component slices on the Mac record coverage and mutation numbers; PLAY-55 is closed. |
| F6 | CI runner economics: larger runner labels queue for minutes, and private repositories are refused for billing. | Move jobs that do not need larger runners to standard labels. Billing is the owner's. | Each workflow's runner choice is justified in the repository, and queued time on standard jobs drops. |

## Order

F1 first: it has the largest blast radius. F2 and F3 run alongside it, because they touch usr and
buildlib, not the serving path. F4 to F6 follow once F1's design lands.

## Out of scope

The Engine retry storm itself (STUF-102) stays with the stats session. Private repositories'
Actions billing is the owner's.
