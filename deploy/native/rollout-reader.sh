#!/bin/sh
# Restart one Stuff native reader without dropping a request: withdraw it so the ingress health
# check moves traffic to the other reader, wait for its requests to finish, restart it on the
# release named in its conf.d file, wait for readiness and restore it.
set -eu
reader=${1:?usage: rollout-reader.sh a|b}
case "$reader" in a) control=127.0.0.1:8091 ;; b) control=127.0.0.1:8093 ;; *) echo "rollout-reader: reader must be a or b" >&2; exit 2 ;; esac
other=$([ "$reader" = a ] && echo 127.0.0.1:8093 || echo 127.0.0.1:8091)
wget -q -O /dev/null "http://$other/ready" || { echo "rollout-reader: the other reader is not ready; refusing" >&2; exit 1; }
wget -q -O /dev/null --post-data= "http://$control/withdraw"
restore() {
	if ! wget -q -O /dev/null --post-data= "http://$control/restore"; then
		echo "rollout-reader: reader-$reader remains withdrawn; restore it at $control" >&2
		exit 1
	fi
}
trap restore EXIT
trap 'exit 1' HUP INT TERM
sleep 4
deadline=$(( $(date +%s) + 900 ))
until wget -q -O - "http://$control/metrics" | grep -q '"activeRequests":0,'; do
	[ "$(date +%s)" -lt "$deadline" ] || { echo "rollout-reader: requests did not drain" >&2; exit 1; }
	sleep 1
done
rc-service "stuff-native.reader-$reader" restart >/dev/null
wget -q -O /dev/null --post-data= "http://$control/restore"
trap - EXIT HUP INT TERM
sleep 3
wget -q -O - "http://$control/identity"
echo
