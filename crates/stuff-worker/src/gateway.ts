
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
const bytes = (value: string): Uint8Array => new TextEncoder().encode(value);
const hex = (value: ArrayBuffer): string => Array.from(new Uint8Array(value), b => b.toString(16).padStart(2, "0")).join("");
const sha = async (value: string): Promise<string> => hex(await crypto.subtle.digest("SHA-256", bytes(value)));
const mac = async (key: string | ArrayBuffer, value: string): Promise<ArrayBuffer> => {
  const imported = await crypto.subtle.importKey("raw", typeof key === "string" ? bytes(key) : key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return crypto.subtle.sign("HMAC", imported, bytes(value));
};
const quote = (s: string): string => encodeURIComponent(s).replace(/[!'()*]/g, c => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);
function query(url: URL): string {
  return [...url.searchParams.entries()].map(([k, v]) => [quote(k), quote(v)] as const)
    .sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0)
    .map(([k, v]) => `${k}=${v}`).join("&");
}
async function signingMaterial(method: string, url: URL, headers: Headers, names: string[], payload: string, date: string, region: string, secret: string): Promise<{ key: CryptoKey; message: Uint8Array }> {
  const canonical = `${method}\n${url.pathname}\n${query(url)}\n${names.map(n => `${n}:${headers.get(n)!.trim().replace(/\s+/g, " ")}\n`).join("")}\n${names.join(";")}\n${payload}`;
  const scope = `${date.slice(0, 8)}/${region}/s3/aws4_request`;
  const key = await mac(await mac(await mac(await mac(`AWS4${secret}`, date.slice(0, 8)), region), "s3"), "aws4_request");
  return { key: await crypto.subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]), message: bytes(`AWS4-HMAC-SHA256\n${date}\n${scope}\n${await sha(canonical)}`) };
}
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
      || (matches[0]![0] === "OCI_BLOBS" && /^sha256\/[0-9a-f]{64}$/.test(key));
    if (!immutable) return new Response("forbidden", { status: 403 });
    const token = req.headers.get("x-amz-security-token");
    if (!token || !(req.headers.get("authorization") ?? "").includes("x-amz-security-token")) return new Response("forbidden", { status: 403 });
    const lease = await coordinator(registry, "gateway-lease", new Request("https://coordinator/", { method: "POST", body: JSON.stringify({ token, generation }) }));
    if (!lease.ok) return new Response("forbidden", { status: 403 });
  }
  if (!env.S3_ENDPOINT || !env.S3_REGION || !env.S3_ACCESS_KEY_ID || !env.S3_SECRET_ACCESS_KEY) return new Response("unavailable", { status: 503 });
  const endpoint = new URL(env.S3_ENDPOINT);
  endpoint.pathname = `${endpoint.pathname.replace(/\/$/, "")}/${match[1]}${match[2] === undefined ? "" : `/${match[2]}`}`;
  endpoint.search = url.search;
  const headers = new Headers();
  for (const name of ["content-type", "content-length", "range", "if-match", "if-none-match", "x-amz-content-sha256", "x-amz-date"]) { const value = req.headers.get(name); if (value !== null) headers.set(name, value); }
  if ((req.method === "PUT" && !url.search) || (req.method === "POST" && url.searchParams.has("uploadId"))) headers.set("if-none-match", "*");
  headers.set("host", endpoint.host);
  const names = [...headers.keys()].sort();
  const date = headers.get("x-amz-date")!;
  const material = await signingMaterial(req.method, endpoint, headers, names, headers.get("x-amz-content-sha256")!, date, env.S3_REGION, env.S3_SECRET_ACCESS_KEY);
  const sig = hex(await crypto.subtle.sign("HMAC", material.key, material.message));
  headers.set("authorization", `AWS4-HMAC-SHA256 Credential=${env.S3_ACCESS_KEY_ID}/${date.slice(0, 8)}/${env.S3_REGION}/s3/aws4_request, SignedHeaders=${names.join(";")}, Signature=${sig}`);
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
  const options: RequestInit & { duplex?: "half" } = { method: req.method, headers, redirect: "manual", signal: req.signal, ...(body === null ? {} : { body, duplex: "half" }) };
  try { return await fetch(endpoint.href, options); }
  catch { return new Response(invalidPayload ? "invalid payload" : "store unavailable", { status: invalidPayload ? 400 : 503 }); }
  finally {
    if (writer !== null) { await writer.abort().catch(() => undefined); writer.releaseLock(); }
  }
}
