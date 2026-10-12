# P0 candidate deployment

This packet composes the existing community P0 services. It renders files only: no service installation/start, credential enrollment, DNS, routing or publication. User authorized launch readiness and Lexicon publication; **the subsequently approved public cutover completed with both write controls paused**. The old inert status-web packet and historical recruitment gates do not govern this successor. PDS and Constellation executors remain unchanged and ATProto-owned.

## Render an exact candidate

```sh
python3 deploy/production/p0-candidate/render.py \
  --community-source /data/git/phlogiston-pds-20261011/community \
  --runtime-root /opt/phlogiston-app/releases/3bf402e4cf4974b5319d2f2ce0ffd76476b61b28/community \
  --moderator-did did:plc:yrdhg6whfezek67fchtrmqgu \
  --community-commit 3bf402e4cf4974b5319d2f2ce0ffd76476b61b28 \
  --output /absolute/new-candidate-directory
```

The accepted community and sole moderator are the controlled curator `did:plc:yrdhg6whfezek67fchtrmqgu`; the renderer refuses another moderator. Waffle `did:plc:b53udqv47g2dayvpstzdefpq` is an external participant, not the community actor. The renderer uses `git show` from the explicitly supplied final forty-digit commit, never dirty working-tree templates. The final frozen source is `3bf402e4cf4974b5319d2f2ce0ffd76476b61b28`; installation still requires exact archive verification and actual installed acceptance. Its product base is `51aa3d73a4034ae0d68d8669cbae413e78e20489`; bind the final product successor and renderer digest at staging. `candidate.json` binds every generated file, original template digests and intended runtime path. It is an inert source packet, not a runtime inventory or installed acceptance.

Four canonical unit names are reused so existing single-writer preflight applies. Dedicated principals default to `community-web-p0` UID42011, `communityd-p0` UID42013, `communitywatch-p0` UID42014. Pass explicit UIDs if the actual host census requires alternatives; never repurpose an existing UID. Daemon and web share only group `community-authority-p0`; observer is outside that group. Host principal checks resolve actual unit `User=` values against matching campaign UIDs rather than assuming names. No notifier or policy unit/config/credential is generated. The explicit combined mode uses exact `https://phlogiston.social` community custody plus ordinary Bluesky authors: app `COMMUNITY_P0_HOSTED_PDS_ORIGIN` and `COMMUNITY_P0_ALLOW_BLUESKY=true`, authority/observer `p0_hosted_pds_origin` and `p0_allow_bluesky=true`. Juche and implicit fallback stay excluded. Dedicated publisher hosting was subsequently authorized on Phlogiston, retaining `lexicon.phlogiston.app`; this hosting correction does not publish or accept a manifest.

Candidate web listens only `127.0.0.1:3211`, observer API `127.0.0.1:8081`. Its OAuth public origin remains exactly `https://phlogiston.app`; direct loopback browsing does not qualify canonical-origin OAuth. Never add a loopback OAuth override to this public-mode packet. Browser qualification needs the existing separately isolated harness or an explicitly approved canonical-origin routing transaction. The generated complete Caddy candidate now has a live consumer after explicit approval. No `.social` route changes.

## Root-owned installed preparation

Record a durable installation checkpoint before changing the host: exact host/machine identity, source/runtime/package digests, run and unit identity, config hashes, prior effective units/drop-ins, prior Caddy bytes/hash and rollback paths, credential custody metadata, capacity/aggregate admission and next authorized action. Reconcile surviving producers before retry. Root owns storage and remote mutation.

1. Stage an independently verified immutable community runtime at the recorded runtime path. It must contain `.venv-authority/bin/communityd-serve`, `.venv-observer/bin/communitywatch-index`, `.venv-observer/bin/communitywatch-web` and `apps/community-live/node_modules/.bin/tsx`, using Python3.12 and Node24+ with the reviewed dependency closure. The local source checkout has a reused node_modules link but no `.venv`; that is not a transferable installed artifact. Reuse the existing release builder/verifier and installed tools; no new installer/framework. Record executable/package inventory and distinguish immutable archive from writable installed dependency links.
2. Census users/groups, ports and all effective service units/drop-ins. A sole authority writer is required; no second installed startable `communityd-serve` unit, including retained qualification units. Do not mask/stop unrelated units blindly. Reconcile exact owner and selected actor before replacing canonical unit names. Keep old unit/config/runtime rollback copies. Ensure notifier/policy units are absent or masked; this packet does not manipulate them automatically.
3. Provision the three dedicated accounts with the exact admitted UIDs, no login shell, and a dedicated `community-authority-p0` group for daemon/web only. Create root-owned `/etc/atproto-community-p0` mode0755 so all three services can read public config; private files below override that general access. Create fresh `/var/lib/community-web-p0` owner web mode0700, `/var/lib/communityd-p0` owner daemon mode0700 and `/var/lib/communitywatch-p0` owner observer mode0700. Do not copy hosted/Juche test decisions, OAuth state or intake into these public-mode directories.
4. Install generated public `.env`, `.toml` and pause controls with root ownership, mode0644 and no service-writable parent. Both controls must initially contain exact `paused\n`. Install `/etc/atproto-community-p0/community-web-secret.env` web-owned mode0600 with one protected `COMMUNITY_SNAPSHOT_SECRET` value using secure custody; never command arguments/logs. Install `communityd-credential.json` daemon-owned mode0600 containing exactly `identifier` and `app_password` for the exact hosted curator actor, then the generated `communityd.env` path reference. Use root-enrolled curator actor credential custody, with exact normal-session DID correspondence; do not substitute waffle participant or publisher credentials. The app never reads actor credentials; observer reads neither private file.
5. Install only the four generated unit files to `/etc/systemd/system`, reconcile all drop-ins, then `systemctl daemon-reload`. Do not enable them at boot yet. Root may run paused candidate preparation after its installed-source/credential boundaries are reconciled; no public route is installed. Use `systemd-analyze verify` against the installed effective units, then start in order: communitywatch-index, communitywatch-web, communityd, community-live. Confirm actual processes/UIDs, listener binds, socket ownership/group/mode and protected state paths. All generated services cap memory512MiB/tasks128; four services can use up to2GiB memory, independently of disk budget. Record host admission, not a capacity claim.
6. Run existing community bundle validation and `host-preflight` with the actual P0 campaign and selected UIDs. Inspect the actual env/TOML, all drop-ins, no fault/resolver/test overrides, and exactly the approved hosted+Bluesky combination, no policy peer, private-state mode binding, protected pause files and actual runtime separately under community `p0/INSTALLED-ACCEPTANCE.md`. Template checks alone cannot pass this boundary. Use `curl --max-time 10 http://127.0.0.1:3211/` and the client metadata endpoint; an observer outage can legitimately produce503 while preserving the sign-in form. Never treat200 alone as useful progress. Keep both controls paused until explicitly admitted qualification.

The existing commands are:

```sh
python3 COMMUNITY_SOURCE/deploy/public-community-pcv0/validate_deployment.py validate-bundle --repository-root COMMUNITY_SOURCE --profile p0
python3 COMMUNITY_SOURCE/deploy/public-community-pcv0/validate_deployment.py validate-campaign ACTUAL_CAMPAIGN.json --ready
python3 COMMUNITY_SOURCE/deploy/public-community-pcv0/validate_deployment.py host-preflight --campaign ACTUAL_CAMPAIGN.json --unit-root /
```

Run against the exact staged source and actual host; do not redirect to a fixture unit tree and claim installed qualification.

The final P0 validator selects the hosted curator community/moderator, dedicated hosted publisher and distinct Bluesky external participant. `validate-campaign --ready` opens and binds the actual manifest, exact eight frozen schemas and record digests, manifest acceptance and publication receipt with exact references/CIDs/timestamps. This is local evidence correspondence; provider readback and independent acceptance remain separate. The renderer supplies no publication approval/evidence. Actual publisher is `did:plc:a3fsoszyvzozh3b5yubhe52b` on `https://phlogiston.social`, with dedicated `lexicon.phlogiston.app` handle/DNS custody reconciled by root. Normal-browser publisher OAuth, eight schema publications and eight independent PDS readbacks now passed; authoritative and Cloudflare TXT agree. Publication receipt SHA256 is `7016669496d50284f740d4bf6eab26db56497fcc0160e133cf66758900b2d18c`. Actual installed host preflight passed against that evidence; canonical homepage/metadata and routing rollback/reapply now pass; normal browser OAuth and seed lifecycle remain separate qualification. Product `preflight.py` remains the withdrawn status-web checker, not this candidate's installed acceptance.


## Activation and rollback transaction

Before approval, root supplies an exact activation packet: final immutable source/runtime/config identities, actual publisher/manifest/publication evidence, effective four-unit/principal/socket acceptance, actual Bluesky lifecycle and observation, bounded queue/duplicate/decline/removal/pause evidence, private-state recovery and rollback results, current Caddy original hash and candidate hash. No human cohort or notification room is added as a gate.

After explicit public-cutover approval only: preserve the complete current Caddy config and static `phlogiston.app` block; produce a complete candidate changing **only** that block to the generated `127.0.0.1:3211` route. Run `caddy validate --config <complete-candidate>` in the actual Caddy installation context. Recheck original bytes/hash immediately before install, install that exact candidate, reload the exact existing Docker container `caddy` and verify canonical TLS, metadata/callback, anonymous source/coverage behavior and static `.social` unchanged. Do not apply a fragment as if it were a complete config. Record hashes/readbacks and unit versions. Open either operator control only under its separately authorized mutation/qualification scope, using root-owned regular mode0644 objects and exact `open\n`; no pause cancels dispatched external writes.

Rollback first returns both controls to exact `paused\n` and reconciles unknown external operations read-only. Restore the retained complete Caddy original only if current bytes still match the installed candidate hash; otherwise stop and reconcile concurrent changes. Validate/reload restored routing through `docker exec caddy caddy validate` and `docker exec caddy caddy reload` and verify the prior static surface. Then stop community-live and authority, followed by observer web/index. Preserve all private intake/OAuth/decision journals and observation state; stopping or changing routes cannot undo external records or admission/removal. Restore prior exact unit/config/runtime only after its authority/state compatibility is independently established. Returning to old binaries against mutated journals is **not** automatically qualified downgrade. If no prior compatible app runtime exists, the truthful rollback is static routing plus stopped candidate, retained unknown operations and named reconciliation owner, not destructive state reset.

A bounded rehearsal can start/stop the paused loopback candidate and verify retained state/config/executable hashes without routing or remote writes; record it as that scope only. Canonical route static rollback/reapply was actually rehearsed by run33a1a105; independent acceptance remains root-owned. Retain exact source, configs, old Caddy/runtime and private journal custody while rollback/recovery consumers exist; review at campaign handoff or 2026-10-18. Root retires exact reproducible staging/test outputs only after acceptance and consumer checks.

## Exact prepared runtime inputs

Final community archive (local): campaign `packaging-797af6c2-4732-45e3-9975-8dc798dfcfdb/community-runtime.tar.gz`, SHA256 `27d0dd1f4887ae3be3542aa6b63baf7f70f326f4dd425a0744a08a15300f867e`, 20,421,923 bytes. Builder is existing clean `f8bbf3319f65a7f7774490539274d965b1c7c50e`; its v2 verifier bound 8 wheels and 7,016 files to final community source. Retained portable toolchain archive SHA256 `7f9a1e5e27e8fdc03ab40b2d17b523632ecaec3dd41cd62683796bf24014f5f1` supplies Python3.12.3, Node24.13.0 and pnpm11.11.0. It contains historical package entrypoints; do not execute them. `install-runtime.sh` uses its interpreter to create fresh separate environments and the final wheels. Observer environment refuses communityd/policy/notifier imports. The web unit explicitly selects the generation's Node24 PATH rather than the host Node22. Partial generation `INSTALLING` marker blocks every unit until `INSTALLED.json` exists.

Root-reviewed installation command, executed only under the exact durable installation checkpoint:

```sh
./install-runtime.sh \
  /var/lib/phlogiston-campaign/20261012/public-runtime-9098c1a5-44d3-4526-ba5b-d776eff22d56/target-runtime.tar.gz \
  /var/lib/phlogiston-campaign/20261012/public-runtime-9098c1a5-44d3-4526-ba5b-d776eff22d56/community-runtime.tar.gz \
  27d0dd1f4887ae3be3542aa6b63baf7f70f326f4dd425a0744a08a15300f867e \
  3bf402e4cf4974b5319d2f2ce0ffd76476b61b28 \
  /opt/phlogiston-app/releases/3bf402e4cf4974b5319d2f2ce0ffd76476b61b28
```

This installs public code/dependencies only; no users, app services, credentials or route. Keep the verified extracted release separate from mutable dependency installation and reverify it afterward. Interpreter/package versions, `pip check`, writer-package absence, actual CLI entrypoint help, Node24 built-in SQLite and complete allocated-byte/capacity samples belong in the installation receipt. Service startup and canonical OAuth remain root-owned subsequent effects.

## Actual proxy and writer coordination

The existing proxy is Docker container `caddy` using host networking, with single-file bind `/home/jbeck/atproto/Caddyfile` → `/etc/caddy/Caddyfile`. There is no host `caddy.service`; never call a guessed systemd reload. The explicitly approved route transaction changed only the phlogiston.app block and reloaded this exact container. Record both host and container-mounted full-file hashes and the current container identity. After cutover approval only, validate the complete candidate inside that same container, preserving the original config directory for any relative imports:

```sh
docker exec -i caddy sh -c 'umask 077; test ! -e /etc/caddy/Caddyfile.p0-RUN; cat > /etc/caddy/Caddyfile.p0-RUN' < /protected/Caddyfile.complete-candidate
docker exec caddy caddy validate --config /etc/caddy/Caddyfile.p0-RUN --adapter caddyfile
```

Use the exact campaign run name in place of RUN. Serialize with the actual proxy owner and establish that no other writer/reloader is active. After comparing both original hashes, write complete candidate bytes into the existing host file object; do not rename a replacement over that pathname and assume the single-file bind follows the new inode. Verify container-mounted `/etc/caddy/Caddyfile` now hashes exactly to the validated candidate, then:

```sh
docker exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
```

Rollback uses the retained complete original bytes through the same opened-file/content/readback/validation procedure, after matching the current candidate hash; it never recreates this shared proxy container or alters unrelated routes. Retire the exact inert candidate file once reload/rollback evidence has its accepted consumer custody. A failed content write or hash correspondence leaves routing indeterminate until root reconciles; do not claim a reload succeeded merely because a host pathname changed.

Root provisioned web UID42011/GID42011 with supplementary authority GID42012; daemon UID42013 with authority GID42012; observer UID42014/GID42014. Shared group name is `community-authority-p0`. Root installed principals/configs; delegated startup and public routing completed after the same-curator crow writer was safely quiesced. The existing protected normal curator credential is `/etc/phlogiston/communityd-credential.json`; only metadata was inspected, not bytes. Actor writer startup must wait for the same-curator crow qualification producer to be terminal and safely quiesced/reconciled. Pause does not cancel an already dispatched write and two concurrently active authority instances are not permitted.

## Current paused candidate receipt

All four installed services are running and enabled at boot, with both root-owned controls `paused\n`. Their actual UID/socket/metadata inspection and stop/start rehearsal passed. Existing private SQLite logical contents were unchanged; this is current-state restart evidence, not uncertain-write or enrolled-session recovery qualification. The launch campaign owns detailed public receipts.

Complete inert proxy files are root-only at `/var/lib/phlogiston-campaign/20261012/proxy-candidate-4235b1da-6bb0-4e08-b9c7-45c5aa87606f`. `candidate.Caddyfile` SHA256 is `6cb1926ec9e4fbab00d5db139d8a6f1ef2c90168f775611b3d3bc388cd25ff9f`; `rollback.Caddyfile` and the preactivation host/mounted original hash `5b783e8d7da8c43e4b8368589497a177b60967100d5e1578d97b27d1ffdba84f`. Only original byte range6274..6705 (`phlogiston.app`) changes; prefix/suffix are identical. `docker exec -i caddy caddy validate --config /dev/stdin --adapter caddyfile` passed. That preactivation validation made no live change. Subsequently approved durable run `33a1a105-f9a1-4c55-bb0f-eb7c6d2cd3fd` activated the candidate, verified canonical homepage/metadata, restored static routing with its exact baseline homepage hash, then reapplied the app candidate. Live host and mounted bytes now hash to the candidate; bound file inode was preserved, both write controls stayed paused, and no accounts or records changed. Recheck actual current identities before any later transaction.
