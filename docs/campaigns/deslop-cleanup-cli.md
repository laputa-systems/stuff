# CLI repository cleanup receipt

Snapshot taken 2026-11-17 in isolated anchor `7d7b81df26b69624ff16fb5a83d20f9c1d7fd962`.
Only the assigned repositories under `/Users/josh/repos` were inspected for cleanup.
Existing canonical roots had clean tracked/untracked status. No source, branch, or worktree
was modified or retired. One set of stale, ignored test output was reclaimed in `loc`.

## Physical checkout inventory

`realpath` resolved every existing assigned canonical root to its requested `/Users/josh/repos`
path. `/Users/josh/repos/e` is absent; the differently named `/Users/josh/repos/laputa-systems/e`
was not substituted or inspected. Every existing canonical root below had an empty
`git status --short` result. Default refs are the local `origin/HEAD` targets and their exact
local integration revisions; no fetch or remote write was performed.

| Canonical root | Root HEAD | `origin/HEAD` → local revision | Registered worktrees (path @ HEAD) |
| --- | --- | --- | --- |
| `/Users/josh/repos/laputa-systems/fastermod` | `e4d8be692d0ef3497447e027222cf6e04b2f374b` | `origin/main` → same | `.work/tmp/bool-toggle` @ `817ac41878d60a3261a963f98507799e7e605cf3`; `.work/wt/llvm` @ `b70a5df7c9fa75ecead8774e592cc4bab82ccef4`; `.work/wt/release-profiles` @ `f893e2d9f531618b135f8379e1d4aab58df22e2c`; `.work/wt/upgrade-fastermod` @ `f613172df0aac4d918beb38282de7bfcf47c83a3`; `.work/wt/upgrade-vuln` @ `e0304a65ccd3ccc51cc458cab9ae03986a1dae3d` |
| `/Users/josh/repos/laputa-systems/fz` | `89f7d9a1f81d737ddba3b85c37bc914e69fc10f4` | `origin/main` → same | None under `/Users/josh/repos`; external worktrees are listed below |
| `/Users/josh/repos/laputa-systems/diff-pretty` | `bb03d98ffbcf1e05f1a517d250e69b3f0bcf888c` | `origin/main` → same | `.work/wt/ab` @ `6ba0962f002cd0f03ad50ede43216bf581a8c228`; `al` @ `aa0e5053aced5644db254acdc0e392a517abb7d2`; `ap` @ `6f1719d8f0bb1ff9ab42ea0fcc91994ea9909ccb`; `cc` @ `03d8acec93d7594aeedb5a74a7434b99ac5643fd`; `ce` @ `02f0723400c584078b42290ceddecc9521353231`; `cg` @ `872ae4c9e41dbeacb37515da32c820670ce668df`; `dr` @ `c057a5fd92f027c13dfd7af24fccc7802c2bd930`; `ds` @ `6f1719d8f0bb1ff9ab42ea0fcc91994ea9909ccb`; `ds-controls-perf` @ `d712a2ba2d18e1061f6404d2de26947d68f8576a`; `ds-perf` @ `31a1831e5af59353b41dd4d63ffedf679a5514b4`; `ds-perf-base` @ `49a1c97d1f60932c3d860318672ecdcc545a0986`; `lf` @ `1010323e50d6a976b8f74fa2b14de69ef9743677`; `llvm` @ `ed5df07cacfe6a79141c53e2644969cf6036ac04`; `upgrade-diff` @ `c5302bddeedac1ef4066b0de1e53d1f56008b122` |
| `/Users/josh/repos/laputa-systems/ptytest` | `3fd48afe94e3f8dd5a145a64afe7061a9830529a` | `origin/main` → same | `.work/wt/btree` @ `f5ecc06748da0685dab90dfe5599d78db9946803`; `.work/wt/lint` @ `dfdf717aafa952dcbaa376f9e62ffb475c183fc6` |
| `/Users/josh/repos/laputa-systems/tm` | `6cf0b949c2593c0959268a3d1995b972b05f58b6` | `origin/main` → same | `.work/wt/acg` @ `8fffdf00b5319dfd95573dd1a83e411359df99b2`; `btree` @ `b4178f05cff8b555e94ef78b746e654788cf1d06`; `lint` @ `3296210d91840fbad7ec9038e37a06a7b2b52f60`; `llvm` @ `cfea22e145ebecedfde743303d6169439252e800`; `owned-help` @ `d4ce842fd6bb85a3214176ce7aac77306b407cf1`; `pins` @ `0d7e73188e222d872f97d62ee95fe7bf76539e65`; `pp` @ `6cf0b949c2593c0959268a3d1995b972b05f58b6`; `toggle` @ `68bc9bf3f5123ace12b8e3cb0669e1caf62e06ce`; `upgrade-tm` @ `93cc193781dbd044216c7c414b5f53b2d14099c1` |
| `/Users/josh/repos/laputa-systems/hi-lite` | `da3d6bee550caf68a547307e1c563eea1ed49d53` | `origin/main` → same | `.work/tmp/bool-toggle` @ `99ecf10e8ad018c18cad8ab736780e872e578e87`; `.work/wt/btree` @ `3481b2f4e006732d772c9b532432914b30123bb2`; `/Users/josh/repos/laputa-systems/hi-lite-all-green-majors` @ `8db60b26dbc00b732781d3c66eddf99302891bbf` |
| `/Users/josh/repos/laputa-systems/rustybench` | `dbb1ca77bd14d2dab5f3ba5f828f05bfba89b29d` | `origin/main` → same | `.work/wt/btree` @ `1784fb6609e70cb8b302852d57504e422b8f5c08`; `lint` @ `3230166f7b7bdc3f26ab67aa17aaaabcdf8745ea`; `llvm` @ `136eece8fd2ca457861cf7d90d354950f9785505` |
| `/Users/josh/repos/loc` | `ac9ffed236687b194f0637244f569817feabf78f` | `origin/master` → same | `.work/wt/asm` @ `92ffad1965ff9f3662b257922c0b50f4279d83cc`; `cnt` @ `f5603d85b27d53464c1c9836e0a72b171efc25f3`; `co` @ `0e8794497441026de8cdbb58bed77122e456dcf6`; `first` @ `d0867b2169aa0a382478efb685f559474d5edbab`; `lga` @ `897131f0948931480008d9b4363a4fb5bfc6ca85`; `ms` @ `77b4ce3c17bb13f7c61240a858668bd85a04df69` |
| `/Users/josh/repos/lz` | `722d74c4f24eaf7263da75a884d5a0017e4613be` | `origin/master` → same | `.work/tmp/bool-toggle` @ `461acda8ca17b893d8400db5cbe166130f3c148d` |
| `/Users/josh/repos/e` | absent | n/a | n/a |
| `/Users/josh/repos/defuddle-rs` | `63a23ca89d409d2e211991d5bd8ebfc1dc349716` | `origin/master` → same | `.work/wt/btree` @ `bc2a98dcff7cd527e36628d94da539ae6c989296`; `lint` @ `da7e99446569556f5afa68bb68913484f32756f0`; `upgrade` @ `eb2e14f198d430688fbfb8cbcc584e518a14802b`; `upgrade-atty` @ `cfe692a21440e3acdc8022feb029a36444a30abe` |
| `/Users/josh/repos/pytest-parallel` | `c07dceb0a5e52971ac9cb6512eaa6e475d687fee` | `origin/main` → `1fd7566c160e0e660aa565c490f4faa6d33bb119` | `.work/wt/cov` @ `7e0f0c9bc6ef45a8e9580623c2f7bd022099309b`; `ds-diagnose` @ `60129d817c3f82f075a8a8dc12578866ed135a10`; `ds-ground` @ `4968f8e59563c92e4617fcafd7ab322d64ff6c9c`; `ds-ground-finish` @ `0ecb2b3f8285c37725050246e99cfe4c10a54e41`; `ds-types` @ `85ef2ff7303da5af52d97fa1ecefb02fb123ec4b`; `ev` @ `e49e7fb1080a8766c28c2257b8261966aef8dcd0`; `fix-flake` @ `42e2d3e007b2d8abed5061cfb47c0cb3c22418be`; `he` @ `2c6957155dce22853dbadd9ade66e8b0cbc59fbe`; `lint` @ `ca6cc4badf0f2ec3a9d39cf9414431b5b15136ce`; `mut` @ `ef73bbe6e4c29641ad79a806b13053151ab053d1`; `ng` @ `56f608fbb05b99d8c9011f1af55c22b5188b25e4`; `ultrareview` @ `d3e1a7e914eb803eeddf1d32081e6997a2b863ce`; `upgrade-pins` @ `b3d23e8af2e3daad94bb37a90b0a9eb1973e3329`; `wr` @ `fe80b262ffdb1dc0767ae50b3e3ae5319b62480a` |

Noncanonical registered worktrees outside `/Users/josh/repos` were left intact and were not passed
to `worktree-retire`: Fz `/Users/josh/d/stuff/.work/wt/fz-mutation-cost` @
`0993fa389ad4bd550a73714ccaa4b4ae8e0b60b2`, `fz-retention-ci` @
`4d8a43c00aedbd8e8bdae558e95741788a10f4c2`, and `pty-drop-fz` @
`eebed611362d5d2b9b1e430633fbf0ab86be23e0`; Diff's
`/private/var/folders/h5/z5h1tjvn4hv1h02qfyvjsmg80000gp/T/opencode/diff-pretty-dist` @
`7d5a40283fcbc24091e832501181d03406f38556`, plus `/Users/josh/d/stuff/.work/wt/` entries
`diff-pretty-branch-control` @ `9380d613560bbdb13ef7154b3b45c2f20cf3e37e`,
`diff-pretty-delete-control` @ `b3ea3477273cd503239cc1368066ea8a98347933`,
`diff-pretty-docs-control` @ `e95385e4e6060ed4d0a20617652e2d746bb7d669`,
`diff-pretty-mixed-control` @ `4381ba3ac5d74fc382d429ff44ed9c4bcacdc246`,
`diff-pretty-retain` @ `6dd965dd9688308db175f33d0c5b15ac90abac54`, and
`diff-pretty-suite-base` @ `49a1c97d1f60932c3d860318672ecdcc545a0986`; Tm
`/Users/josh/d/stuff/.work/wt/pty-drop-tm` @ `6cf0b949c2593c0959268a3d1995b972b05f58b6`;
Loc `/Users/josh/d/stuff/.work/wt/loc-test-inventory` @
`8902fb4c2ec23ac11fdb529cf929a92071892932`; Lz
`/Users/josh/d/stuff/.work/wt/pty-drop-lz` @ `722d74c4f24eaf7263da75a884d5a0017e4613be`;
and Pytest-parallel `/Users/josh/d/stuff/.work/wt/pytest-empty-bind` @
`247e81cd0d9ae1e81c906c77cb1117834afdd719`, `pytest-event-bound` @
`5b096a51e33f73f742afb23e431f9585d5716725`, and `pytest-gate-inventory` @
`6238f5697b17d7af5602dce2056551bac7035583`.

Fastermod's four `llvm`, `release-profiles`, `upgrade-fastermod`, and `upgrade-vuln` worktree
records said `prunable: gitdir file points to non-existent location`; their registered paths were
not treated as removable scratch. Other unmerged upgrade/btree/bool-toggle worktrees remain.
Diff-pretty's current `ds`, `ds-controls-perf`, `ds-perf`, `ds-perf-base`, and `cg` worktrees
remain because the campaign records leave Tests/platform verification open. Tm's Ground evidence
and quiet-host cost remain open. Fastermod's Diagnose/Tests and quiet-host performance rerun,
Ptytest's Diagnose/consumer proof, and Pytest-parallel's whole-change retention remain open.
The records also identify retained performance, parity, and verification inputs; none were
removed. See checkout instructions at Fastermod `AGENTS.md:20`, Fz `AGENTS.md:14,28`, Tm
`AGENTS.md:6,9,16`, and Lz `AGENTS.md:9,11,311`.

## Scratch cleanup

Removed exactly four ignored generated test directories from `/Users/josh/repos/loc/.work/tmp`:

| Exact path | Allocated before |
| --- | ---: |
| `/Users/josh/repos/loc/.work/tmp/loc_init_test_19728_1794695407949417000_specified_path` | 4 KiB |
| `/Users/josh/repos/loc/.work/tmp/loc_init_test_19728_1794695407949426000_no_force` | 4 KiB |
| `/Users/josh/repos/loc/.work/tmp/loc_init_test_19728_1794695407949431000_force` | 4 KiB |
| `/Users/josh/repos/loc/.work/tmp/loc_init_test_19728_1794695407949449000_content_check` | 4 KiB |

Ownership is exact: `loc/src/init.rs:115,126-163` creates timestamped
`loc_init_test_*` directories; the four remaining children were `custom.toml`, `existing.toml`,
`overwrite.toml`, and `check.toml`. `git status --short --ignored -- .work/tmp` returned `!! .work/`.
All four were dated 2026-11-14 14:30:07. `ps -p 19728 -o pid=,lstart=,command=` exited 1
with no process; `lsof -nP +D EXACT_PATH` exited 1 with empty output for each directory. The
broader process snapshot had no loc test or cargo test process. The live set therefore contained
no writer or open consumer for these stale generated test outputs.

The individual `unlink EXACT_FILE` commands and corresponding `rmdir EXACT_DIRECTORY` commands
each exited 0. Required post-cleanup checks all passed: `test ! -e EXACT_PATH` exited 0 for each
of the four exact paths. Allocated space before was 16 KiB total; `/Users/josh/repos/loc/.work/tmp`
then measured 0 KiB. No glob, worktree removal, source edit, cache cleanup, or global cleanup was
used.

Other repo-local data was retained: Fastermod `.work` was 236 KiB; Diff-pretty
`.work/tmp/rb` was 2,220 KiB (versioned rustybench tool inputs); Tm `.work/tmp/tmux-3.8` was
17,364 KiB (the documented tmux 3.8 parity reference). The Fastermod performance rerun is
pending and its checked-in benchmark/workload inputs remain. Fz's pinned fzy oracle, Lz parity
fixtures and oracle tools, Tm fixture evidence, and the Diff/Pytest active verification worktrees
remain untouched.

## Worktree retirement candidates reviewed

`git worktree list --porcelain` was run with `git -C ROOT` for every existing canonical root.
The completed, clean, unlocked Loc and Pytest-parallel deslop lanes below were candidates by
merged-head proof against the exact local `origin/HEAD` revision. `git status --porcelain
--untracked-files=all` was empty and `git merge-base --is-ancestor HEAD INTEGRATION` returned 0
for each. Each `lsof` returned 1 with empty output (no open files). The required dry runs were
then performed; `worktree-retire` exit 1 means it kept the lane because ignored content needs
review. No `--discard-ignored` or retirement command was run.

| Candidate path | HEAD | `--into` integration | Dry-run exit / decisive output |
| --- | --- | --- | --- |
| `/Users/josh/repos/loc/.work/wt/asm` | `92ffad1965ff9f3662b257922c0b50f4279d83cc` | `ac9ffed236687b194f0637244f569817feabf78f` | 1; `.ruff_cache/`, `.work/`, `target/` |
| `/Users/josh/repos/loc/.work/wt/cnt` | `f5603d85b27d53464c1c9836e0a72b171efc25f3` | same | 1; `.work/`, `target/` |
| `/Users/josh/repos/loc/.work/wt/co` | `0e8794497441026de8cdbb58bed77122e456dcf6` | same | 1; `.ruff_cache/`, `.work/`, `target/` |
| `/Users/josh/repos/loc/.work/wt/first` | `d0867b2169aa0a382478efb685f559474d5edbab` | same | 1; `.ruff_cache/`, `.work/`, `target/` |
| `/Users/josh/repos/loc/.work/wt/lga` | `897131f0948931480008d9b4363a4fb5bfc6ca85` | same | 1; `.ruff_cache/`, `.work/`, `target/` |
| `/Users/josh/repos/loc/.work/wt/ms` | `77b4ce3c17bb13f7c61240a858668bd85a04df69` | same | 1; `.work/`, `target/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/cov` | `7e0f0c9bc6ef45a8e9580623c2f7bd022099309b` | `1fd7566c160e0e660aa565c490f4faa6d33bb119` | 1; `.pytest_cache/`, `.ruff_cache/`, `.venv/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/ds-diagnose` | `60129d817c3f82f075a8a8dc12578866ed135a10` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.venv/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/ds-ground` | `4968f8e59563c92e4617fcafd7ab322d64ff6c9c` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.venv/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/ds-ground-finish` | `0ecb2b3f8285c37725050246e99cfe4c10a54e41` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/ds-types` | `85ef2ff7303da5af52d97fa1ecefb02fb123ec4b` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/ev` | `e49e7fb1080a8766c28c2257b8261966aef8dcd0` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/he` | `2c6957155dce22853dbadd9ade66e8b0cbc59fbe` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/mut` | `ef73bbe6e4c29641ad79a806b13053151ab053d1` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.venv/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/ng` | `56f608fbb05b99d8c9011f1af55c22b5188b25e4` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.work/`, `__pycache__/` |
| `/Users/josh/repos/pytest-parallel/.work/wt/wr` | `fe80b262ffdb1dc0767ae50b3e3ae5319b62480a` | same | 1; `.pytest_cache/`, `.ruff_cache/`, `.work/`, `__pycache__/` |

These dry-run refusals are preserved for parent review; contents under ignored `.work/` and
`target/` may include lane evidence. The campaign status explicitly leaves Pytest-parallel's
whole-change retention unfinished (`docs/campaigns/deslop-scorecard.md:21` and
`docs/campaigns/deslop-roadmap.md:205`), so its source checkouts and ignored contents remain.
No retirement candidate was selected in other repositories: Fastermod, Ptytest, Tm, and
Diff-pretty have pending campaign verification (`deslop-roadmap.md:206,210-212`); remaining
unmerged, upgrade, parity, or noncanonical worktrees are retained. All such paths and heads are
in the inventory above.

## Disk readings and proof record

`df -k /Users/josh/repos` before cleanup exited 0:

```text
Filesystem   1024-blocks       Used Available Capacity  iused      ifree %iused  Mounted on
/dev/disk3s5  1948404040 1589170960 318606696    84% 18882178 3186066960    1%   /System/Volumes/Data
```

The same command after cleanup exited 0:

```text
Filesystem   1024-blocks       Used Available Capacity  iused      ifree %iused  Mounted on
/dev/disk3s5  1948404040 1589265108 318512548    84% 18899832 3185125480    1%   /System/Volumes/Data
```

Available space decreased by 94,148 KiB during the scan despite removing 16 KiB of allocated
scratch, so host activity masked any reclaimed blocks; no larger disk recovery is claimed. A
later final `df -k /Users/josh/repos` check after writing this receipt also exited 0 and reported
319,698,664 KiB available, confirming substantial unrelated host activity during the pass.

Decisive commands and results:

- `git rev-parse HEAD`: `7d7b81df26b69624ff16fb5a83d20f9c1d7fd962`; `git status --short`: empty
  before receipt creation.
- For each present canonical root: `realpath ROOT`, `git -C ROOT rev-parse HEAD`,
  `git -C ROOT status --short`, `git -C ROOT worktree list --porcelain`; the inventory command
  exited 0. `/Users/josh/repos/e` failed `test -e` and is recorded absent.
- Candidate eligibility check: `git status --porcelain --untracked-files=all` empty,
  `git merge-base --is-ancestor HEAD origin-default` exit 0, and no `locked` field for all 16
  candidates. `lsof -nP +D EXACT_PATH` exit 1, empty output, for all 16.
- `worktree-retire EXACT_PATH --into VERIFIED_REV --dry-run`: exit 1 with the ignored-file
  refusal shown per candidate above. No candidate was passed `--discard-ignored`.
- Four exact `unlink`, four exact `rmdir`, and four required `test ! -e EXACT_PATH` checks: all
  exit 0. Initial multi-operand `unlink` returned 64 (macOS `unlink` accepts one path); it made
  no changes and was rerun one exact file per successful command.
- `df -k /Users/josh/repos`: exit 0 before and after, readings above.

Unverified: current remote refs were not fetched; integration decisions use the recorded local
`origin/HEAD` targets. Ignored candidate contents were not discarded or individually classified;
the dry-run refusals preserve them for parent review. No builds, tests, releases, remote writes,
canonical source edits, or global cache cleanup were performed.
