import { hex, quote, sha, signingMaterial } from "./sigv4.js";

export interface StoreEnv {
  STUFF_S3_BUCKET_BINDINGS?: string;
  S3_ENDPOINT?: string;
  S3_REGION?: string;
  S3_ACCESS_KEY_ID?: string;
  S3_SECRET_ACCESS_KEY?: string;
}
export function storeBucket(env: StoreEnv, binding: string): string {
  const mapping = JSON.parse(env.STUFF_S3_BUCKET_BINDINGS ?? "") as Record<string, unknown>;
  const name = mapping[binding];
  if (typeof name !== "string" || !/^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$/.test(name)) throw new Error("invalid store bucket");
  return name;
}
export async function storeRequest(env: StoreEnv, method: string, bucket: string, key: string, options: {
  query?: URLSearchParams; headers?: Headers; body?: ReadableStream<Uint8Array> | string | null;
  payload?: string; signal?: AbortSignal;
} = {}): Promise<Response> {
  if (!env.S3_ENDPOINT || !env.S3_REGION || !env.S3_ACCESS_KEY_ID || !env.S3_SECRET_ACCESS_KEY) throw new Error("store unavailable");
  const url = new URL(env.S3_ENDPOINT);
  url.pathname = `${url.pathname.replace(/\/$/, "")}/${quote(bucket)}${key ? `/${key.split("/").map(quote).join("/")}` : ""}`;
  if (options.query) url.search = options.query.toString();
  const headers = new Headers(options.headers);
  const date = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  headers.set("host", url.host);
  headers.set("x-amz-date", date);
  headers.set("x-amz-content-sha256", options.payload ?? await sha(typeof options.body === "string" ? options.body : ""));
  const names = [...headers.keys()].sort();
  const material = await signingMaterial(method, url, headers, names, headers.get("x-amz-content-sha256")!, date, env.S3_REGION, env.S3_SECRET_ACCESS_KEY);
  const signature = hex(await crypto.subtle.sign("HMAC", material.key, material.message));
  headers.set("authorization", `AWS4-HMAC-SHA256 Credential=${env.S3_ACCESS_KEY_ID}/${date.slice(0, 8)}/${env.S3_REGION}/s3/aws4_request, SignedHeaders=${names.join(";")}, Signature=${signature}`);
  const init: RequestInit & { duplex?: "half" } = { method, headers, redirect: "manual", signal: options.signal ?? AbortSignal.timeout(30_000), ...(options.body == null ? {} : { body: options.body, duplex: "half" }) };
  return fetch(url, init);
}

async function controlText(response: Response): Promise<string> {
  if (!response.ok || response.body === null) throw new Error("store control request failed");
  const reader = response.body.getReader();
  let value = "";
  let size = 0;
  const decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: false });
  try {
    while (true) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.byteLength;
      if (size > 4 * 1024 * 1024) throw new Error("store control response too large");
      value += decoder.decode(part.value, { stream: true });
    }
    return value + decoder.decode();
  } finally { await reader.cancel().catch(() => undefined); reader.releaseLock(); }
}
function xmlText(value: string): string {
  return value.replace(/&(#x[0-9a-fA-F]+|#[0-9]+|amp|lt|gt|quot|apos);/g, (_, entity: string) => {
    if (entity.startsWith("#")) return String.fromCodePoint(Number.parseInt(entity.slice(entity.startsWith("#x") ? 2 : 1), entity.startsWith("#x") ? 16 : 10));
    return ({ amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" } as Record<string, string>)[entity]!;
  });
}
function element(xml: string, tag: string): string | undefined {
  const match = new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`).exec(xml);
  return match ? xmlText(match[1]!) : undefined;
}
export async function objectVersions(env: StoreEnv, bucket: string, key: string): Promise<string[]> {
  const versioning = await controlText(await storeRequest(env, "GET", bucket, "", { query: new URLSearchParams({ versioning: "" }) }));
  if (element(versioning, "Status") !== "Enabled") throw new Error("garbage collection requires bucket versioning");
  const versions = new Set<string>();
  const pages = new Set<string>();
  let marker = "";
  let versionMarker = "";
  for (;;) {
    const query = new URLSearchParams({ versions: "", prefix: key });
    if (marker) query.set("key-marker", marker);
    if (versionMarker) query.set("version-id-marker", versionMarker);
    const xml = await controlText(await storeRequest(env, "GET", bucket, "", { query }));
    if (!/<ListVersionsResult(?:\s|>)/.test(xml)) throw new Error("invalid version listing");
    for (const match of xml.matchAll(/<(Version|DeleteMarker)>([\s\S]*?)<\/\1>/g)) {
      const listedKey = element(match[2]!, "Key");
      const version = element(match[2]!, "VersionId");
      if (listedKey === undefined || !version) throw new Error("invalid object version");
      if (listedKey === key) versions.add(version);
    }
    const truncated = element(xml, "IsTruncated");
    if (truncated === "false") break;
    if (truncated !== "true") throw new Error("invalid version pagination");
    marker = element(xml, "NextKeyMarker") ?? "";
    versionMarker = element(xml, "NextVersionIdMarker") ?? "";
    const cursor = JSON.stringify([marker, versionMarker]);
    if (!marker || pages.has(cursor)) throw new Error("invalid version cursor");
    pages.add(cursor);
  }
  return [...versions];
}
