# Deslop cleanup: build repositories

Inventory date: 2026-11-17. Scope: physical checkouts under `/Users/josh/repos` for
`laputa-systems/{buildlib,cmake-build,node-build,ffmpeg-build,chromium-build}` and
`pi-build/tools`. No source checkout or scratch path was changed. No cleanup candidate met
the required ownership, staleness, evidence, and no-consumer checks, so allocated KiB
removed is **0**.

## Proof record

- Writable change: this receipt only.
- Anchor: `/Users/josh/d/stuff/.work/wt/cleanup-builds`, base
  `7d7b81df26b69624ff16fb5a83d20f9c1d7fd962`.
- Every target resolves physically to the same `/Users/josh/repos/...` path named in scope.
- `git -C PATH status --short` returned no lines for all six repository roots (exit 0).
- `git worktree list --porcelain` (exit 0) was run for each root. Full physical root heads
  and additional registered worktrees are recorded below. No candidate worktree was
  identified by an in-scope campaign record as completed and ready for retirement; therefore
  no `worktree-retire ... --dry-run` was applicable. All worktrees remain. Specifically, do
  not retire `/Users/josh/repos/laputa-systems/buildlib/.work/wt/review`; it is explicitly
  active in the scope. Its observed HEAD changed during this inventory, further supporting
  preservation.
- No scratch was cleared; `test ! -e EXACT_PATH` was therefore inapplicable. No `rm`,
  `git clean`, worktree removal, build, release, remote write, or global-cache operation ran.
- `df -k /Users/josh/repos` before inspection: `/dev/disk3s5`, 1,948,404,040 blocks,
  1,589,142,772 used, 318,634,888 available, 84%.
- `df -k /Users/josh/repos` after inspection: `/dev/disk3s5`, 1,948,404,040 blocks,
  1,588,941,680 used, 318,835,976 available, 84%. No cleanup occurred; this filesystem
  movement is unrelated background activity and is not credited to this task.

## Physical repositories and retained worktrees

All `git -C PATH rev-parse --show-toplevel`, `git -C PATH rev-parse HEAD`,
`git -C PATH status --short`, and `git -C PATH worktree list --porcelain` commands
completed successfully. Root status was clean in each checkout.

| Physical checkout | Root HEAD | Worktrees retained |
| --- | --- | --- |
| `/Users/josh/repos/laputa-systems/buildlib` | `890b5bd088a0b71f3436a6da1b2265a5a88720e7` | `/Users/josh/d/stuff/.work/wt/buildlib-branch-control` `f14661d60eec421070ca3992b14fa8737b4aacf3`; `/Users/josh/d/stuff/.work/wt/buildlib-delete-control` `950f1690b1b3a73fba734d3d0e5aff5b7d0af7ae`; `/Users/josh/d/stuff/.work/wt/buildlib-docs-control` `473e1ee7f9ce282c365c707b77532a8ed1c8735d`; `/Users/josh/d/stuff/.work/wt/buildlib-mixed-oracle` `f4094326b207ddefe7c50a2897064da550d7e7c5`; `/Users/josh/d/stuff/.work/wt/buildlib-retention` `cf8391d5a80a8117ab513a13734a6494df5c4f25`; `/Users/josh/repos/laputa-systems/buildlib/.work/wt/cg` `aa4211d7d26bb6e7019f4fd6729d3f8a29bd7544`; `/Users/josh/repos/laputa-systems/buildlib/.work/wt/cov` `8d7e8739c8ce1d25454b346d431850841064f6a0`; `/Users/josh/repos/laputa-systems/buildlib/.work/wt/mix` `7bef43ebcc23641edd465cd584c01fd0ad8bddd2`; `/Users/josh/repos/laputa-systems/buildlib/.work/wt/review` `51dc170d0c94a68965c712df8ca52cba7db9b2fe`; `/Users/josh/repos/laputa-systems/buildlib/.work/wt/te` `7af819fb86507d992ca8089a7b66b16e3c6458db` |
| `/Users/josh/repos/laputa-systems/cmake-build` | `538efea3512ccfd98839f2ce8aff83107c47383c` | none beyond root |
| `/Users/josh/repos/laputa-systems/node-build` | `5deebd839b66cbe4e21bc1958c53a5d651b52dad` | `/Users/josh/d/stuff/.work/wt/buildlib-consumer-node` `5deebd839b66cbe4e21bc1958c53a5d651b52dad` (detached, outside physical scope); `/Users/josh/repos/laputa-systems/node-build/.work/wt/bl-be` `50ee5f5160d1c2b6d1d30e80711ffc4d3da157e0` |
| `/Users/josh/repos/laputa-systems/ffmpeg-build` | `539141d40ffecd42c1eada9abaea1475927a7cf0` | `/Users/josh/d/stuff/.work/wt/buildlib-consumer-ffmpeg` `539141d40ffecd42c1eada9abaea1475927a7cf0` (detached, outside physical scope) |
| `/Users/josh/repos/laputa-systems/chromium-build` | `05b05f775e2e25fd83cd5f308766afa9387e82a7` | `/Users/josh/d/stuff/.work/wt/buildlib-consumer-chromium` `05b05f775e2e25fd83cd5f308766afa9387e82a7` (detached, outside physical scope); `/Users/josh/repos/laputa-systems/chromium-build/.work/wt/cleanup-idle-source` `eef3bef46c6ecbe475bdcbb05b77a8443a68d613`; `.../.work/wt/fix-hid-unavailable` `f760f16452d730a6446bda2e5d973757f7879f6b`; `.../.work/wt/fix-ruff-lint` `eebaf66e8a13570e101280cfd4e7b5fdb26762d3`; `.../.work/wt/helium-idle-r7-build` `edf9e844ed8d28e0f69840482b9ccef7b3a9d613`; `.../.work/wt/helium-r7-pure-qualify` `eef3bef46c6ecbe475bdcbb05b77a8443a68d613`; `.../.work/wt/lint` `13f8f9538cb013ecb5f028cfd4e7b5fdb26762d3`; `.../.work/wt/linux-adblock` `a91dd59680f67e817499b7ba6bb0b1b0c489f609`; `.../.work/wt/macos-helium` `d39d9f2d13d02ac36ff7a300775e1ce0f4c2b137`; `.../.work/wt/merge-r7-main` `dd209c810fe0342cf02d22a3a9d88abcbbb7e7b9`; `.../.work/wt/perf-idle-frame-deadline` `b7f223f65110e1dd668e9ecc5ad1d668262a960a`; `.../.work/wt/perf-ui-frame-settings` `e6f569f787f2517c7e4d068576d3482ccbfe4634`; `.../.work/wt/pure-closure` `e9809cb544f09b695a066e31fd24608298c6c7f2`; `.../.work/wt/pwritev2` `4275db88a4b3883c0316d99e03968a7f9ad9701a`; `.../.work/wt/release-scratch` `6998a398f9d2e46998ebd2ae831309ecd2f1c8d7`; `.../.work/wt/stuf89` `a615f491d828ac913755b0edd43f0c09faed95ae`; `.../.work/wt/upgrade-chromium` `eadbbfd088d37746ed1bacc89eb94630f0282589`; `.../.work/wt/wayland-display` `938c82faade00039bef1d1fc74da74aedb1583da` |
| `/Users/josh/repos/pi-build` (tools component inspected) | `442f463954a6ead8fb9223f8c148bcc4c1bc66cf` | `/Users/josh/d/stuff/.work/wt/buildlib-consumer-pi` `442f463954a6ead8fb9223f8c148bcc4c1bc66cf` (detached, outside physical scope) |

All `/Users/josh/d/stuff/.work/wt/...` entries resolve outside `/Users/josh/repos` and
were preserved. The buildlib `review` worktree was listed as HEAD
`a749bbad6b74ba3301340c3cffaf2798aad5924a` in the first inventory and later as
`51dc170d0c94a68965c712df8ca52cba7db9b2fe`; no action was taken on it.

## Scratch decisions

- Buildlib `/Users/josh/repos/laputa-systems/buildlib/.work/tmp` allocated 1,480 KiB
  in the bounded `du -sk` inventory. It contains `blib-1.patch`, `blib-2.patch`,
  `backlog-start.json`, a uv lock, and `pytest-of-josh` state. Patch/backlog provenance,
  live use, and unique evidence status were not proven stale; preserve all. Buildlib's
  `AGENTS.md:8-10` defines `.work/tmp` as scratch output for commands, but that does not
  establish these particular files as disposable.
- CMake `/Users/josh/repos/laputa-systems/cmake-build/.work` allocated 220 KiB and
  consisted of worker-bridge data and an empty `wt` directory; retain because worker
  session ownership/use was not established.
- Node `/Users/josh/repos/laputa-systems/node-build/.work` allocated 676 KiB, including
  worker-bridge data and the registered `bl-be` checkout. Retain; the checkout is not
  proven superseded.
- FFmpeg `/Users/josh/repos/laputa-systems/ffmpeg-build/.work` allocated 212 KiB and
  includes cached pinned source inputs plus worker-bridge records. Preserve inputs and
  session evidence.
- Chromium `/Users/josh/repos/laputa-systems/chromium-build/.work/tmp` contains lock
  inputs, archives, generated toolchain files, command logs, and prepared build sources.
  A running build was observed: PID 21555, command
  `scripts/macos_backend.py --repo-root .../.work/wt/macos-helium --platform macos
  --arch arm64 --profile macos-helium-release --command build`; its parent shell PID
  21372 runs `MACOS_SKIP_ACCEPTANCE=1 .work/tmp/hb.sh configure build stage-runtime package`
  in that same worktree, and Ninja PID 21574 builds its output. Preserve the active
  worktree and all potentially consumed inputs. A full recursive size scan of this
  large `.work` tree was stopped after it remained blocked in `du`; no bytes were
  changed. This leaves exact Chromium `.work` allocation unmeasured.
- `pi-build/tools` contains `__pycache__`; it is generic generated Python state, not
  attributed to a completed deslop run, so it was preserved. The tools tree had no
  repository-specific `AGENTS.md`; pi-build root status was clean.

## Evidence and unverified cases

- Cleanup rules applied from `/Users/josh/usr/dotfiles/base/.agents/skills/cleanup/SKILL.md:12-22`:
  retain active/in-flight/unknown paths; establish live fixtures and prepared inputs;
  leave ambiguous cases; report exact retained reasons.
- Buildlib checkout guidance: `/Users/josh/repos/laputa-systems/buildlib/AGENTS.md:8-10`
  puts command scratch under `.work/tmp`. Chromium checkout guidance at
  `/Users/josh/repos/laputa-systems/chromium-build/AGENTS.md:20-38` identifies active
  build flows and authoritative pinned inputs.
- The shared status record `/Users/josh/d/stuff/.work/wt/cleanup-builds/docs/campaigns/deslop-status-20261117.md:74-79`
  records a separate disk cleanup in the `stuff` checkout; it supplies no completed
  cleanup ownership or integration proof for any target here.
- No in-scope candidate had sufficient campaign ownership/integration proof for
  `worktree-retire PATH --into VERIFIED_REV --dry-run`. Worktree lock state and exact
  integration were not audited for the retained inventory; those are unverified and no
  retirement is proposed. The old mutation, qualification, parked, and repair lanes
  remain preserved.
- No exact scratch candidate was cleared, so there is no absent-path check to report.
  `du -sk` totals observed above are allocated KiB for named scratch roots only; no
  before/after scratch delta exists. Filesystem-level `df` values are recorded above.
- No checkout outside the six roots, no Python-build checkout, and no global cache was
  inspected or changed.
