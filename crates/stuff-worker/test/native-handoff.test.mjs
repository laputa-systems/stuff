import assert from "node:assert/strict";
import test from "node:test";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createServer, request } from "node:http";
import { nativeHarness } from "./native-harness.mjs";
import { fakeS3 } from "./native-s3.mjs";
import { app, BUCKETS, controllerFixture, root, runController, stage, startLegacy, tailnet, workerDir } from "./handoff-fixture.mjs";

test("writer handoff from the legacy Orange coordinator to the native host", { timeout: 300000 }, async (t) => {
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

test("the handoff controller resumes after stopping at every durable step", { timeout: 300000 }, async (t) => {
  const { directory, s3, native, configFile, op } = await controllerFixture(t);
  const lease = await op("cargo", "begin", {});
  const g1 = stage(s3, BUCKETS.MYCRATES, "g1", { "catalog.json": '{"g":1}' });
  assert.equal((await op("cargo", "activate", { token: lease.body.token, key: "legacy-g1", generation: "g1", manifest: g1, expectedRevision: 0 })).status, 200);
  const journalDir = join(directory, "journal");
  for (const step of ["prepared", "frozen", "drained", "exported", "imported", "fenced", "transferred"]) {
    const paused = await runController(configFile, journalDir, "run", step);
    assert.equal(paused.status, 0, paused.output);
    assert.match(paused.output, new RegExp(`"after":"${step}"`));
  }
  mkdirSync(journalDir, { recursive: true });
  writeFileSync(join(journalDir, "controller.lock"), JSON.stringify({ token: "other", pid: 1, expires: Date.now() + 60000 }));
  const refused = await runController(configFile, journalDir, "run");
  assert.notEqual(refused.status, 0);
  assert.match(refused.output, /lease held by other/);
  writeFileSync(join(journalDir, "controller.lock"), JSON.stringify({ token: "stale", pid: 1, expires: Date.now() - 1000 }));
  const finished = await runController(configFile, journalDir, "run");
  assert.equal(finished.status, 0, finished.output);
  const identity = await (await native.control("/identity")).json();
  assert.equal(identity.authority.publication, "native");
  const unwind = await runController(configFile, join(directory, "journal"), "unwind");
  assert.notEqual(unwind.status, 0);
  assert.match(unwind.output, /only a reverse handoff/);
  const replay = await op("cargo", "activate", { token: "none", key: "legacy-g1", generation: "g1", manifest: g1, expectedRevision: 0 });
  assert.deepEqual(replay.body, { revision: 1, generation: "g1", manifest: g1 });
  const next = await op("cargo", "begin", {});
  assert.equal(next.status, 200);
  const g2 = stage(s3, BUCKETS.MYCRATES, "g2", { "catalog.json": '{"g":2}' });
  assert.equal((await op("cargo", "activate", { token: next.body.token, key: "native-g2", generation: "g2", manifest: g2, expectedRevision: 1 })).status, 200);
  assert.equal(s3.get(BUCKETS.MYCRATES, "current"), "g2");
});

test("a lease that outlives the drain deadline unwinds to the still-current writer", { timeout: 300000 }, async (t) => {
  const { directory, native, configFile, op } = await controllerFixture(t, { drainDeadlineS: 6 });
  const held = await op("npm", "begin", {});
  assert.equal(held.status, 200);
  const result = await runController(configFile, join(directory, "journal"), "run");
  assert.notEqual(result.status, 0);
  assert.match(result.output, /drain deadline passed with live leases on npm/);
  const journal = readFileSync(join(directory, "journal/journal.jsonl"), "utf8");
  assert.match(journal, /"kind":"unwound"/);
  const identity = await (await native.control("/identity")).json();
  assert.equal(identity.authority.publication, "legacy");
  assert.equal((await op("cargo", "begin", {})).status, 200);
  assert.equal((await op("npm", "renew", { token: held.body.token })).status, 200);
});

test("a failure during freeze thaws every legacy coordinator", { timeout: 300000 }, async (t) => {
  const { directory, native, configFile, op } = await controllerFixture(t);
  const journalDir = join(directory, "journal-partial-freeze");
  const proxy = createServer((incoming, outgoing) => {
    if (incoming.url === "/_publication/pypi/freeze") { outgoing.writeHead(503); outgoing.end(); return; }
    const forwarded = request({ host: "127.0.0.1", port: native.ports.listen.port, path: incoming.url, method: incoming.method, headers: incoming.headers }, response => { outgoing.writeHead(response.statusCode, response.headers); response.pipe(outgoing); });
    incoming.pipe(forwarded);
  });
  await new Promise(resolve => proxy.listen(0, "127.0.0.1", resolve));
  t.after(() => new Promise(resolve => proxy.close(resolve)));
  const config = JSON.parse(readFileSync(configFile, "utf8"));
  config.listen = `127.0.0.1:${proxy.address().port}`;
  writeFileSync(configFile, JSON.stringify(config));
  assert.equal((await runController(configFile, journalDir, "run", "prepared")).status, 0);
  const failed = await runController(configFile, journalDir, "run");
  assert.notEqual(failed.status, 0);
  assert.match(failed.output, /pypi freeze answered/);
  assert.match(readFileSync(join(journalDir, "journal.jsonl"), "utf8"), /"kind":"unwound"/);
  assert.equal((await op("cargo", "begin", {})).status, 200);
  assert.equal((await op("npm", "begin", {})).status, 200);
});

test("the hold budget starts with the first freeze attempt", { timeout: 300000 }, async (t) => {
  const { directory, configFile, op } = await controllerFixture(t, { holdBudgetS: 60 });
  const journalDir = join(directory, "journal-hold");
  const paused = await runController(configFile, journalDir, "run", "frozen");
  assert.equal(paused.status, 0, paused.output);
  const journalPath = join(journalDir, "journal.jsonl");
  const entries = readFileSync(journalPath, "utf8").trim().split("\n").map(line => JSON.parse(line));
  entries.find(entry => entry.kind === "begin" && entry.step === "frozen").at = new Date(Date.now() - 120000).toISOString();
  writeFileSync(journalPath, `${entries.map(entry => JSON.stringify(entry)).join("\n")}\n`);
  const result = await runController(configFile, journalDir, "run");
  assert.notEqual(result.status, 0);
  assert.match(result.output, /publication hold exceeded/);
  assert.equal((await op("cargo", "begin", {})).status, 200);
});

test("unwind refuses a native coordinator with a live lease", { timeout: 300000 }, async (t) => {
  const { directory, native, configFile, op } = await controllerFixture(t);
  const journalDir = join(directory, "journal-live-native");
  const imported = await runController(configFile, journalDir, "run", "imported");
  assert.equal(imported.status, 0, imported.output);
  const changed = await native.control("/authority", { method: "POST", body: JSON.stringify({ expectedGeneration: 1, publication: "native", reason: "test" }) });
  assert.equal(changed.status, 200);
  assert.equal((await op("cargo", "thaw", {})).status, 200);
  assert.equal((await op("cargo", "begin", {})).status, 200);
  const result = await runController(configFile, journalDir, "unwind");
  assert.notEqual(result.status, 0);
  assert.match(result.output, /live lease/);
  assert.equal((await (await native.control("/identity")).json()).authority.publication, "native");
});

test("a controller cannot replace a lock created after its existence check", { timeout: 300000 }, async (t) => {
  const { directory, configFile } = await controllerFixture(t);
  const journalDir = join(directory, "journal-lock-race");
  mkdirSync(journalDir);
  const lockPath = join(journalDir, "controller.lock");
  const held = JSON.stringify({ token: "other", pid: 1, expires: Date.now() + 60000 });
  writeFileSync(lockPath, held);
  const preload = join(directory, "lock-race.mjs");
  writeFileSync(preload, `import fs from "node:fs"; import { syncBuiltinESMExports } from "node:module"; const exists = fs.existsSync; fs.existsSync = path => String(path) === ${JSON.stringify(lockPath)} ? false : exists(path); syncBuiltinESMExports();`);
  const result = await runController(configFile, journalDir, "run", undefined, { NODE_OPTIONS: `--import=${preload}` });
  assert.notEqual(result.status, 0);
  assert.equal(readFileSync(lockPath, "utf8"), held);
});
