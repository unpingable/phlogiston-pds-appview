#!/bin/sh
# One qualified notification to the real room with an idempotence proof.
# Given the pending submission created by verify-indexing-lag.sh: wait until
# community-notify has recorded its "pending" event key in the cursor (that
# write happens only after the room accepted the message), then stop the
# notifier, poll once in the foreground as the service user and require
# sent=0 with no baselining, start it again, wait two poll intervals, and
# require the cursor bytes unchanged. Runs on the host as root.
#
# usage: PHLOGISTON_PRODUCTION_VERIFY=1 verify-notification-idempotence.sh --receipt /abs/r.json --uri at://... --cid bafy... [--room-observation "one line seen in #room at 12:34Z"]
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/lib.sh"
verify_guard "$@"; shift 2
uri=; cid=; observation=; unit=community-notify.service; cursor=/var/lib/community-notify/cursor.json
config=/etc/atproto-community/community-notify.toml; binary=/opt/atproto-community/.venv/bin/community-notify
poll=30; user=community-notify
while [ "$#" -gt 0 ]; do
  case "$1" in
    --uri) uri=$2; shift 2 ;;
    --cid) cid=$2; shift 2 ;;
    --room-observation) observation=$2; shift 2 ;;
    --poll-seconds) poll=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
[ -n "$uri" ] && [ -n "$cid" ] || { echo "usage: --uri <submission uri> --cid <cid>" >&2; exit 64; }
[ "$(id -u)" -eq 0 ] || { echo "refused: root required (reads the notifier cursor and restarts the unit)" >&2; exit 64; }
check=notification-idempotence
key="pending $uri $cid"
t0=$(utc_now)

deadline=$(( $(date +%s) + poll * 4 ))
until grep -Fq "\"$key\"" "$cursor" 2>/dev/null; do
  [ "$(date +%s)" -lt "$deadline" ] || fail "$check" "cursor never recorded '$key' (was the message accepted by the room?)"
  sleep 5
done
first_sent_at=$(utc_now)
occurrences=$(grep -Fo "\"$key\"" "$cursor" | wc -l)
[ "$occurrences" = 1 ] || fail "$check" "cursor holds the key $occurrences times"
before=$(sha256sum "$cursor" | cut -d' ' -f1)

systemctl stop "$unit"
once=$(runuser -u "$user" -- "$binary" --config "$config" --once)
printf '%s' "$once" | python3 -c 'import json,sys; c=json.load(sys.stdin); assert c["sent"]==0 and c["baselined"]==0, c' ||
  fail "$check" "foreground poll after stop re-sent or baselined: $once"
after_once=$(sha256sum "$cursor" | cut -d' ' -f1)
systemctl start "$unit"
sleep $(( poll * 2 + 5 ))
after_restart=$(sha256sum "$cursor" | cut -d' ' -f1)
[ "$before" = "$after_once" ] && [ "$before" = "$after_restart" ] || fail "$check" "cursor changed across restart ($before -> $after_once -> $after_restart)"
journal=$(journalctl -u "$unit" --since "$t0" -o cat --no-pager | grep -c -E "baselined|delivery failed" || true)
[ "$journal" = 0 ] || fail "$check" "notifier journal shows $journal baseline/failure lines since $t0"
systemctl is-active --quiet "$unit" || fail "$check" "$unit is not active after restart"

write_receipt "$check" pass "at=$(utc_now)" "event_key=$key" "cursor_first_recorded_by=$first_sent_at" \
  "cursor_sha256_before=$before" "cursor_sha256_after_restart=$after_restart" "foreground_poll_counts=$once" \
  "journal_baseline_or_failure_lines=$journal" "room_observation=$observation"
echo "notification idempotence accepted: one send recorded, none after restart; receipt $receipt"
