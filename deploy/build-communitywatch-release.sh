#!/bin/sh
set -eu
export PYTHONDONTWRITEBYTECODE=1

test "$#" = 14
test "$1" = --output
output=$2
test "$3" = --community-root
community_root=$4
test "$5" = --community-commit
community_commit=$6
test "$7" = --build-tools
build_tools=$8
test "$9" = --js-store
js_store=${10}
test "${11}" = --js-store-manifest
js_store_manifest=${12}
test "${13}" = --js-store-manifest-sha256
js_store_manifest_sha256=${14}
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
test -z "$(git -C "$root" status --porcelain)" || {
  echo "builder source worktree must be clean" >&2; exit 1;
}
builder_commit=$(git -C "$root" rev-parse HEAD)
python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python3.12 required"'
node -e 'if(Number(process.versions.node.split(".")[0])<24)throw Error("Node24 required")'
test "$(pnpm --version)" = 11.11.0

case "$output:$community_root:$build_tools:$js_store:$js_store_manifest" in /*:/*:/*:/*:/*) ;; *) echo "paths must be absolute" >&2; exit 64 ;; esac
test ! -e "$output"
test "${#community_commit}" = 40
test "$(git -C "$community_root" rev-parse "$community_commit^{commit}")" = "$community_commit"
test "$(sha256sum "$build_tools/setuptools-80.9.0-py3-none-any.whl" | cut -d' ' -f1)" = 062d34222ad13e0cc312a4c02d73f059e86a4acbfbdea8f8f76b28c99f306922
test "$(sha256sum "$build_tools/wheel-0.45.1-py3-none-any.whl" | cut -d' ' -f1)" = 708e7481cc80179af0e556bbf0cc00b8444c7321e2700b8d8580231d13017248

python3 - "$root/deploy" "$js_store" "$js_store_manifest" "$js_store_manifest_sha256" <<'PYVERIFY'
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from community_release import verify_offline_tree
verify_offline_tree(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
PYVERIFY

scratch=$(mktemp -d /tmp/communitywatch-release-build-XXXXXX)
cleanup() { rm -rf "$scratch"; }
trap cleanup EXIT HUP INT TERM
mkdir "$scratch/source" "$scratch/wheels" "$scratch/release"
git -C "$community_root" archive "$community_commit" \
  packages/community-model packages/community-space-model packages/community-space-wire \
  packages/communityd packages/communitywatch packages/communitywatch-web \
  packages/community-policy packages/community-notify apps/community-live \
  | tar -x -C "$scratch/source"
python3 -m venv "$scratch/build-venv"
"$scratch/build-venv/bin/python" -m pip install --disable-pip-version-check \
  --no-index --no-deps "$build_tools/setuptools-80.9.0-py3-none-any.whl" "$build_tools/wheel-0.45.1-py3-none-any.whl"

for package in community-model community-space-model community-space-wire communityd communitywatch communitywatch-web community-policy community-notify; do
  SOURCE_DATE_EPOCH=0 PYTHONHASHSEED=0 "$scratch/build-venv/bin/python" -m pip wheel \
    --disable-pip-version-check --no-deps --no-build-isolation \
    --wheel-dir "$scratch/wheels" "$scratch/source/packages/$package"
done

release="$scratch/release/communitywatch"
mkdir -p "$release/wheels"
cp "$scratch/wheels"/*.whl "$release/wheels/"
# Source archive has no working-tree dependency shims or live configuration.
cp -a "$scratch/source/apps/community-live" "$release/community-live"
cp -a "$js_store" "$release/pnpm-store"
cp "$js_store_manifest" "$release/pnpm-store-manifest.json"
python3 - "$root/deploy" "$release/pnpm-store" "$release/pnpm-store-manifest.json" "$js_store_manifest_sha256" <<'PYVERIFY'
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from community_release import verify_offline_tree
verify_offline_tree(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
PYVERIFY
cp "$root/deploy/verify-communitywatch-release.py" "$root/deploy/community_release.py" "$release/"
python3 "$(dirname "$0")/build_communitywatch_manifest.py" \
  --root "$release" --community-commit "$community_commit" --builder-commit "$builder_commit" \
  --node-version "$(node --version)" --pnpm-version "$(pnpm --version)" \
  --python-version "$(python3 -c 'import platform; print(platform.python_version())')" \
  --setuptools-sha256 062d34222ad13e0cc312a4c02d73f059e86a4acbfbdea8f8f76b28c99f306922 \
  --wheel-sha256 708e7481cc80179af0e556bbf0cc00b8444c7321e2700b8d8580231d13017248 \
  --output "$release/communitywatch-release-manifest.json"
python3 "$release/verify-communitywatch-release.py" --root "$release" \
  --community-commit "$community_commit" --builder-commit "$builder_commit"
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
  --hard-dereference -C "$scratch/release" -cf - communitywatch | gzip -n >"$output"
sha256sum "$output"
