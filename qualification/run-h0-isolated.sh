#!/usr/bin/env bash
# Deterministic, disposable H0 occurrence.  No ports, production paths, or external route.
set -Eeuo pipefail
test "$#" = 2 && test "$1" = --receipt
receipt=$2
case "$receipt" in /*) ;; *) exit 64;; esac
test ! -e "$receipt" && test ! -L "$receipt" && test -d "$(dirname -- "$receipt")" && test ! -L "$(dirname -- "$receipt")"
manifest_receipt="${receipt%.json}.manifest.json"
test ! -e "$manifest_receipt" && test ! -L "$manifest_receipt"
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
image='ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a'
pds_rev='7cccef654a9d94d935deba1ee62490b316549ef6'
pds_ver='0.4.5034'
embedded_ver='0.5.34'
app_rev=$(git -C "$root" rev-parse HEAD)
run="phlog-h0-$$"
scratch=$(mktemp -d /tmp/phlogiston-h0-run-XXXXXX)
storage_before=$(df -Pk /tmp | awk 'NR==2{print $4}')
inodes_before=$(df -Pi /tmp | awk 'NR==2{print $4}')
reserve_bytes=1048576
test $((storage_before * 1024)) -gt "$reserve_bytes"
net="$run-net"; src="$run-src"; plc="$run-plc"; dst="$run-dst"
cleanup() { docker rm -f "$src" "$dst" "$plc" >/dev/null 2>&1 || true; docker network rm "$net" >/dev/null 2>&1 || true; rm -rf "$scratch"; }
trap cleanup EXIT
mkdir "$scratch/pds" "$scratch/blank"
docker image inspect "$image" --format '{{.Id}}' >/dev/null
docker network create --internal "$net" >/dev/null
docker run -d --name "$plc" --network "$net" --network-alias plc --read-only --tmpfs /tmp --entrypoint node "$image" -e "const h=require('http');let x={};h.createServer((q,s)=>{let b='';q.on('data',v=>b+=v);q.on('end',()=>{if(q.method==='POST'){x=JSON.parse(b);s.end('{}');return}let d=decodeURIComponent(q.url.slice(1));s.setHeader('content-type','application/json');s.end(JSON.stringify({id:d,alsoKnownAs:x.alsoKnownAs||[],verificationMethod:Object.entries(x.verificationMethods||{}).map(([id,key])=>({id,type:'EcdsaSecp256k1VerificationKey2019',controller:d,publicKeyMultibase:key})),service:Object.entries(x.services||{}).map(([id,serviceEndpoint])=>({id,type:'AtprotoPersonalDataServer',serviceEndpoint}))}))})}).listen(2582)" >/dev/null
envs=(-e PDS_HOSTNAME=localhost -e PDS_PORT=3000 -e PDS_DEV_MODE=true -e PDS_DATA_DIRECTORY=/app/data -e PDS_BLOBSTORE_DISK_LOCATION=/app/data/blocks -e PDS_INVITE_REQUIRED=false -e PDS_CRAWLERS= -e PDS_DID_PLC_URL=http://plc:2582 -e PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX=0000000000000000000000000000000000000000000000000000000000000001 -e PDS_JWT_SECRET=synthetic-h0-jwt-not-a-production-secret -e PDS_ADMIN_PASSWORD=synthetic-h0-admin-not-a-production-secret)
docker run -d --name "$src" --network "$net" --read-only --tmpfs /tmp --mount type=bind,source="$scratch/pds",target=/app/data "${envs[@]}" "$image" >/dev/null
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if docker exec "$src" node -e "fetch('http://127.0.0.1:3000/xrpc/_health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1; then break; fi
  test "$attempt" != 10 || exit 1
  sleep 1
done
source_json=$(docker exec "$src" node -e "(async()=>{const b='http://127.0.0.1:3000/xrpc/';const ar=await fetch(b+'com.atproto.server.createAccount',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({handle:'h0synthetic.test',email:'h0@example.test',password:'h0-password'})});if(!ar.ok)throw Error(await ar.text());const s=await ar.json();await new Promise(r=>setTimeout(r,1000));const sr=await fetch(b+'com.atproto.server.createSession',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({identifier:'h0synthetic.test',password:'h0-password'})});if(!sr.ok)throw Error(await sr.text());const session=await sr.json();const raw=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL3NwAAAABJRU5ErkJggg==','base64');const br=await fetch(b+'com.atproto.repo.uploadBlob',{method:'POST',headers:{authorization:'Bearer '+session.accessJwt,'content-type':'image/png'},body:raw});if(!br.ok)throw Error(await br.text());const blob=await br.json();const r=await fetch(b+'com.atproto.repo.createRecord',{method:'POST',headers:{authorization:'Bearer '+session.accessJwt,'content-type':'application/json'},body:JSON.stringify({repo:s.did,collection:'app.bsky.actor.profile',rkey:'self',record:{\u0024type:'app.bsky.actor.profile',displayName:'H0',avatar:blob.blob}})});if(!r.ok)throw Error(await r.text());console.log(JSON.stringify({did:s.did,uri:(await r.json()).uri,cid:blob.blob.ref.\u0024link,blob_sha256:require('crypto').createHash('sha256').update(raw).digest('hex'),blob_bytes:raw.length}))})().catch(e=>{console.error(e);process.exit(1)})")
source_json=$(docker exec -e SOURCE_JSON="$source_json" "$src" node -e "(async()=>{const b='http://127.0.0.1:3000/xrpc/',x=JSON.parse(process.env.SOURCE_JSON);const s=await (await fetch(b+'com.atproto.server.createSession',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({identifier:'h0synthetic.test',password:'h0-password'})})).json();const h=await (await fetch(b+'com.atproto.sync.getLatestCommit?did='+encodeURIComponent(x.did),{headers:{authorization:'Bearer '+s.accessJwt}})).json();console.log(JSON.stringify({...x,repo_head:h}))})().catch(e=>{console.error(e);process.exit(1)})")
source_head=$source_json
source_json=$(printf '%s' "$source_json" | python3 -c 'import json,sys; x=json.load(sys.stdin); x.pop("repo_head"); print(json.dumps(x,separators=(",",":")))')
docker stop "$src" >/dev/null
did=$(printf '%s' "$source_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["did"])')
PYTHONPATH="$root/src" python3 -m phlogiston_appview.h0_prepare prepare --root "$scratch" --did "$did"
PYTHONPATH="$root/src" python3 -m phlogiston_appview.h0_prepare attest-stopped --root "$scratch" --runtime docker-internal-only
docker run --rm --user 0 --network none --mount type=bind,source="$scratch/pds",target=/state --entrypoint /bin/sh "$image" -c 'chown -R 1000:1000 /state; find /state -type d -exec chmod 700 {} +; find /state -type f -exec chmod 600 {} +'
source_fingerprint=$(find "$scratch/pds" -type f -exec sha256sum {} + | sort | sha256sum | awk '{print $1}')
PYTHONPATH="$root/src" python3 -m phlogiston_appview.h0_prepare stage-key-attestation --source "$scratch/keys/attestation.json" --destination "$scratch/external-key.json"
PYTHONPATH="$root/src" python3 -m phlogiston_appview.h0_recovery capture --source "$scratch" --archive "$scratch/h0.tar" --run-id h0-fresh --pds-revision "$pds_rev" --pds-version "$pds_ver" --pds-image "$image" --app-revision "$app_rev" --quiescence-attestation "$scratch/quiescence.json" >"$scratch/manifest.json"
cp "$scratch/manifest.json" "$manifest_receipt"
cfg=$(sha256sum "$scratch/config/public.json" | awk '{print $1}')
start=$(date +%s%N)
PYTHONPATH="$root/src" python3 -m phlogiston_appview.h0_recovery restore --archive "$scratch/h0.tar" --destination "$scratch/blank" --max-age-seconds 3600 --key-attestation "$scratch/external-key.json" --expected-pds-revision "$pds_rev" --expected-pds-version "$pds_ver" --expected-pds-image "$image" --expected-app-revision "$app_rev" --expected-config-sha256 "$cfg" >/dev/null
end=$(date +%s%N); restore_ms=$(( (end-start)/1000000 ))
PYTHONPATH="$root/src" python3 -c "from pathlib import Path; from phlogiston_appview.h0_recovery import reconcile_restored; reconcile_restored(Path('$scratch/h0.tar'), Path('$scratch/blank'))"
PYTHONPATH="$root/src" python3 -m phlogiston_appview.h0_recovery rebuild-index --destination "$scratch/blank" >/dev/null
PYTHONPATH="$root/src" python3 -m phlogiston_appview.h0_recovery inspect --archive "$scratch/h0.tar" --expected-pds-revision "$pds_rev" --expected-pds-version "$pds_ver" --expected-pds-image "$image" --expected-app-revision "$app_rev" --expected-config-sha256 "$cfg" >/dev/null
started=$(date +%s%N)
docker run -d --name "$dst" --network none --read-only --tmpfs /tmp --mount type=bind,source="$scratch/blank/pds",target=/app/data "${envs[@]/PDS_DID_PLC_URL=http:\/\/plc:2582/PDS_DID_PLC_URL=http:\/\/127.0.0.1:9}" "$image" >/dev/null
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if docker exec "$dst" node -e "fetch('http://127.0.0.1:3000/xrpc/_health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1; then break; fi
  test "$attempt" != 10 || exit 1
  sleep 1
done
ready=$(date +%s%N); readiness_ms=$(( (ready-started)/1000000 ))
restore_json=$(docker exec -e SOURCE_JSON="$source_json" "$dst" node -e "(async()=>{const b='http://127.0.0.1:3000/xrpc/';const src=JSON.parse(process.env.SOURCE_JSON);const sr=await fetch(b+'com.atproto.server.createSession',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({identifier:'h0synthetic.test',password:'h0-password'})});if(!sr.ok)throw Error(await sr.text());const s=await sr.json();const rr=await fetch(b+'com.atproto.repo.getRecord?repo='+encodeURIComponent(src.did)+'&collection=app.bsky.actor.profile&rkey=self',{headers:{authorization:'Bearer '+s.accessJwt}});const rec=await rr.json();const br=await fetch(b+'com.atproto.sync.getBlob?did='+encodeURIComponent(src.did)+'&cid='+src.cid,{headers:{authorization:'Bearer '+s.accessJwt}});const raw=Buffer.from(await br.arrayBuffer());const got={did:src.did,uri:rec.uri,cid:rec.value.avatar.ref.\u0024link,blob_sha256:require('crypto').createHash('sha256').update(raw).digest('hex'),blob_bytes:raw.length};if(!rr.ok||!br.ok||JSON.stringify(got)!==JSON.stringify(src))throw Error('semantic correspondence');console.log(JSON.stringify(got))})().catch(e=>{console.error(e);process.exit(1)})" )
restore_json=$(docker exec -e SOURCE_JSON="$restore_json" "$dst" node -e "(async()=>{const b='http://127.0.0.1:3000/xrpc/',x=JSON.parse(process.env.SOURCE_JSON);const s=await (await fetch(b+'com.atproto.server.createSession',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({identifier:'h0synthetic.test',password:'h0-password'})})).json();const h=await (await fetch(b+'com.atproto.sync.getLatestCommit?did='+encodeURIComponent(x.did),{headers:{authorization:'Bearer '+s.accessJwt}})).json();console.log(JSON.stringify({...x,repo_head:h}))})().catch(e=>{console.error(e);process.exit(1)})")
source_json=$source_head
test "$restore_json" = "$source_json"
test "$source_fingerprint" = "$(find "$scratch/pds" -type f -exec sha256sum {} + | sort | sha256sum | awk '{print $1}')"
scratch_peak=$(du -sb "$scratch" | awk '{print $1}')
python3 - "$receipt" "$scratch/h0.tar" "$restore_ms" "$readiness_ms" "$image" "$pds_rev" "$pds_ver" "$embedded_ver" "$app_rev" "$source_json" "$restore_json" "$scratch/manifest.json" "$storage_before" "$inodes_before" "$scratch_peak" "$source_fingerprint" "$reserve_bytes" <<'PY'
import hashlib,json,os,sys
p,a,ms,rms,img,rev,ver,embedded,app,source,restored,manifest,blocks,inodes,peak,fingerprint,reserve=sys.argv[1:]
with open(a,'rb') as f: h=hashlib.sha256(f.read()).hexdigest()
with open(p,'w') as f: json.dump({'schema':'phlogiston.h0.actual-run.v1','result':'passed','archive_sha256':h,'archive_bytes':os.path.getsize(a),'manifest_sha256':hashlib.sha256(open(manifest,'rb').read()).hexdigest(),'restore_ms':int(ms),'readiness_ms':int(rms),'pds_image':img,'pds_source_revision':rev,'pds_distro_version':ver,'embedded_pds_version':embedded,'app_revision':app,'source':json.loads(source),'restored':json.loads(restored),'source_unchanged':True,'source_pds_fingerprint':fingerprint,'storage_admission':{'tmp_free_blocks_kib':int(blocks),'tmp_free_inodes':int(inodes),'scratch_peak_bytes':int(peak),'reserve_bytes':int(reserve)},'boundaries':['docker-internal-only-local-plc','restore-network-none','no-published-port']},f,sort_keys=True);f.write('\n')
PY
