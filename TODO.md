Prefix: STUF
Next: 85

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

### STUF-82 · P2 · Worker gateway test intermittently sees an already-read body

- **Area:** Worker runtime
- **Where:** crates/stuff-worker/test/runtime.test.mjs:193 (the gateway forwards the host to the cached entrypoint)
- **Problem:** In stuff#9 CI run 43691840562 the worker-runtime job failed with TypeError Body is unusable: Body has already been read on the first cargo.text() call at runtime.test.mjs:202, after the same job passed on the PR's previous run with no Worker change between them. Something consumes the gateway response body before the test reads it; a shared or cached Response handed to two requests would do it. Unreproduced locally.
- **Recommendation:** Root-cause with repeated runs of that test (node --test with a loop) and read the gateway path that serves catalog.json for both hosts; fix the producer, not the test, and keep the test as the regression.
- **Fix with:** root-cause
- **Effort:** M


### STUF-83 · P2 · Mirror the deslop mutation and dead-code tools for Python and TypeScript

- **Area:** Registries
- **Where:** stuff publish pypi, stuff publish npm --lockfile (crates/mynpm/src/inventory.rs:850)
- **Problem:** The deslop campaign mirrored vulture 2.16 and deptry 0.25.1, but mutmut 3.8.1 fails planning because libcst 1.9.0 has no macos-x86_64 wheel (setproctitle and pyyaml are native too), and a lockfile of @stryker-mutator/core 10.1.1, @stryker-mutator/vitest-runner 10.1.1, knip 6.45.1, and @vitest/coverage-v8 5.1.0 resolved from npmjs fails with integrity: verified artifact.artifact.sourceUrl must be a public npm HTTPS URL, without naming the package (lockfile kept at .work/tmp/npm-tools in the campaign clone). Until both are mirrored, Python and TypeScript repositories run mutation and knip from scratch installs and have no CI mutation lane.
- **Recommendation:** Make the npm error name the offending package and fix or exempt its source URL; for mutmut either build the missing wheels with --allow-sdist on a matching host or choose a pure-Python mutation tool. Then pin the tools in the deslop skill tools reference and add the Python and TypeScript lanes.
- **Fix with:** root-cause
- **Effort:** M


### STUF-84 · P2 · Retain deslop gains with fleet rules for coverage, the mutation lane, and strict profiles

- **Area:** Fleet policy
- **Where:** repomod/rules/ (new), fleet/policy/rust-tools.toml (new), docs/policy-development.md; reference implementation laputa-systems/srv Makefile coverage and mutants-diff targets, .github/workflows/ci.yml mutants job, .cargo/mutants.toml
- **Problem:** The deslop campaign proved the Rust recipe in srv (branch coverage, cargo-mutants 27.1.0 diff lane through taiki-e/install-action, exit 3 counted as detected, a whole-crate run for test-only diffs) and adopted strict settings per repository on evidence (Rust unsafe_code forbid; ty missing-type-argument and unsound-return-statement; Ruff ANN401). Nothing in repomod requires them, so a repository can drop its lane or profile, and every Rust repository copies the same Makefile block by hand.
- **Recommendation:** Add rules that apply only to repositories whose TODO-DESLOP.md Tests step is closed (or that already have the targets): make-coverage-target, mutants-diff-lane (job present, pinned tool, base ref through env), and strict-typing-profile for the settings adopted fleet-wide; give mutants-diff-lane a fixer that writes srv's Makefile block and job. Python and TypeScript lanes follow STUF-83.
- **Fix with:** none
- **Effort:** M

