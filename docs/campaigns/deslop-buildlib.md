# Deslop: adopt shared build tooling

Owner request, 2026-11-20: make buildlib the default for most nontrivial projects managed by
stuff, account for usr's `linux-capsule` skill, and commit the plan to the deslop campaign.
Tracking ticket: STUF-101 in [TODO.md](../../TODO.md). This is an accepted plan, not a migration
or capsule qualification receipt. The lasting policy is
[Shared build tooling](../build-repos.md#shared-build-tooling-across-the-fleet).

## Decision and scope

Require `laputa-buildlib` where first-party build tooling materially reimplements its supported
operations: verified acquisition, source-lock reading, release manifests, reproducible archives,
checksums, supported target mapping, or ELF/Mach-O inspection and normalization. Judge the
tooling's behavior, not repository size or product language. One substantial duplicate or a
concrete integrity gap can justify adoption; an unused import cannot.

Keep native compilation and package tools, product-specific policy, task entrypoints, and runtime
dependencies with their current owners. Buildlib remains a small, standard-library-only Python
library. Its upstream rule still applies: add a shared helper only when at least two real
consumers need it. Do not turn it into a build graph, subprocess framework, deployment manager,
test runner, package manager, or universal bootstrap for every language.

Every active catalog entry gets one reviewed disposition:

| Disposition | Meaning and completion evidence |
| --- | --- |
| Shared helpers required | Named local implementations overlap buildlib materially. Record the paths, replacement APIs, pins and migration proof. |
| Bootstrap only | Newer Python is needed, but no shared build primitive replaces material local code. Use the shared bootstrap and count this separately from helper adoption. |
| Native tooling sufficient | Direct native commands or an established smaller implementation already meet the contract. Record the reason and the change that would trigger reassessment. |
| Deferred | An existing exclusion, active conflicting lane, unsupported platform, unavailable artifact or missing environment prevents this slice. Name the blocker and retry condition; do not report adoption as complete. |

Existing adopters use the first disposition but still need a current pin and bootstrap audit.
`IGNORE` entries and pristine upstream/vendor trees are outside the migration denominator.
Record current deslop exclusions separately; a fleet-wide policy does not reopen them.

## Evidence at planning time

Re-read these sources before implementation. Inventory and source review identify work; they do
not prove clean builds, current releases, or capsule passes.

| Source | Reviewed revision and finding |
| --- | --- |
| stuff | `4b6c811947f1f5b80eb0ba5c80c7096e15327ffe`: [catalog](../../fleet/catalog.toml) has 66 active entries, nine tagged `build`; the existing contract already requires Python build repositories to share lock readers. Reconciled the subsequent campaign pause/check-ups at `63d8dfc646bd8c7bf0e58dd77e53e73595bea36d`; this lane stays queued for resumption. |
| buildlib | [50d8081532a4f338527252fe4cf4f0adb10c893c](https://github.com/laputa-systems/buildlib/tree/50d8081532a4f338527252fe4cf4f0adb10c893c): Python >=3.15, no runtime dependencies, helpers and shell bootstrap described below. |
| usr | [acacb4ecbb3cf67c7a26cf2c902073893e5e2140](https://github.com/joshuarli/usr/tree/acacb4ecbb3cf67c7a26cf2c902073893e5e2140): [linux-capsule](https://github.com/joshuarli/usr/blob/acacb4ecbb3cf67c7a26cf2c902073893e5e2140/dotfiles/base/.agents/skills/linux-capsule/SKILL.md) prescribes the vendored buildlib bootstrap and two Linux interpreter paths. Read the latest skill when executing. |
| Existing consumers | The tracked [dependency inventory](../../fleet/dependencies/v1/repos/) identifies CMake, Node, Python, FFmpeg, Chromium and **joshuarli/pi-build**, all pinning 0.1.0; current manifests confirmed those pins. The older build campaign's list of five initial adopters is historical. |

### Qualify the artifact before expanding use

The [v0.1.0 comparison](https://github.com/laputa-systems/buildlib/compare/v0.1.0...50d8081532a4f338527252fe4cf4f0adb10c893c)
contains 63 subsequent commits. The tag resolves to `e8274f561d87ac009f752a9571acec52abce3eec`,
but current source still declares version 0.1.0. The
[bootstrap lock](https://github.com/laputa-systems/buildlib/blob/50d8081532a4f338527252fe4cf4f0adb10c893c/bootstrap/python.lock)
pins wheel SHA-256 `edd102a1713c903f93e19b10036983d123dd76fa1b04a0e5f3c5070f00a95383`,
also present in Node's original adoption lock. Current source fixes and APIs are not evidence
about those installed bytes. The new vendored bootstrap and the old wheel are separate artifacts.

Post-tag changes include ELF PIE/shared-library classification and `require_pie`, removal of
`ELFHeader.elf_class`, `ELFHeader.is_64` and the ELF inspection report's `is_64`, Mach-O validation,
scan-error propagation, redirect fallback, and manifest snapshotting. Before selecting a baseline:

1. Test the intended candidate wheel against every known consumer's relevant tests, including
   excluded repositories as read-only compatibility checks where their access/environment allows.
   Record missing evidence without dispatching changes to an excluded repository.
2. Prepare a new immutable version, source revision, wheel digest, release notes and consumer
   compatibility record. Never replace the bytes of 0.1.0 or depend on a floating main branch.
3. Publication retains the campaign's existing authority boundary. If the qualified artifact is
   unavailable, record the precise release step as blocked and continue inventory, fixtures and
   local candidate checks. A plan or local candidate pass does not authorize publication.
4. Once available, update the consumer's exact package pin, lockfile, any wheel entry in
   `sources.lock.json`, and vendored bootstrap wheel pin together. Record bootstrap source revision
   and file digests separately from package version. Preserve prior pins for a simple revert.

### Reconcile two definitions of a valid lock

The current [repomod checker](../../repomod/rules/build_repos.py) and
[buildlib reader](https://github.com/laputa-systems/buildlib/blob/50d8081532a4f338527252fe4cf4f0adb10c893c/src/buildlib/locks.py)
disagree on these cases:

| Input | repomod | buildlib |
| --- | --- | --- |
| Empty version string | Accepts | Rejects |
| Non-HTTPS URL string | Accepts | Rejects |
| `size: 0` | Rejects | Accepts |
| Empty `inputs` list | Rejects | Accepts |

Resolve the intended contract in [build-repos.md](../build-repos.md) with affected consumers
before changing acceptance. Retain repomod's read-only, multi-finding diagnostics. Use the same
provenance-tracked test vectors in both projects; document intentional additional fleet policy
instead of claiming identical parser semantics. Do not add a third validator.

Stuff must build and recover while its own registries are unavailable. Do not add a normal
dependency on the solely stuff-hosted wheel, or copy the default bootstrap that fetches it, to
stuff's required path. Keep its checker independent initially. Reusing the parser later needs a
separate, narrowly vendored offline source/wheel with revision, digest, license and update
procedure, or an independently available pinned artifact, plus an own-registry-unavailable proof.

## Work queue

The campaign is paused at the reconciled Status; this plan does not resume implementation.
On resumption, reconcile parked branches and current default failures before assigning work.
The integrator can prepare BLD-0 and BLD-1 independently of consumer lanes in an isolated
worktree. One writer owns shared files; one worker owns each consumer. Do not restart a
completed repository-wide deslop pass merely to perform a build-tooling slice.

| Slice | Owner and deliverable | Acceptance / next dependency |
| --- | --- | --- |
| BLD-0: inventory | Stuff integrator reviews every active catalog entry and records disposition, exact revision, overlapping paths, affected outputs, bootstrap needs, exclusions and next action in the existing scorecard. | All active entries accounted for; six known consumers reconciled against fresh defaults; examples below refreshed. No catalog retagging or mass dispatch. |
| BLD-1: baseline | Buildlib owner and stuff integrator qualify the actual candidate wheel/bootstrap; reconcile lock semantics and offline recovery; prepare immutable pins and compatibility evidence. | Buildlib's ordinary lint/tests and relevant consumer checks pass; both real Linux bootstrap branches are proven; release availability is explicit. This gates pin upgrades, not independent inventory. |
| BLD-2: pilots | Use **node-build** as one existing consumer and **play's FFmpeg acquisition/packaging** as one non-build-tag consumer. CMake is an extra compatibility check, not a third mandatory migration. | Each pilot satisfies the per-repository proof below and demonstrates useful removed duplication or a concrete correctness gain. Reconcile play's parked work and recorded headful restriction; if the bounded slice cannot avoid held work, defer it and use the ctrs acquisition slice. |
| BLD-3: adopt | Apply the proven pattern to remaining eligible existing consumers, then material custom tooling in other in-scope repositories. Review established shell implementations before deciding conversion is worthwhile. | One bounded PR per consumer slice, existing required checks green, exact pins and capsule receipts, duplicate implementation removed. Excluded or environment-blocked work stays named. |
| BLD-4: enforce | Stuff integrator implements a read-only `buildlib-usage` rule and explicit admission data in a proposed `fleet/policy/buildlib.toml`; retain existing build/release rules. | Focused rule tests plus `make repomod-test` and `make repomod-lint`; negative cases fail. Run on copied policy/selected checkouts first. Only admitted, proven repositories become blocking under the existing lint path. |
| BLD-5: close | Integrator records adoption coverage and exceptions, refreshes permanent docs, closes STUF-101 when its finite scope is qualified. | Counts distinguish shared-helper adoption, bootstrap-only, native exceptions, pending and deferred. No unqualified target becomes green; no active lane is lost when deslop docs retire. |

These IDs describe new work; none is complete merely because this plan was committed.
BLD-4 can be developed against fixtures after the pilots, in parallel with BLD-3. Broader blocking
enforcement waits for the affected repository's migration proof. New shared behavior goes through
buildlib and known-consumer checks before any dependent rollout.

### Concrete cohorts and exceptions

| Cohort | First bounded action and constraint |
| --- | --- |
| Node, CMake, FFmpeg | Audit existing helper calls and bootstrap/pin alignment first. Preserve archive admission, filesystem staging, cache integrity, release layout and cleanup checks already retained by deslop. |
| Python, Chromium, Pi | Known existing consumers; retain any current deslop exclusion. Inventory and candidate compatibility results are useful without assigning migration work. Recheck the top-level campaign Status before dispatch. |
| play | At [67f24f9e33f34e4892bdb100c525d30dc14e2284](https://github.com/joshuarli/play/tree/67f24f9e33f34e4892bdb100c525d30dc14e2284), `scripts/fetch-ffmpeg-runtime.sh` duplicates verified download and pin handling; `scripts/release-linux.sh` packages and checksums. Python already participates. Keep FFmpeg profile/library validation and application layout local; work only outside the parked headful slice. |
| ctrs | At [919fa6769ceb0bae5b8eab7b24cdf62ca3a83cc0](https://github.com/joshuarli/ctrs/tree/919fa6769ceb0bae5b8eab7b24cdf62ca3a83cc0), `guest/kernel/build.sh` and `scripts/ci/kernel-source.sh` download kernel source without a content digest. Give compilation and corresponding-source packaging one verified kernel/patch identity, including version overrides. Preserve source, patches, configs, recipes and notices. A fetch fixture does not prove that the guest kernel builds or boots. |
| bctl | Candidate `kernel/dev/bootstrap.sh` and `toolchain.lock` at [5e56233da2c7780d6d00a75991f2c9acc83aca09](https://github.com/joshuarli/bctl/tree/5e56233da2c7780d6d00a75991f2c9acc83aca09). Keep deferred while excluded; the opportunity is toolchain acquisition, not VM/runtime or benchmark orchestration. |
| git-build, ssh-build, llvm-prebuilt-musl | Review their established shell/jaq implementations. The [previous build campaign](build-repos.md) explicitly accepted that approach. Keep a reasoned native-tooling exception unless a named replacement yields enough maintenance or correctness benefit to justify the Python bootstrap. |
| stuff, usr and OpenOrange paths | Shared ownership requires the integrator. Stuff's own-registry independence is mandatory. OpenOrange's separately owned deployment work and live services keep their existing boundaries; no opportunistic deployment conversion. |
| laputa and unsupported targets | Preserve Laputa's intentional XSH-native package/seed bootstrap and its exclusion. Buildlib currently models only macOS arm64 and Linux musl x86_64/aarch64; do not map Android, iOS, WASM or other targets onto those triples. Partial helper use may be valid; platform-specific behavior remains local. |
| Simple crates, packages and configuration | Native build/test/package commands can be the complete solution. No Python controller or placeholder lock is required to improve an adoption percentage. Reassess when material overlapping custom tooling appears. |

## Bootstrap and development environment

Follow the latest usr `linux-capsule` skill. Vendor both upstream files,
`bootstrap/buildlib-run` and `bootstrap/python.lock`, with source SHA, hashes and documented
local differences. Keep this small shell boundary reviewable. Python and uv archives have size
and SHA-256 checks before extraction; the wheel is SHA-256 pinned. The uv fallback's managed
Python is verified using uv's upstream metadata: record that distinct trust path accurately.

The shim runs Python with the pinned wheel on `PYTHONPATH`. It does **not** provision pytest,
Ruff, ty, the application's dependencies, or every tool needed by a build. Each repository still
owns a small idempotent setup command for verified distribution packages, pinned toolchains and
locked development dependencies. Do not assume uv or pip is installed, or that distro Python
meets the version floor. Keep native-only commands usable without an unnecessary interpreter
download. README links to a development doc listing each system package's consumer, optional
tools, credentials if any, verified hosts and the one-command setup path.

| Environment | Required evidence for an adopted bootstrap |
| --- | --- |
| Fresh `ubuntu:24.04`, native host architecture | Auto-selection actually takes the pinned uv/upstream CPython fallback when compatible musl is unavailable; documented setup and real default gates pass without preinstalled Python/uv/pip. |
| Fresh Debian 13 **or** Ubuntu 26.04 with distro `musl` installed | Auto-selection actually takes python-build with musl >=1.2.5. Record the selected branch and interpreter; a fallback success does not qualify this branch. |
| Repository's CI distribution when different, and any owner-named distribution | Preserve existing Linux promises and trace host-specific default branches; a preconfigured CI image does not replace a newcomer capsule. |
| Supported macOS targets | Preserve native build, lint, test and changed artifact checks. Current bootstrap documents macOS 27+ on Apple Silicon; surface any repository promising an older host before migration. Linux results cannot qualify macOS signing or execution. |

Run the final proof cold from a clean clone of the delivered commit, not the owner's checkout.
Bootstrap from the documented minimal distribution prerequisites. Cache-assisted runs can debug
failures but do not count as the final proof. Leave capsule `TMPDIR` at its distribution default;
the host's `.work/tmp` convention does not override the skill inside the capsule. Run root and an
unprivileged user where ownership or `sudo` assumptions matter. When default gates require
Docker, use the skill's privileged capsule with its own installed engine and `dockerd`; never
substitute the host socket. An unavailable daemon/privilege is a precise environment blocker.

Keep full logs outside the container under scratch, with a separate exit code for setup, build,
lint and test. Redact host paths/environment before committing an evidence summary. Check that
`git status --porcelain` in the tested clone is empty afterward. Record distribution/image
identity, architecture, native versus emulated, cold versus cached, exact commit, interpreter
path, commands, results and cold cost. Emulation proves only the exercised functional behavior;
cold capsule duration is operational cost, not a performance benchmark.

## Per-repository migration proof

1. **Bound the change.** Record the base SHA, actual entrypoint, local implementation replaced,
   buildlib API, supported targets, output/error contracts and consumer policy that remains local.
   Preserve public Make/CLI entrypoints and compiler flags. Source-lock extension fields, budget
   values, allowed dynamic dependencies and product-specific manifest rules remain validated by
   the consumer; buildlib's structural readers do not prove them.
2. **Pin and exercise the installed bytes.** Use the selected immutable wheel and bootstrap,
   exercise the ordinary user path, and check import provenance so a local source tree or owner
   `PYTHONPATH` does not mask an old wheel. Keep package, source and bootstrap lock identities in
   agreement. A dependency declaration alone does not prove integration.
3. **Keep real boundary tests.** Test changed behavior such as wrong digest/size/target,
   incomplete download, cache reuse, failure propagation, archive membership/modes/symlinks and
   consumer manifest agreement. Prove an important new guard with a focused injected fault.
   Shared internals are tested in buildlib once; consumer tests protect their own policy and
   wiring. Preserve existing stronger checks. Broad new mutation matrices are not required.
4. **Compare outcomes.** For changed release code, verify target identity, content/layout,
   manifests, complete checksums, hardening/linkage and applicable runtime smoke on generated
   artifacts without publishing them. Repeated packaging of identical pinned inputs must be
   deterministic where that contract applies. Do not require equality with a previously
   nondeterministic archive; explain any intentional metadata change and preserve compatibility.
   Integrity changes do not authorize silently changing an existing lock or release format.
5. **Prove the environment.** Complete the applicable cold capsules and native supported-platform
   checks above. A unit test of interpreter selection is not a distro qualification. Missing
   evidence blocks the dependent behavior, not unrelated repositories. Never replace real build,
   lint or test gates with an import smoke or skip a correct test to turn the report green.
6. **Show the benefit and cost.** Record duplicate code removed, shared operations actually used,
   a named correctness improvement if any, cold setup bytes/time, warm cached/no-op overhead and
   relevant acquisition/packaging cost. Preserve existing performance gates and use `bench-pyramid`
   only for an affected workload; existing busy-host and bounded mutation rules apply. Remove
   obsolete helpers after checking other consumers. No LOC quota or new benchmark framework.
7. **Land and retain.** Follow the repository's existing slice workflow and merge only on its
   required checks and this slice's acceptance. Record final revision and evidence in its existing
   development/audit docs and the fleet scorecard. Reverting the slice restores the previous
   pins and implementation; it does not rewrite releases or remote state.

## Enforcement after proof

BLD-4 is a proposed rule, not an existing command. Its explicit fleet policy owns applicability,
approved artifact/bootstrap identities, declared entrypoints, exceptions and their reassessment
conditions. Eligibility must survive deletion of an import, lockfile or local campaign record.
Do not infer it only from `build` tags, language tags, LOC or an import grep. Reconcile new active
catalog entries at admission so unclassified repositories cannot silently become exempt.

Keep rollout progress in the existing scorecard; policy records durable requirements, not a
second mutable rollout ledger. Before enrollment, assess in an explicit report/fixture pass.
After enrollment, the existing repomod lint path checks exact pins and their agreement, required
bootstrap/provenance files, declared entrypoints and supported exceptions. It must not execute
consumer scripts, fetch artifacts, start containers or publish as a lint side effect. File
presence cannot prove meaningful reuse: consumer behavior tests and reviewed receipts do that.

Required controls include a missing/unpinned dependency, mismatched wheel digest, missing or
modified undeclared shim, missing declared entrypoint, and invalid/removed exemption. Legitimate
native-only projects must remain clean. Deleting the consumer's actual helper invocation must
fail its protecting behavior check even if an unused import remains. Keep integrity checks for
tampered downloads and caches in buildlib and changed consumer boundaries, not copied into every
repomod lint. A general automatic script-rewrite fixer is out of scope.

## Completion and authority

The integrator reports the active catalog denominator, reviewed dispositions, qualified shared
consumers, bootstrap-only consumers, native exceptions, pending slices and deferred work with
retry conditions. The six historical imports are not six new successful migrations. A blocked
release, capsule, native host or conflicting lane is visible and never counted as a pass.

Use existing deslop grants for later in-scope implementation. This turn authorizes planning and
a direct stuff commit; it does not perform or independently authorize releases, fleet-wide
rewrites, excluded-repository work, registry changes, live deployments, or new CI infrastructure.
Repo-local changes use the existing PR/check workflow; shared policy remains integrator-owned.

STUF-101 and this plan must survive the main deslop document's retirement until every applicable
slice is qualified or has an explicit disposition under the campaign's existing deferral rules.
Move the durable rules to the permanent fleet/build/policy docs before retiring the plan.
Do not recreate a deleted `TODO-DESLOP.md`; use the repository's existing backlog and preserve
its completed pass history.
