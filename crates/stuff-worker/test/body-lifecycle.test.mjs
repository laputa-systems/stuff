import assert from "node:assert/strict";
import test from "node:test";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { createTestHarness } from "wrangler";

const workerDir = resolve(import.meta.dirname, "..");
const built = join(workerDir, "build/orange/workers/default");
const scratch = resolve(workerDir, "../../.work/tmp");

test("registry reads release every body not handed to the response", async t => {
  process.env.CLOUDFLARE_CF_FETCH_ENABLED = "false";
  mkdirSync(scratch, { recursive: true });
  const directory = mkdtempSync(join(scratch, "body-lifecycle-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  cpSync(join(built, "bundle"), join(directory, "bundle"), { recursive: true });
  const wrapper = join(directory, "entry.mjs");
  writeFileSync(wrapper, `import worker from ${JSON.stringify("./bundle/entry.js")};
const gets = [];
let active = 0, peak = 0, cancelled = 0, pointer = 'g1', delayOld = false;
const values = new Map([['blobs/test.crate','payload'],['generations/g1/llms.txt','first'],['generations/g2/llms.txt','second']]);
const metadata = text => ({ size: new TextEncoder().encode(text).length, etag: 'test', httpEtag: '"test"', body: null });
const store = {
 async head(key) { const text = key === 'current' ? pointer : values.get(key); return text == null ? null : metadata(text); },
 async get(key) {
  gets.push(key);
  const text = key === 'current' ? pointer : values.get(key);
  if (text == null) return null;
  if (delayOld && key === 'generations/g1/llms.txt') await new Promise(done => setTimeout(done, 40));
  if (active >= 2) throw new Error('finite S3 connection pool exhausted');
  active++; peak = Math.max(peak, active);
  let sent = false, released = false;
  const release = () => { if (!released) { released = true; active--; } };
  const body = new ReadableStream({ pull(controller) { if (sent) { release(); controller.close(); } else { sent = true; controller.enqueue(new TextEncoder().encode(text)); } }, cancel() { cancelled++; release(); } }, { highWaterMark: 0 });
  return { ...metadata(text), body, text() { return new Response(body).text(); } };
 }
};
export default { async fetch(req, env, ctx) {
 const path = new URL(req.url).pathname;
 if (path === '/__state') return Response.json({ active, peak, cancelled, gets: gets.slice(-12) });
 if (path === '/__rotate') { pointer = 'g2'; delayOld = true; return new Response('ok'); }
 if (path === '/__missing') { pointer = null; return new Response('ok'); }
 return worker.fetch(req, { ...env, MYCRATES: store, STUFF_RELEASE: 'test', STUFF_ROUTES: JSON.stringify([{ host:'crates.test',bucket_binding:'MYCRATES',key_prefix:'' }]) }, ctx);
} };
`);
  const descriptor = JSON.parse(readFileSync(join(built, "worker.config.json"), "utf8"));
  const harness = createTestHarness({ root: directory, workers: [{ config: {
    name: "body-lifecycle", main: wrapper, no_bundle: true,
    compatibility_date: descriptor.compatibilityDate, compatibility_flags: descriptor.compatibilityFlags,
    rules: [{ type: "ESModule", globs: ["**/*.mjs", "**/*.js"], fallthrough: true }, { type: "CompiledWasm", globs: ["**/*.wasm"], fallthrough: true }],
  } }] });
  t.after(() => harness.close());
  await harness.listen();
  const fetch = (path, init) => harness.getWorker().fetch(`https://crates.test${path}`, init);
  const state = async () => (await fetch("/__state")).json();
  for (let i = 0; i < 60; i++) {
    const head = await fetch("/blobs/test.crate", { method: "HEAD" });
    assert.equal(head.status, 200);
    assert.equal(await head.text(), "");
    const conditional = await fetch("/blobs/test.crate", { headers: { "if-none-match": '"test"' } });
    assert.equal(conditional.status, 304);
    const failed = await fetch("/blobs/test.crate", { headers: { "if-match": '"different"' } });
    assert.equal(failed.status, 412);
    await failed.text();
    assert.equal((await state()).active, 0);
  }
  const read = await fetch("/blobs/test.crate");
  assert.equal(await read.text(), "payload");
  assert.equal((await state()).active, 0);
  assert.equal(await (await fetch("/llms.txt")).text(), "first");
  await fetch("/__rotate");
  assert.equal(await (await fetch("/llms.txt")).text(), "second");
  await new Promise(done => setTimeout(done, 70));
  assert.equal((await state()).active, 0);
  await fetch("/__missing");
  assert.equal((await fetch("/llms.txt")).status, 404);
  await new Promise(done => setTimeout(done, 70));
  const final = await state();
  assert.equal(final.active, 0);
  assert.ok(final.cancelled >= 122, JSON.stringify(final));
  assert.ok(final.peak <= 2, JSON.stringify(final));
});
