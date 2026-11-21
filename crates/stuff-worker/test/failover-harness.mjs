import { execFileSync } from "node:child_process";
import { cpSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { createTestHarness } from "wrangler";

export const workerDir = fileURLToPath(new URL("..", import.meta.url));
const builtBundle = join(workerDir, "build/orange/workers/default/bundle");
export const bundle = join(workerDir, "build/failover-test");
const harnessRoot = fileURLToPath(new URL("../../../.work/tmp", import.meta.url));

export const ROUTES = JSON.stringify([
  { host: "crates.test", bucket_binding: "MYCRATES", key_prefix: "" },
  { host: "crates-blobs.test", bucket_binding: "MYCRATES", key_prefix: "" },
  { host: "npm.test", bucket_binding: "MYNPM", key_prefix: "" },
  { host: "pypi.test", bucket_binding: "PYPI", key_prefix: "" },
  { host: "oci.test", bucket_binding: "OCI", key_prefix: "" },
  { host: "oci-blobs.test", bucket_binding: "OCI_BLOBS", key_prefix: "" },
  { host: "mirror.test", bucket_binding: "MIRROR", key_prefix: "" },
]);

// The OpenOrange build emits entry.ts as its main module. The replica
// entrypoint is compiled separately so the origin requester can be injected,
// which is what lets the failover decision run without a network.
export function buildFailoverBundle() {
  rmSync(bundle, { recursive: true, force: true });
  execFileSync(join(workerDir, "node_modules/.bin/tsrs"), [
    "--fast", "--ignoreConfig",
    "--target", "es2022", "--module", "esnext", "--moduleResolution", "bundler",
    "--allowImportingTsExtensions", "--rewriteRelativeImportExtensions", "--skipLibCheck",
    "--lib", "ES2022,DOM,DOM.Iterable",
    "--outDir", bundle,
    "cloudflare.ts",
  ], { cwd: workerDir, stdio: "inherit" });
  cpSync(join(builtBundle, "build/wasm"), join(bundle, "build/wasm"), { recursive: true });
  cpSync(join(builtBundle, "vendor"), join(bundle, "vendor"), { recursive: true });
}

const ORIGIN_NAME = "ORIGIN_ATTEMPTS";

/**
 * Start a harness whose entrypoint is the replica Worker. `originSource` is the
 * body of the origin's `fetch(request, env)`; it returns a Response, throws, or
 * never settles. Every attempt increments the ORIGIN_ATTEMPTS KV counter, which
 * the test reads back, so "the origin was tried exactly once" is observable.
 *
 * With `r2: false` no R2 binding is declared at all; the entry handler throws on
 * any bucket access, which makes "the replica was not read" a decisive signal.
 */
export async function harness(t, originSource, options = {}) {
  const { r2 = true } = options;
  mkdirSync(harnessRoot, { recursive: true });
  writeFileSync(
    join(bundle, "origin.js"),
    [
      "export default {",
      "  async fetch(request, env) {",
      `    const attempts = Number(await env.${ORIGIN_NAME}.get("count") ?? "0");`,
      `    await env.${ORIGIN_NAME}.put("count", String(attempts + 1));`,
      `    ${originSource}`,
      "  },",
      "};",
      "",
    ].join("\n"),
  );
  writeFileSync(
    join(bundle, "main.js"),
    [
      'import { createFailoverWorker } from "./cloudflare.js";',
      'import origin from "./origin.js";',
      "export default {",
      "  async fetch(request, env, context) {",
      "    const worker = createFailoverWorker({",
      "      origin: (outbound) => origin.fetch(outbound, env),",
      "      headerTimeoutMs: 250,",
      "    });",
      "    return worker.fetch(request, env, context);",
      "  },",
      "};",
      "",
    ].join("\n"),
  );
  const config = {
    name: "stuff-failover-test",
    main: join(bundle, "main.js"),
    modules: true,
    compatibility_date: "2026-10-30",
    compatibility_flags: [],
    no_bundle: true,
    rules: [
      { type: "ESModule", globs: ["**/*.js"], fallthrough: true },
      { type: "CompiledWasm", globs: ["**/*.wasm"], fallthrough: true },
    ],
    kv_namespaces: [{ binding: ORIGIN_NAME, id: "failover-origin-attempts" }],
    vars: {
      STUFF_RELEASE: "test",
      STUFF_ROUTES: ROUTES,
      STUFF_UNIFIED_HOST: "stuff.test",
      STUFF_OCI_HOST: "oci.test",
    },
  };
  if (r2) {
    config.r2_buckets = ["MYCRATES", "MYNPM", "PYPI", "OCI", "OCI_BLOBS", "MIRROR"].map((binding) => ({
      binding,
      bucket_name: binding.toLowerCase().replaceAll("_", "-"),
    }));
  }
  const server = createTestHarness({
    root: harnessRoot,
    workers: [{ config }],
  });
  t.after(() => server.close());
  await server.listen();
  return server;
}

/** Read and reset the origin attempt counter. */
export async function originAttempts(server) {
  const env = await server.getWorker().getEnv();
  const count = Number(await env[ORIGIN_NAME].get("count") ?? "0");
  await env[ORIGIN_NAME].put("count", "0");
  return count;
}

/**
 * Import the compiled pure decision module in this process. The bundle is
 * emitted by `buildFailoverBundle`, so the unit tests exercise the same source
 * the Worker runs without starting workerd.
 */
export async function decisionModule() {
  return await import(join(bundle, "src/failover.js"));
}
