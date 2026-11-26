import { request as httpRequest, Agent } from "node:http";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

const HOP_BY_HOP = new Set(["connection", "keep-alive", "proxy-connection", "transfer-encoding", "upgrade", "te", "trailer"]);
const PUBLICATION_PATH = /^\/(?:_s3|_publication)(?:\/|$)/;

export function isPublicationRequest(url, publishHost) {
  return url.hostname === publishHost && PUBLICATION_PATH.test(url.pathname);
}

export function targetOf(incoming) {
  const host = incoming.headers.host;
  if (typeof host !== "string" || !/^[A-Za-z0-9.-]+(?::\d{1,5})?$/.test(host)) return null;
  const forwarded = incoming.headers["x-forwarded-proto"];
  const proto = (Array.isArray(forwarded) ? forwarded[0] : forwarded)?.split(",")[0]?.trim().toLowerCase();
  try { return new URL(`${proto === "https" ? "https" : "http"}://${host}${incoming.url ?? "/"}`); } catch { return null; }
}

export function requestFrom(incoming, signal) {
  const url = targetOf(incoming)?.href;
  if (url === undefined) throw new TypeError("invalid request target");
  const headers = new Headers();
  for (let index = 0; index + 1 < incoming.rawHeaders.length; index += 2) {
    const name = incoming.rawHeaders[index].toLowerCase();
    if (!HOP_BY_HOP.has(name)) headers.append(name, incoming.rawHeaders[index + 1]);
  }
  const method = incoming.method ?? "GET";
  if (method === "GET" || method === "HEAD") return new Request(url, { method, headers, signal });
  return new Request(url, { method, headers, signal, body: Readable.toWeb(incoming), duplex: "half" });
}

export async function writeResponse(outgoing, response, method, counters) {
  outgoing.statusCode = response.status;
  if (response.statusText !== "") outgoing.statusMessage = response.statusText;
  for (const [name, value] of response.headers) {
    if (name === "set-cookie" || HOP_BY_HOP.has(name)) continue;
    outgoing.setHeader(name, value);
  }
  if (response.body === null || method === "HEAD") {
    await response.body?.cancel().catch(() => undefined);
    outgoing.end();
    return;
  }
  const body = Readable.fromWeb(response.body);
  counters?.streamOpened();
  let bytes = 0;
  body.on("data", chunk => { bytes += chunk.length; });
  try {
    await pipeline(body, outgoing);
    counters?.streamClosed("complete", bytes);
  } catch (error) {
    counters?.streamClosed(outgoing.destroyed && !outgoing.writableFinished ? "cancelled" : "failed", bytes);
    throw error;
  }
}

export function proxyTo(upstream) {
  const [host, port] = upstream.split(":");
  const agent = new Agent({ keepAlive: true, maxSockets: 64 });
  return (incoming, outgoing) => new Promise((resolve, reject) => {
    const headers = {};
    for (let index = 0; index + 1 < incoming.rawHeaders.length; index += 2) {
      const name = incoming.rawHeaders[index];
      if (HOP_BY_HOP.has(name.toLowerCase())) continue;
      const existing = headers[name];
      headers[name] = existing === undefined ? incoming.rawHeaders[index + 1] : [].concat(existing, incoming.rawHeaders[index + 1]);
    }
    if (incoming.headers["transfer-encoding"] !== undefined && incoming.headers["content-length"] === undefined) headers["transfer-encoding"] = "chunked";
    const proxied = httpRequest({ host, port: Number(port), method: incoming.method, path: incoming.url, headers, agent }, upstreamResponse => {
      const responseHeaders = {};
      for (let index = 0; index + 1 < upstreamResponse.rawHeaders.length; index += 2) {
        const name = upstreamResponse.rawHeaders[index];
        if (!HOP_BY_HOP.has(name.toLowerCase())) responseHeaders[name] = [].concat(responseHeaders[name] ?? [], upstreamResponse.rawHeaders[index + 1]);
      }
      outgoing.writeHead(upstreamResponse.statusCode ?? 502, upstreamResponse.statusMessage, responseHeaders);
      pipeline(upstreamResponse, outgoing).then(resolve, reject);
    });
    proxied.on("error", reject);
    outgoing.on("close", () => { if (!outgoing.writableFinished) proxied.destroy(); });
    pipeline(incoming, proxied).catch(reject);
  });
}
