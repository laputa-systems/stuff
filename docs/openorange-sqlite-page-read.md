# Committed SQLite page-read refusal

The private polling/import failure reaches the native SQLite durability flusher
through `probe_depot_head` → `get_pages`. Its captured error is:

```text
sqlite flusher aborted: read sqlite head: volume log mutation failed: QuorumUnavailable { token: None }
```

The filesystem's generic `Log` display says “mutation” for read failures too.
The volume client's `read_committed` returns this tokenless error after none of
its eligible replicas serves the bounded read. It does not establish an
uncertain write. The page protocol previously treated it as fatal and aborted
any staged transaction before returning it to the flusher.

## Repair boundary

`rivet-e5ed391-page-read-refusal.patch` applies after the three staged-write
patches in [the patch directory](../deploy/openorange/patches/README.md).
It classifies this error only when executing `SqliteGetPagesRequest` and the
filesystem still has valid ownership. A private error context retains the
original structured cause. It preserves the stage and supplies the existing
100-ms overload hint to the Envoy's existing bounded identical-request retry.
The ten-second request refusal budget and ownership guard are unchanged.

Writes, admitted tokens, fenced owners and other error categories retain their
existing behavior. Exhausting the retry budget still abandons the retained
stage. No persisted format, ownership lease, wire response or public API
changes. The existing `depot-volume` dependency moves from test-only to an
explicit regular edge; `depot-client` already includes it. There is no new
package or version in the lockfile and no additional transitive runtime crate.

## Source verification

The combined source is `f68e0732f44c1d0ec64e96dc425f585eeef8c255`.
The new patch SHA-256 is
`c756a9f95c64a00bf5fac77e9bf96205ffd4a16c10b009fe0286448c91e5b769`.
It applies to the attested `e5ed3911` source after the three SQLite patches;
the resulting filesystem package matches the tested source exactly.
The combined runtime also includes the separately staged inventory and
lifecycle API patches.

The regression uses the real filesystem and page protocol with an injected
journal. A zero-byte row cache forces a committed page to be read through
that journal while another staged transaction exists. Before the repair,
the injected read reaches the journal and fails because the protocol gives
no retry hint. Afterward, the same request retains the stage without admitting
another write, then reads the exact committed page and completes the stage.

Eight tests pass in dev and release with the attested builder, Rust 1.99.0,
`RUSTFLAGS='--cfg tokio_unstable'` and four build jobs:

```sh
cargo test --locked --offline -j4 -p sqlite-embedded-filesystem --test staged_refusal
cargo test --release --locked --offline -j4 -p sqlite-embedded-filesystem --test staged_refusal
```

The tests also inject an admitted-token read error, ownership loss during the
read, an explicit fence and a tokenless failure during finalize. These do not
receive the new read-refusal classification. Existing abort/fence regressions
remain in the same suite. The independent source review found no demonstrated
introduced defect; it inspected the filesystem status, prefetch path and Envoy
retry caller but did not execute builds or tests.

Three hand faults remove the read scope, ownership check and admitted-token
restriction separately. Each fails its intended safeguard regression; restoring
the source returns the full eight-test suite to green. The release Engine
build passes. Its unstripped binary SHA-256 is
`611b08f609d625ad5379c3b0801f23fc76ab4e17cc3ee0210ba608bf53ae1b01`
and its file size is 81,276,368 bytes. Earlier private candidate binaries were
stripped, so their raw file sizes are not comparable to this artifact.

The protected failed S depot remains unchanged. Production Engine,
applications and collectors have not been replaced or restarted.

## Fresh private import

V starts with an empty depot, new namespace and credentials, the frozen Stats
image and corpus, two CPUs, 3 GiB, 500-row pages and 250-ms pacing. It additionally
runs the same one-second inventory sweeps that exposed S's failure. All 203,950
rows are acknowledged; import exits 0 within its 1,800-second bound. The fixture
verifies the manifest, four complete reference windows, 64 duplicate rows,
changed-duplicate HTTP 409 and an equal summary after application reopen.

All 4,617 inventory requests across 521 sweeps succeed. The cgroup records
13,303 memory-limit events, zero OOMs and zero kills. This is private correctness
and short-run inventory evidence; it is not throughput or 24-hour availability
acceptance. Protected receipts and the stopped depot remain under
`/home/josh/d/stuff/.work/tmp/stuf87-log-read-v-20261116/`.

W's restart preflight runs immediately after import and returns busy (75),
with host load 5.64–5.83 on eight cores. No restart or timing measurement starts.
Its zero-cycle receipt remains unchanged; it contributes no accepted cycles.

## Three Engine-only recoveries

X's initial comparison used M's summary despite V's fresh import shifting
its event timestamps. The exact-equality assertion rejected that mismatched
reference before any restart cycle. The failed receipt remains intact.
For Y, the reference is derived from M using the difference between the two
recorded import shifts (14,219,891 ms), changing only `atMs`, `firstAtMs`,
`lastAtMs`, `fromMs` and `toMs`. The corpus is identical; the fixture's
reference algorithm bins relative to `fromMs`, so counters and durations
remain unchanged. The assertion still compares the entire summary exactly.

Y completes exactly three consecutive Engine-only TERM/start cycles, with
60 seconds of idle spacing. The application and Envoy stay alive. All six
pre/post host gates return zero, and no stop requires a forced kill. Every
cycle recovers all 203,950 events with the same complete summary SHA-256:
`a9a234561d978bd7decbef26e124327d5def3411f41d3df7ba804f8a4978717f`.

| Cycle | Start to verified data | Shutdown to verified data |
| --- | ---: | ---: |
| 1 | 2.631 s | 3.919 s |
| 2 | 2.555 s | 3.847 s |
| 3 | 4.470 s | 5.780 s |

Both boundaries meet 15 seconds on every cycle. The third query first hits
its two-second per-request timeout, then succeeds within the unchanged total
recovery limit; its attempts remain in the proof. All cycle memory counters,
including limit events, OOMs and kills, are zero. The container is stopped.
This satisfies the owner's revised three-restart private recovery requirement.
It does not establish continuous production availability or alter the earlier
incomplete ten-cycle receipts.

The separate U metadata probe in the [lifecycle change](https://github.com/laputa-systems/stuff/pull/38)
resolves the same-actor-ID concern: the other namespace returns 404 before
creation, then creating the same key intentionally produces the same keyed ID
with a distinct namespace and creation time. The original actor's identity
remains unchanged. This covers actor metadata and resolution; cross-namespace
SQLite writes were not exercised by that probe.

[The sanitized proof](openorange-sqlite-page-read-proof.json) contains the
source/binary identity, import integrity, short-run inventory and all three
recovery records. Full logs and unchanged W/X/Y receipts remain in V's
protected directory. STUF-87's private import/recovery defect is resolved;
STUF-88's 24-hour production availability qualification remains open.
