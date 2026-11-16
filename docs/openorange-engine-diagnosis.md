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

An isolated diagnostic dev build added those two error logs without changing
fence behavior. Its stripped binary SHA-256 is
`9bf96d614fbaa2ff853f254daf3a4cec59cf4421ba7cad2e897f363cfb2327d3`.
With a fresh namespace and depot, the import failed after 18,500 acknowledged
rows. At 08:33:24.672992005 UTC, the original request reported
`Overloaded { retry_after_ms: 275, token: None }`; its abort reported another
tokenless overload with a 274 ms hint. The following fence was
`staged_write_abort_failed`. Memory-limit and OOM event counts were zero.

The filesystem's retry hint proves that these errors admitted nothing.
SQLite preserved stages only for cold-read refusals, then attempted an abort
for this overload; that abort was refused too. The
[candidate patch](../deploy/openorange/patches/README.md) retains resumable
staged requests and makes their caller use the same refusal classification.
It leaves uncertain outcomes non-retryable. Both staged-request regressions
fail on the original implementation and pass with the candidate, including
resend and committed page-byte checks. The admitted-token classification test
also passes. The patch changes no persisted format.

The stripped candidate dev binary SHA-256 is
`17c537ddfe201836dce6d0d5a4193bc7984debdb00a2a7be76c370a63b68d1df`.
Its local source commit is `88fc1c449b851049d83e6318a2028d3bb0453894`,
based on the identified revision. The committed patch SHA-256 is
`a2d1d5373f097cac4541a84bd17094dbb1e482085089f0e8fd4d0b483fd2505d`.

The candidate imported 82,500 of 203,950 rows before the fixed ten-minute
cutoff. Its log contains no staged-write abort fence. The container recorded
536 memory-limit events, zero OOM events and zero OOM kills. All 180 bounded
production inventory requests made during that diagnostic returned 200.
This is partial-import evidence, not a complete import or availability gate.

A copy of the stopped candidate depot reopened with exactly 82,500 imported
rows. The first recovery probe incorrectly selected an empty manifest table;
that assertion was invalid. The corrected probe selected
`observe_external_events` and matched the acknowledged count. Exact row
equality remains unverified because the incomplete-import state cannot export
the snapshot. Existing failed depots and receipts remain intact.

Resuming that copied depot failed on its first page with HTTP 500, retaining
82,500 acknowledged rows. Application stderr reports a SQLite transaction
expired after 60,000 ms and rolled back. Its Engine log has no staged-write
abort fence, and this run recorded zero memory-limit or OOM events. This is a
separate unresolved failure; the refusal repair does not establish recovery
acceptance. Increasing that timeout without establishing the stalled
transaction's cause would not establish a repair. Full import, exact row
equality, cross-namespace identity handling and ten ordinary restart cycles
remain unverified.

Protected Lisa evidence is under
`/home/josh/d/stuff/.work/tmp/stuf87-debug-b-20261116/`,
`stuf87-refusal-d-20261116/`, and `stuf87-refusal-f-reopen-20261116/`.
Their containers are stopped. The original deployed binary and earlier failed
depots were not replaced.

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

Production work remains bounded and read-only. No production configuration,
Engine, application or sampler changed. Private containers used an isolated
network, two CPUs and 3 GiB, with preserved depots and protected credentials.
The source's Rust pin and the attested builder image were retained. The
diagnostic binaries use the dev profile; no release or performance acceptance
follows from them.
