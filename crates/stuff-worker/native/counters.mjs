import { monitorEventLoopDelay, performance, PerformanceObserver } from "node:perf_hooks";
import { readdirSync } from "node:fs";

const BUCKETS_MS = [1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000];

function histogram() {
  const counts = Array.from({ length: BUCKETS_MS.length + 1 }, () => 0);
  let sum = 0;
  let count = 0;
  return {
    observe(ms) {
      let index = BUCKETS_MS.findIndex(bound => ms <= bound);
      if (index === -1) index = BUCKETS_MS.length;
      counts[index] += 1;
      sum += ms;
      count += 1;
    },
    snapshot: () => ({ boundsMs: BUCKETS_MS, counts: [...counts], count, sumMs: Math.round(sum * 1000) / 1000 }),
  };
}

function tally() {
  const values = new Map();
  return { add(key, amount = 1) { values.set(key, (values.get(key) ?? 0) + amount); }, snapshot: () => Object.fromEntries(values) };
}

export function createCounters() {
  const startedAt = Date.now();
  const delay = monitorEventLoopDelay({ resolution: 10 });
  delay.enable();
  let metricElu = performance.eventLoopUtilization();
  let sampleElu = metricElu;
  const gc = tally();
  const gcPause = tally();
  const observer = new PerformanceObserver(list => {
    for (const entry of list.getEntries()) {
      const kind = String(entry.detail?.kind ?? "unknown");
      gc.add(kind);
      gcPause.add(kind, entry.duration);
    }
  });
  observer.observe({ entryTypes: ["gc"] });
  const requests = tally();
  const requestLatency = histogram();
  const s3 = tally();
  const streams = tally();
  const admissions = tally();
  const sqlFailures = tally();
  const sqlElapsed = { statement: histogram(), transaction: histogram() };
  const coordinatorOps = histogram();
  const admissionWait = histogram();
  let activeRequests = 0;
  let activeStreams = 0;
  let bytesOut = 0;
  const registry = {
    sql(kind, ms) { sqlElapsed[kind]?.observe(ms); },
    sqlFailure(kind, error) { sqlFailures.add(`${kind}:${error?.errcode === 5 ? "busy" : error?.errcode === 6 ? "locked" : "error"}`); },
    admission(outcome, waitedMs) { admissions.add(outcome); if (waitedMs !== undefined) admissionWait.observe(waitedMs); },
    operation(ms) { coordinatorOps.observe(ms); },
  };
  return {
    s3Request(method) { s3.add(method); },
    requestStarted() { activeRequests += 1; },
    requestFinished(route, status, ms) { activeRequests -= 1; requests.add(`${route}:${Math.floor(status / 100)}xx`); requestLatency.observe(ms); },
    streamOpened() { activeStreams += 1; },
    streamClosed(outcome, bytes) { activeStreams -= 1; streams.add(outcome); bytesOut += bytes; },
    forRegistry: () => registry,
    get activeRequests() { return activeRequests; },
    get activeStreams() { return activeStreams; },
    snapshot({ sample = false } = {}) {
      const usage = process.resourceUsage();
      const memory = process.memoryUsage();
      const now = performance.eventLoopUtilization();
      const utilization = performance.eventLoopUtilization(now, sample ? sampleElu : metricElu).utilization;
      let fds = null;
      try { fds = readdirSync("/proc/self/fd").length; } catch { fds = null; }
      const result = {
        startedAt: new Date(startedAt).toISOString(),
        process: { userCpuUs: usage.userCPUTime, systemCpuUs: usage.systemCPUTime, rssBytes: memory.rss, heapUsedBytes: memory.heapUsed, heapTotalBytes: memory.heapTotal, externalBytes: memory.external, arrayBuffersBytes: memory.arrayBuffers, openFds: fds, fsReads: usage.fsRead, fsWrites: usage.fsWrite },
        eventLoop: { delayP50Ms: delay.percentile(50) / 1e6, delayP99Ms: delay.percentile(99) / 1e6, delayMaxMs: delay.max / 1e6, utilizationSinceLastSnapshot: utilization },
        gc: { counts: gc.snapshot(), pauseMs: gcPause.snapshot() },
        http: { activeRequests, activeStreams, bytesOut, requests: requests.snapshot(), latencyMs: requestLatency.snapshot(), streams: streams.snapshot() },
        s3: { requests: s3.snapshot() },
        coordinator: { admissions: admissions.snapshot(), admissionWaitMs: admissionWait.snapshot(), operationMs: coordinatorOps.snapshot(), sqlStatementMs: sqlElapsed.statement.snapshot(), sqlTransactionMs: sqlElapsed.transaction.snapshot(), sqlFailures: sqlFailures.snapshot() },
      };
      if (sample) { sampleElu = now; delay.reset(); }
      else metricElu = now;
      return result;
    },
    close() { observer.disconnect(); delay.disable(); },
  };
}
