#!/bin/sh
# Deploy the stuff-failover Worker from crates/stuff-worker/cloudflare.config.ts.
#
# cf picks its bundler from the package it runs in. crates/stuff-worker lists
# vite (for the search bundle), so `cf deploy` there runs `vite build` and finds
# no entry. This stages a package that lists only cf and wrangler, reuses the
# Worker's installed node_modules, and points the committed config at the
# Worker's cloudflare.ts, so cf builds with Wrangler.
#
# Usage: deploy/failover-deploy.sh [--dry-run] [--message TEXT]
# Requires: `pnpm install --frozen-lockfile` and the WASM build in
# crates/stuff-worker (node scripts/build.mjs), and a cf login.
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)
WORKER=$ROOT/crates/stuff-worker
[ -d "$WORKER/node_modules" ] || { echo "failover-deploy: run pnpm install --frozen-lockfile in $WORKER first" >&2; exit 2; }
[ -f "$WORKER/build/wasm/stuff_worker_bg.wasm" ] || { echo "failover-deploy: build the WASM first (node scripts/build.mjs in $WORKER)" >&2; exit 2; }
STAGE=$ROOT/.work/failover-deploy
rm -rf "$STAGE"
mkdir -p "$STAGE"
cf=$(cd "$WORKER" && node -p 'require("./package.json").devDependencies.cf')
wrangler=$(cd "$WORKER" && node -p 'require("./package.json").devDependencies.wrangler')
printf '{"name":"stuff-failover-deploy","private":true,"type":"module","devDependencies":{"cf":"%s","wrangler":"%s"}}\n' "$cf" "$wrangler" > "$STAGE/package.json"
ln -s "$WORKER/node_modules" "$STAGE/node_modules"
sed 's#"\./cloudflare\.ts"#"../../crates/stuff-worker/cloudflare.ts"#' "$WORKER/cloudflare.config.ts" > "$STAGE/cloudflare.config.ts"
grep -q '"../../crates/stuff-worker/cloudflare.ts"' "$STAGE/cloudflare.config.ts" || { echo "failover-deploy: could not retarget the config entrypoint" >&2; exit 1; }
cd "$STAGE"
exec "$WORKER/node_modules/.bin/cf" deploy "$@"
