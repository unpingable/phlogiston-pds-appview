#!/bin/sh
# OAuth long-duration continuity: proves that a stored community-live OAuth
# session still refreshes after N hours, driven by a systemd transient timer
# rather than a person waiting. The operator signs the integration identity
# in once in a browser, closes that browser, and does not use that identity
# on the site until the result exists (refresh-token rotation means two
# refreshers on one session would invalidate each other). This script writes
# the scheduling receipt now; the timer writes <receipt>.result.json when it
# fires, as the community-web user. Runs on the host as root.
#
# usage: PHLOGISTON_PRODUCTION_VERIFY=1 verify-oauth-continuity.sh --receipt /abs/r.json --did did:plc:... --hours 12
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
[ -n "$did" ] && [ -n "$hours" ] || { echo "usage: --did <identity DID> --hours <N>" >&2; exit 64; }
[ "$(id -u)" -eq 0 ] || { echo "refused: root required (schedules a transient timer as community-web)" >&2; exit 64; }
check=oauth-continuity
test -x "$live_root/node_modules/.bin/tsx" || fail "$check" "$live_root/node_modules/.bin/tsx is absent (install with pnpm install --frozen-lockfile)"
test -f "$env_file" || fail "$check" "$env_file is absent"
test -d /var/lib/community-web/oauth/session || fail "$check" "no stored OAuth sessions under /var/lib/community-web/oauth/session"

result="$receipt.result.json"
[ ! -e "$result" ] || fail "$check" "result path exists: $result"
install -d -m 0750 -o community-web "$(dirname "$result")"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
unit="phlogiston-oauth-continuity-$stamp"
systemd-run --unit="$unit" --on-active="${hours}h" --timer-property=AccuracySec=1min \
  --uid=community-web --gid=community-authority \
  --property=EnvironmentFile="$env_file" --property=WorkingDirectory="$live_root" \
  --setenv=COMMUNITY_LIVE_ROOT="$live_root" --setenv=PHLOGISTON_VERIFY_SCHEDULED_AT="$(utc_now)" \
  --property=ReadWritePaths=/var/lib/community-web --property=ReadWritePaths="$(dirname "$result")" \
  "$live_root/node_modules/.bin/tsx" "$here/oauth-continuity.ts" "$did" "$result"

write_receipt "$check" scheduled "at=$(utc_now)" "did=$did" "hours=$hours" "timer_unit=$unit.timer" "result_path=$result" \
  "note=pass/fail is in the result file written by the timer; do not use this identity on the site until then"
echo "oauth continuity scheduled: $unit fires in ${hours}h and writes $result; receipt $receipt"
echo "check later with: systemctl list-timers $unit.timer; cat $result"
