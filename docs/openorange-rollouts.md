# OpenOrange rollout transactions

`deploy/openorange/bin/rollout` is the rollout controller. `--target-kind`
selects its adapter: `fake` (a local directory, for tests) or `native` (the
native standby Stats writer, reached with `--host` and `--ssh-config`). The
oo-containers adapter for Lisa is not implemented. The controller never
builds artifacts.

`start` accepts release IDs, the candidate sha256 digest, a target,
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
check operations, plus two hooks. `classify(state, expected, release,
digest)` names an observed state `applied`, `not-applied`, `partial` or
`ambiguous`; a partial effect is finished with `complete` instead of
reactivated. `preparations(config)` lists preparatory steps that run in
`prepared` with the same intent, effect and done records as activation;
`prepare_observed(step)` decides on resume whether a step already took effect. The fake adapter stores its state in `state.json` in the
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

## Native standby adapter

Guest operations run one standard-library script (`GUEST_SCRIPT` in
`lib/oorollout_native.py`) with the guest's `python3` over SSH; tests run the
same script against a simulated guest root. `rollout observe --target-kind
native --host stats-standby --ssh-config FILE --json` is read-only.

- **Runtime releases.** A release is a directory
  `/opt/native-rehearsal/runtime/rt-<12 hex>/` holding an installed closure
  (`package.json`, `pnpm-lock.yaml`, `node_modules`) and `release.json`. Its
  digest is SHA-256 over canonical JSON of the SHA-256 of `package.json`,
  `pnpm-lock.yaml` and `open-orange/dist/bin.js`, the installed open-orange and
  rivetkit versions, and every RivetKit N-API addon file. The release id is
  `rt-` plus the first 12 hex digits.
- **Selection.** `/opt/native-rehearsal/orange` is a symlink to the active
  release, replaced atomically by `rename`. The `native-stats` unit is
  unchanged. The first rollout's `convert-runtime` preparation renames the
  original in-place directory into its release directory and links it; the
  path is absent only between those two system calls.
- **Running identity.** The running release is the one the `native-stats`
  node process loaded: the symlink target if the process started after the
  symlink's mtime, otherwise the release recorded in `runtime/.previous`,
  which is written and synced before every switch. No process or several
  processes make it unknown.
- **Activation.** Conditional on the expected selection and on the staged
  directory's recomputed digest, then `rc-service native-stats restart` and a
  guest health wait. A switch without a restart classifies as partial and is
  completed by a restart.
- **Staging.** `rollout stage --archive TAR --source TEXT` copies an installed
  closure to the guest and extracts it as a new release directory, without
  activating it. Producing a musl closure from the owned OpenOrange package
  is the next step.
- **Lock.** `/var/lib/openorange-rollout/lock.json` with a fencing counter,
  created exclusively under `flock`; every mutating guest operation rechecks
  holder, token and lease in the same invocation.
- **Checks.** Guest health, the expected selected and running release and
  digest, and a running Engine container. Real ingest, durable readback and
  duplicate handling remain the Stats canary's checks.

On 2026-11-20 live `observe` reported the unconverted baseline
`rt-13b896622da5` (`sha256:13b89662…`), selected and running, healthy, with
8.9 GB free.
