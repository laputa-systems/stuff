#!/bin/sh
set -eu
[ "$(node --version)" = "v$NODE_VERSION" ]
npm install -g /work/pnpm.tgz
cd /work/closure
pnpm install --frozen-lockfile --prod --ignore-scripts --store-dir /work/store
