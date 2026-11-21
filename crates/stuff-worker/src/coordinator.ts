import { objectVersions, storeBucket, storeRequest, type StoreEnv } from "./s3.js";

interface ObjectHead { size: number; etag: string; text(): Promise<string> }
interface Bucket {
  get(key: string): Promise<ObjectHead | null>;
  head(key: string): Promise<ObjectHead | null>;
  put(key: string, value: string): Promise<unknown>;
  list(options: { prefix: string; cursor?: string }): Promise<{ objects: { key: string }[]; truncated: boolean; cursor?: string }>;
  delete(key: string): Promise<void>;
}
interface SQL { exec<T = Record<string, unknown>>(query: string, ...bindings: (string | number | null)[]): Iterable<T> }
interface State { storage: { sql: SQL; transactionSync<T>(fn: () => T): T; sync(): Promise<void> }; blockConcurrencyWhile<T>(fn: () => Promise<T>): Promise<T> }
interface Env extends StoreEnv { MYCRATES: Bucket; MYNPM: Bucket; PYPI: Bucket; OCI: Bucket; OCI_BLOBS: Bucket; MIRROR: Bucket }
type Current = { revision: number; generation: string | null; manifest: string | null; pending: number };
type Lease = { kind: string; token: string; expires: number };
type Receipt = { payload: string; revision: number; generation: string; manifest: string };
type ReceiptRow = Receipt & { key: string };
type ExportData = { schemaVersion: 1; registry: string; current: Current; receipts: ReceiptRow[]; retired_generations: string[]; retired_versions: { key: string; version_id: string }[] };
const bindings: Record<string, "MYCRATES" | "MYNPM" | "PYPI" | "OCI" | "MIRROR"> = { cargo: "MYCRATES", npm: "MYNPM", pypi: "PYPI", oci: "OCI", mirror: "MIRROR" };
const validGeneration = (value: unknown): value is string => typeof value === "string" && /^[a-zA-Z0-9_-]{1,128}$/.test(value);
const validToken = (value: unknown): value is string => typeof value === "string" && /^[a-zA-Z0-9_-]{1,128}$/.test(value);
const response = (status: number, value: unknown): Response => Response.json(value, { status, headers: { "cache-control": "no-store" } });
const frozenResponse = (): Response => new Response(JSON.stringify({ error: "frozen" }), { status: 503, headers: { "cache-control": "no-store", "retry-after": "30" } });
const nonEmptyText = (value: unknown, limit: number): value is string => typeof value === "string" && value.length > 0 && value.length <= limit;
function importedData(registry: string, body: Record<string, unknown>): ExportData | undefined {
  if (body.schemaVersion !== 1 || body.registry !== registry) return undefined;
  const receiptsValue = body.receipts;
  const generationsValue = body.retired_generations;
  const versionsValue = body.retired_versions;
  if (!Array.isArray(receiptsValue) || !Array.isArray(generationsValue) || !Array.isArray(versionsValue)) return undefined;
  const current = body.current;
  if (!current || typeof current !== "object" || Array.isArray(current)) return undefined;
  const c = current as Record<string, unknown>;
  if (!Number.isSafeInteger(c.revision) || (c.revision as number) < 0) return undefined;
  if (!(c.generation === null || validGeneration(c.generation))) return undefined;
  if (!(c.manifest === null || (typeof c.manifest === "string" && /^[0-9a-f]{64}$/.test(c.manifest)))) return undefined;
  if (!(c.pending === 0 || c.pending === 1) || (c.generation === null) !== (c.manifest === null)) return undefined;
  const receipts: ReceiptRow[] = [];
  for (const item of receiptsValue) {
    if (!item || typeof item !== "object" || Array.isArray(item)) return undefined;
    const row = item as Record<string, unknown>;
    if (!validToken(row.key) || typeof row.payload !== "string" || !Number.isSafeInteger(row.revision) || (row.revision as number) < 0 || !validGeneration(row.generation) || typeof row.manifest !== "string" || !/^[0-9a-f]{64}$/.test(row.manifest)) return undefined;
    receipts.push({ key: row.key, payload: row.payload, revision: row.revision as number, generation: row.generation, manifest: row.manifest });
  }
  const retired_generations: string[] = [];
  for (const item of generationsValue) {
    if (!validGeneration(item)) return undefined;
    retired_generations.push(item);
  }
  const retired_versions: { key: string; version_id: string }[] = [];
  for (const item of versionsValue) {
    if (!item || typeof item !== "object" || Array.isArray(item)) return undefined;
    const row = item as Record<string, unknown>;
    if (!nonEmptyText(row.key, 1024) || !nonEmptyText(row.version_id, 1024)) return undefined;
    retired_versions.push({ key: row.key, version_id: row.version_id });
  }
  return { schemaVersion: 1, registry, current: { revision: c.revision as number, generation: c.generation as string | null, manifest: c.manifest as string | null, pending: c.pending as number }, receipts, retired_generations, retired_versions };
}
async function hash(value: string): Promise<string> {
  const bytes = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}
async function everyObject<T>(items: readonly T[], check: (item: T) => Promise<boolean>): Promise<boolean> {
  let next = 0;
  let valid = true;
  let unavailable = false;
  await Promise.all(Array.from({ length: Math.min(32, items.length) }, async () => {
    while (valid && !unavailable) {
      const index = next++;
      if (index >= items.length) return;
      try { if (!await check(items[index]!)) valid = false; }
      catch { unavailable = true; }
    }
  }));
  if (unavailable) throw new Error("object verification unavailable");
  return valid;
}
export class PublicationCoordinator {
  private readonly state: State;
  private readonly env: Env;
  constructor(state: State, env: Env) {
    this.state = state;
    this.env = env;
    const sql = state.storage.sql;
    sql.exec("CREATE TABLE IF NOT EXISTS current (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, generation TEXT, manifest TEXT, pending INTEGER NOT NULL)");
    sql.exec("CREATE TABLE IF NOT EXISTS lease (id INTEGER PRIMARY KEY CHECK(id=1), kind TEXT NOT NULL, token TEXT NOT NULL, expires INTEGER NOT NULL)");
    sql.exec("CREATE TABLE IF NOT EXISTS receipts (key TEXT PRIMARY KEY, payload TEXT NOT NULL, revision INTEGER NOT NULL, generation TEXT NOT NULL, manifest TEXT NOT NULL)");
    sql.exec("CREATE TABLE IF NOT EXISTS retired_generations (generation TEXT PRIMARY KEY)");
    sql.exec("CREATE TABLE IF NOT EXISTS retired_versions (key TEXT NOT NULL, version_id TEXT NOT NULL, PRIMARY KEY(key, version_id))");
    sql.exec("CREATE TABLE IF NOT EXISTS frozen (id INTEGER PRIMARY KEY CHECK(id=1), value INTEGER NOT NULL)");
  }
  private one<T>(query: string, ...args: (string | number | null)[]): T | undefined { return Array.from(this.state.storage.sql.exec<T>(query, ...args))[0]; }
  private isFrozen(): boolean { return this.one<{ value: number }>("SELECT value FROM frozen WHERE id=1")?.value === 1; }
  private setFrozen(value: boolean): void { this.state.storage.sql.exec("INSERT INTO frozen VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET value=excluded.value", value ? 1 : 0); }
  private hasData(): boolean {
    return !!this.one("SELECT id FROM current WHERE id=1")
      || !!this.one("SELECT id FROM lease WHERE id=1")
      || !!this.one("SELECT key FROM receipts LIMIT 1")
      || !!this.one("SELECT generation FROM retired_generations LIMIT 1")
      || !!this.one("SELECT key FROM retired_versions LIMIT 1");
  }
  private async manifest(store: Bucket, generation: string): Promise<{ identity: string; objects: { key: string; size: number; etag: string }[] }> {
    const object = await store.get(`manifests/${generation}.json`);
    if (!object) throw new Error("manifest missing");
    const text = await object.text();
    const value: unknown = JSON.parse(text);
    if (!value || typeof value !== "object" || !("schemaVersion" in value) || value.schemaVersion !== 1 || !("objects" in value) || !Array.isArray(value.objects)) throw new Error("invalid manifest");
    const objects: { key: string; size: number; etag: string }[] = [];
    for (const item of value.objects as unknown[]) {
      if (!item || typeof item !== "object" || !("key" in item) || typeof item.key !== "string" || (item.key.startsWith("/") || Array.from(item.key).some((c) => c.charCodeAt(0) < 32)) || item.key.split("/").some((part) => !part || part === "." || part === "..") || !("size" in item) || !Number.isSafeInteger(item.size) || (item.size as number) < 0 || !("etag" in item) || typeof item.etag !== "string" || !item.etag) throw new Error("invalid manifest object");
      objects.push({ key: item.key, size: item.size as number, etag: item.etag });
    }
    return { identity: await hash(text), objects };
  }
  private async current(store: Bucket): Promise<Current> {
    let row = this.one<Current>("SELECT revision, generation, manifest, pending FROM current WHERE id=1");
    if (!row) {
      const marker = await store.get("current");
      const generation = marker ? (await marker.text()).trim() : null;
      if (generation !== null && !validGeneration(generation)) throw new Error("invalid current");
      const manifest = generation === null ? null : (await this.manifest(store, generation)).identity;
      this.state.storage.sql.exec("INSERT INTO current VALUES (1, 0, ?, ?, 0)", generation, manifest);
      row = { revision: 0, generation, manifest, pending: 0 };
    }
    const projected = await store.get("current");
    const projectedGeneration = projected ? (await projected.text()).trim() : null;
    if (row.pending || projectedGeneration !== row.generation) {
      if (row.generation === null) throw new Error("invalid projection");
      if (projectedGeneration !== row.generation) await store.put("current", row.generation);
      this.state.storage.sql.exec("UPDATE current SET pending=0 WHERE id=1 AND revision=?", row.revision);
      row.pending = 0;
    }
    return row;
  }
  private lease(kind: string, token: unknown): boolean {
    const lease = this.one<Lease>("SELECT kind, token, expires FROM lease WHERE id=1");
    return validToken(token) && lease?.kind === kind && lease.token === token && lease.expires > Date.now();
  }
  private async versionAvailable(binding: string, key: string): Promise<boolean> {
    if (!this.one("SELECT version_id FROM retired_versions WHERE key=? LIMIT 1", key)) return true;
    const head = await storeRequest(this.env, "HEAD", storeBucket(this.env, binding), key);
    if (head.status === 404) return false;
    if (!head.ok) throw new Error("store version check failed");
    const version = head.headers.get("x-amz-version-id") ?? "null";
    return !this.one("SELECT version_id FROM retired_versions WHERE key=? AND version_id=?", key, version);
  }
  private async deleteVersions(binding: string, key: string, token: unknown): Promise<boolean> {
    const bucket = storeBucket(this.env, binding);
    const versions = await objectVersions(this.env, bucket, key);
    if (!this.lease("gc", token)) return false;
    this.state.storage.transactionSync(() => {
      for (const version of versions) this.state.storage.sql.exec("INSERT INTO retired_versions VALUES (?, ?) ON CONFLICT(key, version_id) DO NOTHING", key, version);
    });
    await this.state.storage.sync();
    for (const version of versions) {
      if (!this.lease("gc", token)) return false;
      const deleted = await storeRequest(this.env, "DELETE", bucket, key, { query: new URLSearchParams({ versionId: version }) });
      await deleted.body?.cancel();
      if (!deleted.ok && deleted.status !== 404) throw new Error("store version deletion failed");
    }
    return true;
  }
  private async references(store: Bucket, blobInventory: boolean, key: string): Promise<boolean> {
    let cursor: string | undefined;
    const pages = new Set<string>();
    do {
      const listed = await store.list({ prefix: "manifests/", ...(cursor ? { cursor } : {}) });
      for (const object of listed.objects) {
        const match = /^manifests\/([a-zA-Z0-9_-]{1,128})\.json$/.exec(object.key);
        if (!match) throw new Error("invalid manifest key");
        const manifest = await this.manifest(store, match[1]!);
        if (!blobInventory) {
          if (manifest.objects.some(item => item.key === key)) return true;
        } else {
          const inventory = await store.get(`generations/${match[1]}/blobs.json`);
          if (!inventory) throw new Error("OCI blob inventory missing");
          const value = JSON.parse(await inventory.text()) as { schemaVersion?: unknown; blobs?: unknown };
          if (value.schemaVersion !== 1 || !Array.isArray(value.blobs) || value.blobs.some(blob => typeof blob !== "string" || !/^sha256:[0-9a-f]{64}$/.test(blob))) throw new Error("invalid OCI blob inventory");
          if (value.blobs.includes(`sha256:${key.slice(7)}`)) return true;
        }
      }
      cursor = listed.truncated ? listed.cursor : undefined;
      if (listed.truncated && (!cursor || pages.has(cursor))) throw new Error("invalid manifest cursor");
      if (cursor) pages.add(cursor);
    } while (cursor);
    return false;
  }
  async fetch(req: Request): Promise<Response> {
    return this.state.blockConcurrencyWhile(async () => {
      try { return await this.handle(req); } catch { return response(503, { error: "coordinator operation failed" }); }
    });
  }
  private async handle(req: Request): Promise<Response> {
    const [, registry, op] = new URL(req.url).pathname.split("/");
    const binding = registry ? bindings[registry] : undefined;
    if (!binding || !op) return response(404, { error: "not found" });
    const store = this.env[binding];
    const sql = this.state.storage.sql;
    const frozen = this.isFrozen();
    if (op === "current" && req.method === "GET") return response(200, await this.current(store));
    if (op === "export" && req.method === "GET") {
      if (!frozen) return response(409, { error: "not frozen" });
      const existing = this.one<Lease>("SELECT kind, token, expires FROM lease WHERE id=1");
      if (existing && existing.expires > Date.now()) return response(409, { error: "lease held" });
      return response(200, {
        schemaVersion: 1,
        registry,
        current: this.one<Current>("SELECT revision, generation, manifest, pending FROM current WHERE id=1") ?? await this.current(store),
        receipts: Array.from(sql.exec<ReceiptRow>("SELECT key, payload, revision, generation, manifest FROM receipts ORDER BY key")),
        retired_generations: Array.from(sql.exec<{ generation: string }>("SELECT generation FROM retired_generations ORDER BY generation"), row => row.generation),
        retired_versions: Array.from(sql.exec<{ key: string; version_id: string }>("SELECT key, version_id FROM retired_versions ORDER BY key, version_id")),
      });
    }
    if (op === "freeze" && req.method === "POST") {
      this.setFrozen(true);
      const existing = this.one<Lease>("SELECT kind, token, expires FROM lease WHERE id=1");
      return response(200, { current: await this.current(store), liveLease: !!existing && existing.expires > Date.now() });
    }
    if (op === "thaw" && req.method === "POST") {
      this.setFrozen(false);
      return response(200, { frozen: false });
    }
    if (req.method !== "POST") return response(405, { error: "method not allowed" });
    const limit = op === "import" ? 8 * 1024 * 1024 : 16384;
    const length = Number(req.headers.get("content-length") ?? "0");
    if (!Number.isFinite(length) || length > limit) return response(413, { error: "too large" });
    const text = await req.text();
    if (text.length > limit) return response(413, { error: "too large" });
    const body: Record<string, unknown> = text === "" ? {} : JSON.parse(text) as Record<string, unknown>;
    if (!body || typeof body !== "object" || Array.isArray(body)) return response(400, { error: "bad request" });
    if (op === "import") {
      if (this.hasData()) return response(409, { error: "coordinator not empty" });
      const data = importedData(registry, body);
      if (!data) return response(400, { error: "bad request" });
      this.state.storage.transactionSync(() => {
        sql.exec("INSERT INTO current VALUES (1, ?, ?, ?, ?)", data.current.revision, data.current.generation, data.current.manifest, data.current.pending);
        for (const row of data.receipts) sql.exec("INSERT INTO receipts VALUES (?, ?, ?, ?, ?)", row.key, row.payload, row.revision, row.generation, row.manifest);
        for (const generation of data.retired_generations) sql.exec("INSERT INTO retired_generations VALUES (?)", generation);
        for (const row of data.retired_versions) sql.exec("INSERT INTO retired_versions VALUES (?, ?)", row.key, row.version_id);
        this.setFrozen(true);
      });
      return response(200, { imported: true });
    }
    if (op === "gateway-lease") {
      if (!this.lease("upload", body.token)) return response(409, { error: "stale lease" });
      if (body.generation !== undefined && (!validGeneration(body.generation) || this.one("SELECT generation FROM retired_generations WHERE generation=?", body.generation))) return response(409, { error: "retired generation" });
      return response(200, { ok: true });
    }
    if (op === "begin" || op === "gc-claim") {
      if (frozen) return frozenResponse();
      const existing = this.one<Lease>("SELECT kind, token, expires FROM lease WHERE id=1");
      if (existing && existing.expires > Date.now()) return response(409, { error: "lease held" });
      const token = crypto.randomUUID();
      const expires = Date.now() + 300000;
      sql.exec("INSERT OR REPLACE INTO lease VALUES (1, ?, ?, ?)", op === "begin" ? "upload" : "gc", token, expires);
      return response(200, { token, expires, revision: (await this.current(store)).revision });
    }
    if (op === "renew" || op === "abort") {
      if (!this.lease("upload", body.token) && !this.lease("gc", body.token)) return response(409, { error: "stale lease" });
      if (op === "abort") sql.exec("DELETE FROM lease WHERE id=1");
      else sql.exec("UPDATE lease SET expires=? WHERE id=1", Date.now() + 300000);
      return response(200, { ok: true });
    }
    if (op === "activate" || op === "rollback") {
      if (!validToken(body.key) || !validGeneration(body.generation) || typeof body.manifest !== "string" || !/^[0-9a-f]{64}$/.test(body.manifest) || !Number.isSafeInteger(body.expectedRevision)) return response(400, { error: "bad request" });
      const payload = JSON.stringify([op, body.generation, body.manifest, body.expectedRevision]);
      const receipt = this.one<Receipt>("SELECT payload, revision, generation, manifest FROM receipts WHERE key=?", body.key);
      if (receipt) return receipt.payload === payload ? response(200, { revision: receipt.revision, generation: receipt.generation, manifest: receipt.manifest }) : response(409, { error: "idempotency conflict" });
      if (!this.lease("upload", body.token)) return response(409, { error: "stale lease" });
      const current = await this.current(store);
      if (current.revision !== body.expectedRevision) return response(409, { error: "revision conflict" });
      const manifest = await this.manifest(store, body.generation);
      if (manifest.identity !== body.manifest) return response(409, { error: "manifest conflict" });
      const retired = new Set(Array.from(sql.exec<{ generation: string }>("SELECT generation FROM retired_generations"), row => row.generation));
      if (retired.has(body.generation) || manifest.objects.some(item =>
        (item.key.startsWith("generations/") && retired.has(item.key.split("/")[1]!)) ||
        (item.key.startsWith("manifests/") && retired.has(item.key.slice("manifests/".length).replace(/\.json$/, "")))))
        return response(409, { error: "generation permanently retired by garbage collection" });
      if (!await everyObject(manifest.objects, async item => {
        const found = await store.head(item.key);
        return found !== null && found.size === item.size && found.etag.replaceAll('"', "") === item.etag.replaceAll('"', "") && await this.versionAvailable(binding, item.key);
      })) return response(409, { error: "incomplete generation" });
      if (registry === "oci") {
        const object = await store.get(`generations/${body.generation}/blobs.json`);
        if (!object) return response(409, { error: "OCI blob inventory missing" });
        const inventory = JSON.parse(await object.text()) as { schemaVersion?: unknown; blobs?: unknown };
        if (inventory.schemaVersion !== 1 || !Array.isArray(inventory.blobs)) return response(409, { error: "invalid OCI blob inventory" });
        if (!await everyObject(inventory.blobs as unknown[], async blob =>
          typeof blob === "string" && /^sha256:[0-9a-f]{64}$/.test(blob) && await this.env.OCI_BLOBS.head(`sha256/${blob.slice(7)}`) !== null && await this.versionAvailable("OCI_BLOBS", `sha256/${blob.slice(7)}`)))
          return response(409, { error: "OCI blob missing or invalid" });
      }
      if (!this.lease("upload", body.token)) return response(409, { error: "stale lease" });
      const revision = current.revision + 1;
      this.state.storage.transactionSync(() => {
        sql.exec("UPDATE current SET revision=?, generation=?, manifest=?, pending=1 WHERE id=1", revision, body.generation as string, body.manifest as string);
        sql.exec("INSERT INTO receipts VALUES (?, ?, ?, ?, ?)", body.key as string, payload, revision, body.generation as string, body.manifest as string);
        sql.exec("DELETE FROM lease WHERE id=1");
      });
      await this.state.storage.sync();
      await this.current(store);
      return response(200, { revision, generation: body.generation, manifest: body.manifest });
    }
    if (op === "gc-object") {
      if (!this.lease("gc", body.token)) return response(409, { error: "stale lease" });
      const key = body.key;
      const prefix = { cargo: "blobs/", npm: "tarballs/", pypi: "wheels/" }[registry!];
      const ociKey = registry === "oci" && typeof key === "string" && /^(?:oci\/manifests\/)?sha256\/[0-9a-f]{64}$/.test(key);
      if (typeof key !== "string" || !(ociKey || (prefix !== undefined && key.startsWith(prefix) && key.length > prefix.length)) || key.length > 1024 || key.split("/").some(part => !part || part === "." || part === "..") || Array.from(key).some(char => char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127)) return response(400, { error: "invalid shared object" });
      const blobInventory = registry === "oci" && key.startsWith("sha256/");
      if (await this.references(store, blobInventory, key)) return response(409, { error: "referenced object" });
      if (!await this.deleteVersions(blobInventory ? "OCI_BLOBS" : binding, key, body.token)) return response(409, { error: "stale lease" });
      return response(200, { deleted: 1 });
    }
    if (op === "gc-delete") {
      if (!this.lease("gc", body.token)) return response(409, { error: "stale lease" });
      const current = await this.current(store);
      if (!validGeneration(body.generation) || body.generation === current.generation) return response(409, { error: "invalid generation" });
      const prefix = `generations/${body.generation}/`;
      let cursor: string | undefined;
      const keys: string[] = [];
      do {
        const listed = await store.list({ prefix, ...(cursor ? { cursor } : {}) });
        keys.push(...listed.objects.map((object) => object.key));
        cursor = listed.truncated ? listed.cursor : undefined;
        if (listed.truncated && !cursor) throw new Error("missing cursor");
      } while (cursor);
      const deleting = new Set(keys);
      cursor = undefined;
      do {
        const listed = await store.list({ prefix: "manifests/", ...(cursor ? { cursor } : {}) });
        for (const object of listed.objects) {
          const match = /^manifests\/([a-zA-Z0-9_-]{1,128})\.json$/.exec(object.key);
          if (!match) throw new Error("invalid manifest key");
          if (match[1] !== body.generation) {
            const retained = await this.manifest(store, match[1]!);
            if (retained.objects.some((item) => deleting.has(item.key))) return response(409, { error: "referenced generation" });
          }
        }
        cursor = listed.truncated ? listed.cursor : undefined;
        if (listed.truncated && !cursor) throw new Error("missing cursor");
      } while (cursor);
      const manifestKey = `manifests/${body.generation}.json`;
      if (await store.head(manifestKey) !== null) keys.push(manifestKey);
      if (!this.lease("gc", body.token)) return response(409, { error: "stale lease" });
      sql.exec("INSERT INTO retired_generations VALUES (?) ON CONFLICT(generation) DO NOTHING", body.generation);
      await this.state.storage.sync();
      const batch = keys.slice(0, 32);
      for (const key of batch) {
        if (!this.lease("gc", body.token)) return response(409, { error: "stale lease" });
        if (this.env.S3_ENDPOINT) {
          if (!await this.deleteVersions(binding, key, body.token)) return response(409, { error: "stale lease" });
        } else await store.delete(key);
      }
      return response(200, { deleted: batch.length, complete: batch.length === keys.length });
    }
    return response(404, { error: "not found" });
  }
}
