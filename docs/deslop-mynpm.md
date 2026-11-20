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
