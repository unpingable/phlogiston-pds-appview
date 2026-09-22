#!/usr/bin/env bash
# Restore an archive only into a new /tmp target, then require its receipt.
set -Eeuo pipefail
test "$#" = 3
test "$1" = --synthetic-only
archive=$2
target=$3
test -f "$archive"
test ! -e "$target"
case "$target" in /tmp/*) ;; *) echo 'target must be under /tmp for local qualification' >&2; exit 2;; esac
install -d -m 0700 "$target"
tar --extract --file "$archive" --directory "$target"
test -f "$target/index.html"
grep -Fq '"production_changed":false' "$target/receipt.json"
