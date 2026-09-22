#!/bin/sh
set -eu

if [ "$#" -ne 3 ] || [ "$1" != "--confirm-inert-rollback" ]; then
  echo "usage: rollback-inert.sh --confirm-inert-rollback DEPLOYMENT_JSON CADDYFILE_BACKUP" >&2
  exit 64
fi
[ "$(id -u)" -eq 0 ] || { echo "refused: root required" >&2; exit 1; }
config=$2
caddy_backup=$3
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
test -f "$config" && test -f "$caddy_backup" || { echo "refused: configuration or rollback Caddyfile absent" >&2; exit 1; }
caddyfile=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["caddyfile"])' "$config")
caddy_container=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["caddy_container"])' "$config")
candidate=$(mktemp /tmp/phlogiston-rollback-Caddyfile.XXXXXX)
trap 'rm -f "$candidate"' EXIT HUP INT TERM
cp "$caddy_backup" "$candidate"
docker cp "$candidate" "$caddy_container:/tmp/Caddyfile.phlogiston-rollback"
docker exec "$caddy_container" caddy validate --config /tmp/Caddyfile.phlogiston-rollback
cp "$candidate" "$caddyfile"
docker exec "$caddy_container" caddy validate --config /etc/caddy/Caddyfile
docker exec "$caddy_container" caddy reload --config /etc/caddy/Caddyfile
systemctl disable --now phlogiston-web.service 2>/dev/null || true
systemctl disable --now phlogiston-communitywatch.service 2>/dev/null || true
rm -f /etc/systemd/system/phlogiston-web.service /etc/systemd/system/phlogiston-communitywatch.service
systemctl daemon-reload
echo "services disabled; state, immutable releases, configuration, and evidence preserved"
