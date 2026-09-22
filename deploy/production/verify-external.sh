#!/bin/sh
set -eu

host=phlogiston.app
dig +short A "$host"
test -z "$(dig +short AAAA "$host")"
openssl s_client -connect "$host:443" -servername "$host" -verify_return_error </dev/null 2>/dev/null |
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName
curl --fail --silent --show-error --location --proto '=https' "https://$host/healthz"
metadata=$(curl --fail --silent --show-error --proto '=https' "https://$host/oauth-client-metadata.json")
python3 -c 'import json,sys; v=json.load(sys.stdin); assert v["client_id"]=="https://phlogiston.app/oauth-client-metadata.json"; assert v["redirect_uris"]==["https://phlogiston.app/oauth/callback"]; assert v["scope"]=="atproto"' <<EOF
$metadata
EOF
test "$(curl --silent --output /dev/null --write-out '%{http_code}' --proto '=https' "https://$host/community/")" = 503
test "$(curl --silent --output /dev/null --write-out '%{http_code}' --proto '=https' "https://$host/admin/")" = 404
printf 'external inert checks accepted; no OAuth enrollment was begun\n'
