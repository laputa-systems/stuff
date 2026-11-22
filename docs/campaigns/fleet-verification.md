# Fleet verification rollout

## Status

The rollout covers all 72 managed repositories in `fleet/catalog.toml` at `407249c6c`, including private repositories. The catalog excludes `zzz`. This record distinguishes completed changes from full repository conformance.

| Repository | Accepted evidence | Remaining proof |
| --- | --- | --- |
| `joshuarli/loc` | `f54cf9e2` scopes `make clean`. The disposable cleanup probe, 551 Change tests, benchmark parser tests, `ty` on the driver, and `make bench TIER=change WORKLOAD=count_generated_corpus` passed. [Hosted CI passed](https://github.com/joshuarli/loc/actions/runs/45063328421). | Paired workload comparisons and attribution under LOCC-2. |
| `joshuarli/nanoshop` | `d219153` preserves the hosted gate's suite selection through `make test-ci`. `make test` passed 1,258 tests, `pnpm run typecheck` passed, and `make bench WORKLOAD=browse/storied` completed five runs. Benchmark preflight, dry run, and unavailable-workload checks passed. `0784088` passed the cleanup probe for `./release`, preserving local tenant data and dependency installs. | GitHub blocked hosted jobs before any test step with a billing or spending-limit error. NANO-48 tracks the OpenOrange benchmark path. [Hosted run](https://github.com/joshuarli/nanoshop/actions/runs/45063420766). |
| `joshuarli/img` | `1e7aca7` passed the cleanup probe, `make-clean-target`, and `make bench TIER=edit`. | Audit current Change workload and type evidence. |
| `joshuarli/lz` | `338c9dd` passed cleanup. `485743e` rejects name-only and malformed benchmark results. `make test`, `ty check benches/driver.py`, the driver self-tests, and `make bench TIER=change WORKLOAD=search_hit_literal` passed. | DSLP-12 and DSLP-13 track representative journeys and paired comparisons. |
| `laputa-systems/fz` | `77c5c53` passed cleanup and `make test`. | Verify current selected benchmarks and audit typing evidence. |
| `laputa-systems/e` | `695942e` passed cleanup. `7fa70d5` fixed two wrap-sensitive PTY lock tests and passed `make test`, including 165 PTY tests. `7c0522c` passed `ty` on the benchmark driver, its five self-tests, and `make bench BENCH_ARGS='--tier Change --name render_full_frame_plain'`. A fixture proved a successful subprocess with name-only output fails the gate. | Audit paired comparisons and current Rust type boundaries. |
| `joshuarli/defuddle-rs` | `79628f266` passed scoped Rust cleanup. | Verify test, benchmark, and type gates. |
| `joshuarli/shck` | `57ccab859c` passed scoped Rust cleanup. | Verify test, benchmark, and type gates. |
| `joshuarli/play` | `95da2e9f6` passed scoped Rust cleanup. | Verify test, benchmark, and type gates. |
| `joshuarli/stonks` | `a31033e` passed cleanup for Rust and Vite outputs, including refusal of a symlinked `web` parent. `42dfa6a` passed `make test` with 670 Rust tests and four web model tests. Eight provider or child tests were ignored as documented. The strengthened SMA test detected a planted null-for-zero result. The earnings fixture now uses its recorded date. | Qualify the benchmark entrypoint and verify the web type checker. |
| `joshuarli/toolbox` | `c0010ff` passed cleanup for the test and lint caches while preserving the dependency environment and local data. | Verify test, benchmark, and type gates. |
| `laputa-systems/laputa-ui-dashboard` | `af5b046` passed scoped cleanup while preserving installed packages. | Verify test, benchmark, and type gates. |
| `laputa-systems/fastermod` | `8fce05b5` passed cleanup and required PR checks. [PR 45](https://github.com/laputa-systems/fastermod/pull/45). | Verify benchmark and audit coverage. |
| `joshuarli/ish` | `e38c83d0` passed cleanup and all required PR jobs. [PR 49](https://github.com/joshuarli/ish/pull/49). | Verify benchmark entrypoints and audit coverage. |
| `joshuarli/ctrs` | `0480e4e` passed scoped cleanup for the Cargo target. | Verify other gates with the repo's runner and host requirements. |
| `joshuarli/agentctl` | `78b0804` passed cleanup for the web bundle and its new `make test`, which reuses the prior package test commands. Workspace type checking passed with `pnpm -r --if-present run typecheck`. | Verify benchmark and hosted workflow coverage. |
| `joshuarli/obscura` | `c1e823c` passed scoped cleanup and the new `make test`, with 86 renderer tests. | Verify the Android, benchmark and typing boundaries separately. |
| `laputa-systems/srv` | `c0cbbff` passed cleanup, 92 local tests, and the required hosted CI, lint, and mutation checks. The code now uses one ordering comparison, making a stale exemption for an equivalent mutant unnecessary. [PR 51](https://github.com/laputa-systems/srv/pull/51). | SRV-5 tracks representative serving benchmarks. |
| `joshuarli/pytest-parallel` | `f3794e6` passed the cleanup probe and the required Linux, macOS, and lint checks. [PR 46](https://github.com/joshuarli/pytest-parallel/pull/46). | Verify current benchmark and type gates. |
| `laputa-systems/tm` | Cleanup passed locally. The first macOS job caught a status test reading a stale frame after selecting a window. `2296d00` waits for the named window to appear and all four status tests passed locally with socket and configuration isolation. [PR 48](https://github.com/laputa-systems/tm/pull/48). | Required checks on the new PR head. |

At rollout start, the focused repomod check flagged 46 repositories for missing `make clean` and 17 for PR test workflow conformance. It reported no retained strict-profile violations. The strict-profile result covers only repositories registered for those rules, so it is insufficient as a type audit.

## Qualify a repository

1. Inspect its current checkout, repository guidance, and [existing deslop evidence](deslop-scorecard.md). Reuse evidence when the relevant sources, configuration, fixtures, and runners still match. Record the exact revision.
2. Use the repository's native tools. Keep `make test` bounded to Change and keep Full manual. Prove that the gates exercise real required work and surface an empty selection, required skip, or timeout as incomplete. Keep coverage when a stronger test has yet to catch the same defect.
3. Verify representative benchmark selection, preflight, and completed work on one named Change workload. Record unavailable host or service requirements. Keep timing comparisons separate from workload completion and qualify them under the existing performance rules.
4. Run the configured type checker on audited boundaries. Record an actual bad program the checker rejects or an unchecked assertion the change removes. Retain the existing typing profile.
5. Verify cleanup in a disposable checkout. Create an owned output, a nested fixture with the same basename, a `.work` sentinel, and an external target set through the build environment. Run `make clean` twice. The owned output disappears and all sentinels survive. Repeat with the output path replaced by a symlink to the external target and verify the recipe refuses it.
6. Follow the default branch's rules before pushing. Record local and hosted checks independently. Continue local work when GitHub or a named runner blocks hosted evidence.

Start with small Rust tools and then apply the same evidence to other toolchains and services. Use the repo's existing tiered setup wherever it meets the [fleet quality standard](../fleet.md#quality-standard). Repomod's initial check is reproducible with `uv run repomod lint --include-private --rule make-clean-target --rule gha-test-workflow --rule strict-typing-profile`.
