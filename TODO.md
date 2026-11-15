Prefix: STUF
Next: 82

New tickets use STUF. RPMD tickets were filed in repomod before it moved into stuff; they keep their IDs.

Review priorities are reviewer-assigned; existing owner-assigned priorities are retained.

## On hold

- **Shadowdriver**: everything shadowdriver-related is on hold because the owner cannot publicize shadowdriver (private git dependency). This blocks the bctl CI jobs (no read secret), the `h12tiny-client-sync` 0.9.0 publish (and the laputa-rustix migration on top of it), and any other work that depends on shadowdriver being public. Hold stands until shadowdriver is public or a read credential is supplied.
- **Cargo publish 403** (`PUT .../crates-io/gi/ml/gimli: HTTP 403: forbidden`): blocks the cargo mirror backlog (435 crates, 87 npm, 4 pypi still unpublished), the `h12tiny-client-sync` publish, and the audit-upgrades sweep. Bucket/IAM intent unresolved; do not retry until the owner answers.
- **Mirror pollution**: 2006-era packages remain on the mirror, unactioned.
- **npm mirror 500s**: recurring HTTP 500s (outages ~16:26-01:00 UTC and ~02:14 UTC on 2026-11-14); mirror packages (pnpm 12.20/12.21, playwright-core 1.65.1, vitest 5.0.3, ws 8.23.0, vite 8.3.6) still absent. Snapshots of deps/loc must wait for merges and a healthy mirror.
## Tickets

### STUF-75 · P1 · Add integrity-verified S3 backup copies and isolated restore proof

- **Area:** OpenOrange durability
- **Where:** deploy/openorange/bin/backup, bin/restore-rehearsal, docs/openorange-runtime.md; Engine filesystem log and object tier are one recovery unit
- **Problem:** Current recurring backups live on Lisa's disk and known off-host Mac copies are manually made; there is no recurring independently verified S3 backup copy or restore freshness guarantee. Host or disk loss can lose writes after the latest independently verified off-host fence. The owner explicitly defers S3 backup implementation as P1 while repository hardening proceeds.
- **Recommendation:** Use existing fenced backup artifacts to add protected recurring S3 copies with complete manifests and integrity checks, retention and freshness monitoring, plus a non-production full restore rehearsal measuring RPO/RTO. Keep Engine log and object state together, distinguish backup storage from the Engine storage backend, and obtain an explicit deployment handoff/approval before credentials, scheduling or production changes.
- **Fix with:** durable-state
- **Effort:** M

### STUF-76 · P2 · Preserve source identity when merging dependency instances

- **Area:** Dependency inventory
- **Where:** repomod/dependencies/graph.py:328-336; repomod/dependencies/adapters/cargo.py:893-908; repomod/dependencies/adapters/javascript.py:212-230; repomod/dependencies/atlas.py:73-84; repomod/dependencies/analysis.py:433-440
- **Problem:** Instance IDs distinguish sources only within a repository, then build_graph merges equal IDs across the fleet with setdefault. Different sources inherit whichever repository was visited first. Calling the real graph.load_inventory, graph.build_graph and atlas.build on the tracked fleet data produces 11 repository-instance source-kind mismatches: rawzip's registry criterion node is labelled vendored while its own Atlas edges say registry. Reversing Inventory.repositories changes that node to registry. Source-risk reporting consumes the same overwritten records.
- **Recommendation:** Distinguish semantically different sources across repositories in instance identity, or retain repository-scoped instances and aggregate only component identities. Preserve explicit mirror equivalence and scope local sources appropriately. Add a two-repository regression with the same package/version and different source kinds, asserting correct source-risk and Atlas output in either iteration order. Bump the parser version and regenerate inventory if persisted IDs change.
- **Fix with:** single-source-of-truth
- **Effort:** M


### STUF-77 · P2 · Refresh origin HEAD when sync observes a changed default branch

- **Area:** Fleet synchronization
- **Where:** repomod/sync.py:175-196; repomod/git.py:361-367; repomod/dependencies/git_tree.py:24-36; repomod/dependencies/snapshot.py:88-97
- **Problem:** Sync fetches GitHub's current default branch but never repairs refs/remotes/origin/HEAD on an existing checkout. Snapshot and check resolve that symbolic ref, so a main-to-trunk default-branch change leaves them reading old main despite successful sync. A disposable real-Git reproduction cloned main with sync_one, changed the remote HEAD to trunk with a new manifest commit, and called sync_one with the new RemoteRepository metadata: origin/trunk updated, but default_commit still returned old main. The already-current fast path also returns without checking these remote refs.
- **Recommendation:** Under the existing repository lock, make the confirmed default remote-tracking ref and origin/HEAD current before returning success, including the already-current path. Preserve the user's checkout branch and files. Add a real-Git regression that changes the remote default, syncs an old-branch checkout, and verifies snapshot resolves the new default commit.
- **Fix with:** single-source-of-truth
- **Effort:** S


### STUF-78 · P2 · Include rendered OCI content in immutable generation identity

- **Area:** OCI publication
- **Where:** crates/myoci/src/publish.rs:163-207; crates/stuff-worker/src/oci_push.rs:341-376; crates/stuff-store/src/site.rs:208-233; crates/stuff/src/publish/republish.rs:400-436; crates/stuff-worker/entry.ts:525-559
- **Problem:** Both OCI publishers compute generation_id before adding catalog.json, index.html and llms.txt; public_url first affects output after hashing. Unchanged packages therefore keep their generation ID when the renderer or public origin changes, despite different immutable bytes. Native republish pulls the old generation and its verifier rejects replacement. The Worker either skips that same generation or rejects a retained generation's changed bytes. The native failure is established by the complete source trace; executing the unchanged Worker immutableText function with conditional storage confirms rejection and preservation of the original bytes. Full native/WASM publication was not executed.
- **Recommendation:** Share an OCI identity function that includes a generation-independent fingerprint of catalog JSON, HTML, llms.txt and origin alongside repository, blob and provenance inputs; reuse stuff-catalog's catalog_fingerprint normalization where applicable. Preserve old generation readability and immutable-write guards. Add a boundary regression for native and Worker publication that changes only origin or rendered bytes, obtains a distinct generation, and leaves the previous generation readable.
- **Fix with:** durable-state, single-source-of-truth
- **Effort:** M


### STUF-79 · P2 · Prevent stale native HTTP validators across generation changes

- **Area:** Native registry HTTP serving
- **Where:** crates/stuff-server/src/serve.rs:143-146,233-255; crates/stuff-http/src/condition.rs:19-22; crates/stuff-server/src/main.rs:225-230
- **Problem:** The native strong ETag contains only file size and mtime truncated to seconds. Different same-length generation files written or restored within one second therefore share a validator on /current/catalog.json. After activation, the old If-None-Match reaches NotModified and sends an empty 304. A real filesystem witness switched current between the different 13-byte bodies {"version":1} and {"version":2} with mtimes 1800000000100000000 and 1800000000900000000 ns; both map to the exact source expression's ETag "13-1800000000". The 304 path is source-traced; the Rust HTTP binary was not executed.
- **Recommendation:** Derive strong validators from immutable representation identity, such as generation plus object identity or a content digest, and use content-addressed keys for shared artifacts. Add a native HTTP regression that activates same-length, same-second files and requires 200 with new bytes for the old If-None-Match, while an unchanged representation still receives 304.
- **Fix with:** api-surface-and-module-boundaries
- **Effort:** S


### STUF-80 · P3 · Account for concurrent replacements in the unified render cache

- **Area:** Registry serving
- **Where:** crates/stuff-worker/entry.ts:278-320
- **Problem:** Concurrent cache misses await catalog loads after checking the same absent key, then each replaces that key and adds its full size without subtracting the prior entry. Executing the real unifiedIndex function with 16 concurrent requests for a 1 MiB page leaves one 1 MiB entry but charges 16 MiB. Subsequent HTML and llms requests evict each other although both fit within the budget. The byte overcount persists until the Worker restarts; the proof measures stored/accounted bytes and cache reuse, not latency.
- **Recommendation:** Recheck the key after catalog loading or subtract an existing value before eviction and insertion; share in-flight renders only if needed. Add a concurrency regression asserting accounted bytes equal stored bytes and two fitting pages remain reusable after a cold burst.
- **Fix with:** lifecycle-concurrency
- **Effort:** S


### STUF-81 · P3 · Align publishing service region validation with the gateway

- **Area:** Publishing configuration
- **Where:** crates/stuff/src/publish/service.rs:29-32,61-65; crates/stuff-worker/src/gateway.ts:16,24; docs/PUBLISHING.md
- **Problem:** Native service credentials accept a region from the file or STUFF_S3_REGION and sign with it, but gateway authentication requires auto in both the credential grammar and signature verification. Correctly signed requests using accepted non-auto configuration fail with 403. Calling the real gateway and SigV4 functions with otherwise identical valid credentials returned 200 for auto and 403 for us-east-1.
- **Recommendation:** Keep the service signing region fixed to auto and reject other configured values before network work, documenting that constraint. Add a client-configuration-to-gateway regression so every accepted region authenticates. If configurable regions are required later, change both ends together instead.
- **Fix with:** single-source-of-truth
- **Effort:** S
