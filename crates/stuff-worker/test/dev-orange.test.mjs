import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import test from "node:test";

const root = resolve(import.meta.dirname, "../../..");
const scratch = join(root, ".work/tmp");
mkdirSync(scratch, { recursive: true });

test("normal dev serves local data, rebuilds Rust, retains the last good build and shuts down", { timeout: 240000 }, async t => {
  const fixture = mkdtempSync(join(scratch, "dev-proof-"));
  cpSync(join(root, "crates"), join(fixture, "crates"), { recursive: true, filter: path => !relative(join(root, "crates"), path).split("/").some(name => ["node_modules", "target", ".work", ".cloudflare", ".git"].includes(name)) });
  for (const name of ["Cargo.toml", "Cargo.lock", "rust-toolchain.toml"]) cpSync(join(root, name), join(fixture, name));
  cpSync(join(root, "tests/fixtures"), join(fixture, "tests/fixtures"), { recursive: true });
  const worker = join(fixture, "crates/stuff-worker");
  symlinkSync(join(root, "crates/stuff-worker/node_modules"), join(worker, "node_modules"), "dir");
  symlinkSync(join(root, "crates/stuff-worker/orange/node_modules"), join(worker, "orange/node_modules"), "dir");
  const child = spawn("pnpm", ["run", "dev"], { cwd: worker, detached: true, stdio: ["ignore", "pipe", "pipe"], env: { ...process.env, PORT: "0", HOST: "127.0.0.1", TMPDIR: scratch, CARGO_TARGET_DIR: join(fixture, "target"), RUSTC_WRAPPER: "kache", APPLICATION_EVENTS_ENDPOINT: "http://production.invalid", RIVET_ENDPOINT: "http://production.invalid", R2_S3_ENDPOINT: "https://production.invalid", R2_S3_ACCESS_KEY_ID: "must-not-leak", R2_S3_SECRET_ACCESS_KEY: "must-not-leak" } });
  let logs = "";
  child.stdout.on("data", chunk => { logs = (logs + chunk).slice(-65536); });
  child.stderr.on("data", chunk => { logs = (logs + chunk).slice(-65536); });
  const closed = new Promise(ok => child.once("close", ok));
  t.after(async () => {
    if (child.exitCode === null && child.signalCode === null) {
      process.kill(-child.pid, "SIGTERM");
      const timer = setTimeout(() => { try { process.kill(-child.pid, "SIGKILL"); } catch { } }, 10000);
      await closed;
      clearTimeout(timer);
    }
  });
  async function until(predicate) {
    const deadline = Date.now() + 180000;
    while (Date.now() < deadline) {
      if (await predicate()) return;
      if (child.exitCode !== null || child.signalCode !== null) throw new Error(`dev exited: ${logs}`);
      await delay(100);
    }
    throw new Error(`development proof timed out: ${logs}`);
  }
  await until(() => logs.includes("[stuff dev] ready "));
  const origin = /\[stuff dev\] ready (http:\/\/127\.0\.0\.1:\d+)/.exec(logs)[1];
  const page = await fetch(origin);
  assert.equal(page.status, 200);
  const html = await page.text();
  assert.match(html, /crate/);
  assert.match(html, /\/cargo/);
  const ping = await fetch(origin + "/v2/");
  assert.equal(ping.status, 200);
  assert.equal(ping.headers.get("docker-distribution-api-version"), "registry/2.0");
  const source = join(fixture, "crates/stuff-oci/src/response.rs");
  const original = readFileSync(source, "utf8");
  writeFileSync(source, original.replace('"registry/2.0"', '"registry/2.0-dev-proof"'));
  await until(async () => {
    try { return (await fetch(origin + "/v2/")).headers.get("docker-distribution-api-version") === "registry/2.0-dev-proof"; } catch { return false; }
  });
  writeFileSync(source, original + "\nthis is deliberately invalid Rust\n");
  await until(() => logs.includes("build failed; the last successful build is still serving"));
  const retained = await fetch(origin + "/v2/");
  assert.equal(retained.status, 200);
  assert.equal(retained.headers.get("docker-distribution-api-version"), "registry/2.0-dev-proof");
  writeFileSync(source, original);
  await until(async () => {
    try { return (await fetch(origin + "/v2/")).headers.get("docker-distribution-api-version") === "registry/2.0"; } catch { return false; }
  });
  process.kill(-child.pid, "SIGTERM");
  await closed;
  assert.equal(child.signalCode, "SIGTERM");
  await assert.rejects(fetch(origin, { signal: AbortSignal.timeout(2000) }));
});
