import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, watch, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { stage } from "./stage-orange.mjs";
import { seed, seedOci } from "../test/fixtures.mjs";

const worker = dirname(dirname(fileURLToPath(import.meta.url)));
const repository = resolve(worker, "../..");
if (process.argv.length !== 2) throw new Error("configure development HOST and PORT through environment variables");
const scratch = join(repository, ".work/tmp");
mkdirSync(scratch, { recursive: true });
const root = mkdtempSync(join(scratch, "stuff-dev-"));
const runtime = join(root, "runtime");
mkdirSync(runtime);
const requestedPort = Number(process.env.PORT ?? "8787");
if (!Number.isInteger(requestedPort) || requestedPort < 0 || requestedPort > 65535) throw new Error("PORT must be an integer from 0 to 65535");
if (process.env.HOST && !["127.0.0.1", "localhost"].includes(process.env.HOST)) throw new Error("development HOST must be loopback");
const secret = randomBytes(32).toString("hex");
const environment = { ...process.env, TMPDIR: scratch };
for (const name of Object.keys(environment)) {
  if (/^(RIVET_|S3_|R2_S3_|AWS_|ORANGE_|APPLICATION_EVENTS_|STUFF_COORDINATOR_|STUFF_S3_)/.test(name) || name === "GATEWAY_SECRET") delete environment[name];
}
const puts = [];
const buckets = new Proxy({}, { get: (_, binding) => ({ put: async (key, value) => puts.push([binding, key, Buffer.from(value).toString("base64")]) }) });
const fixture = { getWorker: () => ({ getEnv: async () => buckets }) };
await seed(fixture);
await seedOci(fixture);
let stopped = false;
let builder;
let server;
let lastGood;
let building = false;
let queued = false;
let timer;
let sequence = 0;
const watchers = [];
const front = createServer();
await new Promise((ok, fail) => { front.once("error", fail); front.listen(requestedPort, "127.0.0.1", ok); });
const port = front.address().port;
await new Promise(ok => front.close(ok));
const origin = `http://127.0.0.1:${port}`;

function child(command, args, cwd) {
  const process = spawn(command, args, { cwd, env: environment, detached: true, stdio: "inherit" });
  const done = new Promise((ok, fail) => { process.once("error", fail); process.once("close", code => ok(code)); });
  return { process, done };
}
async function stopChild(target) {
  if (!target || target.process.exitCode !== null || target.process.signalCode !== null) return;
  const signal = name => { try { process.kill(-target.process.pid, name); } catch (error) { if (error.code !== "ESRCH") throw error; } };
  signal("SIGTERM");
  const kill = setTimeout(() => signal("SIGKILL"), 5000);
  const deadline = setTimeout(() => { console.error("development child did not close"); process.exit(1); }, 15000);
  try { await target.done; } finally { clearTimeout(kill); clearTimeout(deadline); }
}
async function start(application) {
  cpSync(application, runtime, { recursive: true });
  const current = child(process.execPath, [join(worker, "orange/node_modules/open-orange/dist/bin.js"), "dev", "--ip", "127.0.0.1", "--port", String(port), "--config", join(runtime, "stuff.jsonc")], runtime);
  server = current;
  const deadline = Date.now() + 60000;
  for (;;) {
    if (stopped) { await stopChild(current); throw new Error("development server stopped"); }
    if (current.process.exitCode !== null || current.process.signalCode !== null) throw new Error("Orange development process exited");
    try {
      const response = await fetch(origin + "/", { signal: AbortSignal.timeout(2000) });
      const text = await response.text();
      if (response.status === 200 && text.includes("stuff")) return;
      const seeded = await fetch(origin + "/__stuff_dev_seed", { method: "POST", headers: { "x-dev-secret": secret }, signal: AbortSignal.timeout(2000) });
      await seeded.body?.cancel();
    } catch { }
    if (Date.now() > deadline) { await stopChild(current); throw new Error("Orange development readiness timed out"); }
    await new Promise(ok => setTimeout(ok, 100));
  }
}
async function build() {
  if (stopped) return;
  if (building) { queued = true; return; }
  building = true;
  try {
    const id = ++sequence;
    const directory = join(root, `build-${id}`);
    const workerDirectory = join(directory, "workers/default");
    builder = child(process.execPath, [join(worker, "scripts/build.mjs"), workerDirectory], worker);
    const result = await builder.done;
    builder = undefined;
    if (result !== 0) { console.error("[stuff dev] build failed; the last successful build is still serving"); return; }
    if (stopped) return;
    const application = join(directory, "app");
    stage(application, `development-${id}`, { workerDirectory });
    const path = join(application, "stuff.jsonc");
    const config = JSON.parse(readFileSync(path, "utf8"));
    const original = config.main;
    config.main = "./dev-wrapper.mjs";
    config.vars.STUFF_UNIFIED_HOST = "127.0.0.1";
    config.vars.STUFF_OCI_HOST = "127.0.0.1";
    config.vars.STUFF_CARGO_BLOB_HOST = "crates-blobs.localhost";
    config.vars.STUFF_OCI_BLOB_HOST = "oci-blobs.localhost";
    config.vars.STUFF_OCI_BLOB_ORIGIN = `http://oci-blobs.localhost:${port}`;
    config.vars.STUFF_COORDINATOR_ENABLED = "false";
    config.vars.STUFF_ROUTES = JSON.stringify([["cargo", "MYCRATES"], ["npm", "MYNPM"], ["pypi", "PYPI"], ["mirror", "MIRROR"], ["", "OCI"]].map(([url_prefix, bucket_binding]) => ({ url_prefix, bucket_binding, key_prefix: "" })));
    writeFileSync(path, JSON.stringify(config));
    writeFileSync(join(application, "dev-wrapper.mjs"), `import worker from ${JSON.stringify(original)};
export {PublicationCoordinator} from ${JSON.stringify(original)};
const seed=${JSON.stringify(puts)};
export default {async fetch(req,env,ctx){
if(new URL(req.url).pathname==="/__stuff_dev_seed"){
 if(req.method!=="POST"||req.headers.get("x-dev-secret")!==${JSON.stringify(secret)})return new Response("forbidden",{status:403});
 for(const [binding,key,bytes] of seed){if(await env[binding].head(key)===null)await env[binding].put(key,Uint8Array.from(atob(bytes),char=>char.charCodeAt(0)));}
 return new Response(null,{status:204});
}return worker.fetch(req,env,ctx);}};
`);
    await stopChild(server);
    try { await start(application); lastGood = application; }
    catch (error) {
      if (stopped) return;
      console.error(`[stuff dev] new runtime failed: ${error.message}`);
      await stopChild(server);
      if (lastGood) await start(lastGood); else throw error;
    }
    console.log(`[stuff dev] ready ${origin} build=${id}`);
  } catch (error) {
    console.error(`[stuff dev] ${error.message}`);
  } finally {
    building = false;
    if (queued && !stopped) { queued = false; void build(); }
  }
}
function changed() { clearTimeout(timer); timer = setTimeout(() => void build(), 150); }
for (const name of readdirSync(join(repository, "crates"))) {
  const crate = join(repository, "crates", name);
  for (const directory of ["src", "assets"]) {
    if (existsSync(join(crate, directory))) watchers.push(watch(join(crate, directory), { recursive: true }, changed));
  }
  if (existsSync(join(crate, "Cargo.toml"))) watchers.push(watch(crate, (_event, file) => { if (file && ["Cargo.toml", "build.rs"].includes(file.toString())) changed(); }));
}
watchers.push(watch(worker, (_event, file) => { if (file && ["entry.ts", "orange.jsonc", "tsconfig.json"].includes(file.toString())) changed(); }));
watchers.push(watch(join(worker, "scripts"), changed));
watchers.push(watch(repository, (_event, file) => { if (file && ["Cargo.toml", "Cargo.lock"].includes(file.toString())) changed(); }));
for (const watcher of watchers) watcher.on("error", error => console.error(`[stuff dev] watcher failed: ${error.message}`));
async function shutdown() {
  if (stopped) return;
  stopped = true;
  clearTimeout(timer);
  for (const watcher of watchers) watcher.close();
  await Promise.allSettled([stopChild(builder), stopChild(server)]);
}
for (const signal of ["SIGINT", "SIGTERM"]) process.once(signal, () => { void shutdown(); });
await build();
