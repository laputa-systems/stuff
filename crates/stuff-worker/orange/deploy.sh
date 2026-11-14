#!/bin/sh
set -eu
host=${1:-lisa}
app=stuff
health_host=stuff.17166969.xyz
root=$(git rev-parse --show-toplevel)
cd "$root"
previous=$(ssh "$host" doas -n /opt/openorange/bin/oo deployment "$app" | jaq -er '.image | select(type == "string" and length > 0)')
address=$(ssh "$host" tailscale ip -4)
printf '%s\n' "$address" | awk '
    NR != 1 { exit 1 }
    { if (split($0, octets, ".") != 4) exit 1
      for (i = 1; i <= 4; i++) if (octets[i] !~ /^[0-9]+$/ || length(octets[i]) > 3 || octets[i] + 0 > 255) exit 1 }
    END { if (NR != 1) exit 1 }
' || { echo 'expected a single Tailscale IPv4 address' >&2; exit 1; }
release=$(git rev-parse --short=12 HEAD)
image=$(crates/stuff-worker/orange/build-image.sh "$host")
[ "$image" = "$app:$release" ] || { echo 'unexpected deployment image' >&2; exit 1; }
switched=true
rollback() {
    code=$?
    trap - 0 HUP INT TERM
    if [ "$switched" = true ]; then
        if ssh "$host" doas -n /opt/openorange/bin/oo set-image "$app" "$previous" --if-current "$image" &&
           ssh "$host" doas -n /sbin/rc-service "oo-app.$app" restart; then
            echo 'Deployment failed; restored the previous Orange image' >&2
        else
            echo "Orange rollback failed; inspect oo-app.$app on the host" >&2
            code=1
        fi
    fi
    exit "$code"
}
trap rollback 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
ssh "$host" doas -n /opt/openorange/bin/oo set-image "$app" "$image" --if-current "$previous"
ssh "$host" doas -n /sbin/rc-service "oo-app.$app" restart
ssh "$host" doas -n /opt/openorange/bin/oo wait app "$app" 90
selected=$(ssh "$host" doas -n /opt/openorange/bin/oo deployment "$app" | jaq -er '.image | select(type == "string" and length > 0)')
[ "$selected" = "$image" ] || { echo 'Orange selected image changed during deployment' >&2; exit 1; }
status=$(curl -sS --noproxy "$health_host" --resolve "$health_host:443:$address" --connect-timeout 5 --max-time 10 -o /dev/null -w '%{http_code}' "https://$health_host/")
[ "$status" = 200 ] || { echo "Orange registry health returned HTTP $status" >&2; exit 1; }
selected=$(ssh "$host" doas -n /opt/openorange/bin/oo deployment "$app" | jaq -er '.image | select(type == "string" and length > 0)')
[ "$selected" = "$image" ] || { echo 'Orange selected image changed during health check' >&2; exit 1; }
switched=false
printf 'deployed %s on %s\n' "$image" "$host"
