# OpenOrange runtime releases

`sources/sources.toml` records source identities, artifact names, candidate
patches and unresolved gaps. From `deploy/openorange`, run `bin/sources list
--json` or `bin/sources verify`. Verification is offline. `source-rebuilt`
means the deployed artifact is built here from the recorded source,
`mirrored-unchanged` means the deployed artifact is the published package or
image at the recorded identity, and `unrebuildable` means no source build is
available. `deployment` says where the component runs: `production`,
`candidate` (staged or under rollout), `held` (built and qualified but
deliberately not deployed) or `removed` (in no deployed closure). A component
is locally patched when its patch list is non-empty. A component's patch list is its apply order, and every file
in `patches/` must be registered exactly once. Listed Engine patches are
isolated candidates: no deployed artifact contains them.

## Manifest contract

An immutable JSON object has `schema: "openorange-release-manifest/1"` and
exactly the fields below. Unknown keys are rejected, including in nested
objects. All digest values are `sha256:` followed by 64 lowercase hex digits.

- `id`: `oor-` plus the first 16 hex digits of SHA-256 over UTF-8 JSON with
  sorted keys, no whitespace and Unicode unescaped, excluding `id`.
- `commits`: `stats` and `stuff`, each a full 40-hex commit.
- `sources`: nonempty array of `{name, revision, patches}`; each revision is
  40-hex and `patches` is an ordered array of `{file, sha256}` from the source
  registry.
- `lockfiles`: a nonempty object mapping names to digests. `artifacts` has
  nonempty digest maps named `packages`, `native_addon`, and `executables`,
  plus an optional nonempty `oci` digest map.
- `toolchains`: nonempty object mapping tool names to exact identities.
- `build`: `{recipe, target_arch, libc, features, inspector_ui}`; features is
  an array of names and inspector_ui is a boolean.
- `compatibility`: `{config, persisted_format}`, both nonempty descriptions.
- `previous_release`: the previous compatible `oor-` identifier.
- `recovery_method`: the tested recovery method, as a nonempty description.

`lib/oorelease.py` provides `manifest_id` and `validate_manifest`; validation
checks shape and identities, not whether the build or recovery actually ran.
A first release still needs an explicitly established previous compatible
release before it can use this schema.

## Inspection

Copy `deploy/openorange/sources/inventory.example.toml` to an operator-owned
file, set the SSH config, standby Engine container, configuration and storage paths, and exact recovery route addresses, then run:

```sh
deploy/openorange/bin/release-inspect --inventory inventory.toml --stats-repo /path/to/stats
```

The SSH config must resolve both host aliases. Inspection issues read-only
commands, reports config hashes rather than contents, and does not request
environment or secret files. It compares the standby package and lockfile
hashes with the checkout, and resolves running container image IDs against
selected images. A missing route or image identity is unknown and is reported
as drift; no writer is inferred. Exit 0 means no detected drift, 3 means drift
or unknown identity, 2 means invalid command usage, and 1 means a runtime or
transport failure. Inspection is not a release, health or recovery proof.

## Owned OpenOrange package

`bin/build-open-orange acquire --descriptor FILE --out DIR` fetches the pinned revision,
applies its ordered patches, verifies the pinned pnpm tarball against its npm
registry integrity, and fills `DIR/store` and `DIR/toolchain`. With the upstream
Node requirement on PATH, `bin/build-open-orange build --descriptor FILE --src DIR --out OUT`
builds offline. Production runs the owned `1.0.2-laputa.1` package. Upstream 1.0.2 plus
two registered patches maps to the candidate `1.0.2-laputa.2`, whose serve
startup log reports its package version. The build record
`openorange-build-record/1` identifies the source, ordered patch digests,
lockfile, toolchain and pnpm tarball integrity, commit time, platform and
resulting tarball for a later release manifest. The build sets
`SOURCE_DATE_EPOCH` to the upstream commit time and uses pnpm pack directly. Byte identity is claimed only for the recorded Node and
pnpm identities.

The prototype transaction controller and its current adapter limits are
described in [OpenOrange rollout transactions](openorange-rollouts.md).

## Rivet Engine candidate

`bin/build-rivet-engine acquire --out DIR` fetches the registered source,
checks and applies its six patches in order, acquires the source-pinned Rust
and vendors the locked Cargo dependencies. `bin/build-rivet-engine build --src
DIR --out OUT` checks the patched source against the registry and builds in the
pinned Linux x86-64 builder with networking disabled. Its
`rivet-engine-build-record/1` records the source, ordered patch digests,
Cargo.lock, image, Rust identity, limits and binary digest; the record validator
checks the closed schema and registered identities. Qualification results and
limitations are in [Engine qualification](openorange-engine-qualification.md).
This build record is not a production release manifest or promotion.

The first candidate record hashes to
`sha256:bd867994865b4c250f87683453e45cfbf78143aafe5201eaeff499b18244e620`
and names binary
`sha256:9c1f1c7a1b55b66d730ae6b483fe98a1b0d6b871a36f58bf09b27f5965a3db56`.

Native runtime artifacts use `openorange-runtime-build/1` descriptors. Run
`deploy/openorange/bin/build-runtime-artifact --descriptor FILE --stats-repo PATH --out DIR`
with a Stats checkout containing the pinned revision. The builder verifies the
three input hashes and the pinned pnpm integrity before installing the closure.
It writes `runtime.tar`, `manifest.json`, and `build.json`. The tar carries the
manifest digest in its PAX header, which the native stage operation verifies
against extracted content. `release.json` is the sole excluded path; release
labels do not determine identity.

The OpenOrange package builder requires `--descriptor FILE` for both `acquire`
and `build`. Its `openorange-package-build/1` descriptor names `upstream`
(`repository` and `revision`), `patches` (`file` and `sha256`), `node_version`,
`pnpm_version`, and `pnpm_integrity`. The upstream and patches must agree with
`sources/sources.toml`. Set `STATS_REPO` to the Stats checkout for qualification.
