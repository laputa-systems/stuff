import { registerHooks } from "node:module";
import { createServer } from "node:http";
import { createHash, timingSafeEqual } from "node:crypto";
import { mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { installDigestStream } from "./digest-stream.mjs";

registerHooks({
  load(url, context, next) {
    if (!url.endsWith(".wasm")) return next(url, context);
    return { format: "module", shortCircuit: true, source: `import { readFileSync } from "node:fs"; export default new WebAssembly.Module(readFileSync(new URL(${JSON.stringify(url)})));` };
  },
});
installDigestStream();

const { default: worker } = await import("../entry.js");
const { recordSample } = await import("../src/telemetry.js");
const { s3Bucket, readOnly } = await import("./bucket.mjs");
const { CoordinatorNamespace, REGISTRIES } = await import("./coordinators.mjs");
const { AuthorityConflict, AuthorityRecord, PUBLICATION_MODES } = await import("./authority.mjs");
const { createCounters } = await import("./counters.mjs");
const { isPublicationRequest, proxyTo, requestFrom, targetOf, writeResponse } = await import("./host.mjs");

class ConfigError extends Error { name = "ConfigError"; }

const ROLES = ["reader", "publisher"];
const PUBLICATION_RETRY_AFTER_S = 5;
const LOOPBACK = /^(127\.\d+\.\d+\.\d+|::1|localhost)$/;
const ARTIFACT = new URL("../", import.meta.url);

function address(name, value, { loopback = false } = {}) {
  const match = /^([0-9.]+|\[[0-9a-f:]+\]|localhost):(\d{1,5})$/i.exec(value ?? "");
  if (!match) throw new ConfigError(`${name} must be HOST:PORT`);
  const host = match[1].replace(/^\[|\]$/g, "");
  if (loopback && !LOOPBACK.test(host)) throw new ConfigError(`${name} must bind loopback`);
  return { host, port: Number(match[2]) };
}

function required(env, name) {
  const value = env[name];
  if (value === undefined || value === "") throw new ConfigError(`${name} is required`);
  return value;
}

function configuration(env) {
  if (env.STUFF_NATIVE_ENV_FILE) process.loadEnvFile(env.STUFF_NATIVE_ENV_FILE);
  const role = env.STUFF_NATIVE_ROLE;
  if (!ROLES.includes(role)) throw new ConfigError(`STUFF_NATIVE_ROLE must be one of ${ROLES.join(", ")}`);
  const vars = JSON.parse(readFileSync(env.STUFF_NATIVE_VARS_FILE ?? new URL("native/vars.json", ARTIFACT), "utf8"));
  const bindings = JSON.parse(required(vars, "STUFF_S3_BUCKET_BINDINGS"));
  const store = { S3_ENDPOINT: required(env, "S3_ENDPOINT"), S3_REGION: required(env, "S3_REGION"), S3_ACCESS_KEY_ID: required(env, "S3_ACCESS_KEY_ID"), S3_SECRET_ACCESS_KEY: required(env, "S3_SECRET_ACCESS_KEY") };
  const readStore = env.STUFF_NATIVE_READ_S3_ACCESS_KEY_ID ? { ...store, S3_ACCESS_KEY_ID: env.STUFF_NATIVE_READ_S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY: required(env, "STUFF_NATIVE_READ_S3_SECRET_ACCESS_KEY") } : store;
  const publishHost = env.STUFF_PUBLISH_HOST ?? vars.STUFF_PUBLISH_HOST;
  const telemetry = Object.fromEntries(["APPLICATION_EVENTS_ENDPOINT", "APPLICATION_EVENTS_SERVICE", "APPLICATION_EVENTS_TOKEN"].filter(name => env[name]).map(name => [name, env[name]]));
  const release = required(env, "STUFF_RELEASE");
  for (const name of ["STUFF_OCI_PUSH_TOKEN", "STUFF_OCI_PUSH_SECRET", "STUFF_OCI_WRITER_ORIGIN"]) delete vars[name];
  const config = {
    role, release, sourceCommit: env.STUFF_NATIVE_SOURCE_COMMIT ?? "unknown",
    listen: address("STUFF_NATIVE_LISTEN", env.STUFF_NATIVE_LISTEN),
    control: address("STUFF_NATIVE_CONTROL", env.STUFF_NATIVE_CONTROL, { loopback: true }),
    drainMs: Number(env.STUFF_NATIVE_DRAIN_S ?? "900") * 1000,
    vars: { ...vars, STUFF_RELEASE: release, ...(publishHost ? { STUFF_PUBLISH_HOST: publishHost } : {}) },
    bindings, store, readStore, publishHost, telemetry,
  };
  if (role === "reader" && env.STUFF_NATIVE_PUBLICATION_UPSTREAM) {
    if (!publishHost) throw new ConfigError("STUFF_PUBLISH_HOST is required to forward publication");
    if (!/^127\.0\.0\.1:\d{1,5}$/.test(env.STUFF_NATIVE_PUBLICATION_UPSTREAM)) throw new ConfigError("STUFF_NATIVE_PUBLICATION_UPSTREAM must be a loopback HOST:PORT");
    config.publicationUpstream = env.STUFF_NATIVE_PUBLICATION_UPSTREAM;
  }
  if (role === "publisher") {
    if (!publishHost) throw new ConfigError("STUFF_PUBLISH_HOST is required for the publisher role");
    config.state = required(env, "STUFF_NATIVE_STATE");
    config.controlToken = required(env, "STUFF_NATIVE_CONTROL_TOKEN");
    config.publication = { STUFF_COORDINATOR_TOKEN: required(env, "STUFF_COORDINATOR_TOKEN"), STUFF_S3_ACCESS_KEY_ID: required(env, "STUFF_S3_ACCESS_KEY_ID"), STUFF_S3_SECRET_ACCESS_KEY: required(env, "STUFF_S3_SECRET_ACCESS_KEY") };
  }
  return config;
}

function artifactDigest() {
  const manifest = readFileSync(new URL("native/artifact.json", ARTIFACT));
  return createHash("sha256").update(manifest).digest("hex");
}

function bucketsFor(config, store, counters, wrap) {
  return Object.fromEntries(Object.entries(config.bindings).map(([binding, name]) => [binding, wrap(s3Bucket(store, name, counters))]));
}

function tokenMatches(supplied, token) {
  const a = createHash("sha256").update(supplied ?? "").digest();
  const b = createHash("sha256").update(`Bearer ${token}`).digest();
  return timingSafeEqual(a, b);
}

function json(outgoing, status, value) {
  const body = JSON.stringify(value);
  outgoing.writeHead(status, { "content-type": "application/json", "cache-control": "no-store", "content-length": Buffer.byteLength(body) });
  outgoing.end(body);
}

async function readJson(incoming, limit) {
  let size = 0;
  const chunks = [];
  for await (const chunk of incoming) {
    size += chunk.length;
    if (size > limit) throw new RangeError("request too large");
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

async function main() {
  const config = configuration(process.env);
  const counters = createCounters();
  const startedAt = new Date().toISOString();
  const digest = artifactDigest();
  const readerEnv = Object.freeze({ ...config.vars, ...config.telemetry, STUFF_COORDINATOR_ENABLED: "false", ...bucketsFor(config, config.readStore, counters, readOnly) });
  let coordinators = null;
  let publisherEnv = null;
  let authority = null;
  let proxy = null;
  let legacyInFlight = 0;
  if (config.role === "publisher") {
    mkdirSync(config.state, { recursive: true, mode: 0o700 });
    authority = new AuthorityRecord(config.state);
    const storeEnv = { ...config.store, STUFF_S3_BUCKET_BINDINGS: config.vars.STUFF_S3_BUCKET_BINDINGS };
    const writable = bucketsFor(config, config.store, counters, bucket => bucket);
    coordinators = new CoordinatorNamespace({ directory: join(config.state, "coordinators"), env: { ...storeEnv, ...writable }, counters });
    coordinators.openAll();
    publisherEnv = Object.freeze({ ...config.vars, ...config.telemetry, ...storeEnv, ...config.publication, ...writable, STUFF_COORDINATOR_ENABLED: "true", COORDINATOR: coordinators });
  }
  const publicationProxy = config.publicationUpstream === undefined ? null : proxyTo(config.publicationUpstream);
  const pending = new Set();
  const context = { waitUntil(promise) { const tracked = Promise.resolve(promise).catch(() => undefined).finally(() => pending.delete(tracked)); pending.add(tracked); } };
  let draining = false;

  const server = createServer({ requestTimeout: 0, headersTimeout: 60_000, keepAliveTimeout: 65_000 }, async (incoming, outgoing) => {
    const started = performance.now();
    counters.requestStarted();
    let route = "read";
    outgoing.on("close", () => counters.requestFinished(route, outgoing.statusCode, performance.now() - started));
    if (draining) outgoing.shouldKeepAlive = false;
    const abort = new AbortController();
    outgoing.on("close", () => { if (!outgoing.writableFinished) abort.abort(new Error("client disconnected")); });
    try {
      const target = targetOf(incoming);
      if (target === null) { json(outgoing, 400, { error: "invalid host" }); return; }
      if (config.publishHost !== undefined && isPublicationRequest(target, config.publishHost)) {
        route = "publication";
        if (incoming.headers["x-oo-ingress"] !== "tailnet") { json(outgoing, 404, { error: "not found" }); return; }
        if (authority === null) {
          if (publicationProxy === null) { json(outgoing, 404, { error: "not found" }); return; }
          route = "publication-forward";
          await publicationProxy(incoming, outgoing);
          return;
        }
        const current = authority.value;
        if (current.publication === "legacy") {
          route = "publication-legacy";
          if (proxy?.upstream !== current.legacyUpstream) proxy = { upstream: current.legacyUpstream, forward: proxyTo(current.legacyUpstream) };
          legacyInFlight += 1;
          try { await proxy.forward(incoming, outgoing); } finally { legacyInFlight -= 1; }
          return;
        }
        const request = requestFrom(incoming, abort.signal);
        await writeResponse(outgoing, await worker.fetch(request, publisherEnv, context), request.method, counters);
        return;
      }
      const request = requestFrom(incoming, abort.signal);
      await writeResponse(outgoing, await worker.fetch(request, readerEnv, context), request.method, counters);
    } catch (error) {
      const target = targetOf(incoming);
      console.error(JSON.stringify({ event: "request_failed", at: new Date().toISOString(), route, method: incoming.method, host: target?.hostname ?? null, path: target?.pathname.slice(0, 256) ?? null, range: incoming.headers.range !== undefined, conditional: incoming.headers["if-none-match"] !== undefined || incoming.headers["if-modified-since"] !== undefined, name: error instanceof Error ? error.name : typeof error, message: error instanceof Error ? error.message.slice(0, 200) : "", stack: error instanceof Error ? (error.stack ?? "").split("\n").slice(1, 8).map(line => line.trim().replace(/\(file:\/\/[^)]*\/app\//, "(")) : [] }));
      if (!outgoing.headersSent) {
        if (route === "read") json(outgoing, 500, { error: "request failed" });
        else { outgoing.setHeader("retry-after", String(PUBLICATION_RETRY_AFTER_S)); json(outgoing, 503, { error: "publication temporarily unavailable" }); }
      }
      else outgoing.destroy();
    }
  });

  const identity = () => ({ schemaVersion: 1, role: config.role, publicationUpstream: config.publicationUpstream ?? null, release: config.release, sourceCommit: config.sourceCommit, artifactSha256: digest, node: process.version, pid: process.pid, startedAt, draining, authority: authority?.value ?? null, publishHost: config.publishHost ?? null });

  const control = createServer(async (incoming, outgoing) => {
    try {
      const url = new URL(incoming.url ?? "/", "http://control");
      if (incoming.method === "GET" && url.pathname === "/identity") return json(outgoing, 200, identity());
      if (incoming.method === "GET" && url.pathname === "/ready") return json(outgoing, draining ? 503 : 200, { ready: !draining, release: config.release, artifactSha256: digest });
      if (incoming.method === "GET" && url.pathname === "/metrics") return json(outgoing, 200, { identity: identity(), legacyInFlight, ...counters.snapshot() });
      if (config.role !== "publisher") return json(outgoing, 404, { error: "not found" });
      if (!tokenMatches(incoming.headers.authorization, config.controlToken)) return json(outgoing, 401, { error: "unauthorized" });
      if (incoming.method === "GET" && url.pathname === "/coordinators") return json(outgoing, 200, { authority: authority.value, legacyInFlight, coordinators: coordinators.inspect() });
      const coordinatorOp = /^\/coordinators\/([a-z]+)\/(import|dump)$/.exec(url.pathname);
      if (coordinatorOp && REGISTRIES.includes(coordinatorOp[1])) {
        const [, registry, op] = coordinatorOp;
        if (op === "import" && incoming.method === "POST") {
          if (authority.value.publication !== "legacy") return json(outgoing, 409, { error: "import requires legacy publication authority" });
          const body = await readJson(incoming, 8 * 1024 * 1024);
          const response = await coordinators.get(registry).fetch(new Request(`https://coordinator/${registry}/import`, { method: "POST", body: JSON.stringify(body) }));
          return json(outgoing, response.status, await response.json());
        }
        if (op === "dump" && incoming.method === "GET") return json(outgoing, 200, coordinators.dump(registry));
      }
      if (incoming.method === "POST" && url.pathname === "/authority") {
        const body = await readJson(incoming, 4096);
        if (!PUBLICATION_MODES.includes(body.publication) || typeof body.reason !== "string" || body.reason === "") return json(outgoing, 400, { error: "bad request" });
        if (legacyInFlight > 0) return json(outgoing, 409, { error: "legacy publication requests in flight", legacyInFlight });
        if (body.publication === "legacy" && coordinators.busy()) return json(outgoing, 409, { error: "native coordinator operations in flight" });
        try {
          const next = authority.change(body.expectedGeneration, { publication: body.publication, reason: body.reason, ...(body.publication === "legacy" ? { legacyUpstream: body.legacyUpstream } : {}) });
          console.log(JSON.stringify({ event: "authority_changed", generation: next.generation, publication: next.publication, reason: next.reason }));
          return json(outgoing, 200, next);
        } catch (error) {
          if (error instanceof AuthorityConflict) return json(outgoing, 409, { error: error.message });
          return json(outgoing, 400, { error: error instanceof Error ? error.message : "bad request" });
        }
      }
      return json(outgoing, 404, { error: "not found" });
    } catch (error) {
      if (!outgoing.headersSent) json(outgoing, 500, { error: error instanceof Error ? error.name : "error" });
    }
  });

  const SAMPLE_MS = 60_000;
  const instance = `native-${config.role}-${config.listen.port}`;
  const sampleEnv = config.role === "publisher" ? publisherEnv : readerEnv;
  let previous = counters.snapshot();
  const sum = (values) => Object.values(values ?? {}).reduce((total, value) => total + value, 0);
  const delta = (now, before) => Math.max(0, Math.round(now - before));
  const sampler = setInterval(() => {
    const now = counters.snapshot();
    const requests = now.http.requests;
    const errors = Object.entries(requests).filter(([key]) => key.endsWith(":5xx")).reduce((total, [, value]) => total + value, 0);
    const errorsBefore = Object.entries(previous.http.requests).filter(([key]) => key.endsWith(":5xx")).reduce((total, [, value]) => total + value, 0);
    recordSample(sampleEnv, "stuff.native.runtime", SAMPLE_MS, instance, {
      cpu_user_us: delta(now.process.userCpuUs, previous.process.userCpuUs),
      cpu_system_us: delta(now.process.systemCpuUs, previous.process.systemCpuUs),
      rss_kib: Math.round(now.process.rssBytes / 1024),
      heap_used_kib: Math.round(now.process.heapUsedBytes / 1024),
      loop_p99_us: Math.round(now.eventLoop.delayP99Ms * 1000),
      loop_max_us: Math.round(now.eventLoop.delayMaxMs * 1000),
      loop_utilization_permille: Math.round(now.eventLoop.utilizationSinceLastSnapshot * 1000),
      active_requests: now.http.activeRequests,
      active_streams: now.http.activeStreams,
      requests: delta(sum(requests), sum(previous.http.requests)),
      errors_5xx: delta(errors, errorsBefore),
      bytes_out_kib: delta(now.http.bytesOut / 1024, previous.http.bytesOut / 1024),
      s3_requests: delta(sum(now.s3.requests), sum(previous.s3.requests)),
      gc_pause_us: delta(sum(now.gc.pauseMs) * 1000, sum(previous.gc.pauseMs) * 1000),
      coordinator_ops: delta(now.coordinator.operationMs.count, previous.coordinator.operationMs.count),
      coordinator_wait_ms: delta(now.coordinator.admissionWaitMs.sumMs, previous.coordinator.admissionWaitMs.sumMs),
    });
    previous = now;
  }, SAMPLE_MS);
  sampler.unref();
  const listen = (target, where) => new Promise((resolve, reject) => {
    target.once("error", reject);
    target.listen(where.port, where.host, () => { target.off("error", reject); resolve(); });
  });
  await listen(control, config.control);
  await listen(server, config.listen);
  const bound = target => { const value = target.address(); return { host: value.address, port: value.port }; };
  console.log(JSON.stringify({ event: "listening", ...identity(), listen: bound(server), control: bound(control) }));

  const stop = async (signal) => {
    if (draining) return;
    draining = true;
    clearInterval(sampler);
    console.log(JSON.stringify({ event: "draining", signal, activeRequests: counters.activeRequests, activeStreams: counters.activeStreams }));
    const closed = new Promise(resolve => server.close(resolve));
    server.closeIdleConnections();
    const deadline = setTimeout(() => {
      console.error(JSON.stringify({ event: "drain_deadline", activeRequests: counters.activeRequests, activeStreams: counters.activeStreams }));
      server.closeAllConnections();
    }, config.drainMs);
    const idle = setInterval(() => server.closeIdleConnections(), 1000);
    await closed;
    clearTimeout(deadline);
    clearInterval(idle);
    let flushTimer;
    await Promise.race([Promise.allSettled(pending), new Promise(resolve => { flushTimer = setTimeout(resolve, 5000); })]);
    clearTimeout(flushTimer);
    await coordinators?.close();
    await new Promise(resolve => control.close(resolve));
    counters.close();
    console.log(JSON.stringify({ event: "stopped", signal }));
  };
  for (const signal of ["SIGTERM", "SIGINT", "SIGHUP"]) process.once(signal, () => { void stop(signal).then(() => { process.exitCode = 0; }, error => { console.error(JSON.stringify({ event: "stop_failed", name: error?.name })); process.exitCode = 1; }); });
}

try {
  await main();
} catch (error) {
  if (!(error instanceof ConfigError)) throw error;
  console.error(`stuff-native: ${error.message}`);
  process.exitCode = 2;
}
