Prefix: DSLP
Next: 21

Deslop campaign backlog for the stuff repository ([plan](https://github.com/laputa-systems/stuff/blob/main/docs/campaigns/deslop.md), tier D, worked by component). One agent works this file with the `deslop` skill: take the lowest-numbered open ticket whose area does not start with `Needs owner ·`, one component and one PR per step. Mutation is blocking only for a small scope the repository declares around an important contract (decision 4); broader mutation, coverage and audits are advisory. Close the ticket's remaining steps, then fill in `## Report` below.

## Report

The `repomod/` calibration component is complete: Ground, Diagnose, Types, Tests and Dead code are closed, and its P2 findings are fixed. Evidence is in [the component review](docs/deslop-repomod-diagnose.md), [Types](docs/deslop-repomod-types.md), [Tests](docs/deslop-repomod-tests.md), [Dead code](docs/deslop-repomod-dead-code.md) and [Bench](docs/deslop-repomod-bench.md). The P2 repairs merged in [#51](https://github.com/laputa-systems/stuff/pull/51) to [#54](https://github.com/laputa-systems/stuff/pull/54) and [#57](https://github.com/laputa-systems/stuff/pull/57); Dead code closed in [#98](https://github.com/laputa-systems/stuff/pull/98) and Tests on the finite inventory in [#172](https://github.com/laputa-systems/stuff/pull/172), which also deleted this file. The open repomod P3 findings live in `TODO.md` (STUF-93, STUF-94, STUF-95, STUF-96).

The `crates/stuff` publisher component is complete: Diagnose, Types, Tests, and Dead code are recorded in [the diagnosis](docs/deslop-stuff-publisher-diagnose.md), [Types](docs/deslop-stuff-publisher-types.md), [Tests](docs/deslop-stuff-publisher-tests.md), and [Dead code](docs/deslop-stuff-publisher-dead-code.md). The test inventory records the remaining proof limits.

The other components below remain. Ground covers the whole repository (`AGENTS.md`, Verification: costs, contracts, vendored trees). Each remaining ticket starts with a bounded Diagnose of its component.

## Tickets

### DSLP-16 · P3 · Deslop deploy/: OpenOrange host tooling and maintenance scripts

- **Area:** Needs owner · deploy
- **Where:** deploy/ (141 files), including deploy/openorange/ and its rivet TypeScript
- **Problem:** Deferred: deploy/openorange/ (host runtime, ingress, storage, recovery) is owned by a separate active OpenOrange campaign with dirty worktrees (docs/openorange-runtime.md, docs/campaigns/deslop-roadmap.md). The generic maintenance scripts (R2 pull, put and gc, store copy, fake S3, smoke checks) share that tree. Deslop edits here would collide with that work.
- **Recommendation:** The owner decides whether the OpenOrange campaign has finished or whether deslop takes the non-OpenOrange scripts separately. Until then do not schedule this component. If scheduled: Diagnose first (none exists), then Types, Tests and Dead code; accept with `make test-r2`, `make test-publish-lock`, `make test-store-copy`, `make pipecheck`, `make worker-deploy-test`; live checks (`make test-r2-live`, `make smoke-deployed`, deployments) stay opt-in.
- **Fix with:** deslop
- **Effort:** L

### DSLP-18 · P3 · Upstream responses are buffered up to 1 GiB plus 64 MiB regardless of the caller's byte limit

- **Area:** mynpm · acquire
- **Where:** crates/mynpm/src/acquire.rs HttpsExchange::fetch and transfer
- **Problem:** Unreproduced; read from the code on 52c3999d. HttpsExchange::fetch reads the whole body into memory and stops only at TARBALL_BYTES + 64 MiB. The caller's max_bytes (64 MiB for packuments and metadata) is checked in transfer only after the full body is buffered, and a valid Content-Length is never compared with any limit. A hostile or faulty upstream metadata response can therefore hold about 1.06 GiB in memory per request, and four downloads run concurrently. A reproduction needs a local TLS origin for HttpsExchange; the offline fakes replace the Exchange trait and cannot show it.
- **Recommendation:** Pass max_bytes into Exchange::fetch, reject a Content-Length above it before reading, and stop the read loop at the caller's limit. Add a test with a fake Exchange that records the limit it receives, and a local TLS origin check if one is available.
- **Fix with:** deslop
- **Effort:** S

### DSLP-20 · P3 · Wheel member lookups scan every member, so validation is quadratic in the member count

- **Area:** mypypi · wheel archive
- **Where:** crates/mypypi/src/wheel_zip.rs Archive::member; callers in crates/mypypi/src/validate.rs and acquire.rs
- **Problem:** Confirmed on 52c3999d in a debug build with generated wheels of empty files. inspect_wheel took 0.31 s for 5,000 members, 0.74 s for 10,000 and 1.74 s for 20,000; each name triggers mode, read, size and read_prefix calls that each scan the member list linearly. A 100 MB wheel can hold on the order of 800,000 central directory entries. Not extrapolated beyond 20,000 members.
- **Recommendation:** Index members by name when opening the archive (first entry wins, as today). Duplicate names are rejected by the callers, so the index changes no result.
- **Fix with:** deslop
- **Effort:** S

