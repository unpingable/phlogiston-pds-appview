#!/bin/sh
# Jetstream arrival and indexing lag for one controlled record. Writes exactly
# one zone.neutral.community.submit record (a root submission of the
# identity's own latest post) to the operator's integration identity's own
# PDS, then measures when the observer first received it. Timestamps come
# from the observer's audit event (first_received_at) and the local clock.
#
# Side effects: one submission record in the identity's repository (the
# author can delete it with any client); one pending item in the moderation
# queue, which the moderator leaves unadmitted or admits and removes; one
# "pending" line in the room from community-notify. Run
# verify-notification-idempotence.sh right after this check with the URI it
# prints.
#
# The app password is read from the 0600 file named by
# PHLOGISTON_VERIFY_APP_PASSWORD_FILE and is never printed or written.
#
# usage: PHLOGISTON_PRODUCTION_VERIFY=1 PHLOGISTON_VERIFY_APP_PASSWORD_FILE=/root/x verify-indexing-lag.sh --receipt /abs/r.json --did did:plc:... --community did:plc:b53udqv47g2dayvpstzdefpq [--observer http://127.0.0.1:8080] [--timeout 300]
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/lib.sh"
verify_guard "$@"; shift 2
did=; community=did:plc:b53udqv47g2dayvpstzdefpq; observer=http://127.0.0.1:8080; timeout=300
while [ "$#" -gt 0 ]; do
  case "$1" in
    --did) did=$2; shift 2 ;;
    --community) community=$2; shift 2 ;;
    --observer) observer=$2; shift 2 ;;
    --timeout) timeout=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
[ -n "$did" ] || { echo "usage: --did <identity DID>" >&2; exit 64; }
check=indexing-lag
password_file=${PHLOGISTON_VERIFY_APP_PASSWORD_FILE:-}
[ -n "$password_file" ] && [ -f "$password_file" ] || { echo "refused: PHLOGISTON_VERIFY_APP_PASSWORD_FILE must name a readable file" >&2; exit 64; }
[ "$(stat -c %a "$password_file")" = 600 ] || { echo "refused: $password_file must be mode 0600" >&2; exit 64; }

pds=$(curl --fail --silent --show-error --max-time 15 --proto '=https' "https://plc.directory/$did" |
  python3 -c 'import json,sys; d=json.load(sys.stdin); print(next(s["serviceEndpoint"] for s in d.get("service",[]) if s.get("id")=="#atproto_pds"))')
subject=$(curl --fail --silent --show-error --max-time 15 --proto '=https' \
  "$pds/xrpc/com.atproto.repo.listRecords?repo=$did&collection=app.bsky.feed.post&limit=1" |
  python3 -c 'import json,sys; r=json.load(sys.stdin)["records"][0]; print(r["uri"], r["cid"])')
subject_uri=${subject% *}; subject_cid=${subject#* }

access=$(python3 - "$pds" "$did" "$password_file" <<'PY'
import json, sys, urllib.request
pds, did, path = sys.argv[1:]
body = json.dumps({"identifier": did, "password": open(path).read().strip()}).encode()
request = urllib.request.Request(f"{pds}/xrpc/com.atproto.server.createSession", data=body, headers={"content-type": "application/json"})
with urllib.request.urlopen(request, timeout=20) as response:
    print(json.load(response)["accessJwt"])
PY
)
created_at=$(utc_now)
t_create=$(date +%s.%N)
# The access token crosses to the writer through the environment only (readable
# by root via /proc; never an argument, never printed, never in the receipt).
created=$(PHLOG_VERIFY_ACCESS="$access" python3 - "$pds" "$did" "$community" "$subject_uri" "$subject_cid" "$created_at" <<'PY'
import json, os, sys, urllib.request
pds, did, community, uri, cid, created_at = sys.argv[1:]
record = {"$type": "zone.neutral.community.submit", "community": community, "subject": {"uri": uri, "cid": cid}, "createdAt": created_at}
body = json.dumps({"repo": did, "collection": "zone.neutral.community.submit", "record": record}).encode()
request = urllib.request.Request(f"{pds}/xrpc/com.atproto.repo.createRecord", data=body,
    headers={"content-type": "application/json", "authorization": "Bearer " + os.environ["PHLOG_VERIFY_ACCESS"]})
with urllib.request.urlopen(request, timeout=20) as response:
    result = json.load(response)
print(result["uri"], result["cid"])
PY
)
unset access
uri=${created% *}; cid=${created#* }

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
[ -n "$first_received" ] || fail "$check" "observer did not receive $uri within ${timeout}s"
lag=$(python3 -c 'import sys; from datetime import datetime, timezone
first=datetime.fromisoformat(sys.argv[1].replace("Z","+00:00")); t=float(sys.argv[2]); print(f"{first.timestamp()-t:.3f}")' "$first_received" "$t_create")
seen_after=$(python3 -c 'import sys; print(f"{float(sys.argv[1])-float(sys.argv[2]):.3f}")' "$t_seen" "$t_create")
health=$(curl --silent --max-time 10 "$observer/health" | python3 -c 'import json,sys; h=json.load(sys.stdin); print(h.get("status"), h.get("lastIngestAt"))' || echo "unavailable")
queued=$(curl --silent --max-time 10 "$observer/api/v0/communities/$community/moderation-queue" | grep -c "$uri" || true)

write_receipt "$check" pass "at=$(utc_now)" "identity=$did" "pds=$pds" "community=$community" "record_uri=$uri" "record_cid=$cid" \
  "subject_uri=$subject_uri" "created_at=$created_at" "observer_first_received_at=$first_received" \
  "observer_lag_seconds=$lag" "poll_detected_after_seconds=$seen_after" "observer_health=$health" "in_moderation_queue=$queued"
echo "indexing lag accepted: $uri received by the observer ${lag}s after creation; receipt $receipt"
echo "next: verify-notification-idempotence.sh --uri $uri --cid $cid"
