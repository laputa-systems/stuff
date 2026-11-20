# Shared crates and mycrates deslop pass (DSLP-14)

Scope: `crates/stuff-http` (`796` lines), `crates/stuff-server` (`1,118`), `crates/stuff-store` (`1,177`), `crates/stuff-catalog` (`3,038` Rust + `194` non-vendored `web/*.ts`, excluding modified `web/minisearch/`), `crates/stuff-url` (`498`), `crates/stuff-cargo-shard` (`41`), `crates/stuff-oci` (`2,816`), `crates/mymirror` (`1,521`), and `crates/mycrates` (`4,329` Python oracle lines; `15,528` total source lines inspected) on `rustc 1.102.0-nightly (5b7b37aef 2026-11-08)` / `clippy 0.1.101 (5b7b37aefc 2026-11-08)`.

## 1. Diagnose

Bounded inspection covered untrusted HTTP routing/headers/caching (`stuff-http`, `stuff-server`), storage/generation activation (`stuff-store`), URL and Cargo shard parsing (`stuff-url`, `stuff-cargo-shard`), OCI protocol parsing (`stuff-oci`), catalog rendering/search (`stuff-catalog`), `mymirror`, and the `mycrates` Python oracle.

1. **Confirmed P2 — `crates/stuff-oci/src/request.rs` (`parse_write_request` upload session routing):**
   - `parse_write_request` checked `if length != 5 { return ParsedWrite::NotFound; }` and indexed `segments[4]` for `/v2/<name>/blobs/uploads/<upload_id>`, rejecting every 1-segment repository (`alpine`, length 4) and 3+-segment repository (`org/team/app`, length 6) with `NotFound` even though `POST /v2/<name>/blobs/uploads/` and `PUT /v2/<name>/manifests/<ref>` accepted them.
   - Reproduced with `request::tests::parses_blob_upload_sessions_for_single_and_multi_segment_repositories` (failed on unpatched code for `GET /v2/alpine/blobs/uploads/u1?session=t`), then fixed by removing the `length != 5` guard and reading `segments[length - 1]`. Kept the regression test.

### Open P3 findings

- `crates/mymirror/src/archive.rs` (`extract`, `tar_members`): `TarXz` and `Zip` bound decompressed reads to `MAX_DECOMPRESSED + 1` with `.take(...)`, whereas `TarGzip` passes an unbounded `flate2::read::GzDecoder` into `tar_members` where `entry.read_to_end(&mut data)` buffers an entire member before `enforce_cap` runs (`fetch_verified` verifies SHA-256 first on normal paths).
- `crates/mymirror/src/acquire.rs` (`is_restricted_address`): IPv6 `SUBNETS` omits `::/128` (unspecified) and `::1/128` (loopback) alongside the covered ULA, link-local, NAT64, IPv4-mapped, and multicast ranges.
- `crates/stuff-server/src/config.rs` (`Config::match_route`): matches `route.prefix` against raw `path` without stripping a `?query` suffix (e.g. `"/mirror?x=1"` skips `"mirror"` and falls through) and compares untrimmed `prefix.len()` if `Config` is constructed directly (`main.rs` trims slashes).
- `crates/stuff-http/src/condition.rs` (`parse_range`): uses `str::parse::<u64>()`, which accepts `+`-prefixed digits (`bytes=+0-1`) instead of strict `1*DIGIT`.

## 2. Types

Ran `cargo clippy -p stuff-http -p stuff-server -p stuff-store -p stuff-catalog -p stuff-url -p stuff-cargo-shard -p stuff-oci -p mymirror --all-targets` with the 9 candidate warnings (`-W`):

| Candidate | `src/` non-test | `src/` incl. tests | `tests/` | Disposition |
| --- | ---: | ---: | ---: | --- |
| `unsafe_code` | 0 | 0 | 0 | All 8 crates already carry `#![forbid(unsafe_code)]` (`-W clippy::unsafe_code` is unknown; rustc `unsafe_code` is forbidden). |
| `wildcard_enum_match_arm` | 9 | 16 | 0 | Reject: intentional method, error, tar entry type, ordering, and dependency-kind catchalls. |
| `match_wildcard_for_single_variants` | 0 | 0 | 0 | Reject: no witness. |
| `cast_possible_truncation` | 3 | 3 | 0 | Reject: `schema as u32` (`1..=4`), `remaining.min(buf.len() as u64) as usize` (`<= 65536`), `strip_components as usize` (`<= 16`). |
| `cast_sign_loss` | 0 | 0 | 0 | Reject: no witness. |
| `unwrap_used` | 1 | 333 | 133 | Reject: single non-test site is `"127.0.0.1:8000".parse().unwrap()` in `stuff-server/src/main.rs:319`; remaining are in tests. |
| `expect_used` | 9 | 14 | 22 | Reject: `fmt::Write` to `String` (4), `CONNECT_TIMEOUT` builder (1), non-empty `tags` guard (1), `include_str!` CSS prefix (1), `deser_value` type-checked arms (2). |
| `redundant_clone` | 0 | 1 | 0 | Reject: no non-test witness. |
| `needless_pass_by_value` | 3 | 3 | 0 | Reject: `Site::activate(PathBuf)` public API, `trim_origin(String)`, and `Dependencies::merge(Dependencies)`; ownership style only. |

- Escape-hatch scan (`rg -n "unwrap|expect|as |#\[allow|unsafe"` across `src/`): `556` lines (`stuff-http` 42, `stuff-server` 61, `stuff-store` 129, `stuff-catalog` 146, `stuff-url` 23, `stuff-cargo-shard` 1, `stuff-oci` 100, `mymirror` 54; `0` `unsafe` blocks, `#![forbid(unsafe_code)]` in every crate).
- Python `crates/mycrates`: `uv run --group dev ruff check --statistics crates/mycrates/mycrates` reported `18` lint items (`I001` 4, `SIM115` 3, `RUF005` 2, `PERF401` 2, `A002` 1, `SIM102` 1, `FURB188` 1, `SIM105` 1, `UP041` 1, `RET504` 1, `B905` 1; `554` across `crates/mycrates` including unittest-style `tests/`). `ty` in `pyproject.toml` scopes `include = ["repomod", "tests/repomod", "bench"]` and intentionally skips `crates/mycrates`; running `uv run --group dev ty check crates/mycrates/mycrates/*.py` directly reports `50` diagnostics against the untyped Python 3.11 stdlib-only oracle (e.g. `@typing.override` from 3.12 and `BaseServer` dynamic attributes). Left `mycrates` unchanged.

## 3. Tests

| Contract | Guarding tests | Gap and disposition |
| --- | --- | --- |
| HTTP serving policy (`stuff-http`, `stuff-server`) | `stuff-http` unit tests (`18`: `route`, `condition`, `cache`, `mime`, `npm`), `stuff-server` unit tests (`12`: `admission`, `config`, `serve`), `stuff-server/tests/http_compat.rs` (`6`), `cargo_compat.rs` (`1`), `npm_compat.rs` (`1`) | Covers path traversal, symlinks, ETags, `If-Match`/`If-None-Match`, ranges, cache headers, admission limits, real `cargo`/`npm` installs. |
| Shared storage & generation activation (`stuff-store`) | `stuff-store` unit tests (`23`: `site` 10, `blob` 7, `lock` 3, `fsync` 1, `hash` 1, `generation` 1) | Covers atomic staging, verification/quarantine, immutable generations, file locks, hardlink/copy SHA-256 verification. |
| Catalog schema & search (`stuff-catalog`) | `stuff-catalog` unit tests (`55`: `model` 19, `html` 14, `llms` 8, `ui` 5, `diff` 3, `identity` 3, `version` 3), `make test-search` (`9` in `web/search.test.ts`), `tests/repomod/test_deps_world.py` | Covers schemas 1–4 + mirror dialect, HTML/llms rendering, fingerprint sealing, MiniSearch ranking. |
| URL & Cargo shard parsing (`stuff-url`, `stuff-cargo-shard`) | `stuff-url` unit tests (`7`), `stuff-cargo-shard` unit tests (`2`) | Covers WHATWG special-scheme normalization, dot/slash/redirect resolution, ASCII shard boundaries. |
| OCI protocol API (`stuff-oci`) | `stuff-oci` unit tests (`35`: `response` 8, `request` 6 incl. new test, `manifest` 4, `view` 4, `reference` 3, `referrers` 3, `session` 3, `digest` 1, `error` 1, `generation` 1, `json` 1, `media` 1) | Added `request::tests::parses_blob_upload_sessions_for_single_and_multi_segment_repositories`. |
| Static mirror (`mymirror`) | `mymirror` unit tests (`14`: `manifest` 9, `glob` 5), `tests/mirror.rs` (`14`), plus ignored `tests/seed.rs` (`1`) | Offline coverage of manifest validation, tar.gz/tar.xz/zip extraction, symlink containment, deterministic build/assemble. |
| Python Cargo oracle (`crates/mycrates`) | `make test-mycrates` (`175` tests across `14` test files, including `test_contracts.py` `8`, `test_golden.py` `2`, `test_cargo_native.py` `1`) | Preserved stdlib-only constraint and all golden fixtures. |

- **Hand-injected fault control:** replaced `return Err(PathError::NotFound);` with `continue;` for `b".."` in `crates/stuff-http/src/route.rs:208`; `cargo test -p stuff-http` exited `101` with `route::tests::rejects_traversal_and_bad_encoding` failing at `crates/stuff-http/src/route.rs:245:55`. Restored exact original source byte-for-byte (`git diff --exit-code crates/stuff-http/` exited `0`).
- **Needs environment:** `cargo-llvm-cov` and `cargo-mutants` are not installed, so line coverage and workspace mutation scores were not measured.

## 4. Dead code

Ran `cargo clippy -p stuff-http -p stuff-server -p stuff-store -p stuff-catalog -p stuff-url -p stuff-cargo-shard -p stuff-oci -p mymirror --all-targets -- -W dead_code -W unreachable_pub` and checked workspace consumers (`crates/stuff`, `crates/mynpm`, `crates/mypypi`, `crates/myoci`, `crates/stuff-worker`):

- `0` `dead_code` diagnostics across all 8 Rust crates.
- `4` `unreachable_pub` diagnostics in `stuff-oci` on items inside private modules not re-exported by `crates/stuff-oci/src/lib.rs`:
  - `crates/stuff-oci/src/media.rs`: `DOCKER_SCHEMA1` and `DOCKER_SCHEMA1_SIGNED` (used only by `manifest.rs`) narrowed to `pub(crate) const`.
  - `crates/stuff-oci/src/session.rs`: `hmac_sha256` and `constant_time_eq` (used only inside `session.rs`) narrowed to private `fn`.
- All public crate APIs across the 8 crates are consumed by `crates/stuff`, `crates/mynpm`, `crates/mypypi`, `crates/myoci`, `crates/stuff-worker`, or their own binaries/tests; `crates/stuff-catalog/web/top-k.ts` (`selectTop`) is imported by `web/minisearch/MiniSearch.ts`.
- **Needs environment:** `cargo-machete` and `vulture` are not installed, so unused dependency/Python dead-code scans were not run externally.
