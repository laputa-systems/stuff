import assert from "node:assert/strict";
import test from "node:test";
import { createHash, createHmac } from "node:crypto";
import { createServer, request as httpRequest } from "node:http";
import { connect } from "node:net";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { BINDINGS, nativeHarness, send } from "./native-harness.mjs";
import { fakeS3 } from "./native-s3.mjs";
import { seed } from "./fixtures.mjs";

const scratch = fileURLToPath(new URL("../../../.work/tmp", import.meta.url));
const app = fileURLToPath(new URL("../build/native/app", import.meta.url));
const digest = (text) => createHash("sha256").update(text).digest("hex");
const md5 = (text) => createHash("md5").update(text).digest("hex");
const tailnet = { "x-oo-ingress": "tailnet", authorization: "Bearer coordinator" };
const MUTATIONS = new Set(["PUT", "POST", "DELETE"]);

function stateDirectory(t) {
  mkdirSync(scratch, { recursive: true });
  const directory = mkdtempSync(join(scratch, "native-state-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  return directory;
}

function initAuthority(directory, publication, upstream) {
  execFileSync(process.execPath, [join(app, "native/authority-init.mjs"), join(directory, "state"), publication, ...(upstream ? [upstream] : [])]);
}

function stageGeneration(s3, bucket, generation, files) {
  const objects = Object.entries(files).map(([path, text]) => {
    const key = `generations/${generation}/${path}`;
    s3.put(bucket, key, text);
    return { key, size: Buffer.byteLength(text), etag: md5(text) };
  });
  const manifest = JSON.stringify({ schemaVersion: 1, objects });
  s3.put(bucket, `manifests/${generation}.json`, manifest);
  return digest(manifest);
}

async function publication(harness, registry, op, body) {
  const response = await harness.fetch(`https://publish.test/_publication/${registry}/${op}`, body === undefined ? { headers: tailnet } : { method: "POST", headers: { ...tailnet, "content-type": "application/json" }, body: JSON.stringify(body) });
  return { status: response.status, headers: response.headers, body: await response.json() };
}

async function nativePublisher(t, directory, s3, endpoint) {
  const harness = nativeHarness({}, { role: "publisher", directory, s3, endpoint });
  t.after(() => harness.close());
  await harness.listen();
  return harness;
}

test("the reader never mutates storage and hides publication routes", async (t) => {
  const harness = nativeHarness({ STUFF_OCI_PUSH_TOKEN: "push", STUFF_OCI_WRITER_ORIGIN: "https://writer.test", STUFF_OCI_PUSH_SECRET: "secret", STUFF_PUBLISH_HOST: "publish.test" });
  t.after(() => harness.close());
  await harness.listen();
  await seed(harness);
  const before = harness.s3.log.length;
  for (const url of ["https://stuff.test/", "https://stuff.test/llms.txt", "https://crates.test/llms.txt", "https://pypi.test/simple/wheelpkg/", "https://npm.test/tarballs/abc.tgz", "https://oci.test/v2/", "https://mirror.test/"]) {
    await (await harness.fetch(url)).arrayBuffer();
  }
  for (const [url, method] of [["https://publish.test/_publication/cargo/current", "GET"], ["https://publish.test/_publication/cargo/begin", "POST"], ["https://publish.test/_s3/mycrates/current", "GET"], ["https://stuff.test/_publication/cargo/current", "GET"]]) {
    const response = await harness.fetch(url, { method, headers: tailnet, ...(method === "POST" ? { body: "{}" } : {}) });
    assert.equal(response.status, 404, `${method} ${url}`);
  }
  const push = await harness.fetch("https://oci.test/v2/example/app/blobs/uploads/", { method: "POST", headers: { authorization: "Basic cHVzaDpwdXNo" } });
  assert.notEqual(push.status, 202);
  const writes = harness.s3.log.slice(before).filter(entry => MUTATIONS.has(entry.method));
  assert.deepEqual(writes, []);
});

test("legacy publication authority proxies tailnet publication requests unchanged", async (t) => {
  const seen = [];
  const legacy = createServer(async (req, res) => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    seen.push({ method: req.method, url: req.url, host: req.headers.host, authorization: req.headers.authorization, body: Buffer.concat(chunks).toString() });
    res.writeHead(201, { "content-type": "application/json", "x-legacy": "yes" });
    res.end('{"legacy":true}');
  });
  await new Promise(resolve => legacy.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise(resolve => legacy.close(resolve)));
  const directory = stateDirectory(t);
  initAuthority(directory, "legacy", `127.0.0.1:${legacy.address().port}`);
  const harness = nativeHarness({}, { role: "publisher", directory });
  t.after(() => harness.close());
  await harness.listen();
  const result = await publication(harness, "npm", "begin", { hello: "world" });
  assert.equal(result.status, 201);
  assert.equal(result.headers.get("x-legacy"), "yes");
  assert.deepEqual(seen, [{ method: "POST", url: "/_publication/npm/begin", host: "publish.test", authorization: "Bearer coordinator", body: '{"hello":"world"}' }]);
  const publicIngress = await harness.fetch("https://publish.test/_publication/npm/current", { headers: { ...tailnet, "x-oo-ingress": "public" } });
  assert.equal(publicIngress.status, 404);
  assert.equal(seen.length, 1);
  const status = await (await harness.control("/coordinators")).json();
  assert.equal(status.authority.publication, "legacy");
  assert.equal(status.coordinators.npm.current, null);
});

test("imported state stays frozen and exact until authority is granted", async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "legacy", "127.0.0.1:9");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  const manifest = stageGeneration(s3, "mycrates", "g7", { "catalog.json": "{}" });
  s3.put("mycrates", "current", "g7");
  const exported = { schemaVersion: 1, registry: "cargo", current: { revision: 12, generation: "g7", manifest, pending: 0 }, receipts: [{ key: "k1", payload: JSON.stringify(["activate", "g7", manifest, 11]), revision: 12, generation: "g7", manifest }], retired_generations: ["g1"], retired_versions: [{ key: "generations/g1/catalog.json", version_id: "v1" }] };
  const harness = await nativePublisher(t, directory, s3, endpoint);
  const before = s3.log.length;
  const imported = await harness.control("/coordinators/cargo/import", { method: "POST", body: JSON.stringify(exported) });
  assert.equal(imported.status, 200);
  const again = await harness.control("/coordinators/cargo/import", { method: "POST", body: JSON.stringify(exported) });
  assert.equal(again.status, 409);
  const dump = await (await harness.control("/coordinators/cargo/dump")).json();
  assert.deepEqual({ schemaVersion: dump.schemaVersion, registry: dump.registry, current: dump.current, receipts: dump.receipts, retired_generations: dump.retired_generations, retired_versions: dump.retired_versions }, exported);
  assert.equal(dump.frozen, true);
  assert.deepEqual(s3.log.slice(before), []);
  const wrong = await harness.control("/authority", { method: "POST", body: JSON.stringify({ expectedGeneration: 7, publication: "native", reason: "test" }) });
  assert.equal(wrong.status, 409);
  const granted = await harness.control("/authority", { method: "POST", body: JSON.stringify({ expectedGeneration: 1, publication: "native", reason: "test" }) });
  assert.equal(granted.status, 200);
  assert.equal((await granted.json()).generation, 2);
  const begin = await publication(harness, "cargo", "begin", {});
  assert.equal(begin.status, 503);
  assert.equal(begin.headers.get("retry-after"), "30");
  const replay = await publication(harness, "cargo", "activate", { key: "k1", generation: "g7", manifest, expectedRevision: 11, token: "none" });
  assert.deepEqual(replay, { status: 200, headers: replay.headers, body: { revision: 12, generation: "g7", manifest } });
  const identity = await (await harness.control("/identity")).json();
  assert.equal(identity.authority.generation, 2);
  assert.equal(identity.authority.publication, "native");
});

test("a native activation is durable across SIGKILL and replays its receipt", async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  const g1 = stageGeneration(s3, "mynpm", "g1", { "catalog.json": '{"a":1}' });
  s3.put("mynpm", "current", "g1");
  let harness = await nativePublisher(t, directory, s3, endpoint);
  const current = await publication(harness, "npm", "current");
  assert.deepEqual(current.body, { revision: 0, generation: "g1", manifest: g1, pending: 0 });
  const [first, second] = await Promise.all([publication(harness, "npm", "begin", {}), publication(harness, "npm", "begin", {})]);
  assert.deepEqual([first.status, second.status].sort(), [200, 409]);
  const lease = first.status === 200 ? first.body : second.body;
  const g2 = stageGeneration(s3, "mynpm", "g2", { "catalog.json": '{"a":2}', "index.html": "<p>2</p>" });
  const activation = { token: lease.token, key: "publish-g2", generation: "g2", manifest: g2, expectedRevision: 0 };
  const activated = await publication(harness, "npm", "activate", activation);
  assert.deepEqual(activated.body, { revision: 1, generation: "g2", manifest: g2 });
  assert.equal(s3.get("mynpm", "current"), "g2");
  await harness.stop("SIGKILL");
  harness = await nativePublisher(t, directory, s3, endpoint);
  const after = await publication(harness, "npm", "current");
  assert.deepEqual(after.body, { revision: 1, generation: "g2", manifest: g2, pending: 0 });
  const replay = await publication(harness, "npm", "activate", activation);
  assert.deepEqual(replay.body, activated.body);
  const conflict = await publication(harness, "npm", "activate", { ...activation, expectedRevision: 5 });
  assert.equal(conflict.status, 409);
  const reader = await harness.fetch("https://npm.test/index.html");
  assert.equal(await reader.text(), "<p>2</p>");
});

test("legacy authority requires every native coordinator to be frozen", async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const harness = nativeHarness({}, { role: "publisher", directory });
  t.after(() => harness.close());
  await harness.listen();
  const response = await harness.control("/authority", { method: "POST", body: JSON.stringify({ expectedGeneration: 1, publication: "legacy", legacyUpstream: "127.0.0.1:9", reason: "test" }) });
  assert.equal(response.status, 409);
  assert.equal((await (await harness.control("/identity")).json()).authority.publication, "native");
});

test("authority flip cannot overtake an admitted native request", { timeout: 15000 }, async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const legacy = createServer((req, res) => { res.writeHead(201, { "content-type": "application/json" }); res.end('{"legacy":true}'); });
  await new Promise(resolve => legacy.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise(resolve => legacy.close(resolve)));
  const block = join(directory, "block");
  const entered = join(directory, "entered");
  const release = join(directory, "release");
  const preload = join(directory, "delay-auth.mjs");
  writeFileSync(preload, `import fs from "node:fs"; const digest = crypto.subtle.digest.bind(crypto.subtle); crypto.subtle.digest = async (algorithm, data) => { if (fs.existsSync(${JSON.stringify(block)}) && new TextDecoder().decode(data) === "Bearer coordinator") { fs.writeFileSync(${JSON.stringify(entered)}, ""); while (!fs.existsSync(${JSON.stringify(release)})) await new Promise(resolve => setTimeout(resolve, 10)); } return digest(algorithm, data); };`);
  const harness = nativeHarness({}, { role: "publisher", directory, env: { NODE_OPTIONS: `--import=${preload}` } });
  t.after(() => harness.close());
  await harness.listen();
  for (const registry of ["cargo", "npm", "pypi", "oci", "mirror"]) assert.equal((await publication(harness, registry, "freeze", {})).status, 200);
  writeFileSync(block, "");
  const admitted = publication(harness, "cargo", "current");
  try {
    const deadline = Date.now() + 5000;
    while (!existsSync(entered) && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 10));
    assert.equal(existsSync(entered), true);
    const change = () => harness.control("/authority", { method: "POST", body: JSON.stringify({ expectedGeneration: 1, publication: "legacy", legacyUpstream: `127.0.0.1:${legacy.address().port}`, reason: "test" }) });
    assert.equal((await change()).status, 409);
    writeFileSync(release, "");
    assert.equal((await admitted).status, 200);
    assert.equal((await change()).status, 200);
    assert.equal((await publication(harness, "cargo", "current")).status, 201);
  } finally { writeFileSync(release, ""); await admitted.catch(() => undefined); }
});

test("failed authority initialization leaves no authority record", (t) => {
  const directory = stateDirectory(t);
  const modulePath = new URL("../native/authority.mjs", import.meta.url).href;
  const code = `import fs from "node:fs"; import { syncBuiltinESMExports } from "node:module"; fs.writeFileSync = () => { throw new Error("injected write failure"); }; syncBuiltinESMExports(); const { AuthorityRecord } = await import(${JSON.stringify(modulePath)}); try { AuthorityRecord.initialize(${JSON.stringify(directory)}, { publication: "native", reason: "test" }); } catch {}`;
  execFileSync(process.execPath, ["--input-type=module", "-e", code]);
  assert.equal(existsSync(join(directory, "authority.json")), false);
});

test("a waiting coordinator request expires before the active operation finishes", { timeout: 40000 }, async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  s3.faults.push({ method: "GET", bucket: "mynpm", key: "current", delayMs: 24000 });
  const harness = await nativePublisher(t, directory, s3, endpoint);
  const active = publication(harness, "npm", "current");
  while (!s3.log.some(item => item.bucket === "mynpm" && item.key === "current")) await new Promise(resolve => setTimeout(resolve, 10));
  let finished = false;
  void active.finally(() => { finished = true; });
  const waiting = await publication(harness, "npm", "current");
  assert.equal(waiting.status, 503);
  assert.equal(waiting.headers.get("retry-after"), "5");
  assert.equal(finished, false);
  await active;
});

test("a failed projection is committed as pending, repaired, and replayed after a lost response", async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  stageGeneration(s3, "pypi", "g1", { "catalog.json": "{}" });
  s3.put("pypi", "current", "g1");
  const harness = await nativePublisher(t, directory, s3, endpoint);
  const lease = (await publication(harness, "pypi", "begin", {})).body;
  const g2 = stageGeneration(s3, "pypi", "g2", { "catalog.json": '{"b":1}' });
  s3.faults.push({ method: "PUT", bucket: "pypi", key: "current", status: 500 });
  const activation = { token: lease.token, key: "publish-pypi-g2", generation: "g2", manifest: g2, expectedRevision: 0 };
  const failed = await publication(harness, "pypi", "activate", activation);
  assert.equal(failed.status, 503);
  assert.equal(s3.get("pypi", "current"), "g1");
  const pending = await (await harness.control("/coordinators/pypi/dump")).json();
  assert.deepEqual(pending.current, { revision: 1, generation: "g2", manifest: g2, pending: 1 });
  assert.equal(pending.receipts.length, 1);
  const replay = await publication(harness, "pypi", "activate", activation);
  assert.deepEqual(replay.body, { revision: 1, generation: "g2", manifest: g2 });
  assert.equal(s3.get("pypi", "current"), "g2");
  const repaired = await (await harness.control("/coordinators/pypi/dump")).json();
  assert.equal(repaired.current.pending, 0);
});

test("a second publisher cannot open a held state directory", async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  await nativePublisher(t, directory, s3, endpoint);
  const second = nativeHarness({}, { role: "publisher", directory, s3, endpoint });
  await assert.rejects(second.listen(), /held by another process/);
});

test("SIGTERM drains an in-flight download to its last byte before exiting", async (t) => {
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  const harness = nativeHarness({}, { s3, endpoint });
  t.after(() => harness.close());
  await harness.listen();
  await seed(harness);
  const payload = "x".repeat(32 * 1024 * 1024);
  s3.put("mynpm", "tarballs/big.tgz", payload);
  const received = await new Promise((resolve, reject) => {
    const req = (async () => {
      const { request } = await import("node:http");
      const call = request({ host: "127.0.0.1", port: harness.ports.listen.port, path: "/tarballs/big.tgz", headers: { host: "npm.test" } }, res => {
        let bytes = 0;
        const hash = createHash("sha256");
        res.pause();
        setTimeout(() => {
          harness.stop("SIGTERM");
          setTimeout(() => res.resume(), 500);
        }, 200);
        res.on("data", chunk => { bytes += chunk.length; hash.update(chunk); });
        res.on("end", () => resolve({ status: res.statusCode, bytes, sha: hash.digest("hex"), complete: res.complete }));
        res.on("error", reject);
      });
      call.on("error", reject);
      call.end();
    })();
    req.catch(reject);
  });
  assert.deepEqual(received, { status: 200, bytes: payload.length, sha: digest(payload), complete: true });
  assert.equal(await harness.exited(), 0);
  await assert.rejects(send(harness.ports.listen.port, "https://npm.test/tarballs/abc.tgz"));
});

test("a disconnected streaming client is reported as cancelled", async (t) => {
  const harness = nativeHarness();
  t.after(() => harness.close());
  await harness.listen();
  await seed(harness);
  harness.s3.put("mynpm", "tarballs/cancel.tgz", "x".repeat(16 * 1024 * 1024));
  await new Promise((resolve, reject) => {
    const socket = connect(harness.ports.listen.port, "127.0.0.1", () => socket.write("GET /tarballs/cancel.tgz HTTP/1.1\r\nHost: npm.test\r\n\r\n"));
    socket.once("data", () => { socket.destroy(); resolve(); });
    socket.on("error", reject);
  });
  const deadline = Date.now() + 3000;
  while (!harness.output.includes('"event":"request_cancelled"') && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 20));
  assert.match(harness.output, /"event":"request_cancelled"/);
  assert.doesNotMatch(harness.output, /"event":"request_failed"/);
});

const quote = (s) => encodeURIComponent(s).replace(/[!'()*]/g, c => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);
const hmac = (key, value) => createHmac("sha256", key).update(value).digest();
function signedHeaders(method, path, body, token, overrides = {}) {
  const date = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const headers = Object.fromEntries(Object.entries({ host: "publish.test", "x-amz-date": date, "x-amz-content-sha256": digest(body), ...(token ? { "x-amz-security-token": token } : {}), "content-length": String(Buffer.byteLength(body)), ...overrides }).filter(([, value]) => value !== undefined));
  const names = Object.keys(headers).sort();
  const url = new URL(path, "http://publish.test");
  const query = [...url.searchParams].map(([k, v]) => [quote(k), quote(v)]).sort(([ak, av], [bk, bv]) => ak.localeCompare(bk) || av.localeCompare(bv)).map(pair => pair.join("=")).join("&");
  const canonical = [method, url.pathname, query, names.map(key => `${key}:${String(headers[key]).trim().replace(/\s+/g, " ")}\n`).join(""), names.join(";"), headers["x-amz-content-sha256"]].join("\n");
  const scope = `${date.slice(0, 8)}/auto/s3/aws4_request`;
  const key = hmac(hmac(hmac(hmac("AWS4service-secret", date.slice(0, 8)), "auto"), "s3"), "aws4_request");
  const signature = createHmac("sha256", key).update(["AWS4-HMAC-SHA256", date, scope, digest(canonical)].join("\n")).digest("hex");
  return { ...headers, "x-oo-ingress": "tailnet", authorization: `AWS4-HMAC-SHA256 Credential=service/${date.slice(0, 8)}/auto/s3/aws4_request, SignedHeaders=${names.join(";")}, Signature=${signature}` };
}

test("publisher shutdown cuts blob streams without abandoning a coordinator", { timeout: 10000 }, async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  s3.put("mycrates", "blob", "x".repeat(16 * 1024 * 1024));
  const harness = nativeHarness({}, { role: "publisher", directory, s3, endpoint, drainS: 0.1 });
  t.after(() => harness.close());
  await harness.listen();
  const path = "/_s3/mycrates/blob";
  const response = await new Promise((resolve, reject) => {
    const req = httpRequest({ host: "127.0.0.1", port: harness.ports.listen.port, path, headers: signedHeaders("GET", path, "") }, resolve);
    req.on("error", reject);
    req.end();
  });
  assert.equal(response.statusCode, 200);
  response.pause();
  const closed = new Promise(resolve => response.once("close", resolve));
  s3.faults.push({ method: "GET", bucket: "mynpm", key: "current", delayMs: 800 });
  const operation = publication(harness, "npm", "current");
  while (!s3.log.some(item => item.bucket === "mynpm" && item.key === "current")) await new Promise(resolve => setTimeout(resolve, 10));
  const stopped = harness.stop("SIGTERM");
  setTimeout(() => response.resume(), 400);
  await closed;
  assert.equal((await operation).status, 200);
  assert.equal(await stopped, 0);
});

test("the native gateway streams verified uploads and fences mutations to the lease", async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  stageGeneration(s3, "mycrates", "g1", { "catalog.json": "{}" });
  s3.put("mycrates", "current", "g1");
  const harness = await nativePublisher(t, directory, s3, endpoint);
  const upload = (method, path, body, token, overrides) => harness.fetch(`https://publish.test${path}`, { method, headers: signedHeaders(method, path, body, token, overrides), body });
  const unleased = await upload("PUT", "/_s3/mycrates/generations/g2/catalog.json", "{}", "missing-token");
  assert.equal(unleased.status, 403);
  const lease = (await publication(harness, "cargo", "begin", {})).body;
  const body = "y".repeat(300_000);
  const stored = await upload("PUT", "/_s3/mycrates/generations/g2/big.bin", body, lease.token);
  assert.equal(stored.status, 200);
  assert.equal(s3.get("mycrates", "generations/g2/big.bin"), body);
  const tampered = await upload("PUT", "/_s3/mycrates/generations/g2/bad.bin", "actual", lease.token, { "x-amz-content-sha256": digest("claimed") });
  assert.notEqual(tampered.status, 200);
  assert.equal(s3.get("mycrates", "generations/g2/bad.bin"), null);
  const pointer = await upload("PUT", "/_s3/mycrates/current", "g2", lease.token);
  assert.equal(pointer.status, 403);
  assert.equal(s3.get("mycrates", "current"), "g1");
  const overwrite = await upload("PUT", "/_s3/mycrates/generations/g2/big.bin", "replaced", lease.token);
  assert.equal(overwrite.status, 412);
  assert.equal(s3.get("mycrates", "generations/g2/big.bin"), body);
  const read = await harness.fetch("https://publish.test/_s3/mycrates/current", { headers: signedHeaders("GET", "/_s3/mycrates/current", "", undefined, { "content-length": undefined }) });
  assert.equal(read.status, 200);
  assert.equal(await read.text(), "g1");
});

test("an object body survives garbage collection of the store response until it is consumed", async (t) => {
  assert.equal(typeof globalThis.gc, "function", "run with --expose-gc");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  const body = "q".repeat(256 * 1024);
  s3.put("mynpm", "tarballs/gc.tgz", body);
  const { s3Bucket } = await import(join(app, "native/bucket.mjs"));
  const bucket = s3Bucket({ S3_ENDPOINT: endpoint, S3_REGION: "us-east-1", S3_ACCESS_KEY_ID: "test", S3_SECRET_ACCESS_KEY: "test" }, "mynpm");
  const objects = [];
  for (let index = 0; index < 8; index += 1) objects.push(await bucket.get("tarballs/gc.tgz"));
  for (let round = 0; round < 6; round += 1) {
    globalThis.gc();
    await new Promise(resolve => setImmediate(resolve));
  }
  for (const object of objects) assert.equal(await new Response(object.body).text(), body);
});

test("a ranged bucket read rejects a store that ignores Range", async (t) => {
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  s3.faults.push({ method: "GET", bucket: "mynpm", key: "object", status: 200 });
  const { s3Bucket } = await import(join(app, "native/bucket.mjs"));
  const bucket = s3Bucket({ S3_ENDPOINT: endpoint, S3_REGION: "us-east-1", S3_ACCESS_KEY_ID: "test", S3_SECRET_ACCESS_KEY: "test" }, "mynpm");
  await assert.rejects(bucket.get("object", { range: { offset: 0, length: 1 } }), /store GET answered 200/);
});

test("coordinator bucket reads bound the response body", async (t) => {
  const store = createServer((req, res) => {
    res.writeHead(200, { "content-length": "2" });
    res.flushHeaders();
    setTimeout(() => res.end("ok"), 300);
  });
  await new Promise(resolve => store.listen(0, "127.0.0.1", resolve));
  t.after(() => { store.closeAllConnections(); return new Promise(resolve => store.close(resolve)); });
  const { s3Bucket } = await import(join(app, "native/bucket.mjs"));
  const bucket = s3Bucket({ S3_ENDPOINT: `http://127.0.0.1:${store.address().port}`, S3_REGION: "us-east-1", S3_ACCESS_KEY_ID: "test", S3_SECRET_ACCESS_KEY: "test" }, "mynpm", undefined, { readDeadlineMs: 100 });
  const object = await bucket.get("current");
  await assert.rejects(object.text());
});

test("metrics snapshots do not reset the minute event-loop sample", async () => {
  const { createCounters } = await import(join(app, "native/counters.mjs"));
  const counters = createCounters();
  try {
    await new Promise(resolve => setTimeout(resolve, 30));
    const until = performance.now() + 80;
    while (performance.now() < until) {}
    counters.snapshot();
    await new Promise(resolve => setTimeout(resolve, 30));
    const sample = counters.snapshot({ sample: true });
    assert.ok(sample.eventLoop.utilizationSinceLastSnapshot > 0.25);
    assert.ok(sample.eventLoop.delayMaxMs > 50);
    await new Promise(resolve => setTimeout(resolve, 30));
    assert.ok(counters.snapshot({ sample: true }).eventLoop.delayMaxMs < 50);
  } finally { counters.close(); }
});

test("parity without a limit attempts its first request", () => {
  const script = fileURLToPath(new URL("../../../deploy/native/parity.mjs", import.meta.url));
  assert.throws(() => execFileSync(process.execPath, [script, "127.0.0.1:1", "127.0.0.1:1"], { stdio: "pipe" }), /Command failed/);
});

test("native suite runner executes all suites after a failure", { timeout: 120000 }, (t) => {
  const directory = stateDirectory(t);
  const preload = join(directory, "suite-preload.mjs");
  const log = join(directory, "suites.txt");
  writeFileSync(preload, `import child from "node:child_process"; import fs from "node:fs"; import { syncBuiltinESMExports } from "node:module"; const run = child.execFileSync; child.execFileSync = (command, args, options) => { const name = args?.find(value => /^test\\/(native|native-handoff|runtime)\\.test\\.mjs$/.test(value)); if (!name) return run(command, args, options); fs.appendFileSync(${JSON.stringify(log)}, name + "\\n"); if (name === "test/native.test.mjs") throw new Error("injected failure"); return Buffer.alloc(0); }; syncBuiltinESMExports();`);
  const root = fileURLToPath(new URL("..", import.meta.url));
  assert.throws(() => execFileSync(process.execPath, ["scripts/build-native.mjs", "--test"], { cwd: root, env: { ...process.env, NODE_OPTIONS: `--import=${preload}` }, stdio: "pipe" }));
  assert.deepEqual(readFileSync(log, "utf8").trim().split("\n"), ["test/native.test.mjs", "test/native-handoff.test.mjs", "test/runtime.test.mjs"]);
});

test("native suite runner names the missing handoff prerequisite", { timeout: 120000 }, (t) => {
  const directory = stateDirectory(t);
  const preload = join(directory, "missing-orange.mjs");
  writeFileSync(preload, `import child from "node:child_process"; import fs from "node:fs"; import { syncBuiltinESMExports } from "node:module"; const exists = fs.existsSync; const run = child.execFileSync; fs.existsSync = path => String(path).endsWith("orange/node_modules/open-orange/dist/bin.js") ? false : exists(path); child.execFileSync = (command, args, options) => args?.includes("--test") ? Buffer.alloc(0) : run(command, args, options); syncBuiltinESMExports();`);
  const root = fileURLToPath(new URL("..", import.meta.url));
  let error;
  try { execFileSync(process.execPath, ["scripts/build-native.mjs", "--test"], { cwd: root, env: { ...process.env, NODE_OPTIONS: `--import=${preload}` }, stdio: "pipe" }); }
  catch (caught) { error = caught; }
  assert.match(error?.stderr?.toString() ?? "", /pnpm --dir orange install --frozen-lockfile/);
});

test("a chunked GET body cannot become another upstream request", async (t) => {
  const seen = [];
  const upstream = createServer(async (req, res) => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    seen.push({ path: req.url, body: Buffer.concat(chunks).toString() });
    res.end("ok");
  });
  await new Promise(resolve => upstream.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise(resolve => upstream.close(resolve)));
  const { proxyTo } = await import(join(app, "native/host.mjs"));
  const forward = proxyTo(`127.0.0.1:${upstream.address().port}`);
  const proxy = createServer((req, res) => { void forward(req, res).catch(() => res.destroy()); });
  await new Promise(resolve => proxy.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise(resolve => proxy.close(resolve)));
  const payload = "GET /smuggled HTTP/1.1\r\nHost: internal\r\n\r\n";
  await new Promise((resolve, reject) => {
    const socket = connect(proxy.address().port, "127.0.0.1", () => socket.write(`GET /first HTTP/1.1\r\nHost: external\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n${Buffer.byteLength(payload).toString(16)}\r\n${payload}\r\n0\r\n\r\n`));
    socket.on("data", () => {});
    socket.on("end", resolve);
    socket.on("error", reject);
  });
  assert.deepEqual(seen, [{ path: "/first", body: payload }]);
});

test("a reader forwards tailnet publication to the publisher and holds it while the publisher is away", async (t) => {
  const seen = [];
  const publisher = createServer(async (req, res) => {
    for await (const chunk of req) void chunk;
    seen.push({ method: req.method, url: req.url, ingress: req.headers["x-oo-ingress"] });
    res.writeHead(200, { "content-type": "application/json" });
    res.end('{"from":"publisher"}');
  });
  await new Promise(resolve => publisher.listen(0, "127.0.0.1", resolve));
  const port = publisher.address().port;
  const harness = nativeHarness({ STUFF_PUBLISH_HOST: "publish.test" }, { env: { STUFF_NATIVE_PUBLICATION_UPSTREAM: `127.0.0.1:${port}`, STUFF_PUBLISH_HOST: "publish.test" } });
  t.after(() => harness.close());
  await harness.listen();
  const forwarded = await publication(harness, "oci", "renew", { token: "x" });
  assert.deepEqual([forwarded.status, forwarded.body], [200, { from: "publisher" }]);
  assert.deepEqual(seen, [{ method: "POST", url: "/_publication/oci/renew", ingress: "tailnet" }]);
  const hidden = await harness.fetch("https://publish.test/_publication/oci/current", { headers: { ...tailnet, "x-oo-ingress": "public" } });
  assert.equal(hidden.status, 404);
  await new Promise(resolve => publisher.close(resolve));
  const held = await publication(harness, "oci", "begin", {});
  assert.equal(held.status, 503);
  assert.equal(held.headers.get("retry-after"), "5");
  const reads = await harness.fetch("https://stuff.test/missing");
  assert.equal(reads.status, 404);
  assert.equal(seen.length, 1);
});

test("health reports bounded cached reader and publisher checks", async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  for (const name of ["mycrates", "mynpm", "pypi", "oci", "mirror"]) s3.put(name, "current", "g0");
  const publisher = await nativePublisher(t, directory, s3, endpoint);
  const reader = nativeHarness({ STUFF_PUBLISH_HOST: "publish.test" }, { s3, endpoint, env: { STUFF_NATIVE_PUBLICATION_UPSTREAM: `127.0.0.1:${publisher.ports.listen.port}`, S3_ACCESS_KEY_ID: "health-access-key", S3_SECRET_ACCESS_KEY: "health-secret-key", APPLICATION_EVENTS_TOKEN: "health-telemetry-token" } });
  t.after(() => reader.close());
  await reader.listen();
  const before = s3.log.length;
  const responses = await Promise.all(Array.from({ length: 6 }, () => reader.fetch("https://stuff.17166969.xyz/healthz")));
  assert.ok(responses.every(response => response.status === 200));
  assert.equal(responses[0].headers.get("cache-control"), "no-store");
  const body = await responses[0].text();
  assert.ok(Buffer.byteLength(body) <= 4096);
  for (const secret of [endpoint, "127.0.0.1", "health-access-key", "health-secret-key", "health-telemetry-token", "service-secret", "coordinator", "Bearer ", "S3_SECRET_ACCESS_KEY"]) assert.equal(body.includes(secret), false, secret);
  const health = JSON.parse(body);
  assert.equal(health.status, "ok", body);
  assert.equal(health.role, "reader");
  assert.equal(health.checks.publisher.status, "ok");
  for (const result of Object.values(health.checks)) assert.ok(Number.isInteger(result.ms) && result.ms >= 0 && result.ms <= 500);
  assert.equal(s3.log.slice(before).filter(item => item.key === "current").length, 10);
  await reader.fetch("https://stuff.17166969.xyz/healthz");
  assert.equal(s3.log.slice(before).filter(item => item.key === "current").length, 10);
  const forwarded = await reader.fetch("https://publish.test/healthz", { headers: { "x-oo-ingress": "tailnet" } });
  const publisherBody = await forwarded.text();
  assert.ok(Buffer.byteLength(publisherBody) <= 4096);
  for (const secret of [endpoint, "127.0.0.1", "health-access-key", "health-secret-key", "health-telemetry-token", "service-secret", "Bearer "]) assert.equal(publisherBody.includes(secret), false, secret);
  assert.equal(JSON.parse(publisherBody).role, "publisher");
  assert.equal((await reader.fetch("https://publish.test/healthz", { headers: { "x-oo-ingress": "public" } })).status, 404);
  await reader.control("/withdraw", { method: "POST" });
  const down = await reader.fetch("https://stuff.17166969.xyz/healthz");
  assert.equal(down.status, 503);
  assert.equal((await down.json()).checks.draining.status, "down");
});

test("health degrades for partial store loss and publisher loss, and goes down for total store loss", async (t) => {
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  s3.put("mynpm", "current", "g0");
  const reader = nativeHarness({ STUFF_PUBLISH_HOST: "publish.test" }, { s3, endpoint, env: { STUFF_NATIVE_PUBLICATION_UPSTREAM: "127.0.0.1:1" } });
  t.after(() => reader.close());
  await reader.listen();
  const response = await reader.fetch("https://stuff.17166969.xyz/healthz");
  assert.equal(response.status, 200);
  const partial = await response.json();
  assert.equal(partial.status, "degraded");
  assert.equal(partial.checks.store.status, "degraded");
  assert.equal(partial.checks.publisher.status, "degraded");
  const forwarded = await reader.fetch("https://publish.test/healthz", { headers: { "x-oo-ingress": "tailnet" } });
  assert.equal(forwarded.status, 503);
  assert.equal((await forwarded.json()).status, "down");
  s3.faults.push({ method: "GET", bucket: "mynpm", key: "current", status: 500 });
  await new Promise(resolve => setTimeout(resolve, 1050));
  const down = await reader.fetch("https://stuff.17166969.xyz/healthz");
  assert.equal(down.status, 503);
  assert.equal((await down.json()).checks.store.status, "down");
  assert.doesNotMatch(reader.output, /"event":"request_failed"/);
});

test("health times out stalled store reads within one second", async (t) => {
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  for (const bucket of ["mycrates", "mynpm", "pypi", "oci", "mirror"]) s3.faults.push({ method: "GET", bucket, key: "current", delayMs: 1500 });
  const reader = nativeHarness({}, { s3, endpoint });
  t.after(() => reader.close());
  await reader.listen();
  const started = performance.now();
  const response = await reader.fetch("https://stuff.17166969.xyz/healthz");
  assert.equal(response.status, 503);
  assert.ok(performance.now() - started < 1000);
  const health = await response.json();
  assert.equal(health.checks.store.status, "down");
  for (const result of Object.values(health.checks)) assert.ok(Number.isInteger(result.ms) && result.ms >= 0 && result.ms <= 500);
});

test("publisher health degrades when a coordinator queue is over half full", { timeout: 15000 }, async (t) => {
  const directory = stateDirectory(t);
  initAuthority(directory, "native");
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  for (const name of ["mycrates", "mynpm", "pypi", "oci", "mirror"]) s3.put(name, "current", "g0");
  s3.faults.push({ method: "GET", bucket: "mynpm", key: "current", delayMs: 2500 });
  const publisher = await nativePublisher(t, directory, s3, endpoint);
  const active = publication(publisher, "npm", "current");
  while (!s3.log.some(item => item.bucket === "mynpm" && item.key === "current")) await new Promise(resolve => setTimeout(resolve, 10));
  const waiting = Array.from({ length: 129 }, () => publication(publisher, "npm", "current"));
  let state;
  do {
    state = await (await publisher.control("/coordinators")).json();
    if (state.coordinators.npm.waiting <= 128) await new Promise(resolve => setTimeout(resolve, 10));
  } while (state.coordinators.npm.waiting <= 128);
  const response = await publisher.fetch("https://publish.test/healthz", { headers: { "x-oo-ingress": "tailnet" } });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).checks.coordinators.status, "degraded");
  await Promise.all([active, ...waiting]);
});

test("a withdrawn reader fails its ingress readiness check while it keeps serving", async (t) => {
  const harness = nativeHarness();
  t.after(() => harness.close());
  await harness.listen();
  await seed(harness);
  const ready = () => send(harness.ports.listen.port, "http://127.0.0.1:18493/.well-known/stuff-native/ready").then(r => r.status);
  assert.equal(await ready(), 200);
  assert.equal((await harness.fetch("https://crates.test/.well-known/stuff-native/ready")).status, 404);
  assert.equal((await send(harness.ports.control.port, "http://control/withdraw", { method: "POST" })).status, 200);
  assert.equal(await ready(), 503);
  assert.equal((await harness.fetch("https://crates.test/llms.txt")).status, 200);
  assert.equal((await send(harness.ports.control.port, "http://control/restore", { method: "POST" })).status, 200);
  assert.equal(await ready(), 200);
});

test("withdrawal survives a reader crash until restore", async (t) => {
  const directory = stateDirectory(t);
  const s3 = fakeS3();
  const endpoint = await s3.listen();
  t.after(() => s3.close());
  const options = { directory, s3, endpoint, env: { STUFF_NATIVE_RUNTIME_DIR: directory, STUFF_NATIVE_NAME: "reader-a" } };
  const first = nativeHarness({}, options);
  t.after(() => first.close());
  await first.listen();
  assert.equal((await first.control("/withdraw", { method: "POST" })).status, 200);
  await first.stop("SIGKILL");
  const second = nativeHarness({}, options);
  t.after(() => second.close());
  await second.listen();
  assert.equal((await second.control("/ready")).status, 503);
  assert.equal((await second.control("/restore", { method: "POST" })).status, 200);
  assert.equal((await second.control("/ready")).status, 200);
});

test("a failed reader restart restores the withdrawn reader", (t) => {
  const directory = stateDirectory(t);
  const restored = join(directory, "restored");
  const wget = join(directory, "wget");
  writeFileSync(wget, `#!/bin/sh\ncase "$*" in *"/restore"*) : > ${JSON.stringify(restored)} ;; *"/metrics"*) printf '%s\\n' '{"activeRequests":0,}' ;; esac\nexit 0\n`);
  writeFileSync(join(directory, "rc-service"), "#!/bin/sh\nexit 1\n");
  writeFileSync(join(directory, "sleep"), "#!/bin/sh\nexit 0\n");
  for (const name of ["wget", "rc-service", "sleep"]) chmodSync(join(directory, name), 0o755);
  const script = fileURLToPath(new URL("../../../deploy/native/rollout-reader.sh", import.meta.url));
  assert.throws(() => execFileSync("/bin/sh", [script, "a"], { env: { ...process.env, PATH: `${directory}:/usr/bin:/bin` }, stdio: "pipe" }));
  assert.equal(existsSync(restored), true);
});
