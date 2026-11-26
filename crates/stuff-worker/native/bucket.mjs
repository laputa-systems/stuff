import { createHash } from "node:crypto";
import { controlText, element, storeRequest } from "../src/s3.js";

const HEADERS_DEADLINE_MS = 30_000;
const LIST_PAGE = 1000;

const unquote = (etag) => (etag ?? "").replace(/^"|"$/g, "");

const RETAINED_RESPONSE = Symbol("retained store response");

function stored(response, size, body, finish = () => {}) {
  const etag = unquote(response.headers.get("etag"));
  let consumed = false;
  return {
    [RETAINED_RESPONSE]: response,
    size,
    etag,
    httpEtag: `"${etag}"`,
    version: response.headers.get("x-amz-version-id"),
    body,
    async text() {
      if (body === null) return "";
      if (consumed) throw new TypeError("object body already read");
      consumed = true;
      try { return await new Response(body).text(); } finally { finish(); }
    },
  };
}

function objectSize(response) {
  if (response.status === 206) {
    const total = /\/(\d+)$/.exec(response.headers.get("content-range") ?? "")?.[1];
    if (total === undefined) throw new Error("store range response has no total size");
    return Number(total);
  }
  const length = response.headers.get("content-length");
  if (length === null || !/^\d+$/.test(length)) throw new Error("store response has no content length");
  return Number(length);
}

async function discard(response) {
  await response.body?.cancel().catch(() => undefined);
}

async function headersWithin(run) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error("store response headers deadline")), HEADERS_DEADLINE_MS);
  try {
    return await run(controller.signal);
  } finally {
    clearTimeout(timer);
  }
}

export function s3Bucket(store, name, counters, { readDeadlineMs } = {}) {
  const request = (method, key, options = {}) => {
    counters?.s3Request(method);
    return storeRequest(store, method, name, key, options);
  };
  return {
    async get(key, options) {
      const headers = new Headers();
      const range = options?.range;
      if (range !== undefined) {
        if (!Number.isSafeInteger(range.offset) || !Number.isSafeInteger(range.length) || range.offset < 0 || range.length < 1) throw new RangeError("invalid range");
        headers.set("range", `bytes=${range.offset}-${range.offset + range.length - 1}`);
      }
      const controller = readDeadlineMs === undefined ? null : new AbortController();
      const timer = controller === null ? null : setTimeout(() => controller.abort(new Error("store read deadline")), readDeadlineMs);
      timer?.unref();
      const finish = () => { if (timer !== null) clearTimeout(timer); };
      let response;
      try { response = await headersWithin(signal => request("GET", key, { headers, signal: controller === null ? signal : AbortSignal.any([signal, controller.signal]) })); }
      catch (error) { finish(); throw error; }
      if (response.status === 404) {
        finish();
        await discard(response);
        return null;
      }
      if (range !== undefined ? response.status !== 206 : response.status !== 200 && response.status !== 206) {
        finish();
        await discard(response);
        throw new Error(`store GET answered ${response.status}`);
      }
      try { return stored(response, objectSize(response), response.body, finish); } catch (error) { finish(); throw error; }
    },
    async head(key) {
      const response = await headersWithin(signal => request("HEAD", key, { signal }));
      await discard(response);
      if (response.status === 404) return null;
      if (response.status !== 200) throw new Error(`store HEAD answered ${response.status}`);
      return stored(response, objectSize(response), null);
    },
    async put(key, value, options) {
      if (typeof value !== "string" && !(value instanceof Uint8Array)) throw new TypeError("native buckets accept string or byte bodies");
      const bytes = typeof value === "string" ? Buffer.from(value, "utf8") : value;
      const headers = new Headers({ "content-length": String(bytes.byteLength) });
      const onlyIf = options?.onlyIf;
      if (onlyIf !== undefined) {
        const names = Object.keys(onlyIf);
        if (names.length === 1 && onlyIf.etagDoesNotMatch === "*") headers.set("if-none-match", "*");
        else if (names.length === 1 && typeof onlyIf.etagMatches === "string" && onlyIf.etagMatches !== "") headers.set("if-match", `"${unquote(onlyIf.etagMatches)}"`);
        else throw new TypeError("unsupported conditional put");
      }
      const payload = createHash("sha256").update(bytes).digest("hex");
      const response = await headersWithin(signal => request("PUT", key, { headers, body: bytes, payload, signal }));
      await discard(response);
      if (response.status === 412 && onlyIf !== undefined) return null;
      if (response.status !== 200) throw new Error(`store PUT answered ${response.status}`);
      return stored(response, bytes.byteLength, null);
    },
    async list(options = {}) {
      const query = new URLSearchParams({ "list-type": "2", "max-keys": String(LIST_PAGE) });
      if (options.prefix) query.set("prefix", options.prefix);
      if (options.cursor) query.set("continuation-token", options.cursor);
      const deadline = readDeadlineMs === undefined ? null : AbortSignal.timeout(readDeadlineMs);
      const xml = await controlText(await headersWithin(signal => request("GET", "", { query, signal: deadline === null ? signal : AbortSignal.any([signal, deadline]) })));
      if (!/<ListBucketResult(?:\s|>)/.test(xml)) throw new Error("invalid object listing");
      const objects = [];
      for (const match of xml.matchAll(/<Contents>([\s\S]*?)<\/Contents>/g)) {
        const key = element(match[1], "Key");
        if (key === undefined) throw new Error("invalid listed object");
        objects.push({ key });
      }
      const truncated = element(xml, "IsTruncated");
      if (truncated === "false") return { objects, truncated: false };
      const cursor = element(xml, "NextContinuationToken");
      if (truncated !== "true" || !cursor) throw new Error("invalid listing pagination");
      return { objects, truncated: true, cursor };
    },
    async delete(key) {
      const response = await headersWithin(signal => request("DELETE", key, { signal }));
      await discard(response);
      if (response.status !== 204 && response.status !== 200 && response.status !== 404) throw new Error(`store DELETE answered ${response.status}`);
    },
  };
}

export function readOnly(bucket) {
  const refuse = async () => { throw new Error("read-only bucket"); };
  return Object.freeze({ get: bucket.get, head: bucket.head, list: bucket.list, put: refuse, delete: refuse });
}
