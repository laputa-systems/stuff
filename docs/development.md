# Development on Linux

On a fresh Ubuntu 24.04, Ubuntu 26.04 or Debian 13 host, one command installs everything
`make lint test` needs:

```sh
scripts/setup-dev
export PATH="$HOME/.local/bin:$HOME/.local/share/stuff-dev/node/bin:$HOME/.cargo/bin:$PATH"
make lint test
```

Run it as root, or as a user with `sudo` for the distribution packages. It is idempotent and
verifies every download against a pinned SHA-256. Other distributions are refused.

| Installed | Version source | Consumer |
| --- | --- | --- |
| `build-essential`, `pkg-config`, `make` | distribution | Rust build scripts with C sources; the `Makefile` |
| `bubblewrap` | distribution | mypypi's Linux Python execution boundary in `make test` |
| `python3`, `procps` | distribution | `python3` and `/bin/kill` subprocesses in the Rust tests |
| `git`, `curl`, `ca-certificates`, `xz-utils` | distribution | clones, verified downloads, the Node archive |
| uv | `deploy/uv-version` | repomod and mycrates (`uv run`) |
| CPython 3.15 | `pyproject.toml` | repomod, installed by uv |
| Rust nightly | `rust-toolchain.toml` | the workspace; also set as rustup's default when none exists, because mycrates tests run cargo outside the repository |
| Node 26.13.1, pnpm | `crates/stuff-worker/package.json` | `make ts-lint` and Node subprocesses in the tests |

CPython comes from uv's pinned release and uv's upstream CPython metadata. That is the trust path of buildlib's
uv fallback, not its python-build path. stuff does not vendor buildlib's bootstrap: its builds
must stay independent of its own registries, so the [buildlib policy](build-repos.md#dispositions)
exempts it.

The first cold run on `ubuntu:24.04` arm64, on a 17-core host, took 28 s for setup, 6 s for
`make lint` and 57 s for `make test`.

Optional workflows need more than this: `make smoke` (pinned npm and repair tools, network),
`make test-mypypi-linux-native` and `deploy/test-linux.sh` (Docker), the Worker
(`wasm32-unknown-unknown` and `wasm-bindgen-cli`, see
[the Worker README](../crates/stuff-worker/README.md)), and publication credentials
([PUBLISHING.md](PUBLISHING.md)).

## Serve a local site

`stuff-server` serves a site directory downloaded from a registry:

```sh
cargo run -p stuff-server -- --route /=path/to/site
cargo run -p stuff-server -- --route /mirror=path/to/mirror --max-connections 64
```

The server follows `current` to a generation, serves immutable `generations/` paths, and supports conditional and range requests. Directory requests serve `index.html`. `/`, `/index.html`, `/catalog.json`, `/llms.txt`, and `/simple/...` alias through the current generation.

The native server and Worker support shared wheel/tarball aliases and npm's standard `current/<name>/-/<basename>-<version>.tgz` lookup. Metadata-only npm versions support lockfile checks for excluded platforms without hosting their artifacts; see [mynpm](../crates/mynpm/README.md#metadata-only-versions).

## Command reference

Run these from the repository root. The main targets are `make build`, `make test`
(Rust workspace, mycrates and repomod) and `make lint` (clippy, ruff, ty).

| Area | Commands |
| --- | --- |
| Python oracle | `make test-mycrates` (needs Cargo for the native publication proof) |
| repomod | `uv sync`, then `uv run repomod --help`; `make repomod-test`, `make repomod-lint`. Set `TMPDIR` to `.work/tmp` for scratch data. |
| Fleet dashboard | `make deps` (syncs checkouts, snapshots tracked inventory, renders and serves); `make bench`; `make preview` (canonical preview dataset). See [dependency dashboard](dependency-dashboard.md). |
| Search | `make test-search`; after changing `crates/stuff-catalog/web/`, `make search-bundle` and commit `assets/search.js` (install Worker dependencies first). |
| Browser assets | `make ts-assets` after editing `repomod/dependencies/assets/*.ts` or `deploy/openorange/rivet/*.ts`; commit sources and compiled `.js` together. |
| Catalog styles | `make catalog-css` after bumping `@laputa-systems/ui-dashboard` in `crates/stuff-worker/package.json`; commit `crates/stuff-catalog/assets/ui-dashboard/` and regenerate the mycrates golden generation. |
| Worker | `make worker-test`, `make worker-check`; build instructions are in [its README](../crates/stuff-worker/README.md). |
| Offline maintenance | `make test-r2`, `make test-publish-lock`; `make test-r2-live` accesses real R2 and is opt-in. |
| Ecosystem smoke | `deploy/ecosystem-smoke.sh` needs pinned package managers, CPython, native repair tools and network; use `TMPDIR="$PWD/.work/tmp"`. |
| OCI | `make test-oci-conformance`, `make test-oci-conformance-push`, `make test-oci-pull`, `make test-oci-push`, `make test-oci-publish`, `make oci-bench`. |

## Verification and CI

Warm costs on an M-series Mac: `make test` 163 s, `make repomod-test` 60 s, `make repomod-lint`
under 1 s, `make lint` 19 s. The count is a snapshot, not a contract. `make test`'s macOS
sandbox test needs a real Python first on `PATH`, not Apple's `/usr/bin/python3` shim.
PR CI runs `make test` (`.github/workflows/ci.yml:45`).

Published-format tests live in `crates/stuff/tests/` (`cli.rs`, `cargo_*.rs`, `npm_publish.rs`,
`pypi_*.rs`, `oci_publish.rs`), `crates/mynpm/tests/` and `crates/mypypi/tests/`. HTTP serving is
covered by `crates/stuff-server/tests/*_compat.rs` and `crates/stuff-http` unit tests; the Worker
runtime by `crates/stuff-worker/test/`. R2 and generation activation use `crates/stuff/tests/r2_*.rs`
against `fake_s3.rs`; live R2 is opt-in. Performance workloads are `make oci-bench` (OCI serving)
and `make bench` (dashboard render); each gates only changes on its own path.
