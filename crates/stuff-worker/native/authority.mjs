import { closeSync, fsyncSync, openSync, readFileSync, renameSync, writeFileSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";

export const PUBLICATION_MODES = Object.freeze(["legacy", "native"]);

export class AuthorityConflict extends Error {
  name = "AuthorityConflict";
}

function validate(value) {
  if (!value || typeof value !== "object" || value.schemaVersion !== 1) throw new Error("invalid authority record");
  if (!Number.isSafeInteger(value.generation) || value.generation < 1) throw new Error("invalid authority generation");
  if (!PUBLICATION_MODES.includes(value.publication)) throw new Error("invalid publication authority");
  if (value.publication === "legacy" && !/^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$/.test(value.legacyUpstream ?? "")) throw new Error("legacy authority needs an IPv4:port upstream");
  if (typeof value.changedAt !== "string" || typeof value.reason !== "string") throw new Error("invalid authority record metadata");
  return Object.freeze({ schemaVersion: 1, generation: value.generation, publication: value.publication, ...(value.publication === "legacy" ? { legacyUpstream: value.legacyUpstream } : {}), changedAt: value.changedAt, reason: value.reason });
}

function durableWrite(path, text) {
  const temporary = `${path}.tmp-${process.pid}`;
  try {
    writeFileSync(temporary, text, { mode: 0o600 });
    const file = openSync(temporary, "r");
    try { fsyncSync(file); } finally { closeSync(file); }
    renameSync(temporary, path);
    const directory = openSync(dirname(path), "r");
    try { fsyncSync(directory); } finally { closeSync(directory); }
  } catch (error) {
    rmSync(temporary, { force: true });
    throw error;
  }
}

export class AuthorityRecord {
  #path;
  #value;
  constructor(stateDirectory) {
    this.#path = join(stateDirectory, "authority.json");
    this.#value = validate(JSON.parse(readFileSync(this.#path, "utf8")));
  }
  static initialize(stateDirectory, initial) {
    const path = join(stateDirectory, "authority.json");
    const value = validate({ schemaVersion: 1, generation: 1, changedAt: new Date().toISOString(), ...initial });
    let file;
    try { file = openSync(path, "wx", 0o600); }
    catch (error) { if (error.code === "EEXIST") throw new AuthorityConflict("authority record already exists"); throw error; }
    closeSync(file);
    durableWrite(path, `${JSON.stringify(value)}\n`);
    return value;
  }
  get value() { return this.#value; }
  change(expectedGeneration, next) {
    if (expectedGeneration !== this.#value.generation) throw new AuthorityConflict(`authority generation is ${this.#value.generation}`);
    const value = validate({ schemaVersion: 1, generation: this.#value.generation + 1, changedAt: new Date().toISOString(), ...next });
    durableWrite(this.#path, `${JSON.stringify(value)}\n`);
    this.#value = value;
    return value;
  }
}
