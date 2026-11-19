# Managed checkout cleanup, 2026-11-18

The cleanup retired 90 completed worktrees under `~/repos`.
They accounted for 12,524,744 KiB (11.94 GiB) of path allocation
before removal. The older cleanup has its own receipt.
[Earlier cleanup](deslop-cleanup-20261117.md)

| Repository | Worktrees retired | Path allocation, KiB |
| --- | ---: | ---: |
| FFmpeg-build | 33 | 6,263,420 |
| CMake-build | 30 | 3,772,980 |
| Node-build | 21 | 1,947,524 |
| Lz | 1 | 159,516 |
| Tinyland | 1 | 1,176 |
| Laputa UI Dashboard | 1 | 2,168 |
| E | 1 | 76,236 |
| Gluon | 1 | 60,688 |
| Rustybench | 1 | 241,036 |

The mechanic inventoried worktree registrations for 65 local Git
roots under `~/repos` and investigated the parked Python-build proof.
The integration pass started from Stuff revision
`efe0e21f02416eeea906933116d4d7b53484d88f`. It matched current
worktree heads to merged pull requests, checked accepted revisions
against the owning default, and reviewed ignored outputs. Each
retirement passed `worktree-retire --dry-run` and then
`worktree-retire --discard-ignored`. Git reported no remaining
registration, and the checkout path was gone. An open-file check
preceded each batch.

Volume availability was 53,811,424 KiB before the first batch and
278,645,896 KiB after the last. Availability changed substantially
between batches. The allocation count measures the removed paths.
It does not attribute the full volume change to this cleanup.

## Retained work

- Chromium's `macos-helium` worktree accounted for 72,711,748 KiB.
  The kache engine still held a working directory in its native output.
- Python-build's `jit-reference-init` worktree accounted for
  7,774,668 KiB and had two commits outside the checked default.
  Its campaign record parks the candidate with qualification pending.
  [Python-build qualification record](https://github.com/laputa-systems/python-build/blob/b1d8240f7d56d778b408a38c2f96ed47eef55f69/docs/CAMPAIGN-RUST-CPYTHON-JIT.md#L4069)
- The builder pass retained 24 checkouts that the retirement tool
  could not prove integrated and six Node checkouts with unclassified
  ignored `build/` data. The open mutation drafts and their consumers
  stayed in place.
- Discover remained outside the inventory. Canonical checkouts, the
  Stats registry recovery, Ctrs retained performance work, and
  other active, locked, dirty, parked or unclear paths were preserved.

## Verified retirements

The path column is relative to the named repository's `.work/wt/`.
The accepted revision is the commit supplied to the retirement tool.

| Repository | Worktree | Previous HEAD | Accepted revision | Allocation, KiB |
| --- | --- | --- | --- | ---: |
| ffmpeg-build | `ffmpeg-deslop-checkup` | `063efbbc94906072242539b06a0580c8755cfea6` | `b9d9ce52ddc4cf171cc1f5aa707c8f1df6186474` | 764 |
| cmake-build | `cmake-basic-qualification` | `64f4171e7fa28e656702c019aaf37ba91fc83778` | `0a28b62ff8d3d247e09dd43e2522a9cc1ee89be3` | 261668 |
| cmake-build | `cmake-network-qualification` | `299de277a96d70097736fda5b87097e49cf84ea0` | `0a28b62ff8d3d247e09dd43e2522a9cc1ee89be3` | 262444 |
| cmake-build | `cmake-project-qualification` | `84373cfed7e7f0cf0f0450a16dda3fd9249846bc` | `0a28b62ff8d3d247e09dd43e2522a9cc1ee89be3` | 261816 |
| node-build | `node-worker-child-exec-path` | `c1d9935677103351ac7efc292467d62b49417dc6` | `d03cff8284271984c9e1664c5e8569a225afd77a` | 244880 |
| ffmpeg-build | `ffmpeg-deslop-dead-code` | `5121bc9de72e90418256f5575ed04d8b9cd5bbb1` | `55c83410f860abd5bdf766f73fbb740d21d1a451` | 247428 |
| ffmpeg-build | `ffmpeg-close-deslop-tests` | `fad9b64e31aa06c831ec914913b8307ef2cce433` | `eeafc0f2b2856c1631c52f3b77fd216ddaf543ff` | 752 |
| ffmpeg-build | `ffmpeg-stage-audit-policy` | `60509f347c13442a23c5010d30a088905424651f` | `ee96626068010e0e722c81f0f81119883fd2b153` | 303092 |
| ffmpeg-build | `ffmpeg-stage-synthesis` | `a4242b25726a9897fba7e7378088966a6786aed1` | `32a0e84ac7cc44f35dcf692923e3357a86149fcb` | 303036 |
| ffmpeg-build | `ffmpeg-configure-contract` | `d2defbf5f6d50bde2338ab4fa9cb047c59ae43fb` | `29a4cbd21b0cd73f8a3fec8d7a9e15b71a4b999d` | 414212 |
| ffmpeg-build | `ffmpeg-toolchain-inputs` | `17eadb93c260c52ce4eea5f5ec3daf3f7aca3b3a` | `44e2a2e5c08060a96bfb80a8177d83325253586f` | 191548 |
| ffmpeg-build | `ffmpeg-runtime-filesystem` | `a9cf7bd06a6014da6720c0d8a320292abe79174e` | `068e30ae714ab1b2f0abe566c1a33123f24bddb8` | 525272 |
| ffmpeg-build | `ffmpeg-profile-locale-control` | `0bcc4e3b17e4763cea42cc42656e5622c44fd815` | `23ceb7827cad8e0c1e1e85362018f9b41cf6e45c` | 80128 |
| ffmpeg-build | `ffmpeg-profile-object-admission` | `6fb4492f95643f34ab45efd8f8c43ef1b89d2472` | `5693937fc207629cb0cb2259677aafb66d2a6887` | 112224 |
| ffmpeg-build | `ffmpeg-runtime-build-stages` | `88163fd5429a15e8030653ec65589754279bc903` | `7af23b83770a741b19e612ebe8b8d7594a49be26` | 112172 |
| ffmpeg-build | `ffmpeg-build-stamp-admission` | `0b4172f15e2826653433b18ca3f69006175ca09d` | `3d7a1f7fc5d5b5c8423e7ff7c9bb961789c45c7f` | 144092 |
| ffmpeg-build | `ffmpeg-runtime-probe-boundaries` | `002b50f5acac4b5909840629ef140ebbb85a4f35` | `f645211669019b98d738e105609e73520914adf7` | 112112 |
| ffmpeg-build | `ffmpeg-runtime-admission-details` | `f5643977418f31cc171113a009302ab0e49f545b` | `e1eacd96f66cfae92c8ac0bb819c67dbf435e0bf` | 144036 |
| ffmpeg-build | `ffmpeg-sdk-admission-completion` | `9b2e47dd6708d3d558aa9b4a5a114b9a16407d74` | `87f4e54dace8a3a2641f35d82a52be419e6c38ea` | 112064 |
| ffmpeg-build | `ffmpeg-runtime-version-probe` | `6589d8ccbb756752e066005c6569f9101f9d4f03` | `c9bb518f5b77b7df07c34cc74c95965d20ff5ee6` | 112092 |
| ffmpeg-build | `ffmpeg-sdk-pkgconfig-boundaries` | `aeaf5b70f2cf0ba575341354f84ce03e8ca30ace` | `22e4213d22f4db19960ae92d4cd22d22527bf969` | 115148 |
| ffmpeg-build | `ffmpeg-tools-audit-dispositions` | `049fb9aedb1a639b772114123c104525096ab813` | `aa8e0b69f2531eeec48efb7ec1b81a177b9e8f26` | 223436 |
| ffmpeg-build | `ffmpeg-runtime-audit-boundaries` | `9f4a74a16b11edba9148ef36f41f7015ff72c909` | `c65f9e574668c6ce0d11a54da369c92bece4b85e` | 111804 |
| ffmpeg-build | `ffmpeg-tools-audit-boundaries` | `a484620a1f8a713be71e2f5cf9f48c496bcfa1f9` | `c624bd4d88c4ef24a3aef8b74d140c0df5923c6e` | 143376 |
| ffmpeg-build | `ffmpeg-sdk-audit-archive-admission` | `ef9584d7e268270ef7ab3632622d491312f11664` | `986f9dba0ba0657e2dac82168fccc9d1e09038d7` | 190864 |
| ffmpeg-build | `ffmpeg-native-artifact-dispositions` | `5c721e5485878d6d9bdcde911eceb669be5c6e6e` | `7d0fca8921f1eb7541d2ffe33fbcba48fedcb8de` | 524 |
| ffmpeg-build | `ffmpeg-artifact-boundaries` | `dde690f82d6c8011fdea8b0410ea464defa90785` | `4af3726fd408975b45d7ca934a314c3b4f9fdcf6` | 301824 |
| ffmpeg-build | `ffmpeg-audit-artifact-config` | `97e598bbc0a0b9465a573078618283b116a371aa` | `d1dde2cc162e0d06b84356ce587de5af3b177ce0` | 523148 |
| ffmpeg-build | `ffmpeg-audit-stage-contract` | `bfb9ad16b40db1447287dd5efcbdc43371bffc54` | `8f308f3119110f265771fa54fb3997f2448547bb` | 111372 |
| ffmpeg-build | `deslop-audit-build-tree` | `8fe2ab6ed86e968513962eec49c8da8bf68ffc5f` | `0de54ca9a1dbe17f393912ea4774a71363c1c8ce` | 190396 |
| ffmpeg-build | `deslop-whole-change-gate` | `136443aab35f1084568dad1353ba5e65fdddcc85` | `a61e84a129e89bf68172ecc5256b96490fcc1e6a` | 191340 |
| ffmpeg-build | `deslop-runtime-link-audit` | `9e575605312ad0a85fea3a49910986d1679f126d` | `aa4f74741638ef3762a324b2e687b1509b0c62f1` | 141276 |
| ffmpeg-build | `deslop-qualification-profiles` | `85b715af635523a8e5a85faef8db02f361bc2ac3` | `75fb9ffbe015b53c64ab1d29aed413f52ce84be9` | 379568 |
| ffmpeg-build | `deslop-stage-tests` | `b5e9149371b46f03198fa8a8ff7d9dcf0ac8e899` | `4bf7f0661d8b5cb4235b89a02be200b00e2ff87e` | 160828 |
| ffmpeg-build | `deslop-release-tests` | `c2c2f52e1c8fafce5ea9816cefa808c8247af541` | `090ca476608bc3e908e127997de193082d3fde79` | 160304 |
| ffmpeg-build | `deslop-assembly-tests` | `19cd30b6926ce0d53d8507811c7b2fabcd87956e` | `afe69a35fa3b4ec699869ee2be18b4769d533c43` | 161428 |
| ffmpeg-build | `deslop-tests` | `55094b1e1117764b868fc35fedb388f02dd68363` | `bde17f54c2d1b1f8b2ff502614c25634f0c87ed7` | 241760 |
| cmake-build | `cmake-upstream-phase-handoffs` | `39564e34ed2e4ab1c6d20ab52252f2b153a7afa3` | `eb2b833abdb68d25f30a66fab85246c298aff42f` | 171444 |
| cmake-build | `cmake-upstream-report-admission` | `4b60016c32558d3c9ef19225f579d88d1e151f09` | `a501fe368b430f467e05fd6dc31fb73b76e7e297` | 171444 |
| cmake-build | `cmake-network-setup-cleanup` | `47a352ccbe1eb7ad09c130ca3fce9170edae65ed` | `2f308d091b868988063e189b41b186fc8c684a6c` | 81440 |
| cmake-build | `cmake-upstream-report-count` | `739831d1fdea76f1803b488ee9b909b083fa3d89` | `7304cab5efee822ccfc284b429726b4d00af03af` | 93268 |
| cmake-build | `cmake-wheel-cache-boundaries` | `7d5d540f4483fae31f728386b92cbadaa84318ff` | `ddff12df055e6e4c72e483676811700a6cb43836` | 89036 |
| cmake-build | `cmake-repro-tree-boundaries` | `cb554a057f8a0823bb8e80f2182065a6c23cd0de` | `2ac7c9826781f7844bc2b83afdf9c37e6364d2f6` | 86228 |
| cmake-build | `cmake-phase-record-boundaries` | `15cae18b7cf59840e13d3dc6503574c9781e5ad6` | `133c9e702c75773730133b623390eb297bf6b745` | 92276 |
| cmake-build | `cmake-archive-link-admission` | `b5c6b0c9a7e54fc91ccf0cf0031c4fcc566e78eb` | `02143421d9c43687ac4d22bbf9ddc15edbe16879` | 289924 |
| cmake-build | `cmake-nested-extraction` | `0b2d911284d1a08448a857e6ed8342c38d8b1b12` | `55d7401788f02f98f18ff15017983f272d382996` | 165088 |
| cmake-build | `cmake-archive-read-failure` | `085e5f9fbd348db1f4f9a945a7e3400db00f86a5` | `8faba920cd3f884fc3cbefabf086cdcb7dc00906` | 333564 |
| cmake-build | `cmake-tree-digest` | `cb5584f06979d298337986260937aaf7516da0de` | `e5249543218c1adbb00281ab7cd55ff3a61c7868` | 119884 |
| cmake-build | `deslop-cmake-gate-evidence` | `d3c3563e50bf7f0b4b6662cd02cb25bf35aac24f` | `711926b73f2e0719d4292664133a418c1304c563` | 2536 |
| cmake-build | `cmake-deterministic-manifests` | `a2bac3c858e940b55cd27eb3b10bd1494f383e8c` | `a6ac0d1d57a92f30b9fdb4c8b2a61523eda235c6` | 237060 |
| cmake-build | `deslop-cmake-bootstrap-contract` | `c6c19dbfc2ce2ad40da3581a9e1e57b312e922ec` | `e204a301107acd0cd4a067a5c71db462d8aed0c9` | 157280 |
| cmake-build | `deslop-cmake-stable-proof` | `c2541c57ae2ac47f70ca6dd174c47cd6d30f7b63` | `1617378d7062977704002299940e7d9eef081054` | 2524 |
| cmake-build | `deslop-controller-types` | `e6c5b4d9b87723121c2e6beec9ebcf1ca450eb2a` | `a929b2f257be1de1fe452dc6b4abdd0be082f3a5` | 81280 |
| cmake-build | `deslop-artifact-records` | `1ed3bdf8965a4088bab9314b4000ee73455e3969` | `bf94f6ec153f6870c447330d870396493cdff394` | 81304 |
| cmake-build | `deslop-budget-records` | `1f822f80b342dd3149e898c426f88f8c326b4065` | `a8dd64b7623712ec3718a8735b25926ef875a35e` | 80948 |
| cmake-build | `deslop-upstream-result-types` | `aa5d732c5310c82a573131b88b76574b7df315b4` | `745ac5f7fc11c323ed9314f4925dbcaa871aa194` | 81028 |
| cmake-build | `deslop-process-types` | `2dc94720a029078a83bdb51352e6dad113dcd4b3` | `339507934ee7dd37d0d17b0c0541710458b970ba` | 81276 |
| cmake-build | `deslop-phase-record-types` | `5c309fc1fce3e76e426078e150c36a2e7b190de6` | `8f6643d183dc0f4b5cd41c1c831c75b2c447725e` | 80940 |
| cmake-build | `deslop-budget-types` | `f04075aaf22a34e6b59d4b5637725331e0c6053f` | `e5051ef9978249471a28796f9b2e4a52891c4bd8` | 81280 |
| cmake-build | `deslop-audit-lifecycle` | `e2bd1c3e30652967b21d96ea8646167dd3d44276` | `0111edef816280ce3ebca3ab42e6a89ea4113299` | 80952 |
| cmake-build | `deslop-native-input-cache` | `3e8837fa3373a60e00f63d57f8e504f7931c9702` | `62ffb937576d7761aac5dba7dfc9ea47f98a8803` | 80820 |
| cmake-build | `deslop-cmake-diagnose` | `e8db8d5314dc0baec28f28cda14c061a5ae6b2c3` | `330038ff66ad9e6eabe6389bcbfd9bfcb3edd2a1` | 80952 |
| cmake-build | `deslop-ground` | `0b40ed026dd958eba8e120cb06b358e9a5579365` | `cc8296ddaefef6fec7b2498648f8ce0daa7b94fe` | 80784 |
| cmake-build | `deslop-make-test` | `45e01421af61d4d6ae8f40a0ce8437e0c254335e` | `dfd9c86c33e52bf56c0eb699d1d8a166817c82e4` | 2492 |
| node-build | `node-test-smoke-summary` | `919d75812bcd8d64a47390c4b77ff4df0cf3926f` | `8cd5550fe03e359732daaf9c30fa114ff445b3ad` | 162244 |
| node-build | `node-smoke-output-contract` | `cbf035484fc906a4af63091eea773c07a20b4baa` | `0f016df94bfacbaf64bd10ddf26b254ed666acfa` | 83168 |
| node-build | `node-cli-dispatch-contract` | `f7ca8320e4b68bc5683e7a6d4676a3d023ae8789` | `4e03e17bcd3b3d19c901d497a5b1a0a2d9f3319d` | 87944 |
| node-build | `node-cli-target-admission` | `8d9ca552856315c8ac6f3708c335ec6391ea7ca2` | `4455873499aab80beda63e73a342c0baa5c82772` | 84424 |
| node-build | `node-configure-receipt` | `566c319e4ab079b653564af5301902f3d114f948` | `f7de052663a57fd297841a8a7c9bceb2918151c7` | 82364 |
| node-build | `node-validation-probe-results` | `ddbc0fd82b8a5ba4a9ad47c8797bfbbef19bf71a` | `3b77c25846ebd5b5826174fa6b3dd8eda1d587f6` | 85500 |
| node-build | `node-architecture-smoke-probe` | `638f27a57be809ae4b7950bd1f960437cca91555` | `cc3fe4ae1cf9e0842be86efe5bd34a476b505129` | 82844 |
| node-build | `node-binary-path-policy` | `283afdd8aa97425a2fbe5ab75f8cdd6364caf608` | `5471d277c953d310178e37b9e1918ee50c177962` | 82392 |
| node-build | `node-installed-product-inspection` | `52c019850f2541a889519a0c109dd37600d1743a` | `8a92880f71ed3cbb5a55a9ae642f60fd23e12433` | 85520 |
| node-build | `node-toolchain-verification` | `de5e1348496a16094c8670dcf88e6996a9f16973` | `a0d504bae34d979d6938d8c1259cc52a1bbde396` | 83776 |
| node-build | `node-reproduce-receipt` | `dbe2994a7c18c6bb892a23b010fc83486a45d45b` | `ffb7e7521d97cb83e8f92535f1c1b8d0d27dfde8` | 83576 |
| node-build | `node-qualification-receipt` | `0999dd2f5d5e092070c5cbd16853abeb19da5d4a` | `8eda831dffb799d4ad565cbe5e3d3b33cadc4eae` | 84212 |
| node-build | `node-recipe-contract` | `71144fc26a77d3ac2b5559fba99fa5526203409b` | `c0d8533280bee2c26d5bd0b165bd57a79a7f738e` | 91432 |
| node-build | `node-in-process-encoding-receipts` | `dc115294e7c3c063127a0ce2af8a8717fc32178b` | `a73656fe6fefd11db5c99c5799ec8beb3ffdc059` | 243580 |
| node-build | `node-comparison-disposition` | `3c6580b6b97eac3b8e8e101ffeb3b0d14b070bc1` | `770dae5bc201e00a85b26ca60f74c31a3240a119` | 408 |
| node-build | `node-comparison-repeat` | `ebb85e84fde149d6b6861024a056f1075e69e360` | `33dce86612353eace575b78ad288a9f7265ec512` | 79900 |
| node-build | `node-package-target-dispositions` | `69373a6d0fc05c421b0805b0deaf0cacd858a692` | `c20aec866778e651198f964289c77ad0005e4439` | 404 |
| node-build | `deslop-assembly-copy-digest` | `d645512576aa1c3196cb5edb96af549e02b3fd48` | `0650c30475497f734e2f8eec8b763b2ca03f9964` | 80844 |
| node-build | `deslop-assembly-entrypoints` | `a7605a9fac832a9c36b4a910aab9e8feac0fb250` | `cb208c8196cab0f6aa2b874f9f188a260d76088f` | 117816 |
| node-build | `deslop-make-test` | `0518596c7e30594b18c4f6297e3293bca56759e9` | `c63d32672583e134ed705396ef9951e437546e31` | 296 |
| lz | `deslop-test-entry` | `2c6ee1fe45f033ff7f65b9ab282566a01a88ee9f` | `b76d8b11869193dbea1b61ad17fef444a14122f9` | 159516 |
| tinyland | `deslop-test-entry` | `da326dd5e187bf1f889d8c18be335d563d1527d8` | `f4e6b5e296d78bd36bbc6020f8129c617093da89` | 1176 |
| laputa-ui-dashboard | `deslop-test-entry` | `32a463016cdad4bab93b28035164a57786222bae` | `0e7e993726137d56c83b07b28bbfd0c21dd16733` | 2168 |
| e | `deslop-test-entry` | `b27273eebce4e81398c4c13e29dff769ec84cddc` | `4bc0854597f1e5a598ee2ab23a4e82c7111c1d9b` | 76236 |
| gluon | `deslop-test-entry` | `698c0ee8ef0084ad4a4bef02e3196620abc582e9` | `2a1bca45da57bc36da9a60e1666bd392c9fe011f` | 60688 |
| rustybench | `deslop-test-entry` | `abd34b148cc5eb24c957e1364988fdeabffd61f6` | `d2b7b06de812426dbffd4fe91b9289f2537f725e` | 241036 |

## November 19 follow-up

Seven more completed worktrees accounted for 1,572,920 KiB
(1.50 GiB) of path allocation. The two batches retired 97
worktrees with 14,097,664 KiB (13.44 GiB) measured before removal.

| Repository | Worktrees retired | Path allocation, KiB |
| --- | ---: | ---: |
| CMake-build | 4 | 1,267,364 |
| Defuddle-rs | 2 | 217,536 |
| E | 1 | 88,020 |

The four CMake worktrees matched the merged report, toolchain,
configure, and bootstrap revisions. The Defuddle worktrees
matched the merged Diagnose change and an ancestor of the merged
Types change. The E worktree matched the merged Ground report.
Each passed dry-run, had no open file or working-directory handles,
and was clean before retirement. Git and filesystem checks
confirmed all seven removals. The retirement tool kept the
separate Defuddle Types worktree under its integration check.
[CMake bootstrap](https://github.com/laputa-systems/cmake-build/pull/83) ·
[Defuddle Types](https://github.com/joshuarli/defuddle-rs/pull/17) ·
[E Ground](https://github.com/laputa-systems/e/pull/30)

## TLS and CLI follow-up

Three worktrees completed while the campaign continued. Their
combined path allocation was 684,940 KiB (0.65 GiB). Across
all three batches, 100 worktrees were retired with 14,782,604
KiB (14.10 GiB) measured before removal.

| Repository | Worktree | Retired revision | Accepted default | Path allocation, KiB |
| --- | --- | --- | --- | ---: |
| cmake-build | `cmake-tls-dependency-evidence` | `fbfbcfd8a78bfb3e264f43a0c7ad3678dd69f10b` | `94996d70381500bb7a88c45ba15a10afe9d067ea` | 340372 |
| cmake-build | `cmake-tls-client-evidence` | `c766a44525bedd85dc41aeacae7a8362d1548c84` | `94996d70381500bb7a88c45ba15a10afe9d067ea` | 340608 |
| defuddle-rs | `defuddle-cli-witness` | `c1ef4b35376846ef1495b9f8c0ae399bab58bc31` | `6c32f883567a5be8d5ca2d56941372736485c601` | 3960 |

Each checkout had a clean tracked tree and no open file
handles. The ignored paths held test environments and trial
scratch. The owning backlogs record the reproduced outcomes.
`worktree-retire` confirmed patch equivalence on the dry run.
Git and filesystem checks confirmed all three removals.
[CMake native TLS](https://github.com/laputa-systems/cmake-build/actions/runs/44505269102/job/135495202575) ·
[Defuddle CLI](https://github.com/joshuarli/defuddle-rs/pull/18)

## Native trial follow-up

Six additional completed worktrees accounted for 1,423,744 KiB
(1.36 GiB) of path allocation. The four batches retired 106
worktrees with 16,206,348 KiB (15.46 GiB) measured before removal.

| Repository | Worktree | Retired revision | Accepted default | Path allocation, KiB |
| --- | --- | --- | --- | ---: |
| cmake-build | `cmake-tls-host-evidence` | `5b71eb1bc960b9bf3b92300e981c8f55c786506c` | `e4046c6a8988b55a7b409855a75765bdf2ade25c` | 340692 |
| cmake-build | `cmake-toolchain-order-evidence` | `efc80177acf1c603b23a9531cd50f27b92175298` | `e4046c6a8988b55a7b409855a75765bdf2ade25c` | 247856 |
| cmake-build | `cmake-sysroot-verification-evidence` | `505d0e6aa81738f8308f373de05002566fbdd489` | `e4046c6a8988b55a7b409855a75765bdf2ade25c` | 335400 |
| cmake-build | `cmake-sysroot-build-evidence` | `8829767233d15d843d26ce2968d3517696b0be69` | `e4046c6a8988b55a7b409855a75765bdf2ade25c` | 166180 |
| cmake-build | `cmake-reference-build-evidence` | `344762f8f2ee27220e4354b11e9d727297e91bd3` | `e4046c6a8988b55a7b409855a75765bdf2ade25c` | 329632 |
| defuddle-rs | `defuddle-single-file-contract` | `a8c33d4f42024893a77eb6dc0a53013ba2871e7a` | `b08b13e0ee54b0e9790777760f62d4f9eedf866e` | 3984 |

The dry runs identified all six as patch-equivalent to the
accepted defaults. Every worktree was clean. There were no
open handles when checked. The ignored contents were test
environments and trial scratch. Git and filesystem checks
confirmed each removal.
[CMake 16-scope trial](https://github.com/laputa-systems/cmake-build/actions/runs/44513348433) ·
[Defuddle SingleFile](https://github.com/joshuarli/defuddle-rs/pull/24)
