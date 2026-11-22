# Fleet verification rollout

## Status

The rollout covers all 72 managed repositories in `fleet/catalog.toml` at `407249c6c`, including private repositories. The catalog excludes `zzz`. This record distinguishes completed changes from full repository conformance.

| Repository | Accepted evidence | Remaining proof |
| --- | --- | --- |
| `joshuarli/loc` | `f54cf9e2` scopes `make clean`. The disposable cleanup probe, 551 Change tests, benchmark parser tests, `ty` on the driver, and `make bench TIER=change WORKLOAD=count_generated_corpus` passed. [Hosted CI passed](https://github.com/joshuarli/loc/actions/runs/45063328421). | Paired workload comparisons and attribution under LOCC-2. |
| `joshuarli/nanoshop` | `d219153` preserves the hosted gate's suite selection through `make test-ci`. `make test` passed 1,258 tests, `pnpm run typecheck` passed, and `make bench WORKLOAD=browse/storied` completed five runs. Benchmark preflight, dry run, and unavailable-workload checks passed. `0784088` passed the cleanup probe for `./release`, preserving local tenant data and dependency installs. | GitHub blocked hosted jobs before any test step with a billing or spending-limit error. NANO-48 tracks the OpenOrange benchmark path. [Hosted run](https://github.com/joshuarli/nanoshop/actions/runs/45063420766). |
| `joshuarli/img` | `1e7aca7` passed the cleanup probe, `make-clean-target`, and `make bench TIER=edit`. | Audit current Change workload and type evidence. |
| `joshuarli/lz` | `338c9dd` passed cleanup. `485743e` rejects name-only and malformed benchmark results. `make test`, `ty check benches/driver.py`, the driver self-tests, and `make bench TIER=change WORKLOAD=search_hit_literal` passed. | DSLP-12 and DSLP-13 track representative journeys and paired comparisons. |
| `laputa-systems/fz` | `77c5c53` passed cleanup and `make test`. `4006032` rejects a missing measurement for the exact Rust benchmark name. Seven driver tests, `ty` on the driver and a run of `make bench BENCH_ARGS='--tier change --name rust-search'` passed. | Qualify the fzy comparison on a host with the pinned oracle and review Rust type boundaries. |
| `laputa-systems/e` | `695942e` passed cleanup. `7fa70d5` fixed two wrap-sensitive PTY lock tests and passed `make test`, including 165 PTY tests. `7c0522c` passed `ty` on the benchmark driver, its five self-tests, and `make bench BENCH_ARGS='--tier Change --name render_full_frame_plain'`. A fixture proved a successful subprocess with name-only output fails the gate. | Audit paired comparisons and current Rust type boundaries. |
| `joshuarli/defuddle-rs` | `79628f266` passed scoped Rust cleanup. `a163fc7b9` passed the native Change suite, four driver tests, `ty` on the driver, and the HTML and Markdown corpus benchmark. Profiling mode previously exited successfully without timing either workload and now fails the gate. | Paired comparisons and WASM browser qualification remain open. |
| `joshuarli/shck` | `57ccab859c` passed scoped Rust cleanup. | Verify test, benchmark, and type gates. |
| `joshuarli/play` | `95da2e9f6` passed scoped Rust cleanup. | Verify test, benchmark, and type gates. |
| `joshuarli/stonks` | `a31033e` passed cleanup for Rust and Vite outputs, including refusal of a symlinked `web` parent. `42dfa6a` passed `make test` with 670 Rust tests and four web model tests. Eight provider or child tests were ignored as documented. The strengthened SMA test detected a planted null-for-zero result. The earnings fixture now uses its recorded date. | `50e44c0` passed the common replay Change workload. The gate rejected an unknown workload, the manual sustained profile and an empty report. The web type checker passed under Node 26.13.1. Paired comparisons and full replay qualification remain open. |
| `joshuarli/toolbox` | `c0010ff` passed cleanup for the test and lint caches while preserving the dependency environment and local data. | Verify test, benchmark, and type gates. |
| `laputa-systems/laputa-ui-dashboard` | `af5b046` passed scoped cleanup while preserving installed packages. | Verify test, benchmark, and type gates. |
| `laputa-systems/fastermod` | `8fce05b5` passed cleanup and required PR checks. [PR 45](https://github.com/laputa-systems/fastermod/pull/45). | Verify benchmark and audit coverage. |
| `joshuarli/ish` | `e38c83d0` passed cleanup and all required PR jobs. [PR 49](https://github.com/joshuarli/ish/pull/49). | Verify benchmark entrypoints and audit coverage. |
| `joshuarli/ctrs` | `0480e4e` passed scoped cleanup for the Cargo target. | Verify other gates with the repo's runner and host requirements. |
| `joshuarli/agentctl` | `78b0804` passed cleanup for the web bundle and its new `make test`, which reuses the prior package test commands. Workspace type checking passed with `pnpm -r --if-present run typecheck`. | `99934b5` validates the native owner status response. The test first reproduced acceptance of a malformed response and then passed with the fix. |
| `joshuarli/obscura` | `c1e823c` passed scoped cleanup and 86 renderer tests. The Edit benchmark harness and the named `develop-synthetic` Change workload completed. | Qualify Android and current type boundaries separately. |
| `laputa-systems/srv` | `c0cbbff` passed cleanup, 92 local tests, and the required hosted CI, lint, and mutation checks. The code now uses one ordering comparison, making a stale exemption for an equivalent mutant unnecessary. [PR 51](https://github.com/laputa-systems/srv/pull/51). | SRV-5 tracks representative serving benchmarks. |
| `joshuarli/pytest-parallel` | `f3794e6` passed the cleanup probe and the required Linux, macOS, and lint checks. [PR 46](https://github.com/joshuarli/pytest-parallel/pull/46). | Verify current benchmark and type gates. |
| `laputa-systems/tm` | `9904111` scopes cleanup and makes status and suspend tests wait for the window and kernel stop events. Focused PTY tests with the pinned tmux reference and required Linux, macOS and lint checks passed. [PR 48](https://github.com/laputa-systems/tm/pull/48). | Qualify benchmark entrypoints and the remaining typing audit. |
| `joshuarli/stats` | `79ef16a41c3` passed cleanup for the agent and release outputs, including refusal of an aliased parent. | Verify the Change, benchmark and type gates independently of deployment. |
| `joshuarli/tansu` | `afb2f9aa` passed cleanup for the Cargo and frontend outputs. | Verify the current Change and browser benchmark gates. |
| `joshuarli/bctl` | `f602a256` passed cleanup for the Rust and dashboard outputs, 89 local host tests with 39 VM-only cases ignored, and 27 benchmark suite tests. `1a97f7ec` fixed the preflight interpreter selection. The full Edit harness completed 177 tests with four skips and one fixture-thread warning. Dashboard typecheck passed. | VM and kernel workloads require separate runner evidence. |
| `joshuarli/shadowdriver` | `037578c` passed scoped Rust cleanup. | Verify current SDK test and type evidence. |
| `laputa-systems/doas-rs`, `mdevd-rs` | `44a0de6` and `2752e33` passed scoped cleanup. | Runtime-specific proof uses the documented Linux runners. |
| `laputa-systems/hi-lite`, `rustybench` | `71530bc` and `ef955ceb` passed scoped cleanup and required checks. [Hi-lite PR 33](https://github.com/laputa-systems/hi-lite/pull/33), [Rustybench PR 30](https://github.com/laputa-systems/rustybench/pull/30). | Verify current benchmark and audit evidence. |
| `laputa-systems/oxish`, `rage`, `rg`, `smolith`, `xsh` | `0bd0c26`, `8439c3f`, `4a41eba`, `589ff14` and `e59dae73a` passed scoped cleanup. | Audit each repo’s existing test, benchmark and type boundaries. |
| `laputa-systems/deser`, `tinyland` | `b13180c` and `1137aed` passed scoped cleanup. | Verify the supported benchmark tier and native or container-based test paths. |
| `laputa-systems/diff-pretty`, `fd`, `jaq`, `ptytest`, `rawzip`, `vault` | Scoped cleanup and required hosted checks passed and merged. Rawzip also verified both timestamp paths with a local archive. [Diff-pretty PR 52](https://github.com/laputa-systems/diff-pretty/pull/52), [Fd PR 25](https://github.com/laputa-systems/fd/pull/25), [Jaq PR 17](https://github.com/laputa-systems/jaq/pull/17), [Ptytest PR 34](https://github.com/laputa-systems/ptytest/pull/34), [Rawzip PR 8](https://github.com/laputa-systems/rawzip/pull/8), [Vault PR 45](https://github.com/laputa-systems/vault/pull/45). | Verify current benchmark and audit evidence. |

At rollout start, the focused repomod check flagged 46 repositories for missing `make clean` and 17 for PR test workflow conformance. The first checkpoints reported no retained strict-profile violations. The strict-profile result covers only repositories registered for those rules, so it is insufficient as a type audit.


### Local command changes

| Repositories | Verification and remaining evidence |
| --- | --- |
| Discover, Extensions and usr | `9a187429`, `66c69b1` and `6373284e` passed scoped cleanup probes in isolated worktrees. |
| Aincrad2 and Niceforge | `5aed2be2` and `ac07e6f` preserve simulation results, installed dependencies and local state. Cleanup probes passed. |
| Python Build, LLVM Prebuilt Musl and SSH Build | `689519644` passed 360 controller tests and cleanup probes that preserved research data. `d6267bc` reaches the LLVM artifact tests, which rejected two stale Clang footer outputs. The patch applied once and reversed correctly against pinned source. `b5046ca` passed server and key-generation tests with the installed wrapper disabled for that invocation. |
| Lexopt, Rustls, WebPKI and zlib-rs | `b856de2`, `c11b6b59`, `17d1eb6` and `9327926` passed their new local test targets and cleanup probes. |
| Syncthing, Mactop and Soulseek | `9aca13072` passed the short Go suite for 48 packages. Mactop passed 42 Swift tests and Soulseek passed its bounded native suite. Both PRs passed hosted checks. [Mactop PR 12](https://github.com/joshuarli/mactop/pull/12), [Soulseek PR 12](https://github.com/joshuarli/soulseek-rs/pull/12). |
| Kache | The cleanup probe and pre-PR Linux arm64 container check passed 5,048 tests with 48 ignored. Use the repository Dockerfile and container-local `TMPDIR` and `KACHE_TEST_SCRATCH_DIR`; host bind-mounts do not reproduce the filesystem semantics. The hosted x86 musl check failed in the compiler-family probe. `5d2e8d807` switched its fixture to the existing executable writer that prevents a fork from inheriting the writable descriptor. The targeted probe passed in the Linux arm64 container. Fresh hosted checks are pending. DSLP-125 records the installed wrapper's separate integration-test compile failure. [PR 140](https://github.com/joshuarli/kache/pull/140). |

## Fork CI

The rollout covers 18 managed forks. Inspect the workflow diff from the upstream
merge base. Keep fork-owned release and platform workflows, and preserve
required check names. The regular gates run `make test` or `make test-ci` and
`make lint`. Repomod checks action pins and workflow syntax on those CI files
and reports workflow names outside the fleet set.

- Green and merged on the first two waves: [Lexopt 5](https://github.com/laputa-systems/lexopt/pull/5),
  [zlib-rs 5](https://github.com/laputa-systems/zlib-rs/pull/5),
  [Rawzip 9](https://github.com/laputa-systems/rawzip/pull/9),
  [Rustix 5](https://github.com/laputa-systems/rustix/pull/5),
  [gh 17](https://github.com/joshuarli/gh/pull/17),
  [rust-fontconfig 4](https://github.com/laputa-systems/rust-fontconfig/pull/4),
  [Oxish 5](https://github.com/laputa-systems/oxish/pull/5),
  and [Syncthing 10](https://github.com/joshuarli/syncthing/pull/10).
- Rustls and WebPKI merged from locally verified test and lint runs on unprotected
  branches. GitHub returned no runs for the PRs after reopening or for the merge
  commits at this checkpoint. [Rustls 4](https://github.com/laputa-systems/rustls/pull/4),
  [WebPKI 3](https://github.com/laputa-systems/webpki/pull/3).
- Deser and Crabtables both passed hosted test and lint and merged at
  `22bc8963c` and `4624c7325`. Deser also passed `no_std`, MSRV and Miri.
  [Deser 9](https://github.com/laputa-systems/deser/pull/9),
  [Crabtables 4](https://github.com/laputa-systems/crabtables/pull/4).
- Asterinas, fd, jaq, rage, ripgrep and Soulseek already had fork-owned CI.

Across all 18 defaults, no retained workflow file matches the version at its local upstream merge base. The following check also returned no findings. `workflow-redundancy` and `gha-triggers` also passed. `gha-settings` flagged the release workflows in jaq and ripgrep. These releases retain their own settings and receive separate review.

```sh
uv run repomod lint --include-private --tag fork --rule fork-workflow-names \
  --rule gha-test-workflow --rule gha-lint-workflow --rule gha-syntax
```

## Default-branch entrypoints

All 72 catalogued default branches define a root `make test` target. Kache is
currently the only default branch missing `make clean`. Its [open cleanup PR](https://github.com/joshuarli/kache/pull/140)
contains the verified recipe. Thirty-eight defaults have a root `bench` target. The other repositories may provide named workloads under different commands. Discover's `9a187429` is on its default branch and
passes the entrypoint rule. The source scan checks target declarations. Each
repository still needs evidence that its targets run the intended work.

Scoped cleanup probes passed for Rustix `d8c2624`, Crabtables `07006ef`, Stuff
`a6b44acc6`, Gluon `5616e9118`, Pi Build `7cbb75f88`, and rust-fontconfig
`f17da1f`. The same cleanup controls passed for Asterinas `e310190ae`, Buildlib
`76e00f8`, Chromium Build `76a3b07dc`, CMake Build `ac7f087dbc`, FFmpeg Build
`673d0d9f`, Node Build `ee79e76b5`, SSH Build `f915b51`, Git Build `7e12a61`,
and LLVM Prebuilt Musl `d667755`. LLVM rejects redirected work or release paths
and preserves other architectures and package versions. Asterinas preserves the
installed cargo-osdk even if the Make variable points outside the checkout. Mactop `a38941b` passed its local cleanup probes, 42 Swift tests, and both hosted checks. [Mactop 13](https://github.com/joshuarli/mactop/pull/13).

Rustix's default benchmark ran its `getpid` Change workload. The full Criterion
suite uses Rustix's `bench-full` Make target. The Change workload is a syscall
microbenchmark. Representative downstream benchmarks still need qualification.
Agentctl `0a54fe3` ran the real SQLite inbox workload through ingestion, replay,
and rebuild. It rejected an unknown workload and a planted empty rebuild.
The inbox test suite and benchmark script syntax checks passed. The full
control-plane fixture and browser workload remains manual.

The focused fleet policy check reported 16 first-party PR test workflow gaps on default branches. Chromium Build passed when checked at its default branch instead of the active feature checkout.
The existing lanes need individual inspection for job scope and required check
names before translation to `make test` or `make test-ci`.

- Applications and tools: Agentctl, Aincrad2, bctl, Discover, Mactop,
  Niceforge, Obscura, Shadowdriver, Stonks, usr, Laputa, and xsh.
- Build repositories: Git Build, LLVM Prebuilt Musl, Python Build, and SSH Build.

## Qualify a repository

1. Inspect its current checkout, repository guidance, and [existing deslop evidence](deslop-scorecard.md). Reuse evidence when the relevant sources, configuration, fixtures, and runners still match. Record the exact revision.
2. Use the repository's native tools. Keep `make test` bounded to Change and keep Full manual. Prove that the gates exercise real required work and surface an empty selection, required skip, or timeout as incomplete. Keep coverage when a stronger test has yet to catch the same defect.
3. Verify representative benchmark selection, preflight, and completed work on one named Change workload. Record unavailable host or service requirements. Keep timing comparisons separate from workload completion and qualify them under the existing performance rules.
4. Run the configured type checker on audited boundaries. Record an actual bad program the checker rejects or an unchecked assertion the change removes. Retain the existing typing profile.
5. Verify cleanup in a disposable checkout. Create an owned output, a nested fixture with the same basename, a `.work` sentinel, and an external target set through the build environment. Run `make clean` twice. The owned output disappears and all sentinels survive. Repeat with the output path replaced by a symlink to the external target and verify the recipe refuses it.
6. Follow the default branch's rules before pushing. Record local and hosted checks independently. Continue local work when GitHub or a named runner blocks hosted evidence.

Start with small Rust tools and then apply the same evidence to other toolchains and services. Use the repo's existing tiered setup wherever it meets the [fleet quality standard](../fleet.md#quality-standard). Repomod's initial check is reproducible with `uv run repomod lint --include-private --rule make-clean-target --rule gha-test-workflow --rule strict-typing-profile`.
