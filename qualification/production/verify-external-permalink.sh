#!/bin/sh
# Signed-out permalink from outside: fetches one admitted discussion's
# permalink over the public internet from a machine that is not the host and
# not on its network path, with no cookies, and requires an ordinary 200 page
# with no sign-in wall. Run this from a laptop on a different network (mobile
# tether, another provider), never on the host.
#
# usage: PHLOGISTON_PRODUCTION_VERIFY=1 verify-external-permalink.sh --receipt /abs/r.json --rkey <rkey> --from "mobile tether, <city>" [--origin https://phlogiston.app]
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/lib.sh"
verify_guard "$@"; shift 2
rkey=; from=; origin=https://phlogiston.app
while [ "$#" -gt 0 ]; do
  case "$1" in
    --rkey) rkey=$2; shift 2 ;;
    --from) from=$2; shift 2 ;;
    --origin) origin=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
[ -n "$rkey" ] && [ -n "$from" ] || { echo "usage: --rkey <rkey> --from <description of the network path>" >&2; exit 64; }
check=external-permalink
host=${origin#https://}
public_a=$(dig @1.1.1.1 +short A "$host" | head -n1)
local_addrs=$(hostname -I 2>/dev/null || ip -o addr 2>/dev/null | awk '{print $4}' | cut -d/ -f1)
for addr in $local_addrs; do
  [ "$addr" != "$public_a" ] || { echo "refused: this machine holds $public_a; run the check from another network path" >&2; exit 64; }
done
[ ! -d /var/lib/community-web ] || { echo "refused: this looks like the host itself" >&2; exit 64; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
status=$(curl --silent --show-error --max-time 30 --proto '=https' -o "$tmp/body" -D "$tmp/headers" \
  --write-out '%{http_code} %{remote_ip} %{ssl_verify_result} %{time_total}' "$origin/d/$rkey")
code=${status%% *}
rest=${status#* }; remote_ip=${rest%% *}; rest=${rest#* }; ssl_verify=${rest%% *}; time_total=${rest#* }
[ "$code" = 200 ] || fail "$check" "$origin/d/$rkey answered $code from $from"
[ "$ssl_verify" = 0 ] || fail "$check" "TLS verification result $ssl_verify"
! grep -q "Sign in is required" "$tmp/body" || fail "$check" "permalink demanded sign-in"
grep -q "Community view: admission and removal change only this view" "$tmp/body" || fail "$check" "permalink body lacks the community view note"
! grep -qi "^set-cookie:" "$tmp/headers" || fail "$check" "anonymous permalink set a cookie"
hsts=$(tr -d '\r' < "$tmp/headers" | grep -i "^strict-transport-security:" | head -n1 | cut -d' ' -f2-)
home=$(curl --silent --max-time 30 --proto '=https' -o /dev/null --write-out '%{http_code}' "$origin/")
body_sha=$(sha256sum "$tmp/body" | cut -d' ' -f1)

write_receipt "$check" pass "at=$(utc_now)" "from=$from" "origin=$origin" "rkey=$rkey" "resolved_via_1.1.1.1=$public_a" \
  "remote_ip=$remote_ip" "status=$code" "home_status=$home" "hsts=$hsts" "time_total_seconds=$time_total" "body_sha256=$body_sha"
echo "external permalink accepted: $origin/d/$rkey 200 from $from via $remote_ip; receipt $receipt"
