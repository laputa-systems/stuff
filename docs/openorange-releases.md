# OpenOrange runtime releases

`sources/sources.toml` records source identities, artifact names, candidate
patches and unresolved gaps. From `deploy/openorange`, run `bin/sources list
--json` or `bin/sources verify`. Verification is offline. `source-rebuilt`
identifies a source build target, `mirrored-unchanged` a pinned registry image,
and `unrebuildable` an artifact without an available source build. These are
ownership classifications, not evidence that a candidate patch is deployed.
The lifecycle and inventory candidate order in the registry follows the
requested inventory order but conflicts with the tested order in
[the lifecycle proof](openorange-actor-lifecycle.md); resolve that gap before
building with both patches.

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
