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
uv fallback, not its python-build path. Whether stuff vendors buildlib's bootstrap is decided by
[STUF-101](campaigns/deslop-buildlib.md); stuff's builds must stay independent of its own registries.

The first cold run on `ubuntu:24.04` arm64, on a 17-core host, took 28 s for setup, 6 s for
`make lint` and 57 s for `make test`.

Optional workflows need more than this: `make smoke` (pinned npm and repair tools, network),
`make test-mypypi-linux-native` and `deploy/test-linux.sh` (Docker), the Worker
(`wasm32-unknown-unknown` and `wasm-bindgen-cli`, see
[the Worker README](../crates/stuff-worker/README.md)), and publication credentials
([PUBLISHING.md](PUBLISHING.md)).
