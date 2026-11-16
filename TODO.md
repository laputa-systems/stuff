Prefix: STUF
Next: 89

New tickets use STUF. RPMD tickets were filed in repomod before it moved into stuff; they keep their IDs.

Review priorities are reviewer-assigned; existing owner-assigned priorities are retained.

## On hold

- **Shadowdriver**: everything shadowdriver-related is on hold because the owner cannot publicize shadowdriver (private git dependency). This blocks the bctl CI jobs (no read secret), the `h12tiny-client-sync` 0.9.0 publish (and the laputa-rustix migration on top of it), and any other work that depends on shadowdriver being public. Hold stands until shadowdriver is public or a read credential is supplied.
- **Cargo publish 403** (`PUT .../crates-io/gi/ml/gimli: HTTP 403: forbidden`): blocks the cargo mirror backlog (435 crates, 87 npm, 4 pypi still unpublished), the `h12tiny-client-sync` publish, and the audit-upgrades sweep. Bucket/IAM intent unresolved; do not retry until the owner answers.
- **Mirror pollution**: 2006-era packages remain on the mirror, unactioned.
- **npm mirror 500s**: recurring HTTP 500s (outages ~16:26-01:00 UTC and ~02:14 UTC on 2026-11-14); mirror packages (pnpm 12.20/12.21, playwright-core 1.65.1, vitest 5.0.3, ws 8.23.0, vite 8.3.6) still absent. Snapshots of deps/loc must wait for merges and a healthy mirror.
## Tickets

### STUF-75 · P1 · Add integrity-verified S3 backup copies and isolated restore proof

- **Area:** OpenOrange durability
- **Where:** deploy/openorange/bin/backup, bin/restore-rehearsal, docs/openorange-runtime.md; Engine filesystem log and object tier are one recovery unit
- **Problem:** Fenced backups and known off-host Mac copies are manually made. The shared installer installs log rotation but no recurring backup scheduler was found in its source. There is no recurring independently verified S3 copy or restore freshness guarantee. Host or disk loss can lose writes after the latest independently verified off-host fence. The owner explicitly defers S3 backup implementation as P1.
- **Recommendation:** Use existing fenced artifacts for protected recurring S3 copies, complete manifests, integrity checks, retention and freshness monitoring. Add a non-production full restore rehearsal measuring RPO/RTO. Keep Engine logs and object state together, distinguish backup storage from the Engine backend, and resume scheduling and credential work when the owner resumes this P1.
- **Fix with:** durable-state
- **Effort:** M





### STUF-87 · P1 · Diagnose private Engine volume fencing during acknowledged Stats import

- **Area:** OpenOrange Engine durability
- **Where:** Stats bench/results/2026-11-15-scale-prep-review/README.md; protected Lisa /home/josh/.work/stats-perf-campaign/production-engine-20261115/engine-stdout.log and campaign-rebuild-20261115/; Stats bench/results/2026-11-16-fresh-engine-reproduction/{README.md,evidence.json}; protected Lisa resume-engine-20261116/ and resume-fixture-20261116/
- **Problem:** Isolated Stats fixture using image stats:6cc06db247a3, private Engine binary SHA256 0b6e8c031ce2d2d3259b540a4ae55c6f8d4bb367001406110ce5dc62bcd7357f, two CPUs and 3 GiB repeatedly fails canonical snapshot import with HTTP 500. Engine logs QuorumUnavailable at 18:03:23 UTC and staged_write_abort_failed fencing at 18:03:30, 18:18:35 and 19:08:47 on 2026-11-15. A fresh-namespace single campaign rebuild with 250ms import pacing stopped at 70500 acknowledged rows; memory limit events occurred but zero OOM kills. Blocks tenfold acceptance and repeated recovery. Underlying defect versus Engine configuration/resource limits is unproven; P1 assumed for the blocked durable recovery path, not a claim of production data loss. Fresh private Engine and empty depot reproduction on 2026-11-16 at 04:16:08 UTC fenced with staged_write_abort_failed after 25000 acknowledged rows. Same pinned image/binary, two CPUs, 3 GiB, 500-row pages and 250ms pacing; snapshot was 2018594816 bytes with zero memory-limit/OOM events. Prior failed depot state and cgroup limit events are not necessary conditions. One private Engine reopen returned importing state with exactly 25000 rows; exact row equality is unverified because incomplete-import state disallows snapshot export. No import retry ran. The new container is stopped and failed state preserved.
- **Recommendation:** Preserve failed state and logs; reproduce the volume-layer failure in an isolated pinned runtime, distinguish resource/configuration misuse from Engine defect, and verify acknowledged rows survive reopening and ten ordinary restarts under 15 seconds. Do not restart the shared Engine or repair it within the Stats campaign. Check cross-namespace actor identity handling: actor-list results in two fixture namespaces returned the same actor ID.
- **Fix with:** root-cause
- **Effort:** M






### STUF-86 · P2 · Expose positive observation actor sleep and wake evidence

- **Area:** OpenOrange lifecycle observability
- **Where:** deploy/openorange/rivet/server.py; Stats docs/CAMPAIGN-STATS-PERFORMANCE.md W3 and bench/results/2026-11-15-scale-prep-review/README.md; protected Lisa /home/josh/.work/stats-perf-campaign/
- **Problem:** Pinned Engine 3.1.2-rc.1 in the isolated stats-perf-scale-server fixture returns null sleep_ts, start_ts and connectable_ts for the active observation-store actor on repeated API inspection. Stats exposes no constructor-generation signal. This prevents confirming the after-sleep condition for 200 uncached browser selections per range; idle elapsed time and forced restarts cannot substitute. P2 priority assumed for the missing validation capability.
- **Recommendation:** Provide a supported positive per-actor sleep/eviction transition and wake or constructor-generation signal on the pinned runtime path, preserving unknown values. Verify a natural idle eviction and correlate its next request; do not infer sleep from elapsed time. Resume the Stats after-sleep acceptance study only with positive evidence.
- **Fix with:** root-cause
- **Effort:** M


### STUF-88 · P2 · Keep actor inventory available during native resource collection

- **Area:** OpenOrange lifecycle observability
- **Where:** deploy/openorange/rivet/server.py; Stats bench/native-soak.py and bench/results/2026-11-15-soak-progress/README.md; protected Lisa maintained-rollup-soak-v2.jsonl
- **Problem:** The live 2026-11-15 Stats production soak recorded actor inventory HTTP 503 at 23 of its first 152 samples and one application-health timeout. W6 requires no unavailable groups, so the collection cannot establish plateau acceptance. This is observed diagnostic unavailability, not proof of production data loss or a classified Engine defect. P2 assumed for a repeatable gap blocking production resource validation. At 2026-11-16 04:11 UTC, one read-only production inventory sweep returned 200 for names and all eight first pages, without further cursors. The historical 503 did not reproduce; continuous availability remains unproven. Stats bench/results/2026-11-16-resume-diagnosis/README.md preserves the qualification.
- **Recommendation:** Diagnose the failed actor-list requests using preserved sample indices without restarting the shared Engine or changing the active sampler. Establish a supported bounded inventory path that remains available during normal traffic, preserve unknown lifecycle states and explicit failures, and verify a complete 24-hour collection with zero unavailable groups. Handle the application-health timeout separately if it has an independent cause; do not hide outages with dropped samples or relaxed acceptance.
- **Fix with:** root-cause
- **Effort:** M

