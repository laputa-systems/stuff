# Private Engine SQLite repair candidates

`rivet-e5ed391-staged-refusal.patch` applies to Rivet revision
`e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9`, the source named by the deployed
image's BuildKit provenance. Rivet and this patch use Apache-2.0.

This is an isolated STUF-87 candidate. It has not replaced the production
Engine image or binary. Do not apply it to a running shared Engine.

The captured failure was a staged SQLite request refused with
`Overloaded { retry_after_ms: 275, token: None }`, followed by an abort
refused with the same error category. The original protocol treated only
cold-read refusals as resumable. Its attempted abort then fenced the volume.

The patch retains a staged segment or finalize request when the filesystem
error proves nothing was admitted. The transport resends the identical
request within its existing refusal budget. A token-bearing overload or
uncertain outcome remains non-retryable. Segment prefetch metadata changes
only after admission succeeds; a refused finalize keeps that metadata.
Existing abort and fence behavior remains for other errors and for an
exhausted refusal budget. Two diagnostic sites retain the request and abort
causes. No persisted format changes.

`rivet-e5ed391-staged-head.patch` applies after the refusal patch. Stage
acquisition may settle an older undecided commit after the request read its
head. This patch rechecks the head while holding the new inode footprint,
rejecting an obsolete base through the existing head-fence error. Its
regression holds an admitted finalize undecided, settles it in the next
stage-begin barrier and verifies rejection followed by a valid staged commit.
The regression fails before this patch and passes after it. This is not yet
full import or recovery acceptance.

`rivet-e5ed391-empty-abort.patch` applies third. After resolving any uncertain
admission, an empty filesystem transaction has no durable pending entry to
abort. Release its local reservation instead of writing an unnecessary abort
that overload can refuse. A transaction with an admitted segment still needs
its durable abort. The strengthened regression fails before this change,
then both paths pass in the five-test dev and release runs. The full release
Engine build also passes. All three patches apply in sequence to a disposable
checkout at the attested source revision.

`rivet-e5ed391-page-read-refusal.patch` applies fourth. A tokenless quorum
failure from a committed SQLite page read can be retried while the filesystem
still owns its opening. The page protocol preserves the stage and the
underlying structured error, then uses the existing bounded Envoy retry loop.
The same error during a write, an admitted token or lost ownership remains
non-retryable. Eight regressions pass in dev and release; removing each of the
read-scope, ownership and admitted-token checks fails its intended test.
The source review found no demonstrated introduced defect. See
[the page-read diagnosis](../../../docs/openorange-sqlite-page-read.md) for
the exact source, patch and runtime evidence.

The retry hint has one owner in the page protocol, used by both stage
cleanup and the Envoy caller. The existing cold-read predicate still serves
the prefetch planner. The patch adds four test dependency edges to packages
already in the workspace lockfile; it adds no packages, versions or runtime
dependencies.

Apply the patch in a disposable source checkout at the exact revision:

```sh
git apply --check /path/to/rivet-e5ed391-staged-refusal.patch
git apply /path/to/rivet-e5ed391-staged-refusal.patch
git apply --check /path/to/rivet-e5ed391-staged-head.patch
git apply /path/to/rivet-e5ed391-staged-head.patch
git apply --check /path/to/rivet-e5ed391-empty-abort.patch
git apply /path/to/rivet-e5ed391-empty-abort.patch
git apply --check /path/to/rivet-e5ed391-page-read-refusal.patch
git apply /path/to/rivet-e5ed391-page-read-refusal.patch
```

The tested builder is
`ghcr.io/rivet-dev/rivet/engine-base-builder@sha256:61ba0bec231a20ebe8501be2d26b4649bbb74f31353d0ea8740785ee467d5d11`,
with the source's Rust 1.99.0 pin, `RUSTFLAGS='--cfg tokio_unstable'`, four
build jobs and an 8 GiB container limit. A read-only source mount needs
`RIVET_ERROR_OUTPUT_DIR` directed to writable scratch. With that toolchain
selected, the verification commands are:

```sh
cargo test --locked --offline -j4 -p sqlite-embedded-filesystem
cargo build --locked --offline -j4 -p rivet-engine --bin rivet-engine
```

The segment and finalize regressions fail on the original implementation
because it loses the stage after refusal. With the patch, both retain the
stage, issue no abort, resend successfully and read the committed page
bytes. A third test rejects retry hints for admitted-token overloads,
fences, conflicts and deadline failures. All three pass in the builder.
The refusal candidate's full Engine dev and release builds pass, as do
its three regressions in both profiles. The additional head regression
also passes in both profiles. The two-patch release candidate completed a
preserved-depot import and the preparation integrity checks. The three-patch
release candidate additionally completes a fresh 203,950-row import within
the 1,800-second bound and passes the preparation integrity checks. It records
4,160 memory-limit events and no OOM events or kills. Three gated Engine-only
restarts satisfy the owner's revised requirement on this source; the original
ten-cycle receipt remains incomplete. No performance acceptance follows from
these builds.

The independent read-only review found no implementation defect in the
inspected refusal and retention logic, but stopped over the added test
dependency edges and flagged the absence of an integrated admitted-token
scenario. That review was incomplete. The parent checked the lockfile diff:
only those four edges changed. That token test covers classification. The
later staged-head regression additionally exercises an admitted finalize
whose outcome is unknown and settles in the next acquisition barrier.
The independent review did not cover this later patch and remains incomplete.

Private import and recovery evidence, its limits and the remaining checks
are recorded in [the diagnosis](../../../docs/openorange-engine-diagnosis.md).
