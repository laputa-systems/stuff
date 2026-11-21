import assert from "node:assert/strict";
import test from "node:test";
import { createHash } from "node:crypto";
import { spawn, execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { createServer } from "node:net";
import { request as httpRequest } from "node:http";
import { join, resolve } from "node:path";
import { generate } from "../scripts/orange.mjs";

const workerDir = resolve(import.meta.dirname, "..");
const root = resolve(workerDir, "../..");
const worker = join(workerDir, "build/orange/workers/default/bundle/entry.js");
const bin = join(workerDir, "orange/node_modules/open-orange/dist/bin.js");
const host = "stuff.17166969.xyz";
const digest = (text) => createHash("sha256").update(text).digest("hex");

async function freePort() {
  const server = createServer();
  await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
  const port = server.address().port;
  await new Promise((ok) => server.close(ok));
  return port;
}

function wrapperSource() {
  return `import worker, { PublicationCoordinator as Base } from ${JSON.stringify(worker)};
export class PublicationCoordinator extends Base {
  async fetch(req) {
    if (new URL(req.url).pathname === "/__sql") {
      for (const [query, ...args] of await req.json()) this.state.storage.sql.exec(query, ...args);
      return new Response("ok");
    }
    return super.fetch(req);
  }
}
export default { async fetch(req, env, ctx) {
  const url = new URL(req.url);
  if (url.pathname === "/__seed") {
    for (const [key, value] of await req.json()) await env.MYCRATES.put(key, value);
    return new Response("ok");
  }
  if (url.pathname === "/__sql") {
    return env.COORDINATOR.get(env.COORDINATOR.idFromName("cargo")).fetch(new Request("https://coordinator/__sql", { method: "POST", body: await req.text() }));
  }
  return worker.fetch(req, env, ctx);
} };
`;
}

async function startInstance(scratch, label) {
  const directory = mkdtempSync(join(scratch, `handoff-${label}-`));
  const configPath = join(directory, "orange.jsonc");
  const config = generate(configPath, `handoff-${label}`);
  const wrapper = join(directory, "wrapper.mjs");
  writeFileSync(wrapper, wrapperSource());
  config.main = wrapper;
  config.vars.STUFF_COORDINATOR_ENABLED = "true";
  config.vars.STUFF_COORDINATOR_TOKEN = "test-secret";
  writeFileSync(configPath, JSON.stringify(config));
  const port = await freePort();
  const child = spawn(process.execPath, [bin, "dev", "--json", "--ip", "127.0.0.1", "--port", String(port), "--config", configPath], { cwd: directory, stdio: ["ignore", "pipe", "pipe"] });
  let logs = "";
  await new Promise((ok, fail) => {
    child.stdout.on("data", (chunk) => { logs += chunk; for (const line of logs.split("\n")) { try { const event = JSON.parse(line); if (event.type === "ready") ok(); if (event.type === "fatal" || event.type === "error") fail(new Error(line)); } catch (error) { if (!(error instanceof SyntaxError)) fail(error); } } });
    child.stderr.on("data", (chunk) => { logs += chunk; });
    child.once("exit", (code) => fail(new Error(`orange exited ${code}: ${logs}`)));
    setTimeout(() => fail(new Error(`orange readiness timeout: ${logs}`)), 60000).unref();
  });
  const request = (path, method = "GET", body) => new Promise((ok, fail) => {
    const headers = { host, authorization: "Bearer test-secret" };
    if (body !== undefined) {
      headers["content-type"] = "application/json";
      headers["content-length"] = Buffer.byteLength(body);
    }
    const req = httpRequest({ host: "127.0.0.1", port, path, method, headers }, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => ok({ status: res.statusCode, headers: res.headers, text: Buffer.concat(chunks).toString() }));
    });
    req.on("error", fail);
    req.end(body);
  });
  const manage = async (op, body) => {
    const response = await request(`/_publication/cargo/${op}`, body === undefined ? "GET" : "POST", body === undefined ? undefined : JSON.stringify(body));
    assert.equal(response.status, 200, `${label} ${op}: ${response.text}`);
    return JSON.parse(response.text);
  };
  return { directory, child, request, manage };
}

test("Orange coordinator handoff freezes, exports, imports and thaws a fresh primary", { timeout: 180000 }, async (t) => {
  execFileSync("pnpm", ["run", "build"], { cwd: workerDir, stdio: "inherit" });
  const scratch = join(root, ".work/tmp");
  mkdirSync(scratch, { recursive: true });
  const source = await startInstance(scratch, "source");
  const target = await startInstance(scratch, "target");
  const stop = (instance) => new Promise((ok) => {
    if (instance.child.exitCode !== null) return ok();
    instance.child.once("exit", ok);
    instance.child.kill("SIGTERM");
  });
  t.after(async () => {
    await Promise.all([stop(source), stop(target)]);
    rmSync(source.directory, { recursive: true, force: true });
    rmSync(target.directory, { recursive: true, force: true });
  });

  const manifest = JSON.stringify({ schemaVersion: 1, objects: [] });
  const manifestHash = digest(manifest);
  const payload = "x".repeat(20000);
  await source.request("/__seed", "POST", JSON.stringify([["current", "g0"], ["manifests/g0.json", manifest], ["manifests/g1.json", manifest]]));
  await source.request("/__sql", "POST", JSON.stringify([
    ["INSERT INTO retired_generations VALUES (?)", "g-old"],
    ["INSERT INTO retired_versions VALUES (?, ?)", "blobs/retired", "v1"],
    ["INSERT INTO receipts VALUES (?, ?, ?, ?, ?)", "synthetic", payload, 0, "g0", manifestHash],
  ]));

  const first = await source.manage("begin", {});
  assert.equal(first.revision, 0);
  const frozen = await source.manage("freeze", {});
  assert.equal(frozen.current.revision, 0);
  assert.equal(frozen.current.generation, "g0");
  assert.equal(frozen.liveLease, true);

  for (const op of ["begin", "gc-claim"]) {
    const blocked = await source.request(`/_publication/cargo/${op}`, "POST", "{}");
    assert.equal(blocked.status, 503, `${op} must be frozen`);
    assert.equal(blocked.headers["retry-after"], "30");
    assert.deepEqual(JSON.parse(blocked.text), { error: "frozen" });
  }
  const readable = await source.manage("current");
  assert.equal(readable.revision, 0);
  assert.equal(readable.generation, "g0");

  const held = await source.request("/_publication/cargo/export");
  assert.equal(held.status, 409, "export must wait for the live lease");

  await source.manage("renew", { token: first.token });
  const activation = { token: first.token, key: "handoff-activate", generation: "g1", manifest: manifestHash, expectedRevision: 0 };
  const activated = await source.request("/_publication/cargo/activate", "POST", JSON.stringify(activation));
  assert.equal(activated.status, 200, activated.text);

  const exported = await source.request("/_publication/cargo/export");
  assert.equal(exported.status, 200, exported.text);
  const sourceExport = JSON.parse(exported.text);
  assert.equal(sourceExport.schemaVersion, 1);
  assert.equal(sourceExport.registry, "cargo");
  assert.equal(sourceExport.current.revision, 1);
  assert.equal(sourceExport.current.generation, "g1");
  assert.equal(sourceExport.current.manifest, manifestHash);
  assert.ok(JSON.stringify(sourceExport).length > 16384, "export must exceed the normal request cap");
  assert.ok(sourceExport.receipts.some((receipt) => receipt.key === "handoff-activate"));
  assert.ok(sourceExport.receipts.some((receipt) => receipt.key === "synthetic" && receipt.payload === payload));
  assert.deepEqual(sourceExport.retired_generations, ["g-old"]);
  assert.deepEqual(sourceExport.retired_versions, [{ key: "blobs/retired", version_id: "v1" }]);

  const imported = await target.request("/_publication/cargo/import", "POST", JSON.stringify(sourceExport));
  assert.equal(imported.status, 200, imported.text);

  const stillFrozen = await target.request("/_publication/cargo/begin", "POST", "{}");
  assert.equal(stillFrozen.status, 503, "import must leave the target frozen");

  const targetExported = await target.request("/_publication/cargo/export");
  assert.equal(targetExported.status, 200, targetExported.text);
  const targetExport = JSON.parse(targetExported.text);
  assert.deepEqual(
    { revision: targetExport.current.revision, generation: targetExport.current.generation, manifest: targetExport.current.manifest },
    { revision: sourceExport.current.revision, generation: sourceExport.current.generation, manifest: sourceExport.current.manifest },
  );
  assert.deepEqual(targetExport.receipts, sourceExport.receipts);
  assert.deepEqual(targetExport.retired_generations, sourceExport.retired_generations);
  assert.deepEqual(targetExport.retired_versions, sourceExport.retired_versions);

  const duplicateTarget = await target.request("/_publication/cargo/import", "POST", JSON.stringify(sourceExport));
  assert.equal(duplicateTarget.status, 409, "import into a non-empty coordinator must be refused");
  const duplicateSource = await source.request("/_publication/cargo/import", "POST", JSON.stringify(sourceExport));
  assert.equal(duplicateSource.status, 409, "import into the non-empty source must be refused");

  const sourceStillFrozen = await source.request("/_publication/cargo/begin", "POST", "{}");
  assert.equal(sourceStillFrozen.status, 503, "the source must stay frozen after export");

  await target.manage("thaw", {});
  const resumed = await target.manage("begin", {});
  assert.equal(resumed.revision, 1);
  assert.ok(resumed.token);
  await target.manage("abort", { token: resumed.token });
});
