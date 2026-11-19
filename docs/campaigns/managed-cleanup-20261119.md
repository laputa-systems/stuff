# Managed checkout cleanup, 2026-11-19

This pass retired 72 completed worktrees in seven repositories under
`~/repos`. The removed paths accounted for 18,861,808 KiB (17.99 GiB)
of measured allocation. The data volume reported 211,667,108 KiB
available before the pass and 218,259,456 KiB (208 GiB) at the final
check. Volume availability also reflects concurrent activity.
[Previous cleanup](managed-cleanup-20261118.md)

| Repository | Worktrees retired | Path allocation, KiB |
| --- | ---: | ---: |
| chromium-build | 2 | 1519904 |
| cmake-build | 31 | 8574996 |
| defuddle-rs | 9 | 6260012 |
| ffmpeg-build | 4 | 80824 |
| gluon | 16 | 652316 |
| node-build | 6 | 1060384 |
| rustybench | 4 | 713372 |

The mechanic inventoried recent merged lanes and independently
cross-checked the CMake and other recent merges. For each retirement,
the coordinator reviewed the ignored build outputs, fixtures and
logs, checked user open-file and working-directory handles with
`lsof -Fn -u "$(id -un)"`, and required
`worktree-retire <path> --into <accepted-default> --dry-run --discard-ignored`
to report ancestry or patch equivalence. The actual retirement used
the same arguments without `--dry-run`. A final check confirmed that
every path was absent both on disk and in the owning repository's
`git worktree list --porcelain`.

## Retained work

- Chromium-build's `macos-helium` had open handles in its source and
  release output. Its test-entry worktree had an unmatched change.
  Helium and Headless Chromium's offline APK worktrees were retired
  before the owner excluded Chromium-build. Further campaign cleanup
  there ended with that decision.
- Gluon's dry-run candidate, review and macOS parity worktrees contain
  or serve active verification. The archive-symbols checkout has a
  patch the tool could not match to its integration revision.
- CMake's benchmark median worktree, Node's inspector deadline worktree,
  and several Defuddle and FFmpeg worktrees hold unmatched changes.
  The Defuddle publication-date worktree had local changes.
- Canonical checkouts, Discover, Stats recovery, parked Python-build
  proof and the Ctrs performance work were kept.

## Verified retirements

Paths are relative to each repository's `.work/wt/`. The repository
roots are `~/repos/laputa-systems`, with Defuddle-rs in `~/repos` directly.

| Repository | Worktree | Retired revision | Accepted default | Path allocation, KiB |
| --- | --- | --- | --- | ---: |
| chromium-build | `headless-offline-apk` | `a2d86c044b6829f3c9de1b0a831488aa491842f7` | `1b58c7f81d9a299bab65f79750936525bda14fbc` | 582328 |
| chromium-build | `helium-offline-apk` | `05573b3187ee2af9d2a9a61cb555846a9c0ac4de` | `1b58c7f81d9a299bab65f79750936525bda14fbc` | 937576 |
| cmake-build | `cmake-accounting-lifecycle` | `79cc45cb04eb98f49fbfb543577108e7850d0eed` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 330096 |
| cmake-build | `cmake-archive-write-boundaries` | `e17faf52b3e405511439c596bd51d37f37dd7789` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 86556 |
| cmake-build | `cmake-benchmark-accounting` | `1eca7a14428f71ba7c055cea56e211ac42a49882` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 329896 |
| cmake-build | `cmake-benchmark-admission` | `36a0e00ab37fabc1c7f6acaec931506e1a808c89` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 305504 |
| cmake-build | `cmake-benchmark-boundaries` | `328f52e024912bc7dca77d3c3347234521669c11` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 193900 |
| cmake-build | `cmake-benchmark-evidence` | `6c46766c86eda00fc56b708a12296ac339e079ab` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 193624 |
| cmake-build | `cmake-benchmark-execution` | `47e1c95c718545c08c5e1defbd28ac770c741141` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 305716 |
| cmake-build | `cmake-benchmark-phase-handoffs` | `0cfbf70b0581a8376391313c71ae6e53d964762a` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 194248 |
| cmake-build | `cmake-benchmark-provenance` | `44d3bf518433b0811de2273390b7cf91c01fbbba` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 194212 |
| cmake-build | `cmake-benchmark-publication-contract` | `ca4a50bc8694af57b3ce518663a86e77f11b0e0f` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 194224 |
| cmake-build | `cmake-benchmark-report-schema` | `c908fb60772c78fae4b841da2b584b69cbbda529` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 194000 |
| cmake-build | `cmake-benchmark-report` | `50f855ba4215517d6c106c9dbfbb8a3b9bfcf980` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 528824 |
| cmake-build | `cmake-benchmark-samples` | `944102610fffa4c27a11cee86454c876ab8b4f51` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 194008 |
| cmake-build | `cmake-budget-numeric-boundaries` | `454306088e6efbdfdd495d22458941d467e53dba` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 86332 |
| cmake-build | `cmake-container-execution-contract` | `70cab6467e52844ca028c5e20b11db91e9b2d307` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 96256 |
| cmake-build | `cmake-controller-cli` | `1a6ba3d06310ae99c0b26088ace820fe78940e60` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 920328 |
| cmake-build | `cmake-dependency-inventory` | `c1b2b582992ffb5a716fc38e03edb66d43e08a70` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 415632 |
| cmake-build | `cmake-distribution-fixture` | `284813b2dd5aee6d2529b1561f2c4f1c4e7e7543` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 246344 |
| cmake-build | `cmake-elf-link-evidence` | `f95344c4042bea5a21ff84ec68151b185b301184` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 251592 |
| cmake-build | `cmake-elf-report-evidence` | `6aade9cff3daef94d21c5c2a08def80224a6c320` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 251652 |
| cmake-build | `cmake-fetch-doctor` | `9492641931bcfca917113d390b43a7738db1cdc9` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 288984 |
| cmake-build | `cmake-inner-phases` | `c8618157207d52f87f0fe09d782e6c62afdf10b7` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 289096 |
| cmake-build | `cmake-inner-prepare` | `912f433b7cf75e48d65ab1702c0596461dc80fe7` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 289060 |
| cmake-build | `cmake-parity-qualification` | `1635e48d1b85942150fc79be27ecb1e67b776d6d` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 352516 |
| cmake-build | `cmake-patch-admission` | `2a1338177d008aa1872429084e8afd77e1eed3bf` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 163948 |
| cmake-build | `cmake-patch-inventory` | `5be15e930d7bc0e1ca49eb7fa9dad7cc6597e569` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 329200 |
| cmake-build | `cmake-phase-commands` | `ce5ce422738e36f926f8e863ea784247d62f48e5` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 391688 |
| cmake-build | `cmake-release-admission` | `7abe2e431344ef7a2a5c14d98cb831bec4e4fb5e` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 391640 |
| cmake-build | `cmake-release-command-dispatch` | `147d6ee342a71ff35aa8a652bd58747371970380` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 391696 |
| cmake-build | `cmake-restore-cache-before-host-tests` | `1649d94468dee18133613b46010d6d305875f407` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 2668 |
| cmake-build | `cmake-upstream-proof-digest` | `fb945cafc993a8b91dc5969e4eb0de9c8c19f142` | `6f938dfd2d1e705dd4b74c734d3783008675c61a` | 171556 |
| defuddle-rs | `defuddle-archive-detection` | `57fb65ff56dea6bb336dd20433c1e7a408517814` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 405524 |
| defuddle-rs | `defuddle-archive-fallback` | `06729deed0cd5f63109029190c13939850ce4a99` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 405328 |
| defuddle-rs | `defuddle-archive-redirect` | `b3e10d69f7a5a583a94ce02fe57fafa77503c450` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 1174896 |
| defuddle-rs | `defuddle-document-origin` | `02eceb64fe66d072114574e1e4f136785534276f` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 373532 |
| defuddle-rs | `defuddle-hosted-wasm` | `080b6183d36e3ce9a147997180a5060e7ab04db7` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 608408 |
| defuddle-rs | `defuddle-wasm-options` | `0dfbcbc9e5d464b0856055ae42e2c83151d17950` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 819572 |
| defuddle-rs | `defuddle-wasm-runtime-evidence` | `d74689795baa924eaa46a2315b993f3dcdb7fa97` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 17912 |
| defuddle-rs | `deslop-defuddle-ground` | `fdde0b19726eadcbff6f390ab1e6234951dbdb7f` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 1512840 |
| defuddle-rs | `deslop-defuddle-tests` | `b546bc1152644d6c06ab3bb434741c85d26b2deb` | `207a73e29c8ad89b5dcb9bd01caa37936be1ba19` | 942000 |
| ffmpeg-build | `ffmpeg-deslop-review` | `5121bc9de72e90418256f5575ed04d8b9cd5bbb1` | `b9d9ce52ddc4cf171cc1f5aa707c8f1df6186474` | 788 |
| ffmpeg-build | `ffmpeg-deslop-timing-baseline` | `189a0831fc8ef329289699758eab07730c4b7529` | `b9d9ce52ddc4cf171cc1f5aa707c8f1df6186474` | 78884 |
| ffmpeg-build | `ffmpeg-retention-rule-control` | `79b21eeda95bc896b24b5205fee465c3713a5f38` | `b9d9ce52ddc4cf171cc1f5aa707c8f1df6186474` | 744 |
| ffmpeg-build | `retention-proof` | `bde17f54c2d1b1f8b2ff502614c25634f0c87ed7` | `b9d9ce52ddc4cf171cc1f5aa707c8f1df6186474` | 408 |
| gluon | `deslop-gluon-ground` | `dbdfa75dfcbc83638248bbcbb243bad74a0be123` | `2785395a14d8159a964db8943fbb578b162c4af3` | 95588 |
| gluon | `gluon-clean-dyndep-producers` | `e88f19e1acc3493a875be5f0a207d9ab6cd56dd0` | `2785395a14d8159a964db8943fbb578b162c4af3` | 24244 |
| gluon | `gluon-close-macos-parity` | `a84de1a6163dfaa3c99cb13b14a6a1d29ea385d8` | `2785395a14d8159a964db8943fbb578b162c4af3` | 2364 |
| gluon | `gluon-declared-input-freshness` | `193a4348c49dacd733680f070908c3e288600a2c` | `2785395a14d8159a964db8943fbb578b162c4af3` | 133952 |
| gluon | `gluon-declared-inputs-review` | `86635354b84c1bb15f0206735f8e4b9a6489217c` | `2785395a14d8159a964db8943fbb578b162c4af3` | 2384 |
| gluon | `gluon-expected-fixture-results` | `07ed5f5ea797adc4fec6c69a2edd207172c998e6` | `2785395a14d8159a964db8943fbb578b162c4af3` | 35036 |
| gluon | `gluon-generator-fixture` | `13de763a28aaa88ce62eb9fad8bd7e0c39ffce44` | `2785395a14d8159a964db8943fbb578b162c4af3` | 28840 |
| gluon | `gluon-input-freshness-review` | `f883c86b3961b8f8e2b5866392e17c91f93b3aec` | `2785395a14d8159a964db8943fbb578b162c4af3` | 2416 |
| gluon | `gluon-llvm-config-fixture` | `fb6e1212fa320014f2bf05e0b2ccbdc1de35d482` | `2785395a14d8159a964db8943fbb578b162c4af3` | 29300 |
| gluon | `gluon-missing-ninja-input` | `6ba88da22019ef95a3bca5518d4db4cdc1d8ae5d` | `2785395a14d8159a964db8943fbb578b162c4af3` | 2384 |
| gluon | `gluon-ninja-observables` | `5b244a9b577187aa1b74328dae0a84409b709397` | `2785395a14d8159a964db8943fbb578b162c4af3` | 106480 |
| gluon | `gluon-oracle-preflight` | `597ef38ef16343442ffa6ff37fb51563b9b4d32f` | `2785395a14d8159a964db8943fbb578b162c4af3` | 28864 |
| gluon | `gluon-stale-dyndep-review` | `2700916ffdcd8bf455e3f6be2c1f66709bd4e989` | `2785395a14d8159a964db8943fbb578b162c4af3` | 2440 |
| gluon | `gluon-stale-dyndep` | `78a2ad837b4078ce1ee9652ec1f0598bc97b9f5a` | `2785395a14d8159a964db8943fbb578b162c4af3` | 40444 |
| gluon | `gluon-subninja-fixture` | `853fb40e4a700b0886dfa8f665bb5263b71ee965` | `2785395a14d8159a964db8943fbb578b162c4af3` | 2444 |
| gluon | `gluon-validate-declared-inputs` | `507d2678008f77c8c6d78b64db6087cd68d6d892` | `2785395a14d8159a964db8943fbb578b162c4af3` | 115136 |
| node-build | `node-fs-smoke-bytes` | `d8e30dd43a4551c5680c14ab904cde334194a0f9` | `57e8d65f3b9230b4022b47c93dce0895640f11ff` | 162380 |
| node-build | `node-https-fixture-paths` | `8cefb7dc833f956e27ee2bec16fb21240fe5d7a7` | `57e8d65f3b9230b4022b47c93dce0895640f11ff` | 162692 |
| node-build | `node-inline-smoke-boundaries` | `7322fc0be191d2347ee69527d2fa5394ed9c6210` | `57e8d65f3b9230b4022b47c93dce0895640f11ff` | 162784 |
| node-build | `node-inspector-list` | `4fda98642cba49ff72667c9881597c2fae607364` | `57e8d65f3b9230b4022b47c93dce0895640f11ff` | 79732 |
| node-build | `node-smoke-exclusions` | `897fd72761fab9dd720b9feeb529e0f87e5aa8db` | `57e8d65f3b9230b4022b47c93dce0895640f11ff` | 247684 |
| node-build | `node-smoke-runner-contract` | `96334b34d6f391f19213f3624525167e1bfb9fce` | `57e8d65f3b9230b4022b47c93dce0895640f11ff` | 245112 |
| rustybench | `deslop-rustybench-ground` | `73b3d5400cbd62deb17a638be694dba036c718ab` | `6f5e939055cc6715895cd61980ca905528b533c1` | 248888 |
| rustybench | `rustybench-diagnose-diff` | `c49c52ad05b2027a0701153a2dd13dc230c49fb4` | `6f5e939055cc6715895cd61980ca905528b533c1` | 89156 |
| rustybench | `rustybench-duplicate-comparisons` | `c95b538b75bf52254c00975e367769596dd68626` | `6f5e939055cc6715895cd61980ca905528b533c1` | 112376 |
| rustybench | `rustybench-static-runner-fixture` | `d1f5cc01a135438e22b079cba11007f902772370` | `6f5e939055cc6715895cd61980ca905528b533c1` | 262952 |
