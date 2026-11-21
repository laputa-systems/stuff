# Observe actor sleep and wake

Live topic: [Rivet explorer](../deploy/openorange/rivet/README.md).

The attested Engine reads an actor's committed phase and epoch, but its public
adapter discarded them. It deliberately returns null lifecycle timestamps
because its state does not store those times. Null timestamps alone cannot
establish whether an actor slept or woke.

The private candidate adds two scalar fields to actor responses backed by an
actual state-volume read:

| Field | Meaning |
| --- | --- |
| `lifecycle_phase` | Committed Engine phase, or null when unavailable |
| `lifecycle_epoch` | Engine's u32 fencing epoch, or null when unavailable or held by V2 |

Phase values are `initializing`, `starting`, `running`, `stopping`, `sleeping`,
`destroying`, `destroyed`, `migrating_from_v2` and `delegated_to_v2`.
Responses without a state read, including new-create and historical index
records, need not include these fields. Missing and null mean unknown.
The existing timestamps remain unchanged, including their null values.
The explorer preserves these fields through its authenticated projection and
shows the Engine phase and available epoch before historical timestamp labels.

The epoch is not a constructor counter or a timestamp. Ending an epoch advances
it before the next wake, so running epoch 6, sleeping epoch 7 and running epoch 7
is a valid sequence. It wraps as a u32, and must be interpreted with actor ID,
namespace and incarnation creation time. Do not treat an epoch change alone as
proof of sleep or initialization.

## Private acceptance procedure

1. Record the frozen application, candidate binary and namespace identities.
   Read a running observation-store actor and retain its ID, creation time,
   phase and epoch. Complete an application read with the expected data.
2. Keep the Engine, application and Envoy alive. Stop application requests to
   that actor, but do not call an explicit sleep or stop endpoint. Inventory
   metadata reads may observe its committed phase without waking it.
3. Retain the SDK's positive `sleep idle deadline elapsed` event for that actor
   and an Engine response reporting `sleeping`. A crash can also lead to sleep,
   so phase alone does not establish an idle eviction. Elapsed idle time,
   process restart and null timestamps are not substitutes for this evidence.
4. Send the next application request, verify its complete expected data and
   retain the subsequent `running` response for the same actor and incarnation.
   Correlate observations in time; do not infer a constructor count from epoch.

This is a capability and proof for the private pinned runtime. The Stats
after-sleep browser study remains separate. No shared Engine or application
restart is authorized by this procedure.

## Candidate and checks

Source `0d67a685acc7c88c8744ffb8d1f5bc5a142361a9` adds the fields without a
persisted schema change. The integrated source is
`197af2f08cc5f00ec9a15b5a0d3fc8965c818dda`. Its additive lifecycle patch is
`deploy/openorange/patches/rivet-e5ed391-actor-lifecycle.patch`, SHA-256
`039c0bb5206f2f9815e45b27d1f0d15a35b41eaab0441f18231e8fa29ffe2689`.
Apply `rivet-e5ed391-inventory-read.patch` first, then this lifecycle patch;
both are included together. Their sequence applies cleanly to the attested
base and reproduces the tested API package exactly. The integrated binary
also includes the three SQLite patches recorded in
[stuff#34](https://github.com/laputa-systems/stuff/pull/34).

Two Engine tests pass in dev on the attested Linux x86-64 builder. They assert
the projected lifecycle values, unknown and V2-held epochs, unchanged fields
and null timestamps, and the running/sleeping/running epoch sequence. A hand
fault labeling sleeping as running fails the intended assertion; both tests
pass after restoration. The integrated inventory/lifecycle candidate also
passes all nine API tests in dev and release, and the full release binary
builds. Its stripped x86-64 size is 68,748,840 bytes, SHA-256
`95b483cb6178627161c0fe41c420f8a71e07eebe03d302b23989dd6d0e532b44`.

The proxy's nine Python tests and the frontend regression pass. The proxy
rejects non-integer and out-of-u32 epochs, and secret-containing phase values;
it preserves absent and null values. Both TypeScript sources and generated
JavaScript are rebuilt with `make ts-assets`.

## Observed natural transition

[The qualification receipt](openorange-actor-lifecycle-proof.json) records
the private U observation on a copy of the completed M depot. The same
observation actor and incarnation reported running epoch 3, sleeping epoch 4
and running epoch 4. Its SDK emitted `sleep idle deadline elapsed` for that
actor; the receipt includes the event line's SHA-256 and protected log name.
One request before sleep and one after it each returned all 203,950 events
with the complete summary equal to the retained reference. The Engine PID
did not change, and the application process stayed alive. No explicit sleep,
stop or restart was used to create this transition. The two-CPU, 3-GiB
container recorded zero memory-limit, OOM or kill events and is stopped.

The initial T probe failed its selector assertion because it assumed the
public actor key was the service name; OpenOrange uses a hashed object key.
It did not establish an idle transition. U selects the sole observation-store
actor in this single-service fixture and retains its actual identity. T's
receipt is preserved separately and is not acceptance evidence.

The same Engine also denied an actor read in a new namespace before creation,
then created a distinct metadata record with the intentionally identical
keyed actor ID. The original namespace's actor and creation time remained
unchanged. This validates namespace identity resolution; it is not a
cross-namespace SQLite write test.

Protected evidence is under
`/home/josh/d/stuff/.work/tmp/stuf86-lifecycle-t-20261116/`, using distinct
U receipt and log filenames. The shared Engine, applications and sampler
remain unchanged. This completes the private capability proof required by
STUF-86; the Stats browser after-sleep study remains separate.
