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

## Load drill

On 2026-11-21 from 16:48 to 17:19 UTC, Threadripper ran 64 unconfined busy
loops and repeated 8 GB direct writes beside the VM's image while the guest
served reads. Host load ranged from 10 to 132. All 30 one-minute samples showed
no Engine warning (`command_capacity`, `could not register`,
`request_deadline_exceeded`, `fenced`, `overloaded`) and no failed probe round.
The guest's probe made 845 reads of five registry paths, every one a 200:
p50 116 ms, p99 433 ms, max 4.3 s, against a p99 of 338 ms beforehand.
Production Stats health on the same host stayed 200 throughout. The
reservation holds; disk contention adds tail latency but no errors.

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
   then build the guest's image from the commit deployed to Lisa in step 1
   (`crates/stuff-worker/orange/build-image.sh stuff-primary`, then
   `oo set-image stuff stuff:<sha12>`) and restart `oo-app.stuff`. Since
   2026-11-21 the guest runs `stuff:5020a6f70e24`, which already has the
   STUF-104 fix; rebuild only if step 1 deploys a later commit.
   Check: `curl -H 'Host: crates.17166969.xyz' http://172.29.80.21:8080/current/registry/config.json`
   in the guest answers 200.
3. **Pre-copy the buckets.** Lisa's root has no route to the guest, and the
   guest's sshd allows no remote forwards, so the operator's machine relays one
   rsync session. Lisa runs the sender, the guest runs the client, and two pipes
   carry the protocol between them:

   ```sh
   mkfifo f
   ssh lisa 'doas rsync --server --sender -lHogDtpAXre.iLsfxCIvu --numeric-ids . SRC/' < f |
     ssh -F ~/.config/stuff/primary/ssh_config stuff-primary \
       'rsync -aHAX --numeric-ids --delete -e /root/stdio-rsh x:SRC/ SRC/ 3<&0 4>&1 1>&2' > f
   ```

   `/root/stdio-rsh` copies its stdin to fd 4 and fd 3 to its stdout, and exits
   when fd 3 closes:

   ```sh
   #!/bin/sh
   exec 5<&0
   cat <&5 >&4 &
   out=$!
   cat <&3
   kill $out 2>/dev/null
   ```

   Run it for each `store/data/stuff-*` and `store/versions/stuff-*` under
   `/var/lib/openorange`. The sender's flags are what the guest's rsync 3.5.2
   asks for with `-aHAX --numeric-ids --delete`; print them again with
   `-e` pointing at a script that echoes its arguments if either rsync changes.
   Check: a repeat run reports `Number of regular files transferred: 0`, and a
   sampled object's `user.etag` is equal on both sides. On 2026-11-21 the
   relay carried `stuff-oci` with every `user.*` attribute intact.
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
   gateway secret. Import must be the first op each guest coordinator sees:
   any other op, `export` included, seeds an empty coordinator from the
   bucket's `current` object, and import then answers `409`.
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
