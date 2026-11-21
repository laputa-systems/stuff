# stuff-worker

OpenOrange Worker that serves the registry layouts and static artifact mirror
through R2-compatible bindings backed by the host's S3 store. URL routing
and response planning are Rust (`src/map.rs`, `src/api.rs`, shared `stuff-http`
semantics, `deser` for config parsing), with no `worker` SDK and no async
runtime in the dependency tree. Routes match on the request hostname, so each
registry serves from its own domain root (see `STUFF_ROUTES` in
`orange.jsonc`, which also defines the storage bindings).
The thin fetch handler `entry.ts` initializes the compiled wasm once
(`initSync`) and talks to R2 directly.

That boundary is the wasm-bindgen ABI produced by `scripts/build-wasm.sh`.
The exports are synchronous and carry JSON strings and primitives.
workerd and OpenOrange instantiate the resulting core module. A WIT component
would need a second host. Workers load core
modules through `WebAssembly.instantiate`, and the platform's Rust path is
wasm-bindgen, so this Worker does not add a component host.

## Build

`pnpm run build` (`scripts/build.mjs`) builds the wasm module and bindgen
glue, compiles the TypeScript with `tsrs`, and writes the native module
manifest under `build/orange/workers/default`. `orange.jsonc` is the source
for runtime bindings and compatibility settings. The build needs the pinned
Rust toolchain with the `wasm32-unknown-unknown` target installed.

`pnpm run build:wasm` runs only the wasm step. `pnpm run typecheck` checks
the TypeScript without emitting. `pnpm run dev` starts the OpenOrange local
server; `make dev` installs both pinned dependency closures first.
`make worker-check` validates the OpenOrange package without credentials.

Development binds to `127.0.0.1:8787` by default (`PORT` overrides the port).
The unified page links to `/cargo`, `/npm`, `/pypi`, and `/mirror`; OCI uses
`/v2/`. The data is the synthetic registry fixture in a fresh `.work/tmp`
directory. It has no production storage or telemetry credentials. Successful
Rust and TypeScript builds are staged before restarting the local runtime;
failed builds leave the last successful build serving. Local data survives
those restarts. SIGINT/SIGTERM close the watchers, builder and runtime.
`make worker-dev-test` exercises a real Rust response change and an invalid
Rust edit against the normal `pnpm run dev` command.

Vite 8 builds with Rolldown. Wrangler is a test dependency and brings esbuild;
the Worker build does not invoke either. `make search-bundle` uses Vite to
rebuild `crates/stuff-catalog/assets/search.js`. `make catalog-css` copies the
stylesheets of the pinned `@laputa-systems/ui-dashboard` devDependency, which
`.npmrc` routes to the stuff npm registry, into
`crates/stuff-catalog/assets/ui-dashboard/`.

The wasm step runs:

```sh
cargo build --target wasm32-unknown-unknown --profile wasm-release -p stuff-worker
wasm-bindgen --target web --out-dir build/wasm ../../target/wasm32-unknown-unknown/wasm-release/stuff_worker.wasm
wasm-opt -O3 --strip-debug --strip-producers build/wasm/stuff_worker_bg.wasm -o build/wasm/stuff_worker_bg.opt.wasm
mv build/wasm/stuff_worker_bg.opt.wasm build/wasm/stuff_worker_bg.wasm
```

`--target web` with explicit init is used because the bundler target's
namespace import does not resolve to the wasm exports. The `wasm-release`
profile uses `opt-level = 3`, fat LTO, one codegen unit, and
`panic = "abort"`. `wasm-opt -O3` is the speed-oriented Binaryen pass;
size-oriented `-Oz` is not used. Binaryen's `wasm-opt` must be on `PATH`.
`scripts/build-wasm.sh` reads the bindgen version from `Cargo.lock` and
installs/replaces `wasm-bindgen-cli` with `cargo install --locked` when it
is missing or mismatched.

## Test

`make worker-test` builds the bundle and runs the Node test suite
(`pnpm run test:runtime` → `node --test`, see `package.json`). The runtime tests
seed local storage and cover cold-HEAD caching, root links, pinned artifact
aliases, OCI reads, and OCI writes.

`pnpm run check` builds the Worker, runs Oxlint and the TypeScript checker, and
runs the Worker tests. The Node.js requirement is `engines.node` in `package.json`.

## Bench

`cargo bench -p stuff-worker --bench request_paths` times the Rust half of
the request paths that production metrics show as hot, with allocation
counts:

- the unified page at small (one package per registry), production
  (`tests/fixtures/catalogs`), and heavy (production ×10) scale;
- the unified `llms.txt` on the production catalogs;
- a cargo index revalidation burst: route mapping, pointer resolution,
  and a 304 plan for every crate in the production catalog.

The JavaScript glue, the wasm boundary, and R2 latency are not in these
numbers. Read those from production with the `stats-improve` workflow.

The wasm step must run before `tsrs` because `entry.ts` imports the generated
wasm glue. The runtime tests use the build output from the same directory.

## OpenOrange

The registry runs on self-hosted OpenOrange (pinned in `orange/`; runtime in
`deploy/openorange`). `scripts/orange.mjs OUTPUT RELEASE` writes the runtime descriptor from `orange.jsonc` and rejects unmapped fields;
it derives the S3 bucket binding map and sets `STUFF_RELEASE`. `make worker-orange-test` runs the
built Worker under the pinned `orange dev` with seeded storage for every
registry hostname.

For an image, install the existing locked Worker dependencies, commit the tree,
then run `crates/stuff-worker/orange/build-image.sh HOST`. It builds the Worker,
stages a portable descriptor and bundle, and builds `stuff:<commit>` on HOST
for Linux amd64 over SSH. Supply runtime secrets separately on the host. Run
`make worker-orange-package-test` to verify the relocated staging paths.

From the repository root, `make deploy ORANGE_HOST=lisa` runs the Worker and
OpenOrange checks, builds the committed image on the selected host, and deploys
it. The host must already have the Stuff app configured and running. The
deployment checks Orange readiness, confirms the selected image, and requests
the unified registry over HTTPS using the host's Tailscale IPv4 address. It
restores the previous image if deployment fails or is interrupted. Image
selection and rollback compare the expected image under the host's deployment
lock, preserving newer concurrent deployments. Configuration, credentials and
publication state are retained. Publish registry changes separately with the
native `stuff` publisher. Run
`make worker-deploy-test` for the local deployment and rollback regression.

The [shared host runbook](../../docs/openorange-runtime.md) owns ingress,
storage, credentials, and recovery. The checked-in app configuration enables
the coordinator and private publishing host, with anonymous public registry
reads. Optional OCI HTTP pushes require separate configuration.

### Read replica

`cloudflare.ts` is a separate Cloudflare entrypoint for a route-attached Worker
that serves the registry hostnames from an R2 replica when the OpenOrange origin
does not answer. `cloudflare.config.ts` is its configuration (`stuff-failover`,
six R2 bindings, no Durable Object, no `domains`). The failover decision lives in
`src/failover.ts` so it is testable without a network, and
[registry failover](../../docs/registry-failover.md) owns the routed hosts, the
replica sync, and what does not fail over. `pnpm run check:failover` type-checks
the entrypoint and its config, `pnpm run build:failover` emits it under
`build/failover`, and `pnpm run test:failover` runs its tests.

Cloudflare-specific surfaces and what replaced them:

| Surface | On OpenOrange |
| --- | --- |
| `ctx.exports.Registry.fetch` with `cf.cacheKey` | Removed; one fetch handler. Orange 1.0.2 builds `request.url` from the Host header, so hostname routing is unchanged |
| `caches.default` render cache | In-process LRU of rendered unified pages (64 entries, 16 MiB) keyed by origin, release, generation ids and path; artifact bodies always stream from storage |
| `env.VERSION` | `STUFF_RELEASE` text binding |
| `.wasm` import + `initSync` | Orange loads `.wasm` imports as `WebAssembly.Module`; unchanged |
| Conditional R2 `put` | The S3 facade pins the write with `If-None-Match: *` or `If-Match`; the self-hosted store honors both |

The facade spools streamed S3 PUT bodies to a temporary file. Publishers upload
natively through the Rust S3 client, so only Worker-side OCI pushes take that
path. GET and range reads stream. The runtime is pinned in `orange/package.json`
and not vendored here, so its source line numbers are not quoted.

### Coordinated native uploads

The management host exposes signed S3 requests at `/_s3/BUCKET/KEY` when
`STUFF_COORDINATOR_ENABLED` is true. `STUFF_S3_BUCKET_BINDINGS` is generated
from the built R2 bindings. Publishers use a separate service key and sign
the upload lease in `x-amz-security-token`. The gateway checks the payload
while streaming and keeps the final bytes back until its digest matches.
Backing S3 credentials stay inside the Worker. Immutable PUTs and multipart
completion use conditional creation. Direct writes to `current` are refused.

The management endpoint is `/_publication/<registry>/<operation>` on the stuff
host, with registries `cargo`, `npm`, `pypi`, `oci`, and `mirror`. Requests use
`Authorization: Bearer <STUFF_COORDINATOR_TOKEN>`. `GET current` returns
`revision`, `generation`, `manifest`, and `pending`; all other operations are
POST with JSON. `begin` and `gc-claim` return an exclusive five-minute lease,
expiry in Unix milliseconds, and the current revision; `renew` and `abort` take
`{"token":"..."}`. `activate` and `rollback` take `token`, `key` (idempotency
key), `generation`, `manifest` (lowercase SHA-256 of the manifest bytes), and
`expectedRevision`; both verify the existing version-1 manifest and its objects
before committing, and a replay of the same key and payload returns its receipt.
`gc-delete` takes a GC `token` and `generation`, refuses the current generation
and references from other manifests, and does not collect shared objects. The
Durable Object serializes operations and checks lease expiry. Its SQLite row is
the authority for revision, generation, manifest identity and pending state;
R2 `current` is a repairable compatibility projection, so mutable reads use
SQLite and the next operation repairs drift. Before any delete it durably
retires the exact S3 version IDs; retirement is permanent and the immutable
generation ID is never reused for different bytes.

Direct Stats events use the vendored producer 0.2.0 artifact, whose source
revision and hashes are recorded under `vendor/stats-producer`. Configure
`APPLICATION_EVENTS_ENDPOINT`, `APPLICATION_EVENTS_SERVICE`, and
`APPLICATION_EVENTS_TOKEN`. Delivery holds at most 256 queued events, sends
64 per batch, and uses two retries with a two-second request deadline.
Events report integer wall time. Error messages are redacted, and delivery
failure does not reject a registry request. No platform CPU or billing data
is inferred.
