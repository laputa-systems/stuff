import { createHash } from "node:crypto";
import { request } from "node:http";

const usage = "usage: parity.mjs REFERENCE_HOST:PORT CANDIDATE_HOST:PORT [--limit N] [--packages N] [--json]";
const args = process.argv.slice(2);
if (args.length < 2) { console.error(usage); process.exit(2); }
const [reference, candidate] = args;
const limit = Number(args[args.indexOf("--limit") + 1] || 600);
const HOSTS = ["stuff", "crates", "crates-blobs", "npm", "pypi", "oci", "oci-blobs", "mirror"].map(name => `${name}.17166969.xyz`);
const IGNORED_HEADERS = new Set(["date", "connection", "keep-alive", "transfer-encoding"]);

function send(target, spec) {
  const [host, port] = target.split(":");
  return new Promise((resolve, reject) => {
    const started = performance.now();
    const req = request({ host, port: Number(port), method: spec.method ?? "GET", path: spec.path, headers: { host: spec.host, "x-forwarded-proto": "https", "x-oo-ingress": "public", ...spec.headers } }, res => {
      const hash = createHash("sha256");
      let bytes = 0;
      const chunks = [];
      res.on("data", chunk => { hash.update(chunk); bytes += chunk.length; if (bytes <= 4 * 1024 * 1024) chunks.push(chunk); });
      res.on("end", () => {
        const headers = {};
        for (let i = 0; i + 1 < res.rawHeaders.length; i += 2) {
          const name = res.rawHeaders[i].toLowerCase();
          if (!IGNORED_HEADERS.has(name)) headers[name] = headers[name] === undefined ? res.rawHeaders[i + 1] : `${headers[name]}, ${res.rawHeaders[i + 1]}`;
        }
        resolve({ status: res.statusCode, headers, bytes, sha256: hash.digest("hex"), complete: res.complete, ms: performance.now() - started, text: bytes <= 4 * 1024 * 1024 ? Buffer.concat(chunks).toString("utf8") : "" });
      });
      res.on("error", reject);
    });
    req.setTimeout(600_000, () => req.destroy(new Error("timeout")));
    req.on("error", reject);
    req.end();
  });
}

function links(spec, text) {
  const found = [];
  for (const match of text.matchAll(/(?:href|src)="([^"#]+)"/g)) {
    try {
      const url = new URL(match[1], `https://${spec.host}${spec.path}`);
      if (HOSTS.includes(url.host)) found.push({ host: url.host, path: `${url.pathname}${url.search}` });
    } catch { continue; }
  }
  for (const match of text.matchAll(/https:\/\/([a-z-]+\.17166969\.xyz)(\/[^\s"'<>)]*)/g)) found.push({ host: match[1], path: match[2] });
  return found;
}

const queue = [
  ...HOSTS.map(host => ({ host, path: "/" })),
  { host: "stuff.17166969.xyz", path: "/llms.txt" },
  { host: "crates.17166969.xyz", path: "/current/registry/config.json" },
  { host: "crates.17166969.xyz", path: "/config.json" },
  { host: "crates.17166969.xyz", path: "/current/crates-io/config.json" },
  { host: "npm.17166969.xyz", path: "/current/" },
  { host: "pypi.17166969.xyz", path: "/current/simple/" },
  { host: "mirror.17166969.xyz", path: "/current/SHA256SUMS" },
  { host: "oci.17166969.xyz", path: "/v2/" },
  { host: "stuff.17166969.xyz", path: "/missing-object" },
  { host: "crates.17166969.xyz", path: "/../_publication/cargo/current" },
  { host: "crates.17166969.xyz", path: "/%2e%2e/%2e%2e/etc/passwd" },
  { host: "oci-blobs.17166969.xyz", path: `/sha256/${"0".repeat(64)}` },
  { host: "oci.17166969.xyz", path: "/v2/missing/repo/tags/list" },
];
const sample = (items, count) => items.length <= count ? items : Array.from({ length: count }, (_, i) => items[Math.floor(i * items.length / count)]);
const cargoIndex = name => name.length <= 2 ? `${name.length}/${name}` : name.length === 3 ? `3/${name[0]}/${name}` : `${name.slice(0, 2)}/${name.slice(2, 4)}/${name}`;
const perRegistry = Number(args[args.indexOf("--packages") + 1] || 0);
const BIG = 64 * 1024 * 1024;
async function catalogSeeds() {
  const json = async (host, path) => { const r = await send(reference, { host, path }); return r.status === 200 ? JSON.parse(r.text) : null; };
  const seeds = [];
  const crates = await json("crates.17166969.xyz", "/current/catalog.json");
  for (const pkg of sample(crates?.packages ?? [], perRegistry)) {
    const path = `/current/${pkg.source === "upstream" ? "crates-io" : "registry"}/${cargoIndex(pkg.name.toLowerCase())}`;
    seeds.push({ host: "crates.17166969.xyz", path });
    const index = await send(reference, { host: "crates.17166969.xyz", path });
    if (index.status !== 200) continue;
    for (const line of index.text.split("\n").filter(Boolean).slice(-2)) seeds.push({ host: "crates-blobs.17166969.xyz", path: `/blobs/${JSON.parse(line).cksum}.crate` });
  }
  const npm = await json("npm.17166969.xyz", "/current/catalog.json");
  for (const pkg of sample(npm?.packages ?? [], perRegistry)) {
    const path = `/current/${pkg.name.replace("/", "%2f")}`;
    seeds.push({ host: "npm.17166969.xyz", path }, { host: "npm.17166969.xyz", path: `/current/${pkg.name}` });
    const packument = await send(reference, { host: "npm.17166969.xyz", path });
    try { for (const version of Object.values(JSON.parse(packument.text).versions ?? {}).slice(-2)) { const url = new URL(version.dist.tarball); seeds.push({ host: url.host, path: url.pathname }); } } catch { continue; }
  }
  const pypi = await json("pypi.17166969.xyz", "/current/catalog.json");
  for (const pkg of sample(pypi?.packages ?? [], perRegistry)) seeds.push({ host: "pypi.17166969.xyz", path: `/current/simple/${pkg.name}/` });
  const oci = await json("oci.17166969.xyz", "/current/catalog.json");
  for (const pkg of oci?.packages ?? []) {
    seeds.push({ host: "oci.17166969.xyz", path: `/v2/${pkg.name}/tags/list` });
    for (const version of pkg.versions) {
      const path = `/v2/${pkg.name}/manifests/${version.version}`;
      seeds.push({ host: "oci.17166969.xyz", path, method: "HEAD" }, { host: "oci.17166969.xyz", path });
      const manifest = await send(reference, { host: "oci.17166969.xyz", path });
      try {
        const value = JSON.parse(manifest.text);
        for (const item of [...(value.manifests ?? []), ...(value.layers ?? []), ...(value.config ? [value.config] : [])].slice(0, 6)) {
          if (value.manifests) seeds.push({ host: "oci.17166969.xyz", path: `/v2/${pkg.name}/manifests/${item.digest}` });
          else { seeds.push({ host: "oci.17166969.xyz", path: `/v2/${pkg.name}/blobs/${item.digest}` }); seeds.push({ host: "oci-blobs.17166969.xyz", path: `/sha256/${item.digest.slice(7)}`, large: item.size > BIG }); }
        }
        seeds.push({ host: "oci.17166969.xyz", path: `/v2/${pkg.name}/referrers/${manifest.headers["docker-content-digest"]}` });
      } catch { continue; }
    }
  }
  const sums = await send(reference, { host: "mirror.17166969.xyz", path: "/current/SHA256SUMS" });
  const mirrorCatalog = await json("mirror.17166969.xyz", "/current/catalog.json");
  const sizes = new Map((mirrorCatalog?.artifacts ?? []).map(item => [item.file, item.bytes]));
  for (const line of sums.text.split("\n").filter(Boolean)) {
    const file = line.split(/\s+/)[1];
    seeds.push({ host: "mirror.17166969.xyz", path: `/current/${file}`, large: (sizes.get(file) ?? 0) > BIG });
    if (mirrorCatalog?.generation) seeds.push({ host: "mirror.17166969.xyz", path: `/generations/${mirrorCatalog.generation}/${file}`, large: (sizes.get(file) ?? 0) > BIG });
  }
  return seeds;
}
if (perRegistry > 0) queue.unshift(...await catalogSeeds());
const seen = new Set();
const results = [];
let mismatches = 0;

async function compare(spec) {
  const [a, b] = await Promise.all([send(reference, spec), send(candidate, spec)]);
  const differences = [];
  if (a.status !== b.status) differences.push(`status ${a.status} != ${b.status}`);
  if (a.sha256 !== b.sha256) differences.push(`body ${a.bytes}/${a.sha256.slice(0, 12)} != ${b.bytes}/${b.sha256.slice(0, 12)}`);
  for (const name of new Set([...Object.keys(a.headers), ...Object.keys(b.headers)])) {
    if (a.headers[name] !== b.headers[name]) differences.push(`header ${name}: ${a.headers[name]} != ${b.headers[name]}`);
  }
  if (!a.complete || !b.complete) differences.push("incomplete body");
  if (differences.length > 0) mismatches += 1;
  results.push({ method: spec.method ?? "GET", host: spec.host, path: spec.path, headers: spec.headers ?? {}, status: b.status, bytes: b.bytes, sha256: b.sha256, referenceMs: Math.round(a.ms), candidateMs: Math.round(b.ms), differences });
  return a;
}

while (queue.length > 0 && seen.size < limit) {
  const spec = queue.shift();
  const key = `${spec.method ?? "GET"} ${spec.host}${spec.path}`;
  if (seen.has(key)) continue;
  seen.add(key);
  if (spec.large || spec.method === "HEAD") {
    await compare({ ...spec, method: "HEAD" });
    if (spec.large) await compare({ ...spec, headers: { range: "bytes=1048576-2097151" } });
    continue;
  }
  const reference = await compare(spec);
  if (reference.status === 200) {
    await compare({ ...spec, method: "HEAD" });
    if (reference.headers.etag) await compare({ ...spec, headers: { "if-none-match": reference.headers.etag } });
    if (reference.bytes > 16) {
      await compare({ ...spec, headers: { range: "bytes=3-11" } });
      await compare({ ...spec, headers: { range: `bytes=${reference.bytes - 5}-` } });
      await compare({ ...spec, headers: { range: `bytes=${reference.bytes + 10}-${reference.bytes + 20}` } });
    }
    if (/html|json|text|markdown/.test(reference.headers["content-type"] ?? "")) for (const link of links(spec, reference.text)) queue.push(link);
  }
}

const summary = { reference, candidate, requests: results.length, urls: seen.size, mismatches, bytes: results.reduce((sum, item) => sum + item.bytes, 0) };
if (args.includes("--json")) console.log(JSON.stringify({ summary, results }));
else {
  for (const item of results.filter(entry => entry.differences.length > 0)) console.log(`${item.method} ${item.host}${item.path} ${JSON.stringify(item.headers)}\n  ${item.differences.join("\n  ")}`);
  console.log(JSON.stringify(summary));
}
process.exitCode = mismatches === 0 ? 0 : 1;
