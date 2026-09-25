#!/bin/sh
set -eu

# Phase 2 deploys phlogiston-web only. The community runtime (communitywatch
# observer, communityd) is owned by the atproto-community PCV0 kit and is
# neither extracted nor installed unless --with-community-runtime is given.
with_community_runtime=0
if [ "$#" -ge 1 ] && [ "$1" = "--with-community-runtime" ]; then
  with_community_runtime=1
  shift
fi
if [ "$#" -ne 1 ]; then
  echo "usage: deploy-inert.sh [--with-community-runtime] /etc/phlogiston/deployment.json" >&2
  exit 64
fi
config=$1
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$script_dir/preflight.py" --config "$config"

if [ "$(id -u)" -ne 0 ]; then
  echo "refused: deploy-inert.sh must run as root after preflight acceptance" >&2
  exit 1
fi

read_config() {
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$config" "$1"
}
phlog_archive=$(read_config phlogiston_artifact)
phlog_sha=$(read_config phlogiston_artifact_sha256)
phlog_commit=$(read_config phlogiston_source_commit)
community_commit=$(read_config community_source_commit)
community_archive=$(read_config communitywatch_artifact)
community_sha=$(read_config communitywatch_artifact_sha256)
install_root=$(read_config install_root)
community_root=$(read_config community_install_root)
caddyfile=$(read_config caddyfile)
caddy_backup_dir=$(read_config caddy_backup_dir)
caddy_container=$(read_config caddy_container)

phlog_release="$install_root/releases/$phlog_sha"
observer_release="$community_root/releases/$community_sha"
[ ! -e "$phlog_release" ] || { echo "refused: release target exists" >&2; exit 1; }
if [ "$with_community_runtime" -eq 1 ]; then
  [ ! -e "$observer_release" ] || { echo "refused: release target exists" >&2; exit 1; }
fi

getent group phlogiston >/dev/null 2>&1 || groupadd --system phlogiston
id phlogiston >/dev/null 2>&1 || useradd --system --gid phlogiston --home-dir /var/lib/phlogiston --shell /usr/sbin/nologin phlogiston
install -d -m 0755 "$install_root/releases" /etc/phlogiston /var/lib/phlogiston
chown phlogiston:phlogiston /var/lib/phlogiston

mkdir "$phlog_release"
tar -xzf "$phlog_archive" -C "$phlog_release" --strip-components=1
python3 "$phlog_release/deploy/verify-release.py" --root "$phlog_release" --phlogiston-commit "$phlog_commit" --community-commit "$community_commit"

install -m 0644 "$phlog_release/deploy/phlogiston-web.service" /etc/systemd/system/phlogiston-web.service
install -m 0600 "$phlog_release/deploy/phlogiston-web.env.example" /etc/phlogiston/phlogiston-web.env
ln -s "$phlog_release" "$install_root/current.new"
mv -T "$install_root/current.new" "$install_root/current"

if [ "$with_community_runtime" -eq 1 ]; then
  # Not used for Phase 2: the PCV0 kit owns communitywatch and communityd.
  getent group phlogiston-observer >/dev/null 2>&1 || groupadd --system phlogiston-observer
  id phlogiston-observer >/dev/null 2>&1 || useradd --system --gid phlogiston-observer --home-dir /var/lib/phlogiston-communitywatch --shell /usr/sbin/nologin phlogiston-observer
  install -d -m 0755 "$community_root/releases" /var/lib/phlogiston-communitywatch
  chown phlogiston-observer:phlogiston-observer /var/lib/phlogiston-communitywatch
  mkdir "$observer_release"
  tar -xzf "$community_archive" -C "$observer_release" --strip-components=1
  python3 "$script_dir/../verify-communitywatch-release.py" --root "$observer_release" --community-commit "$community_commit"
  python3 -m venv "$observer_release/venv"
  "$observer_release/venv/bin/pip" install --no-index --no-deps "$observer_release"/wheels/*.whl
  install -m 0644 "$phlog_release/deploy/phlogiston-communitywatch.service" /etc/systemd/system/phlogiston-communitywatch.service
  install -m 0644 "$phlog_release/deploy/communitywatch.toml.example" /etc/phlogiston/communitywatch.toml.inert
  ln -s "$observer_release" "$community_root/current.new"
  mv -T "$community_root/current.new" "$community_root/current"
fi

systemctl daemon-reload
systemctl enable --now phlogiston-web.service
curl --fail --silent --show-error http://127.0.0.1:8092/healthz
curl --fail --silent --show-error http://127.0.0.1:8092/oauth-client-metadata.json >/dev/null
status=$(curl --silent --output /dev/null --write-out '%{http_code}' http://127.0.0.1:8092/community/)
[ "$status" = 503 ] || { echo "refused: inert community route returned $status" >&2; exit 1; }

install -d -m 0700 "$caddy_backup_dir"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
caddy_backup="$caddy_backup_dir/Caddyfile.before-phlogiston.$stamp"
cp --preserve=mode,timestamps "$caddyfile" "$caddy_backup"
sha256sum "$caddy_backup" > "$caddy_backup.sha256"
candidate=$(mktemp /tmp/phlogiston-Caddyfile.XXXXXX)
trap 'rm -f "$candidate"' EXIT HUP INT TERM
python3 "$script_dir/render-caddy.py" --current "$caddyfile" --fragment "$phlog_release/deploy/Caddyfile.fragment" --output "$candidate"
docker cp "$candidate" "$caddy_container:/tmp/Caddyfile.phlogiston-candidate"
docker exec "$caddy_container" caddy validate --config /tmp/Caddyfile.phlogiston-candidate
cp "$candidate" "$caddyfile"
if ! docker exec "$caddy_container" caddy validate --config /etc/caddy/Caddyfile; then
  cp "$caddy_backup" "$caddyfile"
  docker exec "$caddy_container" caddy validate --config /etc/caddy/Caddyfile
  echo "refused: installed Caddyfile failed validation and was restored" >&2
  exit 1
fi
docker exec "$caddy_container" caddy reload --config /etc/caddy/Caddyfile
curl --fail --silent --show-error https://phlogiston.app/healthz

receipt="/var/lib/phlogiston/inert-deployment-$stamp.json"
python3 -c 'import json,sys; json.dump({"schema":"phlogiston.inert-deployment-receipt.v1","artifact_sha256":sys.argv[1],"communitywatch_sha256":sys.argv[2],"community_runtime_installed":sys.argv[5]=="1","caddy_backup":sys.argv[3],"activated_accounts":0,"community_mutations":0},open(sys.argv[4],"x"),sort_keys=True)' "$phlog_sha" "$community_sha" "$caddy_backup" "$receipt" "$with_community_runtime"
chmod 0600 "$receipt"
echo "inert application and public route accepted; no account or community activation occurred"
