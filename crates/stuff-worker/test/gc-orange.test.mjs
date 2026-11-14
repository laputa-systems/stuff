import assert from "node:assert/strict";
import test from "node:test";
import { createHash } from "node:crypto";
import { spawn, execFileSync } from "node:child_process";
import { createServer, request } from "node:http";
import { mkdirSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { resolve, join } from "node:path";
import { generate } from "../scripts/orange.mjs";

const workerDir = resolve(import.meta.dirname, "..");
const root = resolve(workerDir, "../..");
const hash = text => createHash("sha256").update(text).digest("hex");
const etag = text => createHash("md5").update(text).digest("hex");
async function listen(server) { await new Promise(ok => server.listen(0, "127.0.0.1", ok)); return server.address().port; }

test("Orange GC retires exact versions and permits a fresh upload of the same blob", { timeout: 120000 }, async t => {
  execFileSync("pnpm", ["run", "build"], { cwd: workerDir, stdio: "inherit" });
  mkdirSync(join(root, ".work/tmp"), { recursive: true });
  const directory = mkdtempSync(join(root, ".work/tmp/gc-orange-"));
  const objects = new Map();
  const versions = new Map();
  let versioned = true;
  let failDelete = false;
  let number = 0;
  const deleted = [];
  function put(key, text, version = `v${++number}`) {
    const item = { key, text, version, size: Buffer.byteLength(text), etag: etag(text) };
    const existing = versions.get(key) ?? new Map();
    existing.set(version, item); versions.set(key, existing); objects.set(key, item);
    return item;
  }
  const backend = createServer((req, res) => {
    const url = new URL(req.url, "http://backend");
    if (url.pathname === "/__set") { const chunks = []; req.on("data", chunk => chunks.push(chunk)); req.on("end", () => { const [key, text] = JSON.parse(Buffer.concat(chunks)); put(key, text); res.end("ok"); }); return; }
    if (url.pathname === "/__object") { const item = objects.get(url.searchParams.get("key")); res.writeHead(item ? 200 : 404, { "content-type": "application/json" }); res.end(item ? JSON.stringify(item) : "{}"); return; }
    if (url.pathname === "/__list") { res.end(JSON.stringify([...objects.keys()].filter(key => key.startsWith(url.searchParams.get("prefix"))).map(key => ({ key })))); return; }
    if (url.searchParams.has("versioning")) { res.end(`<VersioningConfiguration><Status>${versioned ? "Enabled" : "Suspended"}</Status></VersioningConfiguration>`); return; }
    const key = decodeURIComponent(url.pathname.replace(/^\/[^/]+\/?/, ""));
    if (url.searchParams.has("versions")) {
      const prefix = url.searchParams.get("prefix");
      res.end(`<ListVersionsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>false</IsTruncated>${[...versions].filter(([key]) => key.startsWith(prefix)).flatMap(([key, items]) => [...items.keys()].map(version => `<Version><Key>${key}</Key><VersionId>${version}</VersionId></Version>`)).join("")}</ListVersionsResult>`); return;
    }
    if (req.method === "HEAD") { const item = objects.get(key); res.writeHead(item ? 200 : 404, item ? { "x-amz-version-id": item.version } : {}); res.end(); return; }
    if (req.method === "DELETE") {
      const version = url.searchParams.get("versionId");
      assert.ok(version, "GC must delete specific versions");
      if (failDelete) { res.writeHead(503); res.end(); return; }
      deleted.push([key, version]);
      const items = versions.get(key); items?.delete(version);
      if (objects.get(key)?.version === version) {
        const remaining = items && [...items.values()].at(-1);
        if (remaining) objects.set(key, remaining); else objects.delete(key);
      }
      res.writeHead(204); res.end(); return;
    }
    res.writeHead(404); res.end();
  });
  const backendPort = await listen(backend);
  const holder = createServer(); const port = await listen(holder); await new Promise(ok => holder.close(ok));
  const configPath = join(directory, "orange.jsonc");
  const config = generate(configPath, "gc-test");
  const wrapper = join(directory, "wrapper.mjs");
  const worker = join(workerDir, ".cloudflare/output/v0/workers/default/bundle/entry.js");
  writeFileSync(wrapper, `import worker, { PublicationCoordinator as Base } from ${JSON.stringify(worker)};
let offset=0; const now=Date.now; Date.now=()=>now()+offset;
const endpoint=${JSON.stringify(`http://127.0.0.1:${backendPort}`)};
const store={async get(key){const response=await fetch(endpoint+'/__object?key='+encodeURIComponent(key));if(response.status===404)return null;const item=await response.json();return {...item,text:async()=>item.text};},async head(key){return this.get(key);},async list({prefix}){return {objects:await (await fetch(endpoint+'/__list?prefix='+encodeURIComponent(prefix))).json(),truncated:false};},async put(key,text){const response=await fetch(endpoint+'/__set',{method:'POST',body:JSON.stringify([key,text])});if(!response.ok)throw new Error('projection failed');},async delete(){throw new Error('unversioned deletion forbidden');}};
export class PublicationCoordinator extends Base {constructor(state,env){super(state,{...env,MYCRATES:store});}}
export default {async fetch(req,env,ctx){if(new URL(req.url).pathname==='/__clock'){offset+=600000;return new Response('ok');}return worker.fetch(req,env,ctx);}};`);
  config.main = wrapper;
  Object.assign(config.vars, { STUFF_COORDINATOR_ENABLED: "true", STUFF_COORDINATOR_TOKEN: "secret", STUFF_S3_BUCKET_BINDINGS: JSON.stringify({ MYCRATES: "custom-crates" }), S3_ENDPOINT: `http://127.0.0.1:${backendPort}`, S3_REGION: "auto", S3_ACCESS_KEY_ID: "backend", S3_SECRET_ACCESS_KEY: "backend-secret" });
  writeFileSync(configPath, JSON.stringify(config));
  let child;
  t.after(async () => {
    if (child?.pid && child.exitCode === null) {
      const done = new Promise(ok => child.once("close", ok));
      process.kill(-child.pid, "SIGTERM");
      const timer = setTimeout(() => { try { process.kill(-child.pid, "SIGKILL"); } catch {} }, 5000);
      await done; clearTimeout(timer);
    }
    backend.closeAllConnections(); await new Promise(ok => backend.close(ok)); rmSync(directory, { recursive: true, force: true });
  });
  child = spawn(process.execPath, [join(workerDir, "orange/node_modules/open-orange/dist/bin.js"), "dev", "--json", "--ip", "127.0.0.1", "--port", String(port), "--config", configPath], { cwd: directory, detached: true, stdio: ["ignore", "pipe", "pipe"] });
  let logs = "";
  await new Promise((ok, fail) => { const timer = setTimeout(() => fail(new Error(logs)), 60000); child.stdout.on("data", chunk => { logs = (logs + chunk).slice(-32768); if (logs.includes('"type":"ready"')) { clearTimeout(timer); ok(); } }); child.stderr.on("data", chunk => { logs = (logs + chunk).slice(-32768); }); child.once("exit", code => { clearTimeout(timer); fail(new Error(`Orange exit ${code}: ${logs}`)); }); });
  const call = (op, body) => new Promise((ok, fail) => {
    const req = request({ host: "127.0.0.1", port, path: op === "clock" ? "/__clock" : `/_publication/cargo/${op}`, method: "POST", headers: { host: "stuff.17166969.xyz", authorization: "Bearer secret" } }, res => { const chunks = []; res.on("data", chunk => chunks.push(chunk)); res.on("end", () => ok({ status: res.statusCode, value: JSON.parse(Buffer.concat(chunks).toString() || "{}") })); });
    req.on("error", fail); req.end(JSON.stringify(body ?? {}));
  });
  const manifest = JSON.stringify({ schemaVersion: 1, objects: [] });
  put("current", "g0"); put("manifests/g0.json", manifest);
  put("blobs/orphan", "same content", "null"); put("blobs/orphan-neighbor", "retain sibling", "neighbor");
  let lease = (await call("gc-claim")).value;
  versioned = false;
  assert.equal((await call("gc-object", { token: lease.token, key: "blobs/orphan" })).status, 503);
  assert.deepEqual(deleted, []);
  versioned = true; failDelete = true;
  assert.equal((await call("gc-object", { token: lease.token, key: "blobs/orphan" })).status, 503);
  await call("abort", { token: lease.token });
  lease = (await call("begin")).value;
  const text = objects.get("blobs/orphan");
  const referenced = JSON.stringify({ schemaVersion: 1, objects: [{ key: text.key, size: text.size, etag: text.etag }] });
  put("manifests/g1.json", referenced);
  assert.equal((await call("activate", { token: lease.token, key: "retired", generation: "g1", manifest: hash(referenced), expectedRevision: 0 })).status, 409, "retired bytes cannot be activated after interrupted deletion");
  await call("abort", { token: lease.token });
  objects.delete("manifests/g1.json"); versions.delete("manifests/g1.json");
  lease = (await call("gc-claim")).value; failDelete = false;
  assert.equal((await call("gc-object", { token: lease.token, key: "blobs/orphan" })).status, 200);
  assert.deepEqual(deleted, [["blobs/orphan", "null"]]);
  assert.equal(objects.get("blobs/orphan-neighbor").text, "retain sibling");
  await call("abort", { token: lease.token });
  const fresh = put("blobs/orphan", "same content");
  put("manifests/g1.json", referenced);
  lease = (await call("begin")).value;
  assert.equal((await call("activate", { token: lease.token, key: "fresh", generation: "g1", manifest: hash(referenced), expectedRevision: 0 })).status, 200, "a fresh version of identical content can be published");
  const stale = await fetch(`http://127.0.0.1:${backendPort}/custom-crates/blobs/orphan?versionId=null`, { method: "DELETE" });
  assert.equal(stale.status, 204); assert.equal(objects.get("blobs/orphan").version, fresh.version);
  lease = (await call("gc-claim")).value;
  assert.equal((await call("gc-object", { token: lease.token, key: "blobs/orphan" })).status, 409, "retained manifest protects shared blob");
  assert.equal((await call("gc-object", { token: lease.token, key: "current" })).status, 400);
  await call("abort", { token: lease.token });
  for (let index = 0; index < 37; index++) put(`generations/large/item-${index}`, "collect me");
  put("manifests/large.json", manifest);
  lease = (await call("gc-claim")).value;
  const batch = await call("gc-delete", { token: lease.token, generation: "large" });
  assert.equal(batch.status, 200);
  assert.deepEqual(batch.value, { deleted: 32, complete: false });
  assert.ok(objects.has("manifests/large.json"), "the manifest protects shared references until generation deletion completes");
  assert.equal((await call("renew", { token: lease.token })).status, 200, "large GC leaves the actor available for lease renewal between batches");
  const finished = await call("gc-delete", { token: lease.token, generation: "large" });
  assert.equal(finished.status, 200);
  assert.deepEqual(finished.value, { deleted: 6, complete: true });
  assert.equal(objects.has("manifests/large.json"), false);
  await call("abort", { token: lease.token });
});
