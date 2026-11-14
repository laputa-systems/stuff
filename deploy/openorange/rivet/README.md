# Rivet explorer

A read-only, server-side proxy for the observed Rivet Engine API. It serves `/rivet/` and assets and API routes under `/rivet/`. Every request, including static files, requires both a gateway secret and an explicitly authorized operator identity. The browser never receives the Engine token or gateway secret. A caller able to reach the BFF directly without the secret is denied; protect the secret and limit access to the container network.

Build with `docker build -t rivet-explorer deploy/openorange/rivet`. Run as the image's UID/GID 10001, with a read-only root filesystem, a 128 MiB memory limit (`--memory=128m`), no published ports, and a read-only mounted configuration file at `/run/secrets/rivet-explorer.json`, readable by UID 10001. Attach the container to the private network at `172.29.80.24`; it listens on port 8080. The shared stack owns lifecycle, routing, network isolation and deployment; use `bin/build-rivet` for a content-pinned production image.

The JSON configuration has exactly these required values (use real secrets, not these placeholders):

```json
{"engine_origin":"http://172.29.80.11:6420","engine_token":"ENGINE_ADMIN_TOKEN","gateway_secret":"LONG_RANDOM_GATEWAY_SECRET","operators":["exact-identity"]}
```

Keep this file and its source secret restricted. Set `engine_token` from `/etc/openorange/engine.env`'s `RIVET__AUTH__ADMIN_TOKEN` without putting it in a command line or logs. Use an independently generated gateway secret. Restart the container after changing configuration. Operators are exact, case-sensitive identity strings produced by the existing identity sidecar; tailnet membership alone grants no access.

The generated Caddy route covers `/rivet` and `/rivet/*`, authenticate through the identity sidecar, strip incoming `Stats-Tailnet-Identity` and `Rivet-Gateway-Secret` headers, then set exactly one `Stats-Tailnet-Identity` header to the sidecar-verified identity and exactly one `Rivet-Gateway-Secret` header to the configured secret before proxying to `172.29.80.24:8080`. Never let a client choose either forwarded value. Do not strip the `/rivet` prefix. Keep the secret in Caddy's protected server-side configuration, never in client-visible responses. Configure network policy so only the trusted gateway can reach the BFF.

The BFF allows GET only: health, namespaces, pools, pool nodes, actor names, and actors filtered by namespace and name. Inputs are bounded and restricted, redirects are refused, and upstream responses are capped at 1 MiB with a four-second timeout. Known scalar fields alone are projected; metadata, configuration and arbitrary JSON are excluded. Pagination is not followed and the UI warns when a cursor indicates more results. Timestamps are Engine values. Actor counts describe only the displayed name and first page. Logs, storage, disk usage, placement, activity and inspectors are unsupported. The service does not modify the Engine.

Run tests from the repository root: `TMPDIR=$PWD/.work/tmp python3.14 -m unittest discover -s deploy/openorange/rivet -p 'test_*.py' -v`.

At most 16 requests run concurrently; incoming sockets time out after five seconds of inactivity and are closed after ten seconds total. Oversized or malformed upstream data and projected values containing either secret fail closed. Integers outside JavaScript’s safe range are returned as decimal strings. The actor key is projected as a string, matching the observed Engine response. Actor lifecycle labels derive only from returned timestamps; they do not imply placement or activity. Namespace and actor selections are stored in URL hash parameters for refresh and browser history. Search filters only the displayed actor page.

The frontend race and navigation regression can be run with `node deploy/openorange/rivet/test_ui.js`.
