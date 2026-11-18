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
