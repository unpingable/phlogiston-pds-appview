#!/usr/bin/env bash
# Emits the exact removable local target; it never performs removal itself.
set -Eeuo pipefail
test "$#" = 2
test "$1" = --inspect-only
case "$2" in /tmp/phlogiston-*) ;; *) echo 'refusing non-campaign target' >&2; exit 2;; esac
printf 'operator-approved-removal-target=%s\n' "$2"
