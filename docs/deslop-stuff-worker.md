# stuff-worker review

This review covers `crates/stuff-worker` at DSLP-15's base (`cf8c48fd`), with `rustc 1.102.0-nightly`, Node.js `v26.13.1`, `oxlint 1.93.0`, and `tsrs 0.25.0-ts7.1.0-beta` on macOS. It covers the Rust sources (`src/`, 2,831 lines; `benches/request_paths.rs`, 180 lines), the first-party TypeScript sources (`entry.ts` and `src/*.ts`, 1,689 lines), and the test suite under `test/`. `vendor/stats-producer/` (`upstream.json` version `0.2.0`, revision `bdf65f743a28509d8cb59696d5d6f64bdee15412`) was verified unchanged by SHA-256 and left untouched; deployment targets were not run.

## Diagnose

The review inspected untrusted HTTP request dispatch (`entry.ts`), hostname and prefix routing (`src/map.rs`, `src/api.rs`, `entry.ts`), the synchronous `wasm-bindgen` JSON/primitive boundary (`src/wasm.rs`, `entry.ts`), cache-control, range, conditional, and render-cache handling (`src/api.rs`, `entry.ts`), error handling and redacted telemetry (`src/telemetry.ts`, `entry.ts`), R2 body lifecycle and shared-store alias validation (`entry.ts`), the SigV4 S3 gateway (`src/gateway.ts`, `src/sigv4.ts`, `src/s3.ts`), and the SQLite-backed `PublicationCoordinator` (`src/coordinator.ts`).

| ID | Priority | Finding | State |
| --- | --- | --- | --- |
| DSLP-15-1 | P3 | `writeErrorPlan` (`entry.ts:378`) and `ociFetch` (`entry.ts:752`) pass JS `.length` (UTF-16 code units) as HTTP `content-length` on OCI error JSON. | Probed under `workerd`; open |
| DSLP-15-2 | P3 | `immutableText` (`entry.ts:534`) skips `object.text()` on size mismatch without cancelling `object.body` before throwing `PublicationConflict`. | Read from code; open |

DSLP-15-1: Sending `GET https://oci.test/v2/example/app/tags/list?n=%C3%BC` against `workerHarness` returned status `400` with body `{"errors":[{"code":"PAGINATION_NUMBER_INVALID","message":"invalid pagination number","detail":"ü"}]}` (`101` UTF-8 bytes vs `100` UTF-16 code units). `workerd` stripped/normalized the header (`res.headers.get("content-length") === null`) and delivered the full valid JSON body, so no truncation occurs under `workerd`.

DSLP-15-2: `immutableText` in `coordinatedOciManifest` reads `meta.get(key)` after a conditional `put` conflict and short-circuits `object.size !== value.byteLength || await object.text() !== text` before throwing `PublicationConflict`, leaving `object.body` uncancelled on that conflict error path.

Checked and not filed:

- Host routing and blob isolation. `serve` restricts `STUFF_CARGO_BLOB_HOST` to `/blobs/...` and `STUFF_OCI_BLOB_HOST` to `^/sha256/[0-9a-f]{64}$`. `map_asset` delegates path normalization and traversal rejection to `stuff_http::plan_route`, and `serve` verifies `generations/<id>/catalog.json` (or reads the generation's npm packument) before promoting a shared-store alias to `immutable`.
- Body ownership and speculative reads. `serve` tracks every opened `store.get` object in `opened` and `pending` and cancels every body not handed to `Response` in `finally`, including discarded `lastPointerText` speculative reads.
- S3 gateway and coordinator boundaries. `gateway.ts` verifies SigV4 dates (including calendar round-trip and 15-minute window), sorted signed headers (requiring `x-amz-security-token`), holds back the trailing chunk until `crypto.DigestStream("SHA-256")` matches `x-amz-content-sha256`, forbids `current` and non-immutable keys, and requires an active `gateway-lease`. `coordinator.ts` bounds POST bodies to 16 KiB, serializes via `blockConcurrencyWhile`, validates manifest keys/sizes/etags, enforces idempotency receipts and retired-generation/version checks, and requires bucket versioning before GC deletion.
- OCI manifest push. `ociPushManifest` checks `content-length` and caps streamed body reads at 4 MiB with fatal UTF-8 decoding, validates referenced blobs and child manifests before writing a generation, and keeps `STUFF_OCI_PUSH_TOKEN` constant-time checked (`oci_auth_check`).

## Types

### Rust

The native production check used `cargo clippy --offline -p stuff-worker --lib --message-format=json` with the nine deslop candidate warnings enabled (`-W`), plus `--target wasm32-unknown-unknown --lib` (which compiles `src/wasm.rs`) and `--all-targets` (which includes unit tests and `benches/request_paths.rs`). All commands exited 0 with `rustc 1.102.0-nightly`. `#![forbid(unsafe_code)]` is active in `lib.rs`, `oci.rs`, `oci_push.rs`, and `benches/request_paths.rs`.

| Candidate | `--lib` (native) | `--lib` (wasm32) | `--all-targets` | Decision |
| --- | ---: | ---: | ---: | --- |
| `unsafe_code` | 0 | 0 | 0 | Already forbidden in crate roots; no new setting. |
| `wildcard_enum_match_arm` | 0 | 0 | 16 | Reject: all 16 are `other => panic!(...)` in `map.rs` unit tests. |
| `match_wildcard_for_single_variants` | 0 | 0 | 0 | No diagnostics. |
| `cast_possible_truncation` | 0 | 0 | 0 | No diagnostics. |
| `cast_sign_loss` | 0 | 0 | 0 | No diagnostics. |
| `unwrap_used` | 0 | 0 | 22 | Reject: all 22 are in unit tests (`api.rs`, `oci.rs`, `oci_push.rs`). |
| `expect_used` | 2 | 2 | 56 | Reject: the 2 production sites (`oci_push.rs:345,359`) look up keys collected from the same map; remaining 52 unique test/bench sites (`oci_push.rs:345` compiles in both `--lib` and test unit compilation). |
| `redundant_clone` | 1 | 1 | 2 | Reject: `oci_push.rs:445` (`digest.clone()`), ownership suggestion only, not a type defect. |
| `needless_pass_by_value` | 1 | 4 | 2 | Reject: `oci.rs:151` (`internal_error(message: String)`); the 3 wasm32-only sites (`wasm.rs:24,33,35`) are `Option<String>` parameters required by `wasm-bindgen`. |

### TypeScript

`tsconfig.json` enforces `"strict": true`, `"noEmitOnError": true`, and `"types": []` over `entry.ts`, `src/**/*.ts`, and `build/wasm/*.d.ts`. `pnpm --dir crates/stuff-worker run lint` (`oxlint --type-aware entry.ts src`) passed with 0 warnings and 0 errors across 8 files, and `pnpm --dir crates/stuff-worker run typecheck` (`tsrs -p tsconfig.json --noEmit --fast`) exited 0.

| Escape hatch | `entry.ts` | `src/*.ts` | Total | Disposition |
| --- | ---: | ---: | ---: | --- |
| `as any` | 0 | 0 | 0 | Clean. |
| `@ts-ignore` / `@ts-expect-error` / `@ts-nocheck` | 0 | 0 | 0 | Clean. |
| `as unknown[]` | 0 | 2 | 2 | `coordinator.ts:61,202`; each element is runtime-validated immediately after. |
| Other `as <Type>` assertions | 40 | 12 | 52 | `JSON.parse` / `result.json()` boundary decoders and post-guard narrowings (`coordinator.ts`, `gateway.ts`, `s3.ts`). |
| Non-null `!` assertions | 5 | 20 | 25 | Preceded by regex match groups, `.has`, `.length`, or prior map-key checks. |

No new Rust lint or TypeScript config change was adopted; `strict: true` and `oxlint --type-aware` already guard the TypeScript boundary.

## Tests

Paths below are relative to `crates/stuff-worker`. Rust unit tests (`cargo test -p stuff-worker`) pass 40/40, and `make worker-test` passes 29/29 under `workerd`.

| Contract | Guarding tests | Status / gap |
| --- | --- | --- |
| Rust routing, pointer resolution, unified HTML/`llms.txt`, response planning, OCI read/write planning | `src/map.rs` (11), `src/api.rs` (22), `src/oci.rs` (5), `src/oci_push.rs` (2) via `cargo test -p stuff-worker` | Passed (40/40). |
| Worker bundle & module graph integrity | `test/runtime.test.mjs` ("the uploaded module graph resolves from the main module name"), `test/orange-packaging.test.mjs` | Passed in `make worker-test` and `make worker-check`. |
| Unified index, `llms.txt`, schema-notice resilience, moved pointers, cold `HEAD` | `test/runtime.test.mjs` (lines 42–204) | Passed in `make worker-test`. |
| Shared-store aliases, generation existence gating, ranges, conditionals, native `stuff-server` route/cache parity | `test/runtime.test.mjs` (lines 206–399) | Passed in `make worker-test`. |
| Body stream lifecycle & speculative pointer cleanup | `test/body-lifecycle.test.mjs` | Passed in `make worker-test`. |
| Unified render LRU byte accounting under concurrent cold renders | `test/render-cache.test.mjs` | Passed in `make worker-test`. |
| OCI reads, redirects, pagination, referrers, errors, auth, sessions, mounts, concurrent manifest pushes | `test/runtime.test.mjs` (lines 401–801) | Passed in `make worker-test`. |
| Telemetry integer duration, error redaction, bounded operation names, Stats failure survival | `test/application-producer.test.mjs` | Passed (2/2 via `node --test`). |
| OpenOrange runtime, `PublicationCoordinator` serialization/GC/OCI push, SigV4 S3 gateway | `test/orange.test.mjs`, `test/coordinator-orange.test.mjs`, `test/gateway-orange.test.mjs`, `test/gc-orange.test.mjs`, `test/oci-coordinator-orange.test.mjs` (`make worker-orange-test`) | Retained; not run in this read-only pass (no code changes). |
| Local dev rebuilds & deployment rollback scripts | `test/dev-orange.test.mjs`, `test/deploy-orange.test.mjs` | Retained; not run in this read-only pass. |

Fault control: changing `entry.ts:1040` from `if (generationCatalogKey !== undefined && first.generation === null)` to `if (false && ...)` caused `make worker-test` to fail 2 of 29 tests (`pinned generation artifacts use the shared store aliases` at `test/runtime.test.mjs:224` with `200 !== 404`, and `native server and worker agree on routes and cache kinds` at `test/runtime.test.mjs:392` for `/generations/missing/wheels/pkg-1.0-py3-none-any.whl`), then `entry.ts` was restored byte-for-byte (`git diff -- crates/stuff-worker/entry.ts` empty) and `make worker-test` passed 29/29 again.

Coverage and mutation tools (`cargo-llvm-cov`, `cargo-mutants`) are not installed on this host (**Needs environment**).

## Dead code

- Rust: `cargo clippy --offline -p stuff-worker --all-targets -- -W dead_code -W unreachable_pub` and `--target wasm32-unknown-unknown --lib` reported 0 `dead_code` and 0 `unreachable_pub` warnings. Reference checks across `crates/` confirm every `pub` module item is used by `src/wasm.rs`, `src/api.rs`, unit tests, or `benches/request_paths.rs`.
- TypeScript and scripts: manual export/import scan of `entry.ts`, `src/*.ts`, and `scripts/*.mjs` (excluding `vendor/`) found 0 unused exports and 0 unused files (`vite.search.config.ts` is consumed by the root `Makefile` `search-bundle` target).
- External tools (`cargo-machete`, `knip`): not installed on this host (**Needs environment**).
