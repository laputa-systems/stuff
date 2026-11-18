Prefix: STUF
Next: 93

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


### STUF-92 · P2 · Deliver deployment markers through the native Stats ingress

- **Area:** OpenOrange deployment
- **Where:** deploy/openorange/lib/deployments.py:69; deploy/openorange/DEPLOYMENTS.md; Lisa /etc/openorange/stats-direct.Caddyfile
- **Problem:** On 2026-11-18 OpenOrange activated Discover image discover:41024bef8145 and verified health, then oo record-deployment discover --if-current discover:41024bef8145 returned HTTP 404. The host queued oo-discover-5.json and the release command exited 1 despite the live release. The deployed deployments.py matches the repository SHA-256 0097baed7583228662b01a19508e3938a63955dc40bea2747d4b26bb94610cc8. The current Stats direct proxy on the configured private address accepts only POST /ingest/observe/v1/:service/batches and responds 404 for POST /ingest/services/:name/deployments.
- **Recommendation:** Route authenticated marker delivery through a supported Stats deployment-ingest surface while preserving the private proxy’s exact route allowlist. Confirm a real Discover marker reaches Stats, then use oo sync-deployments discover to drain the existing queue idempotently without restarting Discover. Document service enrollment for new apps such as discover-wine.
- **Fix with:** security
- **Effort:** M


### STUF-89 · P3 · Owned tools lack the design-cli help reference, examples, and footer

- **Area:** Owned-tool help
- **Where:** `fleet/policy/owned-tools.toml` (every `gap` entry outside joshuarli/usr), `docs/campaigns/owned-tool-maintenance.md` (Human help and provenance contract, Remaining tools), usr `dotfiles/base/.agents/skills/design-cli/SKILL.md`
- **Problem:** Agents learn an owned tool from its -h, but most fleet tools print no examples, many omit subcommand details from top-level help, some error on bare invocation, and about 40 commands still lack the owned-tool footer (`uv run repomod tools coverage` lists them). Sampled: fastermod, loc, xsh, vault print no or one example and no footer.
- **Recommendation:** Run one campaign over all repos at once, one worker per repository in parallel batches, one integrator for policy and backlog. Original tools (about 28: bctl, ctrs, defuddle-rs, ish, kache, loc, lz, mactop, play, soulseek-rs, stats, tansu, toolbox, pi-build, img, diff-pretty, doas-rs, e, fastermod, fz, gluon, mdevd-rs, srv, stuff, tinyland, tm, vault, xsh, zzz) get the full design-cli contract: complete top-level reference, an Examples: section with an example per command, bare invocation printing help when a command is required, and the footer. Forks and build distributions (rg, fd, jaq, rage, gh, syncthing, git-build, ssh-build, node-build, python-build, ffmpeg-build, cmake-build, llvm-prebuilt-musl, chromium-build) get only the footer through their maintained patch path, never an upstream schema rewrite. Owner decisions: land source only through each repo's workflow and do not release just for help; flip each policy entry from gap to help with its test as it lands. No parser migrations (for example clap to lexopt) in this campaign. Skip repos with no checkout (ghostty, mold, shck, swift-bylaws, view) and parked tm (laputa-systems/tm#28). Accept when `repomod tools coverage` reports no gap except recorded exemptions and parked or checkout-less repos.
- **Fix with:** design-cli, orchestrate
- **Effort:** L

