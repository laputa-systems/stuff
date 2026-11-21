# OpenOrange shared host stack (`deploy/openorange/`)

Runbook for the shared stack and applications declared in `apps.toml` on
`lisa` (Alpine 3.25, musl, x86_64, OpenRC, Docker, tailnet address
`100.68.104.43`). Stats, Stuff and Tansu use this ingress in production.
Stuff pulls are anonymous and public; publishing uses
`https://stuff-publish.17166969.xyz` over Tailscale. Discover production and
preview serve public reader/MCP traffic with separate private admin names.

## Components and pins

Everything is pinned by multi-arch **index digest** in `images.lock.json`; the
`linux/amd64` manifest digest is recorded next to it and `bin/pin-verify`
re-checks both against the registry (and the local image platform).

| Role | Image | Index digest | linux/amd64 manifest |
| --- | --- | --- | --- |
| Rivet Engine | `rivetdev/engine:3.1.2-rc.1` (slim) | `sha256:6e585002b700dd4d3630808eb67884aa15d1a602d83781984edac47023b6d40f` | `sha256:66de9f77cde47be3cd7af2c001e8083784f6b91ca58b0ab5d7878677cff5bd5d` |
| S3 store | `versity/versitygw:v1.11.0` (posix backend) | `sha256:8319a530d08d537426e2f855bae5280709795dc73a3f0c347973ef915d6343c5` | `sha256:5da5e2cd887eec7ae6ab1cd6f5099207c754964358ab6351da2a9d6b80507e4e` |
| Caddy builder | `caddy:2.11.9-builder-alpine` | `sha256:646fee578e680989ca5c7fd1ce6f1de574d19fd71ef2221810cc0510a9f40c86` | `sha256:29f98311e17e583811355fa62cc080f71d6f3aa19cf09a9e1494d30579f8bebf` |
| Caddy runtime | `caddy:2.11.9-alpine` | `sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0` | `sha256:fc9cbc100585871d18d4e451cca7021785c90a7006087427ae5ceb3e4efe6424` |
| Identity base | `python:3.14-alpine` | `sha256:5862d971d1f0ae26b258cefa4e893556b1d3aba81bd2ff30888704ad378bab67` | `sha256:76c65fc8c52c4d375e958298d9f66198b8fb6b06416c0e5500bf710c19cbaa77` |

Locally built (never pulled): `openorange/caddy:2.11.9-cf0.2.4` is
`xcaddy build v2.11.9 --with github.com/caddy-dns/cloudflare@v0.2.4` (module
list contains `dns.providers.cloudflare`; binary sha256
`d46ee78e53e3362c084968808c6868c6631ead385d626c0be61afeb88624c8e4`, file cap
`cap_net_bind_service=ep`) and `openorange/identity:1` (`identity/identity.py`).
`ingress/Dockerfile` and `identity/Dockerfile` carry the base digests as ARG
defaults; `pin-verify` fails if they drift from the lock.

**Engine version.** The apps pin open-orange 1.0.2 / rivetkit 3.1.2-rc.1. The
Engine image `3.1.2-rc.1` exists on Docker Hub and, like the
`@rivetkit/engine-cli` 3.1.2-rc.1 binary, reports `Rivet 3.1.1`
(`rivet-engine --version`, `/health` -> `"version":"3.1.1"`). `3.1.1` reports
the same string, so the version string cannot tell them apart; the matching
release candidate was chosen. A release candidate is in production position:
re-evaluate when `3.1.2` ships. Rivet's `--runtime-info` and `/health` report
`architecture: v3`. rivet-services ships GNU binaries only; the Engine image
and every Orange app image are Debian/glibc containers, and nothing glibc runs
on the Alpine host itself.

## S3 store selection (empirical)

`bin/s3-conformance` (standard-library SigV4) probes path-style addressing,
multipart completion and ETag format, `If-None-Match: *` / `If-Match`
conditional PUT, an 8-way concurrent create race, ListObjectsV2 pagination and
ranged GET. Raw results: `tests/s3-backend-results.json`.

| Check | Garage v2.5.0 | versitygw v1.11.0 (and the deployed stack) |
| --- | --- | --- |
| Path-style PUT/GET | pass | pass |
| Multipart 3 parts, completes; ETag `md5(md5s)-3` | pass | pass |
| `If-None-Match: *` on existing key -> 412 | **fail (200, value overwritten)** | pass (412, value unchanged) |
| `If-Match` stale ETag -> 412 | **fail (200)** | pass |
| `If-Match` on absent key | **fail (200)** | pass (404) |
| 8 concurrent `If-None-Match: *` creates | **fail (8 x 200)** | pass (1 x 200, 7 x 412) |
| `If-None-Match: *` on CompleteMultipartUpload | fail (info) | pass (412) |
| ListObjectsV2 pages (max-keys 10 over 25), delimiter, start-after | pass | pass |
| Ranged GET `a-b`, `a-`, `-n`; unsatisfiable -> 416 | pass | pass |
| `GET ?partNumber=N` | fail (info) | fail (info, 400) |

Garage silently ignores the conditional headers, so it cannot back registries
that publish with conditional writes. The unreleased Garage `main` image
(`99923a87`) answered 500 on a freshly initialised cluster (`Unable to decode
entry of bucket_v2`) and was not pursued. SeaweedFS was not tested because
versitygw passed. **versitygw** was chosen: posix backend (plain files and
xattrs on ext4), `--fsync`, bucket versioning directory enabled, per-app IAM
users that own their buckets. The deployed stack run (key of the `demo` app)
also proved isolation: the same key gets `403` on PUT, GET and LIST of
`stuff-oci`. Open-orange maps each R2 binding onto this store through
`ORANGE_R2_<BUCKET>_S3_*` variables, which `oo secrets` writes; an R2 `onlyIf`
create through Orange against this store returned `stored:false` on the second
create.

App `vars` are public Worker bindings stored in `apps.toml`; secret names
are declared in `secrets` and their values live only in the root-owned
`apps/NAME.extra.env`. Names cannot overlap or replace runtime credentials.
`oo secrets` derives the Worker binding list from both declarations.
`worker_s3 = true` explicitly exposes the app's own derived S3 credentials
to its Worker. Stuff uses this for its streaming publication gateway. Other
apps receive only their R2 adapters, with no raw store credentials in Worker bindings.

Stuff sets `versioning = true` for its six buckets. Provisioning enables and
verifies S3 versioning; it never suspends versioning on an existing bucket.
The publication coordinator holds the exclusive GC lease, checks retained
manifests and OCI blob inventories, and persists the exact object version IDs
before deleting them. A failed or expired deletion can be retried without
deleting a later upload of the same content. Activation rejects a shared object
whose current version was retired; a newly uploaded version can be published.
Generation retirement remains permanent, so historical URLs are never reused.

## Topology

An optional split-DNS resolver is available for public names. A digest-pinned CoreDNS 1.15.0 container
binds UDP and TCP port 53 only on Lisa's tailnet address. It derives the
names from `public_hostnames`, answers their A records with the ingress address,
and returns empty successful AAAA answers so browsers use the private ingress.
Queries below those names, including ACME TXT checks, fall through to public
resolvers. Other domains are refused. Tailscale's restricted nameserver routes
can name this resolver to reach the private listener by public hostname.
Discover instead uses `hq-admin.` and `hq-preview-admin.` for private
administration. Stuff uses the separate private publishing hostname
`stuff-publish.17166969.xyz`, so its publishers do not require split DNS.
The resolver is stateless and stays up during application data fencing.
`bin/oo dns-routes` prints the exact JSON map for a Tailscale
`PATCH /api/v2/tailnet/-/dns/split-dns`; a partial update preserves unrelated
DNS routes and global nameservers. Preserve the old values before applying it.

CoreDNS is Apache-2.0 and ships as one Go binary in the upstream image; no
language package closure is installed on Lisa. The pinned version is 1.15.0;
its fixes are listed in the
[release record](https://github.com/coredns/coredns/releases/tag/v1.15.0).
Only UDP/TCP DNS, templates and forwarding are enabled; there are no custom
transport listeners, query logs or dynamic update endpoints.

```
tailnet client --443--> [host net] oo-ingress (Caddy, 100.68.104.43:443)
                          |  unix socket /run/openorange/identity/identity.sock
                          |      oo-identity (python, --network none) -> tailscaled LocalAPI whois
                          |  http://172.29.80.2x:8080
oo-tunnel (cloudflared) --> 127.0.0.1:18480 (public listener, same Caddy)
                          v
        docker network `openorange` 172.29.80.0/24, --internal (no route off the host)
        oo-store .10:7070   oo-engine .11:6420   oo-app-<name> .20+:8080
```

* The private bridge `oo0` uses `--internal`. Apps default to this network
  alone. Discover and its preview additionally use the NAT bridge
  `openorange-egress` through explicit `internet = true` app configuration,
  so source watches and image capture can reach public sites. Their source
  fetcher rejects private, tailnet and reserved DNS answers and pins each
  approved address for the connection. Stats, Stuff, Engine and the store
  remain on the private bridge alone. No container publishes a port (`docker ps` shows none; `bin/health`
  asserts it). Engine API, store S3 and app listeners exist only on
  `172.29.80.0/24`; the store admin API is a unix socket in
  `/run/openorange/store-admin`.
* **Why Caddy uses host networking.** Measured on `lisa`: a container publishing
  `100.68.104.43:18999` saw the Mac's request (100.107.2.101) as source
  `172.17.0.1`; Docker's published-port path hides the tailnet peer, so
  `whois` could not work. Host networking gives Caddy the true peer address,
  lets it bind exactly `100.68.104.43:443` (no `:80` listener at all) and reach
  Tansu on `127.0.0.1:3001`; it reaches app containers by their static
  addresses (the host routes to bridge addresses, including `--internal`
  networks). Caddy and the sidecar run as uid 10001 with every capability
  dropped except `NET_BIND_SERVICE` on Caddy.
* Engine storage (`/var/lib/openorange/engine/{log,objects}`, Rivet
  `file_system` tier, its own token) is separate from application buckets
  (`/var/lib/openorange/store/...`, per-app S3 keys). Rivet's S3 tier on this
  store was tried and failed twice identically (see Deviations).
* **Apps**: each `[apps.NAME]` in `apps.toml` gets its own Rivet namespace, S3
  key and bucket set, gateway secret, container and OpenRC instance
  (`oo-app.NAME`). Adding or restarting one never restarts another.
  Pool names are not configurable: open-orange 1.0.2 hard-codes `default`
  (Durable Objects) and `services`; both are created in every namespace and
  isolation is the namespace.
* Admin token: `/etc/openorange/engine.env` (0600 root, never printed). Every
  Orange app container needs it to connect (`RIVET_TOKEN`); Rivet 3.1.x has no
  static namespace-scoped node credential (scoped JWTs expire within a day and
  were not tested for node connections). A compromised app container can
  therefore act on other namespaces; the container boundary, not the token, is
  the isolation.

### Ingress contract

For every enabled hostname in `apps.toml` (`bin/oo render --stdout` prints the
whole Caddyfile) Caddy:

1. deletes client `Tailscale-*`, `Stats-Gateway-Secret`, `Stats-Tailnet-Identity`,
   `X-OO-Peer`, `X-OO-Ingress`, `X-Forwarded-*`, `Forwarded`, `X-Real-Ip`;
2. `forward_auth` to the sidecar with `X-OO-Peer: <accepted connection ip:port>`;
   the sidecar answers `200` + `Stats-Tailnet-Identity: user:<login>` or
   `tags:<tag>,<tag>` (sorted, `tag:` prefix kept), `403` for anything that is not
   a tailnet peer, `503` if tailscaled is unavailable (fail closed);
3. proxies with `Stats-Gateway-Secret: <per-app secret>`, the identity header
   copied only from the sidecar response, `X-OO-Ingress: tailnet`, `Host`
   unchanged (Tansu's passkey origin checks), and Caddy's own
   `X-Forwarded-For` (the true peer).

There is no email allowlist. A local process on `lisa` is the node's own user.
Apps whose image is not deployed yet answer `503 app not deployed` after the
identity check.

### Public listener

Declared in `apps.toml`: `[ingress.public] bind = "127.0.0.1" port = 18480`
(validation rejects any non-loopback bind) and per app `public_hostnames`
(subset of `hostnames`) and `public_deny_paths` (default `["/admin"]`: the path
and `path/*`). Discover is defined as `discover` (`hq.`, `research.`) and
`discover-preview` (`hq-preview.`, `research-preview.`), each with its own
namespace, bucket and secret. On the public listener Caddy serves plain HTTP on
loopback only, with no sidecar and **no gateway secret**; it strips the same
client headers, sets `X-OO-Ingress: public`, answers `404` for `/admin`,
`/admin/*` and normalisation variants (case, `//`, `./`, `../`, `%61dmin`,
`%2f`, `;params`), and `404` for any other Host. The same hostnames on the
tailnet listener serve everything including `/admin`, with identity. Apps must
treat "no valid gateway secret" as anonymous public traffic and must use
`Cf-Connecting-Ip` for the client address on that path.

The outbound-only `oo-tunnel` connector maps the eight public Stuff names
and four prepared Discover names to `http://127.0.0.1:18480`. Stuff DNS
points at this tunnel, as do the four Discover names. Discover's private
administration uses separate `hq-admin.` and `hq-preview-admin.`
names that resolve directly to Lisa. ACME uses DNS-01 for both public and
private names. A route-attached Cloudflare Worker forwards the Stuff names to
this listener and serves reads from an R2 replica when the origin does not
answer; [registry failover](registry-failover.md) covers what fails over, the
replica sync unit, and how to remove it.

### Tansu

`tansu.17166969.xyz` is an `[apps.tansu]` `kind = "native"` entry: tailnet
listener, identity, upstream `127.0.0.1:3001`, `Host` untouched. The native
service remains on Lisa. DNS now resolves to the tailnet address; the old
Cloudflare tunnel and container were retired after preserving their
configuration. The passkey RP hostname is unchanged. The login page and
login-options request pass; a user completing a hardware passkey login
remains unverified.

### Hostnames (tailnet listener; all get DNS-01 certificates)

`stats.` (Stats); `stuff-publish.`, `stuff.`, `crates.`, `crates-blobs.`, `npm.`, `pypi.`, `oci.`,
`oci-blobs.`, `mirror.` (Stuff); `hq.`, `research.`, `hq-admin.` (Discover);
`hq-preview.`, `research-preview.`, `hq-preview-admin.` (Discover preview); `tansu.` (Tansu), all
under `17166969.xyz`.

### TLS

`[ingress].tls = "internal"` (rehearsal): Caddy's internal CA, certificates
for the exact hostnames; clients use `-k` or trust
`/var/lib/openorange/caddy/data/caddy/pki/authorities/local/root.crt`.
`tls = "acme"`: DNS-01 through `caddy-dns/cloudflare`, token from
`/etc/openorange/cloudflare-dns.env` (`CF_API_TOKEN=...`, 0600 root, passed with
`--env-file`, never in argv). Production uses ACME with issued certificates.
The `acme` Caddyfile validates against the built binary, and `oo run-args ingress`
refuses to start in `acme` mode while the file is missing. Switching: write the
token file, set `tls = "acme"`, `bin/oo render`, `rc-service oo-ingress
restart`. `bin/oo render --stdout --tls acme` previews it.

## Layout

| Path | Contents |
| --- | --- |
| `/opt/openorange` | this directory (`bin/sync-code HOST` copies it) |
| `/etc/openorange` (0700 root) | `engine.env`, `store.env`, `ingress.env`, `cloudflare-dns.env` (owner), `apps/NAME.env`, `apps/NAME.image`, `apps/NAME.extra.env`, rendered `engine/config.json`, `ingress/Caddyfile`, `overlay.toml` (rehearsal only) |
| `/var/lib/openorange` | `engine/{log,objects}`, `store/{data,versions,iam}`, `caddy/{data,config}`, `backups/`, `restore/` |
| `/var/log/openorange` | `store.log engine.log identity.log ingress.log app-NAME.log` |
| `/run/openorange` | `identity/`, `caddy/`, `store-admin/` sockets (recreated at start) |
| `/etc/init.d/oo-{store,engine,identity,ingress}`, `oo-app[.NAME]` | OpenRC units |
| `/etc/conf.d/oo-ingress`, `/etc/periodic/daily/oo-logrotate` | generated ordering, log rotation |

`bin/`: `oo` (validate, run-args, secrets, prepare, render, network,
provision, set-image, remove, reload-ingress, wait), `install`, `install-app`,
`build-images`, `build-orange-app`, `health`, `drain`, `disk-usage`, `backup`,
`restore-rehearsal`, `logrotate`, `pin-verify`, `s3-conformance`, `sync-code`.
`tests/`: `client-checks.sh` (from a tailnet client),
`public-listener-checks.sh` (on the host), `s3-backend-results.json`;
`identity/test_identity.py` (unit tests with a fake LocalAPI; run
`cd identity && python3 -m unittest`).

### Supervision design

Each unit is an OpenRC `supervise-daemon` running `docker run --rm` in the
foreground, with the argument vector from `oo run-args` (single source:
`apps.toml` + `images.lock.json`). Chosen over Compose because `docker compose`
is not installed on `lisa`, and installing it would add a host package and a
second supervisor; a foreground CLI lets OpenRC own restart, ordering and
`rc-service ... stop` (the CLI proxies SIGTERM to the container; each unit has
`retry TERM/<n>/KILL/5`, the Engine 150 s). `start_post` blocks until the
service answers; on failure it stops the supervisor and removes the container
(verified: an app with a bogus image failed after 90 s with no supervisor or
container left). Output goes to `/var/log/openorange/*.log` (container log
driver `none`); `bin/logrotate` (daily, copy-truncate, 5 x gz over 20 MiB).
Containers run `--read-only`, `--cap-drop ALL`, `no-new-privileges`, non-root
where the image allows (store, engine, ingress, identity, apps).

`oo-dns` and `oo-ingress` bind the tailnet address, which tailscaled assigns
some seconds after OpenRC starts it at boot. Both units order after
`tailscale`, and `oo prepare` waits up to 120 s for the address before
starting either listener. Without that wait, `oo-dns` failed its readiness
check on the 2026-11-18 reboot and stayed stopped.

Every container runs under the cgroup v2 parent `oo.slice` (`--cgroup-parent`,
one child slice per role). Once a unit passes its checks, `oo prepare` gives
`oo.slice` `cpu.weight 10000`, `memory.min` 6 GiB, `memory.swap.max 0`, and
`io.latency` with a 10 ms target on the whole disk that holds `state_dir`.
Each later unit start reapplies them. Other containers and host builds still
run, but they yield to the stack instead of starving it. On 2026-11-21 three
capsule containers and a host `cargo test` held Lisa at load 16–21 with the
default weight of 100. The Engine's storage refused commands as
`command_capacity`, its worker lease expired waiting on the object store,
and the registries returned 500 from 05:02 to 05:24 UTC. The reservation was
applied live the same night; Threadripper's standby VM passed a load-76
drill with the same settings. The remaining Engine reconnect storm is
STUF-102.

## Install (on `lisa`, as root; `doas` is the privilege tool there, not `sudo`)

`doas` does not search `/sbin`: spell out `/sbin/rc-service` or work in a root shell.

```sh
bin/sync-code lisa                            # from a workstation
ssh lisa doas /opt/openorange/bin/install     # units, secrets, network, builds, render, rc-update
ssh lisa doas /sbin/rc-service oo-store start
ssh lisa doas /sbin/rc-service oo-engine start
ssh lisa doas /opt/openorange/bin/oo provision    # S3 users/buckets, Rivet namespaces/pools
ssh lisa doas /sbin/rc-service oo-identity start
ssh lisa doas /sbin/rc-service oo-ingress start
ssh lisa doas /opt/openorange/bin/health
```

Prerequisites already on the host (no package was installed): `docker`
(29.9), `python3` 3.14 (needs `tomllib`, >= 3.11), `rsync`, `curl`, `openssl`.
`install` pulls and builds images (network needed once; the Go module download
for the Cloudflare plugin).

## Add an app

1. Add `[apps.NAME]` to `apps.toml` (namespace, `ip`, `port`, `hostnames`,
   `buckets`, optional `memory`, `cpus`, `secrets`, `public_hostnames`).
   `bin/oo validate` rejects unknown keys, duplicate hostnames/IPs/buckets and a
   non-loopback public bind.
2. Build the image in the app's own repo/CI. For a Worker:
   `bin/build-orange-app WORKER_DIR IMAGE HOST [TAG]` runs
   `open-orange@1.0.2 deploy --dry-run --outdir`, copies the context and runs
   `docker build --platform linux/amd64` on the host. The generated Dockerfile
   uses an unpinned `node:24-slim` base: pinning is the app repo's decision.
3. `doas /opt/openorange/bin/install-app NAME IMAGE`: provisions namespace,
   pools, S3 key and buckets, writes `/etc/openorange/apps/NAME.env`, creates the
   `oo-app.NAME` instance, starts it, re-renders and reloads Caddy.
   Other apps are not restarted. Roll an app: build, `oo set-image NAME IMAGE`
   (previous kept as `NAME.image.prev` for rollback), `rc-service oo-app.NAME restart`.
   `NAME.image` is a versioned JSON deployment record: image and monotonically
   increasing node version are replaced atomically and fsynced together.
   Re-selecting the same image is idempotent. To roll back, pass the previous
   record's `image` to `set-image`; this advances the node version even when
   the application image moves backward. Existing plain-text image files are
   read as version zero and upgraded on the next `set-image`.
4. The app environment: `RIVET_ENDPOINT RIVET_NAMESPACE RIVET_TOKEN`,
   `GATEWAY_SECRET` (declared in `ORANGE_WORKER_SECRETS`, so it appears as a
   Worker secret binding), `S3_*`, and `ORANGE_R2_<BUCKET>_S3_*` for each R2
   binding. Extra secrets: list the names in `secrets = [...]` and put the
   values in `/etc/openorange/apps/NAME.extra.env`. `RIVET_NODE_VERSION` comes
   from the app deployment record, so Rivet can drain actors across deploys.
   The OpenRC unit sends TERM, permits 30 seconds for the container to drain,
   then kills it; clients must retry interrupted requests. Verify application
   state after every deployment rather than treating container readiness as
   proof of acknowledged-write durability.
5. Remove: `oo remove NAME [--purge-store]`. Rivet 3.1.x has no namespace
   delete, so the namespace and the app's Actor state remain in the Engine
   volumes.

## Operate

* **Health / readiness:** `bin/health [--json]` (root). Checks network, each
  OpenRC service and container, store and Engine health, unauthenticated Engine
  rejection, namespaces/pools, app node connections, sidecar behaviour (own
  address resolves, non-tailnet peer is 403), every ingress hostname, public
  listener `/admin` 404, TLS certificate, that no stack port listens on a host
  interface, that 443 is bound only on the tailnet address, that no container
  publishes a port, free space (Engine refuses to start below 10% / 4 GiB) and
  backup age. Exit 1 on any FAIL.
* **Drain / start:** `bin/drain` stops the tunnel, ingress, dashboard and telemetry
  bridge before apps, identity, Engine and Store. Failed app discovery aborts;
  failed stops or services that remain running make it return nonzero.
  `bin/drain --start` starts dependencies first and reports failures; `--apps`
  stops the tunnel, ingress, bridge and apps. OpenRC dependencies make
  `rc-service oo-engine restart` bounce the apps and `oo-identity restart` bounce ingress.
* **Logs:** `/var/log/openorange/*.log` (root-readable); Caddy writes access
  logs without request or response headers.
* **Disk accounting:** `bin/disk-usage [--json]`: Engine log, Engine objects,
  each app's bucket set (incl. versions), store total, caddy, backups, restore
  rehearsals, logs, free space, Docker.
* **Backup:** `bin/backup [--dest DIR] [--keep N] [--no-restart]` pre-copies
  Engine and Store while applications run, then drains the stack and verifies
  writer containers are absent. It reconciles every file by checksum before copying
  configuration, app declarations and image pins. The live pre-copy alone is unusable. Stats and private ingress restart
  before unrelated apps so host agents can drain their four-minute queues.
  Online copies use Linux idle I/O priority and reduced CPU priority. Application
  readiness requires HTTP 200 with the declared Host and trusted local gateway
  headers; Stats reads its stored host list rather than its process health route.
  It checksums the final copy and retains a positive number of backups. Failed
  drains or copies and SIGTERM/SIGINT restart services that were running before
  the fence, including the tunnel only if it was running. `--no-restart` leaves
  services stopped only after a successful copy; failures still restart them.
  Backups contain secrets and must remain protected.
* **Restore rehearsal:** `bin/restore-rehearsal [BACKUP] [--app A --probe PATH
  --expect TEXT] [--headers-file FILE] [--purge]` verifies backup checksums,
  copies Engine and Store data, versions and IAM, and starts both on a separate internal Docker network
  at private addresses with the backed configurations and pinned images. It checks backed
  namespaces and pools and streams every object in each declared bucket, reporting
  counts, bytes and an aggregate SHA-256. Each served object's SHA-256 and size
  must match the corresponding checksummed file in the copied Store data. With
  an app probe it uses the backed app image and environment, directs S3 and Engine
  to the copies, disables application events, and sends the app's host and a
  synthetic gateway identity. Probe output is limited to status, byte count and
  SHA-256; responses over 1 MiB fail. An optional root-protected `KEY=value`
  headers file supplies operator authentication. Containers are removed afterward;
  `--purge` also removes the copied data. `--soak-s N` keeps the copy running
  after it passes and probes the app every 10 s for N seconds; `--restart-every-s M`
  restarts only the Engine every M seconds and waits for its health. Each restart
  and failed probe prints a JSON line, and a final `soak` line reports probe count,
  p50/p99/max latency, restarts and the slowest recovery. The run fails if a
  probe fails more than 120 s after the last restart, or if an Engine does not
  recover within 120 s. `--engine-image sha256:ID` runs a candidate Engine. Older backups without checksums for
  `apps.toml` and `images.lock.json` cannot be rehearsed by this command.
  A real restore copies the data into live directories with the stack stopped.
* **Upgrade:** (1) `bin/backup`; (2) `bin/pin-verify --resolve` after choosing
  the new tags in `images.lock.json` (review the diff), `bin/pin-verify`;
  (3) `bin/sync-code`, `doas bin/build-images` for Caddy/identity;
  (4) Rivet requires a full stop for the first upgrade: `doas bin/drain`, pull
  the new Engine/store images, `doas bin/drain --start`, `bin/health`;
  (5) upgrade the Engine before the apps' rivetkit (apps behind the Engine are
  accepted; newer SDKs may need the newer Engine); (6) `bin/restore-rehearsal
  --app ... --probe ...` from the pre-upgrade backup if anything looks wrong.
  Caddy-only changes: `oo reload-ingress` (validates, graceful reload).

### Recovery routes

Put active recovery routes in the root-only
`/etc/openorange/recovery-routes.json`. The object maps application names
to route objects. Stage updates by writing a mode-0600 sibling file and
renaming it into place. Preview with `oo render --stdout`, validate the
candidate in the ingress container with the matching environment, then
run `oo reload-ingress` and probe each changed route.

- A reader has `"mode": "reader"`, a private IPv4 `upstream` with a port,
  `hosts` drawn from the application's public hostnames, and a
  `deny_paths` array of extra excluded prefixes. The app's existing public
  path exclusions also apply to the reader. Only GET and HEAD go to it.
  Set `snapshot_at` to a UTC timestamp to emit
  `X-<App>-Recovery-Snapshot`. Keep reader credentials scoped to serving.
- A writer has `"mode": "writer"` and a private IPv4 `upstream` with a
  port. It applies to a tailnet-only Orange app. The renderer uses
  `GATEWAY_SECRET` from the root-only `apps/NAME.recovery.env` and
  preserves tailnet identity verification. Startup and image selection
  refuse the local app while this declaration is present. The read-only
  `oo deployment NAME` response includes `recoveryWriter` with the
  configured upstream while the fence is active.

Before activating a writer route, stop the local app and confirm its
container exited. Run an authenticated write and readback after reload.
Keep the declaration in place throughout failback preparation. After a
write reaches the standby, fence it and transfer and verify its newest
data before removing the declaration or enabling the local app. A reader
can be retired by deleting only its entry after testing the primary. Reload,
probe the adjacent applications, then stop that reader.

`bin/health` reports Engine liveness, runner registration and application
readiness separately. The app check uses the same authenticated request
as OpenRC startup, requires HTTP 200, and includes a structured upstream
error code when one is present. A failed primary still appears as failed
when ingress is serving a reader route; probe that route separately. An app
fenced by a writer route has no local container, so health skips its
service, container and runner checks and instead sends the readiness
request to the writer upstream with `apps/NAME.recovery.env`. The platform
bridge's runtime-pin check reports WARN while its source app is fenced.

## Engine starvation from the HPET clocksource (2026-11-18)

**Symptom.** From about 02:28 UTC every Engine storage command missed its
deadline (`request_deadline_exceeded`). The Engine refused runner connections
because "storage could not register", `oo-app.stuff` failed its 30 s
registration wait and crash-looped, and Discover logged connection failures.
Restarting the Engine did not help. Public registry reads continued through
the separate `oo-stuff-read-*` reader.

**Cause.** The kernel had demoted the TSC and fallen back to the HPET
clocksource; `tsc` was no longer in `available_clocksource`. Every clock
read became a system call: 3.1 to 7.4 µs per read from Python, against about
50 ns normally. The Engine's Tokio runtime reads the clock constantly. Its
eight workers ran at about 600% CPU, 261,000 `clock_gettime` calls in 5 s
under `strace -c`. The host showed 0% idle with 65% system time. The
clocksource watchdog can wrongly mark a stable TSC unstable when the host is
overloaded. A demotion lasts until reboot, and writing `tsc` to
`current_clocksource` is refused.

**Diagnose.**

```sh
cat /sys/devices/system/clocksource/clocksource0/current_clocksource   # must be tsc
cat /sys/devices/system/clocksource/clocksource0/available_clocksource
doas timeout -s INT 5 strace -c -f -p "$(docker inspect -f '{{.State.Pid}}' oo-engine)"
```

A healthy Engine does not show `clock_gettime` in the profile at all.

**Fix.** The usr Alpine provisioner (`host/alpine` in joshuarli/usr) adds
`tsc=nowatchdog` to `GRUB_CMDLINE_LINUX_DEFAULT` on x86_64 CPUs with
`constant_tsc` and `nonstop_tsc` and regenerates the GRUB menu. It also
installs `amd-ucode`, runs the `performance` CPU governor at boot, and sets
BBR with fq, 7.5 MB socket buffers and `vm.swappiness = 10`. Lisa was
drained with `bin/drain` and rebooted. Afterwards the clocksource was
`tsc`, a clock read cost 138 ns, the Engine dropped from 430 to 600% CPU to
about 65 to 110%, host load fell from 12 to 3, and `oo-app.stuff` registered
with 1/1 nodes connected.

**Follow-ups found on the reboot.**

- `oo-dns` started before the tailnet address existed; see
  [Supervision design](#supervision-design).
- The hand-made `oo-stuff-read-app` crash-looped: its `/app/.open-orange`
  tmpfs came back root-owned, and the container runs as uid 1000. It was
  recreated once with `uid=1000,gid=1000` on that tmpfs. After byte-identical
  responses from the primary and the reader on nine read paths, the `stuff`
  reader route was retired by the procedure in
  [Recovery routes](#recovery-routes). Both reader containers are stopped
  with restart policy `no`. The pre-change routes file is
  `/root/recovery-routes.json.pre-stuff-retire` on Lisa.
- The Engine's `actor_inbound` envoy queue still reports 128 of 128 every
  30 s. Before 2026-11-18 this warning appeared once or twice a day. It
  started during the outage and persists after the reboot while all apps
  are idle. See
  [Engine queue saturation](#engine-queue-saturation-after-the-outage).

### Engine queue saturation after the outage

After the reboot, with every app container near 0% CPU, the Engine still
used 65 to 110% CPU, almost all in user space. Its `actor_inbound` envoy
queue stayed at exactly 128 of 128. Two metric samples 30 s apart from
`http://172.29.80.11:6430/metrics` showed:

| Metric | Change in 30 s |
| --- | --- |
| `rivet_depot_alarm_candidates` | 33, unchanged |
| `rivet_depot_alarm_discovery_rows_total` | +660 (about 22 rows/s) |
| `pegboard.actor.alarm` commands completed (`rivet_depot_client_command_duration_seconds_count`) | +22 (about 0.7/s, 120 ms mean) |

The candidate count does not fall, so this is not a backlog draining. The
same alarms are rediscovered and redelivered continuously. Discover's
envoy also renewed its heartbeat about a sixth as often as the other apps'
(`rivet_pegboard_envoy_index_upserts_total`: 135 against 730 to 820), and
Discover, Discover Preview and Discover Wine logged the most
`actor.not_found` responses. The working hypothesis is alarms scheduled for
actors that were destroyed or lost during the outage. Those alarms keep
retrying against a missing actor and hold one envoy's inbound queue full.
This is not yet proven. The Engine log line does not name the envoy, and no
route that lists alarm targets has been verified.

`rivet_state_machine_durable_stale_alarm_deliveries_total{machine="actor"}`
reached 15,975 about 70 minutes after boot, roughly 4 per second. In the
pinned source (`engine/packages/state-machine-durable/src/metrics.rs` at
`e5ed391`) a stale delivery is an alarm for a revision that is no longer
armed, acknowledged without firing. Acknowledged alarms do not retry, so
the rate means actor state machines keep re-arming and invalidating their
alarms. That fits the boot-time warnings "failed to send stop command; the
stop timer resends it" and "actor stop went unanswered past the stop
threshold". Discover's runner also alternated between connected and absent
in `bin/health` within an hour of the reboot.

The public actor listing (`/actors?namespace=NS&name=NAME`) omits lifecycle
state. The Engine's lifecycle warnings do name actors. Since the reboot, the
actor with the most "did not become ready before the gateway deadline"
warnings is `lv9klsjvpn1runcelvimxtw7s2bl00` (41), followed by other
`stats-prod` actors, all resolved with `/actors?namespace=stats-prod&actor_ids=ID`.

**Attribution.** The cycling actors belong to `stats-prod`. Stats is fenced
by its writer recovery route and served off-host, so `stats-prod` has no
runner on Lisa (`/pools/default/nodes?namespace=stats-prod` returns no
nodes). Its actors remain in Lisa's Engine: one `installation-917ceba9`
and 14 `observation-store-13f29dce` actors. `/actors/names` returns no names
for the namespace, so query by name. With no runner, their alarms cannot
fire, wake attempts time out and stop commands go unanswered, which re-arms
the alarms. Restarting Discover on 2026-11-18 at 21:16 left the stale
alarm rate unchanged at about 3 per second. The queue warnings began the
day Stats moved to its recovery writer.

Do not destroy these actors to stop the loop. They are Lisa's copy of the
Stats data, which the writer-route failback in [Recovery routes](#recovery-routes)
must keep until the standby's newest data is transferred and verified. The
loop ends when Stats fails back to Lisa and its runner reconnects, or with
a supported Engine operation that suspends alarms for a fenced namespace;
the pinned Engine's peer API (`engine/packages/api-peer`) has none. Raising
`pegboard.envoy_actor_inbound_capacity` would hide the symptom without
stopping the retries.

Discover's `research-space` actor `pa0699azx51wll1le1qmumrnv3dl00` also
failed to wake from `sleeping` before the gateway deadline while Discover's
runner flapped. Restarting `oo-app.discover` restored its runner, HTTP 200
on its private listener and `hq.17166969.xyz`.

## Loss model

Single host, single NVMe disk. All of Engine, store, Caddy state and the
default backups live on one filesystem, so a disk or host loss loses everything
on `lisa`; the default backup protects against operator error, corruption and a
bad upgrade, not hardware. The Mac has manually copied, integrity-verified
artifacts under `/Users/josh/backups/openorange`. No recurring backup scheduler
was found in the installer source. A recurring S3 copy remains deferred as P1
in STUF-75. Writes after the latest independently verified off-host fence remain
at risk. The Engine log and object tier form one recovery unit. Retaining an
S3 bucket alone does not establish Engine recovery after log-disk loss.
Application logical exports provide an additional recovery path independent
of Engine internals. Store object checksums have passed isolated restore tests.
Full-host replacement RTO and bucket-version recovery remain unmeasured.

## Rehearsal record (lisa, 2026-11-13)

Demo Worker `deploy/openorange/demo` (SQLite Durable Object + R2 binding)
answered `stats.17166969.xyz` and `demo.17166969.xyz` in namespace `demo`
(overlay `rehearsal/overlay.toml`). From the Mac (100.107.2.101),
`tests/client-checks.sh`: identity forwarded as `user:<login>`; forged
`Stats-Tailnet-Identity`, `Stats-Gateway-Secret`, `Tailscale-*`,
`X-Forwarded-*`, `X-OO-Peer` stripped or overwritten; Tansu `/api/v2/health`
200 via ingress; ports 6420/6421/6422/6430/7070/7071/8080/80/18480 closed on
`100.68.104.43` and `10.0.1.56`, 443 open only on the tailnet address.
`public-listener-checks.sh` on the host: `/admin` and ten variants 404, forged
headers not delivered, loopback only. DO count survived app restart, Engine
restart and an Engine SIGKILL (supervisor respawn); backup at count 9 then
restore into a fresh directory returned 9 while the live count was 11.
Tagged-node identity: not run on a real device (no tagged node on the tailnet;
`tailscale status --json` shows no tags); the mapping is unit-tested with
canned `whois` documents only.

After the demo was removed (`oo remove demo --purge-store`, overlay deleted)
the stack stays running, idle: `oo-store`, `oo-engine`, `oo-identity`,
`oo-ingress` (all four boot-enabled), Caddy on `100.68.104.43:443` and
`127.0.0.1:18480`, namespaces `stats stuff discover discover-preview` (plus the
leftover `demo` namespace, whose Actor state cannot be deleted) with all apps
answering `503 app not deployed`. `oo-app.stats` and `oo-app.stuff` init
instances exist but are not in the default runlevel until an image is deployed.

## Deviations and open items

* Engine storage uses Rivet's `file_system` tier, not an S3 bucket: the Engine
  with `object_storage.primary.s3` pointed at versitygw timed out at startup
  (`config operation timed out`) with no request ever reaching the store, twice
  in the same way (also with `api_peer` removed); not diagnosed further
  (budget). The documented single-instance compose guide uses `file_system`.
  Rivet's production guidance (S3 with versioning, 3 instances) is not met.
* Release-candidate Engine image; app pools fixed to `default`/`services`;
  admin token shared by all app containers (see Topology).
* `sudo` does not exist on `lisa`; passwordless `doas` was used. Host changes:
  the paths above, `rc-update add` of the four services, images pulled/built
  (`rivetdev/engine`, `versity/versitygw`, `caddy`, `python`, two local
  builds), docker network `openorange`. No package installed.
* The IAM, `.vgwlocks` and `versions` directories belong to the store; do not
  edit them by hand.

## Remaining verification

A real tagged-node request and Tansu hardware passkey login remain untested.
The current tailnet policy permits HTTPS; Mac, Threadripper and Lisa have
published through the same coordinator without policy changes.

Off-host backups live at `/Users/josh/backups/openorange` on the Mac. The
post-Stuff snapshot `20261114T184204Z` passed an independent Engine/S3
restore with full object checksums. Its 9,256,069,120-byte archive was copied
to `lisa/post-stuff-cutover/state.tar` and verified against SHA-256
`39caece0385a875ca8b19e7cbc94826e18186139d86426584789652893b8b48d`.
The current Stuff build context and ingress/secret configuration overlay
are preserved under `stuff/runtime-9da0f029c115` in that backup directory.

## Stuff production cutover (2026-11-14)

All eight public pull names route through the connector to Lisa. Anonymous
Cargo, npm, PyPI, OCI and mirror reads pass, including a checksum-verified
Cargo download, HEAD, conditional 304, byte-range 206 and invalid-range 416.
Public writes return 405 and publishing paths return 404. Public upstream
requests explicitly carry HTTPS so generated links retain the correct scheme.
Mac, Threadripper and Lisa use the protected credentials file with the private
publishing hostname; real publications and coordinator conflict checks pass.

The Cloudflare Worker `stuff` and its six R2 buckets (`stuff-mycrates`,
`stuff-mynpm`, `stuff-mypypi`, `stuff-oci`, `stuff-mirror`, `stuff-oci-blobs`)
were deleted after source identity checks, full-data recovery and off-host
archive verification. Protected source inventories, copy ledgers and final
retirement receipts are under `stuff/source-cutover` in the Mac backup.
Cloudflare DNS, the public connector and immutable-blob cache rules still
serve public access; application compute, coordination and storage run on Lisa.

The temporary private-DNS interval interrupted GitHub consumers. Public DNS
now returns edge addresses, and the previously failing Ish lint workflow
downloaded its Stuff dependencies and passed on a fresh GitHub runner.

Discover production and preview also completed cutover. Their selected spaces
are `replacement-orange-live-20261114` and
`replacement-orange-preview-live-20261114`, restored from fresh fenced source
snapshots with 15,475 and 667 verified rows and independent recovery proofs.
The source Workers, Durable Object namespaces, two artifact buckets and two
Discover Access applications are deleted. Public search index checksums match;
reader and bearer MCP requests pass, public admin routes return 404, and the
private admin form origin and CSRF checks pass. Their protected snapshots,
runtime contexts and final configuration overlay live under `discover/` and
`discover-preview/` in the Mac backup directory.

## Nanoshop

Nanoshop is deployed at `https://shop.17166969.xyz`, with private owner and
operator access at `https://shop-admin.17166969.xyz/admin`. Public cart and
webhook methods are permitted; public `/admin` is denied. The app has its own
namespace/bucket, no published ports and no internet egress. Its operator hash
is supplied through the root-owned `apps/nanoshop.extra.env`.

`make deploy` in the Nanoshop repository builds and activates only this app,
with image preflight, rollback and a Stats deployment marker. Image
`nanoshop:159a08d7ed2e` passed that path on 2026-11-14. Public health/home,
private administration, cart POST and cart read passed. The old Cloudflare
Worker, Durable Object namespace, empty bucket, Access app and dedicated
service token were deleted. The owner explicitly discarded the old test data;
the native shop uses the repository fixture.

## agentctl

`agentctl` (`joshuarli/agentctl`, `apps/orange`) is a private-only Orange app
on `agentctl.17166969.xyz`: tailnet listener with whois identity, no public
hostname, no tunnel route, no internet egress and no buckets. It sends
application events to Stats on its private address with the `agentctl`
service's ingest token (`APPLICATION_EVENTS_TOKEN` in `apps/agentctl.extra.env`). The Worker enforces its own owner allowlist on top of the gateway
identity. Execution hosts connect to it outbound (`/api/uplink`, per-host
credential), so no execution host needs a listener. The image is built by
`apps/orange/deploy/build-image.sh lisa` in that repository.

## Public connector

`oo-tunnel` runs cloudflared 2026.10.7 by digest under OpenRC. Its only
origin is the loopback public listener. `oo tunnel-config` derives its
remote ingress rules from each enabled app's `public_hostnames`, then
adds a 404 catch-all. Stats and Tansu have no public tunnel route.
Stuff's eight pull hostnames accept only GET and HEAD on this listener;
`/_s3`, `/_publication`, and `/admin` are refused before forwarding.
`public_methods` declares the allowed methods and returns 405 for other
methods. Its private publishing hostname is absent from the public listener
and tunnel. Discover retains its public reader and bearer MCP routes, with
`/admin` refused before forwarding.

The root-owned `/etc/openorange/tunnel.env` supplies `TUNNEL_TOKEN` through
Docker's environment file. The token never appears in process arguments.
Metrics and readiness bind to `127.0.0.1:18481`; `bin/health` checks both
connection readiness and that bind address. `drain` stops the connector
before ingress, and starts it after ingress and the apps. The physical
backup includes its credentials and configuration with the rest of `/etc/openorange`.

### Rivet infrastructure explorer

The custom, read-only explorer is at `https://stats.17166969.xyz/rivet`.
It is managed by `oo-rivet`, separately from Stats and the Engine. Caddy
routes only `/rivet` and `/rivet/*` on the existing private Stats hostname;
Stats' application routes and all other hostnames keep their existing upstreams.
The public tunnel has no route to the explorer.

The `[rivet]` table selects the private hostname, unused bridge address and
explicit operator identities. A public application hostname is rejected.
Tailnet membership alone grants no access: every page, asset and API read
requires both Caddy's gateway secret and an exact identity in `operators`.
Caddy removes client-supplied identity and gateway headers before whois
authentication. The BFF permits only six bounded GET operations against the
fixed Engine origin; it projects known fields and rejects upstream redirects,
malformed responses and secrets in returned fields. It has no Docker socket,
command executor, arbitrary proxy or mutation endpoint.

Every private route evaluates Caddy's `remote_ip` matcher before forwarding to
whois. Caddy 2.11.9 intentionally withholds the remote-address placeholder
during HTTP/3 early data; its
[IP matcher returns HTTP 425 until the TLS handshake completes](https://github.com/caddyserver/caddy/blob/v2.11.9/modules/caddyhttp/ip_matchers.go).
This lets the browser retry with a verified peer instead of treating an empty
address as an authorization failure. The identity sidecar still rejects empty,
malformed and non-tailnet peers.

`oo secrets` generates `/etc/openorange/rivet/config.json` with the Engine
credential, independent gateway secret and operator policy. The file is
root-owned, group-readable only by container GID 10001, mode 0440 inside a
0700 directory. Caddy's derived gateway environment remains root-only.
Credentials never enter frontend configuration or assets. The normal physical
backup includes these files and the selected image ID.

To install or update only this service, after syncing the stack code:

```sh
doas /opt/openorange/bin/oo secrets
doas /opt/openorange/bin/build-rivet
doas install -m 0755 /opt/openorange/openrc/oo-rivet /etc/init.d/oo-rivet
doas rc-update add oo-rivet default
doas rc-service oo-rivet restart
doas /opt/openorange/bin/oo reload-ingress
doas /opt/openorange/bin/health --json
```

The builder uses the digest-pinned Python base and records the resulting
content-addressed image ID in `/etc/openorange/rivet.image`. The container
runs by that ID, as UID/GID 10001, with a read-only filesystem, a 128 MiB
limit, the internal bridge alone and no published ports. Restarting `oo-rivet`
does not restart its dependencies. Caddy's reload reads the current protected
gateway environment and validates the configuration before a graceful reload.
Neither operation replaces or restarts the Engine.

The UI shows live Engine health/version, namespaces, pools, connected and
disconnected nodes, actor names, filtered actor pages and selected record
details. ID/key search covers the displayed actor page. Pagination is marked
incomplete. Lifecycle timestamps are reported events rather than a claim about
the actor's current state. Engine storage health, logs, metrics, arbitrary actor
inspection and WebSockets are unavailable; links lead to Stats' existing
service deployments and host metrics. No SQLite inspection or cluster-wide
actor total is inferred.

#### Production acceptance (2026-11-14)

Stack revision `1011f69` was deployed with explorer image
`sha256:e487fe8adba8e159725220cffce764a4091dc6b5fc13ae0d5174628a3b1bd6ad`.
The authorized Mac browser loaded valid HTTPS over HTTP/3, listed all eight
production/rehearsal namespaces, and displayed real Stats actor metadata and
lifecycle events. Stats had two connected nodes and Stuff had one. Namespace
switching, actor selection/search, Back, reload and the 390 px layout passed.

Unlisted operators and missing/forged gateway credentials received 403;
mutations received 405. The public listener returned 404 even with forged
identity headers. Asset/API scans found no Engine or gateway credentials.
Restarting only `oo-rivet` preserved the Engine and application container IDs
and start times; the Engine configuration and credential hashes were unchanged.
Shared health reported 92 passes, one disk-capacity warning and no failures.

The protected configuration and selected image were copied to the Mac's
`~/backups/openorange/rivet/production/`. The earlier full physical backup
predates the explorer; retain this supplement with it for recovery.

#### UI selection and pinned Engine evidence

On 2026-11-14, the running `oo-engine` image was inspected read-only. Its
image reference was the Engine index digest in `images.lock.json`; the binary
reported `Rivet 3.1.1`, although the configured image tag is `3.1.2-rc.1`.
The image did not expose an OCI revision label. Its attached BuildKit
provenance identifies source revision `e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9`;
see [the Engine diagnosis](openorange-engine-diagnosis.md) for the digest
binding and qualification. Authenticated GETs returned 200 for
`/namespaces`, `/pools?namespace=stats-prod`,
`/pools/default/nodes?namespace=stats-prod`,
`/actors/names?namespace=stats-prod`, and an actor list filtered by name;
`/health` returned 200 without authentication. `/runner-pools` and `/ui`
returned 404. Actor lists require a name or actor ID; a request with only a
namespace returned 400. These observations do not establish the availability
or safety of other routes.

How this Engine refuses work when its host is CPU-saturated, and which limits
turn those refusals into slowness, is in
[Engine degradation](openorange-engine-degradation.md).

The [Rivet `v3.1.2-rc.1` tag](https://github.com/rivet-dev/rivet/tree/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9)
resolves to `e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9`. Its
[public router](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/engine/packages/api-public/src/router.rs)
declares `/runner-pools`, whereas its checked-in
[OpenAPI artifact](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/engine/artifacts/openapi.json)
describes `/pools`. Use the observed live contract, not an assumption that
the tag and image are identical. The current
[self-host control-plane guide](https://rivet.dev/docs/deploy/self-host/control-plane/)
describes the Engine image and does not claim a bundled UI. The tag's
[README](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/README.md)
links Rivet Cloud's hosted dashboard. The separate official
[frontend repository](https://github.com/rivet-dev/frontend) is archived;
it is not evidence of a maintained v3-compatible self-hosted UI. On this date,
the [Docker Hub `rivetdev` namespace](https://hub.docker.com/u/rivetdev)
listed `engine`, `services`, `sandbox-agent`, and `compute-hello-world`, with
no dashboard image. The complete pinned source tree contains no `frontend/`
dashboard build. Search-indexed instructions for an older monorepo frontend
do not describe the files in this tag. The maintained
[Inspector bundle staging contract](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/rivetkit-rust/packages/rivetkit-core/inspector-dist/README.md)
describes a separate actor Inspector UI, with generated assets absent from
the source tree. Its
[versioned protocol](https://github.com/rivet-dev/rivet/blob/e5ed3911ebff8ddc35c08b3f6c6eb3f795d042f9/rivetkit-rust/packages/inspector-protocol/schemas/v6.bare)
also carries actor operations beyond infrastructure reads. The production
Stats application's `/inspector/ui/` returns 404. No compatible, maintained
standalone cluster dashboard with a verified self-hosted deployment was found
in these images, source packages or deployment instructions. The selected
explorer uses the validated Engine read API without introducing a SaaS
dependency, obsolete frontend, or browser-held cluster credential.

### Registry body ownership

Anonymous HEAD and conditional reads must not retain an S3 GET body. The Worker
uses metadata reads for HEAD, tracks speculative/content reads for each request,
and joins and cancels every stream it does not hand to the HTTP response. This
also covers an authoritative pointer moving or disappearing after a speculative
read starts. Without cleanup, unread bodies exhausted the native adapter's
50-connection S3 pool and made publication-coordinator reads time out.

`crates/stuff-worker/test/body-lifecycle.test.mjs` exercises the compiled Worker
with a two-connection streaming store: 60 rounds of HEAD, 304 and 412 responses,
a normal body, a moved pointer and a missing pointer. It verifies zero retained
bodies. The same test fails against the previous Worker when the pool fills.

Production image `stuff:062beac2bcc7` passed 182 anonymous HTTPS reads against
Lisa's real S3 store after deployment: 62 responses with 200, 60 with 304 and
60 with 412, including 60 HEAD requests. The final full read still succeeded;
shared health returned 92 passes, one disk-capacity warning and no failures.

## Stats runtime telemetry

Build the bridge bundle from a clean Stats checkout with its pinned Node and
workspace dependencies:

```sh
node cloudflare/scripts/build-platform-bridge.mjs --out .work/tmp/platform-bundle
```

Copy `main.mjs` to Lisa. Build and pin the separate container there:

```sh
doas /opt/openorange/bin/build-platform-bridge /path/to/main.mjs
```

Enable `[platform_bridge]` in `apps.toml` after deploying a Stats image that
supports the reserved platform sink. Keep `source_app = "stats"` and the
validated runtime versions. Refresh only the relevant configuration:

```sh
doas /opt/openorange/bin/oo secrets
doas /opt/openorange/bin/oo discover-platform
doas install -m 0755 /opt/openorange/openrc/oo-platform /etc/init.d/oo-platform
doas rc-update add oo-platform default
doas rc-service oo-app.stats restart
doas rc-service oo-platform start
doas /opt/openorange/bin/oo wait platform 30
```

Discovery uses the pinned Stats image to derive named-object keys and verifies
exactly one live Engine actor for each selector. It writes the protected policy
without printing keys or Engine credentials. OpenOrange 1.0.2's internal ID
format is a constraint of this helper. Revalidate discovery when changing the
runtime pin. `configure-platform ACTORS.json` accepts separately verified
selectors when automatic discovery is unavailable.

The bridge accepts OTLP HTTP/JSON on its private Docker address. No hostname,
Caddy route or host port is added. Its only ingest credential authorizes the
reserved `stats-platform` sink. Stats verifies its SHA-256 locally, so these
writes do not invoke the Installation actor being observed. The bridge excludes
its destination ObservationStore actor. It never receives the Engine token.

Stats' two Worker processes use 10% root sampling. Native queues and receiver
buffers are bounded. Other applications receive no exporter configuration.
The Engine continues using its filesystem tier. No Engine setting or image is
changed. The first-Worker-only metrics endpoint is not enabled because it would
omit ObservationStore.

The Platform tab lives under the Stats project. It shows observed counts,
failures, source releases, microsecond histograms and delivery reports. Histogram
percentiles are upper bounds. Sampled counts are not complete request totals,
and upstream exporter loss is unknown. See the
[Stats contract](https://github.com/joshuarli/stats/blob/master/docs/platform-observability.md).

Restarting `oo-platform` does not restart the Engine or apps. A collector outage
can lose observations but does not fail actor requests. To disable collection,
set the table's `enabled` flag to false, run `oo secrets`, restart only Stats and
stop `oo-platform`. Protected credentials and policy remain available for a
later activation. Full stack backups already include `/etc/openorange`; preserve
`platform.env`, `platform.image`, `platform/policy.json` and the selected image
in the off-host copy as well.

The 2026-11-14 production activation is recorded in the
[Stats acceptance report](https://github.com/joshuarli/stats/blob/master/bench/results/2026-11-14-platform-runtime/README.md).
It verifies real actor data, browser navigation, private access, restart isolation
and the protected Mac copy. Collection is best effort: slow writes under load
can exhaust the bounded delivery budget, and the dashboard reports abandoned
observations. A healthy receiver does not imply complete telemetry delivery.

## Runtime hardening (2026-11-14)

`bin/drain` fails if application discovery fails, an OpenRC stop fails or a
service remains running. `bin/backup` also checks Docker for any active Engine,
Store or enabled application writer before reconciling backup checksums.
Recovery restores every previously running application, including native apps,
and the platform bridge. These two scripts are installed on Lisa. The focused
shell and shared Python tests cover failed stops and service recovery ordering.

The latest protected physical snapshot has fence `20261114T214525Z`, 76,609
files and 9,555,488,768 bytes. The recorded 169.5 seconds is backup downtime,
not restore RTO. The older `20261114T184204Z` snapshot has an independent
Engine and Store restore with complete object checksums and an application
probe. That older probe does not prove the newest Stats state.

Stats-specific application changes and remaining native-runtime gaps are in
its [hardening audit](https://github.com/joshuarli/stats/blob/master/docs/runtime-hardening.md).
The Engine image, persistence and production credentials remain unchanged.

## Isolated Engine S3 startup reproduction

`bin/repro-engine-s3` compares the pinned AMD64 Engine and Store manifests.
It requires an explicit local Unix-socket Docker context. Every container uses
a fresh internal network and ephemeral state, without published ports.
Generated credentials live in protected files and are removed during cleanup.
The probe uses curl from the pinned Engine image. It does not start another
Engine process for probing.

Run from the Stuff checkout with a new output directory:

```sh
deploy/openorange/bin/repro-engine-s3 --context orbstack \
  --output "$PWD/.work/tmp/engine-s3-repro"
```

The [startup receipt](../deploy/openorange/tests/engine-s3-startup-results.json)
records the actual local run under AMD64 emulation. The default plain-HTTP
configuration times out during configuration startup. Setting
`AWS_ALLOW_HTTP=true` lets the same pinned Engine become healthy against
VersityGW. The pinned S3 builder reads this option from its environment.

This explains a necessary configuration difference in the earlier failed
plain-HTTP attempt. It does not prove conditional-write semantics, recovery,
latency, upgrade compatibility or a safe live backend migration. HTTP remains
permitted only inside this isolated experiment. Production remains on the
filesystem tier. No upstream defect was established by this configuration
test, so no bug was filed. S3 backup work remains separate and deferred.

See [runtime releases](openorange-releases.md) for source ownership and read-only inspection.
