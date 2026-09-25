#!/bin/sh
# Real handle and PLC resolution of a named identity, through community-live's
# own sign-in path: POST /oauth/login resolves handle -> DID -> PDS -> the
# PDS's authorization server, performs a pushed authorization request there,
# and redirects the browser. The redirect is not followed; the only side
# effect is one short-lived PAR entry on the authorization server. No consent
# is given and no session is created.
#
# usage: PHLOGISTON_PRODUCTION_VERIFY=1 verify-identity-resolution.sh --receipt /abs/r.json --handle alice.example.com [--origin https://phlogiston.app]
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/lib.sh"
verify_guard "$@"; shift 2
handle=; origin=https://phlogiston.app
while [ "$#" -gt 0 ]; do
  case "$1" in
    --handle) handle=$2; shift 2 ;;
    --origin) origin=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
[ -n "$handle" ] || { echo "usage: --handle <handle>" >&2; exit 64; }
check=identity-resolution
handle=${handle#@}

# Independent resolution (not through community-live): DNS TXT, then HTTPS well-known.
did=$(dig +short TXT "_atproto.$handle" | tr -d '"' | sed -n 's/^did=//p' | head -n1)
method=dns
if [ -z "$did" ]; then
  did=$(curl --fail --silent --show-error --max-time 15 --proto '=https' "https://$handle/.well-known/atproto-did" | tr -d '\r\n' || true)
  method=https-well-known
fi
case "$did" in did:plc:*) ;; *) fail "$check" "handle $handle did not resolve to a did:plc ($method)";; esac
plc_json=$(curl --fail --silent --show-error --max-time 15 --proto '=https' "https://plc.directory/$did")
pds=$(printf '%s' "$plc_json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next(s["serviceEndpoint"] for s in d.get("service",[]) if s.get("id")=="#atproto_pds"))')
auth_server=$(curl --fail --silent --show-error --max-time 15 --proto '=https' "$pds/.well-known/oauth-protected-resource" | python3 -c 'import json,sys; print(json.load(sys.stdin)["authorization_servers"][0])')

# community-live's own path.
started=$(date +%s%N)
headers=$(curl --silent --show-error --max-time 30 --proto '=https' --max-redirs 0 -o /dev/null -D - \
  --data-urlencode "handle=$handle" "$origin/oauth/login")
elapsed_ms=$(( ($(date +%s%N) - started) / 1000000 ))
status=$(printf '%s' "$headers" | sed -n '1s/^HTTP\/[0-9.]* \([0-9]*\).*/\1/p')
location=$(printf '%s' "$headers" | tr -d '\r' | sed -n 's/^[Ll]ocation: //p' | head -n1)
location_origin=$(printf '%s' "$location" | python3 -c 'import sys; from urllib.parse import urlsplit; u=urlsplit(sys.stdin.read().strip()); print(f"{u.scheme}://{u.netloc}" if u.scheme else "")')
case "$status" in 302|303|307) ;; *) fail "$check" "community-live answered $status instead of a redirect for $handle";; esac
[ "$location_origin" = "$auth_server" ] || fail "$check" "community-live redirected to $location_origin; the identity's authorization server is $auth_server"

write_receipt "$check" pass "at=$(utc_now)" "origin=$origin" "handle=$handle" "did=$did" "independent_method=$method" \
  "pds=$pds" "authorization_server=$auth_server" "community_live_status=$status" \
  "community_live_redirect_origin=$location_origin" "community_live_elapsed_ms=$elapsed_ms" \
  "note=redirect target recorded as origin only; the PAR request_uri is short-lived and was not followed"
echo "identity resolution accepted: $handle -> $did -> $pds (auth $auth_server) in ${elapsed_ms}ms; receipt $receipt"
