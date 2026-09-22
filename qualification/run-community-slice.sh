#!/usr/bin/env bash
set -Eeuo pipefail
test "$#" = 2 -o "$#" = 4
test "$1" = --receipt
receipt=$2
case "$receipt" in /*) ;; *) exit 64;; esac
test ! -e "$receipt"
recovery_receipt=
if test "$#" = 4; then
  test "$3" = --recovery-receipt
  recovery_receipt=$4
  case "$recovery_receipt" in /*) ;; *) exit 64;; esac
  test ! -e "$recovery_receipt"
fi
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
community=${ATPROTO_COMMUNITY_ROOT:?set isolated atproto-community candidate root}
image='ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a'
run="phlog-community-$$"
scratch=$(mktemp -d /tmp/phlog-community-slice-XXXXXX)
net="$run-net"; pds="$run-pds"; participant_pds="$run-participant-pds"; plc="$run-plc"
restored_pds="$run-restored-pds"; restored_participant_pds="$run-restored-participant-pds"
cleanup() {
  docker rm -f "$pds" "$participant_pds" "$restored_pds" "$restored_participant_pds" "$plc" >/dev/null 2>&1 || true
  docker network rm "$net" >/dev/null 2>&1 || true
  for state in pds participant-pds blank/pds/community blank/pds/participant; do
    test -d "$scratch/$state" || continue
    docker run --rm --network none --entrypoint sh --mount type=bind,source="$scratch/$state",target=/state "$image" -c "chown -R $(id -u):$(id -g) /state" >/dev/null 2>&1 || true
  done
  rm -rf "$scratch"
}
trap cleanup EXIT
mkdir "$scratch/pds" "$scratch/participant-pds"
# A user-defined bridge is required for loopback port publication on this
# Docker installation. The PDS has no crawlers and every configured dependency
# is the local PLC container; the receipt verifies no external source.
docker network create "$net" >/dev/null
docker run -d --name "$plc" --network "$net" --network-alias plc -p 127.0.0.1::2582 --read-only --tmpfs /tmp --entrypoint node "$image" -e "const h=require('http');let x={};h.createServer((q,s)=>{let b='';q.on('data',v=>b+=v);q.on('end',()=>{if(q.method==='POST'){x=JSON.parse(b);s.end('{}');return}let d=decodeURIComponent(q.url.slice(1));s.setHeader('content-type','application/json');s.end(JSON.stringify({id:d,alsoKnownAs:x.alsoKnownAs||[],verificationMethod:Object.entries(x.verificationMethods||{}).map(([id,key])=>({id:id.includes('#')?id:d+'#'+id,type:'EcdsaSecp256k1VerificationKey2019',controller:d,publicKeyMultibase:key.replace(/^did:key:/,'')})),service:Object.entries(x.services||{}).map(([id,serviceEndpoint])=>({id:id.includes('#')?id:d+'#'+id,type:'AtprotoPersonalDataServer',serviceEndpoint}))}))})}).listen(2582)" >/dev/null
docker run -d --name "$pds" --network "$net" -p 127.0.0.1::3000 --read-only --tmpfs /tmp --mount type=bind,source="$scratch/pds",target=/app/data   -e PDS_HOSTNAME=localhost -e PDS_PORT=3000 -e PDS_DEV_MODE=true   -e PDS_DATA_DIRECTORY=/app/data -e PDS_BLOBSTORE_DISK_LOCATION=/app/data/blocks   -e PDS_INVITE_REQUIRED=false -e PDS_CRAWLERS= -e PDS_DID_PLC_URL=http://plc:2582   -e PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX=0000000000000000000000000000000000000000000000000000000000000001   -e PDS_JWT_SECRET=synthetic-community-jwt-not-production   -e PDS_ADMIN_PASSWORD=synthetic-community-admin-password "$image" >/dev/null
docker run -d --name "$participant_pds" --network "$net" -p 127.0.0.1::3000 --read-only --tmpfs /tmp --mount type=bind,source="$scratch/participant-pds",target=/app/data   -e PDS_HOSTNAME=localhost -e PDS_PORT=3000 -e PDS_DEV_MODE=true   -e PDS_DATA_DIRECTORY=/app/data -e PDS_BLOBSTORE_DISK_LOCATION=/app/data/blocks   -e PDS_INVITE_REQUIRED=false -e PDS_CRAWLERS= -e PDS_DID_PLC_URL=http://plc:2582   -e PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX=0000000000000000000000000000000000000000000000000000000000000002   -e PDS_JWT_SECRET=synthetic-participant-jwt-not-production   -e PDS_ADMIN_PASSWORD=synthetic-participant-admin-password "$image" >/dev/null
for attempt in $(seq 1 20); do
  docker exec "$pds" node -e "fetch('http://127.0.0.1:3000/xrpc/_health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1 && docker exec "$participant_pds" node -e "fetch('http://127.0.0.1:3000/xrpc/_health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1 && break
  test "$attempt" != 20 || exit 1
  sleep 1
done
pds_port=$(docker port "$pds" 3000/tcp | sed 's/.*://')
participant_pds_port=$(docker port "$participant_pds" 3000/tcp | sed 's/.*://')
plc_port=$(docker port "$plc" 2582/tcp | sed 's/.*://')
export PYTHONPATH="$root/src:$community/packages/community-model/src:$community/packages/communityd/src:$community/packages/communitywatch/src:$community/packages/communitywatch-web/src"
export PYTHON="$community/../../atproto-community/.venv/bin/python"
export PHLOGISTON_SOURCE_COMMIT=$(git -C "$root" rev-parse HEAD)
export COMMUNITY_SOURCE_COMMIT=$(git -C "$community" rev-parse HEAD)
"$PYTHON" "$root/qualification/community_slice.py" \
  --pds-origin "http://127.0.0.1:$pds_port" \
  --participant-pds-origin "http://127.0.0.1:$participant_pds_port" \
  --plc-origin "http://127.0.0.1:$plc_port" \
  --pds-image "$image" \
  --root "$scratch/run" \
  --receipt "$receipt"
test -s "$receipt"

if test -n "$recovery_receipt"; then
  # Freeze both PDSes before attesting or copying their SQLite and blob state.
  docker stop --time 30 "$pds" "$participant_pds" >/dev/null
  for state in pds participant-pds; do
    docker run --rm --network none --entrypoint sh --mount type=bind,source="$scratch/$state",target=/state "$image" -c "chown -R $(id -u):$(id -g) /state" >/dev/null
  done
  "$PYTHON" -m phlogiston_appview.integrated_recovery checkpoint \
    --database "$scratch/run/authority.sqlite3"
  mkdir "$scratch/blank"
  cat >"$scratch/public.json" <<EOF
{"schema":"phlogiston.community-config.v1","pds_image":"$image","projection":"reconstructible","session_state":"reenrollable"}
EOF
  "$PYTHON" -m phlogiston_appview.integrated_recovery attest \
    --output "$scratch/quiescence.json" \
    --community-pds "$scratch/pds" \
    --participant-pds "$scratch/participant-pds" \
    --authority-journal "$scratch/run/authority.sqlite3" \
    --runtime "stopped Docker containers $pds,$participant_pds"
  "$PYTHON" -m phlogiston_appview.integrated_recovery capture \
    --archive "$scratch/community-recovery.tar" \
    --community-pds "$scratch/pds" \
    --participant-pds "$scratch/participant-pds" \
    --authority-journal "$scratch/run/authority.sqlite3" \
    --public-config "$scratch/public.json" \
    --quiescence "$scratch/quiescence.json" \
    --phlogiston-source "$PHLOGISTON_SOURCE_COMMIT" \
    --community-source "$COMMUNITY_SOURCE_COMMIT" \
    --pds-image "$image"
  "$PYTHON" -m phlogiston_appview.integrated_recovery restore \
    --archive "$scratch/community-recovery.tar" \
    --destination "$scratch/blank"
  "$PYTHON" -m phlogiston_appview.integrated_recovery reconcile \
    --archive "$scratch/community-recovery.tar" \
    --destination "$scratch/blank"

  docker run -d --name "$restored_pds" --network "$net" -p 127.0.0.1::3000 --read-only --tmpfs /tmp --mount type=bind,source="$scratch/blank/pds/community",target=/app/data \
    -e PDS_HOSTNAME=localhost -e PDS_PORT=3000 -e PDS_DEV_MODE=true \
    -e PDS_DATA_DIRECTORY=/app/data -e PDS_BLOBSTORE_DISK_LOCATION=/app/data/blocks \
    -e PDS_INVITE_REQUIRED=false -e PDS_CRAWLERS= -e PDS_DID_PLC_URL=http://plc:2582 \
    -e PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX=0000000000000000000000000000000000000000000000000000000000000001 \
    -e PDS_JWT_SECRET=synthetic-community-jwt-not-production \
    -e PDS_ADMIN_PASSWORD=synthetic-community-admin-password "$image" >/dev/null
  docker run -d --name "$restored_participant_pds" --network "$net" -p 127.0.0.1::3000 --read-only --tmpfs /tmp --mount type=bind,source="$scratch/blank/pds/participant",target=/app/data \
    -e PDS_HOSTNAME=localhost -e PDS_PORT=3000 -e PDS_DEV_MODE=true \
    -e PDS_DATA_DIRECTORY=/app/data -e PDS_BLOBSTORE_DISK_LOCATION=/app/data/blocks \
    -e PDS_INVITE_REQUIRED=false -e PDS_CRAWLERS= -e PDS_DID_PLC_URL=http://plc:2582 \
    -e PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX=0000000000000000000000000000000000000000000000000000000000000002 \
    -e PDS_JWT_SECRET=synthetic-participant-jwt-not-production \
    -e PDS_ADMIN_PASSWORD=synthetic-participant-admin-password "$image" >/dev/null
  for attempt in $(seq 1 20); do
    docker exec "$restored_pds" node -e "fetch('http://127.0.0.1:3000/xrpc/_health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1 && docker exec "$restored_participant_pds" node -e "fetch('http://127.0.0.1:3000/xrpc/_health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1 && break
    test "$attempt" != 20 || exit 1
    sleep 1
  done
  restored_pds_port=$(docker port "$restored_pds" 3000/tcp | sed 's/.*://')
  restored_participant_pds_port=$(docker port "$restored_participant_pds" 3000/tcp | sed 's/.*://')
  "$PYTHON" "$root/qualification/verify_restored_community.py" \
    --community-pds-origin "http://127.0.0.1:$restored_pds_port" \
    --participant-pds-origin "http://127.0.0.1:$restored_participant_pds_port" \
    --root "$scratch/blank" \
    --output "$recovery_receipt" \
    --expected "$receipt" \
    --archive "$scratch/community-recovery.tar"
  docker stop --time 30 "$restored_participant_pds" >/dev/null
  "$PYTHON" "$root/qualification/verify_restored_community.py" \
    --community-pds-origin "http://127.0.0.1:$restored_pds_port" \
    --participant-pds-origin "http://127.0.0.1:$restored_participant_pds_port" \
    --root "$scratch/blank" \
    --output "$recovery_receipt.next" \
    --prior "$recovery_receipt"
  mv "$recovery_receipt.next" "$recovery_receipt"
  test -s "$recovery_receipt"
fi
