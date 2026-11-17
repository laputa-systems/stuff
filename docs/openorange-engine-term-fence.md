# Private Engine lease fence during TERM

STUF-90 tracks a nonzero private Engine exit during Stats recovery qualification.
The underlying shutdown trigger is unproven. Production is unchanged by this
qualification. No acknowledged data loss has been demonstrated.

## Observed cohort

Stats uses the release binary from merged PR39, SHA-256
`611b08f609d625ad5379c3b0801f23fc76ab4e17cc3ee0210ba608bf53ae1b01`.
Its combined source is `f68e0732f44c1d0ec64e96dc425f585eeef8c255`.
The frozen Stats image remains `stats:6cc06db247a3`, with two aggregate CPUs
and 3 GiB. Its new depot imports all 203,950 corpus events successfully.
Subsequent isolated workloads leave 219,939 canonical observation events.

Nine Engine-only TERM/start cycles pass all four Mac and Lisa host gates.
Every cycle preserves the complete event-table hash and the complete canonical
Installation manifest. The full fixed-window summary also stays equal. The
application and both Worker process identities remain unchanged. Every accepted
shutdown-to-verified-data interval is below the unchanged 15-second limit.

The observation table hash throughout those cycles is
`0114eb033b8d570bfdd7ee28fd3509b532b522559721652ef62924d639273996`.
These hashes include canonical stored payloads and identities. They are not
summary-count substitutes. Snapshot fences are released before each restart.

The tenth TERM exits with code 1. Its log first reports the following errors
at 2026-11-17 07:32:58 UTC:

```text
topology fenced this worker's lease; reason=dependent_failed
singleton coordinator fenced this worker's lease; exiting process so its heartbeat lifetime ends too
```

The immediately preceding messages include a durable storage stop permit,
UPS draining, log-shard stop and tablet-coordinator request-service stop.
The driver rejects the nonzero exit before starting that cycle's Engine.
Both post gates still pass. Ten-cycle acceptance is not established.

## Investigation boundary

The fence reason can originate from several cleanup paths in the attested
Engine source. Relevant owners are:

- `engine/packages/depot-worker/src/services/storage.rs`: service completion,
  cancellation and the `ServiceTask` drop guard.
- `engine/packages/engine-context/src/services/depot_client.rs`: unexpected
  manifest-watcher completion and client shutdown.
- `engine/packages/engine-context/src/context.rs`: `EngineBackground` shutdown
  and drop cleanup.
- `engine/packages/singleton-coordinator/src/runtime.rs`: `watch_worker`
  intentionally ends the process after a fenced worker lease, preserving the
  heartbeat lifetime invariant.

The log does not identify which cleanup path requested the fence. Do not
remove the heartbeat guard or classify the exit as harmless from this receipt.
Locate the first unexpected completion before choosing a repair.

The stopped depot, credentials and complete logs remain on Lisa under
`/home/josh/.work/stats-perf-campaign/sta128-20261117/fresh/`.
Container `stats-p9-recovery-20261117` is stopped. Preserve that state before
any further reopen. The independent small ingestion comparison uses another
depot and namespace.

Stats owns the [complete recovery receipt](https://github.com/joshuarli/stats/blob/master/bench/results/2026-11-17-observation-overhead/engine-recovery.json)
and reproduction driver `bench/native-scale-recovery.mjs`.
No additional restart cohort or production upgrade follows from this record.
