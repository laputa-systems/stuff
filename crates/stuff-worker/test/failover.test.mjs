import assert from "node:assert/strict";
import test from "node:test";
import { buildFailoverBundle, harness, originAttempts } from "./failover-harness.mjs";
import {
  catalog,
  seed,
  seedOci,
  OCI_LAYER,
} from "./fixtures.mjs";

buildFailoverBundle();

const NPM_DIGEST = "a".repeat(128);

const ORIGIN_UP = 'return new Response("origin-body", { status: 200, headers: { etag: \'"origin-etag"\', "x-origin": "yes" } });';
const ORIGIN_ERROR = 'throw new Error("origin unreachable");';
const ORIGIN_TIMEOUT = "await new Promise(() => {});";

function originStatus(status) {
  // A 304 must not carry a body; the origin's null-body answer is returned as-is.
  const body = status === 304 ? "null" : '"origin-error-body"';
  return `return new Response(${body}, { status: ${status} });`;
}

// The registry paths whose failover the brief requires. Each case is a URL on a
// replica host and the bytes the seeded replica generation holds for it.
async function seedRegistry(server) {
  await seed(server);
  await seedOci(server);
  const env = await server.getWorker().getEnv();
  const cargo = env.MYCRATES;
  await cargo.put("blobs/crate-1.0.0.crate", "crate-bytes");
  await cargo.put(
    "generations/g1/registry/config.json",
    '{"dl":"https://crates.test/blobs/crate-1.0.0.crate"}',
  );
  const npm = env.MYNPM;
  // The tarball alias is `<name>/-/<sha512>.tgz`; the packument names the digest.
  await npm.put(
    "generations/g1/package",
    JSON.stringify({
      name: "package",
      versions: {
        "1.0.0": { dist: { tarball: `https://npm.test/package/-/${NPM_DIGEST}.tgz` } },
      },
    }),
  );
  await npm.put(`tarballs/${NPM_DIGEST}.tgz`, "tarball-bytes");
  const pypi = env.PYPI;
  await pypi.put("wheels/wheelpkg-1.0-py3-none-any.whl", "wheel-bytes");
  await pypi.put(
    "generations/g1/simple/wheelpkg/index.html",
    '<a href="../../wheels/wheelpkg-1.0-py3-none-any.whl">wheel</a>',
  );
  const mirror = env.MIRROR;
  await mirror.put("generations/g1/tool-1.0.tar.xz", "mirror-bytes");
  await mirror.put("generations/g1/catalog.json", catalog("mirror", "tool-1.0"));
}

const REGISTRY_CASES = [
  { url: "https://crates.test/current/registry/config.json", body: '{"dl":"https://crates.test/blobs/crate-1.0.0.crate"}' },
  { url: "https://crates.test/blobs/crate-1.0.0.crate", body: "crate-bytes" },
  { url: "https://npm.test/current/package", matches: /"name":"package"/ },
  { url: `https://npm.test/current/-/tarballs/${NPM_DIGEST}.tgz`, body: "tarball-bytes" },
  { url: "https://pypi.test/current/simple/wheelpkg/", matches: /wheelpkg-1\.0-py3-none-any\.whl/ },
  { url: "https://pypi.test/wheels/wheelpkg-1.0-py3-none-any.whl", body: "wheel-bytes" },
  { url: "https://mirror.test/current/tool-1.0.tar.xz", body: "mirror-bytes" },
  { url: `https://oci-blobs.test/sha256/${OCI_LAYER.slice("sha256:".length)}`, bytes: true },
];

async function assertReplicaServed(server) {
  await seedRegistry(server);
  assert.equal(REGISTRY_CASES.length, 8, "eight registry paths are covered");
  for (const entry of REGISTRY_CASES) {
    await originAttempts(server);
    const response = await server.getWorker().fetch(entry.url);
    assert.equal(response.headers.get("x-stuff-served-by"), "replica", `${entry.url} is served by the replica`);
    assert.equal(await originAttempts(server), 1, `${entry.url} was forwarded to the origin exactly once`);
    assert.equal(response.status, 200, `${entry.url} answered ${response.status}`);
    if (entry.body !== undefined) {
      assert.equal(await response.text(), entry.body, entry.url);
    } else if (entry.matches !== undefined) {
      assert.match(await response.text(), entry.matches, entry.url);
    } else if (entry.bytes) {
      assert.ok((await response.arrayBuffer()).byteLength > 0, `${entry.url} has a body`);
    }
  }
}

test("a healthy origin answer below 500 is returned unchanged and the replica is not read", async (t) => {
  // No R2 binding at all: any replica read would throw instead of answering.
  const server = await harness(t, ORIGIN_UP, { r2: false });
  for (const method of ["GET", "HEAD"]) {
    await originAttempts(server);
    const response = await server.getWorker().fetch("https://crates.test/catalog.json", { method });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("x-stuff-served-by"), null, "the origin answer is not tagged");
    assert.equal(response.headers.get("x-origin"), "yes");
    assert.equal(response.headers.get("etag"), '"origin-etag"');
    if (method === "GET") assert.equal(await response.text(), "origin-body");
    assert.equal(await originAttempts(server), 1, `${method} reached the origin exactly once`);
  }
});

test("304 and 404 from the origin are returned unchanged and the replica is not read", async (t) => {
  for (const status of [304, 404]) {
    const server = await harness(t, originStatus(status), { r2: false });
    const response = await server.getWorker().fetch("https://crates.test/catalog.json");
    assert.equal(response.status, status, `${status} passes through`);
    assert.equal(response.headers.get("x-stuff-served-by"), null, `${status} is not tagged`);
    assert.equal(await originAttempts(server), 1);
  }
});

for (const status of [500, 502, 503, 530]) {
  test(`an origin ${status} serves every registry path from the replica`, async (t) => {
    const server = await harness(t, originStatus(status));
    await assertReplicaServed(server);
  });
}

test("a thrown network error serves every registry path from the replica", async (t) => {
  const server = await harness(t, ORIGIN_ERROR);
  await assertReplicaServed(server);
});

test("an origin that never returns headers serves every registry path from the replica after the timeout", async (t) => {
  const server = await harness(t, ORIGIN_TIMEOUT);
  await assertReplicaServed(server);
});

test("an object the replica lacks answers a retryable 503, not 404, when the origin fails", async (t) => {
  const server = await harness(t, originStatus(502));
  await seedRegistry(server);
  const response = await server.getWorker().fetch("https://pypi.test/wheels/absent-1.0-py3-none-any.whl");
  assert.equal(response.status, 503);
  assert.equal(response.headers.get("x-stuff-served-by"), "replica");
  assert.equal(response.headers.get("retry-after"), "5");
  assert.equal(response.headers.get("cache-control"), "no-store");
  await response.arrayBuffer();
});

test("an origin 404 stays authoritative and is not turned into a 503", async (t) => {
  const server = await harness(t, originStatus(404));
  const response = await server.getWorker().fetch("https://pypi.test/wheels/absent-1.0-py3-none-any.whl");
  assert.equal(response.status, 404);
  assert.equal(response.headers.get("x-stuff-served-by"), null);
  await response.arrayBuffer();
});

test("a non-GET/HEAD request is never failed over and never reaches the replica", async (t) => {
  const server = await harness(t, originStatus(503), { r2: false });
  const response = await server.getWorker().fetch("https://crates.test/catalog.json", {
    method: "POST",
    body: "x",
  });
  assert.equal(response.status, 503, "the origin answer is returned as-is for a write");
  assert.equal(response.headers.get("x-stuff-served-by"), null, "a write is never tagged as replica");
  assert.equal(await originAttempts(server), 1, "a write is forwarded to the origin exactly once");
});

test("the replica reads current from the bucket and never the coordinator", async (t) => {
  const server = await harness(t, originStatus(503));
  await seed(server);
  const env = await server.getWorker().getEnv();
  assert.equal(env.COORDINATOR, undefined, "the replica declares no coordinator");
  assert.notEqual(env.STUFF_COORDINATOR_ENABLED, "true", "the replica runs with the coordinator disabled");
  const before = await server.getWorker().fetch("https://crates.test/catalog.json");
  assert.match(await before.text(), /"registry":"cargo"/);
  // Moving the pointer changes what the replica answers, which proves the read
  // goes through the bucket's `current` object.
  await env.MYCRATES.put("current", "g2");
  await env.MYCRATES.put(
    "generations/g2/catalog.json",
    JSON.stringify({ schema_version: 1, registry: "cargo", generation: "g2", packages: [] }),
  );
  const after = await server.getWorker().fetch("https://crates.test/catalog.json");
  assert.match(await after.text(), /"generation":"g2"/);
});
