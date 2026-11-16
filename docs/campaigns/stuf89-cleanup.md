# STUF-89 worktree retirement

Retired the 24 exact campaign worktrees below after their source landed. Each was
clean, unlocked, integrated into the fetched default branch, and had no open files
reported by `lsof`. The parent independently checked the post-retirement Git
inventories. Canonical checkouts and unlisted worktrees remain in place.

| Exact target | Lane head | `origin/HEAD` ref | Integration head | Verdict |
| --- | --- | --- | --- | --- |
| `/Users/josh/repos/loc/.work/wt/stuf89` | `869409dc448eff7ab5f40ef34d3ecb59ae4d271b` | `refs/remotes/origin/master` | `869409dc448eff7ab5f40ef34d3ecb59ae4d271b` | Removed |
| `/Users/josh/repos/laputa-systems/fastermod/.work/wt/stuf89` | `fda1e8fa0d1be5c8933f319d749c211b0c5f5fec` | `refs/remotes/origin/main` | `fda1e8fa0d1be5c8933f319d749c211b0c5f5fec` | Removed |
| `/Users/josh/repos/defuddle-rs/.work/wt/stuf89` | `0c84fcf21709cb9894b569efccbf79c068da243b` | `refs/remotes/origin/master` | `63a23ca89d409d2e211991d5bd8ebfc1dc349716` | Removed |
| `/Users/josh/repos/laputa-systems/diff-pretty/.work/wt/stuf89` | `3070f951146329f6e89978c8bb5993aeaf9d0879` | `refs/remotes/origin/main` | `6ba0962f002cd0f03ad50ede43216bf581a8c228` | Removed |
| `/Users/josh/repos/laputa-systems/fd/.work/wt/stuf89` | `e44d46befd8a8f1375166a0f29e0f7aa2242882a` | `refs/remotes/origin/master` | `59e6e0233b95fc9fff271c538fe37f7a98df59bf` | Removed |
| `/Users/josh/repos/laputa-systems/rg/.work/wt/stuf89` | `5541f9ed3c079681140469f82498724ac3caf4a1` | `refs/remotes/origin/master` | `d155401a04ac4f0af42482ae855427175b6da7d9` | Removed |
| `/Users/josh/repos/laputa-systems/vault/.work/wt/stuf89` | `065a3e5484b0d219e591ddcfa4d8a1940a356097` | `refs/remotes/origin/main` | `e028e29b984fe50acede18a4a2f3072e9502c96c` | Removed |
| `/Users/josh/repos/laputa-systems/e/.work/wt/stuf89` | `84ff72a1df1d1374fcdbbbd5a894cb531933fe38` | `refs/remotes/origin/main` | `b29c90178b664e12d3c4f7f0f4f49772aee21c33` | Removed |
| `/Users/josh/repos/laputa-systems/doas-rs/.work/wt/stuf89` | `f25416ee2fb0610060f75c2b020bee00ee8c7aea` | `refs/remotes/origin/main` | `ca4a12f8e554f8833e3de8d1b660ab1e5eadc1db` | Removed |
| `/Users/josh/repos/ish/.work/wt/stuf89` | `3fc3b9c7025c673561b2fde3c89497e48336ea69` | `refs/remotes/origin/master` | `fc62468e2428f9aea6fcd611b0820ab709ce0c65` | Removed |
| `/Users/josh/repos/mactop/.work/wt/stuf89` | `82364fb315167972235757a4a6317a2bca437073` | `refs/remotes/origin/master` | `264219f1148f4d6e22c4b89a14c2f47612655cc9` | Removed |
| `/Users/josh/repos/stats/.work/wt/stuf89` | `e5424d36eda0c5369613a0fa12a842971485c4c2` | `refs/remotes/origin/master` | `b9a451a58810e19fdd761df9c5a76060f5004b5f` | Removed |
| `/Users/josh/repos/lz/.work/wt/stuf89` | `b2f83606ec96ac1c8283e99278adeae0c5580d5c` | `refs/remotes/origin/master` | `722d74c4f24eaf7263da75a884d5a0017e4613be` | Removed |
| `/Users/josh/repos/bctl/.work/wt/stuf89` | `e60cf923790fc1879ff531926d54630cdff3b74b` | `refs/remotes/origin/main` | `12de4dff3f50ddde8e453bcfdc0a383ecc552c9a` | Removed |
| `/Users/josh/repos/soulseek-rs/.work/wt/stuf89` | `a73e2260c6bbb60bf202905df64588bec6db7a72` | `refs/remotes/origin/main` | `bf581b412f7e0229d7257de1c0e868f64813db94` | Removed |
| `/Users/josh/repos/laputa-systems/zzz/.work/wt/stuf89` | `f959c5cde330f299e8b434cd93f11ddfe96ba7f5` | `refs/remotes/origin/master` | `f28d1287992ff511c7cdd1e7d4265b3ed0dd9197` | Removed |
| `/Users/josh/repos/laputa-systems/git-build/.work/wt/stuf89` | `72e33cba8a046f681510cd43d9d627de1ab37758` | `refs/remotes/origin/master` | `0f1f948234bcb8ddc94f7be5246dcb71448baa06` | Removed |
| `/Users/josh/repos/gh/.work/wt/stuf89` | `aaa56905b5163fec49004071aec84a5e5837d018` | `refs/remotes/origin/trunk` | `1b0f45bc119007fb4b2a1a66ded29e7a3cb30707` | Removed |
| `/Users/josh/repos/syncthing/.work/wt/stuf89` | `ddfc543ffba0b696172876fee35a30c9033b1d37` | `refs/remotes/origin/main` | `5997118eeacdb422fdcada7834323600cf609e79` | Removed |
| `/Users/josh/repos/laputa-systems/srv/.work/wt/stuf89` | `71f1cbb2f84d8c6f3e5ba1cde4d7818148147eb6` | `refs/remotes/origin/main` | `746b6925b19da0275cf3fb25282d207c5eb8ccae` | Removed |
| `/Users/josh/repos/laputa-systems/jaq/.work/wt/stuf89` | `61730957fb1435296e48c3d76def0f856bc4d218` | `refs/remotes/origin/main` | `ac261459a1e70af07d7495f0d14af4806e665c22` | Removed |
| `/Users/josh/repos/pi-build/.work/wt/stuf89` | `e6df48e5df5bfedf504565b7fc230f9c4aa6e8a2` | `refs/remotes/origin/main` | `442f463954a6ead8fb9223f8c148bcc4c1bc66cf` | Removed |
| `/Users/josh/repos/laputa-systems/rage/.work/wt/stuf89` | `0950fee3c4c6b6d56fa1bb609ca7638219ffbe86` | `refs/remotes/origin/main` | `1c342bcd893a92a5fd6671794aa2865e9fae6aa7` | Removed |
| `/Users/josh/repos/laputa-systems/ffmpeg-build/.work/wt/stuf89` | `c76e11d2a1d35f22f32840ee4e3486c7b23b9af7` | `refs/remotes/origin/main` | `539141d40ffecd42c1eada9abaea1475927a7cf0` | Removed |

Retirement used `worktree-retire PATH --into INTEGRATION_HEAD --dry-run`, then
`--discard-ignored` after reviewing the listed lane build outputs. Every retired
path is absent and unregistered. The cleanup integration checkout began at stuff
`4ff693599154dbc1834b856c947b0948f8737af3`; source integration heads are listed above.

The worker initially retained Syncthing's generated `lib/api/auto/gui.files.go`.
The parent confirmed that `go generate ./lib/api/auto/` recreates it from tracked
inputs and retired that worktree too. Its merged source and tests are preserved.

The 24 worktrees occupied 13,971,896 KiB before retirement; none remain. Only
these exact worktree paths were reclaimed. No active build, parked branch,
uncommitted user work, or unrelated scratch was removed. One Git fetch
auto-followed git-build's existing release tag; it was left in place.

Worktrees for open PRs and unfinished verification remain until their gates pass.

## Six additional merged lanes

This bounded pass used cleanup worktree head `2341c5f01601dd25649a7393d47640bae1048c71`.
The coordinator reported all six PRs merged. For each exact lane, I confirmed the requested
HEAD, clean tracked/untracked status, fetched the remote default branch with `git fetch
--no-tags origin <default-ref>`, and verified the lane HEAD is an ancestor of the fetched
default-branch commit. `lsof -nP +D <exact-path>` returned no open files for each path
(exit 1, empty output). No lane had a live consumer in that scan.

| Exact target | PR | Lane HEAD | Fetched default ref | Integration SHA | Verdict | Outcome; ignored data and disk use |
| --- | ---: | --- | --- | --- | --- | --- |
| `/Users/josh/repos/laputa-systems/tinyland/.work/wt/stuf89` | 4 | `8556f7fd30369b05721f72eaec16b7c61d631f0b` | `refs/heads/main` | `8a4eb0a82bab6da1149da61d124b64283f7578fe` | Ancestor; clean | Removed; ignored Kache cache under `.work/tmp` (1.6 GiB), `target` (238 MiB), and `seatd/.work/tmp`; 1,894,164 KiB before, absent after. |
| `/Users/josh/repos/tansu/.work/wt/stuf89` | 29 | `e198c6c8364c0472df5d09f0389f5e047e3e53dc` | `refs/heads/master` | `1bf0a0dd9cd76e505ff6a607b01fd5319b34e421` | Ancestor; clean | Removed; ignored `.work/tmp`, Cargo `target`, generated `web/dist`; 682,144 KiB before, absent after. |
| `/Users/josh/repos/play/.work/wt/stuf89` | 14 | `db63a78fbd0c8954ec2084e9be84ca69f795d7d7` | `refs/heads/main` | `bae10f91b7003e208964eab030ba024d9b6c1a49` | Ancestor; clean | Removed after parent review of downloaded `.work/tools`, `.work/deps` and generated `target`; 548,044 KiB before, absent after. |
| `/Users/josh/repos/laputa-systems/cmake-build/.work/wt/stuf89` | 6 | `039cbb6d4a817db6323274408cd015561c30d231` | `refs/heads/main` | `538efea3512ccfd98839f2ce8aff83107c47383c` | Ancestor; clean | Removed after parent review of extracted `.work/source`, `.venv`, cache and host build output; 709,424 KiB before, absent after. |
| `/Users/josh/repos/laputa-systems/ssh-build/.work/wt/stuf89` | 17 | `07b57b036a508cda4dc969bf54214e28872646bf` | `refs/heads/master` | `ac7fc2db66e86ff34f3d5480a83dbfb1ab11b9fd` | Ancestor; clean | Removed after parent review of generated sources, build output and patch-editing copies; 615,588 KiB before, absent after. |
| `/Users/josh/repos/laputa-systems/gluon/.work/wt/stuf89` | 16 | `9837ca67245282bbd2f31865826f366f6b26bd13` | `refs/heads/main` | `ff0d5c60ffea6d361b3152a1115539207e4ec5ef` | Ancestor; clean | Removed; ignored `.work/tmp` and Cargo `target` build output; 643,624 KiB before, absent after. |

For tinyland, tansu, and gluon, `worktree-retire <exact-path> --into <integration-SHA>
--discard-ignored --dry-run` exited 0 and reported the lane as an ancestor; the matching
non-dry-run command exited 0, removed the exact checkout, and deleted its now-unchecked-out
`fix/stuf89-help` branch. Their ignored files were inspected as local cache, scratch, or
generated build outputs before discard. The helper initially requested ignored-file
review for Play, cmake-build and ssh-build. The parent confirmed the first two held
task-local downloaded inputs and generated outputs. SSH's reverse-patch dry run
accepted the tracked OpenSSH footer patch against its editing copy; its OxiSH
editing copies differ from the committed binaries' source only by the captured
footer changes, and both vendor-check diff files were empty. These three exact
retirement commands then exited 0 with `--discard-ignored`, removing the worktrees
and their integrated branches. The parent repeated clean-status and open-file checks
before retirement.

Post-checks ran `git worktree list --porcelain` filtered for each exact path and an exact
filesystem existence check: all six exact paths were unregistered and absent.
Before cleanup the six checkouts occupied 5,092,988 KiB total; afterward they occupied
0 KiB. No other worktree, canonical checkout or scratch path was removed. No
integration or consumer case remains unresolved for these six lanes.
