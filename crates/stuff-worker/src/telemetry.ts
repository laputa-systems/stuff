import { createProducer, type Producer } from "../vendor/stats-producer/index.js";
interface Config {
  readonly APPLICATION_EVENTS_ENDPOINT?: string;
  readonly APPLICATION_EVENTS_SERVICE?: string;
  readonly APPLICATION_EVENTS_TOKEN?: string;
  readonly STUFF_RELEASE: string;
}
let configured: { key: string; token: string; producer: Producer } | undefined;
function producer(env: Config): Producer | null {
  if (!env.APPLICATION_EVENTS_ENDPOINT || !env.APPLICATION_EVENTS_SERVICE || !env.APPLICATION_EVENTS_TOKEN) return null;
  const key = JSON.stringify([env.APPLICATION_EVENTS_ENDPOINT, env.APPLICATION_EVENTS_SERVICE, env.STUFF_RELEASE]);
  if (configured?.key === key) { configured.token = env.APPLICATION_EVENTS_TOKEN; return configured.producer; }
  if (configured) void configured.producer.shutdown().catch(() => undefined);
  const state = { key, token: env.APPLICATION_EVENTS_TOKEN, producer: createProducer() };
  state.producer = createProducer({ endpoint: env.APPLICATION_EVENTS_ENDPOINT, service: env.APPLICATION_EVENTS_SERVICE, release: env.STUFF_RELEASE, token: () => state.token, queueLimit: 256, batchSize: 64, timeoutMs: 2000, maxRetries: 2 });
  configured = state;
  return state.producer;
}
export function requestOperation(req: Request): string {
  const path = new URL(req.url).pathname;
  const publication = /^\/_publication\/(cargo|npm|pypi|oci|mirror)\/(activate|rollback)$/.exec(path);
  if (req.method === "POST" && publication) return `registry.publication.attempt.${publication[1]}`;
  if (req.method === "PUT" && /^\/v2\/.+\/manifests\/[^/]+$/.test(path)) return "registry.publication.attempt.oci";
  return "registry.request";
}
export function recordOperation(env: Config, operation: string, durationMs: number, failure: unknown): void {
  try {
    producer(env)?.record({ operation, durationMs: Math.round(durationMs), outcome: failure === undefined ? "ok" : "error",
      ...(failure === undefined ? {} : { errorCode: "registry.request" }),
      ...(failure instanceof Error ? { diagnostics: { version: 1, name: "Error", message: "", frames: (failure.stack ?? "").split("\n").filter(line => /^\s*at /u.test(line)) } } : {}) });
  } catch { return; }
}
export async function flushOperations(): Promise<void> {
  try { await configured?.producer.flush(); } catch { return; }
}
