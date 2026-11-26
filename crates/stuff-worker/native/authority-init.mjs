import { mkdirSync } from "node:fs";
import { AuthorityRecord } from "./authority.mjs";

const [state, publication, upstream] = process.argv.slice(2);
if (!state || !publication) {
  console.error("usage: authority-init.mjs STATE_DIR legacy|native [LEGACY_IPV4:PORT]");
  process.exit(2);
}
mkdirSync(state, { recursive: true, mode: 0o700 });
const value = AuthorityRecord.initialize(state, { publication, reason: "initialized", ...(publication === "legacy" ? { legacyUpstream: upstream } : {}) });
console.log(JSON.stringify(value));
