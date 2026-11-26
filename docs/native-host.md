# Native registry host

Production Stuff runs the existing Worker entry (`crates/stuff-worker/entry.ts`),
its wasm planner and the publication coordinator (`src/coordinator.ts`) under
plain Node: `node:http` serves requests and `node:sqlite` holds coordinator
state. OpenOrange, Rivet and the Engine are not on the serving or publication
path. Cloudflare, the Lisa ingress, Versity and the bucket/version identities
are unchanged.

## Processes

The Threadripper guest `stuff-primary` runs three OpenRC instances of
`/etc/init.d/stuff-native` ([unit](../deploy/native/stuff-native.openrc)),
each configured by `/etc/conf.d/stuff-native.NAME`:

| Instance | Listener / control | Role |
| --- | --- | --- |
| `reader-a` | `127.0.0.1:8090` / `8091` | stateless reader; Lisa forwards `127.0.0.1:18493` here |
| `reader-b` | `127.0.0.1:8092` / `8093` | stateless reader; Lisa forwards `127.0.0.1:18494` here |
| `publisher` | `127.0.0.1:8094` / `8095` | coordinators and authority record in `/var/lib/stuff-native/main/state` |

Each instance runs `/opt/stuff-native/releases/<artifact>/native/main.mjs`
with `/opt/stuff-native/node-v26.13.1-linux-x64-musl/bin/node` as the
unprivileged user named by `stuff_user`: `stuff-native` for the publisher and
`stuff-reader` for both readers. Secrets live in root-owned 0640 env files
under `/etc/stuff-native/` (mode 0711, so no one can list it), and never in
argv: `main.env` (group `stuff-native`) holds the store owner's credential,
and `reader.env` (group `stuff-reader`) holds a store user whose bucket
policies allow only `GetObject`, `GetObjectVersion`, `ListBucket` and
`GetBucketLocation` on the six Stuff buckets. A reader therefore cannot
write the store or read `main.env`.

Lisa's Caddy sends every Stuff hostname, public and tailnet, to a primary
route with two health-checked upstreams (`recovery-routes.json`:
`"standby": ["127.0.0.1:18494"]`, `"health_uri":
"/.well-known/stuff-native/ready"`); `oo-stuff-native-tunnel` carries both
forwards. Caddy keeps the first healthy reader (`lb_policy first`, one-second
checks). Readers answer that path only for a loopback `Host`, so it is not
visible through Cloudflare.

## Reads and publication

A reader runs the entry with `STUFF_COORDINATOR_ENABLED=false` and read-only
bucket adapters: it reads `current` from the store and cannot seed, repair or
advance publication state. Tailnet requests to `stuff-publish` under `/_s3` or
`/_publication` are forwarded to the publisher; while the publisher is
unreachable the reader answers 503 with `Retry-After: 5`, which the native
publisher retries within its 15-minute window. Public ingress never reaches
publication routes (`X-OO-Ingress: public` is refused, and Caddy denies the
paths).

The publisher owns one WAL database per registry (`synchronous=FULL`,
exclusive lock, so a second publisher on the same directory exits). Each
coordinator serializes its whole operation, as the Durable Object did, behind a
bounded queue (256 waiting, 20 s admission deadline, then 503 with
`Retry-After`); a started operation always runs to completion before the next
one is admitted. A commit is durable before `sync()` returns, so the
acknowledgement contract is unchanged: an activation answers 200 only after its
row is committed and `current` is projected.

`state/authority.json` records who answers publication: `legacy` proxies the
routes unchanged to the old app, `native` uses the local coordinators. Changes
are compare-and-set on its `generation` through the control listener and are
written with fsync and an atomic rename. A change to `legacy` requires all native
coordinators to be frozen and idle, with no native publication request in flight.

## Control listener

Loopback only. `GET /identity` and `/ready` report release, source commit,
artifact SHA-256 (of `native/artifact.json`), Node version, role and authority;
`GET /metrics` reports process, event-loop, GC, HTTP, stream, S3 and
coordinator counters. `POST /withdraw` and `/restore` take a reader out of and
back into the ingress rotation. With the control token: `GET /coordinators`,
`GET /coordinators/REGISTRY/dump` (SQL only, never touches the store) and
`POST /coordinators/REGISTRY/import` (only while authority is `legacy`, only
into an empty coordinator). Every minute each instance also sends one
`stuff.native.runtime` application event with those counters to Stats.

Withdrawal persists across reader restarts in `/run/stuff-native/NAME/NAME.withdrawn`; the unit creates that directory for the instance user.
`STUFF_NATIVE_RUNTIME_DIR` changes the directory and `STUFF_NATIVE_NAME` names the instance.
Restore removes the file. A failed reader rollout attempts to restore the reader and names it
if restoration fails.

## Health

`GET /healthz` on `stuff.17166969.xyz` reports reader health. The same path on
`stuff-publish.17166969.xyz` reaches the publisher through the reader and requires tailnet
ingress. Both return JSON with `status`, `service`, `role`, `release`, and timed `checks`.
An `ok` or `degraded` result returns 200. A `down` result returns 503. Responses use
`Cache-Control: no-store` and are at most 4 KiB.

Readers check the current pointer in each registry, publisher reachability, and withdrawal or
draining. A partial store failure or unreachable publisher degrades the result. Losing every
store pointer or withdrawing the reader makes it down. Publishers check the same store
pointers, coordinator availability and load, and the readable authority record. Each check
has a deadline below 500 ms. Instances share concurrent checks and cache results for one
second. Withdrawal and draining change the reported status immediately.

## Build, release and rollout

```sh
cd crates/stuff-worker
pnpm run build:native      # build/native/app with native/artifact.json (file digests, source commit)
pnpm --dir orange install --frozen-lockfile # handoff rehearsal prerequisite
pnpm run test:native       # native tests, the handoff rehearsal, and the runtime suite on the native host
```

Copy `build/native/app` to `/opt/stuff-native/releases/<first 12 of the
artifact digest>/`, set `stuff_release` and `stuff_source_commit` in the conf.d
file, then roll each reader with
[`rollout-reader.sh`](../deploy/native/rollout-reader.sh) `a` and `b`: it
withdraws the reader, waits for its requests to finish, restarts it and
restores it, with no ingress reload. Restart the publisher with
`rc-service stuff-native.publisher restart`. The publisher cuts long `/_s3` GET streams after
30 seconds by default, while started coordinator operations finish. Set `stuff_drain_s` to
change the stream drain deadline. OpenRC does not force-kill a publisher that still has a
started operation. Publication requests may receive 503 with `Retry-After` during the restart.
A Caddy reload is not a zero-error
operation: it closes idle keep-alive connections, and a client that reuses
one at that moment sees a reset (observed 2026-11-26 05:02:28 and 05:12:02).

[`parity.mjs`](../deploy/native/parity.mjs) compares two origins byte for
byte over the live catalogs; [`window-probe.mjs`](../deploy/native/window-probe.mjs)
records every request of a change window from a client vantage.

## Writer handoff and recovery

[`handoff.mjs`](../deploy/native/handoff.mjs) moves publication authority in
eight journaled steps under an exclusive controller lease: prepare, freeze the
old authority, drain (export refuses while a lease lives), export, import and
compare canonically, fence the old app, compare-and-set the authority record,
admit. `--until STEP` stops after a step and a later run resumes from the
journal. Any failure before admission unwinds to the old writer, and the hold
is bounded below the publisher's retry window. The 2026-11-26 run is
journaled in `/var/lib/stuff-native/handoff-20261126/` with the five exports
and before/after store inventories.

Recovery is three separate operations:

- **Reader**: withdraw the failing reader; Caddy serves from the other one.
  Readers hold no state.
- **Code**: install the previous artifact in the conf.d files and roll the
  instances; the coordinator schema is the Durable Object's.
- **Authority**: after the native authority accepted any mutation, return to
  another writer only through a fenced reverse handoff (freeze, drain, export
  from the native publisher, import elsewhere). Never restart the old
  `oo-app.stuff`: its coordinator would rewrite `current` from stale state.

## Diagnosis

Request failures are logged as `request_failed` with method, host, path,
range/conditional flags and a bounded stack. Store responses are held until
their bodies are consumed: undici cancels the body of a collected fetch
Response, which on 2026-11-26 failed four public reads before it was fixed
(`b013ec18c6`).
