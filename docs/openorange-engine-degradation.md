# Engine degradation under host CPU saturation

Reference record for the 2026-11-21 Stats incident: host CPU saturated, 4-vCPU
guest, Engine refusals in sequence ending in
`RivetKit registry did not register with the Engine within 30000ms`.

Every Engine claim below cites a file at Rivet
`e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9`; every open-orange claim cites a file
at `1cabf2e9db300361c9f0b751c7723da7eb706f5e` (the revision `deploy/openorange`
resolves, `deploy/openorange/sources/sources.toml:90`). Paths are
repository-relative to those trees.

## Source identity

The resolved ambiguity in the brief: the owned build revision and "3.1.2-rc.1"
are the same commit, not alternatives.

- `e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9` is exactly tag `v3.1.2-rc.1`
  (verified by `git rev-parse v3.1.2-rc.1^{commit}`).
- Its workspace version is `3.1.1` (`Cargo.toml:82`), which is why the deployed
  binary reports `Rivet 3.1.1` while the image tag is `3.1.2-rc.1`
  (`docs/openorange-runtime.md:32-41`, `sources.toml:124-125`).
- The image's attached BuildKit provenance names the same revision
  (`docs/openorange-engine-diagnosis.md:18-23`).

Read: Rivet source at `e5ed3911` (= `v3.1.2-rc.1`). Not read: the image
manifest itself, or any later tag (`v3.1.2-rc.2`..`-rc.5`).

## 1. Depot command deadlines

Set per command, overridable by one floor, and enforced twice (client and host).

- Trait default: `Command::TIMEOUT = 5 s`
  (`engine/sdks/rust/depot-protocol/src/command.rs:45`). This is the only
  `const TIMEOUT: Duration` in `engine/`; no `impl Command for` overrides it.
  The config doc advertises "5 seconds generic, 30 seconds for actor storage"
  (`engine/packages/config/src/config/depot.rs:105-108`), but no actor-storage
  override is present at this revision, so the effective actor-storage deadline
  is 5 s unless the floor below raises it.
- Config key `storage.command_timeout_ms` (`depot.rs:109`; the struct is renamed
  to `storage` in `engine/packages/config/src/config/mod.rs:68-69`). Default:
  unset, which keeps each command's own deadline (`depot.rs:297-301`). When
  set, it is a floor: `max(command default, floor)` on the client
  (`engine/packages/depot-client/src/lib.rs:111-123`) and on the maintainer
  handler (`engine/packages/depot-worker/src/command/volume_host.rs:2448-2456`).
- Client deadline: computed, then capped by the caller's own boot deadline
  (`engine/packages/depot-client/src/command.rs:193-202`). The whole attempt
  loop runs under `timeout_at(deadline)` (`command.rs:451-454`).
- A request path timeout under the cap is a transport failure, not the command
  deadline; the command deadline only wins when the clock agrees
  (`command.rs:283-291`, `610-620`).

On expiry the outcome is **unknown and not retried inside the client**:

- Client: `timeout_at` maps to `RequestDeadlineExceeded`
  ("The command deadline elapsed; its outcome may be unknown.",
  `command.rs:25-31`, `451-454`). A host refusal returns at once as
  `Overloaded` and the calling edge decides (`command.rs:1-8`, `395-405`).
- Host: past the deadline it answers `unavailable(TimedOut)`
  (`volume_host.rs:1540-1548`), and after a handler timeout it keeps the
  admission until already-dispatched commits settle, because a commit keeps
  running under the filesystem deadline and its outcome may be unknown
  (`volume_host.rs:1561-1597`).
- Classification: a refusal after an uncertain attempt is downgraded to
  `Unavailable` for non-read-only commands, never `Overloaded`
  (`command.rs:622-641`).
- Edge: a deadline after submission is treated as uncertain, not replayed —
  public create returns `actor.create_pending` (`routes.rs:84-93`, `108-134`)
  and maps deadline to 504 versus refusal to 503 (`routes.rs:149-170`). Retries
  at the edge run only for refusals, within one shared budget
  (`routes.rs:60-82`, `808-822`).

## 2. `depot.alarms` limits and `max_background_cold_reads`

Alarm limits (`AlarmConfig`, `depot.rs:1147-1159`) resolve to the defaults in
`engine/packages/depot-worker/src/alarms.rs:38-51`:

| Limit | Default | Source |
| --- | --- | --- |
| `max_candidates` (frontier + parked cap) | 1024 | `alarms.rs:41` |
| `max_operations` (keyed execution slots) | **16** | `alarms.rs:42` |
| `max_callbacks` (worker callback pool) | 128 | `alarms.rs:43` |
| `page_size` | 128 | `alarms.rs:44` |
| `handler_timeout_ms` | 30 000 | `alarms.rs:45` |
| `io_timeout_ms` | 5 000 | `alarms.rs:46` |
| `retry_min_ms` / `retry_max_ms` | 500 / 30 000 | `alarms.rs:47-48` |

`used=16 capacity=16` in the incident is `AlarmSnapshot.operations` against
`operation_capacity = max_operations`
(`engine/packages/depot-worker/src/tablet_maintainer_machine/state/alarms.rs:1158-1171`,
emitted at `engine/packages/depot-worker/src/metrics.rs:2556-2562`).

`storage.max_background_cold_reads`: field `depot.rs:127-130`, default **4**
(`tablet_maintainer_machine/types.rs:479`), resolved in
`depot-worker/src/services/storage.rs:462-464`. It bounds four independent
per-maintainer windows — held-image reads, replica log reads, fork jobs, fork
cleanup (`metrics.rs:1214-1222`). The replica log window is the one that makes
applies **wait** (`metrics.rs:1234-1239`); the held-image and fork-job windows
**refuse** (`metrics.rs:1228-1233`, `1240-1245`).

Config naming note: the config key is `storage.alarms.*` /
`storage.max_background_cold_reads` (`depot.rs:14-16`, `mod.rs:68-69`), while
log text says `depot.alarms` / `depot.max_background_cold_reads`
(`metrics.rs:2576`, `1232`).

When the frontier is full:

- A keyed request at `max_operations` is parked as `Queued`, not refused
  (`state/alarms.rs:271-282`).
- The parked set is separately capped at `max_candidates`; a droppable read or
  forget is dropped and left to rediscovery, and only a non-droppable
  uncertain write can evict a droppable one or, with none available, fence the
  maintainer (`state/alarms.rs:505-546`, `552-563`).
- The candidate queue evicts the furthest hint and re-arms discovery rather
  than rewinding (`state/alarms.rs:610-625`).
- Group-gated keys are capped at 4 per group and `max_candidates` overall; past
  it the hint is dropped and found by a later pass (`state/alarms.rs:33`,
  `312-349`).
- The gauge warns once on entering the 90 % band, which is why the incident saw
  one line rather than a stream (`metrics.rs:2545-2579`).

Retries are **backoff, not immediate**:

- A callback that fails logs
  "the unacknowledged alarm will retry" and still returns `Called`
  (`alarms.rs:254-267`); the state machine then stages an `AlarmRetryRecord`
  at `now + delay`, with `delay = (retry_min_ms << attempt) + jitter`, capped at
  `retry_max_ms` (`state/alarms.rs:1099-1135`).
- A full callback pool returns `Called { busy: true }` and, by its own comment,
  leaves pending alarms on their retry deadlines (`alarms.rs:222-234`).
- A waiting attempt's timer is `retry_min_ms` (500 ms)
  (`state/mod.rs:1018-1024`).

CPU spin: the source does not attribute it.

- The alarms drive runs only while keyed slots are free and, when none are,
  cancels the timer instead of re-arming a past one
  (`state/alarms.rs:809-866`, `897-915`), so the alarm policy above cannot
  tight-loop by inspection.
- The ~1 warning / 30 s cadence is consistent with two caps of exactly 30 s:
  `retry_max_ms` (`alarms.rs:48`) and the group-read backoff
  `GROUP_READ_MAX_BACKOFF_MS` (`state/groups.rs:40`), whose warning fires
  first-failure and at-cap (`state/groups.rs:1497-1540`). This is a match, not
  an attribution.
- The sustained 100 % CPU on three runtime workers with no app connected is
  therefore **not established by inspection**. Experiment (not run here):
  sample the Engine process (`perf record -g` / `tokio-console`) for 30 s under
  the same load and read `depot_alarm_*`, `depot_maintainer_*` and
  `rivet_state_machine` scheduling metrics to identify the hot loop.

Sequence fit: a depot `volume_transition` refusal carries a hint derived from
`kv_refusals::OVERLOADED_RETRY_AFTER_MS = 100`
(`engine/packages/depot-worker/src/kv_refusals.rs:10-45`); the log shard jitters
a 100 ms base by 50–149 % clamped to `[min, 1000]`
(`engine/packages/depot-log/src/log_shard_machine/state/admission.rs:159-167`,
`types.rs:475`), which reaches exactly the observed 149 ms. The alarm callback is
an `ActorAlarm` command (`engine/packages/pegboard/src/commands.rs:635-657`); its
following `request_deadline_exceeded` is the 5 s command deadline elapsing
while the volume never became ready (`command.rs:451-454`,
`volume_host.rs:1533-1548`).

## 3. "storage could not register" and its persistence

Meaning: the connect's first storage read failed, before the envoy was sent its
init.

- The message is logged for any connect rejection that is not the expected
  missing-pool race (`engine/packages/pegboard-envoy/src/connection.rs:1612-1617`,
  `1620-1625`).
- `run()` reads the envoy record with `EnvoyRead` before anything else; any
  error other than volume-gone becomes a connect rejection
  (`connection.rs:136-157`). Init also needs `connect()`, which writes the
  namespace, pool admission, envoy record, active-index entry and heartbeat
  (`connection.rs:1655-1702`); a storage failure there is the same rejection
  (`connection.rs:1420-1434`).
- Classification (`engine/packages/pegboard-envoy/src/rejection.rs:100-144`):
  a depot retry hint closes with 1013 `envoy.connect_unavailable` carrying the
  clamped hint (100–5000 ms) — exactly the observed
  `code=1013 reason="envoy.connect_unavailable;retry_after_ms=1000"`; a
  transient depot `request_deadline_exceeded`/`unavailable` or UPS
  timeout/overloaded/unresolved uses the default hint; anything else closes
  1011. The 1013 code is `TRY_AGAIN_LATER`
  (`engine/packages/pegboard-envoy/src/routes.rs:21`), and the reason format is
  `connect_unavailable;retry_after_ms=…` (`routes.rs:267-271`).

Why an Engine restart does not clear it: the refusal is depot-tablet state, not
Engine-process state.

- The source states the case directly: "a connect whose registration storage
  could not finish, such as while tablets reopen after an engine restart"
  (`rejection.rs:1-4`).
- The maintainer must open the cold store and pass member discovery before it
  serves; an open failure fences it
  (`engine/packages/depot-worker/src/tablet_maintainer_machine/state/opening.rs:17-60`),
  and a fence is followed by supervisor recovery under a new grant
  (`state/mod.rs:1507-1533`, `engine/packages/depot-worker/src/tablet_supervisor.rs:1355-1459`).
- Recovery is retried at `RECOVERY_RETRY_MS = 1000` per grant, and the
  supervisor only sleeps to a deadline it has
  (`tablet_supervisor.rs:486`, `535-569`, `1495-1527`).
- What replays is durable depot state: the tablet log/cold store and the
  volumes holding the namespace, pool, envoy record and indices. The Engine
  process restart therefore does not shorten the apply/recovery backlog, which
  is why it cleared only when host load fell.
- The envoy's own retry is bounded by the advertised lost threshold and the
  100/5000 ms hint clamp
  (`engine/sdks/rust/envoy-client/src/utils.rs:155-212`), so it keeps
  reconnecting rather than giving up.

Not established: which specific tablet/volume was recovering at the time; the
log excerpt names the class, not the volume.

## 4. RivetKit's 30 000 ms registration timeout

Set in RivetKit, not open-orange, and not configurable.

- `REGISTRY_READY_TIMEOUT_MS = 30_000`
  (`rivetkit-typescript/packages/rivetkit/src/registry/index.ts:34`);
  `LOCAL_ENGINE_READY_TIMEOUT_MS = 60_000` (`index.ts:37`).
- The 60 s branch requires `engineSpawn && endpoint !== undefined &&
  isLocalEngineEndpoint(endpoint)` (`index.ts:978-983`); otherwise 30 s.
  `isLocalEngineEndpoint` accepts only `localhost`, `0.0.0.0`, `::`/`::1` and
  `127.*` (`rivetkit-typescript/packages/rivetkit/src/common/engine.ts:11-28`).
- Production takes the 30 s branch: `orange serve` requires `RIVET_ENDPOINT`
  (`src/commands/serve.ts:71-76`), passes it as `endpoint`
  (`packages/runtime-node/src/internal/rivetkit.ts:562-575`), and the URL is the
  bridge address `http://<engine_ip>:6420`
  (`deploy/openorange/lib/oolib.py:246-248`, `deploy/openorange/apps.toml:28`),
  which is neither loopback nor `engineSpawn` (endpoint given without
  `startEngine`).
- The timeout is a module constant raced against readiness
  (`index.ts:984-1009`); the message is built there (`index.ts:986-994`). No
  registry config field overrides it, so it is not configurable.
- open-orange starts it through `startAndWait()` and adds no timeout of its
  own (`packages/runtime-node/src/internal/rivetkit.ts:608-612`,
  `packages/runtime-node/src/bindings/durable-objects/lifecycle.ts:105`).

## 5. Is "overloaded … retry after N ms" tunable; shed or queue?

The Engine queues to a bounded wait, then sheds with a hint. The hint is
tunable; the shed does not become unbounded queueing.

- Depot command refusals are `Overloaded` with the refusing layer's hint, and
  the edge decides whether to retry (`command.rs:1-8`, `622-641`).
- Volume transitions use a 100 ms hint
  (`engine/packages/depot-worker/src/kv_refusals.rs:10-45`), propagating a lower
  layer's hint when one exists.
- Log shard admission: `max_admission_wait_ms` (default 1000) for new work and
  `max_append_admission_wait_ms` (default 1800) for appends that carry admitted
  writes; `overload_retry_after_ms` (default 100) is the hint
  (`depot.rs:637-650`, `engine/packages/depot-log/src/log_shard_machine/types.rs:464-466`).
  New work is shed first, before any work runs
  (`engine/packages/depot-log/src/log_shard_machine/state/admission.rs:51-56`),
  and hints are jittered half-to-one-and-a-half and capped at
  `MAX_RETRY_AFTER_MS = 1000` (`admission.rs:159-167`, `types.rs:473-475`).
- Maintainer admission caps are `max_requests`, `max_queued_opens`,
  `inbox_capacity` and `max_loaded_volumes`, all tunable
  (`depot.rs:188-204`).
- Envoy connect shedding is tunable: `node_connect_admissions_per_second`
  (200), burst (400), `node_connect_retry_after_ms` (1000, 100..=5000)
  (`engine/packages/config/src/config/pegboard.rs:73-88`).
- Under sustained slowness the retry is eventually denied rather than queued
  forever: at most 4 retries per request, backoff 25→1000 ms, and a retry
  denied when it would pass the request deadline or when the shared gateway
  budget is spent, at which point the refusal reaches the client
  (`engine/packages/pegboard-gateway/src/retry_budget.rs:31-37`,
  `278-322`).

## Candidate changes, ranked

Each is a lever that converts a refusal into slowness (or removes the
bottleneck), with its evidence and risk.

1. **Host/guest CPU capacity (operations).** Highest confidence. The guest ran
   4 vCPU under a saturated host; production simulated processing cost is zero
   (`engine/packages/depot-worker/src/tablet_maintainer_machine/mod.rs:278-284`,
   `tablet_maintainer_machine/types.rs:481`), so CPU starvation shows up as
   latency in every step above, which then crosses the admission bounds that
   produce `overloaded` and `request_deadline_exceeded`. More vCPU or a less
   loaded host lengthens the time to each bound. Risk: none to semantics;
   masks nothing, since the bounds still exist.

2. **Raise `storage.max_background_cold_reads` (4 → e.g. 16), config.** The
   replica-log window at cap makes applies wait (`metrics.rs:1234-1239`), which
   is the direct cause of this incident's
   `tablet replica log read window near its cap`. More windows let applies
   drain, so volume transitions settle instead of refusing. Risk: more parallel
   cold reads and their memory/CPU on an already starved guest; the doc says
   each window is separately bounded for exactly this reason
   (`depot.rs:127-136`).

3. **Raise `storage.alarms.max_operations` (16 → e.g. 64), config.** At 16
   keyed slots every further due alarm is parked (`state/alarms.rs:271-282`),
   so delivery queues and the 90 % gauge fires (`metrics.rs:2545-2579`). More
   slots admit more deliveries on the same frontier. Risk: more concurrent
   store work and callbacks on a 4-vCPU guest, against a `max_callbacks` pool of
   128 (`alarms.rs:43`, `222-234`); it does not fix a slow store.

4. **Raise `storage.command_timeout_ms` (unset → e.g. 30000), config.** The
   floor raises both the client budget and the handler timeout
   (`lib.rs:111-123`, `volume_host.rs:2448-2456`), so a command that would time
   out gets a later answer or a later refusal. Risk: an in-flight handler and
   its admission are held longer (`volume_host.rs:1583-1597`), which can deepen
   the overload under saturation and hides the underlying slowness.

5. **Give the actor-inventory read edge the bounded storage-step retry helper,
   code.** The source already shares a bounded gateway retry budget with actor
   creation, but inventory routes do not use the storage-step retry helper
   (`docs/openorange-engine-diagnosis.md:317-323`); using it turns a refusal at
   that edge into an absorbed retry. Risk: it only relabels the failure at that
   edge unless the storage bottleneck behind it is addressed; must stay inside
   the same deadline and budget to avoid turning 503s into timeouts.

6. **Raise RivetKit's readiness constant or make it configurable, code (not a
   refusal-to-slowness change).** `REGISTRY_READY_TIMEOUT_MS` is 30 s
   (`registry/index.ts:34`) and not configurable; a longer value would let the
   app ride out a slower registration instead of failing `orange serve`. Risk:
   it delays detection of a genuinely stuck registry and is a RivetKit change,
   not an open-orange setting.

Not recommended: raising `alarms.retry_min_ms`/`retry_max_ms`. They space
retries (already 500→30 000 ms, `alarms.rs:47-48`, `state/alarms.rs:1099-1135`)
and do not turn a refusal into service.

## Unverified

- The 100 % CPU spin's hot loop: not attributable from source; experiment in
  section 2.
- Which tablet/volume was recovering during the incident: the log excerpt names
  the class only.
- The image manifest and its exact build profile: taken from the recorded
  provenance (`docs/openorange-engine-diagnosis.md:8-23`), not re-inspected.
- No Engine was run for this record; all statements are source reads at the two
  pinned revisions.
