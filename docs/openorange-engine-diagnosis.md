# Engine durability and lifecycle diagnosis

Live topic: [OpenOrange shared host stack](openorange-runtime.md).

This record identifies the deployed source and preserves the failed private
attempts. The verified private SQLite repair and three-restart proof are in
[the page-read diagnosis](openorange-sqlite-page-read.md). Production inventory
availability remains unqualified. STUF-75 is outside this investigation.

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
which registers `/pools`. Reading only
[`api-public/src/router.rs`](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/engine/packages/api-public/src/router.rs),
which registers `/runner-pools`, incorrectly suggests a source mismatch.

A read-only 2026-11-14 inspection of the running image found no OCI revision
label. Authenticated GETs returned 200 for `/namespaces`, `/pools`,
`/pools/default/nodes`, `/actors/names` and a name-filtered actor list;
`/health` needed no authentication. `/runner-pools` and `/ui` returned 404, and
an actor list with only a namespace returned 400. These are observations of
that date, not a guarantee for other routes.

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

A release-profile build of the same refusal candidate failed at 138,500
acknowledged rows. Its log records `SQLite stage fenced`, followed by a
tokenless overload refusal of the abort. The container recorded 470
memory-limit events, zero OOM events and zero OOM kills. This disproves
complete-import acceptance for that candidate beyond the earlier cutoff.

A stopped-depot copy reopened with 139,000 imported rows and reached
160,000 acknowledged rows before failing again. The extra 500 rows match
one page that could commit before its response failed; they do not show a
lost acknowledged write. Diagnostic source
`8e8698cfee2518fa51fc3644c6906790314728bc` records, at
2026-11-16 11:02:04 UTC, the SQLite head changing from 24,766 to 24,917
while a stage remained open. Its first segment had matching stage and
request IDs, 24,767, and no previously accepted segments. The head check,
rather than a request-ID mismatch, rejected it. The abort then returned
`Overloaded { retry_after_ms: 1484, token: None }`. This run recorded
77 memory-limit events and zero OOM events or kills.

Source inspection found a corresponding race: stage-begin reads the committed
head before acquiring its filesystem transaction. Acquisition can settle an
older undecided commit, making that head stale. A deterministic regression
holds a prior finalize undecided, lets the next acquisition barrier settle
it, and demonstrates that stage-begin accepts the obsolete head. The candidate
at local source commit `b99b9d4` reads and checks the head again after acquiring
the inode footprint. The regression then rejects the stale request through
the existing head-fence error and permits a subsequent valid staged commit.
All four staged-write regressions pass in the dev profile. This establishes
a source defect that fits the diagnostic sequence; a full isolated import
and restart proof must still establish whether it resolves the observed run.

The release build of that source also passes all four regressions. Its binary
SHA-256 is `e1cf359f16c2a442388603170c68553579dc6e5223eed928e73929bbebc0646b`;
the additional patch SHA-256 is
`f94e5474e879b225b2bcb6873c4cea2f9debf1207b8d41b94e7c9ad86a379732`.
A new copy of the stopped depot recovered 160,500 rows against the previous
160,000-row acknowledgment, then completed all 203,950 rows with the same
two-CPU, 3-GiB limits and 500-row/250-ms pacing. Preparation exited zero
inside its fixed 1,200-second budget. The manifest row hash matched, all
four reference windows matched, 64 duplicate events were recognized, a
changed duplicate returned 409, and a separate application stop/start
returned the identical summary. The container recorded 1,635 memory-limit
events, zero OOM events and zero OOM kills. These are correctness results;
the initial source image's build profile and performance parity remain
unproven. A fresh import from zero, ten Engine restarts and cross-namespace
identity handling remain open.

This completed copy and its protected preparation proof are under
`/home/josh/d/stuff/.work/tmp/stuf87-stage-head-i-20261116/`. Its container
is stopped. A read-only check still finds the shared Engine's original
binary hash and its 2026-11-14 21:48:02 UTC start time.

A fresh, empty-depot run of the two-patch candidate failed at 138,000
acknowledged rows. It recorded no memory-limit or OOM events. At
12:26:50 UTC, the head recheck returned `SQLite head fence mismatch`, but
cleanup of the newly acquired empty stage attempted a journal abort that
was refused with `Overloaded { retry_after_ms: 1102, token: None }`.
That still fenced the volume. The copied-depot completion therefore does
not establish fresh-import acceptance. The stopped evidence is under
`/home/josh/d/stuff/.work/tmp/stuf87-fresh-l-20261116/`. A preceding K
preflight had wrong file ownership and never started the Engine or imported
rows; it remains separate from this runtime failure.

The third candidate, local source `40ed954dc6a409c19c1cd72d6459ccf56b241580`,
removes an empty transaction's local reservation after reconciliation has
resolved uncertain admissions. No durable transaction entry exists in that
case. An admitted segment still requires a journal abort. The strengthened
head-race regression fails before this change by observing an unwanted abort
admission; all five regressions pass in dev afterward. Its patch SHA-256 is
`d2074588cf857f41c47b620ad8303562702e8f386bfe2cda58c6e458399cda02`.
All five regressions also pass in release, and the full release Engine builds.
The binary SHA-256 is
`45f20f1d38c7f34414ff6e344346cf775980ae51b1d1dd365c4c40cc50d156e6`.
All three patches apply in sequence to a clean checkout of the attested base.

The fresh M fixture starts with an empty depot and new namespace and credentials.
It acknowledges all 203,950 rows in 602.182 seconds, exits successfully within
its 1,800-second bound, and writes the preparation proof after manifest,
reference-window, duplicate/conflict and application-reopen checks. Its 2-CPU,
3-GiB cgroup records 4,160 memory-limit events, zero OOM events and zero kills;
socket throttling is four. This establishes fresh-import correctness for this
private candidate, not a performance or production acceptance. The stopped
fixture is `/home/josh/d/stuff/.work/tmp/stuf87-fresh-m-20261116/`.

A copied-depot restart attempt N verifies the complete summary but stops before
its first restart because the host gate returns 75. It contributes zero accepted
cycles. Its 14.402-second initial query is diagnostic only. Both stop-to-data
and start-to-data boundaries remain required in the next bounded receipt;
failed or busy-host evidence is never converted into a pass.

Whole-container diagnostic O completed ten data-equal restart cycles. Every
cycle passed both host gates, but start-to-data took 44.939–46.033 seconds
and shutdown-to-data 47.090–47.527 seconds: neither meets 15 seconds. Engine
API readiness was 1.962–8.724 seconds. This boundary also replaces the
application and its Envoy. Logs show failed stop commands, then expiry of
the old Envoy's lost threshold before the actor restarts. The source's
`envoy_check.rs` and actor executor retain that lease protection. Shortening
it to pass this diagnostic would change ownership semantics.

The Engine-only diagnostics preserve the application and Envoy while an
owned supervisor stops and starts only the frozen Engine wrapper. Ordinary
TERM completion, a changed child PID, no forced kill, exact summary equality,
both readiness boundaries and pre/post host gates are recorded per cycle.
P has four valid cycles: start-to-data 2.325–6.092 seconds and shutdown-to-data
3.627–7.785 seconds. Its fifth cycle was invalidated by a busy post gate.
R adds 60 seconds of idle spacing and has three valid cycles: 4.646–8.057
and 5.989–9.422 seconds, respectively. Its fourth cycle was also invalidated
by the post gate. Neither receipt is complete or establishes the required
ten-cycle acceptance; valid cycles from separate runs are not combined.
Q failed a supervisor-file preflight and started no Engine or cycles.

The owner subsequently reduced the required count to three restarts. R's
first three consecutive cycles each have equal data and passing pre/post
host gates, and meet 15 seconds at both boundaries: start-to-data
5.686/8.057/4.646 seconds and shutdown-to-data 7.002/9.422/5.989 seconds.
Those cycles satisfy the revised restart requirement for source `40ed954d`.
The original ten-cycle receipt remains incomplete; its fourth busy-host
cycle is excluded. No raw receipt or timing sample was rewritten.

The protected restart receipts and logs remain in
`/home/josh/d/stuff/.work/tmp/stuf87-restart-n-20261116/`, with separate
O/P/Q/R filenames. All these private containers are stopped.

The later inventory-edge candidate `dc461cb` was exercised with a fresh
depot and one-second inventory sweeps during import, rather than the original
sixty-second collection interval. All 3,031 inventory requests succeeded,
but import stopped at 138,500 acknowledged rows with HTTP 500. Engine warnings
report `volume log mutation failed: QuorumUnavailable { token: None }`, with
no staged-abort-fence message. There were 4,580 memory-limit events, zero OOM
events and zero kills. The stopped fixture and receipt are under
`/home/josh/d/stuff/.work/tmp/stuf88-inventory-s-20261116/`.
This establishes an unresolved failure under the additional polling load;
its cause and attribution to the candidate remain unproven. It does not
replace the original canonical import/restart evidence or establish 24-hour
availability. The failed depot is preserved and has not been retried.

The first restart diagnostic recovered an equal 203,950-event summary, then
failed the first stop-inclusive 15-second cycle. Shutdown took 7.182 seconds
and the Engine API became ready 6.222 seconds after start; application-data
readiness did not finish in the remaining budget. This does not provide ten
accepted restarts. The existing fixture reports start-to-ready separately
from shutdown, so both boundaries must remain explicit. Protected evidence
is under `/home/josh/d/stuff/.work/tmp/stuf87-restart-j-20261116/`; it is stopped.

Repeated actor IDs alone are expected in the identified grouped layout:
`pegboard::actor_key::keyed_actor_id` hashes the actor name and key, while
`KeyedActor` retains the namespace group separately. Actor state-volume keys
include that group, and each Envoy SQLite session table belongs to one
connection's namespace group. API resolution uses the request namespace.
Source inspection therefore does not establish a cross-namespace defect
from the repeated ID. A same-Engine runtime isolation check remains unrun.

Protected Lisa evidence is under
`/home/josh/d/stuff/.work/tmp/stuf87-debug-b-20261116/`,
`stuf87-refusal-d-20261116/`, and `stuf87-refusal-f-reopen-20261116/`.
Their containers are stopped. The original deployed binary and earlier failed
depots were not replaced.

The additional stopped-depot evidence is under
`/home/josh/d/stuff/.work/tmp/stuf87-release-g-20261116/` and
`stuf87-head-h-20261116/`.

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

The subsequent bounded, read-only collector preserves each failed endpoint,
HTTP status, safe error code, retry header and protected error body. At sample
73 on 2026-11-16 it captured three actor-list failures: observation-store,
the Stats cron actor and the observation cron actor each returned HTTP 503,
`x-rivet-error: depot.overloaded` and `Retry-After: 1`. The other six
requests succeeded. This classifies these new failures, not the historical
samples. Evidence remains under the protected Lisa directory
`/home/josh/d/stuff/.work/tmp/stuf88-inventory-v2-20261116/`. Its 24-hour
collection remains in progress and has already failed the zero-unavailability
criterion; no retry substitutes for a failed sample.

Inspection of 42 retained failure bodies classifies all of them as
`volume_transition`, with a 100-ms storage retry hint. The public response
rounds that to `Retry-After: 1`. The source already shares a bounded gateway
retry budget with actor creation, but actor inventory routes do not use its
storage-step retry helper. A supported read-edge repair still needs explicit
request bounds, regression coverage and runtime verification; collector-side
retries cannot turn these failed samples into availability acceptance.

## Investigation boundary

The native flusher log narrows the later S error to a committed page read.
[The page-read diagnosis](openorange-sqlite-page-read.md) records its
deterministic regression, narrow retry classification and verification.

Production work remains bounded and read-only. No production configuration,
Engine, application or sampler changed. Private containers used an isolated
network, two CPUs and 3 GiB, with preserved depots and protected credentials.
The source's Rust pin and the attested builder image were retained. The
initial diagnostic binaries use the dev profile. Later release-profile
diagnostics retain the same resource bounds; no performance acceptance follows
from these failure investigations. The deployed image's exact build profile
has not been independently established.
