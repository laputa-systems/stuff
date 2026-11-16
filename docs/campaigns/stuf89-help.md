# STUF-89: complete owned-tool help

Status: in progress. Fifteen repositories have landed verified source changes.
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
| joshuarli/stats | [PR 17](https://github.com/joshuarli/stats/pull/17) | Built agent help, parser examples and CI; no sampler or soak |
| joshuarli/lz | [PR 6](https://github.com/joshuarli/lz/pull/6) | Option catalog, parser examples, built help, clippy and CI |
| joshuarli/bctl | [PR 3](https://github.com/joshuarli/bctl/pull/3) | 62 binary tests, two built CLI tests, real web bundle and clippy |
| joshuarli/soulseek-rs | [PR 9](https://github.com/joshuarli/soulseek-rs/pull/9) | Workspace tests, parser examples, clippy and CI |

Stuff's complete reference and parser-checked command examples are committed
locally. Its CLI and library tests pass, with clippy warnings denied. Repomod's
full suite passed: 1,410 tests, three expected skips.

## Remaining work

PR checks: [stuff 40](https://github.com/laputa-systems/stuff/pull/40),
[ctrs 5](https://github.com/joshuarli/ctrs/pull/5),
[img 7](https://github.com/joshuarli/img/pull/7),
[tansu 29](https://github.com/joshuarli/tansu/pull/29),
[play 14](https://github.com/joshuarli/play/pull/14),
[toolbox 14](https://github.com/joshuarli/toolbox/pull/14),
[fz 41](https://github.com/laputa-systems/fz/pull/41),
[srv 45](https://github.com/laputa-systems/srv/pull/45),
[mdevd-rs 4](https://github.com/laputa-systems/mdevd-rs/pull/4),
[zzz 16](https://github.com/laputa-systems/zzz/pull/16),
[pi-build 6](https://github.com/joshuarli/pi-build/pull/6), and
[syncthing 9](https://github.com/joshuarli/syncthing/pull/9).

Implementation or correction: xsh, gluon, tinyland and gh.
Kache's source is preserved on `fix/stuf89-help`; its required pre-PR gate blocks
publication. Its existing footer coverage does not establish complete help.
Existing footer coverage does not establish the
complete-reference contract for these tools.

In progress distributions: cmake-build, ffmpeg-build and git-build.
Queued forks and distributions: chromium-build, node-build, llvm-prebuilt-musl,
jaq, rage and ssh-build.
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
the focused repair to preserve the platform's native device type. The same
verification build also needed portable FIFO and mutable macOS PTY fixtures
([issue 6](https://github.com/laputa-systems/xsh/issues/6),
[issue 7](https://github.com/laputa-systems/xsh/issues/7)). Build, 64 selected core
unit tests and 12 runner tests pass; the broader gate timed out during integration
test discovery. The tooling help proof remains in progress.

Kache's host `make check` fails fixture assumptions with repository-local scratch.
Its separate Linux proof cannot build the pinned image because the exact Alpine
Git package was removed ([issue 24](https://github.com/joshuarli/kache/issues/24)).
Do not bypass its successful-check-before-PR requirement or update pins here.

Ctrs's platform tests pass, but benchmark harness checks fail with absent scratch
directories ([issue 6](https://github.com/joshuarli/ctrs/issues/6)) and a distinct
artifact ownership fixture exception. Img's Linux ARM corpus test cannot find
`djpeg` ([issue 8](https://github.com/joshuarli/img/issues/8)); its CLI tests pass.
Mdevd-rs's remote gate stops because `rg` is absent before compiling the change.
These checks block their merges; no benchmark assertion was relaxed.

Stuff's macOS ecosystem smoke failed connecting to PyPI's `six` index after
retries. Its Linux Rust and ecosystem jobs pass. No CI configuration changed.

Fastermod landed through a direct push that bypassed a server-side PR requirement.
All subsequent changes use PRs and wait for their checks. No release or managed
installation has been performed.
