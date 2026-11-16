# Observe actor sleep and wake

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

Source `0d67a685acc7c88c8744ffb8d1f5bc5a142361a9` adds the fields to the
attested source without a persisted schema change. The standalone patch is
`deploy/openorange/patches/rivet-e5ed391-actor-lifecycle.patch`, SHA-256
`df05f08d2a22d4b74e64150608146c5c9d7e87cbfb986498afbea977e92a6787`.
It shares the parent SQLite repairs but contains only the lifecycle change.

Two Engine tests pass in dev on the attested Linux x86-64 builder. They assert
the projected lifecycle values, unknown and V2-held epochs, unchanged fields
and null timestamps, and the running/sleeping/running epoch sequence. A hand
fault labeling sleeping as running fails the intended assertion; both tests
pass after restoration. The integrated inventory/lifecycle candidate also
passes all nine API tests in dev. Release and runtime acceptance remain open.

The proxy's nine Python tests and the frontend regression pass. The proxy
rejects non-integer and out-of-u32 epochs, and secret-containing phase values;
it preserves absent and null values. Both TypeScript sources and generated
JavaScript are rebuilt with `make ts-assets`. STUF-86 remains open until the
natural idle transition and correlated wake above are observed.
