#!/bin/sh
# Take a secret-free expiry baseline, then schedule a final probe bound to it.
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/lib.sh"
verify_guard "$@"; shift 2
did=; hours=; live_root=/opt/atproto-community/apps/community-live; env_file=/etc/atproto-community/community-web.env
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
while [ "$#" -gt 0 ]; do
  case "$1" in
    --did) did=$2; shift 2 ;;
    --hours) hours=$2; shift 2 ;;
    --live-root) live_root=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
[ -n "$did" ] && [ -n "$hours" ] || { echo "usage: --did <identity DID> --hours <integer N>=12" >&2; exit 64; }
case "$hours" in 0|[1-9][0-9]*) ;; *) echo "refused: --hours must be a canonical decimal integer >=12" >&2; exit 64 ;; esac
[ "$hours" -ge 12 ] || { echo "refused: --hours must be >=12" >&2; exit 64; }
[ "$hours" -le 8760 ] || { echo "refused: --hours exceeds the bounded one-year scheduler limit" >&2; exit 64; }
minimum_elapsed_seconds=$(( hours * 3600 ))
[ "$(id -u)" -eq 0 ] || { echo "refused: root required (schedules transient units as community-web)" >&2; exit 64; }
check=oauth-continuity
test -x "$live_root/node_modules/.bin/tsx" || fail "$check" "$live_root/node_modules/.bin/tsx is absent"
test -f "$env_file" || fail "$check" "$env_file is absent"
test -d /var/lib/community-web/oauth/session || fail "$check" "no stored OAuth sessions under /var/lib/community-web/oauth/session"

result="$receipt.result.json"
baseline="$receipt.baseline.json"
[ ! -e "$result" ] && [ ! -e "$baseline" ] || fail "$check" "result or baseline path exists"
install -d -m 0750 -o community-web "$(dirname "$result")"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
unit="phlogiston-oauth-continuity-$stamp"
baseline_unit="$unit-baseline"
scheduled_at=$(utc_now)

systemd-run --unit="$baseline_unit" --wait --pipe \
  --property=Type=oneshot --property=RemainAfterExit=yes \
  --uid=community-web --gid=community-authority \
  --property=EnvironmentFile="$env_file" --property=WorkingDirectory="$live_root" \
  --setenv=COMMUNITY_LIVE_ROOT="$live_root" --setenv=PHLOGISTON_VERIFY_SCHEDULED_AT="$scheduled_at" \
  --setenv=PHLOGISTON_VERIFY_MIN_ELAPSED_SECONDS="$minimum_elapsed_seconds" \
  --property=ReadWritePaths=/var/lib/community-web --property=ReadWritePaths="$(dirname "$result")" \
  "$live_root/node_modules/.bin/tsx" "$here/oauth-continuity.ts" baseline "$did" "$baseline"
test -f "$baseline" || fail "$check" "baseline unit completed without the baseline receipt"
baseline_sha=$(sha256sum "$baseline" | awk '{print $1}')

systemd-run --unit="$unit" --on-active="${hours}h" --timer-property=AccuracySec=1min \
  --uid=community-web --gid=community-authority \
  --property=EnvironmentFile="$env_file" --property=WorkingDirectory="$live_root" \
  --setenv=COMMUNITY_LIVE_ROOT="$live_root" --setenv=PHLOGISTON_VERIFY_SCHEDULED_AT="$scheduled_at" \
  --setenv=PHLOGISTON_VERIFY_MIN_ELAPSED_SECONDS="$minimum_elapsed_seconds" \
  --setenv=PHLOGISTON_VERIFY_BASELINE_SHA256="$baseline_sha" \
  --property=ReadWritePaths=/var/lib/community-web --property=ReadWritePaths="$(dirname "$result")" \
  "$live_root/node_modules/.bin/tsx" "$here/oauth-continuity.ts" verify "$did" "$result" "$baseline"

write_receipt "$check" scheduled "at=$scheduled_at" "did=$did" "hours=$hours" \
  "minimum_elapsed_seconds=$minimum_elapsed_seconds" "baseline_unit=$baseline_unit.service" \
  "baseline_path=$baseline" "baseline_sha256=$baseline_sha" \
  "timer_unit=$unit.timer" "result_path=$result" \
  "note=pass requires actual elapsed time, matching DID read and advanced token-expiry provenance; do not use this identity until result"
echo "oauth continuity scheduled: $unit after at least ${hours}h; baseline $baseline; result $result; receipt $receipt"
