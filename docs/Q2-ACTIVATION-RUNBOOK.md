# Q2 activation runbook — Phase 2 external trial

> [Frozen deployment handoff](FROZEN-DEPLOYMENT-HANDOFF.md) supplies the exact
> qualified archive identities and current hard gates. **DO NOT DEPLOY or enroll
> credentials before all three gates are satisfied.** Q2 is approved.

Current initial integration uses the accepted artifact and gates in
[CURRENT-INTEGRATION-STANDING.md](CURRENT-INTEGRATION-STANDING.md).
The external cohort actions below remain prepared for a separate authorized
trial; they are not additional initial-integration owner inputs.

Status: **prepared, not executed.** Nothing here is authorized by this
document. Each action below names the authority it waits for. The order is
the real dependency order; do not reorder to save time. Every action lists
its rollback command, the state it preserves, and the state that would need
reconciliation after a rollback.

Conventions: `<community>` is the verified installed PCV0 source/kit path at
`/opt/atproto-community`; `<release>` is the immutable retained artifact;
`<stage>` is a separate writable installation copy, including its app and pnpm
store; `<venv>` is the approved Python 3.12 environment; `<campaign>` is
`/var/lib/pcv0-campaign`. Bind community source, builder source and archive hash
from the accepted manifest in [current standing](CURRENT-INTEGRATION-STANDING.md).
Commands run as root unless stated. Receipts are secret-free.

For the current initial integration, bind the prepared authority and consenting
participant/room records directly. External-cohort authorization in action 1
and invitations in action 7 apply only to a separately authorized broader trial;
they add no owner input to the initial integration. Actions 2–6 retain the
existing mechanical deployment, rollback and verification order.

## Preconditions (all must hold before action 1)

| # | Precondition | Evidence |
| --- | --- | --- |
| P1 | Q2 observation window closed with an uncontaminated closeout receipt (`atproto.q2-closeout.v1`, `uncontaminated: true`, `ended_at` = the configured `not_before`, which is `2026-09-27T16:54:28Z` in `deployment.json.example`) | `/etc/phlogiston/q2-closeout.json` |
| P2 | Prepared integration identities and second-person/moderator role consent plus notification-room consent accepted. Recover existing facts mechanically; the full external-trial packet is required only for that separately authorized trial. | exact participant/consent records, acceptance row |
| P3 | Lexicon publication complete per the PCV0 README gate (all eight exact documents in the selected publisher manifest, `_lexicon.community.phlogiston.app` TXT resolving to the schema authority DID, publisher receipt with URI/CID/readback for every document) | publisher receipt |
| P4 | PCV0 integration identities recorded; the supervised two-account integration receipt validated `--complete` | `<campaign>/integration-receipt.json` |
| P5 | Host-loss reconstruction inputs retained, small current operational state recorded, and secret custody receipt approved. Existing backup/restore evidence is useful hardening; no off-site key or total-site-loss gate. | retained release/configuration/state and `/etc/phlogiston/secret-custody.json` |
| P6 | Verified artifact manifest binds community runtime source `ed107ed7ed5025ba62c75afa970525eed3bf1707`, builder `80a868973903d7e5ec478b6e112dbb6147a04923` and the accepted archive hash; later documentation tips are not replacement runtime pins. | archive hash and verifier readback |
| P7 | The room's incoming webhook URL is in the operator's custody and nowhere in any repository | operator statement |
| P8 | DNS as recorded in [DNS-CUTOVER-PREP.md](DNS-CUTOVER-PREP.md): `phlogiston.app` → host; product-owned Lexicon TXT/handle bindings; static explainer block replaced only during admitted integration | `dig` |

## Actions in dependency order

### 1. Authorize the external cohort (owner; atproto-community `BUILD.md` amendment)

PCV0 says internal dogfood is the only human trial and PCV2 authorizes no
public trial. The external Phase 2 cohort needs its own `BUILD.md` amendment
in atproto-community naming the accepted participant packet and the Q2
receipt, with `humanDogfood.status` moved off `BLOCKED_MISSING_PARTICIPANTS`
only for the cohort the amendment names.

- Command: none on the host. A commit to atproto-community's `BUILD.md`,
  recorded in the campaign record.
- Rollback: revert the amendment commit; set the campaign status back to
  `BLOCKED_MISSING_PARTICIPANTS`.
- State preserved: everything (no host change).
- Reconciliation after rollback: any invitation already sent must be
  withdrawn in the room by the owner.

### 2. Deploy the PCV0 kit at the exact pins

Prerequisite: action 1. From the PCV0 README "Host preflight and startup".

Use the accepted closed artifact, not editable source installs. Verify its
archive hash and run `verify-communitywatch-release.py` against the exact
community and builder pins before installing. Retain the current generation,
configuration identities and rollback path. Install the eight wheels into the
approved Python 3.12 virtual environment using `pip install --no-index --no-deps`
and require `pip check`; reconstruct community-live from its packaged source and
store in a separate writable `<stage>` copy with `pnpm install --offline --frozen-lockfile --trust-lockfile
--ignore-scripts --store-dir <stage>/pnpm-store`. Place that tree at the
existing PCV0 unit path and require `node_modules/.bin/tsx` executable.
The retained installed-artifact smoke procedure supplies exact target-runtime
and verifier bindings. It already passed; host activation still requires this
runbook's genuine authority/identity gates. Do not rebuild merely to wait.

Install the units and configuration from the kit examples, substituting the
accepted moderator DID, UIDs, `COMMUNITY_NAME`, `COMMUNITY_PURPOSE`,
`COMMUNITY_PUBLIC_URL=https://phlogiston.app`, and the notifier's
`public_base_url` and webhook URL, with `umask 077`. Mask the withdrawn
phlogiston unit: `systemctl mask phlogiston-communityd.service`.

- Rollback: `systemctl disable --now` any unit installed here; remove the
  unit files under `/etc/systemd/system/`; `systemctl daemon-reload`.
- State preserved: `/var/lib/communityd`, `/var/lib/communitywatch`,
  `/var/lib/community-web`, `/var/lib/community-policy`,
  `/var/lib/community-notify`, `/etc/atproto-community` (all left in place).
- Reconciliation after rollback: none if no service started. If any started,
  see action 6.

### 3. Validate the bundle and run the host preflight

Prerequisite: action 2.

```sh
<venv>/bin/python <community>/deploy/public-community-pcv0/validate_deployment.py \
  validate-bundle --repository-root <community>
<venv>/bin/python <community>/deploy/public-community-pcv0/validate_deployment.py \
  validate-campaign <campaign>/campaign.json --ready
<venv>/bin/python <community>/deploy/public-community-pcv0/validate_deployment.py \
  host-preflight --campaign <campaign>/campaign.json
systemd-analyze verify /etc/systemd/system/communityd.service \
  /etc/systemd/system/communitywatch-index.service /etc/systemd/system/communitywatch-web.service \
  /etc/systemd/system/community-policy.service /etc/systemd/system/community-live.service \
  /etc/systemd/system/community-notify.service
```

Also run the phlogiston preflight for its own double-writer and
fragment guards, even though phlogiston-web is not routed:
`python3 /opt/phlogiston/current/deploy/preflight.py --config /etc/phlogiston/deployment.json`
(it refuses while `deployment_authorized` is false or before `not_before`;
that refusal is expected until P1 and the owner's authorization).

- Rollback: none needed (read-only).
- State preserved: all.
- Reconciliation: a refusal here stops the runbook; fix the named input and
  restart from action 2.

### 4. Install the PCV0 Caddy fragment for phlogiston.app and verify TLS

Prerequisite: action 3 passed. The site block routes `phlogiston.app` to
`127.0.0.1:3210`. `community-live` need not be running for Caddy to load the
site and obtain the certificate, but requests will 502 until action 5.

```sh
stamp=$(date -u +%Y%m%dT%H%M%SZ)
cp --preserve=mode,timestamps <caddyfile> <caddy_backup_dir>/Caddyfile.before-pcv0.$stamp
sha256sum <caddy_backup_dir>/Caddyfile.before-pcv0.$stamp > <caddy_backup_dir>/Caddyfile.before-pcv0.$stamp.sha256
# The old phlogiston-web site block for phlogiston.app, if present, must be
# removed in the same edit: one site block per hostname.
grep -n 'phlogiston.app' <caddyfile>
# append the PCV0 fragment (or replace the old phlogiston.app block with it)
docker cp <caddyfile> caddy:/tmp/Caddyfile.candidate
docker exec caddy caddy validate --config /tmp/Caddyfile.candidate
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
openssl s_client -connect phlogiston.app:443 -servername phlogiston.app </dev/null 2>/dev/null |
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName
curl -sI https://phlogiston.app/           # 502 until community-live starts; TLS must already succeed
```

- Rollback: `cp <caddy_backup_dir>/Caddyfile.before-pcv0.$stamp <caddyfile>`;
  `docker exec caddy caddy validate --config /etc/caddy/Caddyfile`;
  `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`.
- State preserved: all service state; Caddy's certificate store.
- Reconciliation after rollback: none. No DNS was changed.

### 5. Start the services, one at a time

Prerequisite: action 4. Check each journal before the next.

```sh
systemctl start communityd.service            && journalctl -u communityd -n 20 --no-pager
systemctl start communitywatch-index.service  && journalctl -u communitywatch-index -n 20 --no-pager
systemctl start communitywatch-web.service    && curl -s http://127.0.0.1:8080/health
systemctl start community-policy.service      && journalctl -u community-policy -n 20 --no-pager
systemctl start community-live.service        && curl -s http://127.0.0.1:3210/healthz
systemctl start community-notify.service      && journalctl -u community-notify -n 20 --no-pager
curl -sI https://phlogiston.app/               # 200 now
```

Enable (`systemctl enable`) only after the production verification in
action 6 passes. `community-notify` baselines on first start: it records the
events that already exist and announces nothing; only events after this
start reach the room.

- Rollback: `systemctl stop community-notify community-live community-policy communitywatch-web communitywatch-index communityd`, in that order.
- State preserved: all `/var/lib/*` stores, the authority journal, the
  notifier cursor.
- Reconciliation after rollback: if `communityd` committed any authority
  record before the stop, that record exists in the community actor's
  repository and is reflected by the observer on the next start; nothing to
  undo (removal is itself a record). If the notifier sent a line to the
  room, the room keeps it; say so in the room.

### 6. Production-only verification

Prerequisite: action 5. Run the checks in
[PRODUCTION-VERIFICATION.md](PRODUCTION-VERIFICATION.md) with
`PHLOGISTON_PRODUCTION_VERIFY=1` and a receipt path each. The identity
resolution, indexing-lag, notification-idempotence and permalink checks run
now; the OAuth continuity check is scheduled here and reports after its
window. Then run the PCV0 README's technical verification once as the
operator (`submit → admit → visible → audit entry`) with the operator's own
integration identity.

- Rollback: stop the services (action 5 rollback). The controlled
  submission created by the indexing-lag check is left unadmitted by the
  moderator, or removed if admitted; the operator's own test post can be
  deleted with their usual client.
- State preserved: receipts under `<campaign>`; the notifier cursor.
- Reconciliation after rollback: the room received exactly one "pending"
  line for the controlled record; say in the room that it was the
  operator's test.

### 7. Enable units and invite the first cohort

Prerequisite: action 6 passed and its receipts recorded.
`systemctl enable communityd communitywatch-index communitywatch-web community-policy community-live community-notify`.
The owner sends the one prompt from the participant packet (section 3) to
the room. The cohort order and its per-cohort authorization are in the
packet; none grants the next.

- Rollback: `systemctl disable` the six units; stop them (action 5); the
  owner tells the room the trial is paused.
- State preserved: all; participants' posts and submission records are
  theirs and untouched.
- Reconciliation after rollback: pending submissions stay pending in the
  observer and reappear when services restart; the window clock is paused
  per [PHASE-2-TRIAL.md](PHASE-2-TRIAL.md) "Deployment blocker".

### Independent: push phlogiston `main`

The phlogiston push ([PUSH-PREPARATION.md](PUSH-PREPARATION.md)) is
independent of every action above and can happen at any time: the host runs
the phlogiston release from the immutable archive verified by
`verify-release.py`, not from the remote. Its rollback is "report and stop";
it is never force-pushed.

## What this runbook does not cover

The `phlogiston.social` PDS activation, its TLS and Horizon 0 restore
(separate operator infrastructure, not Phase 2 gates); the phlogiston-web
inert release install (`deploy-inert.sh`, optional for Phase 2 and never
`--with-status-web`); lexicon publication itself (the PCV0 README's gate);
and the end-of-window interpretation rule.
