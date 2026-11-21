#!/bin/sh
# Copy the six registry buckets from the OpenOrange store to the R2 replica.
#
# The failover Worker (crates/stuff-worker/cloudflare.ts) answers from this
# replica when the origin does not, so the replica must hold a generation
# before its `current` pointer names it. `store-copy.py sync` copies the
# shared stores and the current generation, verifies them, and writes `current` last; it never
# deletes at the destination, so the previously published generation stays
# readable while a newer one copies.
#
# Source credentials are the store's S3 user and destination credentials are
# the R2 replica token; both come from the root-only
# /etc/openorange/replica-sync.env. Neither is ever printed.
#
# Usage: replica-sync.sh [--interval SECONDS] [BUCKET...]
#   Without --interval the buckets are synced once.
#   With --interval the run repeats forever, which is how oo-replica-sync
#   drives the 5-minute cadence.
# Exit codes: 0 every bucket synced, 1 at least one bucket failed.
set -eu

HERE=$(CDPATH='' cd -- "$(dirname "$0")" && pwd)
ENV_FILE=${REPLICA_SYNC_ENV:-/etc/openorange/replica-sync.env}
LEDGER_DIR=${REPLICA_SYNC_LEDGER_DIR:-/var/lib/openorange/replica-sync}
STORE_COPY=${STORE_COPY:-$HERE/store-copy.py}
DEFAULT_BUCKETS="stuff-mycrates stuff-mynpm stuff-mypypi stuff-oci stuff-mirror stuff-oci-blobs"

fail() { echo "replica-sync: $1" >&2; exit 1; }

interval=
while [ "$#" -gt 0 ]; do
	case "$1" in
		--interval)
			[ "$#" -ge 2 ] || fail "--interval needs a value"
			interval=$2
			shift 2
			;;
		--)
			shift
			break
			;;
		-*)
			fail "unknown option: $1"
			;;
		*)
			break
			;;
	esac
done

[ -r "$ENV_FILE" ] || fail "cannot read $ENV_FILE"
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

for name in STUFF_COPY_SOURCE_S3_ENDPOINT STUFF_COPY_SOURCE_S3_ACCESS_KEY_ID STUFF_COPY_SOURCE_S3_SECRET_ACCESS_KEY \
            STUFF_COPY_DEST_S3_ENDPOINT STUFF_COPY_DEST_S3_ACCESS_KEY_ID STUFF_COPY_DEST_S3_SECRET_ACCESS_KEY; do
	eval "value=\${$name:-}"
	[ -n "$value" ] || fail "$name is not set in $ENV_FILE"
done

command -v python3 >/dev/null 2>&1 || fail "python3 is not on PATH"
[ -r "$STORE_COPY" ] || fail "cannot read $STORE_COPY"

mkdir -p "$LEDGER_DIR"
umask 077

sync_once() {
	failed=
	for bucket in "$@"; do
		echo "replica-sync: $bucket"
		if python3 "$STORE_COPY" sync "$bucket" "$bucket" --ledger "$LEDGER_DIR/$bucket.jsonl"; then
			:
		else
			echo "replica-sync: $bucket failed" >&2
			failed="$failed $bucket"
		fi
	done
	if [ -n "$failed" ]; then
		echo "replica-sync: buckets failed:$failed" >&2
		return 1
	fi
	echo "replica-sync: complete"
}

buckets=${*:-$DEFAULT_BUCKETS}

if [ -z "$interval" ]; then
	sync_once $buckets
	exit $?
fi

while :; do
	sync_once $buckets || echo "replica-sync: run failed, retrying in ${interval}s" >&2
	sleep "$interval"
done
