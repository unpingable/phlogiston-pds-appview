#!/bin/sh
# Campaign-owned wrapper around the existing exact release builder; no install/network.
set -eu
test "$#" = 5 || { echo 'usage: prepare-runtime.sh COMMUNITY_ROOT COMMIT NEW_RUN_DIRECTORY CLEAN_BUILDER OLD_INPUT_DIRECTORY' >&2; exit 64; }
community=$1
commit=$2
run=$3
builder=$4
inputs=$5
case "$community:$run:$builder:$inputs" in /*:/*:/*:/*) ;; *) exit 64 ;; esac
test ! -e "$run"
test "${#commit}" = 40
test "$(git -C "$community" rev-parse "$commit^{commit}")" = "$commit"
test -z "$(git -C "$builder" status --porcelain)"
test "$(sha256sum "$builder/deploy/build-communitywatch-release.sh" | cut -d' ' -f1)" = 2b3b87f44c16f9a4edbea41cccb93fbb2c10f243e37e1085a22677745be470d0
mkdir -m 700 "$run"
exec >>"$run/producer.log" 2>&1
trap 'code=$?; printf "exit=%s\n" "$code" > "$run/TERMINAL"' EXIT
printf '%s\n' preparing > "$run/PHASE"
# Reuse retained wrappers; avoid corepack latest lookup and any dependency resolution.
export PATH="$inputs/bin:/home/jbeck/.nvm/versions/node/v24.13.0/bin:/usr/local/bin:/usr/bin:/bin"
export PYTHONDONTWRITEBYTECODE=1
export PIP_NO_CACHE_DIR=1
store_manifest="$inputs/offline-community-store-manifest.json"
store_digest=$(sha256sum "$store_manifest" | cut -d' ' -f1)
"$builder/deploy/build-communitywatch-release.sh" \
  --output "$run/community-runtime.tar.gz" \
  --community-root "$community" --community-commit "$commit" \
  --build-tools "$inputs/offline-build-tools" \
  --js-store "$inputs/offline-community-store-tree" \
  --js-store-manifest "$store_manifest" --js-store-manifest-sha256 "$store_digest"
printf '%s\n' sealed > "$run/PHASE"
sha256sum "$run/community-runtime.tar.gz" > "$run/community-runtime.sha256"
