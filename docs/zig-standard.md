# Zig project standard

This standard applies to every repository tagged `zig` in `fleet/catalog.toml`. It sets a common
floor through configuration, CI, and documentation. It does not require source rewrites, renames,
or limits on language features such as `@ptrCast`. Each repository keeps its own domain gates.

## Requirements

| ID | Area | Requirement |
| --- | --- | --- |
| Z1 | Toolchain | `.zig-version` is exactly `0.17.1`, and `minimum_zig_version` in `build.zig.zon` matches it. |
| Z1a | CI toolchain | Each `mlugg/setup-zig` step omits `version:` or sets it to the pinned version. Any other Zig install uses the pinned version and verifies a checksum. |
| Z1b | CI caches | A Zig cache key contains the pinned version or `hashFiles('build.zig.zon')`. |
| Z2 | Dependencies | Each remote dependency has an immutable URL and a `.hash`. `build.zig.zon` declares `.fingerprint` and explicit `.paths`. A build step fetches outside the Zig package manager only with a verified checksum. |
| Z3 | Formatting | No workflow, Makefile, or hook runs `zig fmt`, including `zig fmt --check`. The fleet `no-formatters` rule applies without a Zig exception. |
| Z4 | Entry points | The root Makefile defines `make test` and `make lint` as thin wrappers over the repository's `zig build` gates. `make lint` runs a compile or static check, never a formatter. |
| Z5 | Known failures | A tracked document lists each known test failure by exact name with its reason. A known failure never hides a new failure. |
| Z6 | Published artifacts | Each published artifact has a fixed, documented optimize mode, target, and CPU baseline. A published artifact never targets the host's native CPU. |

## Toolchain resolution

`mlugg/setup-zig` reads `minimum_zig_version` from `build.zig.zon` when `version:` is empty. If it
cannot read that value, it falls back to the latest tagged release, so a job that omits `version:`
must run with `build.zig.zon` in its working directory.

The action defines no version output. A cache key therefore cannot read the resolved version from
the setup step. Use `hashFiles('build.zig.zon')` when the workflow does not state the version.

## Repository-owned gates

These gates stay outside the shared standard:

- tf owns its kernel contract, Metal, CUDA and HIP builds, and `-Dcpu` and `-Dfixed-cpu` selection.
- ghostty owns its renderer, application runtime, and platform packaging gates.

## Exceptions and enforcement

The fleet `no-formatters` rule enforces Z3. No repomod rule enforces the other requirements yet.
