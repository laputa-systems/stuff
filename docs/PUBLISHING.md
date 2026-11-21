# Publish

For the complete publication command reference and examples, run `stuff --help` offline.


`stuff publish cargo|npm|pypi|oci|mirror` is the normal entry point. `stuff publish --help` is authoritative for its grammar, options, and exit codes. A publish reads the live generation and manifest, prepares the requested packages against them, validates the complete result, uploads only missing objects, activates the generation through the durable coordinator, reads back, and reports; a request whose bytes are already published reports `unchanged` and promotes nothing.

## Check prerequisites

| Requirement | Use | Check |
| --- | --- | --- |
| Owner-only publishing service credentials | Authenticate the gateway and coordinator | `~/.config/stuff/credentials.json`, mode 600 |
| Publication state | Extend the live registry instead of replacing it | A publish reads the live generation; local state is optional |
| Python 3.11+ | Run the kept R2 maintenance scripts and the `mycrates` oracle | `python3 --version` |
| Rust nightly | `cargo publish` for crates | `cargo --version` |
| Node and npm | `mynpm` fetches npm packages | `node --version` |
| uv and CPython 3.15 | `mypypi` resolves and builds wheels | `uv --version` |
| `auditwheel` or `delocate` | `mypypi` repairs native wheels | `deploy/provision-mypypi-repair.sh` installs the pin |
| `sandbox-exec` (macOS, built in) or `bwrap` (Linux) | Confine sdist build backends and wheel import checks | `bwrap --version`; the container needs the flags in the mypypi README |
| Network | Fetch crates, npm tarballs, and Python wheels | |
| OCI writer host (optional) | Stream authenticated pushes through signed upload URLs | `deploy/myoci-writer.sh` runs with the shared secret and publishing service credentials |

The native publisher reads the service credential file described below. It does not invoke Cloudflare or mint backing-store credentials. The gateway accepts immutable uploads under renewable leases; the coordinator owns activation, rollback and collection. Ordinary publishers receive only service credentials.
`stuff` keeps configuration (the per-registry `bucket` and `public_base_url`, and `cargo.download_base_url`) in `${XDG_CONFIG_HOME:-$HOME/.config}/stuff/config.json`, a disposable cache in `${XDG_CACHE_HOME:-$HOME/.cache}/stuff/<registry>`, and durable state in `${XDG_STATE_HOME:-$HOME/.local/state}/stuff/<registry>`; `STUFF_CONFIG_HOME`, `STUFF_CACHE_HOME`, and `STUFF_STATE_HOME` override each. The kept maintenance scripts use the same state root. Back up the state directories. The live generation, not local state, is the publication source of truth.

## Publish a registry

Run `stuff publish` from the repository that owns the packages:

```sh
stuff publish cargo -p crate-a -p crate-b

stuff publish cargo --lockfile Cargo.lock

stuff publish npm --lockfile pnpm-lock.yaml --project my-project

stuff publish npm --tarball joshuarli-ui-0.1.0.tgz

stuff publish pypi six==1.16.0

stuff publish pypi --wheel dist/laputa_buildlib-0.1.0-py3-none-any.whl
```

`stuff publish cargo` publishes the `-p` crates in the order given. Each crate's verification resolves a dependency on an earlier crate of the same run from the registry being published to, so list dependencies before their dependents; the mirror need not hold the new versions. A crate version already in that registry's index, including one a failed earlier run recorded locally but did not promote, is skipped, so rerunning the same command completes the remaining crates.

`--dry-run` stages the requested change without uploading or promoting. `stuff` prepares against the live generation rather than replacing it with a local subset. Validation and drop checks precede uploads; an upload failure can leave unactivated objects. Keep one publishing machine per registry, as described under conditional promotion below. PyPI acquisition can currently populate persistent wheel state during a dry run.

Every writer of a registry holds one lock file: `$STUFF_STATE_HOME/<registry>/publish.lock` for `cargo`, `npm`, and `pypi`, and `$STUFF_STATE_HOME/oci/transaction/publish.lock` for OCI publish and rollback. `stuff lock-path BUCKET` prints it for any bucket in the configuration, including custom names and the OCI blob bucket; `stuff lock-path --registry NAME` prints it by registry. `r2-gc.py`, `r2-gc-blobs.py`, and `mypypi-container.sh` resolve their lock through it and fail on an unconfigured bucket, so the `stuff` on `PATH` (or `$STUFF`) must include `lock-path`; `make install` rebuilds it into `$PREFIX/bin` (default `~/.local/bin`).

`stuff publish pypi` mirrors wheels for five targets: `linux-x86_64`, `linux-aarch64`, `linux-musl-x86_64`, `linux-musl-aarch64`, and `macos-arm64`. macOS is supported on Apple silicon only; `macos-x86_64` is retired and is never planned as a target. Wheels already on the mirror stay served and are carried forward into new generations unchanged. A publishing host whose live manifest records a retired target skips it when planning (unknown, never-retired targets still fail loudly), so a retired target needs no manifest surgery. The musl targets take `musllinux_1_0` through `musllinux_1_2` wheels only, so Alpine hosts install from the mirror; a package with no musllinux wheel and no source archive fails the publish, and one with only a source archive needs `--allow-sdist`. The publishing host's native target is `linux-musl-<arch>` when its Python interpreter links against musl, and `linux-<arch>` otherwise.

PyPI publication inspects foreign-target wheels statically and executes native-target installation/import checks. Use matching runners or `deploy/mypypi-container.sh` for foreign-platform execution checks; see [crates/mypypi/README.md](../crates/mypypi/README.md).

Package code runs only inside an execution boundary. Sdist build backends (`--allow-sdist`) run under `sandbox-exec` on macOS or `bwrap` on Linux with no network; their `build-system.requires` are resolved first in a confined prime stage that pins the hash-pinned build-constraints set (`deploy/build-constraints.txt`), so an unpinned backend fails instead of fetching. The import check of every new native wheel runs in the same boundary, also with no network. If the sandbox tool is missing or cannot start, the publish fails with `execution boundary unavailable` (exit 1) before any package code runs, and nothing is promoted. R2 credentials never leave the `stuff` process. The grants, host requirements, and residual risks are in the [mypypi README](../crates/mypypi/README.md#execution-boundary).

To ingest a whole fleet locally, `deploy/fleet-ingest.sh OUT_DIR --cargo LIST --npm LIST --pypi LIST` (`make fleet-ingest`) runs each registry's import, fetch, verify or validate, and publish into `OUT_DIR/{mycrates,mynpm,mypypi}/site`. Lists hold Cargo.lock paths, pnpm-lock.yaml paths, and `name==version` requirements. It never writes to R2; publish through `stuff publish`.

`stuff publish cargo --lockfile PATH` (repeatable) extends the crates.io mirror view (`current/crates-io/`) with every crates.io package the locks pin; it does not combine with `-p`, `--manifest-path`, or `--registry`. Git, path, and other-registry entries are skipped (`--verbose` lists them). A package neither the local state nor the live generation holds is taken from `https://index.crates.io/` with its exact index line; its archive comes through the index's `dl` template and must match both the lock checksum and the index `cksum` before it is scanned and stored, or the run fails with exit 4 and promotes nothing. Packages already mirrored are not downloaded again, and a run that adds nothing reports `unchanged`. `repomod deps mirror` drives this, `stuff publish npm --lockfile`, and `stuff publish pypi` for the fleet; see [fleet](fleet.md#dependency-upgrades).

## Publish a first-party npm package

`stuff publish npm --tarball PATH.tgz` hosts a package that exists nowhere upstream beside the mirror. Pack it first with `npm pack` or `pnpm pack` (`--tarball` may repeat), and run the pack's `prepack` build yourself; `stuff` reads the tarball and never runs package scripts. `--tarball` and `--lockfile`/`--project` are separate modes and do not combine.

```sh
(cd packages/ui && npm pack --pack-destination /tmp/packs)
stuff publish npm --tarball /tmp/packs/joshuarli-ui-0.1.0.tgz --dry-run
stuff publish npm --tarball /tmp/packs/joshuarli-ui-0.1.0.tgz
```

The publish extends the live generation exactly as a lockfile publish does, so every mirrored package and version stays. The tarball is stored in the shared tarball store and served at `current/-/tarballs/<sha512>.tgz`; the packument carries `dist.integrity` (sha512), `dist.shasum`, `dist-tags.latest` (the newest publish), `time`, and these `package.json` fields: `description`, `license`, `type`, `main`, `module`, `types`, `exports`, `sideEffects`, `bin`, `engines`, `os`, `cpu`, `libc`, and the dependency maps (`dependencies`, `optionalDependencies`, `peerDependencies`, `peerDependenciesMeta`, `bundleDependencies`).

Rules, all exit 3 on violation:

- A published `name@version` is immutable. The same bytes report `unchanged`; different bytes conflict.
- A first-party name cannot reuse a name the mirror hosts (any mirrored version or metadata-only stub).
- A later lockfile publish cannot mirror another version of a first-party name from upstream.

First-party records live in the generation manifest as artifacts marked `"firstParty": true`, with no local state of their own, so later mirror publishes and `stuff republish npm` carry them forward and a machine with no state sees them. Consumers install by version:

```ini
@joshuarli:registry=https://npm.17166969.xyz/current/
```

A lockfile that names a first-party `name@version` resolves from the generation, not from npmjs.

## Publish a first-party Python package

`stuff publish pypi --wheel PATH.whl` hosts a pure-Python package that exists nowhere upstream beside the mirror. Build it first with `uv build --wheel` or `pip wheel` (`--wheel` may repeat); `stuff` reads the wheel and never runs a build backend or imports the package. `--wheel` and `SPEC`/`--allow-sdist` are separate modes and do not combine.

```sh
(cd ../buildlib && uv build --wheel --out-dir /tmp/wheels)
stuff publish pypi --wheel /tmp/wheels/laputa_buildlib-0.1.0-py3-none-any.whl --dry-run
stuff publish pypi --wheel /tmp/wheels/laputa_buildlib-0.1.0-py3-none-any.whl
```

The publish extends the live generation exactly as a mirror publish does, so every mirrored wheel stays. The wheel is stored at `wheels/<filename>` with its `.metadata` sidecar and served by the same simple pages as a mirrored wheel, including `#sha256=`, `data-requires-python`, and `data-core-metadata`. Each wheel is inspected statically for every configured target (METADATA name and version against the filename, `WHEEL` tags, `RECORD` hashes and sizes, unsafe members, native binaries) and must carry only `none-any` tags; a platform wheel exits 2. The wheel is not installed or imported, so its dependencies need not resolve at publish time.

Rules, all exit 3 on violation:

- A first-party `name==version` is immutable. The same wheel reports `unchanged`; different bytes, or a different wheel filename for the same version, conflict.
- A first-party name cannot reuse a name the mirror hosts.
- A later mirror publish cannot add another version of a first-party name.

First-party wheels live in the generation manifest as rows marked `"first_party": true`, with no local state of their own, so later mirror publishes and `stuff republish pypi` carry them forward and a machine with no state sees them. Rows of mirrored wheels are unchanged, so existing generations and their ids are unaffected; older binaries reject a manifest that contains a first-party row. Consumers install by version:

```sh
uv pip install --index-url https://pypi.17166969.xyz/current/simple/ laputa-buildlib==0.1.0
```

A mirror publish resolves its specs against upstream PyPI, so a spec or dependency naming a first-party package fails to resolve there (exit 2) instead of using the hosted wheel.

## Publish the OCI registry

The protocol, storage, and activation design is in
[oci-design.md](oci-design.md).

`stuff publish oci` imports every image into its state, renders one OCI
generation, syncs blobs before metadata, and flips `current`. The metadata
bucket is `stuff-oci`; blob bytes live in `stuff-oci-blobs` under
`sha256/<hex>`. `oci.bucket` and `oci.blobs_bucket` in
`${XDG_CONFIG_HOME:-$HOME/.config}/stuff/config.json` override both names.

```sh
stuff publish oci --image example/app=ghcr.io/example/app:v1

stuff publish oci --layout tests/fixtures/oci/layout --repository example/app \
  --tag stable

stuff publish oci --inventory deploy/oci-mirror.toml --lock deploy/oci-mirror.lock

stuff republish oci
```

An empty `stuff-oci` bucket makes the first publication.

The mirror input mode publishes the entries from an inventory file and
their lock. The inventory pins a source by digest or tag; `myoci mirror
resolve --config <inventory> --lock <lock>` refreshes the lock, verifying
roots, graphs, platforms, and referrers, then writes the lock atomically.
A publish with `--inventory` and `--lock` never resolves tags: it acquires
exactly the locked descriptors, verifies the batch, applies the declared
aliases in one recoverable transaction, renders the generation, and
promotes it. It is mutually exclusive with `--image` and `--layout`. The
published generation carries a deterministic `provenance.json` sidecar
recording the inventory fingerprint, policy, resolved platforms, and
applied aliases; roll back generations as usual with
`stuff rollback oci <generation>`. Acquiring the batch does not enforce
pinned aliases alone: an unmanaged alias whose bytes differ from the lock
aborts the publication before anything is promoted, and no alias moves.
The publish prepares local state and site first, then syncs blobs and
metadata, then promotes `current` conditionally; a failure before
promotion leaves the previously promoted generation untouched, and the
report separates local preparation from remote promotion. Keep one
publishing machine per registry: a home pinned to an older live generation
is refused with exit 3 instead of overwriting a competing publication.

`--image` imports through pinned `oras`; `--layout` imports a local OCI image
layout. Import verifies every digest and size, walks indexes and referrers,
and rejects sparse indexes, missing blobs, foreign layers, and schema 1. A tag
move or push creates a new content-derived generation; a rollback is
`stuff rollback oci <generation>`. With no local state, a publish rebuilds what
it needs from the published generation.

Blob garbage collection is separate from generation GC:
`deploy/r2-gc-blobs.py [--dry-run]` unions every retained generation's
`blobs.json` and deletes unreferenced `sha256/*` objects. `myoci verify`
exits 3 on any digest, size, tag, or referrer mismatch.

Blob GC keeps everything younger than `--grace-minutes` (default 60, the
upload session lifetime): recent blobs, generations whose manifest is recent,
and the `blobs.json` of a recent generation still awaiting its manifest. A
recent generation without `blobs.json` blocks blob deletion entirely. Before
each delete batch it re-reads the metadata bucket and aborts if `current`, a
manifest, or the generation set changed. `--grace-minutes 0` is only safe
when no network push or publication can be in flight. Retain the blobs for
every generation you need to restore: `stuff rollback oci`, including
`--dry-run`, reads the target's `blobs.json` and refuses, with `current`
unchanged, when any referenced blob is missing from the blob bucket.

The registry is sha256-only. Limits: repository name 255 characters, tag 128
characters, manifest 4 MiB, upload session one hour, one upload 20 GiB.
Reads are anonymous. Writes require `Authorization: Basic` with the registry
push token; delete endpoints are not implemented.

### Push writer

The checked-in Worker configuration supplies no `STUFF_OCI_PUSH_TOKEN`, `STUFF_OCI_PUSH_SECRET`, or `STUFF_OCI_WRITER_ORIGIN`, so writes return the OCI `405 UNSUPPORTED` error. Use `stuff publish oci`. The optional network-push path has open activation and snapshot-preservation defects in [TODO.md](../TODO.md); resolve those before enabling it. Its setup uses the writer below on a TLS host and those three Worker settings.

The front (`myoci serve --push`) owns authentication, manifest validation,
generation creation, and the `current` flip. A separate `myoci writer` owns
only blob bytes: it accepts upload `PATCH`/`PUT`s on an HMAC-signed,
repo-bound, one-hour `Location`, streams and verifies the digest, then writes
`sha256/<hex>` to the blob bucket through `deploy/r2-put.py` and
`deploy/r2-multipart.py`. The writer never sees registry credentials.

```sh
MYOCI_WRITER_SECRET_FILE=/run/secrets/oci-push-secret \
  MYOCI_WRITER_BUCKET=stuff-oci-blobs deploy/myoci-writer.sh

target/debug/myoci serve --site-dir SITE --state-dir STATE --push \
  --writer-url https://oci-writer.example \
  --push-token-file /run/secrets/oci-push-token \
  --push-secret-file /run/secrets/oci-push-secret \
  --bind 0.0.0.0:5000
```

Worker bindings: `OCI` and `OCI_BLOBS`, `STUFF_OCI_HOST`,
`STUFF_OCI_PUSH_TOKEN`, `STUFF_OCI_PUSH_SECRET`, and
`STUFF_OCI_WRITER_ORIGIN`. `STUFF_OCI_BLOB_ORIGIN` is set in `cloudflare.config.ts` to
`https://oci-blobs.17166969.xyz`, so blob GET/HEAD returns a `307` to
`<origin>/sha256/<hex>`; the `oci-blobs` bucket domain needs the Cache Rule
for `/sha256/*`. Layers over 300 MB upload through S3 multipart. The writer
host needs `R2_S3_*` for `stuff-oci-blobs`; mint them with:

```sh
eval "$(stuff credentials stuff-oci-blobs)"
```

Offline proofs: `make test-oci-pull`, `make test-oci-push`,
`make test-oci-publish`, `make test-oci-conformance`,
`make test-oci-conformance-push`, `make oci-bench`, and
`R2_S3_* make test-r2-multipart`.

## Operate the OCI mirror

The mirror copies declared upstream images into this registry with locked,
verified descriptors into a reproducible local state. Commands run from the
repository root; the inventory and lock live in `deploy/oci-mirror.toml` and
`deploy/oci-mirror.lock`. myoci exit codes: `2` usage, `3` integrity,
`4` conflict, `5` limit, `6` network, `1` other.

### Add or change an entry

1. Add the `[[entries]]` block to `deploy/oci-mirror.toml`: a `source`
   reference (tag or digest; Docker Hub shorthand is normalized), a
   `destination` repository, `aliases`, `platforms`, and `referrers`
   (`snapshot` to observe referrers, `none` to skip discovery). Each
   destination may appear once across the inventory; two entries cannot
   write one destination.
2. Regenerate the lock:
   `myoci mirror resolve --config deploy/oci-mirror.toml --lock deploy/oci-mirror.lock`.
   It verifies the root, the full graph (nested indexes, configs, layers,
   embedded attestations) and referrer discovery, then writes the lock
   atomically; one failed entry aborts the whole resolution and nothing is
   written. Attachments whose media types are not manifests or indexes are
   not recorded; resolve prints how many were skipped.
3. Review the lock diff. Commit inventory and lock together.

### Refresh a selected entry

`myoci mirror resolve --entry manylinux-amd64 --config deploy/oci-mirror.toml --lock deploy/oci-mirror.lock`
refreshes one entry and preserves every unselected entry byte for byte;
unrelated provenance and ownership carry forward.

### Review the plan

`myoci mirror plan --config deploy/oci-mirror.toml --lock deploy/oci-mirror.lock --state-dir <state> [--json]`
reports desired aliases, local conflicts (aliases unmanaged at a different
digest, managed aliases moved by hand, adopted identical unmanaged aliases),
missing objects (present, missing, total), and deduplicated transfer bytes.
It is local and read-only, never initializes the state, and refuses to
proceed while a mirror transaction is pending — the message says which
command recovers it. A missing or stale transfer cache degrades estimates
to `unknown`, never zero.

### Locked sync

`myoci mirror sync --locked --config deploy/oci-mirror.toml --lock deploy/oci-mirror.lock --state-dir <state> [--json]`
acquires exactly the locked digests (never a tag, never an implicit
upgrade), verifies digests and sizes, and commits aliases into
`mirror.json` plus `provenance.json` as one recoverable transaction. A tag
that moved upstream since `resolve` does not change what is acquired.
`Exit 4` with `conflict-unmanaged`: an alias at the destination is not
managed by the mirror and points at a different digest — inspect the
destination, then add the destination to the inventory intentionally or move
the tag by hand; nothing moves. `Exit 4` with `conflict-stale`: a managed
alias was moved by hand away from the last applied mapping — same recovery,
but decide deliberately before re-resolving. Foreign layers and identical
content across entries transfer at most once; acquired immutable objects may
remain after a failure.

### Offline replay

Add `--offline` to replay purely from local state:
`myoci mirror sync --locked --offline --config ... --lock ... --state-dir <state>`.
It succeeds only with complete local content and otherwise fails naming the
missing objects; it performs zero network requests.

### Publish

`stuff publish oci --inventory deploy/oci-mirror.toml --lock deploy/oci-mirror.lock`
validates the batch, acquires and verifies the locked descriptors, commits
local metadata, renders, syncs blobs and metadata, and promotes `current`
conditionally. It never resolves tags. An inventory with zero entries is
refused with a usage error; an empty generation is never promoted. The
generation carries a deterministic `provenance.json` sidecar. The publishing
machine first reconciles its local state with the live generation by adopting
into a fresh directory and swapping it in, so a concurrent command never
observes a half-rebuilt state; the previous directory is removed only after
the swap. A failure before promotion leaves
the previously promoted generation untouched; the report separates local
preparation from remote promotion. The `stuff-oci-layout` and `--image`
modes stay mutually exclusive with this one.

### Repair missing content

A missing local object: run `myoci mirror plan` to see it, then re-run the
locked sync; acquisition re-fetches exactly the missing digests.
Interrupted acquisitions can leave `mirror-*.tmp` files under `.uploads/`;
they are swept automatically once older than two hours. A missing
remote object: `stuff publish oci --inventory ... --lock ...` re-uploads it
and repairs the generation before reporting success; the previously promoted
generation keeps serving until then. Conflicting immutable remote objects
fail before any upload (exit 3) and `current` stays put; resolve which side
is wrong, never force past the conflict.

### Adopt a generation

`myoci adopt --state-dir <state> --site-dir <site>` rebuilds state from a
published generation. The `provenance.json` sidecar restores the managed
alias ownership; generations without a sidecar adopt cleanly with no
managed aliases, and the next locked sync adopts identical aliases back
into managed ownership. Finish with `myoci verify --state-dir <state>`.

### Roll back

`stuff rollback oci <generation-id>` verifies the target generation's
metadata and every referenced blob (against `stuff-oci-blobs`) before moving
`current`; `--dry-run` verifies without promoting. Retained generations are
adoptable and republishable. Missing referenced blobs make the rollback
refuse with `current` unchanged.

### Initial publication and consumer cutover

Initial publication and consumer cutover are operator steps, not CI:

1. Publish with the mirror mode; note the promoted generation.
2. Verify the live registry:
   `oras manifest fetch oci.17166969.xyz/<repo>:<alias>` and a blob pull,
   plus `stuff doctor --sample-artifacts`.
3. Cut consumers over repository by repository, pinning the mirrored
   digest or alias, verifying one consumer before the next. Do not cut a
   consumer over before the promoted generation verifies.
## Publish the static mirror

`stuff publish mirror` re-hosts static artifacts the `~/usr` installer downloads — Node.js, Codex, OpenCode, installer scripts, and dwl — under `mirror.17166969.xyz` as one homogeneous format: every pinned upstream is extracted, filtered to a list of members that matter, and repacked once. New generations provide `<id>.tar.xz`; existing generations retain their zip files. The manifest lives in [`mirror/manifest.toml`](../mirror/manifest.toml); [crates/mymirror](../crates/mymirror/README.md) documents the format. GitHub-hosted artifacts are deliberately not mirrored yet.

```sh
stuff publish mirror --dry-run
stuff publish mirror
```

Each entry pins an upstream URL, an upstream SHA-256, and an optional keep list (`keep = ["bin/**", "lib/**"]`) applied after stripping leading components. The build downloads the upstream once, verifies the SHA-256 before anything else happens, extracts (`.tar.gz`, `.tar.xz`, `.zip`, or a raw file), drops members outside the keep list, and writes a deterministic tar.xz (fixed timestamps and ownership, Unix file types and modes, symlink targets that stay inside the archive root). The generation contains `<id>.tar.xz` per entry plus `catalog.json` (schemaVersion 1, with the standard `packages` list used by the drop guard) and `SHA256SUMS`; `current` selects the live generation like the other registries. Downloads are cached by upstream SHA-256 under `~/.cache/stuff/mirror/objects` and re-verified on every reuse. When the live marker already names the generation derived from the manifest and every expected remote object is present, the publish rebuilds nothing: it only ensures the local `current` symlink points at that generation and reports `unchanged`, so a republish of an unchanged manifest downloads nothing, uploads nothing, and touches no upstream.

Because bumping an artifact's pinned `version` removes the old row from `packages`, the shared drop guard treats a version bump as a removal: `stuff publish mirror` exits 3 and lists the dropped pins. Pass `--allow-drops` when the bump is intended — this is the one publish verb that accepts the flag; `stuff republish mirror` also rebuilds from the manifest (with `--allow-drops` like the other registries and `--manifest PATH` to use a non-default manifest), and `stuff rollback mirror GENERATION` restores a previous generation. The bucket is `stuff-mirror` (configurable as the `mirror` section in `config.json`, like `npm`), the publish is a normal transaction against it, and the Worker custom domain `mirror.17166969.xyz` serves it like the static registries. The OCI inventory mode is separate and unrelated: it re-hosts container images through `stuff publish oci --inventory`.

The mirror's `catalog.json` carries the artifact manifest itself (`artifacts` with upstream URL and upstream SHA-256, `baseUrl`, `renderer`, `schemaVersion`, `registry: "mirror"`) alongside the standard `packages` list, so the drop guard only needs the packages section and `stuff doctor`, `stuff ls`, and `stuff render` all understand the mirror like any other registry: `stuff doctor --registry mirror --sample-artifacts` checks the immutable catalog, that `current/SHA256SUMS` lists the first artifact, and hashes that artifact against it.

## Republish without new packages

A renderer or catalog change reaches a registry's pages only when that registry publishes again. `stuff republish cargo|npm|pypi` reads the live generation, renders it again, and promotes it without package inputs. `stuff republish oci` fingerprints the catalog and public URL in its generation v2, so a renderer or origin change produces a new generation. `stuff republish mirror` re-derives its generation from the manifest; an unchanged manifest uses cached downloads and produces no new generation. Older manifests remain until `make gc` prunes them outside its retention window.

Republish uses the observed live generation as its promotion base even when this machine's last promoted generation is older. If another publisher changes `current` during the operation, republish refuses the competing update; rerun it to render the new live generation.

```sh
stuff republish cargo
stuff republish npm
stuff republish pypi
```

`make deploy` runs the serving and OpenOrange checks, then builds and deploys the committed image to Lisa. It preserves publication state and credentials. Publish each registry separately with the native commands; an image deployment does not republish packages.
## Shared stores

Generation-scoped aliases (`wheels/`, `tarballs/`, `-/tarballs/`, listed in `deploy/shared-store-paths.txt`) are not uploaded. The Worker resolves them to the shared store, including direct `generations/<id>/...` requests. Files over the 300 MB single-PUT cap upload through S3 multipart and are skipped when the remote multipart ETag already matches.

## Upload and activate

The publishing service provides the S3-compatible upload gateway and the durable
coordinator. A writer acquires a renewable five-minute lease, uploads immutable
objects and their manifest, and activates against the revision it read. SQL
commits the revision, generation, manifest identity and receipt together. Stable
receipt keys make a lost response safe to retry. The S3 `current` object is a
repairable projection; serving and publishers read the coordinator authority.

`stuff credentials BUCKET` prints shell exports for authenticated maintenance
reads through the gateway. It does not mint a token or grant a write lease.
The native publisher and Python writer/GC helpers acquire their own leases from
the same service credential file. Keep backing-store credentials on the server.
Explicit `R2_S3_*` credentials remain for archive/oracle maintenance; a configured
publishing service takes precedence over them, and partial credentials fail.
The retired `cf_profile` configuration field is rejected.

## Publish from a new machine

A pull needs no credentials or Tailscale: the registry and blob URLs accept
anonymous GET and HEAD requests. Publishing uses
`https://stuff-publish.17166969.xyz`, which resolves directly to Lisa's
tailnet address. The public listener blocks other methods and the upload and
coordinator paths. Publishers need Tailscale access and the protected service
credential file; they do not need split DNS.

A machine with no local state reads the live generation and manifest, verifies the objects it uses against listing size and ETag, and prepares against that snapshot. The coordinator serializes writers across machines. A conflicting lease or revision returns a conflict without replacing another writer's generation.

`deploy/r2-pull.py BUCKET DEST` only reads the bucket. It fetches the current generation and the shared stores and checks each object against its listing ETag, using the multipart ETag algorithm for objects uploaded in parts. After the download it checks every entry of the generation's manifest (key, size, ETag) against the pulled tree; a generation published before manifests existed is pulled without that check. With the publishing service credentials, or explicit archive `R2_S3_*`, it lists through the S3 API and downloads `R2_PULL_JOBS` objects in parallel. `R2_PULL_CF_ONLY=1` forces the paced `cf` transport.

The Python `mycrates` adoption sequence (`mycrates init`, `adopt`, and `verify`) belongs to the legacy oracle and its golden tests; it is not a publishing entry point.

## Legacy mycrates tools

`mycrates migrate-state` converts a Rust-tool state directory's TOML records to JSON; other commands refuse a directory that still holds TOML. `stuff publish cargo` migrates its own legacy state automatically. See [mycrates state migration](mycrates-migration.md) and the [mycrates README](../crates/mycrates/README.md). The legacy Python write path's token and `auth_required` rules are in [mycrates contracts](mycrates-contracts.md#upload-and-yank-api).

## Deploy the serving application

```sh
make deploy ORANGE_HOST=lisa
```

The image build consumes the existing compatibility build output and pinned
OpenOrange closure. Deployment reads the host's previous image, changes only
that app's image, and verifies stored registry data through the real HTTPS
hostname at the selected host's Tailscale address. Failure or interruption
restores the previous image. Runtime configuration and service credentials stay
on the host; image deployment does not publish registry content.

## Registry access

Registry and blob hostnames accept anonymous GET and HEAD through the public
tunnel and loopback ingress. Package clients need no Tailscale connection,
Cloudflare login, or browser challenge. `stuff-publish.17166969.xyz` resolves
directly to Lisa's tailnet ingress for authenticated publication. The
[host runbook](openorange-runtime.md#public-listener) defines both listeners.
When the origin does not answer, reads are served from an R2 replica by a
route-attached Cloudflare Worker; [registry failover](registry-failover.md)
defines what fails over, the replica lag, and how to drill and remove it.

Cargo downloads `.crate` files from `crates-blobs.17166969.xyz`; that reader
accepts only `/blobs/` paths. OCI redirects blob reads to
`oci-blobs.17166969.xyz`, which accepts only SHA-256 blob paths. Both readers
stream from the same private S3 store and preserve HEAD, conditional and ranged
reads. Published generation URLs and artifact hashes remain unchanged.

## Verify the publication

```sh
make smoke-deployed
```

This builds the `stuff` binary and runs `deploy/deployed-smoke.sh`. The check is read-only and needs no Cloudflare credentials. It runs `stuff doctor --sample-artifacts` against the active generations, catalog objects, and sample artifact hashes, plus `npm view`, `uv pip install --dry-run`, and `oras manifest fetch` probes, and verifies the static artifact mirror by downloading the first `SHA256SUMS` artifact and hashing it.

## Roll back a generation

```sh
stuff rollback cargo <generation-id>
```

`stuff rollback` verifies every object in the target generation's manifest before moving `current`, and records the target as this machine's promoted generation. For OCI it also HEADs every digest in the target generation's `blobs.json` against the blob bucket and refuses the rollback, with `current` unchanged, when any referenced blob is missing. `--dry-run` performs the verification without promoting. To roll forward, run the same command with the newer generation id; gc keeps generations newer than `current` by default, so the target survives.

## Reclaim storage

`make gc` deletes R2 generations outside its retention window and shared-store objects no retained manifest references, then prints per-bucket and total storage before and after. It keeps `current` plus `GC_KEEP_PREVIOUS` older generations (default 1) and `GC_KEEP_NEWER` newer generations (default `all`). Preview with `GC_DRY_RUN=1`, and restrict buckets with `GC_BUCKETS`.

Generation and OCI blob collection use the same renewable exclusive coordinator
lease as publishers. A collector checks every retained manifest and blob inventory,
records exact S3 version IDs as retired before deleting them, and leaves each
generation manifest until its bounded deletion batches finish. A generation that
has been collected cannot be reactivated. New versions of shared immutable content
can be uploaded safely. Bucket versioning must be enabled and verified.

## Fix common failures

Exact error strings live in the CLI (`crates/stuff/tests/cli.rs` pins the contract). Common causes:

- No service credential file is configured — install the owner-only credential file below.
- Another publisher moved `current`, or this machine lags the live generation — pull the new generation, re-plan, and republish; a no-op republish does not clear a stale promoted record.
- A local immutable file differs from the remote, or a pulled object fails its manifest ETag — find which side is wrong; immutable objects are never overwritten.
- An object exceeds the 300 MB single-PUT cap — set `R2_S3_*` for multipart.
- Another publish, rollback, or GC holds the lease — wait for it to finish.
- A proposed catalog drops versions served by the live generation — re-plan against the current publication; use explicit rollback for a deliberate generation switch.

## Copy a registry bucket to another store

`deploy/store-copy.py copy SOURCE DEST --ledger FILE` copies every object of a bucket to another
S3-compatible store and records each verified object in a JSON Lines ledger (key, size, SHA-256,
source and destination ETags). Source credentials come from `STUFF_COPY_SOURCE_S3_*` or, when unset,
`stuff credentials SOURCE`; destination credentials come from `STUFF_COPY_DEST_S3_*`. Objects stream
through a temporary file. A multipart object is re-uploaded with the source's part sizes (read with
`HEAD ?partNumber=N`, or the 64 MiB publication part size), so its ETag and every manifest that
records it stay valid; the ledger's `etagPreserved` says whether that held. A rerun skips ledger
entries whose source and destination still match and re-copies changed sources.

`deploy/store-copy.py verify SOURCE DEST --ledger FILE [--deep]` compares both listings, sizes and
ETags with the ledger and, with `--deep`, re-downloads the destination and checks SHA-256. It exits 1
naming each missing, extra, changed or corrupted key. `make test-store-copy` proves both offline.

`deploy/store-copy.py sync SOURCE DEST --ledger FILE` copies every object except the `current`
pointer, checks the destination holds them, and copies `current` last, so a reader following the
pointer never lands on a generation the destination lacks. It refuses to move the pointer when the
source names a generation with no objects and never deletes at the destination. The failover replica
uses it; see [registry failover](registry-failover.md).

### Publication coordinator

The publishing service's Durable Object owns each registry's activation revision;
R2 `current` is a repairable compatibility projection, not the authority. The
management endpoint, lease and activation operations, and retirement rules are in
the [Worker README](../crates/stuff-worker/README.md#coordinated-native-uploads).
The service requires `STUFF_COORDINATOR_ENABLED=true`; enable it only after
validating copied registries and fencing legacy writers during cutover.

Native publication, rollback, both GC helpers and optional OCI manifest pushes
use this authority. Immutable uploads stream through the authenticated S3 gateway,
including multipart requests, under the renewable writer lease. The gateway
refuses direct `current` writes, immutable replacement and arbitrary deletion.
GC retires exact object versions before deletion, so a delayed deletion cannot
remove a later upload of the same content. The store's root and application
backend keys remain on the runtime host.

## Coordinated publishing service

A configured publishing service owns the registry revision and grants one
renewable upload lease per registry. Native publication and rollback use that
revision, upload immutable objects through the service's signed `/_s3` route,
and activate the exact manifest through the coordinator. A lost activation
response retries the same receipt identity. Dry runs acquire no upload lease.

Store service credentials in `~/.config/stuff/credentials.json` with mode 600
(or select a file with `STUFF_CREDENTIAL_FILE`). `STUFF_CONFIG_HOME` and
`XDG_CONFIG_HOME` follow the existing configuration directory rules. The JSON
has schema 1 and requires `endpoint`, `coordinator_token`, `access_key_id`,
`secret_access_key`, and `region`. Use `auto` for the service region; other values
are rejected before any network request, matching the gateway (see below).
The endpoint is the management origin, for
example `https://stuff-publish.17166969.xyz`; its S3 route is derived from that origin.
These are service credentials, distinct from the backing store credentials.
The service must be enabled and verified before installing this file.

For isolated runs the equivalent bindings are `STUFF_COORDINATOR_URL`,
`STUFF_COORDINATOR_TOKEN`, `STUFF_S3_ACCESS_KEY_ID`, `STUFF_S3_SECRET_ACCESS_KEY`,
and optional `STUFF_S3_REGION` (must be `auto`). Partial service configuration
fails before publishing. Endpoint URLs require HTTPS except for local test
servers. Service tokens and secret keys are omitted from debug output.

`make gc` and `deploy/r2-gc-blobs.py` use the same service credential file.
They resolve bucket ownership through `stuff lock-path`, acquire a renewable
exclusive GC lease before planning, and send generation and shared-object
deletions to the coordinator. Renewal failure stops deletion. The coordinator
checks every retained manifest or OCI blob inventory and retires exact S3
version IDs before deletion; a later upload of the same content remains safe.
Dry runs hold the lease while planning and release it without deleting objects.
Backend credentials must never be given to an ordinary publisher.

Optional OCI HTTP manifest pushes use the same activation lease and receipt
protocol. The native `myoci writer` uploads completed blobs through the service
using the same credential file; single PUT and multipart helpers acquire and
renew an upload lease. Repeated immutable uploads verify the existing bytes.
Each upload session holds a file lock across append, digest verification and
storage, and separate sessions use separate staging directories. Lock files
remain stable between requests; remove them only while the writer is stopped.
HTTP push remains disabled unless its push token, session secret and writer
origin are configured. Native `stuff publish oci` needs none of those settings.

When application telemetry is configured, activation, rollback and OCI manifest
requests emit `registry.publication.attempt.<registry>`; other requests emit
`registry.request`. Receipt retries count as attempts. Operation names contain
no package names, paths or tokens. Delivery is bounded and does not gate serving
or publication when Stats is unavailable.

The publishing service signing region is `auto`. Both credential-file `region` and
`STUFF_S3_REGION` reject other values before any network request, matching the gateway.
