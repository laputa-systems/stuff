# STUF-89: complete owned-tool help

Status: in progress. Thirty-four repositories have landed verified source changes.
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
| laputa-systems/zzz | [PR 16](https://github.com/laputa-systems/zzz/pull/16) | Native Linux built help, parser examples and CI; no power actions |
| laputa-systems/git-build | [PR 11](https://github.com/laputa-systems/git-build/pull/11) | Patched native macOS/Linux ARM products, qualification/runtime tests and CI |
| joshuarli/gh | [PR 16](https://github.com/joshuarli/gh/pull/16) | Full tests, stamped build, built footer/version/JSON/completion checks and CI |
| joshuarli/syncthing | [PR 9](https://github.com/joshuarli/syncthing/pull/9) | Native tests, Linux static build, local-fixture JSON/completion checks and CI |
| laputa-systems/srv | [PR 45](https://github.com/laputa-systems/srv/pull/45) | Full tests, clippy and CI including mutation gate |
| laputa-systems/jaq | [PR 15](https://github.com/laputa-systems/jaq/pull/15) | Workspace tests/doc tests, CBOR build, clippy and CI |
| joshuarli/pi-build | [PR 6](https://github.com/joshuarli/pi-build/pull/6) | Real assembled macOS product, archive proof, 18 command references/examples and CI |
| laputa-systems/rage | [PR 9](https://github.com/laputa-systems/rage/pull/9) | Both built binaries, CLI/version snapshots, workspace tests, clippy and CI |
| laputa-systems/ffmpeg-build | [PR 6](https://github.com/laputa-systems/ffmpeg-build/pull/6) | Real macOS tools product/audit, 73 controller tests, Ruff/ty and CI |
| laputa-systems/tinyland | [PR 4](https://github.com/laputa-systems/tinyland/pull/4) | Five isolated Linux parser/CLI tests and CI; no host daemon or compositor |
| joshuarli/tansu | [PR 29](https://github.com/joshuarli/tansu/pull/29) | Built help and parser examples, real frontend assets and CI |
| joshuarli/play | [PR 14](https://github.com/joshuarli/play/pull/14) | Real native CLI, parser tests, macOS/Linux PR checks and lint |
| laputa-systems/cmake-build | [PR 6](https://github.com/laputa-systems/cmake-build/pull/6) | Patched host CMake help, controller/lint CI; musl qualification remains unavailable |
| laputa-systems/ssh-build | [PR 17](https://github.com/laputa-systems/ssh-build/pull/17) | Eight native binaries, reproducible vendor patches, crypto graph and platform/fuzz CI |
| laputa-systems/gluon | [PR 16](https://github.com/laputa-systems/gluon/pull/16) | Shared parser/help names and defaults, release build, full parity corpus and CI |
| laputa-systems/stuff | [PR 40](https://github.com/laputa-systems/stuff/pull/40) | Complete stuff/repomod references and parser examples, local suites and every required PR check |
| joshuarli/kache | [PR 25](https://github.com/joshuarli/kache/pull/25) | Complete reference, pinned-nightly native Linux pre-PR gate, macOS/end-to-end and both Linux musl PR checks |
| laputa-systems/node-build | [PR 16](https://github.com/laputa-systems/node-build/pull/16) | Newly compiled native macOS Node help/version/JSON/completion proof, strict source patch tests and both required CI checks; locked distribution qualification remains separate |
| laputa-systems/llvm-prebuilt-musl | [PR 6](https://github.com/laputa-systems/llvm-prebuilt-musl/pull/6) | Native ARM build, 219 clean-package checks, five optimizer regressions, GNU/BSD strict patch regression and both native CI build/validation jobs |

Stuff's complete reference and parser-checked command examples are merged.
Its CLI and library tests pass, with clippy warnings denied. Repomod's
full suite passed: 1,410 tests, three expected skips.

## Remaining work

PR checks: [ctrs 5](https://github.com/joshuarli/ctrs/pull/5),
[img 7](https://github.com/joshuarli/img/pull/7),
[toolbox 14](https://github.com/joshuarli/toolbox/pull/14),
[fz 41](https://github.com/laputa-systems/fz/pull/41),
[mdevd-rs 4](https://github.com/laputa-systems/mdevd-rs/pull/4),
[xsh 9](https://github.com/laputa-systems/xsh/pull/9).

Existing footer coverage does not establish the
complete-reference contract for these tools.

Draft source with built-product proof blocked:
[chromium-build 21](https://github.com/laputa-systems/chromium-build/pull/21).
No repositories remain undispatched.
Python-build already has its maintained footer patch and executable help/version
test; its existing policy remains unchanged. No CPython/JIT campaign was resumed.

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
test discovery ([issue 8](https://github.com/laputa-systems/xsh/issues/8)).
The xsht schema/example and built primary/nested help checks also pass.
Remote lint formats the entire repository then reports extensive differences,
including unchanged source trees
([issue 10](https://github.com/laputa-systems/xsh/issues/10)); no formatter or CI
change was run locally.
Its Linux test job reached the 60-minute limit during the core corpus tests
([issue 11](https://github.com/laputa-systems/xsh/issues/11)); the last reported
unfinished test was the desugared corpus check, without an established cause.

Kache's required `make check` passed in native ARM64 GNU Linux before PR creation:
warnings-denied workspace clippy, the client graph, resource guard, 3,094 native
unit tests, all integration cases and the remaining workspace suites. Its three
reference tests and both built binaries' help/version/JSON checks pass on macOS.
The local pinned Alpine image build remains unavailable because its exact Git
package was removed ([issue 24](https://github.com/joshuarli/kache/issues/24)).
Both remote Linux musl checks, macOS tests, macOS end-to-end and lint passed on
`6b44c40d` before merge. No release artifact was published or installed.

To reproduce the successful GNU gate, use `rust:1.100.0-bookworm` with real
`clang`, `lld`, `zsh` and `python3` installed in the disposable container. Install
the repository's `nightly-2026-11-09` with clippy and rust-src. Bind the source
worktree; separately expose its absolute Git common directory read-only;
use a Linux-native volume for both scratch and Cargo target data. Run as the
source owner's unprivileged UID, with scratch outside any Cargo/Git ancestor,
`CARGO_BUILD_JOBS=2`, `RUST_TEST_THREADS=2`, and a two-CPU allocation:

```sh
make check TARGET=aarch64-unknown-linux-gnu \
  CARGO_CMD='env CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER=cc cargo'
```

Earlier root/APFS-bound attempts failed filesystem fixtures; the oversubscribed
native-scratch run hit one four-second wall-clock assertion. The isolated case
passed. A reused host-mounted target then lost an object file during archiving.
The final native target/scratch, bounded, equipped environment completed every
unchanged assertion. No timing threshold or test selection was changed.

Ctrs's platform tests pass, but benchmark harness checks fail with absent scratch
directories ([issue 6](https://github.com/joshuarli/ctrs/issues/6)) and a distinct
artifact ownership fixture exception. Img's Linux ARM corpus test cannot find
`djpeg` ([issue 8](https://github.com/joshuarli/img/issues/8)); its CLI tests pass.
Mdevd-rs's remote gate stops because `rg` is absent before compiling the change
(`MDEV-1` in its new root backlog).
These checks block their merges; no benchmark assertion was relaxed.

Fz's Linux/macOS functional and lint jobs pass; its mutation gate rejects a
buffer-size mutant in unchanged input reading
([issue 42](https://github.com/laputa-systems/fz/issues/42)). Toolbox's jobs did not
start because GitHub reports an account billing/spending limit. Its installed
CLI/lint checks pass; its local broader suite has an independent loudnorm failure.

CMake's patched native host binary passes the help test and its required PR
checks passed. Its separate qualified Linux build is blocked by the removed
locked `libcrypto3-3.5.9-r0.apk`
([issue 7](https://github.com/laputa-systems/cmake-build/issues/7)).
Node's locked distribution doctor requires Xcode 27.1/SDK 27.0 while the host
has only 27.2. The supported `build.py build --target aarch64-apple-darwin --jobs 2`
path compiled the SHA-verified Node 26.12.1 source without changing that gate.
The actual binary passes `buildsys.smoke.check_help_footer`: both help flags
end with the exact footer once, version/JSON are exact and completion has no
footer. Binary output `00 01 ff` is preserved. CI controller/lint checks passed
on `8f77bc1`; merge `5deebd8` lands the source. This establishes host product
behavior, not locked distribution qualification; the full local controller
suite still fails the unchanged doctor gate. No package was released or installed.
Chromium's native doctor and smoke-preflight require the missing Xcode Metal
Toolchain; its draft has no actual built-product proof.

LLVM's first fresh Linux CI build exposed asymmetric patch context rejected by
GNU `patch -F0`. Balanced context and `tests/clang-footer-patch.sh` repair it;
the new regression fails on the old patch and passes with both GNU and BSD
patch. Fresh application of the complete patch set is idempotent in Linux and
produces C++ byte-identical to the validated native ARM package. That package
passes 219 checks, including both actual Clang driver modes, and five optimizer
regressions. Both native CI build/validation jobs and lint passed on `2bbccee`
before merge `4507caa`. Reproduce the patch regression with
`TMPDIR="$PWD/.work/tmp" bash tests/clang-footer-patch.sh <pristine Driver.cpp>`
from the locked LLVM 23.1.5 archive; package proof uses `make build` and
`make verify` for the native target. No package was published or installed.

Stuff's first macOS ecosystem smoke timed out reaching PyPI; the next legitimate
policy update passed every required check, including macOS Rust.
No CI configuration changed.

Gluon's parity gate needed two host-specific test repairs
([issue 17](https://github.com/laputa-systems/gluon/issues/17)): compare defined
global Mach-O symbols without debug-map paths, and use a Darwin linker alias for
the C++ fixture's sentinel. The native regression test fails with the old symbol
selection; the full corpus passes with no ledger or acceptance-assertion changes.

Retired 31 completed repository worktrees after confirming integration and absence of live
consumers. [The cleanup record](stuf89-cleanup.md) lists exact paths and heads.

Fastermod landed through a direct push that bypassed a server-side PR requirement.
All subsequent changes use PRs and wait for their checks. No release or managed
installation has been performed.
