# mypypi review

This review covers `crates/mypypi` at DSLP-12's base (`52c3999d` plus the mynpm commits, which do not touch this crate), with Rust nightly 2026-11-09 on macOS. It does not review the other crates, the Worker, `deploy/` scripts, repair tooling, or live services. Nothing was downloaded from PyPI or published, and no package was imported outside the crate's own sandbox tests.

## Diagnose

The review read the boundaries that take untrusted bytes or run package code: wheel and zip reading (`src/wheel_zip.rs`), wheel validation and RECORD verification (`src/validate.rs`), acquisition and download (`src/acquire.rs`), sdist inspection (`src/build.rs`), and the import sandbox (`src/sandbox.rs`, `src/process_policy.rs`) through its existing tests.

| ID | Priority | Finding | State |
| --- | --- | --- | --- |
| DSLP-19 | P2 | RECORD verification reads each wheel member whole into memory with no size limit. | Reproduced, fixed in this change set |
| DSLP-20 | P3 | Member lookups scan the member list, so validation is quadratic in the member count. | Reproduced to 20,000 members; open |

DSLP-19: `metadata_from_wheel` hashed members through `Archive::read`, which collected the whole decompressed member into a `Vec`. A generated 2.4 MB wheel with a 512 MiB zero member and a correct RECORD row was accepted after 3.4 s with a 558 MB peak resident set (155 MB for 128 MiB, so linear). Only the compressed download limit (1 GiB) applied, and deflate reaches about 1000:1. Every target runs this inspection before installing, so a hostile upstream wheel could exhaust the publisher's memory. The fix hashes through a bounded streaming reader, limits `read` to 64 MiB (every caller reads metadata, RECORD or `setup.py`), and rejects archives whose members declare more than 4 GiB in total.

DSLP-20: `Archive::member` is a linear search that `mode`, `read`, `size` and `read_prefix` call for every name. In a debug build `inspect_wheel` took 0.31 s, 0.74 s and 1.74 s for 5,000, 10,000 and 20,000 empty members. Larger counts were not measured.

Checked and not filed:

- Wheel paths. `metadata_from_wheel` and `safe_member_names` reject duplicate names, absolute paths, backslashes, NUL, `.` and `..` segments, drive-like first segments and symbolic links; `rejects_a_wheel_with_a_symbolic_link` covers links.
- Identity. The filename, METADATA name and version, `.dist-info` directory, WHEEL tags and filename tags must agree, direct-URL dependencies are rejected, and RECORD must list every file with a matching hash and size.
- Digests. `download_artifact` verifies the digest PyPI reports before the file is used, rejects unsafe filenames, and removes a download that fails. The download URL's host is not restricted to the PyPI file host, so a hostile metadata response could direct a request to another HTTPS host; the response is discarded when the digest differs, and the metadata comes from `pypi.org`, so this was not filed.
- Transfer limits. `http_get` stops reading at the caller's limit (16 MiB for JSON, 1 GiB for artifacts), unlike the npm client (DSLP-18), and bounds redirects to 5 with an HTTPS-only, credential-free check at every hop.
- Execution boundary. Import checks run inside the sandbox; `importing_a_wheel_cannot_read_publisher_files_or_write_outside_scratch` attempts a read and a write from a hostile module. The test is skipped without `uv` and a CPython interpreter, and both are present on this host, so it ran.
- sdist inspection. The tar branch bounds expanded size at 1 GiB and rejects unsafe, duplicate and non-regular members. The zip branch had no expanded-size check; the 4 GiB open limit from DSLP-19 now bounds it.

## Types

The production measurement used `cargo clippy --offline -p mypypi --lib --bins --message-format=json` with the candidates enabled by `-W`, at the DSLP-19 fix commit (`7744ea22`). Counts include diagnostics whose first span is under `crates/mypypi/src`; unit tests are not compiled by this command. The command exited 0, with rustc nightly 2026-11-09. The crate has 11,160 Rust source lines in `src/`, including unit tests.

| Candidate | Diagnostics | Decision |
| --- | ---: | --- |
| `unsafe_code = forbid` | 0 | Already enforced by `#![forbid(unsafe_code)]` in `lib.rs` and the binary root; no new setting. |
| `wildcard_enum_match_arm` | 12 | Reject: no witness. Sampled arms are open-ended string or value kinds. |
| `match_wildcard_for_single_variants` | 2 | Reject: `planner.rs:191` and `:222` pick one `UpstreamArtifact` variant with `filter_map`, and the other variant is the intended exclusion. |
| `cast_possible_truncation` | 4 | Reject: all four are `nanos as u64` in the temporary-name helper copied into four modules; the truncation only mixes bits into a name. |
| `cast_sign_loss` | 0 | No diagnostics. |
| `unwrap_used` outside tests | 11 | Reject: no defect witness. Sampled sites (`dist_infos.iter().next().unwrap()` after a length check, `pop().unwrap()` after a non-empty check) follow the check that makes them safe. |
| `expect_used` outside tests | 11 | Reject: no defect witness. |
| `indexing_slicing` | 128 | Reject: no witness; sampled sites follow length checks. |
| `as_conversions` | 29 | Reject: no demonstrated defect; widening casts and byte counts. |
| `redundant_clone` | 15 | Reject: ownership suggestions do not reject an invalid type or remove a typing escape hatch. |
| `needless_pass_by_value` | 0 | No diagnostics. |

No new profile setting was adopted and no source changed for Types. The DSLP-19 fix is a behavior change, not a typing change; it does add a bounded `Archive::read` so `Vec<u8>` of unbounded size is no longer returned for any caller.

## Tests

The inventory below follows DSLP-12's named contracts and the crate README. Paths are relative to `crates/mypypi` unless they start with `crates/`. After this change the crate has 90 library tests (3 ignored) and 10 integration tests. Test names are representative, not exhaustive.

| Contract | Guarding tests | Gap and disposition |
| --- | --- | --- |
| Release metadata and wheel selection | `acquire::tests::release_metadata_is_parsed_matched_to_identity_and_filtered_by_target`, `musl_targets_take_musllinux_wheels_and_never_manylinux_ones`; `tests/wheel_tags.rs` checks the tag ranking against `tests/fixtures/wheel_tags.json`, generated by `generate-wheel-tags.py`. | Retained. |
| Download digest verification | `download_artifact` compares the SHA-256 PyPI reports before storing a file. | Gap, not closable offline. The only HTTP path is the real TLS client with no injectable exchange, so no test serves bytes that differ from the digest. **Needs environment:** a local TLS origin. Not a demonstrated fault; the comparison is one `!=`. |
| Wheel structure, identity and RECORD | `validate::tests::rejects_a_wheel_with_a_symbolic_link`, `accepts_noncanonical_metadata_name`, `acquire::tests::validates_fixture_wheel_metadata`, `wheel_zip::tests`, and `crates/stuff/tests/pypi_first_party.rs` (a tampered RECORD is rejected before upload). New: `rejects_a_member_that_differs_from_its_record_row` (hash and size) and `verifies_a_member_larger_than_the_metadata_read_limit_against_record`. | Gap, closed. The crate's own suite had no RECORD mismatch test; only the publisher's integration test caught one. Added because DSLP-19 rewrote that code. |
| Archive limits | `wheel_zip::tests`: bounded `read`, streamed members, the declared-size limit (`open_refuses_an_archive_whose_members_declare_more_than_the_limit`). `build::tests::rejects_sdist_expanded_size_over_cap` covers the tar sdist branch. | Retained. The 4 GiB zip limit is exercised through a private constructor taking a smaller limit; a full-size archive would take minutes. |
| Python execution boundary | `sandbox::tests` (profile and bwrap arguments, deny-by-default, no network offline, publisher credentials never reach the child, links, missing programs), `process_policy::tests` (environment allowlist, scratch redirection, redaction, output caps, timeouts, descendants), `validate::tests::importing_a_wheel_cannot_read_publisher_files_or_write_outside_scratch`, `build::tests::a_build_backend_cannot_read_publisher_files_or_write_outside_scratch`. | Retained. These ran on this host (macOS Seatbelt). The bwrap path is covered by argument-level tests only: **Needs environment**, a Linux host. |
| Native-target execution checks | `validate::tests::importing_a_benign_wheel_succeeds_inside_the_boundary` installs and imports a wheel for the local target. Native sdist and repair tests are `#[ignore]`d and run by `deploy/test-mypypi-native.sh` and `deploy/ecosystem-smoke.sh`. | **Needs environment:** repair tooling, a native compiler and network. The three ignored tests were not run. The execution check itself is unchanged. |
| sdist inspection | `build::tests::rejects_sdist_member_traversal`, `rejects_duplicate_sdist_members`, `inspects_valid_tar_sdist`, and the `build_requires_*` tests. | Retained. |
| Publication and CLI | `tests/publish.rs` (3), `tests/cli.rs` (6), `crates/stuff/tests/pypi_publish.rs` and `pypi_first_party.rs`. | Retained. |

One test was added to close a gap and was proven by one hand-injected fault, restored byte for byte. Changing the RECORD comparison to `if false && computed != *expected_digest` left the other 86 passing library tests green and failed the new test; `cargo test -p stuff --test pypi_first_party` also failed under the same fault, so the publisher's integration test already covered it. The other three tests added in this review guard DSLP-19 (the bounded read failed first on the old code) and the streaming path. Coverage and mutation measurement are **Needs environment**: `cargo-llvm-cov` and `cargo-mutants` were not run. No mutation lane is proposed.

## Dead code

`cargo rustc -p mypypi --lib -- --force-warn dead_code --force-warn unreachable_pub` exited 0. Before the removals it reported one `dead_code` warning and ten `unreachable_pub` warnings (nine in `wheel_zip.rs`, one in `publish.rs`); afterwards only the ten `unreachable_pub` warnings remain. The `wheel_zip` module is private to the crate and the `publish.rs` item is `TempScope::create`, a method of a `pub(crate)` type, so those are only a `pub` spelling and no code is dead.

The compiler could not see unused items in the `pub` modules, so a reference count over every Rust file under `crates/` found them. Eight items had no caller, in the crate, the other crates, `deploy/`, or `docs/`, and were removed:

- `acquire::CompatibilityRejection::to_error`, `add::resolve_dependencies` and `add::canonical_pin`.
- `build::validate_wheel_identity`: the same filename and identity checks run in `acquire::validate_wheel_metadata_at`.
- `index::Index::targets_sorted`, `process_policy::check_captured`, and `validate::canonical_package_name`.
- `validate::version_parse_unused`, an `#[allow(dead_code)]` function whose name says it is unused.

Removing them left three imports unused and they were removed too. Four identical copies of a temporary-name helper (`rand_u64` in `acquire.rs`, `rand_hex` in `build.rs`, `publish.rs` and `store.rs`) became one `unique_u64` in `lib.rs`; the expression is unchanged. In total the change deletes 84 lines net. `cargo clippy -p mypypi --all-targets`, `cargo check -p stuff --all-targets` and `cargo test -p mypypi` passed afterwards. The scan covers the crate's current target and configuration and cannot see consumers outside this repository; the crate is not a published API (`stuff` is its only dependent).
