# Engine durability and lifecycle diagnosis

STUF-86, STUF-87 and STUF-88 remain open. The observations below identify
the deployed source and narrow the investigation. They establish no repair.
STUF-75 is outside this investigation.

## Source identity

The pinned Engine image index is
`sha256:6e585002b700dd4d3630808eb67884aa15d1a602d83781984edac47023b6d40f`.
Its AMD64 manifest is
`sha256:66de9f77cde47be3cd7af2c001e8083784f6b91ca58b0ab5d7878677cff5bd5d`.
The index attaches attestation manifest
`sha256:28335a94f83677b5ec6f4ff13ebd8cdd38b6ba62870bccc7f8078e3e5f67c4de`
to that AMD64 manifest.

The attached BuildKit provenance names
`https://github.com/rivet-dev/rivet` and revision
`e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9` in
`runDetails.metadata.buildkit_metadata.vcs`. Its build finished on
2026-11-12 at 01:08:52 UTC. This is attached build metadata, not an
independently reproduced build or a verified publisher signature.

The running `oo-engine` binary at `/usr/bin/rivet-engine` hashes to
`0b6e8c031ce2d2d3259b540a4ae55c6f8d4bb367001406110ce5dc62bcd7357f`.
That matches the preserved private fixture binary. The production container
still reports its original start time, 2026-11-14 at 21:48:02 UTC.

Read the attached provenance with:

```sh
docker buildx imagetools inspect \
  docker.io/rivetdev/engine@sha256:6e585002b700dd4d3630808eb67884aa15d1a602d83781984edac47023b6d40f \
  --format '{{json .Provenance}}' |
  jaq 'map_values(.SLSA.runDetails.metadata.buildkit_metadata.vcs)'
```

The source contains two API routers. The deployed V3 contract matches
[`api-public-shim/src/lib.rs`](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/engine/packages/api-public-shim/src/lib.rs),
which registers `/pools`. Reading only `api-public/src/router.rs`, which
registers `/runner-pools`, incorrectly suggests a source mismatch.

## Lifecycle timestamps

[`actor_json`](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/engine/packages/api-public-shim/src/routes.rs#L2604)
explicitly emits null `start_ts`, `pending_allocation_ts`,
`connectable_ts`, `sleep_ts` and `reschedule_ts`. Its contract says V3
does not record those times. Repeating the actor-list request cannot
produce the positive transition evidence STUF-86 requires. The explorer
must preserve those unknown values.

The source has actor phases and epochs internally, but this public
projection does not expose them. A positive lifecycle signal needs a
supported runtime or application boundary and a natural idle transition.
Aggregate metrics, elapsed idle time and a forced restart do not establish
that transition for one observation-store actor.

## Filesystem fence

The preserved fresh fixture log records `staged_write_abort_failed` at
2026-11-16 04:16:08.100150489 UTC. Its application stderr reports
`durability_failed` and a database volume fenced for epoch 0. These are
the terminal errors, not the first failing storage operation.

In the identified source,
[`page_protocol::execute`](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/engine/packages/sqlite-embedded-filesystem/src/page_protocol/mod.rs)
fences after a failed request also fails to abort its staged transaction.
`abandon_stage` emits the same fence reason when its abort fails. Neither
site logs the abort error. The reason alone does not distinguish the two
callers or establish why the abort failed.

The next isolated reproduction needs both the original request error and
the abort error at these boundaries. Increasing timeouts, reducing import
page sizes or disabling fencing without that evidence would not establish
a repair. Existing failed depots and acknowledged-row receipts must remain
intact. Exact row recovery and ten restart cycles remain unverified.

## Inventory availability

The stopped production soak contains 628 samples. Ninety-two have an
actor-inventory HTTP 503. One other sample, index 30, has an application
timeout. The end record reports 93 degraded samples and `complete: false`.
The sampler records no failed actor endpoint, error body or retry header,
so those historical 503s cannot be assigned to a particular actor name.

The retained production Engine log contains `filesystem_overloaded`
alarm warnings around 16:51 UTC, during failed sample 10. This correlation
does not prove that the inventory request met the same refusal.

Ten current read-only sweeps each requested names and the first page for
all eight names. All 90 requests returned 200. This did not reproduce the
historical failure and does not establish continuous availability.

The identified API shim maps read-side `depot.overloaded` and
`actor.fork_unavailable` refusals to HTTP 503. Those are candidate causes,
not classifications of the historical samples. A diagnostic collection
must preserve endpoint, group, status, safe error code and retry hint at
failure time. It must retain failed samples rather than replace them with
retries or cached success. A complete 24-hour collection with zero
unavailable groups remains required.

## Investigation boundary

This investigation read existing logs, image metadata and source. It made
only bounded read-only requests to production. It changed no production
configuration, restarted no Engine or application, and started no import
or sampler. No runtime test or performance acceptance follows from these
observations.
