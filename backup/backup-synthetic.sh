#!/usr/bin/env bash
# Archive a verified synthetic render only. Never accepts a PDS path.
set -Eeuo pipefail
test "$#" = 6
test "$1" = --synthetic-only
output=$2
receipt=$3
snapshot=$4
archive=$5
renderer=$6
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
PYTHONPATH="$project_dir/src" exec python3 -m phlogiston_appview.archive backup \
  --output "$output" --receipt "$receipt" --snapshot "$snapshot" --archive "$archive" --renderer "$renderer"
