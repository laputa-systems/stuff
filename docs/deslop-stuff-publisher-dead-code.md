# Publisher dead-code review

Scope: `crates/stuff/src` at DSLP-10's base, on macOS with rustc 1.102.0-nightly. `CARGO_BUILD_JOBS=1 cargo rustc -p stuff --lib -- --force-warn dead_code --force-warn unreachable_pub` exited 0. An earlier four-job build was killed by SIGKILL while compiling `tar`; the one-job retry completed.

The scan reported no dead-code warnings and four `unreachable_pub` warnings: `Staging`, `create`, `path`, and `join` in `src/publish/staging.rs`. The enclosing `staging` module is `pub(crate)`. These items are used by the Cargo, npm, PyPI, OCI, mirror, and republish paths; `Staging` also removes its directory on drop. They are not dead. Restricting their spelling to `pub(crate)` would not remove behavior or code, so the review retains them.

The debloat read checked the binary entry point and command dispatch in `src/main.rs`, the command definitions in `src/cli.rs`, and the `Request` dispatch and module registrations in `src/publish/mod.rs`. The five registry publishers, republish, rollback, doctor, catalog operations, and lock-path commands have registered paths. `docs/PUBLISHING.md`, `deploy/test-publish-lock.sh`, and integration tests consume these paths. The Worker maps published generation paths, and repomod reads published catalogs. The generation and manifest formats therefore cannot be classified as dead from local call counts.

No behavior-preserving dead code was demonstrated or removed. No public CLI or format removal is proposed. Any future removal of those contracts is **Needs owner ·** and requires a separate walk-back. The compiler scan covers the library's current target and configuration; it does not prove reachability for every target, dynamic consumer, or public API.
