# Registry failover

When the OpenOrange origin fails, public registry reads are served from an R2
replica by a route-attached Cloudflare Worker. The replica is a read path:
publishing, OCI pushes and every mutation stay on the origin and are
unavailable during a failover. Registry access and the replica's purpose are
described in [PUBLISHING.md](PUBLISHING.md#registry-access).

**Current state (2026-11-24):** the origin is the Stuff primary VM on
Threadripper and `oo-replica-sync` is stopped on Lisa and not installed on the
guest ([cutover record](roadmap.md#campaign-stuff-primary-on-threadripper)). No
new replica objects are written, so the Worker's fallback would serve stale
data. The Worker and its routes remain deployed; remove them with the
[remove steps](#remove) before relying on that fallback again.

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

`deploy/store-copy.py sync` copies the shared stores and current generation
names before moving `current`, so an interrupted sync never names a generation
the replica lacks; see
[PUBLISHING.md](PUBLISHING.md#copy-a-registry-bucket-to-another-store).

## Deploy

Deployment is done by the owner. The replica bundle build, bucket seed, sync
unit install, and Worker route deploy are in
[crates/stuff-worker/README.md](../crates/stuff-worker/README.md#read-replica)
and `deploy/failover-deploy.sh`; nothing here contacts Cloudflare or Lisa.
Do not add `domains` to the Worker config: a custom domain detaches the
hostname from the tunnel and the origin subrequest no longer resolves.

## Remove

Delete the Worker's routes (the deploy steps linked above, reversed) and the
Worker. With the routes gone, the eight hostnames resolve to the tunnel again
and the origin serves every request. Then stop and remove the sync:

```sh
doas /sbin/rc-service oo-replica-sync stop
doas rc-update del oo-replica-sync
```

The R2 replica buckets can be deleted once nothing reads them.
