import { bytes, hex, sha, signingMaterial } from "./sigv4.js";
import { storeRequest } from "./s3.js";

interface GatewayEnv {
  STUFF_S3_BUCKET_BINDINGS?: string;
  STUFF_S3_ACCESS_KEY_ID?: string;
  STUFF_S3_SECRET_ACCESS_KEY?: string;
  S3_ENDPOINT?: string;
  S3_REGION?: string;
  S3_ACCESS_KEY_ID?: string;
  S3_SECRET_ACCESS_KEY?: string;
}
type Coordinator = (registry: string, op: string, request?: Request) => Promise<Response>;
const registries: Record<string, string> = { MYCRATES: "cargo", MYNPM: "npm", PYPI: "pypi", OCI: "oci", OCI_BLOBS: "oci", MIRROR: "mirror" };
async function authenticate(req: Request, env: GatewayEnv): Promise<boolean> {
  const auth = /^AWS4-HMAC-SHA256 Credential=([^/]+)\/(\d{8})\/auto\/s3\/aws4_request, SignedHeaders=([a-z0-9;-]+), Signature=([0-9a-f]{64})$/.exec(req.headers.get("authorization") ?? "");
  const date = req.headers.get("x-amz-date") ?? "";
  const payload = req.headers.get("x-amz-content-sha256") ?? "";
  if (!auth || !env.STUFF_S3_ACCESS_KEY_ID || !env.STUFF_S3_SECRET_ACCESS_KEY || auth[1] !== env.STUFF_S3_ACCESS_KEY_ID || !/^\d{8}T\d{6}Z$/.test(date) || date.slice(0, 8) !== auth[2] || !/^[0-9a-f]{64}$/.test(payload)) return false;
  const instant = Date.parse(`${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}T${date.slice(9, 11)}:${date.slice(11, 13)}:${date.slice(13, 15)}Z`);
  if (!Number.isFinite(instant) || Math.abs(Date.now() - instant) > 900000 || new Date(instant).toISOString().replace(/[-:]/g, "").replace(".000", "") !== date) return false;
  const names = auth[3]!.split(";");
  if (names.join(";") !== [...new Set(names)].sort().join(";") || !["host", "x-amz-content-sha256", "x-amz-date"].every(n => names.includes(n)) || names.some(n => !req.headers.has(n)) || (req.headers.has("x-amz-security-token") && !names.includes("x-amz-security-token"))) return false;
  const material = await signingMaterial(req.method, new URL(req.url), req.headers, names, payload, date, "auto", env.STUFF_S3_SECRET_ACCESS_KEY);
  const supplied = Uint8Array.from(auth[4]!.match(/../g)!, pair => Number.parseInt(pair, 16));
  return crypto.subtle.verify("HMAC", material.key, supplied, material.message);
}
export async function gateway(req: Request, env: GatewayEnv, coordinator: Coordinator): Promise<Response> {
  if (!await authenticate(req, env)) return new Response("unauthorized", { status: 403 });
  const url = new URL(req.url);
  const match = /^\/_s3\/([^/]+)(?:\/(.*))?$/.exec(url.pathname);
  if (!match) return new Response("not found", { status: 404 });
  let mapping: Record<string, unknown>;
  let bucket: string, key: string;
  try { mapping = JSON.parse(env.STUFF_S3_BUCKET_BINDINGS ?? "") as Record<string, unknown>; bucket = decodeURIComponent(match[1]!); key = decodeURIComponent(match[2] ?? ""); } catch { return new Response("unavailable", { status: 503 }); }
  const matches = Object.entries(registries).filter(([binding]) => mapping[binding] === bucket);
  if (matches.length !== 1 || !bucket || key.split("/").some(p => p === "." || p === "..")) return new Response("forbidden", { status: 403 });
  const registry = matches[0]![1];
  if (req.body === null && req.headers.get("x-amz-content-sha256") !== await sha("")) return new Response("invalid payload", { status: 403 });
  const read = req.method === "GET" || req.method === "HEAD";
  if (read && key === "current") {
    const result = await coordinator(registry, "current");
    if (!result.ok) return new Response("unavailable", { status: 503 });
    const current = await result.json() as { generation: string | null };
    if (current.generation === null) return new Response(null, { status: 404 });
    return new Response(req.method === "HEAD" ? null : current.generation, { headers: { "content-length": String(bytes(current.generation).length), etag: `"${await sha(current.generation)}"` } });
  }
  if (!read) {
    const names = [...url.searchParams.keys()];
    const uploadId = url.searchParams.get("uploadId");
    const multipart = (req.method === "POST" && names.length === 1 && (names[0] === "uploads" || (names[0] === "uploadId" && !!uploadId))) || (req.method === "PUT" && names.length === 2 && !!uploadId && /^[1-9][0-9]*$/.test(url.searchParams.get("partNumber") ?? "") && names.includes("uploadId") && names.includes("partNumber")) || (req.method === "DELETE" && names.length === 1 && names[0] === "uploadId" && !!uploadId);
    if (!key || key === "current" || !(req.method === "PUT" && names.length === 0 || multipart)) return new Response("forbidden", { status: 403 });
    const generation = /^generations\/([a-zA-Z0-9_-]{1,128})\/.+/.exec(key)?.[1] ?? /^manifests\/([a-zA-Z0-9_-]{1,128})\.json$/.exec(key)?.[1];
    const sharedPrefix = { MYCRATES: "blobs/", MYNPM: "tarballs/", PYPI: "wheels/" }[matches[0]![0]];
    const immutable = !!generation || (sharedPrefix !== undefined && key.startsWith(sharedPrefix) && key.length > sharedPrefix.length)
      || (matches[0]![0] === "OCI" && /^oci\/manifests\/sha256\/[0-9a-f]{64}$/.test(key))
      || (matches[0]![0] === "OCI_BLOBS" && /^sha256\/[0-9a-f]{64}$/.test(key));
    if (!immutable) return new Response("forbidden", { status: 403 });
    const token = req.headers.get("x-amz-security-token");
    if (!token || !(req.headers.get("authorization") ?? "").includes("x-amz-security-token")) return new Response("forbidden", { status: 403 });
    const lease = await coordinator(registry, "gateway-lease", new Request("https://coordinator/", { method: "POST", body: JSON.stringify({ token, generation }) }));
    if (!lease.ok) return new Response("forbidden", { status: 403 });
  }
  const headers = new Headers();
  for (const name of ["content-type", "content-length", "range", "if-match", "if-none-match"]) { const value = req.headers.get(name); if (value !== null) headers.set(name, value); }
  if ((req.method === "PUT" && !url.search) || (req.method === "POST" && url.searchParams.has("uploadId"))) headers.set("if-none-match", "*");
  let invalidPayload = false;
  let body: ReadableStream<Uint8Array> | null = null;
  let writer: WritableStreamDefaultWriter<ArrayBuffer | ArrayBufferView> | null = null;
  if (req.body !== null) {
    const digest = new crypto.DigestStream("SHA-256");
    const digestWriter = digest.getWriter();
    writer = digestWriter;
    void digest.digest.catch(() => undefined);
    let last: Uint8Array | null = null;
    // Keep the final bytes back until the signed payload digest is verified, before S3 can commit.
    body = req.body.pipeThrough(new TransformStream<Uint8Array, Uint8Array>({
      async transform(chunk, controller) {
        for (let start = 0; start < chunk.byteLength; start += 65_536) {
          const part = chunk.subarray(start, start + 65_536);
          await digestWriter.write(part);
          if (last !== null) controller.enqueue(last);
          last = part.slice();
        }
      },
      async flush(controller) {
        await digestWriter.close();
        if (hex(await digest.digest) !== req.headers.get("x-amz-content-sha256")) { invalidPayload = true; throw new Error("payload checksum mismatch"); }
        if (last !== null) controller.enqueue(last);
      },
      cancel(reason) { void digestWriter.abort(reason).catch(() => undefined); },
    }));
  }
  try { return await storeRequest(env, req.method, bucket, key, { query: url.searchParams, headers, body, payload: req.headers.get("x-amz-content-sha256")!, signal: req.signal }); }
  catch { return new Response(invalidPayload ? "invalid payload" : "store unavailable", { status: invalidPayload ? 400 : 503 }); }
  finally {
    if (writer !== null) { await writer.abort().catch(() => undefined); writer.releaseLock(); }
  }
}
