# myoci deslop pass (DSLP-13)

Scope: `crates/myoci` (`8,514` source lines before edits under `crates/myoci/src/`, plus `crates/myoci/tests/`) on `rustc 1.102.0-nightly (5b7b37aef 2026-11-08)` / `clippy 0.1.101`. Serving read paths (`src/serve.rs`) were unchanged, so `make oci-bench` did not need to rerun.

## 1. Diagnose

Bounded inspection covered untrusted input, mirror/blob acquisition, push/chunked framing, and store boundaries in `crates/myoci/src/`. Both pre-campaign leads were confirmed as P2 defects, reproduced with failing tests, and fixed:

1. **Confirmed P2 — `crates/myoci/src/push.rs` (`read_chunked_body` length overflow):**
   - `body.len() + size > limit` overflowed `usize` when `body` already contained bytes and a subsequent chunk header carried a size near `usize::MAX`. In debug builds `push::tests::chunked_body_rejects_overflowing_chunk_size_without_panicking` panicked at `src/push.rs:238:12` (`attempt to add with overflow`); in release builds wrapping arithmetic bypassed the `limit` check and truncated `body`.
   - Fix: reject empty or non-hex-digit chunk sizes (such as `+`-prefixed strings) and compute `body.len().checked_add(size)` before resizing, returning `ErrorCode::SizeInvalid`. Kept `push::tests::chunked_body_rejects_overflowing_chunk_size_without_panicking`.
2. **Confirmed P2 — `crates/myoci/src/mirror/acquire.rs` (`acquire_entry` temp file leak on digest mismatch):**
   - When `fetch_blob_to_file` downloaded the expected byte count and `state.store_blob(&temp, &blob.digest)?` failed on digest mismatch (or `get_to_file` failed mid-stream), early `?` return skipped `std::fs::remove_file(&temp)` and left `.uploads/mirror-<hex>-<pid>.tmp` behind until the 2-hour `MIRROR_TEMP_GRACE` sweep.
   - Fix: wrap the temporary upload path in an RAII `TempUploadFile` drop guard that removes the file on every exit path. Kept `blob_digest_mismatch_removes_temporary_upload_file` in `crates/myoci/tests/mirror.rs` using `Fixture::tamper_blob` in `crates/myoci/tests/fixture/registry.rs`.

### Open P3 findings

- `crates/myoci/src/push.rs` (`read_chunked_body`): `read_line` for chunk headers and trailers has no per-line byte cap or trailer count limit (unlike `writer.rs::BodyReader::read_line` at 4,096 bytes), though callers require push auth and `READ_TIMEOUT`.
- `crates/myoci/src/import.rs` (`walk_descriptor`): recurses across nested `Image::Index` manifests without a `MAX_GRAPH_DEPTH` cap (cycle-protected via `walk.manifests`, whereas `mirror/graph.rs` and `mirror/acquire.rs` cap depth at 32).
- `crates/myoci/src/writer.rs` (`upload_r2`, `run`): `upload_r2` leaves `.r2-<hex>-<session>` staging directories if `copy` or `write` fails before `r2-put.py`; `run` decrements `active` manually instead of using a drop guard like `serve.rs::ActiveGuard`.
- `crates/myoci/src/mirror/plan.rs` (`ObjectReport`): encodes a two-state report using `graph: &'static str` plus five `Option<u64>` fields unwrapped nine times in `render_text`/`render_json`.

## 2. Types

Ran `cargo clippy -p myoci --all-targets` with the 9 candidate warnings (`-W`):

| Candidate | `src/` non-test | `src/` incl. tests | `tests/` | Disposition |
| --- | ---: | ---: | ---: | --- |
| `unsafe_code` | 0 | 0 | 0 | Already `#![forbid(unsafe_code)]` in every `src/*.rs` file; no new setting. |
| `wildcard_enum_match_arm` | 3 | 3 | 0 | Reject: `push.rs` error/method dispatch and `writer.rs` fallback arms are intentional. |
| `match_wildcard_for_single_variants` | 0 | 0 | 0 | Reject: no witness. |
| `cast_possible_truncation` | 5 | 5 | 0 | Reject: bounded `1 << 16`/`1 << 20` buffer slices, 64-bit timestamps, and percentile rank in `bench.rs`. |
| `cast_sign_loss` | 1 | 1 | 0 | Reject: `bench.rs::percentile` operates on non-negative durations and `sorted.len() >= 1`. |
| `unwrap_used` | 9 | 73 | 407 | Reject lint adoption: all 9 non-test occurrences are `ObjectReport` in `mirror/plan.rs` (filed as P3 above); remaining are in tests. |
| `expect_used` | 23 | 23 | 4 | Reject: CLI post-validation `.expect("validated")` and static HTTP client timeout / `"latest"` invariants. |
| `redundant_clone` | 3 | 3 | 9 | Reject: ownership style only, no soundness witness. |
| `needless_pass_by_value` | 5 | 5 | 2 | Reject: ownership style only, no soundness witness. |

Escape-hatch scan (`rg -n "unwrap|expect|as |#\[allow|unsafe" crates/myoci/src/`): `308` lines before edits (`28` `#![forbid(unsafe_code)]` lines, `0` `#[allow(...)]`, `0` `unsafe` blocks). No candidate lint was adopted.

## 3. Tests

| Contract | Guarding tests | Gap and disposition |
| --- | --- | --- |
| OCI protocol and storage | `src/import.rs::tests` (3), `src/publish.rs::tests` (2), `tests/cli.rs` (`imported_state_publishes_serves_adopts_and_detects_tampering`, `verify_names_the_integrity_check_that_rejects_each_tampering`), `crates/stuff/tests/oci_publish.rs`, `crates/stuff/tests/republish.rs`, `make test-oci-publish` | Offline tests cover local layouts, generation determinism, catalog schema 4, adopt, and tamper rejection. Retain existing checks. |
| CLI and exit codes | `src/error.rs::tests::maps_the_shared_exit_contract`, `tests/cli.rs::failures_map_to_the_documented_exit_codes`, `tests/mirror.rs::operational_contract` | Covers documented exit codes (`0`, `1`, `2`, `3`, `4`) and option validation. |
| Server | `tests/cli.rs::imported_state_publishes_serves_adopts_and_detects_tampering`, `crates/stuff/tests/oci_publish.rs`, `make test-oci-conformance`, `make test-oci-pull` | Read API endpoints, manifest/blob/tag/referrer serving, and 404s are covered in `cli.rs`; conformance suite tests full HTTP matrix externally. |
| Writer | `src/writer.rs::tests::upload_sessions_exclude_concurrent_mutation_and_release_on_disconnect`, `tests/cli.rs::pushed_blob_and_manifest_are_served_back_and_verified`, `make test-oci-push`, `make test-oci-conformance-push` | Covers session locking, HMAC upload tokens, PATCH/PUT, and digest mismatch rejection; R2 sink (`deploy/test-r2-multipart.sh`) is live-env opt-in. |
| Mirror | `src/mirror/http.rs` tests (3), `src/mirror/reference.rs` tests (3), `tests/mirror.rs` (10 tests, including new `blob_digest_mismatch_removes_temporary_upload_file`) | Added regression test for temp file cleanup on blob digest mismatch. |
| Push | `tests/cli.rs::pushed_blob_and_manifest_are_served_back_and_verified`, `src/push.rs::tests::chunked_body_rejects_overflowing_chunk_size_without_panicking`, `make test-oci-push`, `make test-oci-conformance-push` | Added regression test for chunked body length overflow. |

- **Hand-injected fault control:** inverted `!authorized(headers, &options.token)` to `authorized(...)` in `crates/myoci/src/push.rs`; `cargo test -p myoci` exited `101` with `tests/cli.rs::pushed_blob_and_manifest_are_served_back_and_verified` failing at line 395 (`202` vs `401`). Restored exact source immediately after.
- **Needs environment:** `cargo-llvm-cov` and `cargo-mutants` are not installed in this environment, so coverage and mutation scores were not measured.

## 4. Dead code

Ran `cargo clippy -p myoci --all-targets -- -W dead_code -W unreachable_pub` and checked workspace consumers (`crates/stuff`, `crates/stuff-worker`, `crates/stuff-server`, `deploy/`, `Makefile`):

- `0` `dead_code` diagnostics across `myoci` lib, bin, and tests.
- `1` `unreachable_pub` diagnostic in `crates/myoci/src/mirror/plan.rs:43` (`pub fn run`, called by `mirror::run` through private `mod plan`), plus `18` `unreachable_pub` diagnostics in `crates/myoci/tests/fixture/registry.rs` (`#![allow(dead_code)]` test fixture module). Changing visibility removes no code or behavior, so nothing was removed.
- External consumers: `crates/stuff` calls `myoci::{Error, state::State, publish::{publish, adopt, DEFAULT_PUBLIC_URL}, import::{import_layout, import_from}, mirror::{MirrorLock, Inventory, MirrorCommand, MirrorOptions, resolve, sync}, serve::{run, ServeOptions}, verify::verify_state}`; `deploy/` scripts and `Makefile` invoke the `myoci` CLI subcommands (`init`, `import`, `inspect`, `publish`, `verify`, `adopt`, `serve`, `writer`, `bench`).
- **Needs environment:** external runtime conformance/integration scripts (`make test-oci-conformance`, `make test-oci-conformance-push`, `make test-oci-pull`, `make test-oci-push`, `make test-oci-publish`, `deploy/test-r2-multipart.sh`) were not run in this slice.
