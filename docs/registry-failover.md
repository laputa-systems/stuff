# Registry failover

Every public registry hostname resolves Cloudflare → `cloudflared` tunnel →
Caddy on Lisa → the `stuff` Worker on OpenOrange/workerd → R2-compatible
bindings backed by the host's versitygw store. When Lisa's Engine fails, the
origin answers every registry with 500/530. A second origin keeps reads
available: a Cloudflare Worker that forwards to the origin first and serves from
an R2 replica only when the origin does not answer.

The replica is a read path. Publishing, OCI pushes and every mutation stay on
the origin and are unavailable during a failover.

## Shape

| Piece | Location |
| --- | --- |
| Failover entrypoint | `crates/stuff-worker/cloudflare.ts` |
| Failover decision (pure) | `crates/stuff-worker/src/failover.ts` |
| Cloudflare config | `crates/stuff-worker/cloudflare.config.ts` |
| Tests | `crates/stuff-worker/test/failover.test.mjs` |
| Replica copy | `deploy/store-copy.py sync`, driven by `deploy/replica-sync.sh` |
| Sync supervisor | `deploy/openorange/openrc/oo-replica-sync` |

The Worker is attached to the eight hostnames as **routes**, never as custom
domains. A custom domain would take the hostname away from the tunnel; a route
delivers the request to the Worker and leaves the hostname with the tunnel, so
`fetch(request)` on the route's own hostname is a subrequest that reaches the
origin. The Worker is named `stuff-failover` and declares no Durable Object and
no `COORDINATOR` binding, so it runs with `STUFF_COORDINATOR_ENABLED` unset and
`entry.ts` reads each bucket's `current` object (`entry.ts`, `readPointer`).

## The decision

Only `GET` and `HEAD` are eligible. For those the Worker forwards the request
to the origin and settles at response headers:

- any origin status below 500 — including 200, 206, 304 and 404 — is returned
  unchanged, body streaming, with no `x-stuff-served-by` header;
- an origin 5xx, a thrown network error, or no response headers within
  `ORIGIN_HEADER_TIMEOUT_MS` (8 s, `src/failover.ts`) serves the replica through
  `entry.ts` and adds `x-stuff-served-by: replica`.

A non-`GET`/`HEAD` request is forwarded unchanged and never replayed against the
replica, so a rejected write cannot be applied twice.

Bodies are never buffered: the decision is made on headers only, and the origin
response body is passed through unread when the origin answers. When the replica
takes over, the abandoned origin body is cancelled.

## What fails over

Served from the replica for the registry and blob hostnames:

- Cargo sparse index at `crates.`/`current/…`, `.crate` downloads at
  `crates-blobs.`/`blobs/…`;
- npm packuments at `npm.`/`current/…` and tarballs at
  `npm.`/`current/-/tarballs/<digest>.tgz` (shared `tarballs/` alias);
- PyPI simple pages at `pypi.`/`current/simple/…` and wheels at
  `pypi.`/`wheels/…`;
- the static mirror at `mirror.`/`current/…` and `SHA256SUMS`;
- pinned generation URLs (`/generations/<id>/…`) on every registry;
- OCI reads at `oci.`: `/v2/` ping, manifests, blob redirects, tag lists and
  referrers (all computed from the generation's `repository.json`);
- OCI blobs at `oci-blobs.`/`sha256/…`;
- the unified page `stuff.`/ and `stuff.`/llms.txt, rendered from the replica's
  generation catalogs.

## What does not fail over

Never forwarded to the replica, so it fails when the origin is down:

- every non-`GET`/`HEAD` request: `stuff publish`, OCI manifest puts and blob
  uploads, multipart sessions, and the `/_s3/` gateway;
- `stuff-publish.17166969.xyz`: it is not one of the eight routed hostnames, so
  publishing does not even reach this Worker;
- the coordinator paths `/_publication/…` (activate, rollback, GC): the replica
  runs with the coordinator disabled and has no Durable Object.

Best-effort, because they depend on what the last sync copied:

- **Replica lag.** `oo-replica-sync` copies every five minutes, so the replica
  trails the origin by up to that cadence plus the copy time. A generation
  published inside the window is not on the replica yet: the current pointer's
  previous target still answers, while a
  brand-new generation URL returns 404 until the next sync. Live publication
  therefore keeps working only while the origin does.
- **The unified page** renders only when every one of the five registry buckets
  has a `current` pointer naming a generation whose `catalog.json` the replica
  holds; `sync` moves each pointer last, so this is a lag effect, not a torn
  read.
- **OCI tag listing and referrers** are best-effort in the same sense: they are
  served from the replica generation, so they show the tags that generation
  recorded, not tags pushed after the last sync.

## Replica contents and sync ordering

The replica holds the same six buckets (`stuff-mycrates`, `stuff-mynpm`,
`stuff-mypypi`, `stuff-oci`, `stuff-mirror`, `stuff-oci-blobs`). Generations
live under `generations/<id>/`, the shared stores (`blobs/`, `tarballs/`,
`wheels/`, `manifests/`, `sha256/`) sit at the root, and `current` is a pointer
object naming a generation.

`deploy/store-copy.py sync SOURCE DEST --ledger FILE` copies the shared stores
and the generation `current` names, verifies the destination holds them, and
only then copies `current`. Other generations are not copied, so the replica
holds the generations that were current at some sync since it was seeded.
It refuses to move the pointer when the source names a generation with no
`generations/<id>/` objects, and it never deletes at the destination, so the
previously published generation stays readable while a newer one copies. An
interrupted sync leaves the destination pointer where it was, so the replica
never names a generation it does not hold.

## Deploy

Deployment is done by the owner. Nothing here contacts Cloudflare or Lisa.
Replace the placeholders with the account's own values.

1. Build the replica bundle (writes `build/failover/`):

   ```sh
   cd crates/stuff-worker
   pnpm install --frozen-lockfile
   pnpm run check:failover
   pnpm run build:failover
   ```

   The config also needs the Worker's entry module; `pnpm exec cf deploy` (or
   `cf build`) reads `cloudflare.config.ts`, so build it with the project's own
   `cf` dev dependency.

2. Create the six R2 buckets that back the bindings and copy them from Lisa:

   ```sh
   BUCKET=stuff-mycrates   # repeat for all six
   REPLICA_SYNC_ENV=/etc/openorange/replica-sync.env deploy/replica-sync.sh "$BUCKET"
   ```

   Destination credentials come from `/etc/openorange/replica-sync.env`
   (mode 0700 root), holding `STUFF_COPY_SOURCE_S3_*` (the store's S3 user) and
   `STUFF_COPY_DEST_S3_*` (the R2 replica token). They are never committed.

3. Install the sync unit on Lisa and start it:

   ```sh
   doas install -m 0755 deploy/openorange/openrc/oo-replica-sync /etc/init.d/oo-replica-sync
   doas install -d -m 0755 /opt/openorange/replica-sync
   doas install -m 0755 deploy/replica-sync.sh deploy/store-copy.py deploy/r2_common.py deploy/r2-multipart.py deploy/r2-put.py deploy/publication_service.py /opt/openorange/replica-sync/
   doas install -m 0700 replica-sync.env /etc/openorange/replica-sync.env
   doas rc-update add oo-replica-sync default
   doas /sbin/rc-service oo-replica-sync start
   ```

4. Deploy the Worker with its routes. The route list is expressed in
   `cloudflare.config.ts` as `<host>/*` for all eight hostnames; confirm the
   resolved triggers print those eight patterns before deploying:

   ```sh
   cd crates/stuff-worker
   pnpm exec cf workers triggers list          # or the account's route listing
   pnpm exec cf deploy
   ```

   Do not add `domains`: a custom domain detaches the hostname from the tunnel
   and the origin subrequest no longer resolves.

## Drill

Prove failover without touching the origin:

1. Run the tests, which drive an injected origin and a seeded replica:

   ```sh
   make worker-test
   ```

   They assert that 200/304/404 pass through untagged, and that 500/502/503/530,
   a thrown error and a header timeout serve the replica with
   `x-stuff-served-by: replica` for the cargo index, cargo blob, npm packument
   and tarball alias, PyPI simple page and wheel alias, mirror file and OCI
   blob.

2. In production, block the origin for one hostname at the Worker (for example
   by temporarily omitting one route) or stop `oo-app.stuff` on Lisa, then
   request a known path and check the header:

   ```sh
   curl -sS -D- -o /dev/null https://crates.17166969.xyz/current/registry/config.json
   # healthy: no x-stuff-served-by
   # origin down: x-stuff-served-by: replica
   ```

3. Verify replica freshness before relying on it:

   ```sh
   doas tail -n 20 /var/log/openorange/replica-sync.log
   ```

## Remove

Delete the Worker's routes (the four-step deploy above, reversed) and the
Worker. With the routes gone, the eight hostnames resolve to the tunnel again
and the origin serves every request. Then stop and remove the sync:

```sh
doas /sbin/rc-service oo-replica-sync stop
doas rc-update del oo-replica-sync
```

The R2 replica buckets can be deleted once nothing reads them.
