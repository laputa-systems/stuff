# Resuming deslop on a cloud Linux host

This page is for an agent resuming the [deslop campaign](deslop.md) on a fresh Linux host,
such as a cloud AI environment, instead of the owner's Mac. Such a host sees only public
repositories, so the campaign continues there with a narrower scope. The campaign's **Status**
remains the handoff; this page covers what changes on Linux.

## Before leaving the Mac

A cloud host sees only what is pushed. Every parked branch named in **Status** was pushed on
2026-11-21. Before resuming elsewhere, push any branch parked after that, or record it as Mac-only in **Status**. Check with:

```sh
git -C <checkout> ls-remote --exit-code --heads origin <branch>
```

## Host setup

Verified on `ubuntu:24.04` arm64 on 2026-11-21. Run as a user whose home holds the layout
the fleet expects: `~/usr`, `~/repos/<name>` for `joshuarli` repositories, and
`~/repos/laputa-systems/<name>` for `laputa-systems` repositories.

1. System packages: `apt-get install -y git ca-certificates curl xz-utils python3 libatomic1 clang build-essential`.
   usr's sync has no Python bootstrap on glibc Linux, Node needs `libatomic1`, and the linked
   cargo config compiles C through `kache clang` ([usr README](https://github.com/joshuarli/usr#readme)).
2. Install rustup before syncing. The linked `~/.cargo/config.toml` sets `rustc-wrapper = "kache"`,
   and sync installs kache only when rustup is already present. Without kache, cargo fails in
   every Rust repository.
3. `git clone https://github.com/joshuarli/usr ~/usr && sh ~/usr/sync`. This links the skills
   (`deslop`, `orchestrate`, `campaign-winddown`) and installs `todo`, `worktree-retire`,
   `mdtool`, `fastermod`, `fd`, `rg`, kache and Node. Without a musl loader it leaves out its
   musl-linked `python3`, `ffmpeg` and `player` (python-build#19); the campaign needs none of them.
   Install `jaq` separately; sync's Linux defaults omit it.
4. `git clone https://github.com/laputa-systems/stuff ~/repos/laputa-systems/stuff`, then
   `scripts/setup-dev` there (see [development](../development.md)). repomod's F2/F3 checks run from this checkout.
5. `gh auth login` with a token that can push branches and open pull requests in the public
   `joshuarli` and `laputa-systems` repositories.

## Scope on a public-only host

- **Out of scope:** the private catalog repositories `joshuarli/bctl`, `discover`,
  `niceforge` and `toolbox`. That excludes discover's red lint and its DSLP-6 branches. Toolbox
  is also owned by another session.
- **`repomod sync`** walks the whole catalog and has no repository filter. Clone the repositories a
  slice needs with `gh repo clone` into the layout above instead.
- **Mac-only work:** findings whose reproduction depends on macOS (APFS names, the 104-byte
  `sun_path`, `/dev/fd` as devfs, macOS `poll`) cannot be reproduced on Linux. Leave them for the Mac.
  On Linux, the socket-path artifacts that blocked srv, soulseek-rs and oxish check-ups do not
  occur (`sun_path` is 108 bytes), so rerun those check-ups there.
- **Linux-favoured work:** coverage and mutation tools that Darwin slices recorded under Needs
  environment (`cargo llvm-cov`, `cargo mutants`) run on Linux. Install them with
  `cargo install --locked cargo-llvm-cov cargo-mutants`. img DSLP-4 and the kache
  components are the main beneficiaries. tinyland's seatd fix and crabtables' hosted-kernel item are also Linux work. A privileged container may still lack the kernel features crabtables needs.

## The buildlib adoption lane

The queued [buildlib lane](deslop-buildlib.md) (STUF-101) needs cold Linux capsules for each
adopted bootstrap: `ubuntu:24.04` for the uv fallback, and Debian 13 or Ubuntu 26.04 with musl
for python-build. A cloud host runs them only with a Docker daemon that allows `--privileged`.
Its native macOS checks still need the Mac.

## Delegation

The Pi bridge stays the default on the Mac. Its providers need credentials a cloud host does
not have, so set `USR_DELEGATION=native` in the cloud environment. usr's startup hook then
tells the session to use the tier-matched native subagents in `orchestrate`, with the same brief,
worktree, scope check and independent review. Never wrap builds in `cpu-guard`.
