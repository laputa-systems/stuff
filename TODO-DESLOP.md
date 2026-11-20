Prefix: DSLP
Next: 17

Deslop campaign backlog for the stuff repository ([plan](https://github.com/laputa-systems/stuff/blob/main/docs/campaigns/deslop.md), tier D, worked by component). One agent works this file with the `deslop` skill: take the lowest-numbered open ticket whose area does not start with `Needs owner ·`, one component and one PR per step. Mutation is blocking only for a small scope the repository declares around an important contract (decision 4); broader mutation, coverage and audits are advisory. Close the ticket's remaining steps, then fill in `## Report` below.

## Report

The `repomod/` calibration component is complete: Ground, Diagnose, Types, Tests and Dead code are closed, and its P2 findings are fixed. Evidence is in [the component review](docs/deslop-repomod-diagnose.md), [Types](docs/deslop-repomod-types.md), [Tests](docs/deslop-repomod-tests.md), [Dead code](docs/deslop-repomod-dead-code.md) and [Bench](docs/deslop-repomod-bench.md). The P2 repairs merged in [#51](https://github.com/laputa-systems/stuff/pull/51) to [#54](https://github.com/laputa-systems/stuff/pull/54) and [#57](https://github.com/laputa-systems/stuff/pull/57); Dead code closed in [#98](https://github.com/laputa-systems/stuff/pull/98) and Tests on the finite inventory in [#172](https://github.com/laputa-systems/stuff/pull/172), which also deleted this file. The open repomod P3 findings live in `TODO.md` (STUF-93, STUF-94, STUF-95, STUF-96).

The other components below remain. Ground covers the whole repository (`AGENTS.md`, Verification: costs, contracts, vendored trees). Diagnose does not: `docs/deslop-repomod-diagnose.md` reviewed `repomod/` only and states that the other Stuff components were not reviewed, so each ticket starts with a bounded Diagnose of its component. No other component has a review document.

## Tickets

### DSLP-10 · P2 · Deslop crates/stuff: the publisher (about 30k lines)

- **Area:** deslop · stuff publisher
- **Where:** crates/stuff/src/ (cli.rs, doctor.rs, source.rs, publish/) and crates/stuff/tests/
- **Problem:** Steps owed: Diagnose (bounded, this component only; no review exists), then Types, Tests and Dead code, one PR each. Ground is AGENTS.md Verification. Contracts: `stuff publish cargo|npm|pypi|oci|mirror` is the only publication entry point; its exit codes and output (`tests/cli.rs`, `publish_output.rs`, `publish_retry.rs`, `mirror_publish.rs`); Cargo index and archives (`tests/cargo_*.rs`, mycrates golden generation); R2 storage and generation activation (`tests/r2_*.rs` against `fake_s3.rs`); republish and rollback (`republish.rs`, `rollback.rs`); one registry's publication never rebuilds another's (`make pipecheck`). Consumers: operators and docs/PUBLISHING.md, the Worker serving published generations, repomod reading `<origin>/current/catalog.json`, `deploy/` maintenance scripts. Slice by registry subtree under `src/publish/` so each PR stays near 20k lines.
- **Recommendation:** Tests: map each named contract to its guarding tests, add only missing behavior tests, and if a mutation lane is wanted declare a small `scope` and `critical` regex around one contract (never a whole tree); broader mutation stays advisory. Accept each slice with `make test-stuff`, `make test-r2`, `make test-publish-lock`, `make pipecheck` and `make lint`; run `make test` before the last PR. `make test-r2-live` stays opt-in. Preserve the unsafe-code ban and published generation readability.
- **Fix with:** deslop
- **Effort:** L

### DSLP-11 · P3 · Deslop crates/mynpm: npm inventory and publication

- **Area:** deslop · mynpm
- **Where:** crates/mynpm/src/ and crates/mynpm/tests/ (about 13.6k lines)
- **Problem:** Steps owed: Diagnose (bounded, this component only; no review exists), then Types, Tests and Dead code, one PR each. Ground is AGENTS.md Verification. Contracts: npm lifecycle scripts stay disabled during acquisition and validation; inventory identity and metadata-only behavior (`tests/inventory_identity.rs`, `metadata_only.rs`, `cli.rs`); npm publication through `stuff publish npm` (`crates/stuff/tests/npm_publish.rs`); serving compatibility (`crates/stuff-server/tests/npm_compat.rs`). Reference: crates/mynpm/README.md. Consumers: the stuff publisher, `deploy/ecosystem-smoke.sh` and `deploy/ingest-npm-fleet.sh`, repomod dependency enrichment.
- **Recommendation:** Tests: map each named contract to its guarding tests, add only missing behavior tests, and if a mutation lane is wanted declare a small `scope` and `critical` regex around one contract (never a whole tree); broader mutation stays advisory. Accept with `cargo test -p mynpm`, `cargo test -p stuff --test npm_publish`, `make lint`; `deploy/ecosystem-smoke.sh` needs the pinned package managers and network and is opt-in.
- **Fix with:** deslop
- **Effort:** L

### DSLP-12 · P3 · Deslop crates/mypypi: wheel acquisition and PyPI publication

- **Area:** deslop · mypypi
- **Where:** crates/mypypi/src/ and crates/mypypi/tests/ (about 11.6k lines)
- **Problem:** Steps owed: Diagnose (bounded, this component only; no review exists), then Types, Tests and Dead code, one PR each. Ground is AGENTS.md Verification. Contracts: wheel acquisition, validation and the Python execution boundary (crates/mypypi/README.md); native-target execution checks for wheels are retained; wheel tags and publication (`tests/wheel_tags.rs`, `publish.rs`, `cli.rs`, `crates/stuff/tests/pypi_*.rs`). Consumers: the stuff publisher, `deploy/test-mypypi-native.sh`, `deploy/ecosystem-smoke.sh`, repair tooling under `deploy/`.
- **Recommendation:** Tests: map each named contract to its guarding tests, add only missing behavior tests, and if a mutation lane is wanted declare a small `scope` and `critical` regex around one contract (never a whole tree); broader mutation stays advisory. Accept with `cargo test -p mypypi`, `cargo test -p stuff --test pypi_publish --test pypi_first_party`, `make lint`; `make test-mypypi-native` needs repair tooling and is opt-in.
- **Fix with:** deslop
- **Effort:** L

### DSLP-13 · P3 · Deslop crates/myoci: OCI CLI, server, writer

- **Area:** deslop · myoci
- **Where:** crates/myoci/src/ and crates/myoci/tests/ (about 11.7k lines)
- **Problem:** Steps owed: Diagnose (bounded, this component only; no review exists), then Types, Tests and Dead code, one PR each. Ground is AGENTS.md Verification. Contracts: OCI protocol and storage (docs/oci-design.md, crates/stuff-oci/README.md); the CLI, server, writer and benchmarks (crates/myoci/README.md; `tests/cli.rs`, `mirror.rs`, `crates/stuff/tests/oci_publish.rs`); conformance (`make test-oci-conformance`, `test-oci-conformance-push`, `test-oci-pull`, `test-oci-push`, `test-oci-publish`); benchmark results and the direct blob origin (docs/oci-benchmarks.md, docs/oci-a11.md). Consumers: the stuff publisher, the Worker's OCI paths, OCI clients. Existing evidence: the OCI benchmark and A11 documents; no deslop review.
- **Recommendation:** Tests: map each named contract to its guarding tests, add only missing behavior tests, and if a mutation lane is wanted declare a small `scope` and `critical` regex around one contract (never a whole tree); broader mutation stays advisory. Accept with `cargo test -p myoci`, `make test-oci-conformance`, `make test-oci-publish`, `make lint`; `make oci-bench` gates only changes on the serving path.
- **Fix with:** deslop
- **Effort:** L

### DSLP-14 · P3 · Deslop the remaining crates: shared HTTP, store, catalog, URL, OCI protocol, mirror and mycrates oracle

- **Area:** deslop · shared crates
- **Where:** crates/stuff-http, stuff-server, stuff-store, stuff-catalog (Rust and web/), stuff-url, stuff-cargo-shard, stuff-oci, mymirror (about 12k lines), and the Python mycrates oracle under crates/mycrates
- **Problem:** Steps owed: Diagnose (bounded, this component only; no review exists), then Types, Tests and Dead code, one PR each. Ground is AGENTS.md Verification. Contracts: HTTP serving policy (routes, caching, conditional requests, MIME) in `crates/stuff-server/tests/*_compat.rs` and `stuff-http` unit tests; shared storage and generation activation in `stuff-store`; the `<origin>/current/catalog.json` schema in `stuff-catalog` tests and `tests/repomod/test_deps_world.py` (change the schema and repomod's reader together); search (`make test-search`; commit `assets/search.js` after web changes; `web/minisearch/` is modified, see its NOTICE.md); URL and Cargo shard parsing; OCI protocol API (crates/stuff-oci/README.md); the mycrates oracle stays only as a parity oracle (crates/mycrates/AGENTS.md, docs/mycrates-contracts.md). Consumers: myoci, mynpm, mypypi, the stuff publisher and the Worker. Split into one PR per crate group; none exceeds about 20k lines.
- **Recommendation:** Tests: map each named contract to its guarding tests, add only missing behavior tests, and if a mutation lane is wanted declare a small `scope` and `critical` regex around one contract (never a whole tree); broader mutation stays advisory. Accept with `make test`, `make test-search`, `make lint`. Keep the pristine/modified vendored-tree rules and the oracle's standard-library-only constraint.
- **Fix with:** deslop
- **Effort:** L

### DSLP-15 · P3 · Deslop crates/stuff-worker: the registry Worker

- **Area:** deslop · worker
- **Where:** crates/stuff-worker/ (src/ Rust about 3k lines, TypeScript about 1.7k lines, test/)
- **Problem:** Steps owed: Diagnose (bounded, this component only; no review exists), then Types, Tests and Dead code, one PR each. Ground is AGENTS.md Verification. Contracts: the Worker host, WASM build and runtime tests (crates/stuff-worker/README.md; `test/*.test.mjs` under workerd); Worker package and tool pins in `package.json` and `Cargo.lock`; `vendor/stats-producer/` is pristine (`upstream.json` records its upstream) and must stay so. Consumers: OpenOrange deployment (`make worker-deploy*`), the registries it serves, catalog pages that embed committed assets. Types here include the TypeScript sources.
- **Recommendation:** Tests: map each named contract to its guarding tests, add only missing behavior tests, and if a mutation lane is wanted declare a small `scope` and `critical` regex around one contract (never a whole tree); broader mutation stays advisory. Accept with `make worker-test`, `make worker-check`, `make ts-lint` and `make lint`. Deployment targets stay out of scope.
- **Fix with:** deslop
- **Effort:** M

### DSLP-16 · P3 · Deslop deploy/: OpenOrange host tooling and maintenance scripts

- **Area:** Needs owner · deploy
- **Where:** deploy/ (141 files), including deploy/openorange/ and its rivet TypeScript
- **Problem:** Deferred: deploy/openorange/ (host runtime, ingress, storage, recovery) is owned by a separate active OpenOrange campaign with dirty worktrees (docs/openorange-runtime.md, docs/campaigns/deslop-roadmap.md). The generic maintenance scripts (R2 pull, put and gc, store copy, fake S3, smoke checks) share that tree. Deslop edits here would collide with that work.
- **Recommendation:** The owner decides whether the OpenOrange campaign has finished or whether deslop takes the non-OpenOrange scripts separately. Until then do not schedule this component. If scheduled: Diagnose first (none exists), then Types, Tests and Dead code; accept with `make test-r2`, `make test-publish-lock`, `make test-store-copy`, `make pipecheck`, `make worker-deploy-test`; live checks (`make test-r2-live`, `make smoke-deployed`, deployments) stay opt-in.
- **Fix with:** deslop
- **Effort:** L
