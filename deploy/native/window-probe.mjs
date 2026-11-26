import { createHash } from "node:crypto";
import { appendFileSync, readFileSync } from "node:fs";
import { Agent, request as httpsRequest } from "node:https";

const usage = "usage: window-probe.mjs TARGETS.json OUTPUT.jsonl SECONDS [--long URL=SHA256[@RESOLVE] ...]";
const [targetsFile, output, seconds, ...rest] = process.argv.slice(2);
if (!targetsFile || !output || !Number(seconds)) { console.error(usage); process.exit(2); }
const targets = JSON.parse(readFileSync(targetsFile, "utf8"));
const longs = [];
for (let i = 0; i < rest.length; i += 2) {
  if (rest[i] !== "--long") { console.error(usage); process.exit(2); }
  const match = /^(https:\/\/[^=]+)=([0-9a-f]{64})(?:@(\d+\.\d+\.\d+\.\d+))?$/.exec(rest[i + 1] ?? "");
  if (!match) { console.error(usage); process.exit(2); }
  longs.push({ name: `long:${new URL(match[1]).pathname.slice(-16)}${match[3] ? ".direct" : ".public"}`, url: match[1], sha256: match[2], ...(match[3] ? { resolve: match[3] } : {}), path: match[3] ? "direct" : "public" });
}
const record = (value) => appendFileSync(output, `${JSON.stringify({ at: new Date().toISOString(), ...value })}\n`);

const agents = { public: new Agent({ keepAlive: true }), direct: new Agent({ keepAlive: true }) };
function fetchBody(target, timeoutMs) {
  return new Promise(resolve => {
    const started = performance.now();
    const lookup = target.resolve ? (_h, o, cb) => o?.all ? cb(null, [{ address: target.resolve, family: 4 }]) : cb(null, target.resolve, 4) : undefined;
    let done = false;
    const finish = v => { if (!done) { done = true; resolve({ ms: Math.round(performance.now() - started), ...v }); } };
    const req = httpsRequest(target.url, { agent: agents[target.path], headers: { "user-agent": "stuff-window-probe", "accept-encoding": "identity" }, ...(lookup ? { lookup } : {}) }, res => {
      const hash = createHash("sha256");
      let bytes = 0;
      res.on("data", c => { bytes += c.length; hash.update(c); });
      res.on("end", () => {
        const sha256 = hash.digest("hex");
        const length = res.headers["content-length"];
        const complete = res.complete && (length === undefined || Number(length) === bytes);
        finish({ status: res.statusCode, bytes, complete, digestOk: !target.sha256 || target.sha256 === sha256, ok: res.statusCode === 200 && complete && (!target.sha256 || target.sha256 === sha256), cache: res.headers["cf-cache-status"] ?? null });
      });
      res.on("aborted", () => finish({ status: res.statusCode, bytes, ok: false, error: "aborted" }));
      res.on("error", e => finish({ status: res.statusCode, bytes, ok: false, error: e.code ?? e.name }));
    });
    req.setTimeout(timeoutMs, () => req.destroy(Object.assign(new Error("timeout"), { code: "ETIMEDOUT" })));
    req.on("error", e => finish({ ok: false, error: e.code ?? e.name }));
    req.end();
  });
}

const deadline = Date.now() + Number(seconds) * 1000;
const summary = {};
const tally = (name, result) => {
  const entry = summary[name] ??= { ok: 0, failed: 0 };
  if (result.ok) entry.ok += 1; else entry.failed += 1;
};
const longResults = Promise.all(longs.map(async target => {
  const result = await fetchBody(target, 3_600_000);
  record({ name: target.name, path: target.path, long: true, ...result });
  tally(target.name, result);
}));
await Promise.all(targets.map(async target => {
  while (Date.now() < deadline) {
    const result = await fetchBody(target, 60_000);
    record({ name: target.name, path: target.path, ...result });
    tally(target.name, result);
    await new Promise(r => setTimeout(r, 250));
  }
}));
await longResults;
const failed = Object.values(summary).reduce((sum, entry) => sum + entry.failed, 0);
console.log(JSON.stringify({ failed, summary }));
process.exitCode = failed === 0 ? 0 : 1;
