# Publisher diagnosis

This review covers the high-risk publication boundaries in `crates/stuff` at DSLP-10's base. It does not review the other crates, the Worker, deployment scripts, or live services. Registry library internals, the full CLI, and every archive and index case were not exhaustively reviewed.

No defect met the reproduction threshold, so no finding was filed. In particular, a dry run against `FakeS3` with the Cargo fixture and no initial `Cargo.lock` completed with the file still absent. The temporary reproduction called `stuff::publish::run(dry_run_request(&manifest), &environment)` using the setup in `tests/cargo_publish_e2e.rs`; `cargo test -p stuff --test cargo_publish_e2e dslp10_repro_missing_lockfile -- --exact --nocapture` passed. The temporary test was removed after the run. The existing interdependent-workspace test checks restoration when the lockfile already exists.

The review traced these boundaries and their existing offline tests:

- Credentials: service file permissions and validation, environment selection, signing, and redaction in `publish/service.rs`, `publish/r2/credentials.rs`, `publish/r2/client.rs`, and `tests/r2_credentials.rs`.
- Activation: object and manifest upload phases, manifest verification, conditional marker writes, rollback, and republish in `publish/r2/sync.rs`, `publish/r2/promote.rs`, `publish/transaction.rs`, `publish/rollback.rs`, `publish/republish.rs`, `tests/r2_transaction.rs`, and `tests/republish.rs`.
- Retry and locks: R2 retry behavior, coordinator lease renewal and activation retry, the transaction conflict loop and file lock, and `tests/publish_retry.rs` and `tests/r2_transaction.rs`.
- Cargo archive and index: framing and bounds, archive path and identity checks, packaged-manifest reconciliation, index rendering, and `tests/cargo_publish_e2e.rs`.
- Errors: `PublishError` classification and CLI output in `publish/mod.rs`, `main.rs`, `tests/cli.rs`, and `tests/publish_output.rs`.

The review did not establish correctness under every crash, network failure, or concurrent writer. It did not exercise live R2 or publish to a real registry. The Tests and Dead code steps remain open.
