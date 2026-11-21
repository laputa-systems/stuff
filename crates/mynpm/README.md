# mynpm

npm archive: imports npm and pnpm lockfiles, fetches and verifies the exact
tarballs, and publishes immutable static generations (see the repository
README for serving and the exit-code contract).

## Fleet ingest

`deploy/fleet-ingest.sh` drives the npm import, fetch, and publish for a whole
fleet into a local site; see [PUBLISHING.md](../../docs/PUBLISHING.md#publish-a-registry).
Re-running is safe: imports are identified by content, unchanged lockfiles leave
the inventory byte-identical, and `fetch` promotes each artifact as soon as it
verifies.

## Metadata-only versions

Packages whose `os`/`cpu`/`libc` exclude every configured target (win32,
android, freebsd, ppc64, ...) are never fetched or hosted. `fetch` records each
such name@version as a metadata-only inventory record: the lockfile's sha512
integrity, the lockfile's `os`/`cpu`/`libc`, and the upstream `time[version]`
(one packument request per package, same host, size, and byte limits as other
fetches; an upstream `dist.integrity` that disagrees with the lockfile is a
conflict). `publish` renders them into the packument as
`versions[v].dist.{integrity,tarball}`, `os`/`cpu`/`libc`, and `time[v]`. The
tarball URL is the standard `current/<name>/-/<basename>-<version>.tgz` path,
which is 404 because no object exists. `deprecated` and `engines` are not
copied: frozen installs never read them for a version that is not installed.
`os`/`cpu`/`libc` are copied so non-frozen resolves skip the unhostable build.

Metadata-only versions are not artifacts. They are absent from `catalog.json`,
`index.html`, `llms.txt`, and `stuff ls`/`stuff doctor`, and `fetch`, `verify`,
and `publish` report their counts separately. Hosting such a version later (a
target that supports it) replaces its record if the integrity matches.

Contract: inventory `schemaVersion` is 2 until a metadata-only record exists
and 3 afterwards (`metadataOnly` array), so existing state loads unchanged and
stays byte-identical until `fetch` records one; older binaries cannot read a
version 3 inventory. Publication renderer 6 adds `metadataOnly` to
`manifest.json` and stub-only packuments; generation renderer 8 (the current
renderer) renders `llms.txt` with each generation's configured `publicBaseUrl`
so a deployment at another origin publishes its own registry instructions.
Generations of renderer 1 to 7 stay valid.

## First-party packages

`stuff publish npm --tarball PATH` hosts a package that exists nowhere upstream
(see [docs/PUBLISHING.md](../../docs/PUBLISHING.md)). It is an ordinary artifact
record whose `artifact` object carries the extra key `"firstParty": true`; the key
is absent from every other record, so existing manifests, inventories and
generation ids are unchanged. A first-party record's `sourceUrl` is its own
`dist.tarball` on the publishing registry instead of a `registry.npmjs.org` URL.
The live generation manifest is the only place the records persist. Older binaries
reject a manifest that contains one.

## Adopting a pulled publication

`mynpm publish` extends the `mirror/current` generation of its site directory, so a
site without it would drop everything live. `deploy/r2-pull.py BUCKET SITE/mirror`
fetches the live generation and tarball store, and `mynpm adopt --site-dir SITE` makes
it publishable:

- It re-creates the `tarballs/` and `-/tarballs/` hardlink aliases that `stuff publish`
  does not upload.
- It verifies the generation: manifest shape, packuments re-rendered from the manifest
  records, every tarball's SHA-512, and the generation id. A generation published before
  catalog fingerprints joined the id (the id of a renderer 3 to 5 generation without
  `catalogFingerprint`) is accepted; its catalog, landing page, and `llms.txt` are not
  compared because the catalog renderer has changed since.
  A generation sealed under an older catalog renderer stays valid: its seal is checked
  against the catalog, landing page, and `llms.txt` stored in the generation instead of a
  fresh render, so a catalog renderer change never strands published generations.
- It republishes the same records under the current renderer and identity, switching
  `current` to the new generation. The pulled generation stays in place. Renderer 1 and 2
  generations are refused.

Run it again on an unchanged site and it reports `Already published`.
