import assert from "node:assert/strict";
import test from "node:test";
import { createHash } from "node:crypto";
import { execFileSync, spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import { join, resolve } from "node:path";
import { generate } from "../scripts/orange.mjs";
import { nativeHarness } from "./native-harness.mjs";
import { fakeS3 } from "./native-s3.mjs";

const workerDir = resolve(import.meta.dirname, "..");
const root = resolve(workerDir, "../..");
const bin = join(workerDir, "orange/node_modules/open-orange/dist/bin.js");
const app = join(workerDir, "build/native/app");
const digest = (text) => createHash("sha256").update(text).digest("hex");
const md5 = (text) => createHash("md5").update(text).digest("hex");
const BUCKETS = { MYCRATES: "stuff-mycrates", MYNPM: "stuff-mynpm", PYPI: "stuff-mypypi", OCI: "stuff-oci", OCI_BLOBS: "stuff-oci-blobs", MIRROR: "stuff-mirror" };
const tailnet = { "x-oo-ingress": "tailnet", authorization: "Bearer coordinator" };

async function freePort() {
  const server = createServer();
  await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
  const port = server.address().port;
  await new Promise((ok) => server.close(ok));
  return port;
}

async function startLegacy(directory, endpoint) {
  const configPath = join(directory, "orange.jsonc");
  const config = generate(configPath, "legacy");
  Object.assign(config.vars, { STUFF_COORDINATOR_ENABLED: "true", STUFF_COORDINATOR_TOKEN: "coordinator", STUFF_PUBLISH_HOST: "publish.test", STUFF_S3_ACCESS_KEY_ID: "service", STUFF_S3_SECRET_ACCESS_KEY: "service-secret", S3_ENDPOINT: endpoint, S3_REGION: "us-east-1", S3_ACCESS_KEY_ID: "test", S3_SECRET_ACCESS_KEY: "test" });
  writeFileSync(configPath, JSON.stringify(config));
  const env = { ...process.env };
  for (const name of Object.values(BUCKETS)) {
    const prefix = `ORANGE_R2_${name.toUpperCase().replace(/[^A-Z0-9]/g, "_")}_S3_`;
    Object.assign(env, { [`${prefix}ENDPOINT`]: endpoint, [`${prefix}REGION`]: "us-east-1", [`${prefix}ACCESS_KEY_ID`]: "test", [`${prefix}SECRET_ACCESS_KEY`]: "test" });
  }
  const port = await freePort();
  const child = spawn(process.execPath, [bin, "dev", "--json", "--ip", "127.0.0.1", "--port", String(port), "--config", configPath], { cwd: directory, env, stdio: ["ignore", "pipe", "pipe"] });
  let logs = "";
  await new Promise((ok, fail) => {
    child.stdout.on("data", chunk => { logs += chunk; for (const line of logs.split("\n")) { try { const event = JSON.parse(line); if (event.type === "ready") ok(); if (event.type === "fatal") fail(new Error(line)); } catch (error) { if (!(error instanceof SyntaxError)) fail(error); } } });
    child.stderr.on("data", chunk => { logs += chunk; });
    child.once("exit", code => fail(new Error(`orange exited ${code}: ${logs}`)));
    setTimeout(() => fail(new Error(`orange readiness timeout: ${logs}`)), 90000).unref();
  });
  return { port, child, stop: () => new Promise(ok => { if (child.exitCode !== null) return ok(); child.once("exit", ok); child.kill("SIGTERM"); }) };
}

function stage(s3, bucket, generation, files) {
  const objects = Object.entries(files).map(([path, text]) => {
    const key = `generations/${generation}/${path}`;
    s3.put(bucket, key, text);
    return { key, size: Buffer.byteLength(text), etag: md5(text) };
  });
  const manifest = JSON.stringify({ schemaVersion: 1, objects });
  s3.put(bucket, `manifests/${generation}.json`, manifest);
  return digest(manifest);
}

test("writer handoff from the legacy Orange coordinator to the native host", { timeout: 300000 }, async (t) => {
  execFileSync(process.execPath, [join(workerDir, "scripts/build-native.mjs")], { cwd: workerDir, stdio: "ignore" });
  mkdirSync(join(root, ".work/tmp"), { recursive: true });
  const directory = mkdtempSync(join(root, ".work/tmp/handoff-native-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  stage(s3, BUCKETS.MYCRATES, "g0", { "catalog.json": "{}" });
  s3.put(BUCKETS.MYCRATES, "current", "g0");

  const legacy = await startLegacy(mkdtempSync(join(directory, "legacy-")), endpoint);
  t.after(() => legacy.stop());
  mkdirSync(join(directory, "native"));
  execFileSync(process.execPath, [join(app, "native/authority-init.mjs"), join(directory, "native/state"), "legacy", `127.0.0.1:${legacy.port}`]);
  const start = async () => {
    const harness = nativeHarness({ STUFF_S3_BUCKET_BINDINGS: JSON.stringify(BUCKETS) }, { role: "publisher", directory: join(directory, "native"), s3, endpoint });
    t.after(() => harness.close());
    await harness.listen();
    return harness;
  };
  let native = await start();
  const op = async (registry, name, body) => {
    const response = await native.fetch(`https://publish.test/_publication/${registry}/${name}`, body === undefined ? { headers: tailnet } : { method: "POST", headers: { ...tailnet, "content-type": "application/json" }, body: JSON.stringify(body) });
    return { status: response.status, retryAfter: response.headers.get("retry-after"), body: await response.json() };
  };
  const read = async () => (await native.fetch("https://crates.test/catalog.json")).text();

  const lease1 = await op("cargo", "begin", {});
  assert.equal(lease1.status, 200);
  const g1 = stage(s3, BUCKETS.MYCRATES, "g1", { "catalog.json": '{"g":1}' });
  const legacyActivation = { token: lease1.body.token, key: "legacy-g1", generation: "g1", manifest: g1, expectedRevision: 0 };
  assert.deepEqual((await op("cargo", "activate", legacyActivation)).body, { revision: 1, generation: "g1", manifest: g1 });
  assert.equal(await read(), '{"g":1}');

  const inFlight = await op("cargo", "begin", {});
  assert.equal(inFlight.status, 200);
  const frozen = await op("cargo", "freeze", {});
  assert.equal(frozen.body.liveLease, true);
  assert.equal((await op("cargo", "begin", {})).status, 503);
  assert.equal((await op("cargo", "export")).status, 409);
  const g2 = stage(s3, BUCKETS.MYCRATES, "g2", { "catalog.json": '{"g":2}' });
  assert.equal((await op("cargo", "activate", { token: inFlight.body.token, key: "legacy-g2", generation: "g2", manifest: g2, expectedRevision: 1 })).status, 200);
  for (const registry of ["npm", "pypi", "oci", "mirror"]) assert.equal((await op(registry, "freeze", {})).status, 200);

  const exports = {};
  for (const registry of ["cargo", "npm", "pypi", "oci", "mirror"]) {
    const exported = await op(registry, "export");
    assert.equal(exported.status, 200, `${registry} export`);
    exports[registry] = exported.body;
  }
  assert.equal(exports.cargo.current.generation, s3.get(BUCKETS.MYCRATES, "current"));
  assert.equal(exports.cargo.current.pending, 0);
  assert.deepEqual(exports.cargo.receipts.map(receipt => receipt.key), ["legacy-g1", "legacy-g2"]);

  for (const [registry, exported] of Object.entries(exports)) {
    const imported = await native.control(`/coordinators/${registry}/import`, { method: "POST", body: JSON.stringify(exported) });
    assert.equal(imported.status, 200, `${registry} import`);
  }
  await native.stop("SIGKILL");
  native = await start();
  for (const [registry, exported] of Object.entries(exports)) {
    const dump = await (await native.control(`/coordinators/${registry}/dump`)).json();
    assert.deepEqual({ schemaVersion: dump.schemaVersion, registry: dump.registry, current: dump.current, receipts: dump.receipts, retired_generations: dump.retired_generations, retired_versions: dump.retired_versions }, exported, `${registry} canonical state`);
    assert.equal(dump.frozen, true);
  }

  await legacy.stop();
  const identity = await (await native.control("/identity")).json();
  const switched = await native.control("/authority", { method: "POST", body: JSON.stringify({ expectedGeneration: identity.authority.generation, publication: "native", reason: "rehearsal handoff" }) });
  assert.equal(switched.status, 200);
  const stale = await native.control("/authority", { method: "POST", body: JSON.stringify({ expectedGeneration: identity.authority.generation, publication: "native", reason: "stale controller" }) });
  assert.equal(stale.status, 409);

  const held = await op("cargo", "begin", {});
  assert.equal(held.status, 503);
  assert.equal(held.retryAfter, "30");
  assert.deepEqual((await op("cargo", "activate", legacyActivation)).body, { revision: 1, generation: "g1", manifest: g1 });
  for (const registry of ["cargo", "npm", "pypi", "oci", "mirror"]) assert.equal((await op(registry, "thaw", {})).status, 200);
  const lease3 = await op("cargo", "begin", {});
  assert.equal(lease3.status, 200);
  assert.equal(lease3.body.revision, 2);
  const g3 = stage(s3, BUCKETS.MYCRATES, "g3", { "catalog.json": '{"g":3}' });
  assert.deepEqual((await op("cargo", "activate", { token: lease3.body.token, key: "native-g3", generation: "g3", manifest: g3, expectedRevision: 2 })).body, { revision: 3, generation: "g3", manifest: g3 });
  assert.equal(s3.get(BUCKETS.MYCRATES, "current"), "g3");
  assert.equal(await read(), '{"g":3}');
});
