# Roadmap

This is the single plan for this repository: all current and future work, and the handoff for resuming it. Campaigns are sections below, and their items interleave in **Sequence**. "Resume the roadmap" means continue from **Status**.

## Status

- Native migration (NM): active since 2026-11-26. Production Stuff reads and publication authority run on the [native host](native-host.md) with no OpenOrange app, Rivet or Engine on their path (reads since 04:49 UTC, authority since the 05:14 handoff). Open: NM7 (24 h observation, GC resume, Rust-serving decision, removal of the guest's `oo-engine`/old image). Migration-induced failure windows are recorded in the campaign and halt any further reload-based change. Resume from [Campaign: Native Stats and Stuff](#campaign-native-stats-and-stuff).
- State: Owned tools first closed 2026-11-26. Acceptance passes: `uv run repomod lint --rule owned-tool-substitution --rule buildlib-usage` returns 0 findings fleet-wide, and `make repomod-lint` plus `make repomod-test` pass (1818 passed, 5 skipped). The principle and generated producer table stay in [docs/fleet.md](fleet.md#owned-tools-first); residual upstream installs are reasoned exemptions in `fleet/policy/owned-substitutes.toml`, each linked to an open producer ticket (STUF-117, STUF-123, STUF-126, STUF-127, STUF-128, STUF-129).
- Last accepted Stuff revision: `a92d66cc9d` on `main`, after kache#170 merged and its stale exemptions were removed; repomod tests, ruff and ty pass there. Owned-tools image v4 `sha256:aaec19e7…` and node 26.13.1 are approved.
- Needs owner: ghostty branch `lane/ot7-owned-tools` at `ae86acd0f` (no PR by that repo's rule — owner applies it, then removes `[exempt."joshuarli/ghostty"]` from `fleet/policy/buildlib.toml`); NODE-6 decided Alpine-only; laputa seed work deferred to LAP-94 with image publishing approved.
- Needs environment: llvm-prebuilt-musl#12 (LLVM-1) unverified — retry `make build && make verify` on threadripper, dispatch ci.yml, release, bump the image and rerun play's `build/owned-clang`. FFB-9 needs a hosted mutation-receipt generation job. cmake-build coverage needs a python-build 3.15.2 release. loc#33 needs a rebase and recheck.
- Other campaigns: owned-tool maintenance (tm#28, STUF-89); dependency friction F2 (kache#104 release) and F5; release archives (ctrs unpushed, fastermod uncommitted, xsh broader changes); stuff primary awaits Lisa's Engine soak. XSH-196/197 are with another session.
- Pre-existing, not from this campaign: 10 stuff worktrees under .work/wt (three oo-* trees hold uncommitted changes) and about 114 unmerged stuff branches; triage before reuse.
- Next: choose from the other campaigns above. Owned tools first needs no further local work.

## Charter

Read [fleet operations](fleet.md) and [fleet design](fleet-design.md) before fleet work. Sync first and preserve canonical checkouts and user data. Use each repository's current instructions, existing checks and tiered setup. Record local and hosted evidence separately. Do not treat unavailable runners or declarations as passing runtime proof. [TODO.md](../TODO.md) owns deferred tickets.

## Sequence

| ID | Campaign | Owned files | Prerequisites | Acceptance command or evidence |
| --- | --- | --- | --- | --- |
| V1 | Fleet verification | Selected repository's tests, benchmarks, typing and cleanup | Inspect current source and applicable evidence; use its supported runner | Repository's Change test, named benchmark, configured type checker and cleanup probe below |
| F4 | Dependency friction | `repomod/`, `fleet/`, producer and consumer release inputs | Inventory each release hand-off; preserve registry holds | One documented release command reaches consumer lockfiles; `uv run repomod lint --include-private --rule audit-upgrades` |
| STUF-89 | Owned-tool maintenance | `fleet/policy/owned-tools.toml`, affected owned tools and [TODO.md](../TODO.md) | Recheck pending PRs and each source checkout | `uv run repomod tools coverage` has no ordinary gaps; built help tests pass |
| A1 | Release archives | Producer release definitions and consumer installer pins | Consumers accept tar.xz before producers switch; verify held checkouts and current release state | `uv run repomod lint --rule release-archive-format --rule binary-release-standard`; verify downloaded archive and checksums per release |
| NM | Native Stats and Stuff | `crates/stuff-worker/native/`, `deploy/native/`, `deploy/openorange/` ingress and rollout adapters | Stats native parity (Stats roadmap NS); independent observer evidence | Per-stage acceptance in the campaign below |
| STUF-104 | Stuff primary | `deploy/openorange/`, `crates/stuff-worker/` and host runtime | Lisa Engine soak ends and is recorded; verify current state | Complete the cutover checks and canary in the procedure below |
| F5 | Dependency friction | usr sync, affected macOS fixtures | Identify supported pinned tools and fixture dependencies | macOS component slices record coverage and mutation; PLAY-55 closes |
| F6 | Dependency friction | Affected repository workflows | Inspect each job's actual runner needs and hosted access | Verify runner choice per workflow and compare standard-job queue times |

## Campaign: Fleet verification

### Goal and state

Qualify the catalog's test, benchmark, typing and cleanup boundaries. The baseline audit covered 72 managed repositories at `407249c6c`, including private repositories and excluding `zzz`. The catalog may have changed since. Declarations and strict-profile checks do not establish execution or a full type audit. [Audit](evidence/fleet-audit.md) and [recorded results](evidence/fleet-verification-results.md) identify per-repository gaps and revisions.

### Decisions

Use native tools and the [fleet quality standard](fleet.md#quality-standard). Start with small Rust tools, then other toolchains and services. Reuse evidence only when source, configuration, fixtures and runner match. Preserve fork-owned release and platform workflows and required check names. Inspect each workflow against its upstream merge base before changing it.

### Baseline

All 72 audited defaults declared `make test` and `make clean`; 39 had a root benchmark target. The recorded workflow check identified 16 first-party test workflow gaps. Each repo still needs proof that its targets exercise the intended work. The audit and results record the specific outstanding benchmark, typing, browser, VM, service and hosted-runner gaps.

### Acceptance

1. Inspect the current checkout, guidance and applicable evidence; record the exact revision.
2. Run native Change tests, with Full manual. Prove empty selection, required skip and timeout cannot be mistaken for completion. Keep coverage until a stronger test catches the same defect.
3. Check representative benchmark selection, preflight and completion of one named Change workload. Record host and service prerequisites. Qualify timing comparisons separately under the performance rules.
4. Run the configured type checker on audited boundaries. Record a bad program it rejects or an unchecked assertion removed. Retain the existing typing profile.
5. In a disposable checkout, create an owned output, a nested fixture of the same basename, a `.work` sentinel and an external target specified through the build environment. Run `make clean` twice: only the owned output disappears. Replace the output path with a symlink to the external target and verify refusal.
6. Follow default-branch rules before pushing. Record local and hosted checks independently, and continue local work when hosted evidence is blocked.

The baseline policy check is `uv run repomod lint --include-private --rule make-clean-target --rule gha-test-workflow --rule strict-typing-profile`.

### Needs environment

Use each repository's documented runner, fixtures and services. Private hosted jobs can be blocked by billing. VM, browser, Linux and hardware-dependent results require their named environments.

### Execution boundary and non-goals

Do not claim a benchmark from preflight or a dry run, or typing coverage from a declaration. Keep Full workloads manual and avoid changing unrelated repository policy.

### Reference

[Fleet audit](evidence/fleet-audit.md), [verification results](evidence/fleet-verification-results.md), [fleet quality standard](fleet.md#quality-standard).

## Campaign: Fleet dependency friction

### Goal and state

Remove recurring cross-fleet dependency friction. F1 registry failover and F3 buildlib adoption were completed on 2026-11-21. F2 waits on kache#104's release. F4 has one ptytest-to-tm hand-off completed; F5 and F6 were not started in the last campaign record.

### Decisions

- F2: keep kache and clang defaults where installed, but support cargo without them and a verified CPython on glibc. usr#49 merged. Accept when fresh `ubuntu:24.04` with rustup builds under usr's linked config with and without kache, and `sh sync` provides working `python3`.
- F4: automate producer-to-consumer hand-offs in repomod release and mirror flows. Ptytest 0.5.0 reached tm via `uv run repomod sync`, `uv run repomod fix --repo laputa-systems/tm --rule audit-upgrades --no-mirror`, then `uv run repomod merge --repo laputa-systems/tm`; tm#47 merged. The fixer also upgraded unrelated outdated direct dependencies and tm required a separate merge.
- F5: install measurement tools through usr sync and pin or decouple brew-dependent checks. PLAY-55 tracks the fixture hash drift.
- F6: move jobs without larger-runner needs to standard labels; private repository billing belongs to the owner.

### Baseline

F4 still needs a release trigger, own-registry cache invalidation, support for exact and git pins, updates to `sources.lock.json`, vendored copies and derived assets, missing producer bump or tag tooling, and a decision for private consumers. Remaining ptytest consumers include fz, xsh, e and defuddle-rs on 0.4, soulseek-rs on 0.3 and lz's git pin. Recheck current versions first.

### Acceptance

A dependency release reaches consumer lockfiles through one documented command. F5 requires Mac coverage and mutation results and closure of PLAY-55. F6 requires justified runner choices and lower standard-job queue time. F2 requires the clean-clone checks above.

### Needs environment

F2 needs a kache release containing kache#104 and a fresh Ubuntu capsule. F5 needs a suitable macOS host. F6 depends on hosted runner and billing availability.

### Execution boundary and non-goals

Respect Cargo publish holds and do not run live fleet fix while changing repomod. The Engine retry storm is STUF-102, outside this campaign.

### Reference

[Registry failover](registry-failover.md), [buildlib policy](build-repos.md#shared-build-tooling-across-the-fleet), [backlog](../TODO.md).

## Campaign: Owned-tool maintenance

### Goal and state

Make owned agent-facing tools discoverable and repairable. The owned-tool rule, `repomod tools which|coverage`, policy inventory and usr standing instructions landed. Help footers landed in several tools; remaining producers and controlled agent and release exercises remain open. STUF-89 tracks the help rollout. `uv run repomod tools coverage` is the current inventory; tm is parked on tm#28.

### Decisions

Resolve maintained ownership from catalog, installer and actual executable provenance, not a basename or banner alone. Record nonblocking problems in the owning repository and continue; a genuine blocker permits a focused repair under the standing usr instructions. Release only if a supported local build or existing distribution cannot deliver the verified fix.

Original tools expose a complete top-level reference from existing parser declarations, examples for every command, help on bare invocation when a command is required, and the owned-tool footer. Preserve bare invocations that perform work. Forks and build distributions add the footer through maintained source or patches without changing upstream schemas. Keep protocol versions, JSON, completion and ordinary output compatible. Land source and tests before marking policy coverage; do not release merely for help. Skip checkout-less and parked repositories until their blockers clear.

### Baseline

`fleet/policy/owned-tools.toml` tracks gaps. The STUF-89 backlog records pending repository PRs and the exact remaining rollout. Existing lookup only reports owned with install evidence, and `repomod/which.py` uses the standard library.

### Acceptance

Run `uv run repomod tools coverage` until no ordinary gap remains, and run the affected tools' built-help and behavior checks. Verify aliases, relocation, duplicate basenames, wrong origins, PATH shadowing and missing provenance. A controlled nonblocker exercise files or updates one producer ticket and continues; a blocker exercise tests a fix and retries the original operation. A mocked release exercise verifies revision, artifact, installation and retry, and confirms no release when a supported local path suffices. Check both usr instruction profiles and applicable harness adapters. Use focused `tests/repomod/` cases and `make repomod-lint` for Stuff changes.

### Needs environment

Built help and platform-specific checks require each tool's supported environment. Recheck open PRs and tm#28 before taking action.

### Execution boundary and non-goals

Preserve canonical checkouts, verify ownership and follow each repository's rules. No parser migration, mass release, new shared runtime dependency or general recovery orchestration system. Distinguish metadata coverage from observed built help and source changes from installed releases.

### Reference

[STUF-89](../TODO.md), [owned tools](fleet.md#owned-tools), `fleet/policy/owned-tools.toml`, usr's `dotfiles/base/.agents/instructions/owned-tools.md`.

## Campaign: Dependency ownership

### Goal and state

Report deterministically, from tracked data and without manual review, how much of the fleet's dependency surface is owned, mirrored through stuff, replaceable by an owned producer, or upstream with no owned alternative, and which externally invoked commands the fleet relies on beyond the base userland. The owner approved the four slices and an owned ast-grep fork on 2026-11-25. DO1 landed in 33b6201605 and 85ab3c4db9: `repomod deps ownership [--json]` classifies the tracked inventory. Its first fleet run (unique package names) found 36 owned, 800 mirrored through stuff (npm 770, pypi 30), 26 substitutable (17 apk packages such as git in 22 repositories and python3 in 12; setup-uv in 14, setup-node in 6, setup-python in 5; criterion in 4) and 1,896 upstream (cargo 1,192, npm 231, golang 180, apk 131, pypi 91). DO3 landed: laputa-systems/ast-grep is an owned fork at the fleet fork standard (owned help footer, Makefile, lint and CI workflows, upstream publishing workflows retired), its prerelease `release-ece6c9546dd52b2644d217c66bf107c08b83b87f` ships static-pie Linux musl and macOS builds, it is catalogued as a producer, and laputa-systems/buildlib#37 adds it to the tool table. DO4 landed in 94243980d8: `deps snapshot` parses workflow `run:` steps, Makefile recipes, shell scripts and Dockerfile `RUN` lines with the pinned ast-grep (`REPOMOD_AST_GREP` or PATH; it refuses another version) into a `command` ecosystem, and `deps ownership` reports 37 owned, 9 substitutable, 82 baseline and 1,105 external command names (top external: make 82 repositories, cargo 61, docker 49, curl 46, rustup 44, apk 35, rustc 30, readelf 27, shasum 26, sudo 22, wget 19). A fleet snapshot takes about 17 s. Running `make deps` now needs the owned ast-grep on the host; usr's installer does not yet install it. DO5 landed (50d08cf15e, 498195a463): the blocking `shell-portability` rule enforces the usr portability standard with path-scoped exemptions (about 370 fleet findings, led by shasum, stat -c, sed -i, echo -n and nproc). DO2 landed (ee78c018b7): system-package installs share one parser with `owned-tool-substitution` and appear in `deps ownership` (21 substitutable, 189 upstream). The campaign's slices are complete; remaining work is consumer remediation of the portability findings.

### Design

- `deps ownership` extends the existing inventory (`fleet/dependencies/v1/`) instead of scanning again. A component is owned when it is first-party or its source is a `joshuarli` or `laputa-systems` repository or fork; mirrored when an upstream package is served from the stuff registries; substitutable when `fleet/policy/owned-substitutes.toml` maps it to an owned producer; upstream otherwise.
- Command use is an inventory adapter, so `deps diff` and the dashboard show its trend. It parses shell with a real Bash grammar through the owned ast-grep build; the baseline userland (POSIX utilities, coreutils, base archivers) is policy data. A command class says only that an owned producer exists; which binary actually runs is install provenance, which `owned-tool-substitution` checks.

### Baseline

A 2026-11-25 prototype (line tokenizer over workflow `run:` steps, Makefile recipes, shell scripts and Dockerfile `RUN` lines of every catalogued checkout) found about 560 command names used in two or more repositories: 84 baseline, 25 with an owned producer (git 52 repositories, python3 51, gh 44, jaq 25, clang 20, node 18, rg 16), 7 upstream with an owned substitute (jq 16, npm 16, python 9, ccache 3) and about 450 external, roughly half of them tokenizer noise from quoted programs. Recurring external commands: make, cargo, curl, rustup, docker, readelf, apt-get, codesign, wget, pnpm, uv, rsync, brew, openssl, qemu-system-x86_64, gcc, pkg-config, otool, unshare, go and xcrun. The inventory then held 3,547 package names (cargo 1,235, npm 1,154, golang 180, apk 148, pypi 122, GitHub Actions 43, Docker images 34), 355 of them first-party.

### Acceptance

The DO1–DO4 rows in Sequence. The finished report runs in under a minute fleet-wide from the tracked inventory and exits 0 with JSON on stdout.

### Execution boundary and non-goals

No execution of managed-repository code, as for the rest of the inventory. Tracking every invocation inside interpreted programs (Python `subprocess`, Rust `Command`) is out of scope until the shell surfaces are complete.

## Campaign: Release archives

### Goal and state

Publish owned release archives and mirror artifacts as `.tar.xz`. The repomod rule and packaging fixer are live, consumers have gained tar.xz support, and most in-scope producers switched. The last handoff left ctrs, fastermod and xsh held and the consumer zip-removal phase unfinished. Recheck merged PRs and current releases before acting.

### Decisions

Consumers accept tar.xz before a producer switches. Archives use sorted entries, fixed mtimes and uid/gid 0; extractors reject symlinks and paths escaping the root. Exempt required external formats: python-build's uv install-only tar.gz, npm-pack tgz and wheels. Registry package formats, raw binaries, DMGs, manifests and checksums are not release archives. `zzz`, ignored mold and ghostty, and third-party archives only consumed are outside scope.

### Baseline

The mirror serves tar.xz and usr supports it for the ish family, img, lz, kache, gluon and Player. Previously held: ctrs had unpushed commits, fastermod had uncommitted work, and xsh's core archive needed its tag, preflight and target rewrites. Stuff#26 and play#13 were in flight in the last handoff; verify their present state before using the old sequence.

### Acceptance

After prerequisites land, sync and use `uv run repomod fix --rule binary-release-standard --rule gha-ubuntu --no-mirror --repo R` for eligible template producers. Review each diff before merge and release. Download a release archive and `SHA256SUMS` and verify them. Update ssh-build's ish pin and extractor, img's kache pins and other affected consumers. Drop zip fallback only after each producer's tar.xz release exists; retain it for excluded or held producers. Run the relevant repomod archive policy checks and consumer tests.

### Needs environment

Release publication and downloads require each repository's current release workflow and access. Preserve dirty or unpushed work and recheck current checkouts before proceeding.

### Execution boundary and non-goals

Do not publish a producer before its consumers can read tar.xz or alter externally required archive formats. Review existing branch state before repomod fix reuses a local fix branch.

### Reference

[Build repository contracts](build-repos.md), [fleet policy](fleet.md), [backlog](../TODO.md).

## Campaign: Native Stats and Stuff

### Goal and state

Run production Stats and Stuff with no OpenOrange or Rivet runtime, keeping
Cloudflare (DNS, TLS, Tunnel, Worker routes, R2 fallback), Versity, the
existing VM isolation and the bucket/version identities. This campaign
supersedes the earlier decisions to keep OpenOrange/Rivet for these two
applications and to treat native Node only as a reference adapter. It does
not change agentctl, Discover, nanoshop, discover-wine, tansu or the shared
Lisa Engine/store/ingress units those parked apps use. Stats-side stages live
in the Stats roadmap (campaign NS); this section owns Stuff and the shared
deployment path.

Hard gates: zero migration-induced public Stuff errors; no lost acknowledged
publication, receipt, artifact or retirement record; the private publisher
contract (30 s request timeout, 503 + `Retry-After` retried for up to 15
minutes, `crates/stuff/src/publish/coordinator.rs`) is preserved, so any
admission hold must be a 503 with `Retry-After` inside that window.

### Baseline (2026-11-26 03:10–03:50 UTC, read-only inspection)

| Fact | Observed |
| --- | --- |
| Public path | Cloudflare → `cloudflared` on Lisa → Caddy v2.11.9 `127.0.0.1:18480` (`X-OO-Ingress: public`, `/_s3`, `/_publication`, `/admin` denied, GET/HEAD only) → `127.0.0.1:18491` |
| Tailnet path | Caddy `100.68.104.43:443`, `X-OO-Ingress: tailnet`, identity sidecar, all nine hosts incl. `stuff-publish` → `127.0.0.1:18491` |
| Forward | Lisa `oo-stuff-primary-tunnel` (ssh `-L 18491:172.29.80.21:8080 -L 18492:172.29.80.10:7070` via Threadripper `127.0.0.1:49187`); 11 respawns recorded |
| Caddy reload | `grace_period 15s`; the largest object is a 1 GiB OCI blob (`stuff-oci-blobs/sha256/2c06ade9…`), so a reload under the current setting can truncate long downloads |
| Writer | Guest `stuff-primary` (Alpine 3.24.4, 8 vCPU, 8 GiB), `oo-app-stuff` image `stuff:5020a6f70e24` with five Rivet-backed coordinators; Engine `7df2c2be40ce`; Lisa's coordinators frozen as the fence and Lisa's `oo-app.stuff` removed |
| Store | `oo-store` versitygw `sha256:8319a530…` `posix --fsync --versioning-dir`, `172.29.80.10:7070`; six buckets ≈20 GB, 154,761 files; per-app IAM accounts with role `user` |
| Replica | Lisa `oo-replica-sync` is running (every 300 s) from `127.0.0.1:18492` (guest store) to R2; the STUF-104 record that says no replica is fed is stale |
| Observer | Threadripper `stats-observer` (`/var/lib/stats-observer/evidence.jsonl`, 60 s) probes Stats health and crates/npm/pypi/mirror status codes only |
| Incidents | Both guests restarted 2026-11-25 18:06 (three `console.log.crash-*` each on 11-25); Threadripper load ≈20 |

### Stages

| Stage | What | Prerequisites | Acceptance and evidence | Recovery | Status |
| --- | --- | --- | --- | --- | --- |
| NM1 | Native host (`crates/stuff-worker/native/`): existing entry, wasm planner and coordinator on node:http/node:sqlite | — | `pnpm run build:native && pnpm run test:native && pnpm run test:runtime && pnpm run lint && pnpm run typecheck` | None needed | Done (`1e3451edd7`, fixes through `baa0d1f462`) |
| NM2 | Evidence path: observer content probes on public and direct paths, full-body digests, rotated fsynced evidence | NM1 | Threadripper `/var/lib/stats-observer/content.jsonl`; 28 targets every 15 s | Revert observer unit | Done (Stats `ed0eb708`, pool fix `1c71da65`) |
| NM3 | Private reader parity on real buckets | NM1, NM2 | `deploy/native/parity.mjs`: 2,545 requests over 499 URLs, 458 MB, 0 mismatches against the live app | Stop candidate | Done |
| NM4 | Caddy reload rehearsal | NM3 | 40 s and 1 GiB downloads survive reloads; 21,039 keep-alive requests over 20 local reloads, 0 failures | n/a | Done; production still showed resets (below) |
| NM5 | Public reads to native readers | NM4 | Windows at 04:10, 04:49, 05:02 and 05:12 (probe files under Threadripper `~/stuff-native-rehearsal/window/`) | Reader recovery: withdraw a reader, or route back to another reader | Done; failures recorded |
| NM6 | Writer handoff | NM5, rehearsal `test/native-handoff.test.mjs` | Guest journal `/var/lib/stuff-native/handoff-20261126/journal/`: no live lease, five exports, canonical import, fence, authority generation 2, admission at 05:14:01; publication held 12 s; store inventory unchanged (154,359 data and 70 version files) | Before 05:14:01: unwind; since then: reverse handoff only | Done; canary below |
| NM7 | Observation, GC resume, Rust-serving decision, removal of the guest's `oo-engine` and old `oo-app.stuff` image | NM6 + 24 h | 24 h post-cutover observation; restore rehearsal | Retained exports, old image and Engine depot | Open |

### Improvement cycle (2026-11-26)

1. **Cost.** Native readers spent about 6 ms of CPU per request under live
   and probe traffic (control-listener `/metrics`; 2.0 S3 requests per read).
2. **Hypothesis and objective.** Re-deriving the SigV4 key (four chained
   HMACs and a key import) on every S3 request is a measurable part of that
   cost; caching the derived key lowers reader CPU per request beyond the
   run-to-run spread. Objective: CPU µs per request on a fixed workload.
3. **Baseline and protocol.** The idle standby reader served 60 s of 32-way
   load over eight live read routes (`/tmp/measure.mjs` in the guest, CPU
   from the reader's own counters), alternating baseline and candidate
   releases: base 2,834 (pre-run), 2,910, 3,879, 4,882, 3,119 µs; candidate
   2,579, 2,769, 1,586 µs. Guest load 1.8–2.7; one baseline run lost a third
   of its throughput to host contention.
4. **Change.** `acadf76eaf` caches the imported signing key per day, region
   and secret (bounded to 16 entries).
5. **Result.** Lower in all three pairs and every candidate run below every
   baseline run (one-sided Mann–Whitney p ≈ 0.02, 5 vs 3); the median falls
   about 17%. The ±30% spread under uncontrolled host load means the
   magnitude is not established; this is recorded as a direction, not a
   percentage win.
6. **Qualification and rollout.** `pnpm run test:native` and the runtime
   suite pass; parity against production 1,537 requests, 0 mismatches;
   artifact `0cd13c02ea11` rolled to both readers through
   `rollout-reader.sh` at 05:36 UTC.
7. **Next.** Measure again on a quiet host with more pairs before claiming a
   size; the next candidate is the second S3 request per pointer read.

### Rust serving decision

The engine-free reader is the supported final reader. It reproduces the live
contract byte for byte (parity above), its direct-path medians are below the
OpenOrange app's on every probed route (observer, legacy 04:00–04:49 versus
native 05:15–06:00: Cargo config 214 → 34 ms, `llms.txt` 224 → 42 ms, PyPI
simple 48 → 24 ms, OCI ping 20 → 7 ms), and it costs about 110 MiB RSS and a
few milliseconds of CPU per read. A Rust reader would need the hostname,
catalog, OCI and alias logic the Worker entry already has, plus its own S3 and
streaming path, for no measured need, and Stuff would then carry two serving
implementations. The Rust crates remain the publisher and the shared
protocol/catalog libraries; no experiment dependency was added.

### Recorded failures (2026-11-26)

| Window (UTC) | What clients saw | Cause | Disposition |
| --- | --- | --- | --- |
| 04:10:02–04:36:48 | Four 500s from the native reader out of about 75,000 requests (paths not recorded) | undici cancelled the body of a garbage-collected store Response before the entry forwarded it | Reads returned to the legacy app at 04:36:48; fixed with a forced-GC regression test (`b013ec18c6`); failure logs now carry method, host and path |
| 05:02:28 | Eight probe requests (Threadripper and workstation) reset | Caddy reload closed idle keep-alive connections that clients reused | Reload-based route changes stopped; readers fail over by health check (`baa0d1f462`) |
| 05:12:02 | Two probe requests reset at the reload that installed the health-checked route | same | Last planned reload of the Stuff route; reader restarts use `rollout-reader.sh` (05:13:16, no failures) |

Until `0a2c1bbe10` the window probe's public and direct requests shared one
keep-alive pool per hostname, so a request labelled public may have used a
tailnet socket; the observer had the same flaw (fixed in Stats `1c71da65`).
The workstation's own OCI publisher state was stale (it expected revision 14,
`c0ed40fc…`, while another machine had already published revision 15 before
this campaign), so its first native canary attempt correctly refused with a
conflict and nothing was uploaded; canaries run with a fresh
`STUFF_STATE_HOME`.

Canary through the native authority: `stuff publish oci --layout` of a
one-layer image to `native-canary-20261126:native-authority-b`. The first run
(05:16:45) was killed by its own 50-minute `timeout` while pulling the
registry's existing blobs (STUF-131), before any upload; OCI stayed at
revision 15 and the upload lease expired. Reruns then failed with
`integrity: No such file or directory` until the interrupted `site/` was moved
aside (STUF-132). The run of 06:10:37–06:28:58 published generation
`02bfc28c52e74efc5ace63aa` (27 objects, 133,545 bytes uploaded, 363 skipped):
the coordinator reached revision 16 with 16 receipts and no lease, the tag and
manifest resolve publicly, the layer blob changed from 404 `no-store` to 200
`public, max-age=31536000, immutable` with its digest, and Lisa's replica sync
copied pointer `02bfc28c…` to R2. The publisher had been restarted onto
`0cd13c02ea11` at 06:07:16 (ready in 1.1 s), so the canary exercised the
final artifact. The publisher was also stopped 05:19:50–05:21:47 for the
restore drill's consistent copy; the first run retried through it.

Post-cutover hardening (2026-11-26, after an independent review of
`69fbf0a284..main`):

- **Store credentials:**
  - Readers now hold a store user with read-only bucket policies on the six
    Stuff buckets, proved first on a scratch bucket.
  - Readers run as `stuff-reader`, which cannot open `main.env`
    (`4c9cebeacd`).
  - Lisa's replica sync completed unchanged afterwards.
- **Release `db5c4ad01313` (merge `bb011147f1`):**
  - A handoff that fails during freeze now unwinds, and its hold budget
    starts at the first freeze.
  - Authority returns to legacy only when every native coordinator is frozen
    and idle; admission is atomic with the authority check.
  - Per-waiter admission deadlines and a bounded body on coordinator reads.
  - Chunked GET/DELETE bodies are framed when proxied (closes a
    request-smuggling path).
  - Withdrawal persists in `/run/stuff-native/NAME/`.
  - The publisher drain is 30 s; long blob streams are cut, coordinator
    operations are never abandoned.
  - Client disconnects are logged as `request_cancelled`.
  - A ranged read requires 206.
  - Per-minute event-loop samples.
  - New `/healthz` under the Stats health contract.
- **Rollout:** both readers rolled with no ingress reload, then the publisher
  restarted in 1.2 s. 896 observer probes 10:15–10:24 UTC recorded no failure.
- **Stats probe:** `https://stuff.17166969.xyz/healthz` probes `ok`.
- **Follow-ups:**
  - STUF-132: an interrupted OCI state pull is not resumable.
  - STUF-133: the guest's idle memory is not returned to the host.
  - STUF-134: both reader forwards share one tunnel.

## Campaign: Stuff primary on Threadripper

### Goal and state

Stuff's write primary moves from Lisa's shared Engine to its own VM on
Threadripper. Lisa keeps the edge: Cloudflare, `cloudflared` and Caddy. Its
ingress sends Stuff's public and tailnet hostnames to the VM over a supervised
SSH forward. The move takes no downtime. Reads never stop, and publishers retry
while the coordinators are frozen. Lisa's Engine is never restarted, so
Discover, nanoshop and agentctl are not touched.

### Baseline

The following is the recorded target configuration; verify current live state before cutover.

#### What runs where

| Piece | Where |
| --- | --- |
| VM | Threadripper `/var/lib/stuff-primary/` (`os.qcow2`, a 160 GiB preallocated `data.qcow2`, `seed.iso`), OpenRC `stuff-primary-vm` and `stuff-primary-vm-watchdog` from `deploy/openorange/standby/` |
| Reservation | `cpu.weight 10000`, `memory.min 9G`, `memory.swap.max 0`, `io.latency` 10 ms on the image's disk |
| Guest | Alpine 3.24, 8 vCPU, 8 GiB. `/opt/openorange` from this repository; the overlay `/etc/openorange/overlay.toml` disables Rivet, the platform bridge, the tunnel and DNS and caps the Engine at 4 CPUs and 3 GiB. Only `oo-store`, `oo-engine` and `oo-app.stuff` run |
| Engine | The seven-patch candidate `sha256:7df2c2be40ce9d4fa40ddccc4ae20383088b9a5b38754ea94d7430c7c5e74918` on a fresh depot |
| Access | `~/.config/stuff/primary/ssh_config` (`stuff-primary`, through Threadripper). The host's `shutdown` key may only power the guest off |
| Forward | Lisa `oo-stuff-primary-tunnel` (`deploy/openorange/standby/oo-stuff-primary-tunnel.openrc`): `127.0.0.1:18491` is the guest app, `127.0.0.1:18492` the guest store. The guest key may open only those two destinations |

The guest has its own Engine, so its coordinator state is moved with the
coordinator handoff ops (`docs/openorange-runtime.md`), not by copying a depot.
The Stuff buckets are copied with their extended attributes, so object ETags
and version IDs stay identical.

#### Load drill

On 2026-11-21 from 16:48 to 17:19 UTC, Threadripper ran 64 unconfined busy
loops and repeated 8 GB direct writes beside the VM's image while the guest
served reads. Host load ranged from 10 to 132. All 30 one-minute samples showed
no Engine warning (`command_capacity`, `could not register`,
`request_deadline_exceeded`, `fenced`, `overloaded`) and no failed probe round.
The guest's probe made 845 reads of five registry paths, every one a 200:
p50 116 ms, p99 433 ms, max 4.3 s, against a p99 of 338 ms beforehand.
Production Stats health on the same host stayed 200 throughout. The
reservation holds; disk contention adds tail latency but no errors.

### Acceptance and cutover

Run after Lisa's Engine soak has ended and been recorded. Each step lists its
check and its rollback. Until the guest is thawed in step 7, Lisa remains the
only writer and every step is reversible.

1. **Deploy the handoff build to Lisa.** `crates/stuff-worker/orange/deploy.sh lisa`
   from `main`. Reads fail over to R2 while `oo-app.stuff` restarts.
   `main` includes the STUF-104 blob-miss fix.
   Check: `oo deployment stuff` names the new image, a HEAD for a random
   absent `https://oci-blobs.17166969.xyz/sha256/<hex>` carries
   `cache-control: no-store`, and
   `POST /_publication/cargo/thaw` with the coordinator token answers 200; the
   previous build answers 404 for that op.
   Rollback: the script restores the previous image.
2. **Refresh the guest's Stuff environment.** Copy Lisa's
   `/etc/openorange/apps/stuff.env` and `stuff.extra.env` into the guest. Run
   `oo secrets` there so the Engine-derived values point at the guest Engine,
   then build the guest's image from the commit deployed to Lisa in step 1
   (`crates/stuff-worker/orange/build-image.sh stuff-primary`, then
   `oo set-image stuff stuff:<sha12>`) and restart `oo-app.stuff`. Since
   2026-11-21 the guest runs `stuff:5020a6f70e24`, which already has the
   STUF-104 fix; rebuild only if step 1 deploys a later commit.
   Check: `curl -H 'Host: crates.17166969.xyz' http://172.29.80.21:8080/current/registry/config.json`
   in the guest answers 200.
3. **Pre-copy the buckets.** Lisa's root has no route to the guest, and the
   guest's sshd allows no remote forwards, so the operator's machine relays one
   rsync session. Lisa runs the sender, the guest runs the client, and two pipes
   carry the protocol between them:

   ```sh
   mkfifo f
   ssh lisa 'doas rsync --server --sender -lHogDtpAXre.iLsfxCIvu --numeric-ids . SRC/' < f |
     ssh -F ~/.config/stuff/primary/ssh_config stuff-primary \
       'rsync -aHAX --numeric-ids --delete -e /root/stdio-rsh x:SRC/ SRC/ 3<&0 4>&1 1>&2' > f
   ```

   `/root/stdio-rsh` copies its stdin to fd 4 and fd 3 to its stdout, and exits
   when fd 3 closes:

   ```sh
   #!/bin/sh
   exec 5<&0
   cat <&5 >&4 &
   out=$!
   cat <&3
   kill $out 2>/dev/null
   ```

   Run it for each `store/data/stuff-*` and `store/versions/stuff-*` under
   `/var/lib/openorange`. The sender's flags are what the guest's rsync 3.5.2
   asks for with `-aHAX --numeric-ids --delete`; print them again with
   `-e` pointing at a script that echoes its arguments if either rsync changes.
   Check: a repeat run reports `Number of regular files transferred: 0`, and a
   sampled object's `user.etag` is equal on both sides. On 2026-11-21 the
   relay carried `stuff-oci` with every `user.*` attribute intact.
4. **Freeze Lisa's coordinators.** For `cargo npm pypi oci mirror`:
   `POST https://stuff-publish.17166969.xyz/_publication/REGISTRY/freeze`.
   New publishes now receive 503 with `Retry-After: 30` and retry. In-flight
   publishes finish.
   Check: `GET .../export` answers 200 for all five, which means no lease is
   live. Rollback: `POST .../thaw` on each.
5. **Final delta and export.** Run the step 3 rsync again; it must report no
   changes when repeated. Save each registry's export.
   Check: each export's `current.generation` equals the bucket's `current`
   object in the guest.
6. **Import into the guest.** Post each export to the guest coordinator's
   `import` op through the guest app with the coordinator token and the
   gateway secret. Import must be the first op each guest coordinator sees:
   any other op, `export` included, seeds an empty coordinator from the
   bucket's `current` object, and import then answers `409`.
   Check: each guest export equals Lisa's export. Rollback: stop the guest app,
   discard its Engine depot, thaw Lisa.
7. **Switch the route and thaw the guest. Point of no return.**
   Install and start `oo-stuff-primary-tunnel` on Lisa. Write
   `/etc/openorange/apps/stuff.recovery.env` with the guest's
   `GATEWAY_SECRET`. Add `"stuff": {"mode": "primary", "upstream":
   "127.0.0.1:18491"}` to `/etc/openorange/recovery-routes.json`, keeping the
   other entries. Run `oo render --stdout`, then `oo reload-ingress`. Stop and
   disable Lisa's `oo-replica-sync`, because Lisa's frozen pointers would
   otherwise rewrite R2's `current` objects backwards. Then
   `POST .../thaw` on the guest for all five registries.
   Check: public reads carry no `x-stuff-served-by`; a canary `stuff publish`
   succeeds and reads back. Make the canary an OCI push, and HEAD one of its
   new layer URLs on `oci-blobs` before the push (404, `BYPASS`) and after it
   (200, `public, max-age=31536000, immutable`); this is STUF-104's live
   acceptance. Lisa stays frozen as the fence.
   Rollback before the canary publish: restore `recovery-routes.json` and
   reload, freeze the guest, thaw Lisa, restart Lisa's replica sync. After the
   first write lands on the guest, roll back only by repeating this handoff in
   the other direction.
8. **Feed the replicas.** In the guest, install and start `oo-replica-sync`
   with Lisa's `replica-sync.env` (the guest store has the same endpoint
   address and credentials). On Lisa, a second sync instance copies from
   `http://127.0.0.1:18492` into Lisa's store.
   Check: after a canary publish, R2 and Lisa name the new generation within
   ten minutes.
9. **Rotate the store credential.** The guest store's Stuff account key was
   exposed in an operator transcript on 2026-11-21. Create a new account in the
   guest store, update `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY` in the guest's
   `stuff.env`, restart `oo-app.stuff`, then delete the old account.

### Execution record (2026-11-24)

The handoff was executed. Live evidence, in runbook order:

1. Lisa deployed `stuff:5020a6f70e24` from the clean worktree at that commit
   (`oo deployment stuff` version 5). A HEAD for an absent
   `oci-blobs` layer returned `404`, `cf-cache-status: BYPASS`,
   `cache-control: no-store`; `POST /_publication/cargo/thaw` returned 200.
2. The guest already ran the same image and served
   `curl -H 'Host: crates.17166969.xyz' http://172.29.80.21:8080/current/registry/config.json`
   with 200. Its app binds the private IP, not `127.0.0.1`.
3. All six `data/stuff-*` and five `versions/stuff-*` trees were copied with
   the FIFO relay. The shipped `/root/stdio-rsh` failed with
   `cat: write error: Resource temporarily unavailable` under throughput; it
   was replaced on the guest with a Python pump that clears `O_NONBLOCK` and
   retries writes. Repeat rsync reported no changes after the final delta.
4. All five Lisa coordinators froze with `liveLease: false` and produced
   `GET .../export` 200 (`cargo` r12, `npm` r12, `pypi` r26, `oci` r6,
   `mirror` r1).
5. The final delta copied only the changed `current` pointers.
6. Import initially returned `coordinator not empty`: the guest app's
   readiness probe (`GET /`) seeds each coordinator from the bucket pointer,
   so an import cannot be the first op after a normal app start. The guest
   Engine depot was moved aside (backups `log.pre-import3-*` and
   `objects.pre-import3-*`), `oo provision` recreated namespace `stuff`, the
   readiness probe was temporarily removed from the guest's `oo-app.stuff`
   unit, and import ran before any read. All five returned
   `{"imported":true}`; each guest export is byte-identical to Lisa's, and
   each guest bucket `current` matches the imported generation. The unit was
   restored and `oo wait app stuff 90` passes.
7. `oo-stuff-primary-tunnel` was installed on Lisa with its existing
   `~/.local/share/stuff-primary` key, `stuff.recovery.env` received the
   guest gateway secret, and `recovery-routes.json` gained
   `{"stuff":{"mode":"primary","upstream":"127.0.0.1:18491"}}`. Lisa's
   installed `oo`/`oolib.py` predated primary-route support and were refreshed
   from this repository; `oo validate` and `render --stdout` then showed both
   the public and tailnet 18491 routes. `oo reload-ingress` succeeded. Public
   probes of stuff/crates/npm/pypi/oci answer with no `x-stuff-served-by`.
   `oo-replica-sync` was stopped and removed from the default runlevel, then
   all five guest coordinators were thawed (200 `{"frozen":false}`).

8. Not performed: no replica is fed, so there is no read-only fallback. The
   R2 Worker and its routes remain deployed but stale; see
   [registry failover](registry-failover.md).
9. The guest store's exposed account was replaced in place in
   `/var/lib/openorange/store/iam/users.json` and `stuff.env` (old access key
   `OOAPP10D…` is gone, new key `OOAPP834…` is present), and `oo-app.stuff`
   was restarted. Public reads stayed 200.
10. Canary: `stuff publish oci --layout` produced generation
    `6acfbe3ff87b3cc5f81c10ac`, revision 7, 16 new objects. The new layer
    returned `404`/`BYPASS`/`no-store` before the push and `200` with
    `public, max-age=31536000, immutable` after it (STUF-104's live check).
    The public tag returned 200 with no `x-stuff-served-by` header.
11. Lisa's `oo-app.stuff` was stopped and removed from the default runlevel.
    `oo deployment stuff` still reports
    `recoveryWriter: 127.0.0.1:18491`; public stuff/crates/canary reads stayed
    200 after the decommission.

Lisa's Engine remains frozen as the rollback fence. The owner explicitly
parked Discover, discover-preview, nanoshop, agentctl and discover-wine on
Lisa on 2026-11-24, so their Engine/store and the edge units stay in place;
no cutover for them is planned. This closes the Stats/Stuff cutover: Lisa no
longer hosts a canonical Stats or Stuff deployment, and no read replica is
fed.

### Decisions

Keep Lisa as the only writer until the guest is thawed. Preserve the fencing and rollback order below.

### Needs environment

Wait for Lisa’s Engine soak to end and be recorded. This procedure needs access to Lisa and Threadripper, the guest, coordinator credentials and publication tools.

### Execution boundary and non-goals

Do not restart Lisa’s Engine or disturb other applications. After the first guest write, reverse the handoff rather than thawing Lisa directly.

### Reference

[OpenOrange runtime](openorange-runtime.md), [rollouts](openorange-rollouts.md), [STUF-104](../TODO.md).

## Later

- STUF-91: finish the stable Solid 2.0 consumer upgrade when its registry and VM prerequisites are met; Discover remains excluded during rearchitecture.
- STUF-95: qualify repomod performance comparisons and attribution.
- STUF-102, STUF-103 and STUF-104: Engine recovery, rollout and OCI edge follow-ups are in [TODO.md](../TODO.md).
- STUF-105 through STUF-113: component findings and reproduction details are in [TODO.md](../TODO.md) and [reconciliation evidence](evidence/retired-p3-reconciliation-20261121.md).
