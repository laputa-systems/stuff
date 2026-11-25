Prefix: STUF
Next: 119

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
- **Recommendation:** Deploy the seven-patch image. Finish the paired soak on the Threadripper standby, require no probe failure outside a restart window and a drained Engine, then swap `oo-engine` with `oo set-engine-image sha256:7df2c2be…`. Move `sources.toml:30-32` from `deployment = "held"` to production once deployed. Profile the next spin with perf on Lisa before restarting.
- **Design:** `deploy/openorange/patches/rivet-e5ed391-envoy-refusal.patch` (SHA-256 `17041863ae7269915bdfb3b0a46c4a685f86768f33592e95fdd8a06668d95f50`) applies seventh, after staged-refusal, staged-head, empty-abort, page-read-refusal, inventory-read and actor-lifecycle, to a fresh checkout at `e5ed3911`. Server: `disconnect` writes nothing when neither the pool admission nor the record write landed; a connection whose admission landed still releases its pool lease. Client (`rivet-envoy-client`, shared by native and wasm transports): a hinted refusal keeps the server hint as the floor while its jitter ceiling doubles per consecutive refusal, capped at the ordinary reconnect ceiling, and an init from the engine resets the streak. Two disconnect regressions and five backoff regressions fail on the original code and pass with the patch; both packages and the wasm target check. All seven patches apply in order to a pristine archive of `e5ed3911`. The isolated Threadripper drill (`deploy/openorange/bin/drill-envoy-storm`, `docs/openorange-engine-qualification.md` § Envoy-refusal contention drill) ran both images on 2026-11-21: the candidate refused 33,510 connects with 0 disconnect writes and drained in 0.129 s (quiesce 5.59 s), while the upstream pin refused 24,688 with 98,760 disconnect writes and drained in 0.068 s (quiesce 6.33 s); neither restarted. The drill does not reproduce the self-sustaining phase (upstream also drained in 0.07 s), so a soak is still required. An admitted lease whose registration write was refused lapses after `ENVOY_HEARTBEAT_TIMEOUT_MS` (15 s, `pegboard/src/catalog.rs:1124-1126`); an expired lease does not block `PoolDelete` (`catalog.rs:1151-1169`).
- **Fix with:** root-cause
- **Effort:** M

### STUF-103 · P1 · Roll Lisa's Engine onto the patched laputa-systems build through a qualified rollout

- **Area:** OpenOrange Engine · Rollout
- **Where:** deploy/openorange/sources/sources.toml; deploy/openorange/lib/oobuild.py; deploy/openorange/patches/README.md; docs/openorange-rollouts.md; Lisa's `oo-engine` unit
- **Problem:** Production on Lisa runs the upstream `rivetdev/engine` image (`sha256:6e585002…`). The six Rivet repairs, now also on `laputa-systems/rivet` `laputa/e5ed391` (`128bcfc0`), have never run in production, and STUF-102's reconnect fix will join them. The rollout controller's only real adapter is the Stats native app on the Threadripper standby guest; nothing builds a patched Engine image, qualifies it against a copy of Lisa's Engine state, or swaps `oo-engine` under the maintenance lock with rollback.
- **Recommendation:** Remaining: pass the paired 24-hour soaks (no probe failure outside a restart window, all twelve restarts recovered, candidate latency no worse than upstream; explain any candidate failure from its evidence directory), then swap Lisa with `oo set-engine-image sha256:7df2c2be…` and an Engine-only restart, check the registries, and roll back with `oo set-engine-image upstream` on any failure. Landed 2026-11-21: `oo set-engine-image` with `upstream` rollback and `build-rivet-engine image` (`c7782d25`), soak mode in `restore-rehearsal` (`13871a7f`), the native build `f8e364dc…` as image `sha256:98d3d60b…`, a production-state rehearsal and the fixed workload qualification (docs/openorange-engine-qualification.md). The first soak pair failed after a peer drill stopped production `oo-app.stuff`; `181b7170` fixed the restart race and now keeps timestamps, failed responses and logs. The rerun started 09:38 UTC with the seven-patch candidate and the upstream pin; logs are `/var/log/openorange/soak-{candidate,upstream}.log`.
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
- **Where:** fleet/catalog.toml; affected Solid consumer manifests and lockfiles
- **Problem:** The owner reports Solid 2.0 left RC on 2026-11-17 and explicitly requests upgrading every consumer on campaign resumption. Existing consumers and migration requirements have not yet been inventoried. P2 assumed for the requested fleet upgrade; no production defect is claimed.
- **Recommendation:** Remaining: finish `laputa-ui-dashboard`'s RC pins once stable Solid, renderer and Vite plugin are served by Stuff, and close bctl's VM acceptance. Discover stays excluded during the owner's rearchitecture. Use the stable release, changelog and migration guide; check the compiler, JSX, router, test and SSR pins, then qualify each upgrade with lint, type checks, builds and relevant integration tests.
- **Fix with:** upgrade-the-world
- **Effort:** L

### STUF-104 · P2 · Stop caching blob 404s for a year at the oci-blobs edge

- **Area:** OCI blobs · Edge caching
- **Where:** oci-blobs.17166969.xyz `/sha256/*` (Cloudflare Cache Rule in front of the Lisa origin); docs/PUBLISHING.md:209-212
- **Problem:** A GET or HEAD for a blob that is not yet uploaded returns `404 not found` with `cache-control: public, max-age=31536000`, and Cloudflare caches it (`cf-cache-status: HIT`). Reproduction 2026-11-21: a crabc build fetched 153 locked inputs from `https://oci-blobs.17166969.xyz/sha256/<hex>` minutes before `stuff publish oci --layout ... --repository crabc/image-inputs --tag x86_64` (generation 4b124444500568dec2362721) uploaded them. Afterwards every exact URL still answers 404 from cache (`age: 464`) while `?nocache=1` returns 200 with the right bytes, and the registry's own `/v2/crabc/image-inputs/blobs/sha256:<hex>` 307s to the poisoned URL. Any read that races a publish, or probes a digest before it exists, makes that content-addressed URL unusable at that edge for a year.
- **Fix with:** root-cause
- **Effort:** S
- **Recommendation:** Remaining, in the Stuff primary cutover (`docs/roadmap.md#campaign-stuff-primary-on-threadripper` steps 1, 2 and 7):
  1. Deploy a Worker image that contains the origin fix below to Lisa. The Threadripper guest has it (`stuff:5020a6f70e24`; a miss answers `no-store`).
  2. Accept live with a HEAD for an absent digest, its upload, and a second HEAD that must return 200, while existing 200 responses keep `public, max-age=31536000, immutable`.

Landed 2026-11-21: blob-host misses (an absent object or a malformed `/sha256/` path) now return `cache-control: no-store` instead of `public, max-age=60`. Present blobs keep the immutable header on GET, HEAD and 206. The runtime test `an oci blob read before its upload is not cached, and the uploaded blob is immutable` performs absent HEAD and GET, the upload, then HEAD, GET and range; it fails on the previous Worker with `public, max-age=60`.

Edge, same day: the `/sha256/*` Cache Rule (zone ruleset `stuff cache rules`, version 3) now keeps the year-long edge lifetime for 200 and 206 only, sets 300 to 599 to no-store, and respects the origin's browser lifetime. Before, it overrode every status to a year. The 153 poisoned `crabc/image-inputs` blob URLs were purged. Afterwards all 154 of that manifest's blobs answer 200 with `public, max-age=31536000, immutable`, a second read is a `HIT`, and the registry's `/v2/crabc/image-inputs/blobs/` 307s to a working URL. Three HEADs and a GET for a random absent digest each answered 404 with `cf-cache-status: BYPASS`. The Lisa Worker still sends `public, max-age=60` on that miss until step 1.

The `crates-blobs.17166969.xyz` `/blobs/*` rule had the same flaw: a HEAD for an absent path returned `404` with `public, max-age=31536000`, and the second was a `HIT`. It got the same status-code TTLs (ruleset version 4); absent paths now answer `BYPASS`, and `stuff doctor --registry cargo --sample-artifacts` still matches a sampled crate's hash.

### STUF-116 · P2 · Owned-tool lookup cannot verify usr's gluon install

- **Area:** Owned tools
- **Where:** fleet/policy/owned-tools.toml:285-287 (record = "gluon"); repomod/which.py; usr tools/sync/installer.py install_gluon
- **Problem:** meson, ninja and gluon-build resolve to usr's gluon release under ~/.local/share/gluon/current, but which.py reports unverified with 'no install record at /Users/josh/gluon': the record path is home-relative and usr writes no record file there, and no installer-manifest evidence matches. Agents are told to trust only owned, so they conclude meson is upstream and may reach for another install.
- **Recommendation:** Point the gluon commands at evidence usr actually produces (the dl-owned installer manifest entry or a release record under ~/.local/share/gluon), add a which.py regression for a gluon-style current/releases layout, and confirm `which.py meson --json` reports owned on a synced host.
- **Fix with:** none
- **Effort:** S

### STUF-117 · P2 · Musl-dynamic owned builds cannot run on glibc CI runners

- **Area:** Owned tools
- **Where:** laputa-systems/ffmpeg-build ffmpeg-runtime-*-linux-musl; laputa-systems/python-build cpython-*-linux-musl; laputa-systems/buildlib setup/action.yml; docs/roadmap.md OT5
- **Problem:** On ubuntu-26.04-arm the buildlib setup action installed the locked ffmpeg-runtime and `ffmpeg -version` failed with 'cannot execute: required file not found': the binary needs /lib/ld-musl-aarch64.so.1, which Ubuntu runners lack (and the runtime also needs libva). python-build's musl builds have the same limit, which is why buildlib-run falls back to uv's upstream CPython on glibc. Static owned tools (gluon, rg) ran fine. Until fixed, consumers on GitHub-hosted Linux runners cannot use these producers and need exemptions.
- **Recommendation:** Pick one fleet-wide fix: either the setup action provisions a pinned musl loader (and the runtime's shared libraries) on glibc hosts from an owned producer such as llvm-prebuilt-musl's sysroot, or ffmpeg-build and python-build publish a fully static or glibc-loadable variant. Prove it with the buildlib setup workflow running `ffmpeg -version` and `python3 -c 'import ssl'` on ubuntu-26.04 and ubuntu-26.04-arm.
- **Fix with:** architect
- **Effort:** M

### STUF-118 · P2 · Rotating an app's store key leaves its buckets owned by the deleted user

- **Area:** openorange · store
- **Where:** deploy/openorange/bin/oo (cmd_secrets, provision_store)
- **Problem:** On 2026-11-24 at 18:17 the stuff primary's S3_ACCESS_KEY_ID was changed by hand and the old store user deleted, without running `oo provision stuff`. The ORANGE_R2_* bindings kept the deleted key and every stuff bucket stayed owned by the deleted user, so all bucket requests answered 403 AccessDenied: publication failed at `list stuff-mypypi`, the coordinator Durable Objects could not load, and the app stopped passing readiness after its next restart. `oo provision stuff` repaired it on 2026-11-25 by rewriting the bindings and changing each bucket's owner.
- **Recommendation:** Give key rotation one command (for example `oo rotate-store-key APP`) that creates the new user, runs change-bucket-owner for every app bucket, rewrites the derived bindings and only then deletes the old user; make `oo health` fail when an app's bucket owner or ORANGE_R2_* key differs from its S3_ACCESS_KEY_ID.
- **Fix with:** none
- **Effort:** M

### STUF-89 · P3 · Owned tools lack the design-cli help reference, examples, and footer

- **Area:** Owned-tool help
- **Where:** `fleet/policy/owned-tools.toml` (every `gap` entry outside joshuarli/usr), `docs/roadmap.md` (owned-tool maintenance), usr `dotfiles/base/.agents/skills/design-cli/SKILL.md`
- **Problem:** Agents learn an owned tool from its -h, but most fleet tools print no examples, many omit subcommand details from top-level help, some error on bare invocation, and about 40 commands still lack the owned-tool footer (`uv run repomod tools coverage` lists them). Sampled: fastermod, loc, xsh, vault print no or one example and no footer.
- **Recommendation:** Remaining: land the five pending PR checks (ctrs, img, toolbox, mdevd-rs, xsh) and the chromium-build draft, flip each policy entry from `gap` to `help` with its test, then reach `repomod tools coverage` with no ordinary gap. The campaign method is settled: one campaign over all repos at once, one worker per repository in parallel batches, one integrator for policy and backlog. Original tools get the full design-cli contract (complete top-level reference, an Examples: section, bare invocation printing help, footer); forks and build distributions get only the footer through their maintained patch path, never an upstream schema rewrite. Land source only through each repo's workflow and do not release just for help. No parser migrations. Skip checkout-less and parked repos.
- **Fix with:** design-cli, orchestrate
- **Effort:** L

### STUF-93 · P3 · An interruption after a fixer commit can delete its recovery branch

- **Area:** repomod · lifecycle
- **Where:** repomod/fix.py:486-493; tests/repomod/test_fix_safety.py
- **Problem:** Confirmed on `40112564` with a local Git fixture: wrapping _commit_paths to complete the real commit and immediately raise KeyboardInterrupt leaves outcome.commits empty. Cleanup deletes the newly created fix branch although its tip contains the completed change. The object remains readable by SHA; permanent loss or later object collection was not demonstrated.
- **Recommendation:** Before deleting a newly created fix branch, inspect its actual tip against the base and preserve any completed commit independently of the recorded outcome list. Cover the precise post-commit interruption window with a real local commit and no remote writes.
- **Fix with:** lifecycle-concurrency
- **Effort:** S

### STUF-94 · P3 · A filtered line-count snapshot drops unselected index entries

- **Area:** repomod · inventory
- **Where:** repomod/loc.py:63-75; tests/repomod/test_loc_snapshot.py
- **Problem:** Confirmed on `40112564`: snapshot two mocked real Inspection records A and B, then snapshot A with filtered=True. repos/B.json remains, but B disappears from index.json because _entries returns only selected repositories. The dashboard reads retained files directly, so missing dashboard rows were not established. The filtered metadata index no longer describes every retained repository.
- **Recommendation:** Merge selected line-count entries into the existing index for filtered snapshots while retaining full-snapshot deletion behavior. Assert the full index and unselected record bytes across a filtered refresh, including unchanged commit stamping.
- **Fix with:** durable-state
- **Effort:** S

### STUF-95 · P3 · Qualify repomod performance comparisons and attribution

- **Area:** repomod · benchmarks
- **Where:** bench/deps_perf.py, bench/suite.py
- **Problem:** The isolated preview workload verifies content and reports single-process resources, but has no reference comparison, regression gate, process-tree attribution, or isolated coverage of sync, snapshot and live status. Existing live workloads can access canonical checkouts and external services.
- **Recommendation:** Add isolated representative workloads and process-tree attribution, then qualify interleaved comparisons and a regression gate on an appropriate host. Keep Full manual-only.
- **Fix with:** bench-pyramid
- **Effort:** M

### STUF-96 · P3 · Qualify and retain a small hosted publication mutation check

- **Area:** repomod · publication
- **Where:** repomod/fix.py (push_fix_branch); tests/repomod/test_fix_push.py; tests/repomod/test_fix_safety.py
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
- **Problem:** Deferred: deploy/openorange/ (host runtime, ingress, storage, recovery) is owned by a separate active OpenOrange campaign (docs/openorange-runtime.md). The generic maintenance scripts (R2 pull, put and gc, store copy, fake S3, smoke checks) share that tree. Deslop edits here would collide with that work.
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

### STUF-105 · P3 · A tar.gz mirror artifact buffers a whole member before the decompression cap

- **Area:** mymirror · archive
- **Where:** crates/mymirror/src/archive.rs `extract` (TarGzip arm) and `tar_members`
- **Problem:** Reproduced on `d51b2786`. `TarXz` and `Zip` bound decompression with `.take(MAX_DECOMPRESSED + 1)`, but `TarGzip` hands an unbounded `GzDecoder` to `tar_members`, whose `entry.read_to_end` buffers a whole member before `enforce_cap` runs. A 7.3 MB `.tar.gz` holding a single 1.5 GiB member took 10.3 s and peaked at 1.09 GB RSS (debug build, macOS) before it was rejected. macOS compresses zero pages, so that RSS figure understates the buffer. The artifact must first match its manifest SHA-256 pin, so exposure requires a pinned hostile or faulty archive. Reproduction is in docs/evidence/retired-p3-reconciliation-20261121.md.
- **Recommendation:** Bound each member read by the remaining cap plus one (or wrap the gzip decoder in `.take(MAX_DECOMPRESSED + 1)`, as for xz). Add a regression that a gzip member larger than a lowered test cap fails without reading past it.
- **Fix with:** os-boundaries
- **Effort:** S

### STUF-106 · P3 · myoci push reads chunk-size and trailer lines without a byte cap

- **Area:** myoci · push
- **Where:** crates/myoci/src/push.rs `read_chunked_body`
- **Problem:** Reproduced on `d51b2786`. `read_line` for chunk sizes and trailers has no per-line cap or trailer count limit. With a body limit of 1 KiB, a client sent 256 MiB of hex digits with no newline. The server consumed and buffered all of it before failing with `SizeInvalid`. Exposure requires the push token, and `READ_TIMEOUT` applies per read, not per line. `writer.rs` `BodyReader::read_line` already caps lines at 4,096 bytes.
- **Recommendation:** Read chunk-size and trailer lines through a capped line reader (4 KiB, matching the writer) and bound the trailer count. Add a regression that a newline-free chunk-size line fails after the cap without consuming the rest of the stream.
- **Fix with:** os-boundaries
- **Effort:** S

### STUF-107 · P3 · Importing a deeply nested OCI index overflows the stack

- **Area:** myoci · import
- **Where:** crates/myoci/src/import.rs `walk_descriptor`; callers `import_layout` and `import_from` (crates/stuff/src/publish/oci.rs:462-468)
- **Problem:** Reproduced on `d51b2786`. `walk_descriptor` recurses once per nested `Image::Index` and has no depth cap. Cycles are stopped by `walk.manifests`, but `mirror/graph.rs` and `mirror/acquire.rs` cap depth at 32. A chain of 10,000 distinct nested indexes aborted the process with a stack overflow on an 8 MiB thread (debug build); 1,000 succeeded. `import_from` copies a remote image with oras before this walk, so an upstream image can reach it during `stuff publish oci`.
- **Recommendation:** Apply `MAX_GRAPH_DEPTH` to the import walk, or make it iterative with the same cap, and return `Error::Limit`. Add a regression with a chain one deeper than the cap.
- **Fix with:** os-boundaries
- **Effort:** S

### STUF-108 · P3 · The mirror's non-public address filter admits IPv6 loopback and unspecified

- **Area:** mymirror · acquire
- **Where:** crates/mymirror/src/acquire.rs `is_restricted_address`
- **Problem:** Reproduced on `d51b2786`. `is_restricted_address` returns false for `::1` and `::`, but true for `127.0.0.1`. The IPv6 `SUBNETS` cover ULA, link-local, NAT64 and multicast, and IPv4-mapped addresses are rejected separately. A mirror upstream host whose DNS resolves to `::1` therefore passes the check, and the fetch reaches a local HTTPS listener.
- **Recommendation:** Add `::/128` and `::1/128`. Extend the address-table test with both, and with `127.0.0.1` for parity.
- **Fix with:** security
- **Effort:** S

### STUF-109 · P3 · myoci writer leaves R2 staging on early failure and decrements its connection count by hand

- **Area:** myoci · writer
- **Where:** crates/myoci/src/writer.rs `upload_r2` (`.r2-<hex>-<session>` staging) and `run` (`active` counter)
- **Problem:** Code-reading lead on `d51b2786`, not reproduced. When `std::fs::copy` or the keys `write` fails, `upload_r2` returns before `remove_dir_all(&stage)`, leaving a partial blob copy under `uploads/`. No sweep of `.r2-*` was found. `run` decrements `active` after `handle_connection` returns. Native release builds unwind on panic (only `wasm-release` sets `panic = "abort"`), so a panicking connection thread would leak a slot permanently. `serve.rs` uses an `ActiveGuard` drop guard for the same job.
- **Recommendation:** Reproduce first: inject a copy failure and check for a leftover stage, and inject a handler panic and count `active`. If either reproduces, use drop guards for the stage directory and the counter.
- **Fix with:** lifecycle-concurrency
- **Effort:** S

### STUF-110 · P3 · The Worker's immutable publication check leaves the R2 body open on a size mismatch

- **Area:** stuff-worker · OCI publication
- **Where:** crates/stuff-worker/entry.ts `immutableText` (line 534)
- **Problem:** Code-reading lead on `d51b2786`, not reproduced. After a conditional `put` conflict, `immutableText` reads `meta.get(key)` and short-circuits on `object.size !== value.byteLength`, throwing `PublicationConflict` without consuming or cancelling `object.body`. `serve` cancels every R2 body it does not hand to a `Response`, so the codebase already treats an open body as a leak. Only the conflict path is affected.
- **Recommendation:** Cancel `object.body` before throwing on the size mismatch. Cover it with a fake R2 object that records cancellation.
- **Fix with:** lifecycle-concurrency
- **Effort:** S

### STUF-114 · P3 · npm inventory rejects valid external local links

- **Area:** repomod · inventory
- **Where:** repomod/dependencies/adapters/javascript.py, _npm_edges
- **Problem:** A version 3 package-lock generated by npm 11.20.0 can record a file:../sdk link and a ../sdk manifest entry whose devDependencies are installed by the SDK's own lockfile. npm ci --offline --dry-run --ignore-scripts accepts the consumer lock, but the dependency inventory requires the SDK's devDependencies to resolve inside the consumer lock and reports parse_error, making the repository fail strict coverage.
- **Recommendation:** Add a fixture with a consumer and independently locked local SDK. Verify that the consumer retains its local link and the SDK lock owns its dev dependency edges. Preserve errors for unresolved required entries owned by the consumer lock.
- **Fix with:** reference-parity
- **Effort:** S

### STUF-115 · P3 · Verify repomod mutation scope beyond the five protected decisions

- **Area:** Fleet tests
- **Where:** tests/repomod/mutation_gate.py; .github/workflows/repomod-mutation-trial.yml; docs/repomod-mutation.md
- **Problem:** The mutation check protects only checkout refusal, upstream fetch, workflow matrix, snapshot entry and fixer publication decisions; wider snapshot, catalog and policy decisions and whole-file scope are unverified, so the hosted workflow runs only on its trial branch and is not registered for retention.
- **Recommendation:** Choose the next bounded decision set (snapshot, catalog or policy), add its witness tests and shard, prove it with a negative control, and only then decide whether to register the workflow in fleet/policy/retention.toml.
- **Fix with:** test-audit
- **Effort:** M

### STUF-111 · P4 · stuff-server matches route prefixes against the raw request target

- **Area:** stuff-server · routing
- **Where:** crates/stuff-server/src/config.rs `Config::match_route`; caller crates/stuff-server/src/main.rs:224
- **Problem:** Reproduced on `d51b2786`. `match_route` receives the request target, including its query, so with routes `""` and `mirror`, `/mirror?x=1` selects the root route with rest `/mirror?x=1`. Longer paths are unaffected, because `stuff_http::plan_route` strips the query from the rest. The original report also flagged untrimmed prefixes in a directly constructed `Config`; `main.rs` trims every prefix and only tests construct `Config` directly, so that part is dismissed.
- **Recommendation:** Strip the query before route matching and add the bare-prefix-with-query case to `longest_prefix_wins`.
- **Fix with:** root-cause
- **Effort:** S

### STUF-112 · P4 · Range parsing accepts plus-signed positions

- **Area:** stuff-http · conditional requests
- **Where:** crates/stuff-http/src/condition.rs `parse_range`
- **Problem:** Reproduced on `d51b2786`. `parse_range("bytes=+0-+1", 10)` returns `Ok([0..=1])` because `str::parse::<u64>` accepts a leading `+`. RFC 9110 positions are `1*DIGIT`, and an invalid range should be ignored rather than served as a 206.
- **Recommendation:** Require ASCII digits before parsing each position, and add `+` cases to the invalid-range tests.
- **Fix with:** root-cause
- **Effort:** S

### STUF-113 · P4 · Worker OCI error responses set content-length from UTF-16 length

- **Area:** stuff-worker · OCI errors
- **Where:** crates/stuff-worker/entry.ts `writeErrorPlan` (line 378) and `ociFetch` (line 752)
- **Problem:** Probed under `workerd` at DSLP-15's base and still present on `d51b2786`. Both set `content-length` from `String.length`, which counts UTF-16 code units. A tags list with `n=%C3%BC` returned a 101-byte body declared as 100. `workerd` drops the header and delivers the full body, so no truncation was observed. Correctness depends on that runtime normalization.
- **Recommendation:** Use the encoded byte length, or omit the header and let the runtime set it. Assert the header against the byte length in the existing worker harness case.
- **Fix with:** root-cause
- **Effort:** S
