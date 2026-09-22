#!/usr/bin/env bash
# Archive a verified synthetic render only. Never accepts a PDS path.
set -Eeuo pipefail
test "$#" = 3
test "$1" = --synthetic-only
source_dir=$2
archive=$3
test -d "$source_dir"
test -f "$source_dir/receipt.json"
test ! -e "$archive"
grep -Fq '"network_contacted":false' "$source_dir/receipt.json"
grep -Fq '"production_changed":false' "$source_dir/receipt.json"
case "$archive" in /tmp/*) ;; *) echo 'archive must be under /tmp for local qualification' >&2; exit 2;; esac
tar --create --file "$archive" --directory "$source_dir" index.html receipt.json
