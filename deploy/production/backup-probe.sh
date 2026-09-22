#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "usage: backup-probe.sh BACKUP_ROOT RECEIPT" >&2
  exit 64
fi
root=$1
receipt=$2
probe_dir="$root/.phlogiston-probe"
umask 077
mkdir -p "$probe_dir"
probe="$probe_dir/probe.$$"
renamed="$probe.complete"
trap 'rm -f "$probe" "$renamed"' EXIT HUP INT TERM
printf 'phlogiston backup probe v1\n' > "$probe"
python3 -c 'import os,sys; f=open(sys.argv[1], "rb+"); f.flush(); os.fsync(f.fileno()); f.close(); d=os.open(sys.argv[2], os.O_RDONLY); os.fsync(d); os.close(d)' "$probe" "$probe_dir"
expected=$(sha256sum "$probe" | cut -d ' ' -f 1)
mv "$probe" "$renamed"
actual=$(sha256sum "$renamed" | cut -d ' ' -f 1)
[ "$expected" = "$actual" ]
rm "$renamed"
rmdir "$probe_dir" 2>/dev/null || true
python3 -c 'import datetime,json,sys; json.dump({"schema":"phlogiston.backup-custody.v1","status":"accepted","destination":"phlogiston-production","probed_at":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),"probe_sha256":sys.argv[1]},open(sys.argv[2],"x"),sort_keys=True)' "$actual" "$receipt"
chmod 0600 "$receipt"
printf '%s\n' "$receipt"
