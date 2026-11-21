#!/bin/sh
set -eu
here=$(CDPATH='' cd -- "$(dirname "$0")" && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/store-copy.XXXXXX")
pids=
cleanup() { for pid in $pids; do kill "$pid" 2>/dev/null || true; done; rm -rf "$work"; }
trap cleanup EXIT INT TERM
start() {
	mkfifo "$work/$1.in"
	python3 "$here/fake_s3.py" < "$work/$1.in" > "$work/$1.out" 2>"$work/$1.err" &
	pids="$pids $!"
}
port() {
	until grep -q '^PORT ' "$work/$1.out" 2>/dev/null; do sleep 0.1; done
	sed -n 's/^PORT //p' "$work/$1.out"
}
start source
exec 8>"$work/source.in"
start dest
exec 9>"$work/dest.in"
src=$(port source)
dst=$(port dest)
export STUFF_COPY_SOURCE_S3_ENDPOINT="http://127.0.0.1:$src" STUFF_COPY_SOURCE_S3_ACCESS_KEY_ID=source STUFF_COPY_SOURCE_S3_SECRET_ACCESS_KEY=source-secret STUFF_COPY_SOURCE_S3_REGION=us-east-1
export STUFF_COPY_DEST_S3_ENDPOINT="http://127.0.0.1:$dst" STUFF_COPY_DEST_S3_ACCESS_KEY_ID=dest STUFF_COPY_DEST_S3_SECRET_ACCESS_KEY=dest-secret STUFF_COPY_DEST_S3_REGION=us-east-1
export R2_LIST_PAGE=100 PYTHONPATH="$here"
python3 - "$src" <<'PY'
import importlib.util, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
import xml.etree.ElementTree as ET
os.environ.update(R2_S3_ACCESS_KEY_ID="source", R2_S3_SECRET_ACCESS_KEY="source-secret", R2_S3_REGION="us-east-1")
base = f"http://127.0.0.1:{sys.argv[1]}/bucket"
for index in range(250):
    status, _, _ = s3.request("PUT", f"{base}/objects/{index:04d}.txt", f"object {index}\n".encode() * (index + 1), "text/plain")
    assert status == 200, status
status, body, _ = s3.request("POST", f"{base}/blobs/layer?uploads", b"", "application/octet-stream")
upload = s3.find_text(ET.fromstring(body), "UploadId")
parts = []
for number, size in enumerate([1 << 20, 1 << 20, 12345], start=1):
    status, _, headers = s3.request("PUT", f"{base}/blobs/layer?partNumber={number}&uploadId={upload}", bytes([number]) * size, "application/octet-stream")
    assert status == 200, status
    parts.append(f"<Part><PartNumber>{number}</PartNumber><ETag>{headers.get('ETag')}</ETag></Part>")
status, _, _ = s3.request("POST", f"{base}/blobs/layer?uploadId={upload}", f"<CompleteMultipartUpload>{''.join(parts)}</CompleteMultipartUpload>".encode(), "application/octet-stream")
assert status == 200, status
PY
copy() { python3 "$here/store-copy.py" copy bucket bucket --ledger "$work/ledger.jsonl"; }
verify() { python3 "$here/store-copy.py" verify bucket bucket --ledger "$work/ledger.jsonl" "$@"; }
field() { python3 -I -c 'import json,sys; print(json.loads(sys.stdin.read())[sys.argv[1]])' "$1"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

first=$(copy 2>"$work/copy.err") || { cat "$work/copy.err" >&2; fail "first copy failed"; }
[ "$(echo "$first" | field copied)" = 251 ] || fail "first copy did not copy every object: $first"
out=$(verify --deep) || fail "verify after copy"
[ "$(echo "$out" | field etagPreserved)" = 251 ] || fail "multipart ETag was not preserved: $out"
[ "$(copy | field copied)" = 0 ] || fail "rerun copied verified objects"
printf '{"key":"interrupted' >> "$work/ledger.jsonl"
[ "$(copy | field copied)" = 0 ] || fail "recovery of a torn ledger copied verified objects"
[ "$(jaq -s length "$work/ledger.jsonl")" = 251 ] || fail "torn ledger tail was not removed"
head -n 100 "$work/ledger.jsonl" > "$work/partial" && mv "$work/partial" "$work/ledger.jsonl"
[ "$(copy | field copied)" = 151 ] || fail "resume did not copy exactly the unverified objects"
python3 - "$src" <<'PY'
import importlib.util, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
os.environ.update(R2_S3_ACCESS_KEY_ID="source", R2_S3_SECRET_ACCESS_KEY="source-secret", R2_S3_REGION="us-east-1")
assert s3.request("PUT", f"http://127.0.0.1:{sys.argv[1]}/bucket/objects/0007.txt", b"changed after copy\n", "text/plain")[0] == 200
PY
verify >/dev/null 2>&1 && fail "verify missed a changed source"
[ "$(copy | field recopiedChanged)" = 1 ] || fail "changed source was not re-copied"
verify --deep >/dev/null || fail "verify after re-copy"
python3 - "$dst" <<'PY'
import importlib.util, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
os.environ.update(R2_S3_ACCESS_KEY_ID="dest", R2_S3_SECRET_ACCESS_KEY="dest-secret", R2_S3_REGION="us-east-1")
base = f"http://127.0.0.1:{sys.argv[1]}/bucket"
assert s3.request("PUT", f"{base}/objects/0010.txt", b"corrupted\n", "text/plain")[0] == 200
assert s3.request("DELETE", f"{base}/objects/0011.txt")[0] in (200, 204)
PY
out=$(verify 2>&1) && fail "verify missed corruption"
echo "$out" | grep -q 'destination differs from the ledger: objects/0010.txt' || fail "corruption not named: $out"
echo "$out" | grep -q 'missing at destination: objects/0011.txt' || fail "missing object not named: $out"

# --- sync: generations before the pointer, and an interrupted sync keeps the old pointer ---
G2_OBJECTS=400
export G2_OBJECTS
python3 - "$src" <<'PY'
import importlib.util, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
os.environ.update(R2_S3_ACCESS_KEY_ID="source", R2_S3_SECRET_ACCESS_KEY="source-secret", R2_S3_REGION="us-east-1")
base = f"http://127.0.0.1:{sys.argv[1]}/site"
for key in ["generations/g0/catalog.json", "generations/g1/catalog.json", "generations/g1/index.html", "generations/g1/simple/proj/index.html"]:
    assert s3.request("PUT", f"{base}/{key}", f"{key}\n".encode(), "text/plain")[0] == 200
assert s3.request("PUT", f"{base}/current", b"g1", "text/plain")[0] == 200
PY
sync() { python3 "$here/store-copy.py" sync site site --ledger "$work/sync-ledger.jsonl"; }
dest_puts() { python3 - "$dst" "$1" <<'PY'
import json, sys, urllib.request
port, needle = sys.argv[1], sys.argv[2]
log = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/_fake/requests"))["requests"]
puts = [entry["path"] for entry in log if entry["method"] == "PUT" and entry["path"].startswith("/site/")]
print(len(puts), sum(1 for path in puts if needle in path))
PY
}
out=$(sync) || fail "sync failed: $out"
[ "$(echo "$out" | field pointer)" = g1 ] || fail "sync did not report the copied pointer: $out"
[ "$(echo "$out" | field skipped)" = 0 ] || fail "first sync skipped objects: $out"
python3 - "$dst" <<'PY'
import importlib.util, json, os, sys, urllib.request
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
port = sys.argv[1]
log = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/_fake/requests"))["requests"]
puts = [entry["path"] for entry in log if entry["method"] == "PUT" and entry["path"].startswith("/site/")]
pointer = [index for index, path in enumerate(puts) if path == "/site/current"]
generation = [index for index, path in enumerate(puts) if "/generations/" in path]
assert pointer, "sync never wrote the pointer"
assert generation, "sync never wrote a generation object"
assert max(generation) < pointer[-1], f"the pointer was written before a generation object: {puts}"
os.environ.update(R2_S3_ACCESS_KEY_ID="dest", R2_S3_SECRET_ACCESS_KEY="dest-secret", R2_S3_REGION="us-east-1")
status, body, _ = s3.request("GET", f"http://127.0.0.1:{port}/site/current")
assert status == 200 and body == b"g1", (status, body)
assert not any("/generations/g0/" in path for path in puts), f"sync copied a generation the pointer does not name: {puts}"
PY

# A newer generation is published at the source. The sync is killed while the
# generation objects are copying, so the destination must still answer g1.
python3 - "$src" <<'PY'
import importlib.util, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
os.environ.update(R2_S3_ACCESS_KEY_ID="source", R2_S3_SECRET_ACCESS_KEY="source-secret", R2_S3_REGION="us-east-1")
base = f"http://127.0.0.1:{sys.argv[1]}/site"
for index in range(int(os.environ["G2_OBJECTS"])):
    assert s3.request("PUT", f"{base}/generations/g2/objects/{index:03d}.json", b"x" * 65536, "application/json")[0] == 200
assert s3.request("PUT", f"{base}/current", b"g2", "text/plain")[0] == 200
PY
python3 "$here/store-copy.py" sync site site --ledger "$work/sync-ledger.jsonl" --jobs 1 >"$work/sync2.out" 2>"$work/sync2.err" &
sync_pid=$!
pids="$pids $sync_pid"
i=0
while [ "$i" -lt 2000 ]; do
	g2=$(dest_puts generations/g2/ | cut -d' ' -f2)
	[ "$g2" -ge 1 ] && break
	i=$((i + 1))
	sleep 0.02
done
kill -KILL "$sync_pid" 2>/dev/null || true
wait "$sync_pid" 2>/dev/null || true
[ "$g2" -ge 1 ] || fail "the interrupted sync never copied a g2 object"
g2_placed=$(dest_puts generations/g2/ | cut -d' ' -f2)
[ "$g2_placed" -lt "$G2_OBJECTS" ] || fail "the sync finished before it could be interrupted; the case proved nothing"
python3 - "$dst" <<'PY'
import importlib.util, json, os, sys, urllib.request
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
port = sys.argv[1]
os.environ.update(R2_S3_ACCESS_KEY_ID="dest", R2_S3_SECRET_ACCESS_KEY="dest-secret", R2_S3_REGION="us-east-1")
status, body, _ = s3.request("GET", f"http://127.0.0.1:{port}/site/current")
assert status == 200 and body == b"g1", f"an interrupted sync moved the pointer: {status} {body!r}"
objects = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/_fake/state"))["objects"]
present = {entry["key"] for entry in objects if entry["bucket"] == "site"}
assert "generations/g1/catalog.json" in present, "the g1 generation the pointer names is incomplete"
PY
g2_verified=$(grep -c 'generations/g2/' "$work/sync-ledger.jsonl" || true)
[ "$g2_verified" -ge 1 ] || fail "the interrupted sync recorded no verified g2 object"
out=$(sync) || fail "resumed sync failed: $out"
[ "$(echo "$out" | field pointer)" = g2 ] || fail "the resumed sync did not move the pointer: $out"
[ "$(echo "$out" | field skipped)" -ge "$g2_verified" ] || fail "the resumed sync re-copied verified objects: $out"

# A pointer naming a generation with no objects at the source must not be
# copied: moving it would leave the destination naming a generation it does
# not hold. This is the invariant an interrupted sync must also preserve.
python3 - "$src" <<'PY'
import importlib.util, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
os.environ.update(R2_S3_ACCESS_KEY_ID="source", R2_S3_SECRET_ACCESS_KEY="source-secret", R2_S3_REGION="us-east-1")
base = f"http://127.0.0.1:{sys.argv[1]}/partial"
assert s3.request("PUT", f"{base}/generations/g9/catalog.json", b"catalog", "text/plain")[0] == 200
assert s3.request("PUT", f"{base}/current", b"g9", "text/plain")[0] == 200
PY
python3 "$here/store-copy.py" sync partial partial --ledger "$work/partial-ledger.jsonl" >/dev/null || fail "partial sync failed"
python3 - "$src" <<'PY'
import importlib.util, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
os.environ.update(R2_S3_ACCESS_KEY_ID="source", R2_S3_SECRET_ACCESS_KEY="source-secret", R2_S3_REGION="us-east-1")
base = f"http://127.0.0.1:{sys.argv[1]}/partial"
for key in ["current", "generations/g9/catalog.json"]:
    assert s3.request("DELETE", f"{base}/{key}")[0] in (200, 204)
assert s3.request("PUT", f"{base}/current", b"g10", "text/plain")[0] == 200
PY
if python3 "$here/store-copy.py" sync partial partial --ledger "$work/partial-ledger.jsonl" >/dev/null 2>"$work/partial.err"; then
	fail "sync copied a pointer that names a missing generation"
fi
grep -q 'no generations/g10/' "$work/partial.err" || fail "sync did not name the missing generation: $(cat "$work/partial.err")"
python3 - "$dst" <<'PY'
import importlib.util, os, sys
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
os.environ.update(R2_S3_ACCESS_KEY_ID="dest", R2_S3_SECRET_ACCESS_KEY="dest-secret", R2_S3_REGION="us-east-1")
status, body, _ = s3.request("GET", f"http://127.0.0.1:{sys.argv[1]}/partial/current")
assert status == 200 and body == b"g9", f"the refused sync moved the destination pointer: {status} {body!r}"
PY
python3 - "$dst" <<'PY'
import importlib.util, json, os, sys, urllib.request
sys.path.insert(0, os.environ["PYTHONPATH"])
spec = importlib.util.spec_from_file_location("s3", os.path.join(os.environ["PYTHONPATH"], "r2-multipart.py"))
s3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s3)
port = sys.argv[1]
log = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/_fake/requests"))["requests"]
puts = [entry["path"] for entry in log if entry["method"] == "PUT" and entry["path"].startswith("/site/")]
generation = [index for index, path in enumerate(puts) if "/generations/g2/" in path]
pointer = [index for index, path in enumerate(puts) if path == "/site/current"]
assert generation and pointer, (generation, pointer)
assert max(generation) < pointer[-1], f"the pointer was written before a g2 object: {puts}"
os.environ.update(R2_S3_ACCESS_KEY_ID="dest", R2_S3_SECRET_ACCESS_KEY="dest-secret", R2_S3_REGION="us-east-1")
status, body, _ = s3.request("GET", f"http://127.0.0.1:{port}/site/current")
assert status == 200 and body == b"g2", (status, body)
PY

# replica-sync.sh reads plain assignments from its env file; store-copy.py
# must still see them, with none inherited from this script's environment.
env -u STUFF_COPY_SOURCE_S3_ENDPOINT -u STUFF_COPY_SOURCE_S3_ACCESS_KEY_ID -u STUFF_COPY_SOURCE_S3_SECRET_ACCESS_KEY -u STUFF_COPY_SOURCE_S3_REGION \
	-u STUFF_COPY_DEST_S3_ENDPOINT -u STUFF_COPY_DEST_S3_ACCESS_KEY_ID -u STUFF_COPY_DEST_S3_SECRET_ACCESS_KEY -u STUFF_COPY_DEST_S3_REGION \
	sh -c 'env | grep "^STUFF_COPY_" && exit 1; exit 0' || fail "the replica-sync case inherited STUFF_COPY_ variables"
cat >"$work/replica-sync.env" <<EOF
STUFF_COPY_SOURCE_S3_ENDPOINT=http://127.0.0.1:$src
STUFF_COPY_SOURCE_S3_ACCESS_KEY_ID=source
STUFF_COPY_SOURCE_S3_SECRET_ACCESS_KEY=source-secret
STUFF_COPY_SOURCE_S3_REGION=us-east-1
STUFF_COPY_DEST_S3_ENDPOINT=http://127.0.0.1:$dst
STUFF_COPY_DEST_S3_ACCESS_KEY_ID=dest
STUFF_COPY_DEST_S3_SECRET_ACCESS_KEY=dest-secret
STUFF_COPY_DEST_S3_REGION=us-east-1
EOF
out=$(env -u STUFF_COPY_SOURCE_S3_ENDPOINT -u STUFF_COPY_SOURCE_S3_ACCESS_KEY_ID -u STUFF_COPY_SOURCE_S3_SECRET_ACCESS_KEY -u STUFF_COPY_SOURCE_S3_REGION \
	-u STUFF_COPY_DEST_S3_ENDPOINT -u STUFF_COPY_DEST_S3_ACCESS_KEY_ID -u STUFF_COPY_DEST_S3_SECRET_ACCESS_KEY -u STUFF_COPY_DEST_S3_REGION \
	REPLICA_SYNC_ENV="$work/replica-sync.env" REPLICA_SYNC_LEDGER_DIR="$work/replica-ledgers" \
	sh "$here/replica-sync.sh" site 2>&1) || fail "replica-sync.sh failed with a plain env file: $out"
echo "$out" | grep -q '"pointer": "g2"' || fail "replica-sync.sh did not sync the site bucket: $out"

echo "OK: copy, ETag-preserving multipart, resume, changed-source, corruption and missing-object detection, paginated listings, sync ordering, current-generation-only sync, interrupted sync, a refused incomplete-generation pointer, and replica-sync.sh with a plain env file"
