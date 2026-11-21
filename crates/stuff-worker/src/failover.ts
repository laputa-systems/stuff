// Failover policy for the replica Worker. The decision is kept separate from
// the network so it can be tested without workerd.

/** How long the origin may take to return response headers before the replica answers. */
export const ORIGIN_HEADER_TIMEOUT_MS = 8000;

export type OriginOutcome =
  | { readonly kind: "response"; readonly status: number }
  | { readonly kind: "error" }
  | { readonly kind: "timeout" };

/**
 * Only safe, idempotent reads may fail over. A non-GET/HEAD request is never
 * forwarded and never replayed against the replica, so a rejected write can
 * never be applied twice.
 */
export function isFailoverMethod(method: string): boolean {
  return method === "GET" || method === "HEAD";
}

export type OriginAttempt =
  | { readonly kind: "origin" }
  | { readonly kind: "pass_through" };

/**
 * Decide whether the request is forwarded to the origin. Non-GET/HEAD requests
 * pass through unchanged so the origin owns them and the replica never serves
 * or replays them.
 */
export function planOriginAttempt(method: string): OriginAttempt {
  return isFailoverMethod(method) ? { kind: "origin" } : { kind: "pass_through" };
}

export type FailoverDecision =
  | { readonly kind: "origin" }
  | { readonly kind: "replica"; readonly reason: "status" | "error" | "timeout" };

/**
 * Decide who answers once an origin attempt finished. Any origin status below
 * 500 (including 304 and 404) is authoritative and returned unchanged; a 5xx,
 * a thrown network error or a header timeout is served from the replica.
 */
export function shouldServeReplica(outcome: OriginOutcome): FailoverDecision {
  switch (outcome.kind) {
    case "response":
      return outcome.status >= 500 ? { kind: "replica", reason: "status" } : { kind: "origin" };
    case "error":
      return { kind: "replica", reason: "error" };
    case "timeout":
      return { kind: "replica", reason: "timeout" };
  }
}
