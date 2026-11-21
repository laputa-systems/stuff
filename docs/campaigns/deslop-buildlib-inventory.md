# Buildlib adoption inventory (BLD-0)

Prepared 2026-11-21 for STUF-101 and the [buildlib adoption plan](deslop-buildlib.md).
This is the BLD-0 inventory: one row per active entry in [fleet/catalog.toml](../../fleet/catalog.toml),
recording the reviewed disposition, exact default-branch revision, overlapping tooling, affected
outputs, bootstrap need, exclusions and next action. It is review evidence only; it does not
qualify a migration, change a pin or run a build.

**Method.** Parsed `fleet/catalog.toml` with Python `tomllib` and dropped every entry tagged
`IGNORE`, leaving 66 active entries. For each checkout at `~/repos/<name>` (joshuarli) or
`~/repos/laputa-systems/<name>`, ran `git -C <checkout> fetch -q origin` and then
git -C <checkout> rev-parse origin/HEAD read-only; no checkout, reset or switch was performed.
Tooling paths, imports and pins were read from the recorded revision with `git ls-tree`,
`git grep` and `git show`, not from working-tree state. Buildlib was read at
`50d8081532a4f338527252fe4cf4f0adb10c893c` (origin/HEAD), the revision the plan reviewed:
`locks`, `release`, `hashing`, `targets`, `elf`, `macho` and `_atomic`, with no runtime dependencies
and `requires-python >= 3.15`.

**Counts.**

| Disposition | Entries |
| --- | --- |
| Shared helpers required | 12 |
| Bootstrap only | 0 |
| Native tooling sufficient | 38 |
| Deferred | 16 |
| **Total active** | **66** |

Four checkouts were not clean when read: joshuarli/discover (untracked `handoff.md`),
laputa-systems/git-build (untracked tools/), laputa-systems/ssh-build (untracked
tools/make-archive/) and laputa-systems/stuff (modified `Cargo.toml`). Their default
revisions were still readable without modifying either checkout; untracked files are not part of
the recorded revision and are excluded from this inventory.

## Existing 0.1.0 consumers

All six declare `laputa-buildlib==0.1.0`, resolve the same wheel, and take **Shared helpers
required**; each needs a BLD-1 pin/bootstrap audit rather than a new migration. The wheel digest
below is the `sha256:` recorded in each `uv.lock`, not evidence about newly built bytes.

| Consumer | Pin | Wheel SHA-256 | Imported buildlib modules | `sources.lock.json` pin |
| --- | --- | --- | --- | --- |
| joshuarli/pi-build | `0.1.0` | `edd102a1713c903f93e19b10036983d123dd76fa1b04a0e5f3c5070f00a95383` | `locks`; `hashing.sha256_file`; `release.build_manifest`, `create_archive`, `write_manifest`, `write_sha256sums`; `targets.TRIPLES` | yes |
| laputa-systems/cmake-build | `0.1.0` | `edd102a1713c903f93e19b10036983d123dd76fa1b04a0e5f3c5070f00a95383` | `hashing.digest_file`/`sha256_file`; `locks.FetchError`, `Input`, `LockError`; `release`; `targets`; `elf.ELFError`, `hardening_violations` | yes |
| laputa-systems/node-build | `0.1.0` | `edd102a1713c903f93e19b10036983d123dd76fa1b04a0e5f3c5070f00a95383` | `hashing`, `locks`, `release`, `targets`, `elf`, `macho` | yes |
| laputa-systems/python-build | `0.1.0` | `edd102a1713c903f93e19b10036983d123dd76fa1b04a0e5f3c5070f00a95383` | `hashing`, `locks` (`fetch_input`, `load_sources`, `load_bootstrap`, `load_budgets`), `release` (`archive_name`, `manifest_name`, `create_archive`), `targets`, `macho` | yes |
| laputa-systems/ffmpeg-build | `0.1.0` | `edd102a1713c903f93e19b10036983d123dd76fa1b04a0e5f3c5070f00a95383` | `hashing`, `locks`, `release`, `targets` | yes |
| laputa-systems/chromium-build | `0.1.0` | `edd102a1713c903f93e19b10036983d123dd76fa1b04a0e5f3c5070f00a95383` | `hashing`, `locks`, `release` | no entry |

joshuarli/ctrs is an additional helper consumer that does not pin 0.1.0 as a package: it
vendors bootstrap/buildlib-run and bootstrap/python.lock and imports `buildlib.locks` in
scripts/dev-tools.py. Its row below records that state.

## Active entries

Rows are ordered by owner and repository name. Revisions are full default-branch commit IDs
captured after the fetch described above.

| Entry | Default revision | Disposition | Overlapping custom tooling (paths) | Affected outputs | Bootstrap | Exclusions | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `joshuarli/bctl` | `b631d5335f72f2d30db1689a20aa1f66ae8ba806` | Deferred | kernel/dev/bootstrap.sh (sha256-checked fetch helper), kernel/dev/toolchain.lock, release/package.sh | Toolchain, sysroot, release images | No | Owner exclusion 2026-11-14 (heavy development); private catalog repo (deslop-cloud) | Retry awaits exclusion lift; candidate work is toolchain acquisition only |
| `joshuarli/ctrs` | `e431b988ff1ad190328250fef3359a6d0434f52d` | Shared helpers required | scripts/dev-tools.py (`buildlib.locks.fetch_input`/`load_sources`), vendored bootstrap/buildlib-run + bootstrap/python.lock, custom `native_triple()`; guest/kernel/build.sh fetches `linux-$KVER.tar.xz` with no digest | `$XDG_DATA_HOME/ctrs-dev` tool links; guest `Image`/`bzImage` | Yes (vendored bootstrap, buildlib >=3.15) | None | BLD-2 ctrs acquisition slice: pin kernel/patch identity; reuse `buildlib.targets` instead of `native_triple()` |
| `joshuarli/defuddle-rs` | `94f334ba087daee39d48c8999c947116d6afa8fb` | Native tooling sufficient | None material; cargo/npm build and test scripts | Native release binary and WASM | No | None | Reassess if acquisition or release tooling appears |
| `joshuarli/discover` | `2b1b12325fec1741a78e0286fda481b8f5fe2dc7` | Deferred | deploy/orange/build-img.sh and app build scripts; no release primitive overlap verified | Container image and app bundles | No | Owner exclusion (rearchitecture); private catalog repo (deslop-cloud) | Retry after the rearchitecture |
| `joshuarli/extensions` | `234244bcdb8ad7817067ded32f8061a72616e68e` | Native tooling sufficient | scripts/build-extensions.mjs builds extension bundles and manifests | Browser extension bundles | No | None | Reassess if release archives or pinned acquisition appear |
| `joshuarli/gh` | `1b0f45bc119007fb4b2a1a66ded29e7a3cb30707` | Native tooling sufficient | None material; Go build plus script/api-host-gateway/test.sh | Native binary | No | Fork; only our changes are in scope | Reassess if packaging grows |
| `joshuarli/img` | `a974ad121beae86be53abc010eb6fa803d30bc1d` | Shared helpers required | scripts/package-release.py (deterministic `tar --sort=name --mtime=@0`, `hashlib` SHA256SUMS), scripts/verify-release.py (`readelf`/`otool` linkage) | dist/packages/*.tar.xz, `SHA256SUMS` | Yes (buildlib >=3.15; scripts use system `python3`) | None | BLD-3: replace archive/checksum/linkage helpers with `release`, `hashing`, `elf` and `macho` |
| `joshuarli/ish` | `186bc99cdcab01afc6c1a28565f228967f92d7c7` | Native tooling sufficient | scripts/vendor-fz.sh (git-archive vendoring, no digest or release primitive) | Vendored fz source and native binary | No | None | Reassess if vendoring gains pinned acquisition |
| `joshuarli/kache` | `59a68ed45a871f0ce0068ceed82a6563f90bdfc7` | Native tooling sufficient | None material; benchmark and mutation scripts only | Native binary and benchmarks | No | None | Reassess if build/release tooling appears |
| `joshuarli/loc` | `7f4d945e317cd709b67c84b6c6a95390b32048de` | Native tooling sufficient | None material; tools/bench.py and tools/mutants_gate.py | Native release binary | No | None | Reassess if release packaging appears |
| `joshuarli/lz` | `b9726643b253f9413d9cef20ac21de63096e3fc2` | Native tooling sufficient | None material; tests/parity/setup.py prepares test fixtures | Native release binary | No | None | Reassess if release packaging appears |
| `joshuarli/mactop` | `264219f1148f4d6e22c4b89a14c2f47612655cc9` | Native tooling sufficient | None; native `swift build`/`make` | Native app | No | None | Reassess if packaging appears |
| `joshuarli/niceforge` | `05b56e29e6d950a94404c932a2a98b244829f0ed` | Deferred | scripts/fetch-native-inputs.sh -> scripts/update_smolvm.py, scripts/build_smolvm_host.py, scripts/build_smolvm_debian.py, scripts/build-runner-bundle.sh | Runner bundle and smolvm images | No (deferred) | Private catalog repo; out of scope in deslop-cloud | Integrator decision after privacy and CI access change |
| `joshuarli/pi-build` | `3cbd3c119c8c7077af45370a7074e634aeeb43ea` | Shared helpers required | tools/fetch.py, tools/archive.py, tools/release.py, tools/pack.py (`locks`, `hashing`, `release`, `targets`) | Release archives, manifests, `SHA256SUMS` | Yes (already `>=3.15`) | Owner exclusion 2026-11-19 (existing consumer; audit only) | BLD-1 pin and bootstrap audit only; no migration dispatch |
| `joshuarli/play` | `67f24f9e33f34e4892bdb100c525d30dc14e2284` | Shared helpers required | scripts/fetch-ffmpeg-runtime.sh + `ffmpeg-runtime.lock.json` (curl plus manual SHA-256), scripts/release-linux.sh + scripts/package-linux.sh (tar.xz plus `sha256sum`) | dist/player-x86_64-linux-musl.tar.xz and `.sha256` | Yes (scripts use distribution `python3`; buildlib needs >=3.15) | None; plan requires avoiding the parked headful slice | BLD-2 pilot after reconciling parked work; move verified fetch, archive and checksums to buildlib |
| `joshuarli/pytest-parallel` | `37bdea3694f33aa65a4893425ec69bd5b25b9725` | Native tooling sufficient | scripts/preflight_pypi.py, scripts/mutants_scheduling.py (release/test orchestration) | Wheel and test reports | No | None | Reassess if build primitives appear |
| `joshuarli/shck` | `9f56f4002090bdf186eba48d2798bb673959e531` | Shared helpers required | scripts/build-python-release.py + `.lock` (`TargetSpec` mapping, `tarfile`/`zipfile`, `hashlib`); wheel tags include gnu/windows beyond buildlib triples | Platform wheels | Yes (script needs >=3.12; buildlib needs >=3.15) | None | BLD-3: partial adoption for tar.xz/checksums; keep gnu/windows wheel mapping local |
| `joshuarli/soulseek-rs` | `df65f2868d7bbbeccf2958362ec7aea120e55ba6` | Native tooling sufficient | scripts/package-linux.sh (pinned nfpm download with SHA-256; deb/rpm packaging) | deb and rpm packages | No | None | Reassess if acquisition grows beyond one pinned tool |
| `joshuarli/stats` | `45fe3826036fa83b30ebdac8aef51025c353c7c3` | Shared helpers required | agent/scripts/build-static.sh (SHA-256-pinned LLVM/rustup), agent/scripts/build-target.sh (target mapping, `llvm-readobj` ELF check, `SHA256SUMS`), agent/scripts/build-release.sh | agent/dist/stats-* and `SHA256SUMS` | Yes (buildlib >=3.15) | None | BLD-3: move pinned acquisition, target mapping and ELF checks to buildlib |
| `joshuarli/syncthing` | `5997118eeacdb422fdcada7834323600cf609e79` | Native tooling sufficient | android/syncthing/build-syncthing.py (NDK build helper), `build.sh` | Android native library | No | Fork; only our changes are in scope | Reassess if release packaging appears |
| `joshuarli/tansu` | `3d38fdf31999a159433d2aac9c3c7e4dbf622abd` | Native tooling sufficient | scripts/build-sqlite-static.sh (SHA3-256 pin), scripts/build-defuddle-wasm.mjs | SQLite prefix and WASM bundle | No | None | Reassess; buildlib covers SHA-256 only, so SHA3 stays local |
| `joshuarli/toolbox` | `2c3693972f126ad3e1af269d5e145c01304da67d` | Deferred | None material; media tools do not implement build/release primitives | Native tools | No (deferred) | Private; out of scope 2026-11-15 (no Actions jobs) | Retry only if repository access and CI change |
| `joshuarli/usr` | `01c3510bbb5de27dc00e20b029f89d62026ec5fa` | Deferred | tools/sync/ffmpeg_runtime.py (tar/manifest validation, hashing), tools/sync/installer.py, host/alpine/build/*.sh; owns the `linux-capsule` skill and vendored bootstrap | Installed runtime, skills and bootstrap | No (owns the bootstrap; no package adoption in this slice) | None in deslop; shared-file/skill ownership requires the integrator | Integrator review; BLD-1 consumes the bootstrap and skill as the source of truth |
| `laputa-systems/buildlib` | `50d8081532a4f338527252fe4cf4f0adb10c893c` | Shared helpers required | Provider: src/buildlib/{locks,release,hashing,targets,elf,macho,_atomic}.py, bootstrap/{buildlib-run,python.lock} | Wheel and sdist | Yes (provider requires >=3.15) | None; this is the shared provider | BLD-1 qualifies the candidate wheel and bootstrap before any pin changes |
| `laputa-systems/chromium-build` | `e04cddcfe35781c157afccb23f9fb33134b658d1` | Shared helpers required | scripts/sources_lock.py, scripts/release_assets.py, scripts/lockcheck.py, scripts/package-runtime.py (`locks`, `hashing`, `release`) | APKs, runtime archive, release assets | Yes (already `>=3.15`) | Owner exclusion 2026-11-19 (existing consumer; audit only) | BLD-1 pin audit only; no migration dispatch |
| `laputa-systems/cmake-build` | `8031b5ebd72a846701170d432c41bd6c00c484c1` | Shared helpers required | buildsys/inputs.py, buildsys/budgets.py, buildsys/package.py, buildsys/targets.py, buildsys/elf.py (`hashing`, `locks`, `release`, `targets`, `elf`) | Release archives, manifests, `SHA256SUMS` | Yes (already `>=3.15`) | None | BLD-1 compatibility check; then BLD-2 extra compatibility check |
| `laputa-systems/crabtables` | `17fdc8c96da5dd57227e8c8a911f25a8287ae676` | Native tooling sufficient | None material; cargo/make | Native crate | No | Fork-diverged; only our changes are in scope | Reassess if release tooling appears |
| `laputa-systems/deser` | `1320aa3fda2c0122696334e555edc08792e980ea` | Deferred | None material; scripts/update-*-test-data.sh fetch test corpora and scripts/publish.sh publishes | Test corpora and crate | No (deferred) | Owner exclusion 2026-11-14 | Retry when exclusion lifts |
| `laputa-systems/diff-pretty` | `9b86cae2769c1acb5be8dac39451e6e8283f0ba6` | Native tooling sufficient | None material; scripts/mutants_gate.py and cargo/make | Native release binary | No | None | Reassess if release packaging appears |
| `laputa-systems/doas-rs` | `1e618953350b9084c4382a089971a5bbf978c611` | Native tooling sufficient | None; cargo/make | Native binary | No | None | Reassess if release packaging appears |
| `laputa-systems/e` | `3fbb0eed8f13138b82a91386442459ca8009a5a7` | Native tooling sufficient | None; cargo/make | Native binary | No | None | Reassess if release packaging appears |
| `laputa-systems/fastermod` | `7030b21e72b115642ce50263a582d3ae90ecb715` | Native tooling sufficient | None material; tools/mutants_gate.py and cargo/make | Native release binary | No | None | Reassess if release packaging appears |
| `laputa-systems/fd` | `9e0c70b791572ac2549b02e614b13fb6a01558d5` | Native tooling sufficient | scripts/create-archive.sh (upstream tar.gz/zip packaging) | fd archive | No | Fork-diverged; upstream script is untouched | Reassess only if our packaging diverges |
| `laputa-systems/ffmpeg-build` | `6d82a0e244209bd75dfaf95674df1c7de0790067` | Shared helpers required | `bootstrap.py`, `build.py`, .github/scripts/assemble_release.py (`hashing`, `locks`, `release`, `targets`) | Runtime/SDK archives, manifests, `SHA256SUMS` | Yes (already `>=3.15`) | None | BLD-2 produces the artifact play consumes; BLD-1 qualifies its pinned bytes |
| `laputa-systems/fz` | `d7b3aefd0b9d2981af149062f0656453edba83c7` | Native tooling sufficient | None material; benchmark and mutation scripts | Native release binary | No | None | Reassess if release packaging appears |
| `laputa-systems/git-build` | `0f1f948234bcb8ddc94f7be5246dcb71448baa06` | Native tooling sufficient | scripts/download-git-source.sh, `source-lock.sh`, `sha256.sh`, `package.sh`, `archive.sh`, `verify-archive.sh`, `audit-release.sh`, `qualify-binaries.sh` (shell plus jaq) | Git archives, manifests, `SHA256SUMS` | No | None; established shell implementation accepted by the previous build campaign | Keep the reasoned native-tooling exception; reassess on a named maintenance or correctness benefit (the untracked tools/ is not at the recorded revision) |
| `laputa-systems/gluon` | `2774e0a6dadd346711878c960c60c9e231786ca9` | Native tooling sufficient | None material; differential and benchmark test scripts | Native libraries | No | None | Reassess if release tooling appears |
| `laputa-systems/hi-lite` | `d53962729b945ab0cdbee719a00c3bab9cf2103e` | Native tooling sufficient | None material; tools/bump_minor_release.sh and golden generators | Crate and goldens | No | None | Reassess if packaging appears |
| `laputa-systems/jaq` | `37e94fb7ec427d40239d96016da1af4fd09c6bf5` | Native tooling sufficient | None; cargo/make | Native binary | No | Fork-diverged; only our changes are in scope | Reassess if release packaging appears |
| `laputa-systems/laputa` | `06158e925c1f1cc39bcd9a34642090eafd5d8dd5` | Deferred | `Makefile`, release/*.sh, guest seed/package scripts (XSH-native) | XSH packages and seed | No (deferred) | Owner exclusion 2026-11-14; buildlib has no model for the XSH-native target | Retry only if the exclusion lifts and a supported triple is named |
| `laputa-systems/laputa-ui-dashboard` | `cd18e480f9d31c608ffc4e1a3c2bdfeca201cb06` | Native tooling sufficient | None; pnpm and vitest | npm package | No | None | Reassess if packaging primitives appear |
| `laputa-systems/lexopt` | `7db9a3355dde415f16cc5935db842497afffd1ab` | Deferred | .github/setup_wasmtime.sh (test setup only) | Crate | No (deferred) | Effectively-upstream fork; excluded 2026-11-14 | No action while excluded |
| `laputa-systems/llvm-prebuilt-musl` | `4507caa6495479c47baec25fba663f7d7f3b00ab` | Native tooling sufficient | scripts/fetch-sources.sh, `lock.sh`, `sha256.sh`, `apply-patches.sh`, `build.sh`, `package.sh`, `validate.sh`, `check-purity.sh`, `verify-release.sh` (shell plus jaq) | LLVM archives and `SHA256SUMS` | No | None; established shell implementation in the native-tooling cohort | Keep the reasoned native-tooling exception; reassess on a named benefit |
| `laputa-systems/mdevd-rs` | `5fd4cdb637723cce01d38581b9fe7f7af97d0b6a` | Native tooling sufficient | tools/build-qemu-guest.sh (SHA-256-pinned Alpine rootfs/package lock; `apk verify`) | Guest rootfs and static daemons | No | None | Reassess if acquisition grows beyond the distro package manager |
| `laputa-systems/node-build` | `a3a4554277cdeaa664a1d1bea7349ac72fbe047a` | Shared helpers required | buildsys/node.py, buildsys/product.py, buildsys/package.py, buildsys/release.py, buildsys/budgets.py, buildsys/bootstrap.py, buildsys/validate_product.py, buildsys/reproduce.py, buildsys/targets.py (`hashing`, `locks`, `release`, `targets`, `elf`, `macho`) | Node archives, manifests, `SHA256SUMS` | Yes (already `>=3.15`) | None | BLD-2 pilot as an existing consumer; verify current pin and bootstrap first |
| `laputa-systems/oxish` | `855c64b9b12a467fa26499cf1614565058239f75` | Native tooling sufficient | None; `dist-workspace.toml` release metadata only | Native crates/binaries | No | Fork-diverged; only our changes are in scope | Reassess if release tooling appears |
| `laputa-systems/ptytest` | `15176fadfb3b5e910ebbf4784e155f437464910a` | Native tooling sufficient | None material; tools/mutants_gate.py | Crate and test reports | No | None | Reassess if packaging appears |
| `laputa-systems/python-build` | `ffeca5f338387e6621d0775a1d769076f7878584` | Shared helpers required | buildsys/inputs.py, buildsys/package.py, buildsys/targets.py, buildsys/macho.py, buildsys/bootstrap.py, buildsys/uvmirror.py, buildsys/product.py, buildsys/generations.py, buildsys/reproduce.py (all shared modules) | Python runtime archives, manifests, `SHA256SUMS` | Yes (already `>=3.15`) | Owner exclusion 2026-11-14 (heavy development; existing consumer; audit only) | BLD-1 pin audit only; no migration dispatch |
| `laputa-systems/rage` | `1c52d3e2b565d743631b74bdadd147af3016ae1e` | Native tooling sufficient | tools/publish_age_core.sh (cargo publish orchestration; no acquisition/archive primitive) | Crate publication | No | Fork-diverged; only our changes are in scope | Reassess if release packaging appears |
| `laputa-systems/rawzip` | `9453e3876b6e22e6fccbd55112a996bf28c994d6` | Deferred | None material | Crate | No (deferred) | Effectively-upstream fork; excluded 2026-11-14 | No action while excluded |
| `laputa-systems/rg` | `1f1bb5479f80f222318d8bf1b11480638cd5ef55` | Deferred | None material; .cargo/config.toml only | Native binary | No (deferred) | Effectively-upstream fork; excluded 2026-11-14 | No action while excluded |
| `laputa-systems/rust-fontconfig` | `b5b9b365b9d237772a7561d25268842d4624d9c1` | Native tooling sufficient | None; cargo/make | Native library | No | Fork-diverged; only our changes are in scope | Reassess if release tooling appears |
| `laputa-systems/rustix` | `15e30b432ee357fbf2cd180cae57d658405b9843` | Native tooling sufficient | None; cargo/make | Native library | No | Fork-diverged; only our changes are in scope | Reassess if release tooling appears |
| `laputa-systems/rustls` | `39c675f043bb8935140b8495dfecec5a9b110c07` | Deferred | None material; cargo/make | Crate | No (deferred) | Effectively-upstream fork; excluded 2026-11-14 | No action while excluded |
| `laputa-systems/rustybench` | `879cbaf26c272f7870f1b286ff5eb27c6a33c03c` | Native tooling sufficient | None material; tools/bump_minor_release.sh | Crate | No | None | Reassess if packaging appears |
| `laputa-systems/smolith` | `fc84413244cb0588691eec1aa2983d3b6aa549f8` | Native tooling sufficient | tools/stage.py (local sparse-registry staging), tools/release_graph.py, tools/release_apply.py, scripts/bump_minor_release.sh (cargo publish flow) | Crates | No | None | Reassess if acquisition or archive primitives appear |
| `laputa-systems/srv` | `b19c4c359492ddd9344d29743a319a19b40f20d7` | Native tooling sufficient | None material; scripts/mutants_gate.py | Native release binary | No | None | Reassess if release packaging appears |
| `laputa-systems/ssh-build` | `9286354b2cb826a0f56e436e632eeb9adeeba104` | Native tooling sufficient | scripts/fetch-sources.sh, `lock.sh`, `sha256.sh`, `package.sh`, `archive.sh`, `verify-release.sh`, `write-sums.sh`, `qualify-binaries.sh`, `fetch-*.sh` (shell plus jaq) | SSH/oxish archives and `SHA256SUMS` | No | None; established shell implementation in the native-tooling cohort | Keep the reasoned native-tooling exception; reassess on a named benefit (the untracked tools/make-archive/ is not at the recorded revision) |
| `laputa-systems/stuff` | `57045a134e2822bf2fe17a2210b869f98b2b615c` | Deferred | repomod/rules/build_repos.py (independent read-only lock validator), deploy/openorange/lib/oobuild.py, deploy/openorange/runtime-artifact/build.py, crates/mycrates/mycrates/acquire.py | Registries, OpenOrange runtime artifacts | No (checker must stay stdlib; offline adoption would need a separate vendored artifact) | None in deslop; own-registry independence is mandatory | BLD-1 offline vendoring/independent-artifact proof; keep the checker independent until then |
| `laputa-systems/tinyland` | `43ffad375318f105770615857ec66dbe067bf5ae` | Native tooling sufficient | tinyland/harness/prepare-guest.sh, `build-guest.sh`, `audit.sh` (SHA-256-pinned Alpine rootfs and package lock) | Guest image and audit output | No | None | Reassess if acquisition grows beyond the distro package manager |
| `laputa-systems/tm` | `66df5018c0f159ebc169907cb79ab4b532188801` | Native tooling sufficient | None material; tests/support/install-tmux-ref.sh installs a test reference | Native binary | No | None | Reassess if release packaging appears |
| `laputa-systems/vault` | `87e2045e72a774071cd64f637bf12faf4cadaeea` | Deferred | None material; cargo/make | Native binary | No (deferred) | Owner exclusion 2026-11-19 | Retry when exclusion lifts |
| `laputa-systems/webpki` | `f547200ca59301a747ecb6002aac46d63a6a9500` | Deferred | tests/amazon/download_ca_certs.sh (test data only) | Crate | No (deferred) | Effectively-upstream fork; excluded 2026-11-14 | No action while excluded |
| `laputa-systems/xsh` | `c68ac9594aefbacf08ff88699b9682cd6f91ad53` | Deferred | bench/consolidation/sources.lock.json, dev/checks/upstream.lock.json (benchmark and upstream checks, not release tooling) | XSH binary and benchmark data | No (deferred) | Owner exclusion 2026-11-14 | Retry when exclusion lifts |
| `laputa-systems/zlib-rs` | `1f5a56315585261976d3d348962076080104a90f` | Deferred | None material | Crate | No (deferred) | Effectively-upstream fork; excluded 2026-11-14 | No action while excluded |
| `laputa-systems/zzz` | `f28d1287992ff511c7cdd1e7d4265b3ed0dd9197` | Native tooling sufficient | `Makefile` (unpinned `zig` download, native `zig build`) | `zzz` binary | No | None; owner keeps zip release archives (release-archive campaign exclusion) | Keep native; add a digest if the Zig fetch becomes release-critical |

## Notes

- "None material" means the repository uses native tool commands or tooling unrelated to
  buildlib primitives; it is not an exemption from the inventory.
- Excluded repositories are recorded as deferred or, for existing consumers, audited under
  Shared helpers required. The fleet-wide policy does not reopen an existing exclusion.
- Buildlib has no XSH-native, gnu, Windows, Android, iOS or WASM target model; those mappings
  stay local even where a repository adopts a shared archive or checksum helper.
- No pin, lockfile, bootstrap or consumer repository was changed by this inventory.
