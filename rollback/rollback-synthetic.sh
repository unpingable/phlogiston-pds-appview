#!/usr/bin/env bash
# Selection-only rollback preparation; no server, symlink, or DNS mutation.
set -Eeuo pipefail
test "$#" = 2
test "$1" = --inspect-only
test -f "$2/receipt.json"
grep -Fq '"network_contacted":false' "$2/receipt.json"
sha256sum "$2/index.html" "$2/receipt.json"
