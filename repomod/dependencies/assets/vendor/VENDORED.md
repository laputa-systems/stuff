# Vendored atlas engine

`atlas.vendor.js` is a build-time bundle of the pinned npm packages below. It is checked
in so the dashboard renders with no Node, npm, or network. It is loaded only by
`explore.html`; every other page stays engine-free.

| Package | Version | License | npm tarball sha256 |
| --- | --- | --- | --- |
| sigma | 4.0.6 | MIT | `eba961adf8cd661ec2c29134598a735e0fbcd494944f574e72e50d95e97140b7` |
| graphology | 0.26.0 | MIT | `3c0cc63556e32b9d00ea953dce29790a5e49fc448f19247e25540156caef6b98` |
| graphology-utils (sigma dep) | 2.5.2 | MIT | resolved via `tools/atlas-vendor/package-lock.json` |
| graphology-types (utils dep) | 0.24.8 | MIT | resolved via `tools/atlas-vendor/package-lock.json` |
| events (graphology/sigma dep) | 3.3.0 | MIT | resolved via `tools/atlas-vendor/package-lock.json` |

`atlas.vendor.js` sha256: `8d029c9209e71ac7d02f520b6d71856f9f8ad175d697849ed79f65488c3a86ed`

License texts for every bundled package sit next to the bundle (`*-LICENSE*`).

The focus layout is computed by first-party code (`layeredPositions` in `atlas.js`:
BFS layering with a barycenter ordering pass). No physics/layout library ships in the
bundle.

## Rebuild

```sh
cd tools/atlas-vendor
npm ci
npm run build
```

`npm ci` uses the committed lockfile; `build.mjs` (esbuild, bundle, minify, IIFE global
`AtlasVendor`) writes `repomod/dependencies/assets/vendor/atlas.vendor.js`. Verify the
sha256 above after any rebuild and update this file. No bundled package is used at
dashboard render time; the dashboard only copies the committed file.
