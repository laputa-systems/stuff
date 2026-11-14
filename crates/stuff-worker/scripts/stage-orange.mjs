import { cpSync, mkdirSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { generate, DEFAULT_WORKER_DIRECTORY } from "./orange.mjs";


export function stage(destination, release, { workerDirectory = DEFAULT_WORKER_DIRECTORY } = {}) {
  const bundle = join(workerDirectory, "bundle");
  const app = resolve(destination);
  mkdirSync(app, { recursive: true });
  const descriptor = join(app, "stuff.jsonc");
  const config = generate(descriptor, release, { workerDirectory });
  const main = relative(bundle, config.main);
  if (!main || main.startsWith("..") || resolve(bundle, main) !== config.main) throw new Error("worker main is outside bundle");
  cpSync(bundle, join(app, "bundle"), { recursive: true });
  config.main = `./bundle/${main}`;
  writeFileSync(descriptor, `${JSON.stringify(config, null, 2)}\n`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [destination, release] = process.argv.slice(2);
  if (!destination || !release) throw new Error("usage: node scripts/stage-orange.mjs APP RELEASE");
  stage(destination, release);
}
