#!/usr/bin/env bash
# Restore a two-member archive into a new run-owned child and verify every binding.
set -Eeuo pipefail
test "$#" = 6
test "$1" = --synthetic-only
archive=$2
target_root=$3
run_id=$4
snapshot=$5
renderer=$6
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
PYTHONPATH="$project_dir/src" exec python3 -m phlogiston_appview.archive restore \
  --archive "$archive" --target-root "$target_root" --run-id "$run_id" --snapshot "$snapshot" --renderer "$renderer"
