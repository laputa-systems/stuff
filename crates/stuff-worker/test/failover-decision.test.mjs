import assert from "node:assert/strict";
import test from "node:test";
import { buildFailoverBundle, decisionModule } from "./failover-harness.mjs";

buildFailoverBundle();

test("a status below 500 is the origin's answer", async () => {
  const { shouldServeReplica } = await decisionModule();
  for (const status of [200, 206, 304, 404, 499]) {
    assert.deepEqual(shouldServeReplica({ kind: "response", status }), { kind: "origin" }, `${status}`);
  }
});

test("a status of 500 or above is served from the replica", async () => {
  const { shouldServeReplica } = await decisionModule();
  for (const status of [500, 502, 503, 530]) {
    assert.deepEqual(
      shouldServeReplica({ kind: "response", status }),
      { kind: "replica", reason: "status" },
      `${status}`,
    );
  }
});

test("a thrown network error and a header timeout are served from the replica", async () => {
  const { shouldServeReplica } = await decisionModule();
  assert.deepEqual(shouldServeReplica({ kind: "error" }), { kind: "replica", reason: "error" });
  assert.deepEqual(shouldServeReplica({ kind: "timeout" }), { kind: "replica", reason: "timeout" });
});

test("only GET and HEAD are eligible to fail over", async () => {
  const { isFailoverMethod, planOriginAttempt } = await decisionModule();
  for (const method of ["GET", "HEAD"]) {
    assert.equal(isFailoverMethod(method), true, method);
    assert.deepEqual(planOriginAttempt(method), { kind: "origin" }, method);
  }
  for (const method of ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"]) {
    assert.equal(isFailoverMethod(method), false, method);
    assert.deepEqual(planOriginAttempt(method), { kind: "pass_through" }, method);
  }
});

test("the header deadline is a named constant", async () => {
  const { ORIGIN_HEADER_TIMEOUT_MS } = await decisionModule();
  assert.equal(ORIGIN_HEADER_TIMEOUT_MS, 8000);
});
