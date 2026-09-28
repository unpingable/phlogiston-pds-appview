#!/bin/sh
# Production V2. One exact caller-supplied rkey is durably reserved before
# createRecord. Any uncertain response is reconciled by getRecord at that rkey;
# an absent prior attempt is never redispatched.
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/lib.sh"
verify_guard "$@"; shift 2
did=; community=did:plc:b53udqv47g2dayvpstzdefpq; observer=http://127.0.0.1:8080; timeout=300; intent=; rkey=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --did) did=$2; shift 2 ;;
    --community) community=$2; shift 2 ;;
    --observer) observer=$2; shift 2 ;;
    --timeout) timeout=$2; shift 2 ;;
    --intent) intent=$2; shift 2 ;;
    --rkey) rkey=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
[ -n "$did" ] && [ -n "$intent" ] && [ -n "$rkey" ] || {
  echo "usage: --did <identity DID> --intent /absolute/create-intent.json --rkey <preallocated record key>" >&2
  exit 64
}
case "$intent" in /*) ;; *) echo "refused: --intent must be absolute" >&2; exit 64 ;; esac
[ -d "$(dirname "$intent")" ] || { echo "refused: intent parent is absent" >&2; exit 64; }
check=indexing-lag
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
password_file=${PHLOGISTON_VERIFY_APP_PASSWORD_FILE:-}
[ -n "$password_file" ] && [ -f "$password_file" ] || {
  echo "refused: PHLOGISTON_VERIFY_APP_PASSWORD_FILE must name a readable file" >&2; exit 64;
}
[ "$(stat -c %a "$password_file")" = 600 ] || { echo "refused: $password_file must be mode 0600" >&2; exit 64; }

pds=$(curl --fail --silent --show-error --max-time 15 --proto '=https' "https://plc.directory/$did" |
  python3 -c 'import json,sys; d=json.load(sys.stdin); print(next(s["serviceEndpoint"] for s in d.get("service",[]) if s.get("id")=="#atproto_pds"))')
created_at=; subject_uri=; subject_cid=
if [ ! -e "$intent" ]; then
  subject=$(curl --fail --silent --show-error --max-time 15 --proto '=https' \
    "$pds/xrpc/com.atproto.repo.listRecords?repo=$did&collection=app.bsky.feed.post&limit=1" |
    python3 -c 'import json,sys; r=json.load(sys.stdin)["records"][0]; print(r["uri"], r["cid"])')
  subject_uri=${subject% *}; subject_cid=${subject#* }
  created_at=$(utc_now)
fi

if [ -e "$intent" ]; then
  record_json=$(python3 -B "$here/verify_indexing_record.py" \
    --intent "$intent" --pds "$pds" --did "$did" --community "$community" --rkey "$rkey" \
    --password-file "$password_file") || record_status=$?
else
  record_json=$(python3 -B "$here/verify_indexing_record.py" \
    --intent "$intent" --pds "$pds" --did "$did" --community "$community" --rkey "$rkey" \
    --password-file "$password_file" --created-at "$created_at" \
    --subject-uri "$subject_uri" --subject-cid "$subject_cid") || record_status=$?
fi
if [ "${record_status:-0}" -ne 0 ]; then
  fail "$check" "exact record writer refused; inspect the retained intent and do not redispatch"
fi
json_field() {
  printf '%s\n' "$record_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$1"
}
uri=$(json_field uri); cid=$(json_field cid); subject_uri=$(json_field subject_uri)
created_at=$(json_field created_at); record_sha=$(json_field record_sha256)
intent_sha=$(json_field intent_sha256); disposition=$(json_field disposition); attempts=$(json_field attempts)
t_create=$(python3 -c 'import sys; from datetime import datetime; print(datetime.fromisoformat(sys.argv[1].replace("Z","+00:00")).timestamp())' "$created_at")

deadline=$(( $(date +%s) + timeout ))
first_received=
while [ "$(date +%s)" -lt "$deadline" ]; do
  first_received=$(curl --silent --max-time 10 "$observer/api/v0/communities/$community/audit?limit=100" |
    python3 -c 'import json,sys; uri=sys.argv[1]
try: events=json.load(sys.stdin)["events"]
except Exception: events=[]
print(next((e["first_received_at"] for e in events if e.get("record_uri")==uri), ""))' "$uri" || true)
  [ -n "$first_received" ] && break
  sleep 2
done
t_seen=$(date +%s.%N)
if [ -z "$first_received" ]; then
  write_receipt "$check" fail "reason=observer timeout after exact write" "at=$(utc_now)" \
    "record_uri=$uri" "record_cid=$cid" "intent_path=$intent" "intent_sha256=$intent_sha"
  exit 1
fi
lag=$(python3 -c 'import sys; from datetime import datetime
first=datetime.fromisoformat(sys.argv[1].replace("Z","+00:00")); print(f"{first.timestamp()-float(sys.argv[2]):.3f}")' "$first_received" "$t_create")
seen_after=$(python3 -c 'import sys; print(f"{float(sys.argv[1])-float(sys.argv[2]):.3f}")' "$t_seen" "$t_create")
health=$(curl --silent --max-time 10 "$observer/health" | python3 -c 'import json,sys; h=json.load(sys.stdin); print(h.get("status"), h.get("lastIngestAt"))' || echo "unavailable")
queued=$(curl --fail --silent --show-error --max-time 10 "$observer/api/v0/communities/$community/moderation-queue" |
  python3 -c 'import json,sys; community,uri=sys.argv[1:]; d=json.load(sys.stdin)
assert type(d) is dict and d.get("communityDid")==community and type(d.get("submissions")) is list
print(sum(type(x) is dict and type(x.get("submission")) is dict and x["submission"].get("uri")==uri for x in d["submissions"]))' "$community" "$uri")
if [ "$queued" -ne 1 ]; then
  write_receipt "$check" fail "reason=exact record is not present exactly once in moderation queue" "at=$(utc_now)" \
    "record_uri=$uri" "record_cid=$cid" "in_moderation_queue=$queued" \
    "intent_path=$intent" "intent_sha256=$intent_sha"
  exit 1
fi

write_receipt "$check" pass "at=$(utc_now)" "identity=$did" "pds=$pds" "community=$community" \
  "record_uri=$uri" "record_cid=$cid" "subject_uri=$subject_uri" "created_at=$created_at" \
  "record_sha256=$record_sha" "intent_path=$intent" "intent_sha256=$intent_sha" \
  "write_disposition=$disposition" "write_attempts=$attempts" \
  "observer_first_received_at=$first_received" "observer_lag_seconds=$lag" \
  "poll_detected_after_seconds=$seen_after" "observer_health=$health" "in_moderation_queue=$queued"
echo "indexing lag accepted: $uri reconciled and present exactly once in moderation queue; receipt $receipt"
echo "next: verify-notification-idempotence.sh --uri $uri --cid $cid"
