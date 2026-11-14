import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
export const DEFAULT_WORKER_DIRECTORY = join(root, "build/orange/workers/default");
const keys = (value, allowed, context) => {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error(`invalid ${context}`);
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw new Error(`unmapped ${context} field: ${key}`);
};
export function configuration() {
  const config = JSON.parse(readFileSync(join(root, "orange.jsonc"), "utf8"));
  keys(config, ["name", "main", "no_bundle", "compatibility_date", "compatibility_flags", "vars", "r2_buckets", "durable_objects", "migrations"], "Orange configuration");
  if (config.name !== "stuff" || config.main !== "entry.ts" || config.no_bundle !== true) throw new Error("unsupported registry entry point");
  if (typeof config.compatibility_date !== "string" || !Array.isArray(config.compatibility_flags) || !config.compatibility_flags.every(flag => typeof flag === "string")) throw new Error("invalid compatibility configuration");
  if (config.vars === null || typeof config.vars !== "object" || Object.entries(config.vars).some(([key, value]) => !/^[A-Z_][A-Z0-9_]*$/.test(key) || typeof value !== "string")) throw new Error("invalid text bindings");
  if (!Array.isArray(config.r2_buckets) || !Array.isArray(config.durable_objects?.bindings) || !Array.isArray(config.migrations)) throw new Error("invalid storage bindings");
  keys(config.durable_objects, ["bindings"], "Durable Objects");
  for (const bucket of config.r2_buckets) {
    keys(bucket, ["binding", "bucket_name"], "bucket");
    if (typeof bucket.binding !== "string" || typeof bucket.bucket_name !== "string") throw new Error("invalid bucket binding");
  }
  const classes = [];
  for (const migration of config.migrations) {
    keys(migration, ["tag", "new_sqlite_classes"], "migration");
    if (typeof migration.tag !== "string" || !Array.isArray(migration.new_sqlite_classes) || !migration.new_sqlite_classes.every(name => typeof name === "string")) throw new Error("invalid migration");
    classes.push(...migration.new_sqlite_classes);
  }
  for (const binding of config.durable_objects.bindings) {
    keys(binding, ["name", "class_name"], "Durable Object binding");
    if (typeof binding.name !== "string" || !classes.includes(binding.class_name)) throw new Error("unmapped Durable Object class");
  }
  if (classes.some(name => !config.durable_objects.bindings.some(binding => binding.class_name === name))) throw new Error("unbound Durable Object class");
  return config;
}
export function generate(destination, release, { workerDirectory = DEFAULT_WORKER_DIRECTORY } = {}) {
  if (!release) throw new Error("expected a release label");
  const config = configuration();
  config.main = join(workerDirectory, "bundle/entry.js");
  config.vars.STUFF_S3_BUCKET_BINDINGS = JSON.stringify(Object.fromEntries(config.r2_buckets.map(({ binding, bucket_name }) => [binding, bucket_name])));
  config.vars.STUFF_RELEASE = release;
  writeFileSync(destination, `${JSON.stringify(config, null, 2)}\n`);
  return config;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [destination, release] = process.argv.slice(2);
  if (!destination) throw new Error("usage: node scripts/orange.mjs OUTPUT RELEASE");
  generate(resolve(destination), release);
}
