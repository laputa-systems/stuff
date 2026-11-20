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
