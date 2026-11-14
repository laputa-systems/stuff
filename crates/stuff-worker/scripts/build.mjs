#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { configuration, DEFAULT_WORKER_DIRECTORY } from "./orange.mjs";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const bin = (name) => join(root, "node_modules/.bin", name);
const workerDir = process.argv[2] === undefined ? DEFAULT_WORKER_DIRECTORY : resolve(process.argv[2]);
if (process.argv.length > 3 || !workerDir.endsWith("/workers/default")) throw new Error("expected an optional workers/default output directory");
const bundleDir = join(workerDir, "bundle");

const run = (command, args) =>
  execFileSync(command, args, { cwd: root, stdio: "inherit", env: process.env });

run("sh", ["scripts/build-wasm.sh"]);

rmSync(workerDir, { recursive: true, force: true });
run(bin("tsrs"), ["-p", "tsconfig.json", "--fast", "--outDir", bundleDir]);

for (const name of ["stuff_worker.js", "stuff_worker_bg.wasm"]) {
  const target = join(bundleDir, "build/wasm", name);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(join(root, "build/wasm", name), target);
}
for (const name of ["index.js", "protocol.js"]) {
  const destination = join(bundleDir, "vendor/stats-producer", name);
  mkdirSync(dirname(destination), { recursive: true });
  copyFileSync(join(root, "vendor/stats-producer", name), destination);
}

const manifest = {
  type: "complete",
  mainModule: "entry.js",
  modules: {
    "entry.js": { type: "esm" },
    "src/coordinator.js": { type: "esm" },
    "src/gateway.js": { type: "esm" },
    "src/sigv4.js": { type: "esm" },
    "src/s3.js": { type: "esm" },
    "src/telemetry.js": { type: "esm" },
    "vendor/stats-producer/index.js": { type: "esm" },
    "vendor/stats-producer/protocol.js": { type: "esm" },
    "build/wasm/stuff_worker.js": { type: "esm" },
    "build/wasm/stuff_worker_bg.wasm": { type: "wasm" },
  },
};
if (existsSync(join(bundleDir, "entry.js.map"))) {
  manifest.modules["entry.js.map"] = { type: "sourcemap" };
}

const config = configuration();
const env = Object.fromEntries(Object.entries(config.vars).map(([name, value]) => [name, { type: "text", value }]));
for (const { binding, bucket_name } of config.r2_buckets) env[binding] = { type: "r2", name: bucket_name };
for (const { name, class_name } of config.durable_objects.bindings) env[name] = { type: "durable-object", worker: config.name, exportName: class_name };
const classes = config.migrations.flatMap(migration => migration.new_sqlite_classes);
writeFileSync(join(workerDir, "worker.config.json"), JSON.stringify({
  name: config.name, compatibilityDate: config.compatibility_date, compatibilityFlags: config.compatibility_flags,
  env, exports: Object.fromEntries(classes.map(name => [name, { type: "durable-object", storage: "sqlite" }])), manifest,
}));

console.log(
  `built ${manifest.mainModule} (${statSync(join(bundleDir, "entry.js")).size} B), ` +
    `wasm (${statSync(join(bundleDir, "build/wasm/stuff_worker_bg.wasm")).size} B)`,
);
