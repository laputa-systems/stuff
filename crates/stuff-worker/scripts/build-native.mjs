#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { cpSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { configuration } from "./orange.mjs";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const bundle = join(root, "build/orange/workers/default/bundle");
const output = join(root, "build/native/app");

execFileSync(process.execPath, [join(root, "scripts/build.mjs")], { cwd: root, stdio: "inherit" });
rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
for (const entry of readdirSync(bundle)) {
  if (entry.endsWith(".map")) continue;
  cpSync(join(bundle, entry), join(output, entry), { recursive: true, filter: source => !source.endsWith(".map") });
}
mkdirSync(join(output, "native"));
for (const name of readdirSync(join(root, "native"))) {
  if (name.endsWith(".mjs")) cpSync(join(root, "native", name), join(output, "native", name));
}
writeFileSync(join(output, "package.json"), `${JSON.stringify({ type: "module", private: true })}\n`);

const config = configuration();
const vars = { ...config.vars };
delete vars.STUFF_RELEASE;
vars.STUFF_S3_BUCKET_BINDINGS = JSON.stringify(Object.fromEntries(config.r2_buckets.map(({ binding, bucket_name }) => [binding, bucket_name])));
writeFileSync(join(output, "native/vars.json"), `${JSON.stringify(vars, null, 2)}\n`);

const files = [];
const walk = directory => {
  for (const name of readdirSync(directory).sort()) {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) walk(path);
    else files.push(path);
  }
};
walk(output);
const commit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
const dirty = execFileSync("git", ["status", "--porcelain", "--untracked-files=no"], { cwd: root, encoding: "utf8" }).trim() !== "";
const manifest = {
  schemaVersion: 1,
  sourceCommit: commit,
  sourceDirty: dirty,
  node: ">=26.13.1",
  files: files.map(path => ({ path: relative(output, path), sha256: createHash("sha256").update(readFileSync(path)).digest("hex") })),
};
writeFileSync(join(output, "native/artifact.json"), `${JSON.stringify(manifest, null, 2)}\n`);
const digest = createHash("sha256").update(readFileSync(join(output, "native/artifact.json"))).digest("hex");
console.log(JSON.stringify({ event: "native_artifact", output, sourceCommit: commit, sourceDirty: dirty, artifactSha256: digest, files: files.length }));
