Prefix: STUF
Next: 87

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

### STUF-85 · P1 · First-party packuments freeze dist-tags.latest at the lexicographic max instead of the newest publish

- **Area:** npm
- **Where:** crates/mynpm/src/packument.rs packument_modified / latest_snapshot
- **Problem:** latest_snapshot sorts candidate snapshots by a top-level "modified" key no record carries (first-party packuments nest time.modified under "time"; upstream packuments have no top-level modified either), so dist-tags.latest and time.modified froze at the lexicographic max packument (0.9.1 for @laputa-systems/ui-dashboard) after publishes of 0.10.0-0.11.3. Renderer fix merged in PR #14 with regression test; mynpm suite + clippy green. BLOCKER to shipping it to the live npm registry: the registry seals its current generation by re-hashing base+artifacts+packument bytes with the running renderer, so ANY packument-byte change makes the live generation unsealable by the fixed binary ("integrity: generation identity does not match its contents"). stuff republish npm routes through the same Seal::Current check and cannot cross it either (verified: its only steps are pull -> publish_site -> read_current(Seal::Current)). The npm registry has no adopt/re-seat entry point wired into republish (myoci and mycrates have adopt; see docs/PUBLISHING.md 296-321 for OCI). Advancing dist-tags.latest on the live registry requires, ONCE, an operator-run migration: r2-pull the npm bucket into a site, mynpm adopt --site-dir SITE to re-render + verify + switch the local current to a new generation, then stuff republish npm to stage and promote it, then verify npm view @laputa-systems/ui-dashboard dist-tags. Pulling the whole mirror may be large; verify disk and window before starting, run it supervised rather than unattended. Do NOT install a #14-built stuff (cargo install / usr sync) before that re-seat lands: the seal then rejects the pre-re-seat generation used for every subsequent npm publication on this machine until the migration lands.
- **Recommendation:** merge #14 (done) and record the exact completion path: operator (Joshua) runs the one-time pull -> adopt -> republish migration against the npm bucket, supervised, then npm view @laputa-systems/ui-dashboard dist-tags must report 0.11.3 and stuff publish npm --tarball must succeed again; then close this ticket. Alternatively, the tool gains a wired npm adopt (republish does adopt-then-promote), after which republish is a no-op-safe renderer catch-up; that is the durable fix for the missing command but is a bigger change than a one-time migration and wants its own review.
- **Fix with:** worker
- **Effort:** M




### STUF-82 · P2 · Worker gateway test intermittently sees an already-read body

- **Area:** Worker runtime
- **Where:** crates/stuff-worker/test/runtime.test.mjs:193 (the gateway forwards the host to the cached entrypoint)
- **Problem:** In stuff#9 CI run 43691840562 the worker-runtime job failed with TypeError Body is unusable: Body has already been read on the first cargo.text() call at runtime.test.mjs:202, after the same job passed on the PR's previous run with no Worker change between them. Something consumes the gateway response body before the test reads it; a shared or cached Response handed to two requests would do it. Unreproduced locally.
- **Recommendation:** Root-cause with repeated runs of that test (node --test with a loop) and read the gateway path that serves catalog.json for both hosts; fix the producer, not the test, and keep the test as the regression.
- **Fix with:** root-cause
- **Effort:** M


### STUF-84 · P2 · Retain deslop gains with fleet rules for coverage, the mutation lane, and strict profiles

- **Area:** Fleet policy
- **Where:** repomod/rules/ (new), fleet/policy/rust-tools.toml (new), docs/policy-development.md; reference implementation laputa-systems/srv Makefile coverage and mutants-diff targets, .github/workflows/ci.yml mutants job, .cargo/mutants.toml
- **Problem:** The deslop campaign proved the Rust recipe in srv (branch coverage, cargo-mutants 27.1.0 diff lane through taiki-e/install-action, exit 3 counted as detected, a whole-crate run for test-only diffs) and adopted strict settings per repository on evidence (Rust unsafe_code forbid; ty missing-type-argument and unsound-return-statement; Ruff ANN401). Nothing in repomod requires them, so a repository can drop its lane or profile, and every Rust repository copies the same Makefile block by hand.
- **Recommendation:** Add rules that apply only to repositories whose TODO-DESLOP.md Tests step is closed (or that already have the targets): make-coverage-target, mutants-diff-lane (job present, pinned tool, base ref through env), and strict-typing-profile for the settings adopted fleet-wide; give mutants-diff-lane a fixer that writes srv's Makefile block and job. Python and TypeScript lanes follow STUF-83.
- **Fix with:** none
- **Effort:** M


### STUF-86 · P2 · Expose positive observation actor sleep and wake evidence

- **Area:** OpenOrange lifecycle observability
- **Where:** deploy/openorange/rivet/server.py; Stats docs/CAMPAIGN-STATS-PERFORMANCE.md W3 and bench/results/2026-11-15-scale-prep-review/README.md; protected Lisa /home/josh/.work/stats-perf-campaign/
- **Problem:** Pinned Engine 3.1.2-rc.1 in the isolated stats-perf-scale-server fixture returns null sleep_ts, start_ts and connectable_ts for the active observation-store actor on repeated API inspection. Stats exposes no constructor-generation signal. This prevents confirming the after-sleep condition for 200 uncached browser selections per range; idle elapsed time and forced restarts cannot substitute. P2 priority assumed for the missing validation capability.
- **Recommendation:** Provide a supported positive per-actor sleep/eviction transition and wake or constructor-generation signal on the pinned runtime path, preserving unknown values. Verify a natural idle eviction and correlate its next request; do not infer sleep from elapsed time. Resume the Stats after-sleep acceptance study only with positive evidence.
- **Fix with:** root-cause
- **Effort:** M

