# OpenOrange rollout transactions

`deploy/openorange/bin/rollout` is a controller prototype. Its only target is a
local fake adapter directory; the native-standby and oo-containers host
adapters are not implemented. It does not build artifacts. Do not use it to
release a host.

`start` accepts release IDs, the candidate sha256 digest, a target directory,
a policy JSON file, a Stats evidence directory and a controller journal
folder. Policy fields are `max_age_s`, `observation_s`, and
`check_interval_s`. Stats' `decision.json` supplies verdict, evaluation time
and reason codes; `candidate.manifest.json` and `baseline.manifest.json`
supply `releaseId`. Only a pass with matching identities qualifies. The
qualified digest is the only candidate digest activated. Preparation checks
baseline selection and running identity, decision freshness, the exact
baseline recovery digest and headroom.

The journal progresses through staged, qualified, prepared, activated,
verifying and promoted. A failed pre-activation gate is rejected. After
preparation, failure or abort enters recovering and ends in recovered or
needs-operator. Verification repeatedly asks the adapter for identity and its
post-activation checks through the configured observation window. A real
adapter must check authenticated readiness, real ingest, durable readback and
duplicate handling. Recovery reactivates and verifies the recorded baseline
digest. No promotion implies a build.

Each run has a controller-host directory outside the target, with an append-only
`journal.jsonl` and controller serialization lock. Records have increasing
sequence numbers and are fsynced with their directory. Transitions have
deadlines, heartbeats carry deadlines, and activation and recovery have intent
and observed done records. `status --run PATH` replays records; a torn final
line is reported and discarded before the next append. `resume --run PATH`
compares selected release, running release and digest before reapplying an
idempotent conditional effect. Ambiguous identity requires an operator.
`abort --run PATH` rejects before preparation and recovers afterward.
`watchdog --journal-dir DIR` recovers post-prepare runs with overdue
heartbeats through the same lock and reconciliation path.

The adapter provides acquire, release, observe, conditional activate and
check operations. The fake adapter stores its state in `state.json` in the
target directory. A single maintenance lock covers deployment, backup/fence,
Engine replacement, ingress change and writer handoff. Its record contains
holder, operation, monotonically increasing fencing token and lease expiry.
Acquisition creates the lock exclusively; expired takeover advances the token.
Each target mutation checks the holder, live lease and token under the same
atomic serialization boundary. A real host adapter must supply an equivalent
host-wide atomic lock and reject stale tokens at every mutation boundary; the
fake's local filesystem lock is not a distributed lock.

Exit codes: 0 promoted (or successful status/no watchdog work), 3 rejected or
recovered, 4 lock held, 5 needs operator, 2 usage, 1 runtime failure. A
watchdog returns 3 when it recovered any run, 4 for a held lock, and 5 for
operator intervention. Inspect the journal and actual host before manually
repairing an ambiguous run.
