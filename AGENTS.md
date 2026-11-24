# AGENTS.md

stuff holds the infrastructure for every repository its owner maintains:

- **Registries** (`crates/`, `deploy/`): four static registries share one Rust serving platform
  and the `stuff` publisher. The Python 3.11 standard-library `mycrates` package remains an
  archive/maintenance tool and publication parity oracle.
- **Fleet** (`repomod/`, `fleet/`, `docker/musl/`): repomod, a Python 3.15 tool, manages the
  repositories in `fleet/catalog.toml`. It syncs checkouts, checks policy and opens pull requests
  for fixes, releases binaries, and keeps the dependency inventory in `fleet/dependencies/` with its
  dashboard. `fleet/policy/` holds its policy data and `docker/musl/` the fleet's musl toolchain
  image.
- **OpenOrange** (`deploy/openorange/`): the shared host runtime, ingress, storage, and recovery tools.

## Commands and verification

Build, test, lint, fleet, publishing, OCI and Worker commands are in
[development](docs/development.md#command-reference); CI and verification coverage are in
[development](docs/development.md#verification-and-ci). Fleet operating commands are in
[fleet](docs/fleet.md). Run everything from the repository root.

## Topic map

| Topic | Owner |
| --- | --- |
| Publishing, credentials, state, deployment, recovery | [docs/PUBLISHING.md](docs/PUBLISHING.md); native implementation in `crates/stuff/src/publish/` |
| Cargo archive and Python oracle | [crates/mycrates/AGENTS.md](crates/mycrates/AGENTS.md) |
| Cargo formats and shared catalog schema | [docs/mycrates-contracts.md](docs/mycrates-contracts.md) |
| Legacy Cargo state migration | [docs/mycrates-migration.md](docs/mycrates-migration.md) |
| npm inventory and publication | [crates/mynpm/README.md](crates/mynpm/README.md) |
| Wheel acquisition, validation, and the Python execution boundary | [crates/mypypi/README.md](crates/mypypi/README.md) |
| OCI protocol and storage | [docs/oci-design.md](docs/oci-design.md); [protocol API](crates/stuff-oci/README.md) |
| OCI CLI, server, writer, benchmarks | [crates/myoci/README.md](crates/myoci/README.md) |
| OCI benchmark results and the direct blob origin (A11) | [docs/oci-benchmarks.md](docs/oci-benchmarks.md), [docs/oci-a11.md](docs/oci-a11.md) |
| Worker host, WASM build, runtime tests | [crates/stuff-worker/README.md](crates/stuff-worker/README.md) |
| Registry read failover, replica sync, what does not fail over | [docs/registry-failover.md](docs/registry-failover.md) |
| OpenOrange host stack, ingress, deployment, and recovery | [docs/openorange-runtime.md](docs/openorange-runtime.md) |
| OpenOrange runtime releases and rollouts | [docs/openorange-releases.md](docs/openorange-releases.md), [docs/openorange-rollouts.md](docs/openorange-rollouts.md) |
| Shared storage and generation activation | `crates/stuff-store/src/`; `Site` is used by myoci, while mynpm/mypypi activate their own sites |
| Shared HTTP policy and native adapter | `crates/stuff-http/src/`, `crates/stuff-server/src/` |
| Catalog rendering and search | `crates/stuff-catalog/src/`, `crates/stuff-catalog/web/` |
| URL and Cargo shard parsing | `crates/stuff-url/src/lib.rs`, `crates/stuff-cargo-shard/src/lib.rs` |
| Maintenance helpers and offline fakes | `deploy/`; commands in [development](docs/development.md#command-reference) |
| Using repomod: catalog, sync, lint, fix, release | [docs/fleet.md](docs/fleet.md) |
| repomod architecture, sync, repair, and state ownership | [docs/fleet-design.md](docs/fleet-design.md) |
| Catalog tags and visibility | [docs/tagging.md](docs/tagging.md) |
| Rules, fixers, and musl publication | [docs/policy-development.md](docs/policy-development.md) |
| Repomod mutation testing | [docs/repomod-mutation.md](docs/repomod-mutation.md) |
| Owned-tool ownership lookup and help contract | [docs/fleet.md#owned-tools](docs/fleet.md#owned-tools); `fleet/policy/owned-tools.toml` |
| Build repositories: make targets, pinned inputs, releases | [docs/build-repos.md](docs/build-repos.md) |
| Shared build tooling, buildlib dispositions and Linux capsule adoption | [docs/build-repos.md#shared-build-tooling-across-the-fleet](docs/build-repos.md#shared-build-tooling-across-the-fleet); `fleet/policy/buildlib.toml` |
| Shared standard for Zig repositories | [docs/zig-standard.md](docs/zig-standard.md) |
| Dependency policy checks and the registry policy the fleet follows | [docs/audit.md](docs/audit.md); `fleet/registries.toml` |
| Tracked dependency model and extraction | [docs/dependency-inventory.md](docs/dependency-inventory.md) |
| Dependency dashboard, owners, mirror coverage, browser checks, benchmarks | [docs/dependency-dashboard.md](docs/dependency-dashboard.md) |
| Repository layout used by repomod | `repomod/paths.py` |
| Checkout removal contract | [docs/fleet-design.md#checkout-removal](docs/fleet-design.md#checkout-removal) |
| Deferred fixes and owner decisions | [TODO.md](TODO.md) |

The deslop campaign closed on 2026-11-21; its lasting rules are the fleet quality standard in
[fleet](docs/fleet.md#quality-standard) and the build-repo contracts in
[build-repos](docs/build-repos.md). Roadmap: [docs/roadmap.md](docs/roadmap.md) holds all current
and future work; its Status is the resume point.

## Invariants

- `stuff publish cargo|npm|pypi|oci|mirror` is the only publication entry point; the Python Cargo writer is a parity oracle. One registry's publication never rebuilds another.
- Keep package semantics per ecosystem; share serving/storage/generation code without a universal `Package` abstraction. Preserve published generation readability.
- First-party Rust forbids unsafe code; Python mycrates uses only the standard library. Keep npm lifecycle scripts disabled during acquisition and retain native-target execution checks for wheels.
- The registries must build when their own package registries are unavailable: Cargo, npm and PyPI deps of registry crates resolve upstream, except `@laputa-systems/ui-dashboard`, which is installed from stuff at a pinned version with its stylesheets committed.
- repomod reads the catalogs the registries publish (`<origin>/current/catalog.json`); change the catalog schema and its reader together. Run fleet commands from the canonical checkout's main worktree and keep it clean; `fix` publishes only from an unchanged checkout.
- Stuff files use Apache-2.0; imported crates retain their license fields.
- The fleet uses its own tools. Where an owned producer in `fleet/policy/owned-tools.toml` supplies a tool, consumers take that producer's release instead of the upstream package, and a gap in it is fixed in its repository rather than worked around with the upstream build. See [owned tools first](docs/fleet.md#owned-tools-first).

## Fleet constraints

Read the rules in [fleet](docs/fleet.md) and [fleet design](docs/fleet-design.md) before fleet work.
In short: run `uv run repomod sync` first; treat `fleet/catalog.toml` and canonical checkouts as
user data; never run `fix` against the live catalog while changing repomod; keep Git, GitHub,
sync and policy checks in their owning modules under `repomod/`; keep rules read-only and fixers
as validated file plans; keep pull-request publication in the fix flow.
