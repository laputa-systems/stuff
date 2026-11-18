# Deslop checkout cleanup, 2026-11-17

Four mechanic lanes inventoried build, CLI, application and systems
checkouts beneath `~/repos`. Retirements covered completed campaign
worktrees with verified default-branch integration. The inventory and
removal checks used the physical checkout paths.

| Repository | Integration revision | Retired worktrees under `.work/wt/` | Removed allocation, KiB |
| --- | --- | --- | ---: |
| `laputa-systems/buildlib` | `a749bbad6b74ba3301340c3cffaf2798aad5924a` | `cg`, `cov`, `te` | 292,816 |
| `extensions` | `66259229057b34e7405bc334f4d421f301a8431e` | `br`, `fs`, `mv`, `st`, `mvci`, `mvreport` | 854,612 |
| `pytest-parallel` | `e54d5b2fd9ff6b29bb53dbac9b658ced61d1f8e8` | `ds-diagnose`, `ds-ground`, `ds-types`, `cov` | 270,936 |
| `loc` | `ac9ffed236687b194f0637244f569817feabf78f` | `asm`, `cnt`, `co`, `first`, `lga` | 3,798,000 |

The CLI lane also removed four old generated `loc_init_test_*` fixtures
from loc's `.work/tmp`, totaling 16 KiB. Smolith's inactive
`.work/tmp/protocol-target` was a 1,444,880 KiB Cargo target used by the
protocol checks. A Cargo clean dry run identified 16,824 files, and the
target path was absent after the clean.

Every retirement passed a clean-status and ancestor check, an open-file
check and a `worktree-retire` dry run. After removal, the path was absent and
Git no longer listed it as a worktree. Useful ignored evidence was moved
to `.work/deslop-retired-evidence/<worktree>` in each repository first.
Loc's nine nested Cargo targets were verified via `CACHEDIR.TAG`, checked
as ignored, and cleared with `cargo clean --target-dir` before the evidence
was moved.

The removed paths accounted for 6,661,260 KiB after subtracting preserved
evidence. `df -k ~/repos` showed available space rise from 318,952,104 to
320,681,560 KiB during the pass. Checkout allocations and available blocks
are separate observations on the shared APFS volume.

Active and parked work remains, including Stats and Stuff recovery,
Chromium's build, Srv #47, Vault #30 and retained performance inputs.
The mdevd-rs help worktree still contains three unintegrated commits.
Discover was outside the cleanup scope.

## Follow-up, 2026-11-18

The follow-up checked these worktrees for clean tracked and untracked state
and removed each with Git's normal worktree removal. The integrated reports
and the closed Linux draft keep the evidence available.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| FFmpeg-build | `75fb9ffbe015b53c64ab1d29aed413f52ce84be9` | `deslop-package-linux`, `deslop-package-mutation`, `deslop-controller-static` | 681,632 |
| Node-build | `79fb67417304aa304efcf9705fd18dae28e8b62b` | `deslop-release-lock`, `deslop-package-binding`, `deslop-build-revision`, `deslop-assembly-mutation`, `deslop-assembly-record-shapes` | 404,956 |
| Pi-build | `32324e80853b5b7a562234e51e6699891208fcad` | `deslop-vendor-mutation`, `deslop-release-merge` | 828,004 |

The ten paths accounted for 1,914,592 KiB (1.83 GiB) before removal. This
follow-up measured path allocation. The available-block measurement above
covers the original shared-volume pass.

## Later builder retirement, 2026-11-18

Nine completed builder worktrees passed `worktree-retire --dry-run`
against their integrated default branch. The tool confirmed each was
patch-equivalent before removing it. The owning PRs preserve the
tracked work and the worktrees are absent. Their branches remain
available for replay.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| FFmpeg-build | `73bd1a6357a6b1163321ed60209764c01ae5c0a8` | `deslop-release-collector`, `deslop-bootstrap-cache`, `deslop-stamp-recovery` | 356,692 |
| Node-build | `597add72e9b3ea144819bc751876f1b221f30c97` | `deslop-assembly-command`, `deslop-toolchain-lock`, `deslop-bytes-lock` | 332,088 |
| Pi-build | `992b70926ed50de0a4b9da317edaa57856e9d101` | `deslop-archive-member-inventory`, `deslop-vendor-inventory`, `deslop-fetch-admission` | 915,060 |

These paths totaled 1,603,840 KiB (1.53 GiB) before removal.
Three disposable detached inventory worktrees were also retired.
Their allocation is excluded from the total.

## Native proof follow-up, 2026-11-18

Three completed worktrees were retired after the owning merge retained
their test and artifact evidence. Git verified the FFmpeg checkout as
an ancestor and the Pi checkouts as patch-equivalent. Their paths are
absent and the Pi branches remain available.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| FFmpeg-build | `82bcb48153c33ac86c1b33b1f1a6cc05277ebcd2` | `deslop-native-macos` | 924,488 |
| Pi-build | `0da2614bfe44e628daea873343301aa2b7165e6d` | `deslop-pack-commands`, `deslop-companion-identity` | 484,412 |

The three paths accounted for 1,408,900 KiB (1.34 GiB). During the
FFmpeg retirement, available blocks on the shared volume rose from
284,085,620 to 284,810,924 KiB. This is a separate observation from
the measured checkout allocation.

## Completed checkouts, 2026-11-18

Three more worktrees were retired after the owning reports recorded
their results. Git verified the detached checkouts against their
default branches and the Mdevd report against its squash merge.

| Repository | Last checked revision | Retired worktree under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| e | `b29c90178b664e12d3c4f7f0f4f49772aee21c33` | `deslop-hi-lite-bracket-consumer` | 143,684 |
| Buildlib | `1497970d9454a6a9875b1f201cbaad71fd92a010` | `deslop-current-qualification` | 116,036 |
| Mdevd-rs | `81c378de7e5f66faa2af89cabdccbcbdfa918c46` | `deslop-mdevd-config-decisions` | 343,448 |

These paths accounted for 603,168 KiB.

Four more worktrees were removed after their exact file trees matched the
owning squash merges. CMake's exact archive and memory receipts are in its
owning report. Git removed each clean worktree without force.

| Repository | Last checked integration | Retired worktree under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| Mdevd-rs | `9603b750ef63e6abcbd284bb45c1a46b46c8e735` | `deslop-mdevd-event-records` | 75,640 |
| Mdevd-rs | `64826edd2e8efaa55540bf7d9cfb5cc1cbcb40ea` | `deslop-mdevd-node-path` | 59,540 |
| Doas-rs | `afe63f522ec0af3e40bf4ea075537fd834efbd45` | `stable-alpine-doas` | 1,172 |
| CMake-build | `0bbf8f4e900aa1590bb4c61241a5099190ab790b` | `stable-alpine-bootstrap` | 2,339,676 |

The four additional paths accounted for 2,476,028 KiB. Across all cleanup
passes, 47 retired worktrees and the listed generated artifacts accounted
for 14,667,788 KiB (13.99 GiB) of measured path allocation.

The native verification follow-up retired five more worktrees after
checking that their harnesses and receipts were recorded in the owning
repository. The temporary proof branches remain available on GitHub.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| Mdevd-rs | `9661631ba4e8d549abfa569820a24674966139c1` | `deslop-mdevd-native-guest`, `deslop-mdevd-guest-preparation` | 2,824 |
| Mdevd-rs | `da5c2c9757300a732ccba9fe591aa19681147403` | `deslop-mdevd-consumer`, `deslop-mdevd-consumer-harness` | 2,724 |
| CMake-build | `b71678b9ee99e01be264cd0f52a6c7d4eed5d03e` | `deslop-cmake-final-qualification` | 43,608 |

The XSH verification retired another two worktrees after the editor
comparison and benchmark evidence were merged in Hi-lite #19. The
editor's disposable Cargo lock override was restored before retirement.

| Repository | Last checked integration | Retired worktree under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| e | `b29c90178b664e12d3c4f7f0f4f49772aee21c33` | `deslop-xsh-highlight-consumer` | 110,588 |
| Hi-lite | `5a38860ba797d5d0cdcdf2221f5adf7edeb9b010` | `deslop-pin-xsh-vocabulary` | 224,204 |

Across all passes, 54 retired worktrees and the listed generated
artifacts accounted for 15,051,736 KiB (14.35 GiB) of measured path
allocation.


## Controller and diff follow-up, 2026-11-18

Ten further campaign worktrees were retired after comparing the changed
files to their owning merges. The detached Hi-lite baseline matched its
recorded source revision. Git removed each checkout without force.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| CMake-build | #29, #30, #32, #31 | `reuse-cmake-native-controller-cache`, `cmake-controller-cache-evidence`, `deslop-cmake-phase-records`, `cmake-bootstrap-projection` | 363,660 |
| Doas-rs | #8 | `deslop-doas-types` | 384 |
| Mdevd-rs | #22, #23 | `deslop-mdevd-parser-counts`, `deslop-mdevd-token-boundaries` | 78,532 |
| Hi-lite | #20, #21 and baseline `5a38860` | `diff-preview-context-range`, `deslop-hi-lite-diff-preview`, `deslop-hi-lite-diff-baseline` | 416,424 |

These paths accounted for 859,000 KiB. Across all passes, 64 retired
worktrees and the listed generated artifacts accounted for 15,910,736
KiB (15.17 GiB) of measured path allocation.


## Artifact and engine follow-up, 2026-11-18

Seven more worktrees were retired after the owning merges recorded their
proofs. The Node trial branch remained available after its PR was closed.
The detached Mdevd baseline used the recorded `8f38cb9` revision.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| Node-build | #37 and #38 | `deslop-native-node`, `deslop-node-native-artifacts` | 956 |
| Mdevd-rs | #24, #25 and baseline `8f38cb9` | `mdevd-invalid-argv`, `mdevd-sysfs-selection`, `mdevd-sysfs-selection-base` | 174,492 |
| CMake-build | #33 and #34 | `deslop-cmake-dead-code`, `deslop-cmake-package-archive` | 278,628 |

These paths accounted for 454,076 KiB. Across all passes, 71 retired
worktrees and the listed generated artifacts accounted for 16,364,812
KiB (15.61 GiB) of measured path allocation.


## Edge policy and Node budgets, 2026-11-18

Both worktrees were clean and idle, and their changed files matched the
merged trees. Git removed both worktrees without force.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| Stuff | #128 | `reject-edge-repository-redirects` | 126,584 |
| Node-build | #39 | `node-budget-boundaries` | 126,964 |

These paths accounted for 253,548 KiB. Across all passes, 73 retired
worktrees and the listed generated artifacts accounted for 16,618,360
KiB (15.85 GiB) of measured path allocation.


## Controller and guest verification, 2026-11-18

The retired worktrees were clean and idle. Each removed candidate
matched its accepted files. The closed Doas proof branch retains
the successful workflow revision.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| CMake-build | #38 and #39 | `cmake-cache-writers`, `cmake-cache-volume` | 173,572 |
| Doas-rs | #9 and #10 | `doas-kvm-qualification`, `doas-serial-guest` | 644 |
| Diff-pretty | #42 | `pager-sigterm` | 126,080 |

These paths accounted for 300,296 KiB. Across all passes, 78 retired
worktrees and the listed generated artifacts accounted for 16,918,656
KiB (16.13 GiB) of measured path allocation.


## Coverage and terminal follow-up, 2026-11-18

Eight integrated or proven worktrees were retired. Their branches and
durable verification records retain the accepted source and results.

| Repository | Last checked integration | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| CMake-build | #41 and #42 | `cmake-native-coverage-receipt`, `cmake-bootstrap-values` | 95,188 |
| Doas-rs | #11 through #15 | `doas-diagnose-final`, `doas-clear-kvm`, `doas-clear-status`, `doas-type-dispositions`, `doas-branch-coverage` | 9,604 |
| Diff-pretty | #43 | `pager-terminal-tests` | 137,628 |

These paths accounted for 242,420 KiB. Across all passes, 86 retired
worktrees and the listed generated artifacts accounted for 17,161,076
KiB (16.37 GiB) of measured path allocation.

## Stage and session follow-up, 2026-11-18

Nine more clean worktrees were idle at retirement. The changed paths
matched their accepted commits before removal. The two Doas trial trees
were ancestors of the retained proof revision linked from its default
branch. The closed trial and its hosted logs remain available.

| Repository | Last checked integration or retained proof | Retired worktrees under `.work/wt/` | Allocation, KiB |
| --- | --- | --- | ---: |
| FFmpeg-build | `32535b71`, `b0751940`, `4bd60762`, `004297dd` | `deslop-diagnose`, `deslop-controller-entry`, `deslop-stage-manifest-shape`, `deslop-verified-release-edges` | 319,760 |
| CMake-build | `fc472b1c` | `cmake-tree-identity` | 188,860 |
| Diff-pretty | `9ce6235e` | `scrl-session-finish` | 69,428 |
| Doas-rs | `0cab3038`, `45efba88` | `doas-cli-boundaries`, `doas-cli-help-boundaries`, `doas-cli-mutation` | 4,156 |

These paths accounted for 582,204 KiB. Across all passes, 95 retired
worktrees and the listed generated artifacts accounted for 17,743,280
KiB (16.92 GiB) of measured path allocation.
