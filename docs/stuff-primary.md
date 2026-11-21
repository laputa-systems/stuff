# Stuff primary on Threadripper

Stuff's write primary moves from Lisa's shared Engine to its own VM on
Threadripper. Lisa keeps the edge: Cloudflare, `cloudflared` and Caddy. Its
ingress sends Stuff's public and tailnet hostnames to the VM over a supervised
SSH forward. The move takes no downtime. Reads never stop, and publishers retry
while the coordinators are frozen. Lisa's Engine is never restarted, so
Discover, nanoshop and agentctl are not touched.

## What runs where

| Piece | Where |
| --- | --- |
| VM | Threadripper `/var/lib/stuff-primary/` (`os.qcow2`, a 160 GiB preallocated `data.qcow2`, `seed.iso`), OpenRC `stuff-primary-vm` and `stuff-primary-vm-watchdog` from `deploy/openorange/standby/` |
| Reservation | `cpu.weight 10000`, `memory.min 9G`, `memory.swap.max 0`, `io.latency` 10 ms on the image's disk |
| Guest | Alpine 3.24, 8 vCPU, 8 GiB. `/opt/openorange` from this repository; the overlay `/etc/openorange/overlay.toml` disables Rivet, the platform bridge, the tunnel and DNS and caps the Engine at 4 CPUs and 3 GiB. Only `oo-store`, `oo-engine` and `oo-app.stuff` run |
| Engine | The seven-patch candidate `sha256:7df2c2be40ce9d4fa40ddccc4ae20383088b9a5b38754ea94d7430c7c5e74918` on a fresh depot |
| Access | `~/.config/stuff/primary/ssh_config` (`stuff-primary`, through Threadripper). The host's `shutdown` key may only power the guest off |
| Forward | Lisa `oo-stuff-primary-tunnel` (`deploy/openorange/standby/oo-stuff-primary-tunnel.openrc`): `127.0.0.1:18491` is the guest app, `127.0.0.1:18492` the guest store. The guest key may open only those two destinations |

The guest has its own Engine, so its coordinator state is moved with the
coordinator handoff ops (`docs/openorange-runtime.md`), not by copying a depot.
The Stuff buckets are copied with their extended attributes, so object ETags
and version IDs stay identical.

## Cutover

Run after Lisa's Engine soak has ended and been recorded. Each step lists its
check and its rollback. Until the guest is thawed in step 7, Lisa remains the
only writer and every step is reversible.

1. **Deploy the handoff build to Lisa.** `crates/stuff-worker/orange/deploy.sh lisa`
   from `main`. Reads fail over to R2 while `oo-app.stuff` restarts.
   `main` includes the STUF-104 blob-miss fix.
   Check: `oo deployment stuff` names the new image, a HEAD for a random
   absent `https://oci-blobs.17166969.xyz/sha256/<hex>` carries
   `cache-control: no-store`, and
   `POST /_publication/cargo/thaw` with the coordinator token answers 200; the
   previous build answers 404 for that op.
   Rollback: the script restores the previous image.
2. **Refresh the guest's Stuff environment.** Copy Lisa's
   `/etc/openorange/apps/stuff.env` and `stuff.extra.env` into the guest. Run
   `oo secrets` there so the Engine-derived values point at the guest Engine,
   then rebuild the guest's image from the `main` deployed in step 1 (the guest
   still runs `stuff:fdbd63275a79`, which predates the STUF-104 fix), deploy
   it and restart `oo-app.stuff`.
   Check: `curl -H 'Host: crates.17166969.xyz' http://172.29.80.21:8080/current/registry/config.json`
   in the guest answers 200.
3. **Pre-copy the buckets.** From Lisa, as root, stream
   `store/data/stuff-*` and `store/versions/stuff-*` into the guest with GNU tar
   `--xattrs --xattrs-include='user.*' --numeric-owner`. Repeat with `rsync -aHAX
   --numeric-ids --delete` to shrink the final delta.
   Check: object counts per bucket match, and a sampled object's `user.etag`
   and `user.version-id` are equal on both sides.
4. **Freeze Lisa's coordinators.** For `cargo npm pypi oci mirror`:
   `POST https://stuff-publish.17166969.xyz/_publication/REGISTRY/freeze`.
   New publishes now receive 503 with `Retry-After: 30` and retry. In-flight
   publishes finish.
   Check: `GET .../export` answers 200 for all five, which means no lease is
   live. Rollback: `POST .../thaw` on each.
5. **Final delta and export.** Run the step 3 rsync again; it must report no
   changes when repeated. Save each registry's export.
   Check: each export's `current.generation` equals the bucket's `current`
   object in the guest.
6. **Import into the guest.** Post each export to the guest coordinator's
   `import` op through the guest app with the coordinator token and the
   gateway secret.
   Check: each guest export equals Lisa's export. Rollback: stop the guest app,
   discard its Engine depot, thaw Lisa.
7. **Switch the route and thaw the guest. Point of no return.**
   Install and start `oo-stuff-primary-tunnel` on Lisa. Write
   `/etc/openorange/apps/stuff.recovery.env` with the guest's
   `GATEWAY_SECRET`. Add `"stuff": {"mode": "primary", "upstream":
   "127.0.0.1:18491"}` to `/etc/openorange/recovery-routes.json`, keeping the
   other entries. Run `oo render --stdout`, then `oo reload-ingress`. Stop and
   disable Lisa's `oo-replica-sync`, because Lisa's frozen pointers would
   otherwise rewrite R2's `current` objects backwards. Then
   `POST .../thaw` on the guest for all five registries.
   Check: public reads carry no `x-stuff-served-by`; a canary `stuff publish`
   succeeds and reads back. Make the canary an OCI push, and HEAD one of its
   new layer URLs on `oci-blobs` before the push (404, `BYPASS`) and after it
   (200, `public, max-age=31536000, immutable`); this is STUF-104's live
   acceptance. Lisa stays frozen as the fence.
   Rollback before the canary publish: restore `recovery-routes.json` and
   reload, freeze the guest, thaw Lisa, restart Lisa's replica sync. After the
   first write lands on the guest, roll back only by repeating this handoff in
   the other direction.
8. **Feed the replicas.** In the guest, install and start `oo-replica-sync`
   with Lisa's `replica-sync.env` (the guest store has the same endpoint
   address and credentials). On Lisa, a second sync instance copies from
   `http://127.0.0.1:18492` into Lisa's store.
   Check: after a canary publish, R2 and Lisa name the new generation within
   ten minutes.
9. **Rotate the store credential.** The guest store's Stuff account key was
   exposed in an operator transcript on 2026-11-21. Create a new account in the
   guest store, update `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY` in the guest's
   `stuff.env`, restart `oo-app.stuff`, then delete the old account.
