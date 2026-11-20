# mynpm review

This review covers `crates/mynpm` at DSLP-11's base (`52c3999d`), with Rust nightly 2026-11-09 on macOS. It does not review the other crates, the Worker, `deploy/` scripts, or live services. Every upstream interaction in this review used offline fixtures or code reading; no live registry was contacted and nothing was published.

## Diagnose

The review read the boundaries that take untrusted bytes or run external programs: tarball inspection (`src/archive.rs`), upstream transfer and digest verification (`src/acquire.rs`), the package-manager environment for resolution and validation (`src/resolve.rs`, `src/validate.rs`), first-party package ingestion (`src/first_party.rs`), and root pin parsing.

| ID | Priority | Finding | State |
| --- | --- | --- | --- |
| DSLP-17 | P2 | Repeated entry names bypassed the entry limit and each repeat cost a scan of the retained list. | Reproduced, fixed in this change set |
| DSLP-18 | P3 | `HttpsExchange::fetch` buffers up to 1 GiB plus 64 MiB whatever limit the caller passes. | Read from the code, not reproduced; open |

DSLP-17: `inspect_archive` let a regular file replace an earlier regular file of the same path, as npm's extractor does, but compared the 100,000-entry limit against the retained list. The probe `rejects_too_many_replacement_entries` (one `package.json` plus 100,000 repeats of one file) returned `Ok` with two entries. The replacement also called `entries.iter().any` and `entries.retain` per repeat. With 50,000 retained paths, 20,000 repeats took 1.39 s in a debug build, and the cost is linear in the repeat count. Repeated empty headers compress roughly 1000:1, so the 1 GiB compressed limit does not bound it. The fix counts every header and finds the replaced entry through a path index; archive order and the replacement rule are unchanged.

DSLP-18: `transfer` checks the caller's `max_bytes` (64 MiB for packuments) only after the whole body is in memory, and `Content-Length` is validated for syntax but never compared with a limit. Reproduction needs a local TLS origin for `HttpsExchange`; the offline fakes replace the `Exchange` trait below the code in question.

Checked and not filed:

- Lifecycle scripts. Resolution (`resolve.rs`) and validation (`validate.rs`) pass `--ignore-scripts` on the command line, set `npm_config_ignore_scripts=true`, write `ignore-scripts=true` to the per-run npmrc, and pass `--ignore-pnpmfile` for pnpm. Package executables run only under the explicit `--smoke-executables` option, which is the documented opt-in execution check.
- Root pins. `parse_root_pins` validates names and versions before they are formatted into the resolution `package.json` and the command line, and the validators reject quotes, slashes beyond the scope, and a leading dash.
- Digests. `download_stage` hashes the staged bytes with SHA-1, SHA-256, SHA-384 and SHA-512, compares every expected claim, and removes the staged file on mismatch. Stored objects are re-hashed and compared with the inventory and upstream metadata on reuse.
- Upstream URLs. `validate_source_url` requires HTTPS, the configured host, no port, credentials, query, or fragment, and redirects are re-validated at every hop up to the limit. `resolve_public_host` rejects non-public addresses. It resolves before the client does, so a rebinding upstream DNS answer is not covered; the host is the configured registry, so this was not filed.
- Archive paths. Entry types other than files and directories, non-UTF-8, control characters, quotes, backslashes, `.` and `..` segments, multiple roots, and duplicates of `package.json` are rejected, with tests in `src/archive.rs`.
- `first_party_artifact` inspects the archive and then reads it again to hash it, so a file replaced between the two reads would be hashed uninspected. The archive is a local file the operator names; the window was not filed.

Lockfile import reads the operator's own lockfile without a size limit. That input is local and trusted, so it was not filed.

## Types

The production measurement used `cargo clippy --offline -p mynpm --lib --bins --message-format=json` with the candidates enabled by `-W`, at the Diagnose fix commit (`e2e2f5a2`). Counts include diagnostics whose first span is under `crates/mynpm/src`; unit tests are not compiled by this command. The command exited 0 and the compiler was rustc nightly 2026-11-09. The crate has 13,048 Rust source lines in `src/`, including unit tests.

| Candidate | Diagnostics | Decision |
| --- | ---: | --- |
| `unsafe_code = forbid` | 0 | Already enforced by `#![forbid(unsafe_code)]` in each source file; no new setting. |
| `wildcard_enum_match_arm` | 10 | Reject: no witness. The sampled arms (`acquire.rs:934`, `archive.rs:74`) are open-ended: value kinds and tar entry types where every other kind is rejected or ignored. |
| `match_wildcard_for_single_variants` | 1 | Reject: `inventory.rs:583` matches a lockfile version enum where any non-npm version yields the expected version 0 and fails the comparison; naming the variants would not change behavior. |
| `cast_possible_truncation` | 2 | Reject: `hex_decode` casts `hi * 16 + lo` of two hex digits to `u8`, and its input is the crate's own lower-case digest; `renderer as u32` follows a checked renderer range. No defect witness. |
| `cast_sign_loss` | 0 | No diagnostics. |
| `unwrap_used` / `panic` outside tests | 0 / 0 | No diagnostics. |
| `expect_used` outside tests | 23 | Reject: no defect witness. Sampled sites assert a key or kind the preceding check established. |
| `indexing_slicing` | 49 | Reject: no witness; the sampled sites index fixed 64 KiB buffers and slices bounded by the preceding length checks. |
| `as_conversions` | 24 | Reject: no demonstrated defect; widening casts and byte counts. |
| `redundant_clone` | 21 | Reject: ownership suggestions do not reject an invalid type or remove a typing escape hatch. |
| `needless_pass_by_value` | 6 | Reject: same reason. |

No new profile setting was adopted and no source changed. No candidate met the required witness (a demonstrated invalid state it would reject) or removed a trust assumption. One observation is not a defect: `hex_decode` maps a non-hex digit to 0 instead of failing, but its only callers pass digests produced by `lower_hex`. The DSLP-17 change was a behavior fix and is not a typing change.

## Tests

The inventory below follows DSLP-11's named contracts and the crate README. Paths are relative to `crates/mynpm` unless they start with `crates/`. After this change the crate has 75 library tests and 9 integration tests. Test names are representative, not exhaustive.

| Contract | Guarding tests | Gap and disposition |
| --- | --- | --- |
| Lifecycle scripts stay disabled during resolution and validation | New: `resolve::tests::resolution_runs_package_managers_with_lifecycle_scripts_disabled` and `validate::tests::validation_clients_run_with_lifecycle_scripts_disabled` check the environment and the generated `npmrc`. | Gap, closed. No test mentioned `ignore-scripts` before. The command-line flags in `resolve_target` and `install_project` are built inline and still have no unit test; the environment and `npmrc` repeat the setting, so removing one layer is caught. Extracting the argument builders would change production code for a redundant check, so it was not done. |
| Tarball integrity | `acquire::tests::fetches_and_verifies_offline` and `reuses_a_first_party_artifact_pinned_as_a_registry_source` cover the stored path; `tests/metadata_only.rs::rejects_upstream_integrity_that_disagrees_with_the_lockfile` covers a metadata and lockfile disagreement. New: `a_tarball_that_differs_from_the_claimed_integrity_is_never_stored`. | Gap, closed. No test served bytes whose digest differs from the claim that both metadata and lockfile agree on. |
| Archive inspection and limits | The `archive::tests` suite covers identity, traversal, duplicate and replacement entries, multiple roots, entry types and the entry limit (`rejects_too_many_replacement_entries`, added with DSLP-17). | Retained. Size limits (1 GiB compressed, 2 GiB unpacked) have no test because the fixtures would be that large; the arithmetic is a checked sum. |
| Upstream URL policy and transfer | `acquire::tests::rejects_redirect_outside_registry`, `non_public_hosts_are_policy_errors`, `restricted_addresses`, `oversized_responses_are_limit_errors`, `exhausted_fetch_budget_is_a_limit_error`, `http_status_failures_stay_operation_errors`. | The real `HttpsExchange` (TLS, DNS) has no offline test: **Needs environment**, a local TLS origin. DSLP-18 rests on it. |
| Inventory identity and merge | `tests/inventory_identity.rs`: identity tracks platform flags, aliases and snapshot; duplicate imports do not inflate totals. `inventory_store::tests`: round trip, symlinked inventory, lock conflict, no-op update. | Retained. |
| Metadata-only versions | `tests/metadata_only.rs`: records, publication, idempotence, conflict and corrupt categories, verification. | Retained. |
| Lockfile import and CLI | `lock_npm::tests`, `lock_pnpm::tests` (v9 and v12 fixtures, bad versions, duplicates), `tests/cli.rs` (import, plan, usage and exit codes). | `doctor` has no unit tests and is exercised only through the CLI help paths. Not a demonstrated gap. |
| Publication and adoption | `publish::tests` (catalog, landing page, id stability, adoption reseal, tampered tarball, older renderer) and `crates/stuff/tests/npm_publish.rs` (12 tests). | Retained. |
| Serving compatibility | `crates/stuff-server/tests/npm_compat.rs` installs from the served registry. | Retained; real npm client versions beyond the pinned ones are outside this review. |
| Child processes | `process::tests`: timeout, output overflow, descendants that ignore TERM or hold pipes. | Retained. |

Two tests were added, each proven by one hand-injected fault that was restored byte for byte. Changing `npm_config_ignore_scripts` to `false` in `client_environment` left all 74 existing tests passing and failed the new validation test. Making `check_digests` return early made the 74 existing tests pass and failed the new integrity test. The resolution environment test has no separate fault run; it asserts the same line shape in the other module. Coverage and mutation measurement are **Needs environment**: `cargo-llvm-cov` and `cargo-mutants` were not run. No mutation lane is proposed.
