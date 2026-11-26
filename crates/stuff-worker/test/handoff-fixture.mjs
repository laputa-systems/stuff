import { createHash } from "node:crypto";
import { execFileSync, spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import { join, resolve } from "node:path";
import { generate } from "../scripts/orange.mjs";
import { nativeHarness } from "./native-harness.mjs";
import { fakeS3 } from "./native-s3.mjs";

export const workerDir = resolve(import.meta.dirname, "..");
export const root = resolve(workerDir, "../..");
const bin = join(workerDir, "orange/node_modules/open-orange/dist/bin.js");
export const app = join(workerDir, "build/native/app");
export const digest = (text) => createHash("sha256").update(text).digest("hex");
const md5 = (text) => createHash("md5").update(text).digest("hex");
export const BUCKETS = { MYCRATES: "stuff-mycrates", MYNPM: "stuff-mynpm", PYPI: "stuff-mypypi", OCI: "stuff-oci", OCI_BLOBS: "stuff-oci-blobs", MIRROR: "stuff-mirror" };
export const tailnet = { "x-oo-ingress": "tailnet", authorization: "Bearer coordinator" };

async function freePort() {
  const server = createServer();
  await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
  const port = server.address().port;
  await new Promise((ok) => server.close(ok));
  return port;
}

export async function startLegacy(directory, endpoint) {
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
  return { port, child, logs: () => logs, stop: () => new Promise(ok => { if (child.exitCode !== null) return ok(); child.once("exit", ok); child.kill("SIGTERM"); }) };
}

export function stage(s3, bucket, generation, files) {
  const objects = Object.entries(files).map(([path, text]) => {
    const key = `generations/${generation}/${path}`;
    s3.put(bucket, key, text);
    return { key, size: Buffer.byteLength(text), etag: md5(text) };
  });
  const manifest = JSON.stringify({ schemaVersion: 1, objects });
  s3.put(bucket, `manifests/${generation}.json`, manifest);
  return digest(manifest);
}

const controller = join(root, "deploy/native/handoff.mjs");
export function runController(configFile, journalDir, command, until, env = {}) {
  return new Promise(resolve => {
    const child = spawn(process.execPath, [controller, configFile, journalDir, command, ...(until ? ["--until", until] : [])], { stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, ...env } });
    let output = "";
    child.stdout.on("data", chunk => { output += chunk; });
    child.stderr.on("data", chunk => { output += chunk; });
    child.on("close", status => resolve({ status, output }));
  });
}

export async function controllerFixture(t, options = {}) {
  mkdirSync(join(root, ".work/tmp"), { recursive: true });
  const directory = mkdtempSync(join(root, ".work/tmp/handoff-controller-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  for (const bucket of [BUCKETS.MYCRATES, BUCKETS.MYNPM, BUCKETS.PYPI, BUCKETS.OCI, BUCKETS.MIRROR]) {
    stage(s3, bucket, "g0", { "catalog.json": "{}" });
    s3.put(bucket, "current", "g0");
  }
  const legacyDirectory = mkdtempSync(join(root, ".work/tmp/handoff-legacy-"));
  t.after(() => rmSync(legacyDirectory, { recursive: true, force: true }));
  const legacy = await startLegacy(legacyDirectory, endpoint);
  t.after(() => legacy.stop());
  mkdirSync(join(directory, "native"));
  execFileSync(process.execPath, [join(app, "native/authority-init.mjs"), join(directory, "native/state"), "legacy", `127.0.0.1:${legacy.port}`]);
  const native = nativeHarness({ STUFF_S3_BUCKET_BINDINGS: JSON.stringify(BUCKETS) }, { role: "publisher", directory: join(directory, "native"), s3, endpoint });
  t.after(() => native.close());
  const ports = await native.listen();
  const envFile = join(directory, "main.env");
  writeFileSync(envFile, `S3_ENDPOINT=${endpoint}\nS3_REGION=us-east-1\nS3_ACCESS_KEY_ID=test\nS3_SECRET_ACCESS_KEY=test\nSTUFF_COORDINATOR_TOKEN=coordinator\nSTUFF_NATIVE_CONTROL_TOKEN=control\n`);
  const configFile = join(directory, "handoff.json");
  writeFileSync(configFile, JSON.stringify({ listen: `127.0.0.1:${ports.listen.port}`, control: `127.0.0.1:${ports.control.port}`, legacy: `127.0.0.1:${legacy.port}`, publishHost: "publish.test", envFile, artifact: app, buckets: BUCKETS, fence: { stop: [["kill", String(legacy.child.pid)], ["sleep", "2"]], restore: [["true"]] }, ...options }));
  const op = async (registry, name, body) => {
    const response = await native.fetch(`https://publish.test/_publication/${registry}/${name}`, body === undefined ? { headers: tailnet } : { method: "POST", headers: { ...tailnet, "content-type": "application/json" }, body: JSON.stringify(body) });
    return { status: response.status, body: await response.json() };
  };
  return { directory, s3, legacy, native, configFile, op };
}

