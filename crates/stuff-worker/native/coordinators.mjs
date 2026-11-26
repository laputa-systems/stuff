import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { PublicationCoordinator } from "../src/coordinator.js";

export const REGISTRIES = Object.freeze(["cargo", "npm", "pypi", "oci", "mirror"]);
const QUEUE_LIMIT = 256;
const ADMISSION_DEADLINE_MS = 20_000;
const BUSY_RETRY_AFTER_S = 5;

export class CoordinatorBusy extends Error {
  name = "CoordinatorBusy";
}

export function openCoordinatorDatabase(path) {
  const db = new DatabaseSync(path);
  try {
    const mode = db.prepare("PRAGMA journal_mode=WAL").get()?.journal_mode;
    if (mode !== "wal") throw new Error(`coordinator database refused WAL (${mode})`);
    db.exec("PRAGMA synchronous=FULL");
    db.exec("PRAGMA locking_mode=EXCLUSIVE");
    db.exec("BEGIN IMMEDIATE; COMMIT");
  } catch (error) {
    db.close();
    if (error instanceof Error && "errcode" in error && (error.errcode === 5 || error.errcode === 6)) throw new Error(`coordinator database ${path} is held by another process`);
    throw error;
  }
  return db;
}

function sqlStorage(db, counters) {
  const statements = new Map();
  const prepared = (query) => {
    let statement = statements.get(query);
    if (statement === undefined) {
      statement = db.prepare(query);
      statements.set(query, statement);
    }
    return statement;
  };
  const timed = (kind, run) => {
    const started = performance.now();
    try {
      return run();
    } catch (error) {
      counters?.sqlFailure(kind, error);
      throw error;
    } finally {
      counters?.sql(kind, performance.now() - started);
    }
  };
  return {
    sql: {
      exec(query, ...bindings) {
        return timed("statement", () => {
          const statement = prepared(query);
          if (statement.columns().length > 0) return statement.all(...bindings);
          statement.run(...bindings);
          return [];
        });
      },
    },
    transactionSync(run) {
      return timed("transaction", () => {
        db.exec("BEGIN IMMEDIATE");
        try {
          const result = run();
          db.exec("COMMIT");
          return result;
        } catch (error) {
          if (db.isTransaction) db.exec("ROLLBACK");
          throw error;
        }
      });
    },
    async sync() {
      if (db.isTransaction) throw new Error("coordinator sync inside an open transaction");
    },
  };
}

class Serializer {
  #tail = Promise.resolve();
  #waiting = 0;
  #active = null;
  #counters;
  constructor(counters) { this.#counters = counters; }
  get waiting() { return this.#waiting; }
  get active() { return this.#active; }
  get idle() { return this.#tail; }
  run(run, signal) {
    if (this.#waiting >= QUEUE_LIMIT) {
      this.#counters?.admission("queue_full");
      return Promise.reject(new CoordinatorBusy("coordinator queue is full"));
    }
    this.#waiting += 1;
    const queued = performance.now();
    const previous = this.#tail;
    let release;
    this.#tail = new Promise(resolve => { release = resolve; });
    return previous.then(async () => {
      this.#waiting -= 1;
      const waited = performance.now() - queued;
      try {
        if (signal?.aborted) {
          this.#counters?.admission("cancelled");
          throw new CoordinatorBusy("coordinator request cancelled before admission");
        }
        if (waited > ADMISSION_DEADLINE_MS) {
          this.#counters?.admission("deadline");
          throw new CoordinatorBusy("coordinator admission deadline passed");
        }
        this.#counters?.admission("admitted", waited);
        this.#active = { since: Date.now() };
        const started = performance.now();
        try {
          return await run();
        } finally {
          this.#active = null;
          this.#counters?.operation(performance.now() - started);
        }
      } finally {
        release();
      }
    });
  }
}

export class CoordinatorNamespace {
  #directory;
  #env;
  #counters;
  #instances = new Map();
  #closed = false;
  constructor({ directory, env, counters }) {
    mkdirSync(directory, { recursive: true, mode: 0o700 });
    this.#directory = directory;
    this.#env = env;
    this.#counters = counters;
  }
  openAll() {
    for (const name of REGISTRIES) this.#instance(name);
  }
  idFromName(name) {
    if (!REGISTRIES.includes(name)) throw new RangeError("unknown coordinator registry");
    return name;
  }
  get(name) {
    return { fetch: request => this.#fetch(name, request) };
  }
  #instance(name) {
    if (this.#closed) throw new Error("coordinators are closed");
    let instance = this.#instances.get(name);
    if (instance === undefined) {
      const db = openCoordinatorDatabase(join(this.#directory, `${name}.sqlite`));
      const serializer = new Serializer(this.#counters?.forRegistry(name));
      const storage = sqlStorage(db, this.#counters?.forRegistry(name));
      let currentSignal;
      const state = { storage, blockConcurrencyWhile: run => serializer.run(run, currentSignal) };
      const coordinator = new PublicationCoordinator(state, this.#env);
      instance = { db, serializer, coordinator, setSignal: signal => { currentSignal = signal; } };
      this.#instances.set(name, instance);
    }
    return instance;
  }
  async #fetch(name, request) {
    const instance = this.#instance(this.idFromName(name));
    instance.setSignal(request.signal);
    try {
      return await instance.coordinator.fetch(request);
    } catch (error) {
      if (!(error instanceof CoordinatorBusy)) throw error;
      return Response.json({ error: "coordinator busy" }, { status: 503, headers: { "cache-control": "no-store", "retry-after": String(BUSY_RETRY_AFTER_S) } });
    }
  }
  busy() {
    return [...this.#instances.values()].some(instance => instance.serializer.waiting > 0 || instance.serializer.active !== null);
  }
  dump(name) {
    const { db } = this.#instance(this.idFromName(name));
    const current = db.prepare("SELECT revision, generation, manifest, pending FROM current WHERE id=1").get() ?? null;
    return {
      schemaVersion: 1,
      registry: name,
      current: current === null ? null : { revision: current.revision, generation: current.generation, manifest: current.manifest, pending: current.pending },
      receipts: db.prepare("SELECT key, payload, revision, generation, manifest FROM receipts ORDER BY key").all().map(row => ({ key: row.key, payload: row.payload, revision: row.revision, generation: row.generation, manifest: row.manifest })),
      retired_generations: db.prepare("SELECT generation FROM retired_generations ORDER BY generation").all().map(row => row.generation),
      retired_versions: db.prepare("SELECT key, version_id FROM retired_versions ORDER BY key, version_id").all().map(row => ({ key: row.key, version_id: row.version_id })),
      frozen: db.prepare("SELECT value FROM frozen WHERE id=1").get()?.value === 1,
      lease: db.prepare("SELECT kind, expires FROM lease WHERE id=1").get() ?? null,
    };
  }
  inspect() {
    const result = {};
    for (const name of REGISTRIES) {
      const instance = this.#instances.get(name);
      if (instance === undefined) { result[name] = { opened: false }; continue; }
      result[name] = { opened: true, ...inspectDatabase(instance.db), waiting: instance.serializer.waiting, active: instance.serializer.active };
    }
    return result;
  }
  async close() {
    this.#closed = true;
    for (const instance of this.#instances.values()) await instance.serializer.idle;
    for (const instance of this.#instances.values()) instance.db.close();
    this.#instances.clear();
  }
}

export function inspectDatabase(db) {
  const tables = new Set(db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all().map(row => row.name));
  const one = (table, query) => tables.has(table) ? db.prepare(query).get() ?? null : null;
  const count = (table) => tables.has(table) ? db.prepare(`SELECT count(*) AS n FROM ${table}`).get().n : 0;
  const lease = one("lease", "SELECT kind, expires FROM lease WHERE id=1");
  return {
    current: one("current", "SELECT revision, generation, manifest, pending FROM current WHERE id=1"),
    frozen: one("frozen", "SELECT value FROM frozen WHERE id=1")?.value === 1,
    lease: lease === null ? null : { kind: lease.kind, expires: lease.expires, live: lease.expires > Date.now() },
    receipts: count("receipts"),
    retiredGenerations: count("retired_generations"),
    retiredVersions: count("retired_versions"),
  };
}
