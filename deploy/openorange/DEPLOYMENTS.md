# Deployment markers

Create each Stats service with the actual OpenOrange host in `hostIds`, then
install its service creation response as `/etc/openorange/deploy-markers/APP.json`.
It must contain `name`, `hostIds`, and `deployToken`, be owned by root, and have
mode 0600; its directory must be root-only. Transfer the credential over a
protected channel without putting the token in command arguments, logs, or app
bindings. Stats service creation and token rotation are documented in the
[joshuarli/stats `docs/operations.md` service markers section](https://github.com/joshuarli/stats/blob/master/docs/operations.md).
Replace this file after rotation.

After selecting the image, restarting the app, and completing deploy health
checks, call `doas /opt/openorange/bin/oo record-deployment APP --if-current IMAGE`.
Callers must disable their rollback trap before this step: delivery failure
returns nonzero while the healthy app remains running. The helper verifies the
selected image, container image and node version and health, then writes the
exact marker to `/var/lib/openorange/deployments/APP/` before sending it directly
to Stats on its configured private container address. Release identifiers use
`stats-IMAGE_TAG` and `stuff-IMAGE_TAG` for those apps and `IMAGE_TAG` for other
apps; image builders must embed the same application release identifier.

Use `doas /opt/openorange/bin/oo sync-deployments APP` to retry queued markers,
or omit APP to retry every Orange app. A subsequent record also drains that
app's queue. A failed or missing credential is an error. Requests retained after
an ambiguous response are retried unchanged; Stats accepts identical marker
retries. Markers older than Stats' 30-day retention require operator attention.
The queue contains no deploy tokens and is root-only. No background process
retries it.

Successful deliveries retain their exact marker body under `delivered/`. A
container restart with the same selected version keeps the original activation
time; recording it again neither rewrites nor resends the marker. Selecting a
different image, including a rollback, increments the version and records a new
activation.

Physical backups include `deployments/` under each app's lock, together with
the deploy credentials in `etc/`. Restore rehearsals copy and checksum that
state without replaying it against live Stats. A real restore must restore
`deployments/` as well as Engine, Store and `etc/` before marker delivery resumes.

While the Stats standby holds write authority, the private Stats address is
Lisa's relay, defined in
[joshuarli/stats `deploy/orange/recovery/stats-direct.Caddyfile`](https://github.com/joshuarli/stats/blob/master/deploy/orange/recovery/stats-direct.Caddyfile),
which forwards `POST /ingest/services/NAME/deployments` to the standby alongside
signed application events. Stats authenticates the marker with the service's
deploy token. Service enrollment for a new app is `statsctl service create`
followed by installing `{name, hostIds, deployToken}` here as described above.
