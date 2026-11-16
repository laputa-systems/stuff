# STUF-89: complete owned-tool help

Status: in progress. Eleven repositories have landed verified source changes.
The remaining repositories are being implemented and reviewed in parallel batches.
STUF-89 remains open until coverage has no ordinary gaps.

## Contract

Original tools get a complete top-level reference from their existing parser
declarations, an `Examples:` section covering every command, and the owned-tool
footer. A bare invocation prints help when a command is required. Existing bare
invocations that perform work retain their behavior. Forks and build distributions
get the footer through their maintained source or patch path.

Keep parsers, valid invocations, defaults, output formats and version protocols.
Do not migrate parsers, release tools, install binaries, or resume performance
campaigns. One worker owns each repository. The stuff integrator owns policy and
the backlog. Update a policy entry only after its source change lands with tests.

## Landed source

| Repository | Landed change | Verification |
| --- | --- | --- |
| joshuarli/loc | `2b5d096`, `869409d` | 532 tests, clippy, built help and example parsing |
| laputa-systems/fastermod | `fda1e8f` | 42 tests, clippy, build, all mode examples |
| joshuarli/defuddle-rs | [PR 14](https://github.com/joshuarli/defuddle-rs/pull/14) | Workspace tests and clippy; examples execute offline |
| laputa-systems/diff-pretty | [PR 30](https://github.com/laputa-systems/diff-pretty/pull/30) | Workspace checks and Linux/macOS CI |
| laputa-systems/fd | [PR 23](https://github.com/laputa-systems/fd/pull/23) | Built help and output regression; full CI |
| laputa-systems/rg | [PR 15](https://github.com/laputa-systems/rg/pull/15) | Built help, search, JSON, completion, man and version checks; full CI |
| laputa-systems/vault | [PR 33](https://github.com/laputa-systems/vault/pull/33) | 58 macOS tests, clippy, Linux CI; two hardware tests ignored |
| laputa-systems/e | [PR 28](https://github.com/laputa-systems/e/pull/28) | CLI/parser tests, clippy and Linux/macOS CI |
| laputa-systems/doas-rs | [PR 3](https://github.com/laputa-systems/doas-rs/pull/3) | 166 Linux container tests, clippy and CI |
| joshuarli/ish | [PR 31](https://github.com/joshuarli/ish/pull/31) | ish/epsh built help, examples, shell regressions and Linux/macOS CI |
| joshuarli/mactop | [PR 11](https://github.com/joshuarli/mactop/pull/11) | Built Swift help test, lint and CI |

Stuff's complete reference and parser-checked command examples are committed
locally. Its CLI and library tests pass, with clippy warnings denied. Repomod's
full suite passed: 1,410 tests, three expected skips.

## Remaining work

Source review or PR checks: bctl, ctrs, lz, stats, Rust stuff.

Implementation or correction: kache, xsh, play, soulseek-rs, tansu, toolbox,
pi-build, img.

Queued originals: fz, srv, gluon, mdevd-rs, tinyland, zzz.
Existing footer coverage does not establish the
complete-reference contract for these tools.

Queued forks and distributions: gh, syncthing, chromium-build, cmake-build,
ffmpeg-build, git-build, node-build, llvm-prebuilt-musl, jaq, rage, ssh-build.
Python-build already has its maintained help patch and test; verify that existing
source coverage when closing the batch.

Keep the recorded checkout-less gaps for ghostty, mold, shck, swift-bylaws and
view. Keep tm parked on [issue 28](https://github.com/laputa-systems/tm/issues/28).
Preserve all existing justified command exemptions.

## Verification limits and repairs

Local rg, fd and e broader suites fail when their fixture assumptions meet long
repo-local scratch paths or a containing Git checkout. Their normal CI suites
passed. Their help changes do not relax assertions or alter those runtime paths.

Vault's macOS cache fixture exceeded the socket path limit in a worktree.
[Issue 32](https://github.com/laputa-systems/vault/issues/32) is fixed by shortening
the fixture basename. Production path validation is unchanged.

Xsh's macOS build failed because directory cleanup assumed an unsigned 64-bit
device identifier. [Issue 5](https://github.com/laputa-systems/xsh/issues/5) tracks
the focused repair to preserve the platform's native device type. Build succeeds;
the changed-path gate and both runner/tooling help checks remain in progress.

Fastermod landed through a direct push that bypassed a server-side PR requirement.
All subsequent changes use PRs and wait for their checks. No release or managed
installation has been performed.
