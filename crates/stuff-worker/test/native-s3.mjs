import { createHash, randomUUID } from "node:crypto";
import { createServer } from "node:http";

const escape = (value) => value.replace(/[<>&'"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", "'": "&apos;", '"': "&quot;" })[c]);

export function fakeS3() {
  const buckets = new Map();
  const uploads = new Map();
  const faults = [];
  const log = [];
  const bucket = (name) => {
    if (!buckets.has(name)) buckets.set(name, new Map());
    return buckets.get(name);
  };
  const latest = (name, key) => {
    const versions = bucket(name).get(key) ?? [];
    const top = versions.at(-1);
    return top && !top.deleteMarker ? top : null;
  };
  const write = (name, key, body) => {
    const version = { versionId: randomUUID().replaceAll("-", ""), body, etag: `"${createHash("md5").update(body).digest("hex")}"`, deleteMarker: false };
    const versions = bucket(name).get(key) ?? [];
    versions.push(version);
    bucket(name).set(key, versions);
    return version;
  };
  const reply = (res, status, body = "", headers = {}) => {
    res.writeHead(status, { "content-length": Buffer.byteLength(body), ...headers });
    res.end(body);
  };
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, "http://s3");
    const [, name, ...rest] = url.pathname.split("/");
    const key = rest.map(decodeURIComponent).join("/");
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    log.push({ method: req.method, bucket: name, key, query: url.search });
    const fault = faults.findIndex(item => item.method === req.method && item.key === key && (item.bucket === undefined || item.bucket === name));
    if (fault !== -1) {
      const [item] = faults.splice(fault, 1);
      if (item.delayMs) await new Promise(resolve => setTimeout(resolve, item.delayMs));
      if (item.status) return reply(res, item.status, "<Error><Code>InjectedFault</Code></Error>");
    }
    const q = url.searchParams;
    if (key === "") {
      if (q.has("versioning")) return reply(res, 200, "<VersioningConfiguration><Status>Enabled</Status></VersioningConfiguration>");
      if (q.has("versions")) {
        const prefix = q.get("prefix") ?? "";
        const entries = [...bucket(name).entries()].filter(([k]) => k.startsWith(prefix)).sort(([a], [b]) => (a < b ? -1 : 1));
        const items = entries.flatMap(([k, versions]) => versions.map(v => `<${v.deleteMarker ? "DeleteMarker" : "Version"}><Key>${escape(k)}</Key><VersionId>${v.versionId}</VersionId></${v.deleteMarker ? "DeleteMarker" : "Version"}>`)).join("");
        return reply(res, 200, `<ListVersionsResult><IsTruncated>false</IsTruncated>${items}</ListVersionsResult>`);
      }
      if (q.get("list-type") === "2") {
        const prefix = q.get("prefix") ?? "";
        const max = Number(q.get("max-keys") ?? "1000");
        const after = q.get("continuation-token") ?? "";
        const keys = [...bucket(name).keys()].filter(k => k.startsWith(prefix) && k > after && latest(name, k) !== null).sort();
        const page = keys.slice(0, max);
        const truncated = keys.length > max;
        return reply(res, 200, `<ListBucketResult><IsTruncated>${truncated}</IsTruncated>${truncated ? `<NextContinuationToken>${escape(page.at(-1))}</NextContinuationToken>` : ""}${page.map(k => `<Contents><Key>${escape(k)}</Key></Contents>`).join("")}</ListBucketResult>`);
      }
      return reply(res, 400);
    }
    if (req.method === "POST" && q.has("uploads")) {
      const id = randomUUID();
      uploads.set(id, { name, key, parts: new Map() });
      return reply(res, 200, `<InitiateMultipartUploadResult><UploadId>${id}</UploadId></InitiateMultipartUploadResult>`);
    }
    if (req.method === "PUT" && q.has("uploadId")) {
      const upload = uploads.get(q.get("uploadId"));
      if (!upload) return reply(res, 404);
      upload.parts.set(Number(q.get("partNumber")), body);
      return reply(res, 200, "", { etag: `"${createHash("md5").update(body).digest("hex")}"` });
    }
    if (req.method === "POST" && q.has("uploadId")) {
      const upload = uploads.get(q.get("uploadId"));
      if (!upload) return reply(res, 404);
      if (req.headers["if-none-match"] === "*" && latest(name, key)) return reply(res, 412);
      uploads.delete(q.get("uploadId"));
      const version = write(name, key, Buffer.concat([...upload.parts.entries()].sort(([a], [b]) => a - b).map(([, part]) => part)));
      return reply(res, 200, `<CompleteMultipartUploadResult><ETag>${escape(version.etag)}</ETag></CompleteMultipartUploadResult>`, { "x-amz-version-id": version.versionId });
    }
    if (req.method === "DELETE" && q.has("uploadId")) { uploads.delete(q.get("uploadId")); return reply(res, 204); }
    if (req.method === "PUT") {
      const existing = latest(name, key);
      if (req.headers["if-none-match"] === "*" && existing) return reply(res, 412);
      if (req.headers["if-match"] !== undefined && req.headers["if-match"] !== existing?.etag) return reply(res, 412);
      const version = write(name, key, body);
      return reply(res, 200, "", { etag: version.etag, "x-amz-version-id": version.versionId });
    }
    if (req.method === "DELETE") {
      const versions = bucket(name).get(key) ?? [];
      if (q.has("versionId")) bucket(name).set(key, versions.filter(v => v.versionId !== q.get("versionId")));
      else versions.push({ versionId: randomUUID().replaceAll("-", ""), deleteMarker: true }), bucket(name).set(key, versions);
      return reply(res, 204);
    }
    if (req.method === "GET" || req.method === "HEAD") {
      const object = q.has("versionId") ? (bucket(name).get(key) ?? []).find(v => v.versionId === q.get("versionId") && !v.deleteMarker) : latest(name, key);
      if (!object) return reply(res, 404, req.method === "HEAD" ? "" : "<Error><Code>NoSuchKey</Code></Error>");
      const headers = { etag: object.etag, "x-amz-version-id": object.versionId, "content-type": "application/octet-stream" };
      const range = /^bytes=(\d+)-(\d+)$/.exec(req.headers.range ?? "");
      if (range) {
        const start = Number(range[1]);
        const end = Math.min(Number(range[2]), object.body.length - 1);
        const slice = object.body.subarray(start, end + 1);
        res.writeHead(206, { ...headers, "content-length": slice.length, "content-range": `bytes ${start}-${end}/${object.body.length}` });
        return res.end(req.method === "HEAD" ? undefined : slice);
      }
      res.writeHead(200, { ...headers, "content-length": object.body.length });
      return res.end(req.method === "HEAD" ? undefined : object.body);
    }
    return reply(res, 405);
  });
  return {
    server, log, faults,
    put(name, key, value) { return write(name, key, Buffer.from(value)); },
    get(name, key) { const object = latest(name, key); return object ? object.body.toString("utf8") : null; },
    versions(name, key) { return (bucket(name).get(key) ?? []).map(v => v.versionId); },
    listen() { return new Promise(resolve => server.listen(0, "127.0.0.1", () => resolve(`http://127.0.0.1:${server.address().port}`))); },
    close() { server.closeAllConnections(); return new Promise(resolve => server.close(resolve)); },
  };
}
