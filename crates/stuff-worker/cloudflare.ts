// Cloudflare entrypoint for the read replica of the registries.
//
// Every registry hostname is attached to this Worker as a route, so a request
// arrives here before the tunnel. `fetch(request)` for a route's own hostname
// is a subrequest that reaches the tunnel origin (Caddy on the OpenOrange
// host) rather than this Worker again. The origin answers when it is healthy.
// Only a 5xx, a network error or a header timeout is served from the R2
// replica by the existing entry handler, which reads each bucket's `current`
// pointer because the coordinator is disabled for this Worker.
//
// The replica Worker runs with STUFF_COORDINATOR_ENABLED unset and declares no
// Durable Object, so no publication state exists on this side.
import handler from "./entry.ts";
import type { ExecutionContext } from "./src/runtime-types.js";
import { ORIGIN_HEADER_TIMEOUT_MS, planOriginAttempt, shouldServeReplica } from "./src/failover.js";

export const SERVED_BY_HEADER = "x-stuff-served-by";

type Env = Parameters<typeof handler.fetch>[1];

export interface FailoverOptions {
  /** Origin requester. Defaults to the runtime's global `fetch`. */
  origin?: (request: Request) => Promise<Response>;
  /** Header deadline before the replica answers. Defaults to the named constant. */
  headerTimeoutMs?: number;
}

type OriginAttempt =
  | { readonly kind: "response"; readonly response: Response }
  | { readonly kind: "error" }
  | { readonly kind: "timeout" };

/**
 * Fetch the origin and settle at response headers. The body keeps streaming
 * when the response is returned unchanged; when the replica takes over, the
 * origin body is cancelled rather than left unread.
 */
function attemptOrigin(
  request: Request,
  origin: (request: Request) => Promise<Response>,
  headerTimeoutMs: number,
): Promise<OriginAttempt> {
  // Settle through a promise so a synchronously-throwing origin is a network
  // error rather than an exception that escapes the handler.
  const pending = Promise.resolve().then(() => origin(request));
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      pending.then((response) => response.body?.cancel().catch(() => undefined)).catch(() => undefined);
      resolve({ kind: "timeout" });
    }, headerTimeoutMs);
    const settle = (result: OriginAttempt): void => {
      clearTimeout(timer);
      resolve(result);
    };
    pending.then(
      (response) => settle({ kind: "response", response }),
      () => settle({ kind: "error" }),
    );
  });
}

/**
 * Build the failover handler. The origin requester and header deadline are
 * injectable so the failover behavior can be exercised without a network;
 * the deployed Worker uses the defaults.
 */
export function createFailoverWorker(options: FailoverOptions = {}) {
  const origin = options.origin ?? ((request: Request) => fetch(request));
  const headerTimeoutMs = options.headerTimeoutMs ?? ORIGIN_HEADER_TIMEOUT_MS;
  return {
    async fetch(request: Request, env: Env, context: ExecutionContext): Promise<Response> {
      if (planOriginAttempt(request.method).kind === "pass_through") {
        return origin(request);
      }
      const attempt = await attemptOrigin(request, origin, headerTimeoutMs);
      if (attempt.kind === "response" && shouldServeReplica({ kind: "response", status: attempt.response.status }).kind === "origin") {
        return attempt.response;
      }
      if (attempt.kind === "response") {
        await attempt.response.body?.cancel().catch(() => undefined);
      }
      const replica = await handler.fetch(request, env, context);
      const headers = new Headers(replica.headers);
      headers.set(SERVED_BY_HEADER, "replica");
      return new Response(replica.body, { status: replica.status, statusText: replica.statusText, headers });
    },
  };
}

export default createFailoverWorker();
