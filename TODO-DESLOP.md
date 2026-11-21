Prefix: DSLP
Next: 21

Deslop campaign backlog for the stuff repository ([plan](https://github.com/laputa-systems/stuff/blob/main/docs/campaigns/deslop.md), tier D, worked by component). One agent works this file with the `deslop` skill: take the lowest-numbered open ticket whose area does not start with `Needs owner ·`, one component and one PR per step. Mutation is blocking only for a small scope the repository declares around an important contract (decision 4); broader mutation, coverage and audits are advisory. Close the ticket's remaining steps, then fill in `## Report` below.

## Report

**Scorecard:** Repository-wide before/after source lines, test lines, warm `make test`, line and branch coverage, mutation totals, escape hatches, dead-code lines and dependencies, performance, and escaped regressions were not measured; do not infer zero from an absent measurement. The repomod calibration measured 22,053/25,752 statements and 8,064/10,618 branches at #60, not a current workspace comparison. Its Python escape-hatch matching lines fell 324 to 319; publisher Rust matching lines remained 331. Bounded repomod mutation results include 19 removal and 25 upstream identities caught, 121/127 publication and 55/58 matrix identities caught; the survivors and unrun scopes are dispositioned in [Tests](docs/deslop-repomod-tests.md), not a whole-repository score. Mynpm removed 46 lines and mypypi 84 net; repomod removed unused owners and wrappers, but no campaign-wide line or dependency total was recorded. Five repomod P2 findings were fixed in [#51–#54](https://github.com/laputa-systems/stuff/pull/51) and [#57](https://github.com/laputa-systems/stuff/pull/57); mynpm and mypypi fixed two P2s in [#176](https://github.com/laputa-systems/stuff/pull/176), myoci two in [#177](https://github.com/laputa-systems/stuff/pull/177), and shared OCI routing one in [#179](https://github.com/laputa-systems/stuff/pull/179). No P1 was reported in these component reviews. P3 findings remain in this backlog and `TODO.md`; the component documents also record leads. A campaign-wide filed/fixed count and escaped-regression count were not established. No paired performance verdict was established; the OCI serving paths did not change in #177.

**Per step:** Ground scoped components and recorded commands and contracts in `AGENTS.md`. Repomod Diagnose found five P2s; Types narrowed two consumer boundaries, Tests inventoried five boundary clusters and bounded mutation results, Dead code removed uncalled owners, and Bench added fixture-checked isolated workloads ([diagnosis](docs/deslop-repomod-diagnose.md), [Types](docs/deslop-repomod-types.md), [Tests](docs/deslop-repomod-tests.md), [Dead code](docs/deslop-repomod-dead-code.md), [Bench](docs/deslop-repomod-bench.md), [#172](https://github.com/laputa-systems/stuff/pull/172)). Publisher Diagnose found no reproduced defect; Types adopted no lint, Tests mapped contracts and limitations, and Dead code found nothing removable ([diagnosis](docs/deslop-stuff-publisher-diagnose.md), [Types](docs/deslop-stuff-publisher-types.md), [Tests](docs/deslop-stuff-publisher-tests.md), [Dead code](docs/deslop-stuff-publisher-dead-code.md), [#174](https://github.com/laputa-systems/stuff/pull/174), [#175](https://github.com/laputa-systems/stuff/pull/175)). [Mynpm](docs/deslop-mynpm.md) and [mypypi](docs/deslop-mypypi.md) fixed archive limits and added controls; [myoci](docs/deslop-myoci.md) fixed chunk framing and temporary-file cleanup; [Worker](docs/deslop-stuff-worker.md) inventoried runtime boundaries; [shared crates](docs/deslop-shared-crates.md) fixed OCI upload routing. The deploy component is owner-deferred. Per-step wall time and CI minutes were not consistently recorded; no aggregate cost is claimed.

**Method feedback:** A repeated-entry archive limit test caught the mynpm defect, and a RECORD verification fault exposed a missing mypypi unit guard even though a publisher integration test already failed it. Broad clippy candidates lacked defect witnesses; Vulture reported dynamic uses that required caller checks. Publisher Diagnose and Dead code found no demonstrated defect or removable code. Coverage and mutation were unavailable for the later Rust components; their absence is not a pass.

**Shared-file gaps:** The hosted repomod publication mutation lane was never qualified; [STUF-96](TODO.md) retains that work. [STUF-95](TODO.md) retains dashboard benchmark attribution and comparison gaps. A bounded mutation scope and hosted negative controls must be qualified before a required lane is retained; #173 made fleet eligibility independent of this backlog. The deploy pass needs an owner decision because OpenOrange work shares its tree.

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

