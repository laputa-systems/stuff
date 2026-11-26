import { createHash, randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import { appendFileSync, closeSync, existsSync, fsyncSync, mkdirSync, openSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { request } from "node:http";
import { connect } from "node:net";
import { join } from "node:path";

const usage = "usage: handoff.mjs CONFIG.json JOURNAL_DIR status|run|unwind [--until STEP]";
const REGISTRIES = ["cargo", "npm", "pypi", "oci", "mirror"];
const BUCKET = { cargo: "MYCRATES", npm: "MYNPM", pypi: "PYPI", oci: "OCI", mirror: "MIRROR" };
const STEPS = ["prepared", "frozen", "drained", "exported", "imported", "fenced", "transferred", "admitted"];
const LEASE_MS = 120_000;

const [configPath, directory, command, ...options] = process.argv.slice(2);
const until = options[0] === "--until" ? options[1] : undefined;
if (!configPath || !directory || !["status", "run", "unwind"].includes(command) || (options.length > 0 && !STEPS.includes(until))) { console.error(usage); process.exit(2); }
const config = JSON.parse(readFileSync(configPath, "utf8"));
const hostPort = value => { const [host, port] = value.split(":"); return { host, port: Number(port) }; };
const LISTEN = hostPort(config.listen);
const CONTROL = hostPort(config.control);
const LEGACY = hostPort(config.legacy);
const PUBLISH_HOST = config.publishHost;
const DRAIN_DEADLINE_MS = (config.drainDeadlineS ?? 360) * 1000;
const HOLD_BUDGET_MS = (config.holdBudgetS ?? 480) * 1000;
mkdirSync(directory, { recursive: true, mode: 0o700 });
const journalPath = join(directory, "journal.jsonl");
const lockPath = join(directory, "controller.lock");
const env = Object.fromEntries(readFileSync(config.envFile, "utf8").split("\n").filter(line => /^[A-Z][A-Z0-9_]*=/.test(line)).map(line => [line.slice(0, line.indexOf("=")), line.slice(line.indexOf("=") + 1)]));
const runArgv = argv => execFileSync(argv[0], argv.slice(1), { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });

function durable(path, text, flag = "a") {
  const fd = openSync(path, flag, 0o600);
  try { appendFileSync(fd, text); fsyncSync(fd); } finally { closeSync(fd); }
  const dir = openSync(directory, "r");
  try { fsyncSync(dir); } finally { closeSync(dir); }
}
function journal() {
  if (!existsSync(journalPath)) return [];
  const text = readFileSync(journalPath, "utf8");
  if (text && !text.endsWith("\n")) throw new Error("journal has a torn final record");
  return text.split("\n").filter(Boolean).map(line => JSON.parse(line));
}
const completed = () => journal().filter(entry => entry.kind === "step").map(entry => entry.step);
let lease = null;
function record(entry) {
  renew();
  durable(journalPath, `${JSON.stringify({ at: new Date().toISOString(), controller: lease?.token ?? null, ...entry })}\n`);
  console.log(JSON.stringify(entry));
}

function acquire() {
  const now = Date.now();
  if (existsSync(lockPath)) {
    const held = JSON.parse(readFileSync(lockPath, "utf8"));
    if (held.expires > now) throw new Error(`controller lease held by ${held.token} until ${new Date(held.expires).toISOString()}`);
    durable(journalPath, `${JSON.stringify({ at: new Date().toISOString(), kind: "takeover", from: held.token })}\n`);
    rmSync(lockPath);
  }
  lease = { token: randomUUID(), pid: process.pid, expires: now + LEASE_MS };
  durable(lockPath, JSON.stringify(lease), "wx");
}
function renew() {
  if (lease === null) return;
  const held = JSON.parse(readFileSync(lockPath, "utf8"));
  if (held.token !== lease.token) throw new Error("controller lease was taken over; stopping without mutation");
  if (held.expires <= Date.now()) throw new Error("controller lease expired; stopping without mutation");
  lease.expires = Date.now() + LEASE_MS;
  const temporary = `${lockPath}.${lease.token}`;
  durable(temporary, JSON.stringify(lease), "w");
  renameSync(temporary, lockPath);
}
function release() { if (lease !== null && JSON.parse(readFileSync(lockPath, "utf8")).token === lease.token) rmSync(lockPath); }

function http(target, path, { method = "GET", headers = {}, body } = {}) {
  return new Promise((resolve, reject) => {
    const req = request({ ...target, path, method, headers: { ...headers, ...(body === undefined ? {} : { "content-type": "application/json", "content-length": Buffer.byteLength(body) }) } }, res => {
      const chunks = [];
      res.on("data", chunk => chunks.push(chunk));
      res.on("end", () => { const text = Buffer.concat(chunks).toString("utf8"); let json; try { json = JSON.parse(text); } catch { json = undefined; } resolve({ status: res.statusCode, headers: res.headers, text, json }); });
    });
    req.setTimeout(60_000, () => req.destroy(new Error("timeout")));
    req.on("error", reject);
    req.end(body);
  });
}
const publication = (registry, op, body) => http(LISTEN, `/_publication/${registry}/${op}`, { method: body === undefined ? "GET" : "POST", body: body === undefined ? undefined : JSON.stringify(body), headers: { host: PUBLISH_HOST, "x-oo-ingress": "tailnet", authorization: `Bearer ${env.STUFF_COORDINATOR_TOKEN}` } });
const control = (path, body) => http(CONTROL, path, { method: body === undefined ? "GET" : "POST", body: body === undefined ? undefined : JSON.stringify(body), headers: { authorization: `Bearer ${env.STUFF_NATIVE_CONTROL_TOKEN}` } });
const canonical = value => ({ schemaVersion: value.schemaVersion, registry: value.registry, current: value.current, receipts: value.receipts, retired_generations: value.retired_generations, retired_versions: value.retired_versions });
const sha = text => createHash("sha256").update(text).digest("hex");
const legacyListening = () => new Promise(resolve => { const socket = connect(LEGACY); socket.setTimeout(3000); socket.once("connect", () => { socket.destroy(); resolve(true); }); socket.once("error", () => resolve(false)); socket.once("timeout", () => { socket.destroy(); resolve(false); }); });
const identity = async () => (await control("/identity")).json;

async function storeCurrent(registry) {
  const { s3Bucket } = await import(join(config.artifact, "native/bucket.mjs"));
  const bucket = s3Bucket(env, config.buckets[BUCKET[registry]]);
  const object = await bucket.get("current");
  return object === null ? null : (await object.text()).trim();
}
async function nativeDumps() {
  const dumps = {};
  for (const registry of REGISTRIES) dumps[registry] = (await control(`/coordinators/${registry}/dump`)).json;
  return dumps;
}
const exportsFile = registry => join(directory, `export-${registry}.json`);
const savedExport = registry => JSON.parse(readFileSync(exportsFile(registry), "utf8"));

class Paused extends Error { name = "Paused"; }
async function step(name, run) {
  if (completed().includes(name)) { if (name === until) throw new Paused(name); return; }
  const frozenAt = journal().find(entry => entry.kind === "begin" && entry.step === "frozen")?.at;
  if (frozenAt !== undefined && Date.now() - Date.parse(frozenAt) > HOLD_BUDGET_MS) throw new Error(`publication hold exceeded ${HOLD_BUDGET_MS / 1000} s before ${name}`);
  const index = STEPS.indexOf(name);
  if (index > 0 && !completed().includes(STEPS[index - 1])) throw new Error(`step ${name} requires ${STEPS[index - 1]}`);
  record({ kind: "begin", step: name });
  const detail = await run();
  record({ kind: "step", step: name, detail });
  if (name === until) throw new Paused(name);
}

async function run() {
  await step("prepared", async () => {
    const id = await identity();
    if (id.role !== "publisher" || id.authority?.publication !== "legacy") throw new Error(`native host is not a legacy-authority publisher: ${JSON.stringify(id.authority)}`);
    const dumps = await nativeDumps();
    for (const registry of REGISTRIES) if (dumps[registry].current !== null || dumps[registry].receipts.length > 0) throw new Error(`native ${registry} coordinator is not empty`);
    const legacy = {};
    for (const registry of REGISTRIES) {
      const current = await publication(registry, "current");
      if (current.status !== 200) throw new Error(`legacy ${registry} current answered ${current.status}: ${current.text.slice(0, 300)}`);
      legacy[registry] = current.json;
    }
    return { release: id.release, artifactSha256: id.artifactSha256, authorityGeneration: id.authority.generation, legacy };
  });
  await step("frozen", async () => {
    const result = {};
    for (const registry of REGISTRIES) {
      const frozen = await publication(registry, "freeze", {});
      if (frozen.status !== 200) throw new Error(`legacy ${registry} freeze answered ${frozen.status}`);
      result[registry] = { revision: frozen.json.current.revision, liveLease: frozen.json.liveLease };
    }
    return result;
  });
  await step("drained", async () => {
    const deadline = Date.now() + DRAIN_DEADLINE_MS;
    const pending = new Set(REGISTRIES);
    while (pending.size > 0) {
      for (const registry of [...pending]) {
        const exported = await publication(registry, "export");
        if (exported.status === 200) pending.delete(registry);
        else if (exported.status !== 409) throw new Error(`legacy ${registry} export answered ${exported.status}`);
      }
      if (pending.size === 0) break;
      if (Date.now() > deadline) throw new Error(`drain deadline passed with live leases on ${[...pending].join(",")}`);
      record({ kind: "waiting", step: "drained", leases: [...pending] });
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
    const metrics = (await http(CONTROL, "/metrics")).json;
    return { legacyInFlight: metrics.legacyInFlight };
  });
  await step("exported", async () => {
    const result = {};
    for (const registry of REGISTRIES) {
      const exported = await publication(registry, "export");
      if (exported.status !== 200) throw new Error(`legacy ${registry} export answered ${exported.status}`);
      const value = exported.json;
      if (value.current.pending !== 0) throw new Error(`legacy ${registry} still has a pending projection`);
      const projected = await storeCurrent(registry);
      if (projected !== value.current.generation) throw new Error(`legacy ${registry} generation ${value.current.generation} is not the store's current ${projected}`);
      if (existsSync(exportsFile(registry))) { if (readFileSync(exportsFile(registry), "utf8") !== exported.text) throw new Error(`legacy ${registry} export changed since it was first saved`); }
      else writeFileSync(exportsFile(registry), exported.text, { mode: 0o600, flag: "wx" });
      result[registry] = { sha256: sha(exported.text), bytes: exported.text.length, revision: value.current.revision, generation: value.current.generation, receipts: value.receipts.length, retiredGenerations: value.retired_generations.length, retiredVersions: value.retired_versions.length };
    }
    return result;
  });
  await step("imported", async () => {
    const result = {};
    for (const registry of REGISTRIES) {
      const exported = savedExport(registry);
      let dump = (await control(`/coordinators/${registry}/dump`)).json;
      if (dump.current === null) {
        const imported = await control(`/coordinators/${registry}/import`, exported);
        if (imported.status !== 200) throw new Error(`native ${registry} import answered ${imported.status}: ${imported.text}`);
        dump = (await control(`/coordinators/${registry}/dump`)).json;
      }
      if (JSON.stringify(canonical(dump)) !== JSON.stringify(canonical(exported))) throw new Error(`native ${registry} state differs from its export`);
      if (dump.frozen !== true) throw new Error(`native ${registry} is not frozen after import`);
      result[registry] = { canonicalSha256: sha(JSON.stringify(canonical(dump))) };
    }
    return result;
  });
  await step("fenced", async () => {
    for (const argv of config.fence.stop) runArgv(argv);
    if (await legacyListening()) throw new Error("legacy app still accepts connections");
    return { legacyListening: false, fence: config.fence.stop.map(argv => argv.join(" ")) };
  });
  await step("transferred", async () => {
    const before = await identity();
    if (before.authority.publication === "native") return { generation: before.authority.generation, already: true };
    const prepared = journal().find(entry => entry.kind === "step" && entry.step === "prepared").detail;
    const changed = await control("/authority", { expectedGeneration: prepared.authorityGeneration, publication: "native", reason: `handoff ${lease.token}` });
    if (changed.status !== 200) throw new Error(`authority change answered ${changed.status}: ${changed.text}`);
    const after = await identity();
    if (after.authority.publication !== "native" || after.authority.generation !== changed.json.generation) throw new Error("loaded authority does not match the recorded change");
    return { generation: after.authority.generation };
  });
  await step("admitted", async () => {
    const dumps = await nativeDumps();
    for (const registry of REGISTRIES) if (JSON.stringify(canonical(dumps[registry])) !== JSON.stringify(canonical(savedExport(registry)))) throw new Error(`native ${registry} advanced before admission`);
    for (const registry of REGISTRIES) {
      const thawed = await publication(registry, "thaw", {});
      if (thawed.status !== 200) throw new Error(`native ${registry} thaw answered ${thawed.status}`);
    }
    return { thawed: REGISTRIES };
  });
}

async function unwind() {
  const done = completed();
  if (done.includes("admitted")) throw new Error("publication was admitted on the native host; only a reverse handoff can move authority back");
  const id = await identity();
  if (id.authority.publication === "native") {
    for (const registry of REGISTRIES) {
      const frozen = await publication(registry, "freeze", {});
      if (frozen.status !== 200 || frozen.json?.liveLease) throw new Error(`native ${registry} could not be frozen without a live lease`);
    }
  }
  const dumps = await nativeDumps();
  if (done.includes("imported")) for (const registry of REGISTRIES) if (JSON.stringify(canonical(dumps[registry])) !== JSON.stringify(canonical(savedExport(registry)))) throw new Error(`native ${registry} changed after import; refusing a simple unwind`);
  if (id.authority.publication === "native") {
    const changed = await control("/authority", { expectedGeneration: id.authority.generation, publication: "legacy", legacyUpstream: `${LEGACY.host}:${LEGACY.port}`, reason: `unwind ${lease.token}` });
    if (changed.status !== 200) throw new Error(`authority unwind answered ${changed.status}`);
  }
  if (!(await legacyListening())) {
    for (const argv of config.fence.restore) runArgv(argv);
    if (!(await legacyListening())) throw new Error("legacy app did not come back");
  }
  for (const registry of REGISTRIES) {
    const thawed = await publication(registry, "thaw", {});
    if (thawed.status !== 200) throw new Error(`legacy ${registry} thaw answered ${thawed.status}`);
  }
  record({ kind: "unwound", completed: done, nativeStateRetained: done.includes("imported") });
}

if (command === "status") {
  console.log(JSON.stringify({ completed: completed(), lock: existsSync(lockPath) ? JSON.parse(readFileSync(lockPath, "utf8")) : null, identity: await identity() }, null, 2));
} else {
  acquire();
  try {
    if (journal().some(entry => entry.kind === "unwound")) throw new Error("this journal was unwound; start a new journal directory");
    await (command === "run" ? run() : unwind());
    if (command === "run") record({ kind: "complete" });
  } catch (error) {
    if (error instanceof Paused) {
      record({ kind: "paused", after: error.message });
    } else {
      try { record({ kind: "failed", error: error instanceof Error ? error.message : String(error) }); } catch { console.error("could not journal the failure"); }
      console.error(`handoff: ${error instanceof Error ? error.message : error}`);
      process.exitCode = 1;
      if (command === "run" && journal().some(entry => entry.kind === "begin" && entry.step === "frozen") && !completed().includes("admitted") && !/lease (was taken over|expired)/.test(String(error.message))) {
        try { await unwind(); } catch (unwindError) { console.error(`handoff: automatic unwind failed: ${unwindError.message}`); try { record({ kind: "unwind_failed", error: unwindError.message }); } catch { console.error("could not journal the unwind failure"); } }
      }
    }
  } finally {
    release();
  }
}
