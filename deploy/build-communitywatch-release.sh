#!/bin/sh
set -eu

test "$#" = 8
test "$1" = --output
output=$2
test "$3" = --community-root
community_root=$4
test "$5" = --community-commit
community_commit=$6
test "$7" = --build-tools
build_tools=$8

case "$output:$community_root:$build_tools" in /*:/*:/*) ;; *) echo "paths must be absolute" >&2; exit 64 ;; esac
test ! -e "$output"
test "${#community_commit}" = 40
test "$(git -C "$community_root" rev-parse "$community_commit^{commit}")" = "$community_commit"
test "$(sha256sum "$build_tools/setuptools-80.9.0-py3-none-any.whl" | cut -d' ' -f1)" = 062d34222ad13e0cc312a4c02d73f059e86a4acbfbdea8f8f76b28c99f306922
test "$(sha256sum "$build_tools/wheel-0.45.1-py3-none-any.whl" | cut -d' ' -f1)" = 708e7481cc80179af0e556bbf0cc00b8444c7321e2700b8d8580231d13017248

scratch=$(mktemp -d /tmp/communitywatch-release-build-XXXXXX)
cleanup() { rm -rf "$scratch"; }
trap cleanup EXIT HUP INT TERM
mkdir "$scratch/source" "$scratch/wheels" "$scratch/release"
git -C "$community_root" archive "$community_commit" \
  packages/community-model packages/community-space-model packages/community-space-wire \
  packages/communityd packages/communitywatch packages/communitywatch-web \
  | tar -x -C "$scratch/source"
python3 -m venv "$scratch/build-venv"
"$scratch/build-venv/bin/python" -m pip install --disable-pip-version-check \
  --no-index --no-deps "$build_tools"/*.whl

for package in community-model community-space-model community-space-wire communityd communitywatch communitywatch-web; do
  SOURCE_DATE_EPOCH=0 PYTHONHASHSEED=0 "$scratch/build-venv/bin/python" -m pip wheel \
    --disable-pip-version-check --no-deps --no-build-isolation \
    --wheel-dir "$scratch/wheels" "$scratch/source/packages/$package"
done

release="$scratch/release/communitywatch"
mkdir -p "$release/wheels"
cp "$scratch/wheels"/*.whl "$release/wheels/"
python3 "$(dirname "$0")/build_communitywatch_manifest.py" \
  --root "$release" --community-commit "$community_commit" \
  --python-version "$(python3 -c 'import platform; print(platform.python_version())')" \
  --setuptools-sha256 062d34222ad13e0cc312a4c02d73f059e86a4acbfbdea8f8f76b28c99f306922 \
  --wheel-sha256 708e7481cc80179af0e556bbf0cc00b8444c7321e2700b8d8580231d13017248 \
  --output "$release/communitywatch-release-manifest.json"
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
  --hard-dereference -C "$scratch/release" -cf - communitywatch | gzip -n >"$output"
sha256sum "$output"
