#!/bin/sh
set -eu
[ "$(node --version)" = "v$NODE_VERSION" ]
mkdir -p /work/home /work/tools
npm install -g --prefix /work/tools /work/pnpm.tgz
export PATH=/work/tools/bin:$PATH
cd /work/closure
pnpm install --frozen-lockfile --prod --ignore-scripts --store-dir /work/store
