#!/bin/sh
# Root explicitly stages reviewed public artifacts. No units/users/credentials/routes/start.
set -eu
test "$(id -u)" = 0 || exit 64
test "$#" = 5 || { echo 'usage: install-runtime.sh PORTABLE_ARCHIVE COMMUNITY_ARCHIVE COMMUNITY_SHA256 COMMIT NEW_GENERATION' >&2; exit 64; }
portable=$1
archive=$2
archive_hash=$3
commit=$4
generation=$5
case "$portable:$archive:$generation" in /*:/*:/*) ;; *) exit 64 ;; esac
case "$generation" in *[!a-zA-Z0-9_./-]*|*/../*|*/) exit 64 ;; esac
test "${#commit}" = 40
test "${#archive_hash}" = 64
case "$commit$archive_hash" in *[!0-9a-f]*) exit 64 ;; esac
test ! -e "$generation"
test "$(sha256sum "$portable" | cut -d' ' -f1)" = 7f9a1e5e27e8fdc03ab40b2d17b523632ecaec3dd41cd62683796bf24014f5f1
test "$(sha256sum "$archive" | cut -d' ' -f1)" = "$archive_hash"
mkdir -m 755 "$generation"
printf '%s\n' 'Never start from this generation while this marker exists' > "$generation/INSTALLING"
mkdir "$generation/toolchain" "$generation/verified" "$generation/community" "$generation/community/apps"
tar -xzf "$portable" -C "$generation/toolchain"
tar -xzf "$archive" -C "$generation/verified"
toolchain="$generation/toolchain"
python="$toolchain/python3.12/bin/python3.12"
export PATH="$toolchain/node24/bin:/usr/local/bin:/usr/bin:/bin"
export PYTHONDONTWRITEBYTECODE=1
export PIP_NO_CACHE_DIR=1
release="$generation/verified/communitywatch"
builder_commit=$("$python" -c 'import json,sys;print(json.load(open(sys.argv[1]))["builder_commit"])' "$release/communitywatch-release-manifest.json")
"$python" "$release/verify-communitywatch-release.py" --root "$release" --community-commit "$commit" --builder-commit "$builder_commit"
ln -s "$toolchain" "$generation/community/toolchain"
cp -a "$release/community-live" "$generation/community/apps/community-live"
cp -a "$release/pnpm-store" "$generation/community/pnpm-store"
"$python" -m venv "$generation/community/.venv-authority"
"$python" -m venv "$generation/community/.venv-observer"
for package in community_model community_space_model community_space_wire communityd; do
    "$generation/community/.venv-authority/bin/python" -m pip install --no-index --no-deps "$release/wheels/${package}-0.1.0-py3-none-any.whl"
done
for package in community_model community_space_model community_space_wire communitywatch communitywatch_web; do
    "$generation/community/.venv-observer/bin/python" -m pip install --no-index --no-deps "$release/wheels/${package}-0.1.0-py3-none-any.whl"
done
"$generation/community/.venv-authority/bin/python" -m pip check
"$generation/community/.venv-observer/bin/python" -m pip check
"$generation/community/.venv-observer/bin/python" -c 'import importlib.util; assert all(importlib.util.find_spec(n) is None for n in ("communityd","community_policy","community_notify")); import communitywatch,communitywatch_web'
"$generation/community/.venv-authority/bin/communityd-serve" --help >/dev/null
"$generation/community/.venv-observer/bin/communitywatch-index" --help >/dev/null
"$generation/community/.venv-observer/bin/communitywatch-web" --help >/dev/null
node "$toolchain/pnpm11/bin/pnpm.cjs" --dir "$generation/community/apps/community-live" install --offline --frozen-lockfile --trust-lockfile --ignore-scripts --store-dir "$generation/community/pnpm-store"
# Recheck the retained immutable release after mutable installation in a separate tree.
"$python" "$release/verify-communitywatch-release.py" --root "$release" --community-commit "$commit" --builder-commit "$builder_commit"
printf '{"communityCommit":"%s","communityArchiveSha256":"%s","portableArchiveSha256":"%s","status":"installed-not-started"}\n' "$commit" "$archive_hash" 7f9a1e5e27e8fdc03ab40b2d17b523632ecaec3dd41cd62683796bf24014f5f1 > "$generation/INSTALLED.json"
rm "$generation/INSTALLING"
echo 'Public runtime installed without users, service changes, credentials or routes'
