# Retired component findings: reconciliation, 2026-11-21

`d7898dd8` deleted the shared-crates, myoci and stuff-worker deslop reports while ten P3
findings in them were still open. Read them with `git show d7898dd8^:docs/deslop-<name>.md`, where
`<name>` is `shared-crates`, `myoci` or `stuff-worker`.
Each finding was revalidated against `d51b2786`. It is classified as one of:

- **Reproduced:** observed with a test or probe.
- **Lead:** read from the code and not reproduced.
- **Design:** a type or structure concern with no defect.

Each finding is now a TODO ticket or is dismissed below. Severity changed only after reproduction.

| Source | Finding | Class on `d51b2786` | Disposition |
| --- | --- | --- | --- |
| shared-crates | mymirror `TarGzip` buffers a member before the cap | Reproduced | STUF-105, P3 |
| shared-crates | mymirror IPv6 filter omits `::1` and `::` | Reproduced | STUF-108, P3 |
| shared-crates | stuff-server `match_route` sees the query; untrimmed prefix | Reproduced (query); untrimmed prefix dismissed | STUF-111, P4 |
| shared-crates | stuff-http `parse_range` accepts `+` | Reproduced | STUF-112, P4 |
| myoci | `read_chunked_body` lines have no cap | Reproduced | STUF-106, P3 |
| myoci | `walk_descriptor` has no depth cap | Reproduced | STUF-107, P3 |
| myoci | `upload_r2` staging leak; manual `active` decrement | Lead | STUF-109, P3 |
| myoci | `ObjectReport` is an option soup | Design | Dismissed |
| stuff-worker | DSLP-15-1 UTF-16 `content-length` | Reproduced mismatch, no observed impact | STUF-113, P4 |
| stuff-worker | DSLP-15-2 `immutableText` leaves the body open | Lead | STUF-110, P3 |

The resource-bound findings were reproduced first. STUF-105, STUF-106 and STUF-107 keep P3: each
is reachable only after a digest pin, the push token, or a publisher import. STUF-109 and STUF-110
are unreproduced resource leads, so their P3 stands until a reproduction supports a change. The
three P4s were reproduced, but each has a narrow effect: a misrouted bare-prefix query, a lenient
range grammar, and a header the runtime normalizes.

## Dismissed

- **`ObjectReport` (`crates/myoci/src/mirror/plan.rs`).** `graph: &'static str` and five
  `Option<u64>` fields encode two states, and `render_text`/`render_json` unwrap them nine times.
  All three constructors (lines 189, 200, 238) set every option exactly when `graph` is `"known"`,
  so no unwrap can fail. This is a representation preference with no defect or consumer;
  revisit only if a fourth constructor appears.
- **Untrimmed prefix in a directly constructed `Config`.** `main.rs` trims every route prefix, and
  only unit tests build `Config` by hand.

## Reproductions

The reproductions ran as throwaway tests in a scratch worktree at `d51b2786` (debug profile,
macOS arm64). To repeat one, add the test to the named module and run
`cargo test -p <crate> --lib <name> -- --nocapture`.

- **STUF-105 (`mymirror::archive`).**
  - Fixture: a GNU tar with one regular member of `MAX_DECOMPRESSED + 512 MiB` zero bytes,
    gzip-compressed with `Compression::fast()` (7,328,411 bytes), passed to `tar_members` with a
    `.tar.gz` artifact.
  - Result: the call returned an error after 10.3 s. `/usr/bin/time -l` on the test binary
    reported a peak RSS of 1,091,158,016 bytes.
- **STUF-106 (`myoci::push`).**
  - Fixture: a loopback client writes 256 × 1 MiB of `b'1'` with no newline, then closes.
  - Result: `read_chunked_body(&mut server, b"", 1024)` returned `SizeInvalid`, and the client's
    writes all succeeded (`sent=268435456`), so the server consumed all of it.
- **STUF-107 (`myoci::import`).**
  - Fixture: a layout of N distinct nested index manifests ending in an empty index, walked by
    `walk_descriptor` on a thread with an 8 MiB stack.
  - Result: N = 1,000 returned 1,000 manifests. N = 10,000 and N = 50,000 aborted with
    `has overflowed its stack`.
- **STUF-108 (`mymirror::acquire`).** `is_restricted_address` returned false for `::1` and `::`
  and true for `127.0.0.1`.
- **STUF-111 (`stuff-server::config`).** With the test `cfg()` routes, `match_route("/mirror?x=1")`
  returned route `""` with rest `/mirror?x=1`.
- **STUF-112 (`stuff-http::condition`).** `parse_range("bytes=+0-+1", 10)` returned
  `Ok([RangeRequest { start: 0, end_inclusive: 1 }])`.
- **STUF-113.** The `workerd` probe is recorded in `d7898dd8^:docs/deslop-stuff-worker.md`, and
  lines 378 and 752 of `entry.ts` are unchanged.
