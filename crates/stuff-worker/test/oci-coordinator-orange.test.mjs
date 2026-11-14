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

test("Orange OCI HTTP publication shares coordinator authority and retains manifest references", { timeout: 120000 }, async t => {
  execFileSync("pnpm", ["run", "build"], { cwd: workerDir, stdio: "inherit" });
  mkdirSync(join(root, ".work/tmp"), { recursive: true });
  const directory = mkdtempSync(join(root, ".work/tmp/oci-coordinator-"));
  const configPath = join(directory, "orange.jsonc");
  const config = generate(configPath, "oci-coordinator-test");
  const worker = join(workerDir, ".cloudflare/output/v0/workers/default/bundle/entry.js");
  const wrapper = join(directory, "wrapper.mjs");
  writeFileSync(wrapper, `import worker, {PublicationCoordinator as Base} from ${JSON.stringify(worker)};
let loseActivation=false, failPut=false;
export class PublicationCoordinator extends Base {
 async fetch(req) {const response=await super.fetch(req);if(new URL(req.url).pathname.endsWith('/activate')&&response.ok&&loseActivation){loseActivation=false;return new Response('lost acknowledgement',{status:503});}return response;}
}
export default {async fetch(req,env,ctx){const url=new URL(req.url);if(url.pathname==='/__seed'){for(const item of await req.json())await env[item.binding].put(item.key,item.value);return new Response('ok');}if(url.pathname==='/__lose'){loseActivation=true;return new Response('ok');}if(url.pathname==='/__fail'){failPut=true;return new Response('ok');}const actual=env.OCI;const proxy=new Proxy(actual,{get(target,key){if(key==='put')return async(name,...args)=>{if(failPut&&name.startsWith('generations/')){failPut=false;throw new Error('injected publication failure');}return target.put(name,...args);};const value=target[key];return typeof value==='function'?value.bind(target):value;}});return worker.fetch(req,{...env,OCI:proxy},ctx);}};`);
  config.main = wrapper;
  Object.assign(config.vars, { STUFF_COORDINATOR_ENABLED: "true", STUFF_COORDINATOR_TOKEN: "management", STUFF_OCI_PUSH_TOKEN: "write-secret" });
  writeFileSync(configPath, JSON.stringify(config));
  const holder = createServer(); await new Promise(ok => holder.listen(0, "127.0.0.1", ok)); const port = holder.address().port; await new Promise(ok => holder.close(ok));
  let child;
  t.after(async () => {
    if (child?.pid && child.exitCode === null) {
      const done = new Promise(ok => child.once("close", ok)); process.kill(-child.pid, "SIGTERM");
      const timer = setTimeout(() => { try { process.kill(-child.pid, "SIGKILL"); } catch {} }, 5000);
      await done; clearTimeout(timer);
    }
    rmSync(directory, { recursive: true, force: true });
  });
  child = spawn(process.execPath, [join(workerDir, "orange/node_modules/open-orange/dist/bin.js"), "dev", "--json", "--ip", "127.0.0.1", "--port", String(port), "--config", configPath], { cwd: directory, detached: true, stdio: ["ignore", "pipe", "pipe"] });
  let logs = "";
  await new Promise((ok, fail) => { const timer = setTimeout(() => fail(new Error(logs)), 60000); child.stdout.on("data", chunk => { logs = (logs + chunk).slice(-32768); if (logs.includes('"type":"ready"')) { clearTimeout(timer); ok(); } }); child.stderr.on("data", chunk => { logs = (logs + chunk).slice(-32768); }); child.once("exit", code => { clearTimeout(timer); fail(new Error(`Orange exit ${code}: ${logs}`)); }); });
  const call = (method, path, body = "", host = "oci.17166969.xyz", authorization = "Basic " + Buffer.from("stuff:write-secret").toString("base64"), chunked = false) => new Promise((ok, fail) => {
    const req = request({ host: "127.0.0.1", port, path, method, headers: { host, authorization, "content-type": "application/vnd.oci.image.manifest.v1+json", ...(chunked ? {} : { "content-length": Buffer.byteLength(body) }) } }, res => { const chunks = []; res.on("data", chunk => chunks.push(chunk)); res.on("end", () => ok({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks).toString() })); }); req.on("error", fail); req.end(body);
  });
  const manage = async (op, body) => {
    const response = await call(body === undefined ? "GET" : "POST", `/_publication/oci/${op}`, body === undefined ? "" : JSON.stringify(body), "stuff.17166969.xyz", "Bearer management");
    assert.equal(response.status, 200, response.body); return JSON.parse(response.body);
  };
  const configBody = "{}"; const digest = `sha256:${hash(configBody)}`;
  await call("POST", "/__seed", JSON.stringify([{ binding: "OCI_BLOBS", key: `sha256/${hash(configBody)}`, value: configBody }]));
  const manifest = version => JSON.stringify({ schemaVersion: 2, mediaType: "application/vnd.oci.image.manifest.v1+json", config: { mediaType: "application/vnd.oci.image.config.v1+json", digest, size: 2 }, layers: [], annotations: { version } });
  const first = manifest("one"); const second = manifest("two");
  const path = "/v2/example/app/manifests/proof";
  assert.equal((await call("PUT", path, first, "oci.17166969.xyz", "")).status, 401);
  const oversized = await call("PUT", path, " ".repeat(4 * 1024 * 1024 + 1), "oci.17166969.xyz", undefined, true);
  assert.equal(oversized.status, 400);
  assert.equal(JSON.parse(oversized.body).errors[0].code, "SIZE_INVALID");
  const malformed = await call("PUT", path, Buffer.from([255]));
  assert.equal(malformed.status, 400);
  assert.equal(JSON.parse(malformed.body).errors[0].code, "MANIFEST_INVALID");
  assert.equal((await call("PUT", path, first)).status, 201, logs);
  const original = await manage("current"); assert.equal(original.revision, 1);
  assert.equal((await call("GET", path)).body, first);
  const held = await manage("begin", {});
  assert.equal((await call("PUT", path, second)).status, 409);
  assert.deepEqual(await manage("current"), original);
  await manage("abort", { token: held.token });
  await call("POST", "/__fail");
  assert.equal((await call("PUT", path, second)).status, 500);
  assert.deepEqual(await manage("current"), original);
  const afterFailure = await manage("begin", {}); await manage("abort", { token: afterFailure.token });
  await call("POST", "/__lose");
  assert.equal((await call("PUT", path, second)).status, 201, logs);
  const activated = await manage("current"); assert.equal(activated.revision, 2);
  assert.equal((await call("GET", path)).body, second);
  assert.equal((await call("GET", `/v2/example/app/manifests/sha256:${hash(first)}`)).body, first);
  assert.equal((await call("GET", `/generations/${original.generation}/repositories/example/app/repository.json`)).status, 200);
  const inventory = JSON.parse((await call("GET", `/manifests/${activated.generation}.json`)).body);
  for (const content of [first, second]) assert.ok(inventory.objects.some(object => object.key === `oci/manifests/sha256/${hash(content)}`), "every referenced immutable manifest must remain protected from GC");
  assert.equal((await call("PUT", path, second)).status, 201);
  assert.equal((await manage("current")).revision, 2, "repeating the same OCI PUT is idempotent");
});
