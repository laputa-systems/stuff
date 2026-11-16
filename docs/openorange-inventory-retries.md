# Engine inventory refusal repair

The protected inventory collector captured HTTP 503 responses with
`depot.overloaded`, reason `volume_transition`, storage hint 100 ms and
`Retry-After: 1`. These classify new failures; they do not classify the old
soak's 93 degraded samples. The current collection has already failed its
zero-unavailability criterion. Keep its failed samples.

The candidate patch is
`deploy/openorange/patches/rivet-e5ed391-inventory-read.patch`, SHA-256
`4ed8deee5eb7fc9681cc9155ebba75cd87c08cb00105f486a2808cb948fd9b6f`.
It changes the attested Engine source `e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9`.
The local candidate commit is `dc461cb78b2ca61d624d9305249324ca0ee7d430`,
whose parent also contains the separately reviewed private SQLite repairs.
The inventory patch contains only its own three-file change and can be
reviewed independently of those repairs.

## Boundary and behavior

`GET /actors` and `GET /actors/names` retry through the gateway's existing
process-wide `RetryBudget`. The existing refusal classifier, four-retry cap,
retry hints, backoff and process token limit remain the owners. An uncertain
`depot.unavailable` is returned immediately. Exhaustion preserves the original
error and retry hint. A three-second deadline bounds the entire inventory
read, including retries, below the explorer and collector's four-second
upstream timeout. A stalled read returns the existing
`depot.request_deadline_exceeded`; it does not report success or cached data.

Query parameters, namespace authorization, actor filtering, pagination,
cursor encoding and response bodies are unchanged. Each attempt computes a
whole response; no partial page is combined with another attempt. The existing
create helper now takes the environment directly and has a storage-oriented
name; its create call sites retain the same retries, body, actor identity,
submission tracking and thirty-second deadline.

The HTTP boundary owns this retry because it can limit complete read requests
and share the existing admission budget. Collector retries would conceal
unavailable samples. Storage-layer retries would broaden mutation semantics
and compete with the existing budget. Neither is part of this candidate.

## Verification and remaining proof

Seven tests pass in dev and release on Linux x86-64 with the attested builder,
Rust 1.99.0, locked offline dependencies and default package features:

```sh
cargo test --locked --offline -j4 -p rivet-api-public-shim inventory_tests -- --nocapture
cargo test --locked --offline --release -j4 -p rivet-api-public-shim inventory_tests -- --nocapture
```

They assert a whole page and its original cursor after two refusals, immediate
uncertain-error propagation, the per-request cap, process-budget sharing,
rejection of an unserviceable hint, the deadline error, and actual HTTP
middleware status/header/body behavior. GET remains 503 and POST remains 400
for an exhausted overload, with `x-rivet-error`, `Retry-After` and metadata
preserved. This POST is a test fixture for the existing middleware contract;
no mutating production route uses the new inventory wrapper.

Hand faults removing retries, replacing the shared budget with a private
budget and mapping timeout to the wrong error each fail the intended test
assertion. All seven tests pass after restoration. Tower's `util` feature is
a test-only edge to version 0.5.3 already locked and used by Axum: no package,
version or shipped dependency is added. Its existing MIT-licensed service
test adapter exercises the actual router and middleware without opening a
listener or implementing another HTTP test stack.

A source reviewer inspected the retry and timeout owners, authorization and
read paths, and found no supported defect, but its review is incomplete:
the reviewer lacked the commit diff and its one-attempt limit prevented a
correction. Parent inspection covers the complete diff; do not describe this
as a completed independent diff review. The full private release build succeeds.
Its stripped x86-64 binary is 68,746,408 bytes, SHA-256
`77321ee6d4455d6e6e9b3f9421d54c98c9b236084fc7f0fae74f109fea8a8496`.
The natural-refusal runtime comparison and complete 24-hour qualified collection
remain outstanding. STUF-88 stays open. No production binary, application,
sampler or shared Engine has changed.

The subsequent private S run adds one-second inventory sweeps during a fresh
canonical import, versus the original sixty-second collection interval. All
3,031 inventory requests succeeded, but the import failed at 138,500
acknowledged rows with `QuorumUnavailable { token: None }`. The container
recorded 4,580 memory-limit events, zero OOM events and zero kills. It is
stopped, with its failed depot and receipts preserved under
`/home/josh/d/stuff/.work/tmp/stuf88-inventory-s-20261116/`. No inventory retry
event was captured, so this hot-polling run does not establish a natural cold
refusal comparison. Its import failure's cause and candidate attribution
remain open. Neither this run nor the successful lifecycle probe is a
qualified 24-hour availability collection.
