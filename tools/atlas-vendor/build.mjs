import { createHash } from "node:crypto";
import { readFileSync, statSync, writeFileSync } from "node:fs";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const outfile = join(here, "..", "..", "repomod", "dependencies", "assets", "vendor", "atlas.vendor.js");
await build({
  entryPoints: [join(here, "entry.mjs")],
  bundle: true,
  minify: true,
  format: "iife",
  globalName: "AtlasVendor",
  outfile,
  legalComments: "none",
  logLevel: "info",
});
const bytes = readFileSync(outfile);
const sha256 = createHash("sha256").update(bytes).digest("hex");
console.log(`atlas.vendor.js ${statSync(outfile).size} bytes sha256 ${sha256}`);
