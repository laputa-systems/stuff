import { bindings, defineConfig, triggers } from "cf/config";
import * as entrypoint from "./cloudflare.ts" with { type: "cf-worker" };

// Read replica for the registry hostnames. The Worker is attached as routes,
// not custom domains: a custom domain would take the hostname away from the
// tunnel origin, while a route delivers the request here first and lets
// `fetch(request)` reach the origin. There is no COORDINATOR binding and no
// Durable Object export, so entry.ts reads each bucket's `current` pointer.
const HOSTS = [
	"crates.17166969.xyz",
	"crates-blobs.17166969.xyz",
	"npm.17166969.xyz",
	"pypi.17166969.xyz",
	"stuff.17166969.xyz",
	"oci.17166969.xyz",
	"oci-blobs.17166969.xyz",
	"mirror.17166969.xyz",
] as const;

export default defineConfig(() => ({
	worker: {
		name: "stuff-failover",
		compatibilityDate: "2026-10-30",
		entrypoint,
		triggers: HOSTS.map((host) => triggers.fetch({ pattern: `${host}/*`, zone: "17166969.xyz" })),
		env: {
			STUFF_ROUTES: bindings.text("[{\"host\":\"crates.17166969.xyz\",\"bucket_binding\":\"MYCRATES\",\"key_prefix\":\"\"},{\"host\":\"crates-blobs.17166969.xyz\",\"bucket_binding\":\"MYCRATES\",\"key_prefix\":\"\"},{\"host\":\"npm.17166969.xyz\",\"bucket_binding\":\"MYNPM\",\"key_prefix\":\"\"},{\"host\":\"pypi.17166969.xyz\",\"bucket_binding\":\"PYPI\",\"key_prefix\":\"\"},{\"host\":\"oci.17166969.xyz\",\"bucket_binding\":\"OCI\",\"key_prefix\":\"\"},{\"host\":\"mirror.17166969.xyz\",\"bucket_binding\":\"MIRROR\",\"key_prefix\":\"\"}]"),
			STUFF_CARGO_BLOB_HOST: bindings.text("crates-blobs.17166969.xyz"),
			STUFF_OCI_BLOB_HOST: bindings.text("oci-blobs.17166969.xyz"),
			STUFF_UNIFIED_HOST: bindings.text("stuff.17166969.xyz"),
			STUFF_OCI_HOST: bindings.text("oci.17166969.xyz"),
			STUFF_OCI_BLOB_ORIGIN: bindings.text("https://oci-blobs.17166969.xyz"),
			MYCRATES: bindings.r2({
				name: "stuff-mycrates",
			}),
			MYNPM: bindings.r2({
				name: "stuff-mynpm",
			}),
			PYPI: bindings.r2({
				name: "stuff-mypypi",
			}),
			OCI: bindings.r2({
				name: "stuff-oci",
			}),
			MIRROR: bindings.r2({
				name: "stuff-mirror",
			}),
			OCI_BLOBS: bindings.r2({
				name: "stuff-oci-blobs",
			}),
			STUFF_RELEASE: bindings.text("replica"),
		},
	},
}));
