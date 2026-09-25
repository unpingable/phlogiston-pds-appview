#!/bin/sh
# Shared guard for the production verification checks. Every check refuses to
# run unless PHLOGISTON_PRODUCTION_VERIFY=1 is set and an absolute, not yet
# existing receipt path is given first. Nothing before the guard touches the
# network, the host, or any file. Receipts are secret-free JSON.
set -eu

verify_guard() {
  if [ "${PHLOGISTON_PRODUCTION_VERIFY:-}" != 1 ]; then
    echo "refused: set PHLOGISTON_PRODUCTION_VERIFY=1 to run a production verification check" >&2
    exit 64
  fi
  if [ "$#" -lt 2 ] || [ "$1" != --receipt ] || [ -z "$2" ]; then
    echo "refused: the first arguments must be --receipt /absolute/path.json" >&2
    exit 64
  fi
  case "$2" in
    /*) ;;
    *) echo "refused: receipt path must be absolute" >&2; exit 64 ;;
  esac
  if [ -e "$2" ]; then
    echo "refused: receipt exists: $2" >&2
    exit 64
  fi
  receipt=$2
}

utc_now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# write_receipt CHECK STATUS key=value...  (values are recorded as strings)
write_receipt() {
  python3 - "$receipt" "$@" <<'PY'
import json, sys
receipt, check, status, *pairs = sys.argv[1:]
fields = {}
for pair in pairs:
    key, _, value = pair.partition("=")
    fields[key] = value
document = {"schema": "phlogiston.production-verification.v1", "check": check, "status": status, "fields": fields}
with open(receipt, "x") as handle:
    json.dump(document, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY
  chmod 0600 "$receipt"
}

fail() {
  echo "verification failed: $2" >&2
  write_receipt "$1" fail "reason=$2" "at=$(utc_now)"
  exit 1
}
