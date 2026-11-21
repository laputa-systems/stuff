Prefix: STUF
Next: 105

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

### STUF-102 · P1 · Stop refused envoy reconnects from feeding the Engine overload that refused them

- **Area:** OpenOrange Engine
- **Where:** Rivet `e5ed3911` `engine/packages/pegboard-envoy/src/connection.rs` (pre-init `EnvoyRead`, refusal at 1612-1617, disconnect write); the envoy client's reconnect loop; docs/openorange-engine-degradation.md sections 3 and 5
- **Problem:** On 2026-11-21 three capsule containers (owner unknown) ran `cargo test --workspace` on Lisa from 05:02 to about 05:11 UTC, holding load at 16-21 on 8 cores with 14% iowait. The production Engine's storage refused commands (`command_capacity`), its worker lease expired waiting on the object store, and it fenced and exited at 05:04 and 05:10. crates, mirror, npm and pypi returned 500 from about 05:02 to 05:24. After the outside load ended, the Engine stayed at about 750% CPU with every tokio worker busy. Each minute 150-850 envoy connects were refused as "storage could not register" with `retry_after_ms=100`, and most refusals then attempted an "envoy disconnect write", itself a storage command that also failed. Refusals generated more storage work, so the overload sustained itself until the worker fenced again at 05:21; after that restart it went idle and the registries recovered. A 30 s perf sample after recovery showed slatedb merge-iterator reads and allocation, so the spin itself was not profiled. The same envoy-refusal pattern occurred on the Threadripper standby on 2026-11-20 and 2026-11-21 (Stats STA-135).
- **Recommendation:** Reproduce in an isolated Engine: hold storage at `command_capacity` with several envoys reconnecting, and measure storage commands per refused connect. Then patch so a refused connect costs no storage write (skip the disconnect record for a connection that was never registered) and envoys back off exponentially with jitter, starting from the server hint and capped. The regression must show storage commands per refusal and the reconnect rate both bounded under sustained refusal, and the Engine draining once capacity returns without a restart. Carry it as a `rivet-e5ed391-*.patch` beside the existing candidates. Profile the next spin with perf (now installed on Lisa) before restarting.
- **Candidate:** `deploy/openorange/patches/rivet-e5ed391-envoy-refusal.patch` (SHA-256 `17041863ae7269915bdfb3b0a46c4a685f86768f33592e95fdd8a06668d95f50`) applies seventh, after staged-refusal, staged-head, empty-abort, page-read-refusal, inventory-read and actor-lifecycle, to a fresh checkout at `e5ed3911`. Server: `disconnect` writes nothing when neither the pool admission nor the record write landed, so a connect refused before storage registered it adds no pool disconnect, index delete or record update to the overload; a connection whose admission landed still releases its pool lease. The client half ships only in the mirrored rivetkit N-API addon, so the Engine image carries the server half alone. Client (`rivet-envoy-client`, shared by native and wasm transports): a hinted refusal keeps the server hint as the floor while its jitter ceiling doubles per consecutive refusal, capped at the ordinary reconnect ceiling, and an init from the engine resets the streak so a healthy session starts over. Two disconnect regressions and five backoff regressions (plus a third disconnect test that keeps the admitted-lease release) fail on the original code and pass with the patch; `cargo check -p pegboard-envoy` and `-p rivet-envoy-client` pass, and the wasm target checks. All seven patches apply in order to a pristine archive of `e5ed3911`.
- **Remaining:** not deployed and not run in an Engine. No isolated Engine reproduction was built, so "storage commands per refusal bounded" and "drains once capacity returns without a restart" are unproven at runtime; only the unit-level no-write and backoff-bound properties are. One residue is left by design: if a connect's pool-admission write landed and a later registration write was refused, its lease is not deleted, so it lapses after `ENVOY_HEARTBEAT_TIMEOUT_MS` (15 s, `pegboard/src/catalog.rs:1124-1126`); an expired lease does not block `PoolDelete` (`catalog.rs:1151-1169`), so this only delays nothing. The patch is not registered in `deploy/openorange/sources/sources.toml`, which is outside this task's writable paths, so the source manifest does not yet carry its purpose or hash. Profile the next spin with perf on Lisa before restarting.
- **Fix with:** root-cause
- **Effort:** M

### STUF-103 · P1 · Roll Lisa's Engine onto the patched laputa-systems build through a qualified rollout

- **Area:** OpenOrange Engine · Rollout
- **Where:** deploy/openorange/sources/sources.toml; deploy/openorange/lib/oobuild.py; deploy/openorange/patches/README.md; docs/openorange-rollouts.md; Lisa's `oo-engine` unit
- **Problem:** Production on Lisa runs the upstream `rivetdev/engine` image (`sha256:6e585002…`). The six Rivet repairs, now also on `laputa-systems/rivet` `laputa/e5ed391` (`128bcfc0`), have never run in production, and STUF-102's reconnect fix will join them. The rollout controller's only real adapter is the Stats native app on the Threadripper standby guest; nothing builds a patched Engine image, qualifies it against a copy of Lisa's Engine state, or swaps `oo-engine` under the maintenance lock with rollback.
- **Recommendation:** Done on 2026-11-21: `oo set-engine-image` with `upstream` rollback and `build-rivet-engine image` (`c7782d25`), the soak mode in `restore-rehearsal` (`13871a7f`), the native build `f8e364dc…` as image `sha256:98d3d60b…` on Lisa, a production-state rehearsal identical to upstream, and the fixed workload qualification (docs/openorange-engine-qualification.md). The qualified build does not reproduce across hosts, so the native build was qualified again. Remaining: the two 24-hour soaks on Lisa started about 07:15 UTC on 2026-11-21 (`/var/log/openorange/soak-{candidate,upstream}.log`); a pass needs no probe failure outside a restart window, all twelve restarts recovered, and candidate latency no worse than upstream. Then swap with `oo set-engine-image sha256:98d3d60b…` and an Engine-only restart, check the registries, and roll back with `oo set-engine-image upstream` on any failure. A contention drill belongs with STUF-102 on Threadripper.
- **Fix with:** blast-radius
- **Effort:** L

### STUF-88 · P2 · Keep actor inventory available during native resource collection

- **Area:** OpenOrange lifecycle observability
- **Where:** deploy/openorange/rivet/server.py; Stats bench/native-soak.py and bench/results/2026-11-15-soak-progress/README.md; protected Lisa maintained-rollup-soak-v2.jsonl
- **Problem:** The live 2026-11-15 Stats production soak recorded actor inventory HTTP 503 at 23 of its first 152 samples and one application-health timeout. W6 requires no unavailable groups, so the collection cannot establish plateau acceptance. This is observed diagnostic unavailability, not proof of production data loss or a classified Engine defect. P2 assumed for a repeatable gap blocking production resource validation. At 2026-11-16 04:11 UTC, one read-only production inventory sweep returned 200 for names and all eight first pages, without further cursors. The historical 503 did not reproduce; continuous availability remains unproven. Stats bench/results/2026-11-16-resume-diagnosis/README.md preserves the qualification. 2026-11-16 review: the actor-list 503s come from the Engine itself — the sampler hits cfg.engine_url directly with a Bearer token; this proxy maps Engine errors to 502, and the identity sidecar fails closed with 503 only when tailscaled is unavailable. Diagnosis needs the preserved indices and the live collection on Lisa; acceptance requires a complete 24-hour collection with zero unavailable groups. No change was made to the sampler or the shared Engine; the bounded-inventory-path design is open for the owner. The protected v2 collector now classifies new failures as depot.overloaded with volume_transition and a 100-ms hint. Candidate Engine source dc461cb uses bounded inventory-edge retries and the existing shared budget; seven dev/release tests and three restored fault controls pass. The full private release build succeeds. docs/openorange-inventory-retries.md records its contract and verification limits. Runtime refusal proof and a complete qualified 24-hour collection remain outstanding; no shared Engine or sampler changed. Latest evidence: The separate bounded collector captured HTTP 503, `depot.overloaded` and `Retry-After: 1` on three actor-name pages at sample 73. Other requests in that sweep succeeded. This classifies the new failures; historical samples still lack endpoint/error evidence. The in-progress 24-hour collection has already failed zero-unavailability acceptance. Its failed samples and protected bodies remain intact.
- **Recommendation:** Diagnose the failed actor-list requests using preserved sample indices without restarting the shared Engine or changing the active sampler. Establish a supported bounded inventory path that remains available during normal traffic, preserve unknown lifecycle states and explicit failures, and verify a complete 24-hour collection with zero unavailable groups. Handle the application-health timeout separately if it has an independent cause; do not hide outages with dropped samples or relaxed acceptance.
- **Fix with:** root-cause
- **Effort:** M

### STUF-90 · P2 · Classify the private Engine lease fence during TERM

- **Area:** OpenOrange recovery
- **Where:** docs/openorange-engine-term-fence.md; Stats bench/results/2026-11-17-observation-overhead/engine-recovery.json; protected Lisa /home/josh/.work/stats-perf-campaign/sta128-20261117/fresh/engine-study.stdout.log
- **Problem:** Nine gated Engine-only TERM/start cycles preserve all 219939 canonical observation events and unchanged Installation state, with the application processes unchanged. On the tenth TERM the patched release binary exits 1 after dependent_failed topology fencing and the singleton heartbeat-lifetime guard. The driver stops before starting cycle ten, so ten-cycle acceptance is unestablished. The original 203950-row import passes; no production impact or acknowledged data loss is demonstrated. The underlying shutdown trigger is unproven. P2 assumed for a repeated-recovery qualification blocker.
- **Recommendation:** Preserve the stopped depot and original receipt. Identify the first unexpected completion or cleanup drop before the dependent_failed fence, tracing the storage service owner, depot-client watcher and EngineBackground shutdown. Keep lease and heartbeat safeguards intact. Add a decisive regression for the established cause, then run a bounded private ten-cycle cohort with canonical table hashes and the unchanged fifteen-second readiness limit. Do not restart the shared Engine for this investigation.
- **Fix with:** root-cause
- **Effort:** M

### STUF-91 · P2 · Upgrade all Solid consumers to stable 2.0 using the changelog

- **Area:** Fleet · frontend dependencies
- **Where:** docs/campaigns/deslop-roadmap.md#upgrade-solid-consumers-on-resumption; fleet/catalog.toml; affected Solid consumer manifests and lockfiles
- **Problem:** The owner reports Solid 2.0 left RC on 2026-11-17 and explicitly requests upgrading every consumer on campaign resumption. Existing consumers and migration requirements have not yet been inventoried. P2 assumed for the requested fleet upgrade; no production defect is claimed.
- **Recommendation:** Use the stable release, changelog and migration guide to verify the remaining consumers listed in the roadmap. Check the compiler, JSX, router, test and SSR pins, then qualify each upgrade with lint, type checks, builds and relevant integration tests. Discover is outside campaign scope during the owner's rearchitecture.
- **Fix with:** upgrade-the-world
- **Effort:** L

### STUF-101 · P2 · Adopt buildlib for material shared build tooling

- **Area:** Fleet · build tooling
- **Where:** docs/campaigns/deslop-buildlib.md; docs/build-repos.md; repomod/rules/build_repos.py; eligible managed repositories
- **Problem:** Owner-requested 2026-11-20 adoption work. Six known consumers pin the original 0.1.0 wheel while buildlib main has advanced; custom acquisition and packaging remain elsewhere, the two source-lock validators disagree, and fresh Linux bootstrap qualification is not recorded fleet-wide. P2 tracks the requested initiative, not a claim that every non-adopter is defective.
- **Recommendation:** Execute BLD-0 through BLD-5 in the linked plan under existing campaign authority: classify the active fleet, qualify immutable artifacts and both linux-capsule interpreter paths, prove Node and bounded play pilots, migrate material overlaps, then enforce admitted consumers through read-only policy. Preserve native-tooling exceptions, current exclusions and stuff's independent recovery. Releases retain their existing boundary. Keep this ticket and evidence after deslop's main document retires.
- **Fix with:** deslop, linux-capsule
- **Effort:** L

### STUF-104 · P2 · Stop caching blob 404s for a year at the oci-blobs edge

- **Area:** OCI blobs · Edge caching
- **Where:** oci-blobs.17166969.xyz `/sha256/*` (Cloudflare Cache Rule in front of the Lisa origin); docs/PUBLISHING.md:209-212
- **Problem:** A GET or HEAD for a blob that is not yet uploaded returns `404 not found` with `cache-control: public, max-age=31536000`, and Cloudflare caches it (`cf-cache-status: HIT`). Reproduction 2026-11-21: a crabc build fetched 153 locked inputs from `https://oci-blobs.17166969.xyz/sha256/<hex>` minutes before `stuff publish oci --layout ... --repository crabc/image-inputs --tag x86_64` (generation 4b124444500568dec2362721) uploaded them. Afterwards every exact URL still answers 404 from cache (`age: 464`) while `?nocache=1` returns 200 with the right bytes, and the registry's own `/v2/crabc/image-inputs/blobs/sha256:<hex>` 307s to the poisoned URL. Any read that races a publish, or probes a digest before it exists, makes that content-addressed URL unusable at that edge for a year.
- **Recommendation:** Serve misses with `cache-control: no-store` (or a short max-age) and restrict the long immutable TTL to 200/206 responses. Accept when a HEAD for an absent digest followed by its upload and a second HEAD returns 200 on the second request, and existing 200 responses keep `public, max-age=31536000, immutable`.
- **Fix with:** root-cause
- **Effort:** S

### STUF-89 · P3 · Owned tools lack the design-cli help reference, examples, and footer

- **Area:** Owned-tool help
- **Where:** `fleet/policy/owned-tools.toml` (every `gap` entry outside joshuarli/usr), `docs/campaigns/owned-tool-maintenance.md` (Human help and provenance contract, Remaining tools), usr `dotfiles/base/.agents/skills/design-cli/SKILL.md`
- **Problem:** Agents learn an owned tool from its -h, but most fleet tools print no examples, many omit subcommand details from top-level help, some error on bare invocation, and about 40 commands still lack the owned-tool footer (`uv run repomod tools coverage` lists them). Sampled: fastermod, loc, xsh, vault print no or one example and no footer.
- **Recommendation:** Run one campaign over all repos at once, one worker per repository in parallel batches, one integrator for policy and backlog. Original tools (about 28: bctl, ctrs, defuddle-rs, ish, kache, loc, lz, mactop, play, soulseek-rs, stats, tansu, toolbox, pi-build, img, diff-pretty, doas-rs, e, fastermod, fz, gluon, mdevd-rs, srv, stuff, tinyland, tm, vault, xsh, zzz) get the full design-cli contract: complete top-level reference, an Examples: section with an example per command, bare invocation printing help when a command is required, and the footer. Forks and build distributions (rg, fd, jaq, rage, gh, syncthing, git-build, ssh-build, node-build, python-build, ffmpeg-build, cmake-build, llvm-prebuilt-musl, chromium-build) get only the footer through their maintained patch path, never an upstream schema rewrite. Owner decisions: land source only through each repo's workflow and do not release just for help; flip each policy entry from gap to help with its test as it lands. No parser migrations (for example clap to lexopt) in this campaign. Skip repos with no checkout (ghostty, mold, shck, swift-bylaws, view) and parked tm (laputa-systems/tm#28). Accept when `repomod tools coverage` reports no gap except recorded exemptions and parked or checkout-less repos.
- **Fix with:** design-cli, orchestrate
- **Effort:** L

### STUF-93 · P3 · An interruption after a fixer commit can delete its recovery branch

- **Area:** repomod · lifecycle
- **Where:** repomod/fix.py:486-493; docs/deslop-repomod-diagnose.md
- **Problem:** Confirmed on `40112564` with a local Git fixture: wrapping _commit_paths to complete the real commit and immediately raise KeyboardInterrupt leaves outcome.commits empty. Cleanup deletes the newly created fix branch although its tip contains the completed change. The object remains readable by SHA; permanent loss or later object collection was not demonstrated.
- **Recommendation:** Before deleting a newly created fix branch, inspect its actual tip against the base and preserve any completed commit independently of the recorded outcome list. Cover the precise post-commit interruption window with a real local commit and no remote writes.
- **Fix with:** lifecycle-concurrency
- **Effort:** S

### STUF-94 · P3 · A filtered line-count snapshot drops unselected index entries

- **Area:** repomod · inventory
- **Where:** repomod/loc.py:63-75; docs/deslop-repomod-diagnose.md
- **Problem:** Confirmed on `40112564`: snapshot two mocked real Inspection records A and B, then snapshot A with filtered=True. repos/B.json remains, but B disappears from index.json because _entries returns only selected repositories. The dashboard reads retained files directly, so missing dashboard rows were not established. The filtered metadata index no longer describes every retained repository.
- **Recommendation:** Merge selected line-count entries into the existing index for filtered snapshots while retaining full-snapshot deletion behavior. Assert the full index and unselected record bytes across a filtered refresh, including unchanged commit stamping.
- **Fix with:** durable-state
- **Effort:** S

### STUF-95 · P3 · Qualify repomod performance comparisons and attribution

- **Area:** repomod · benchmarks
- **Where:** bench/deps_perf.py, bench/suite.py, docs/deslop-repomod-bench.md
- **Problem:** The isolated preview workload verifies content and reports single-process resources, but has no reference comparison, regression gate, process-tree attribution, or isolated coverage of sync, snapshot and live status. Existing live workloads can access canonical checkouts and external services.
- **Recommendation:** Add isolated representative workloads and process-tree attribution, then qualify interleaved comparisons and a regression gate on an appropriate host. Keep Full manual-only.
- **Fix with:** bench-pyramid
- **Effort:** M

### STUF-96 · P3 · Qualify and retain a small hosted publication mutation check

- **Area:** repomod · publication
- **Where:** repomod/fix.py (push_fix_branch); tests/repomod/test_fix_push.py; tests/repomod/test_fix_safety.py; docs/deslop-repomod-tests.md
- **Problem:** The hosted publication mutation check was once called required but no job, selection or retention was ever qualified, so it is advisory. Publication is protected only by the ordinary suite; six of 127 push_fix_branch mutants survive as recorded equivalence dispositions.
- **Recommendation:** Only if wanted: choose an explicit list of publication functions and a critical regex naming them (push_fix_branch and its refusal checks), never a whole file or the whole inventory. Accept when (1) a hosted job runs the shared gate with that declared scope and fails on a missed mutant, (2) negative controls fail it: delete a refusal test and weaken one refusal branch, (3) the 3x timeout replay selects exactly one mutant, (4) runner cost and wall time are recorded and within a stated budget, and (5) the job is retained by registering the repository in fleet/policy/retention.toml [mutation-lane]. Run it first as advisory, then block only after those controls pass.
- **Fix with:** test-audit
- **Effort:** M

### STUF-97 · P3 · Mirror @pnpm/exe for each pinned pnpm packageManager release

- **Area:** repomod · dependency mirror
- **Where:** repomod/mirror.py; repomod/cmd/deps.py (_mirror)
- **Problem:** repomod deps mirror publishes what relocked lockfiles pin. pnpm 12 lockfiles record only pnpm under packageManagerDependencies, so @pnpm/exe at the pinned version is never mirrored. An older pnpm on PATH (for example Homebrew pnpm 11.0.2) switches to the packageManager pin by fetching @pnpm/exe@<pin> and fails with No matching version found against npm.17166969.xyz. Seen 2026-11-20 on joshuarli/tansu (its DSLP-24); repaired by hand with stuff publish npm --lockfile on a scratch lockfile depending on @pnpm/exe@12.21.0.
- **Recommendation:** When a repository pins packageManager pnpm@X, add @pnpm/exe@X (and its platform optional dependencies) to the mirror plan, with a test that a fleet repo pinning pnpm@X reports @pnpm/exe@X as missing until it is served.
- **Fix with:** repomod
- **Effort:** S

### STUF-98 · P3 · Deslop deploy/: OpenOrange host tooling and maintenance scripts

- **Area:** Needs owner · deploy
- **Where:** deploy/ (141 files), including deploy/openorange/ and its rivet TypeScript
- **Problem:** Deferred: deploy/openorange/ (host runtime, ingress, storage, recovery) is owned by a separate active OpenOrange campaign with dirty worktrees (docs/openorange-runtime.md, docs/campaigns/deslop-roadmap.md). The generic maintenance scripts (R2 pull, put and gc, store copy, fake S3, smoke checks) share that tree. Deslop edits here would collide with that work.
- **Recommendation:** The owner decides whether the OpenOrange campaign has finished or whether deslop takes the non-OpenOrange scripts separately. Until then do not schedule this component. If scheduled: Diagnose first (none exists), then Types, Tests and Dead code; accept with `make test-r2`, `make test-publish-lock`, `make test-store-copy`, `make pipecheck`, `make worker-deploy-test`; live checks (`make test-r2-live`, `make smoke-deployed`, deployments) stay opt-in.
- **Fix with:** deslop
- **Effort:** L

### STUF-99 · P3 · Upstream responses are buffered up to 1 GiB plus 64 MiB regardless of the caller's byte limit

- **Area:** mynpm · acquire
- **Where:** crates/mynpm/src/acquire.rs HttpsExchange::fetch and transfer
- **Problem:** Unreproduced; read from the code on 52c3999d. HttpsExchange::fetch reads the whole body into memory and stops only at TARBALL_BYTES + 64 MiB. The caller's max_bytes (64 MiB for packuments and metadata) is checked in transfer only after the full body is buffered, and a valid Content-Length is never compared with any limit. A hostile or faulty upstream metadata response can therefore hold about 1.06 GiB in memory per request, and four downloads run concurrently. A reproduction needs a local TLS origin for HttpsExchange; the offline fakes replace the Exchange trait and cannot show it.
- **Recommendation:** Pass max_bytes into Exchange::fetch, reject a Content-Length above it before reading, and stop the read loop at the caller's limit. Add a test with a fake Exchange that records the limit it receives, and a local TLS origin check if one is available.
- **Fix with:** deslop
- **Effort:** S

### STUF-100 · P3 · Wheel member lookups scan every member, so validation is quadratic in the member count

- **Area:** mypypi · wheel archive
- **Where:** crates/mypypi/src/wheel_zip.rs Archive::member; callers in crates/mypypi/src/validate.rs and acquire.rs
- **Problem:** Confirmed on 52c3999d in a debug build with generated wheels of empty files. inspect_wheel took 0.31 s for 5,000 members, 0.74 s for 10,000 and 1.74 s for 20,000; each name triggers mode, read, size and read_prefix calls that each scan the member list linearly. A 100 MB wheel can hold on the order of 800,000 central directory entries. Not extrapolated beyond 20,000 members.
- **Recommendation:** Index members by name when opening the archive (first entry wins, as today). Duplicate names are rejected by the callers, so the index changes no result.
- **Fix with:** deslop
- **Effort:** S

