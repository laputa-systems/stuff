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

## Commands

Run everything from the repository root.

- Fresh Linux host: `scripts/setup-dev` installs the pinned toolchains; see [docs/development.md](docs/development.md).
- Build/test/lint: `make build`, `make test` (Rust workspace, mycrates, and repomod), `make lint` (clippy, ruff, ty).
- Rust toolchain: `rust-toolchain.toml`; Worker package/tool pins: `crates/stuff-worker/package.json` and `Cargo.lock`.
- Python oracle: `make test-mycrates` (needs Cargo for the native publication proof).
- repomod: `uv sync`, then `uv run repomod --help`; `make repomod-test`, `make repomod-lint`. Set `TMPDIR` to `.work/tmp` for commands that create scratch data.
- Fleet dashboard: `make deps` syncs the checkouts, re-snapshots the tracked inventory
  (committing any changes under `fleet/dependencies/v1/` and `fleet/loc/v1/`), renders, and serves it; `make bench` measures the render.
  `make preview` serves the dashboard from its canonical preview dataset, which the golden test in
  `tests/repomod/test_dashboard_preview.py` also renders; see [the dashboard doc](docs/dependency-dashboard.md).
- Search: `make test-search`; after changing `crates/stuff-catalog/web/`, run `make search-bundle` and commit `assets/search.js` (install Worker dependencies first).
- TypeScript browser assets: edit the `.ts` sources (`repomod/dependencies/assets/*.ts`, `deploy/openorange/rivet/*.ts`); run `make ts-assets` and commit the sources and compiled `.js` artifacts together.
- Catalog page styles: after bumping `@laputa-systems/ui-dashboard` in `crates/stuff-worker/package.json`, run `make catalog-css` and commit `crates/stuff-catalog/assets/ui-dashboard/`. App styles live in `crates/stuff-catalog/assets/catalog.css`. Both renderers (`stuff-catalog` and the mycrates oracle) embed them, so regenerate the mycrates golden generation with them.
- Worker: `make worker-test`, `make worker-check`; build instructions are in its README below.
- Offline maintenance: `make test-r2`, `make test-publish-lock`; `make test-r2-live` accesses real R2 and is opt-in.
- Ecosystem integration: `deploy/ecosystem-smoke.sh` needs the pinned package managers, CPython, native repair tools, and network. Use `TMPDIR="$PWD/.work/tmp"` for campaign commands.
- OCI checks: `make test-oci-conformance`, `make test-oci-conformance-push`, `make test-oci-pull`, `make test-oci-push`, `make test-oci-publish`, `make oci-bench`.

## Verification

- Costs on an M-series Mac, warm: `make test` 163s, `make repomod-test` 60s (1,348 passed, 3 skipped: two opt-in live-fleet tests and the `PINACT_LAUNCHER` integration), `make repomod-lint` under 1s, `make lint` 19s. `make test`'s macOS sandbox test needs a real Python first on `PATH`, not Apple's `/usr/bin/python3` shim. PR CI runs `make test` (`.github/workflows/ci.yml:45`).
- `stuff` CLI (`publish`, `doctor`, republish, rollback), its exit codes and output: `crates/stuff/tests/cli.rs`, `publish_output.rs`, `publish_retry.rs`, `mirror_publish.rs`.
- Published registry formats: Cargo index and archives in `crates/stuff/tests/cargo_*.rs` and the mycrates golden generation; npm `npm_publish.rs` and `crates/mynpm/tests/`; PyPI `pypi_*.rs` and `crates/mypypi/tests/`; OCI `oci_publish.rs`, `crates/myoci/tests/`, and `make test-oci-conformance`.
- HTTP serving (routes, caching, conditional requests, MIME): `crates/stuff-server/tests/*_compat.rs` and `crates/stuff-http` unit tests. Worker runtime: `crates/stuff-worker/test/`.
- `<origin>/current/catalog.json`, read by repomod: `crates/stuff-catalog` tests and `tests/repomod/test_deps_world.py`.
- R2 storage and generation activation: `crates/stuff/tests/r2_*.rs` against `fake_s3.rs`; live R2 is opt-in (`make test-r2-live`).
- repomod CLI (`sync`, `lint`, `fix`, `push`, `merge`, `release`, `deps`, `topics`): `tests/repomod/` against local Git repositories and fake GitHub responses. File formats it owns: `fleet/catalog.toml` (`test_catalog.py`), `fleet/dependencies/v1/` and `fleet/loc/v1/` (`test_deps_snapshot.py`, `test_loc_snapshot.py`).
- Performance workloads: `make oci-bench` (OCI serving) and `make bench` (dashboard render). Each gates only changes on its own path.
- Vendored trees: `crates/stuff-worker/vendor/stats-producer/` is pristine (`upstream.json` records joshuarli/stats `bdf65f7`, `packages/producer`); `crates/stuff-catalog/web/minisearch/` is modified (`NOTICE.md` records its upstream).
- Components: `crates/stuff` (30k), `crates/mynpm`, `crates/mypypi`, `crates/myoci`, the remaining crates, `repomod/dependencies`, `repomod/rules`, `repomod/` top-level, the Worker, and `deploy/`. Deslop works one component per slice; the calibration component is `repomod/`.

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
| Shared storage and generation activation | `crates/stuff-store/src/`; `Site` is used by myoci, while mynpm/mypypi activate their own sites |
| Shared HTTP policy and native adapter | `crates/stuff-http/src/`, `crates/stuff-server/src/` |
| Catalog rendering and search | `crates/stuff-catalog/src/`, `crates/stuff-catalog/web/` |
| URL and Cargo shard parsing | `crates/stuff-url/src/lib.rs`, `crates/stuff-cargo-shard/src/lib.rs` |
| Maintenance helpers and offline fakes | `deploy/`; commands in `Makefile` |
| Using repomod: catalog, sync, lint, fix, release | [docs/fleet.md](docs/fleet.md) |
| repomod architecture, sync, repair, and state ownership | [docs/fleet-design.md](docs/fleet-design.md) |
| Repomod calibration findings and reproduction | [docs/deslop-repomod-diagnose.md](docs/deslop-repomod-diagnose.md) |
| Catalog tags and visibility | [docs/tagging.md](docs/tagging.md) |
| Rules, fixers, and musl publication | [docs/policy-development.md](docs/policy-development.md) |
| Workflow matrix include proof | [docs/deslop-workflow-matrix.md](docs/deslop-workflow-matrix.md) |
| Owned-tool ownership lookup and help contract | [docs/fleet.md#owned-tools](docs/fleet.md#owned-tools); `fleet/policy/owned-tools.toml` |
| Build repositories: make targets, pinned inputs, releases | [docs/build-repos.md](docs/build-repos.md) |
| Shared build tooling, buildlib dispositions and Linux capsule adoption | [docs/build-repos.md](docs/build-repos.md#shared-build-tooling-across-the-fleet); `fleet/policy/buildlib.toml` |
| Dependency policy checks and the registry policy the fleet follows | [docs/audit.md](docs/audit.md); `fleet/registries.toml` |
| Tracked dependency model and extraction | [docs/dependency-inventory.md](docs/dependency-inventory.md) |
| Enrichment type-boundary proof | [docs/deslop-enrichment-types.md](docs/deslop-enrichment-types.md) |
| Dependency dashboard, owners, mirror coverage, browser checks, benchmarks | [docs/dependency-dashboard.md](docs/dependency-dashboard.md) |
| Repository layout used by repomod | `repomod/paths.py` |
| Checkout removal contract | [docs/fleet-design.md#checkout-removal](docs/fleet-design.md#checkout-removal) |
| Campaign records | [docs/campaigns/](docs/campaigns/) |
| Retired repomod repair lanes | [docs/deslop-fix-cleanup.md](docs/deslop-fix-cleanup.md) |
| Deferred fixes | [TODO.md](TODO.md) |

## Invariants

- `stuff publish cargo|npm|pypi|oci|mirror` is the publication entry point; the Python Cargo writer stays only as a parity oracle.
- One registry's publication never rebuilds another registry's output.
- Keep package semantics per ecosystem; share serving/storage/generation code without a universal `Package` abstraction.
- First-party Rust forbids unsafe code; Python mycrates uses only the standard library.
- Keep npm lifecycle scripts disabled during acquisition and validation; retain native-target execution checks for wheels.
- Preserve published generation readability; format contracts belong in the owning registry docs.
- Keep fixtures while parity consumers use them, including the executable examples in `crates/mycrates/README.md`.
- stuff depends on the published `h12tiny-*` crates from upstream; change upstream (laputa-systems/smolith) and publish before stuff needs a newer h12tiny.
- The registries must stay buildable when their own package registries are unavailable: Cargo, npm,
  and PyPI dependencies of the registry crates resolve from upstream, not from stuff. The catalog
  exempts stuff from repomod's `registry-sources` rule for this reason. The one exception is
  `@laputa-systems/ui-dashboard`, which the catalog pages use and which is published only on stuff:
  install it from stuff at a pinned version, and commit the stylesheets copied from it so a Rust
  build needs neither Node nor the npm registry.
- repomod manages stuff like any other repository. Run fleet commands from the canonical checkout's
  main worktree (`~/repos/laputa-systems/stuff`), which `repomod sync` fast-forwards, and develop in
  worktrees under its `.work/wt/`. `fix` publishes only from an unchanged canonical checkout, so keep
  the main worktree clean. To test a repomod change, run `uv run repomod` from the worktree: paths
  resolve from the checkout you run, so it reads that worktree's fleet data.
- repomod reads the catalogs the registries publish (`<origin>/current/catalog.json`); change the
  catalog schema and its repomod reader together.
- Stuff files use Apache-2.0; imported crates retain their license fields.

## Fleet constraints

- Run `uv run repomod sync` before fleet work, so canonical checkouts reflect their remotes.
- `fleet/catalog.toml` is curated user data. Read it before catalog work and preserve its comments and repository selection.
- Do not run `fix` against the live catalog while changing repomod. Tests use local Git repositories and fake GitHub responses; use copied catalogs for mutation tests.
- Canonical checkouts are user data. Never reset, stash, clean, switch, or discard changes in them.
- Sync may fetch and only fast-forward clean checkouts on their default branch. Fixers use detached worktrees and publish only from an unchanged canonical checkout.
- Remote-write commands are `topics apply`, `push`, `fix`, `merge`, and `release`; `fix` pushes branches and opens pull requests. `pins refresh` writes local approved pins.
- Keep Git subprocesses, GitHub operations, synchronization, and policy checks in their owning modules under `repomod/`. Resolve repository files through `repomod/paths.py`.
- Keep rules read-only and fixers as explicit, validated file plans. Do not add databases, background workers, or generic workflow frameworks.
- Keep pull-request publication in the fix flow. Do not add rollout tracking, patch storage, or per-fixer clone directories.
