import assert from "node:assert/strict";
import test from "node:test";
import { createHash, createHmac } from "node:crypto";
import { createServer } from "node:http";
import { mkdirSync, mkdtempSync, rmSync } from "node:fs";
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
