#!/bin/sh
set -eu

test "$#" = 10
test "$1" = --output
output=$2
test "$3" = --store
store=$4
test "$5" = --store-manifest
store_manifest=$6
test "$7" = --oauth-tarball
oauth_tarball=$8
test "$9" = --community-commit
community_commit=${10}

case "$output:$store:$store_manifest:$oauth_tarball" in
  /*:/*:/*:/*) ;;
  *) echo "all paths must be absolute" >&2; exit 64 ;;
esac
test ! -e "$output"
test -d "$store"
test -f "$store_manifest"
test -f "$oauth_tarball"
case "$community_commit" in
  *[!0-9a-f]*|'') exit 64 ;;
esac
test "${#community_commit}" = 40

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
test -z "$(git -C "$root" status --porcelain)" || {
  echo "source worktree must be clean" >&2
  exit 1
}
phlogiston_commit=$(git -C "$root" rev-parse HEAD)
scratch=$(mktemp -d /tmp/phlogiston-release-build-XXXXXX)
cleanup() { rm -rf "$scratch"; }
trap cleanup EXIT HUP INT TERM

generated_store_manifest="$scratch/store-manifest.tsv"
(cd "$store" && find . -type f -print0 | sort -z | xargs -0 sha256sum) >"$generated_store_manifest"
cmp "$store_manifest" "$generated_store_manifest"
store_manifest_sha256=$(sha256sum "$store_manifest" | cut -d' ' -f1)

oauth_sha256=$(sha256sum "$oauth_tarball" | cut -d' ' -f1)
test "$oauth_sha256" = ab145aa3394dff0e00bfb87f6ed4df1fcb9c7bb932104bd619d0e95be8485eed
oauth_sri=$(openssl dgst -sha512 -binary "$oauth_tarball" | base64 -w0)
test "$oauth_sri" = XEJS6GMk5mG136FVcoSzzFynnMKGsJ3J2Z0oVWotwkYdCyawN1UCoxtKalMqzFRSsk6uWyiNKig1OK+XwC+weQ==
test "$(tar -xOf "$oauth_tarball" package/package.json | node -e "let d='';process.stdin.on('data',x=>d+=x).on('end',()=>process.stdout.write(JSON.parse(d).version))")" = 0.0.0-spaces-alpha-20260818163953

mkdir "$scratch/source" "$scratch/release"
git -C "$root" archive "$phlogiston_commit" | tar -x -C "$scratch/source"
(
  cd "$scratch/source/web"
  pnpm install --offline --frozen-lockfile --ignore-scripts --store-dir "$store"
  pnpm run build
  pnpm install --prod --offline --frozen-lockfile --ignore-scripts --store-dir "$store"
)

release="$scratch/release/phlogiston"
mkdir -p "$release/web" "$release/python" "$release/deploy"
cp -a "$scratch/source/web/dist" "$scratch/source/web/node_modules" "$release/web/"
cp "$scratch/source/web/package.json" "$scratch/source/web/pnpm-lock.yaml" "$release/web/"
cp -a "$scratch/source/src/phlogiston_appview" "$release/python/"
cp -a "$scratch/source/deploy/production/." "$release/deploy/"
cp "$scratch/source/README.md" "$scratch/source/PROVENANCE.md" "$release/"
python3 "$scratch/source/deploy/build_release_manifest.py" \
  --root "$release" \
  --phlogiston-commit "$phlogiston_commit" \
  --community-commit "$community_commit" \
  --store-manifest-sha256 "$store_manifest_sha256" \
  --oauth-tarball-sha256 "$oauth_sha256" \
  --output "$release/release-manifest.json"

tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
  -C "$scratch/release" -czf "$output" phlogiston
sha256sum "$output"
