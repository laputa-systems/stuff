# Scoped deslop disk cleanup receipt

Scope: `laputa-systems/{srv,vault,smolith,doas-rs,mdevd-rs,tinyland,stuff,jaq,rust-fontconfig,rustix,rage,fd,oxish,crabtables}` and personal `soulseek-rs`, only under `/Users/josh/repos`. No canonical source checkout was modified. Stuff was inventory-only. No worktree or scratch was removed.

## Physical checkout inventory

Each listed root resolved physically to the same `/Users/josh/repos/...` path and was clean at the recorded HEAD. The inventory command was the successful retry using `/usr/bin/git` after the shell could not resolve `git` or `realpath` on the first attempt.

| Checkout | HEAD | Root `.work` KiB; `.work/tmp` KiB |
| --- | --- | ---: |
| `/Users/josh/repos/laputa-systems/srv` | `c9965411d80a8b02d8b8c4cac2492ecc973ee296` | 122240; 104 |
| `/Users/josh/repos/laputa-systems/vault` | `0e72b21112b840aa5b7fa373eeeab79e63ed59bb` | 5113504; 223424 |
| `/Users/josh/repos/laputa-systems/smolith` | `5c794c6b2a05a8f5ade3f2160646ea7b60fc6752` | 4215836; 1446444 |
| `/Users/josh/repos/laputa-systems/doas-rs` | `ca4a12f8e554f8833e3de8d1b660ab1e5eadc1db` | 184; no root tmp |
| `/Users/josh/repos/laputa-systems/mdevd-rs` | `2fcc0c608c0999d248c83e2eba841d53be8aeb85` | 87128; no root tmp |
| `/Users/josh/repos/laputa-systems/tinyland` | `c30e8efe06cd28937e6b6fab5b64f13863cff9e6` | 3902108; no root tmp |
| `/Users/josh/repos/laputa-systems/stuff` | `bf40fb572212a518a19a495d8421087dfffe2690` | inventory only; no size walk |
| `/Users/josh/repos/laputa-systems/jaq` | `ac261459a1e70af07d7495f0d14af4806e665c22` | 1348; 0 |
| `/Users/josh/repos/laputa-systems/rust-fontconfig` | `cf9f073d744202db17204db2a6cf3a909c5da89f` | no root `.work` |
| `/Users/josh/repos/laputa-systems/rustix` | `1fb51827a51cd7bc081b3f802881cc482b45cdf8` | 0; no root tmp |
| `/Users/josh/repos/laputa-systems/rage` | `1c342bcd893a92a5fd6671794aa2865e9fae6aa7` | 160; no root tmp |
| `/Users/josh/repos/laputa-systems/fd` | `59e6e0233b95fc9fff271c538fe37f7a98df59bf` | 7424; 6488 |
| `/Users/josh/repos/laputa-systems/oxish` | `3c52aa28622eac897369f60fab07a90117146a10` | no root `.work` |
| `/Users/josh/repos/laputa-systems/crabtables` | `76765cf39bd50a8b1ffe891dceefa4410c11d187` | no root `.work` |
| `/Users/josh/repos/soulseek-rs` | `bf581b412f7e0229d7257de1c0e868f64813db94` | 5052; no root tmp |

## Registered worktrees and disposition

The exact inventory command was `git worktree list --porcelain`, run for each scoped canonical repository. These are the noncanonical registrations and their HEADs; each remains registered:

| Repository | Physical worktree path | HEAD | Disposition |
| --- | --- | --- | --- |
| srv | `/private/var/folders/h5/z5h1tjvn4hv1h02qfyvjsmg80000gp/T/opencode/srv-release-profiles` | `b91ac1edcc5141dd9cd337f4de730c5a90edd6fb` | Outside canonical root; Git reports prunable gitdir; preserved. |
| srv | `/Users/josh/d/stuff/.work/wt/srv-head-check` | `7cd8627b2669b80c72d45a14f43706b6ae0e33af` | `deslop/current-head-check`; explicitly preserved with Srv #47 work; outside `/Users/josh/repos`. |
| srv | `/Users/josh/repos/laputa-systems/srv/.work/wt/lint` | `d3c2cb9b806f151823e5906603c3081fcd56f477` | No campaign retirement proof; retained. |
| srv | `/Users/josh/repos/laputa-systems/srv/.work/wt/llvm` | `99f4b3131803b556a52e07714bb89cd2c9978224` | Other campaign ownership; retained. |
| srv | `/Users/josh/repos/laputa-systems/srv/.work/wt/upgrade-vuln` | `5f95642483cd1792680d891dfa7314fb070cbe65` | Other campaign ownership; retained. |
| vault | `/Users/josh/d/repomod/.work/wt/vault-release-profiles` | `0be1148fedd61983348a9dd5f8b398a5ff092524` | Outside canonical root; Git reports prunable gitdir; preserved. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/asc` | `0e72b21112b840aa5b7fa373eeeab79e63ed59bb` | Retained; ownership not shown as completed. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/b` | `47dfb47ec6a1f9de2ad2d0619d5fead9bc6d8d2d` | Retained; ownership not shown as completed. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ban` | `5fab411dec740618791921c99adfe3588bfb90ca` | Other campaign; retained; Git reports prunable gitdir. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/cg` | `e8c79312e9fa1faa503b90708ab50b414e720ecf` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/co` | `94c2210bf0c15c0d313b7785e5b515dd8958b651` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds` | `bf3dcd9b4d893dce12de453705ef0b73dae4e0bf` | Resumed deslop tests; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds-atomic` | `7db74f652af5cffc2fee21d956f1dc4dfcc091ec` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds-bootstrap` | `f655ec01735fc23998d05d18ad1bb070c533b30f` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds-faults` | `6856af3421b82cfb7ff6bf0d5b35eede660798aa` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds-identity` | `f82546e15860197a2d893daabcff1cf2d8075dbe` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds-independent-review` | `6856af3421b82cfb7ff6bf0d5b35eede660798aa` | Independent review; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds-list` | `9dbf993cd8de9d9a98ba1a2efc194af142b797a6` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/ds-mode` | `2c0035b6f5bdd75cd709d81ea5809a121683298a` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/pi` | `0e72b21112b840aa5b7fa373eeeab79e63ed59bb` | Retained; ownership not shown as completed. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/pt` | `c68d9ccdeaf44677270f483fff11b9714093743d` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/q` | `63b25c74862bf2971cc8b9a20c40dab702077744` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/sg` | `bf3dcd9b4d893dce12de453705ef0b73dae4e0bf` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/sig` | `e939a06dffc66df80bcf5677b1a5a5eb4e3f8601` | Parked candidate; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/upgrade-todos` | `8cef58f8fb88c0a1dbc4bbc553a12dd5632d5372` | Other campaign ownership; retained. |
| vault | `/Users/josh/repos/laputa-systems/vault/.work/wt/upgrade-vault` | `31a5937646691e5a437e06a6c8b212de4421380a` | Other campaign ownership; retained. |
| smolith | `/Users/josh/repos/laputa-systems/smolith/.work/wt/btree` | `dc3b9f0a34322af186d4d18f8b0eab1668144108` | Unresolved work; retained. |
| smolith | `/Users/josh/repos/laputa-systems/smolith/.work/wt/ctrs-response-shutdown` | `9e1984754c84272f5dd15b245db11e3b6773d8af` | Unresolved work; retained. |
| smolith | `/Users/josh/repos/laputa-systems/smolith/.work/wt/h12tiny-0.9-response-shutdown` | `448a24c7e799681d1a6a33b7668e47bbceb06587` | Unresolved work; retained. |
| smolith | `/Users/josh/repos/laputa-systems/smolith/.work/wt/qualify` | `ba58526a156bcde9aac829751be00efc1d455326` | Qualification work; retained. |
| smolith | `/Users/josh/repos/laputa-systems/smolith/.work/wt/upgrade-smolith` | `b08bab86341ddc18a24c546b827eca4df70c678c` | Other campaign; retained. |
| mdevd-rs | `/Users/josh/repos/laputa-systems/mdevd-rs/.work/wt/rustix-pilot` | `a429cb068091c7872bb88e14937ef7e59c144f84` | Unresolved pilot; retained. |
| mdevd-rs | `/Users/josh/repos/laputa-systems/mdevd-rs/.work/wt/stuf89` | `e0bb29461995b789fe8fe4f9962bf141b3bd6a72` | Candidate checked below; not integrated; retained. |
| tinyland | `/Users/josh/repos/laputa-systems/tinyland/.work/wt/merge-headed-upstream` | `56f11a932d27fa0b99a5721043ea06f4f265091f` | Unresolved integration work; retained. |
| tinyland | `/Users/josh/repos/laputa-systems/tinyland/.work/wt/nanos-virtual-display` | `351c5cc116a8f278369f2e5251d6dca4abed61ac` | Active campaign; retained. |
| tinyland | `/Users/josh/repos/laputa-systems/tinyland/.work/wt/remote-clipboard` | `63e91e5edcff4412dfd5b5009dd17c3aada89654` | Unresolved work; retained. |
| tinyland | `/Users/josh/repos/laputa-systems/tinyland/.work/wt/sr` | `c30e8efe06cd28937e6b6fab5b64f13863cff9e6` | No completion proof; retained. |
| stuff | `/Users/josh/repos/laputa-systems/stuff/.work/wt/stats-campaign-blockers` | `2a82b588cbb98ea8a34b1cc93aa08e1e807a47cd` | Inventory only; retained. |
| jaq | `/Users/josh/repos/laputa-systems/jaq/.work/wt/lint` | `d09b2633b48faf8eb3692796d2a2a7a7820e0489` | Other campaign ownership; retained. |
| rage | `/Users/josh/repos/laputa-systems/rage/.work/wt/llvm` | `46a746fa42c65f0bc6a34432c31b573b14c6c9e2` | Other campaign; retained; Git reports prunable gitdir. |
| fd | `/private/var/folders/h5/z5h1tjvn4hv1h02qfyvjsmg80000gp/T/fd-allgreen` | `1329ff9884992cb65009ce4091523c90765b7d9b` | Outside canonical root; Git reports prunable gitdir; preserved. |
| fd | `/Users/josh/repos/laputa-systems/fd/.work/wt/lint` | `c8811a4cac34b44f30de5e3fecfdab87ebdf46fa` | Other campaign ownership; retained. |
| soulseek-rs | `/Users/josh/repos/soulseek-rs/.work/wt/llvm` | `12ddde2675c748b2f3a926feded3a4a7d555043a` | Other campaign; retained. |

The omitted scoped repositories (`doas-rs`, `rust-fontconfig`, `rustix`, `oxish`, and `crabtables`) had no noncanonical worktrees. Worktree inventory showed no `locked` entries. Every target outside `/Users/josh/repos` is preserved, including paths Git marked prunable. The user explicitly requires preserving the Srv #47 tree, Vault #30 and parked candidates, and evidence; these were not retirement candidates.

## Candidate check and scratch decision

The only remaining registered scoped worktree specifically tied to a completed campaign PR record was mdevd-rs `fix/stuf89-help`. `docs/campaigns/stuf89-cleanup.md` records the general retirement of completed STUF-89 lanes but has no mdevd-rs retirement row (`docs/campaigns/stuf89-cleanup.md:8-33`); `docs/campaigns/stuf89-help.md:69` identifies mdevd-rs PR #4. Its worktree was clean (`git status --short --branch` printed only `## fix/stuf89-help`), and `lsof -nP +D /Users/josh/repos/laputa-systems/mdevd-rs/.work/wt/stuf89` exited 1 with no open files. Canonical `refs/remotes/origin/HEAD` and `refs/remotes/origin/main` both resolved to `2fcc0c608c0999d248c83e2eba841d53be8aeb85`. The lane HEAD was `e0bb29461995b789fe8fe4f9962bf141b3bd6a72`; `git merge-base --is-ancestor fix/stuf89-help refs/remotes/origin/main` exited 1, and `git cherry refs/remotes/origin/main fix/stuf89-help` exited 0 with three `+` commits (`ceff0b8b27e70fc69255ea9a2babb7d38c9f691b`, `73283f21e4e786c10828006a2856e0ecdc33a7eb`, `e0bb29461995b789fe8fe4f9962bf141b3bd6a72`).

The required dry-run command, `worktree-retire /Users/josh/repos/laputa-systems/mdevd-rs/.work/wt/stuf89 --into 2fcc0c608c0999d248c83e2eba841d53be8aeb85 --dry-run`, exited 0 and printed `kept ...: review ignored files, then pass --discard-ignored: .work/, target/`. It did not approve retirement. The positive cherry entries independently establish unintegrated commits, so this tree and its ignored contents remain.

No root `.work/tmp` item met the evidence bar for deletion. Largest inspected roots were Vault `.work/tmp` at 223424 KiB, including `baseline-target` at 191352 KiB and `baseline` source copy; smolith `.work/tmp` at 1446444 KiB, mainly `protocol-target`; and fd `.work/tmp` at 6488 KiB. Their exact task ownership, lack of consumers, or supersession could not be established from the available campaign records, so they are retained. Srv `.work/tmp/mm-eval` (104 KiB total), Vault's age/APK and temporary directories, and the remaining small/empty scratch paths are also retained as ambiguous or potentially useful evidence. No `rm`, `git clean`, cache purge, worktree retirement, or source edit ran. No scratch path was cleared, so `test ! -e EXACT_PATH` was not applicable.

## Exact proof record

Commands and decisive results:

- `git worktree list --porcelain` for each of the 15 scoped checkouts — exit 0; all paths and HEADs are tabulated above.
- Checkout roots: `/usr/bin/git -C "$path" rev-parse --show-toplevel`, `rev-parse HEAD`, and `status --short` in the scoped loop — exit 0; each top-level path matched the physical path above and status output was empty.
- Scratch sizing: `/usr/bin/du -sk "$path/.work"` and `/usr/bin/du -sk "$path/.work/tmp"` where present — exit 0; KiB values above.
- `git -C /Users/josh/repos/laputa-systems/mdevd-rs/.work/wt/stuf89 status --short --branch` — exit 0; branch-only output, clean.
- `git -C /Users/josh/repos/laputa-systems/mdevd-rs rev-parse refs/remotes/origin/HEAD` and `rev-parse refs/remotes/origin/main` — exit 0; both `2fcc0c608c0999d248c83e2eba841d53be8aeb85`.
- `git -C /Users/josh/repos/laputa-systems/mdevd-rs merge-base --is-ancestor fix/stuf89-help refs/remotes/origin/main` — exit 1; not integrated.
- `git -C /Users/josh/repos/laputa-systems/mdevd-rs cherry refs/remotes/origin/main fix/stuf89-help` — exit 0; three positive entries listed above.
- `lsof -nP +D /Users/josh/repos/laputa-systems/mdevd-rs/.work/wt/stuf89` — exit 1, empty output (no open files).
- `worktree-retire /Users/josh/repos/laputa-systems/mdevd-rs/.work/wt/stuf89 --into 2fcc0c608c0999d248c83e2eba841d53be8aeb85 --dry-run` — exit 0; kept pending ignored-file review, with unintegrated commits independently confirmed.
- `df -k /Users/josh/repos` before inventory: 1,589,142,592 KiB used, 318,635,064 KiB available. After the read-only inventory and receipt write: 1,589,262,536 KiB used, 318,515,120 KiB available. No allocated KiB were reclaimed by this task; filesystem usage drifted during the read-only inventory and receipt write.
- `test -e docs/campaigns/deslop-cleanup-systems.md` before writing — exit 1; receipt did not exist.
- Assigned worktree remained `7d7b81df26b69624ff16fb5a83d20f9c1d7fd962`; `git status --short --branch` showed only `## chore/deslop-cleanup-systems...main [behind 2]` before this receipt edit.

Campaign evidence: Srv #47 remains under qualification at `docs/campaigns/deslop-roadmap.md:75` and `docs/campaigns/deslop-scorecard.md:17`; Vault #30 remains active with exhausted mutation shards at `docs/campaigns/deslop-status-20261117.md:195-206` and `docs/campaigns/deslop-scorecard.md:22`. The roadmap identifies parked checkpoints at `docs/campaigns/deslop-roadmap.md:381-397`. Vault's active resumed worktree is recorded at `docs/campaigns/d-overlap-preservation.md:106-114`, and the source overlap inventory identifies preserved Vault drafts and evidence at `docs/campaigns/d-overlap-inventory.md:51-53`.

Unverified: no scratch directory was cleared; there is no cleared-path absence proof. Root `.work/tmp` consumers and exact ownership remain unverified as stated above. Parent owns any later worktree retirement after independent review.

ACCEPTANCE: met
