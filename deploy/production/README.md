# Inert deployment packet

This packet installs no service by itself. It contains only the Phlogiston
OAuth/read surface. It creates no PDS account, OAuth enrollment, membership,
admission, moderation action, record, or Lexicon.

The Phase 2 allocation on the shared host (decided 2026-09-25; see
`docs/PHASE-2-TRIAL.md` "Deployment topology") is:

| Component | Owner | Boundary |
|---|---|---|
| Phlogiston web | this packet | systemd `phlogiston-web.service`, `127.0.0.1:8092`; the only unit this packet installs; **withdrawn from public routing for Phase 2** (installed, not enabled, no Caddy route unless `--with-status-web`) |
| communitywatch observer (index + web) | atproto-community PCV0 kit | `127.0.0.1:8080`; phlogiston-web reads it unchanged via `PHLOGISTON_PROJECTION_ORIGIN` |
| communityd, community-policy, community-live, community-notify | atproto-community PCV0 kit | PCV0 units, users, paths and credential; not installed here |
| Phlogiston PDS (`phlogiston.social`) | separate activation | `127.0.0.1:3002`; operator infrastructure, not on the participant path, not required for Phase 2 |
| community-live at `https://phlogiston.app` | atproto-community PCV0 kit | the participant origin; its Caddy site block (`phlogiston.app` → `127.0.0.1:3210`) is the PCV0 kit's fragment, not this packet's |
| Caddy | existing shared container/config | this packet installs no site block in Phase 2; `Caddyfile.fragment` is withdrawn (comment only) |

Two-kit rule: exactly one communityd per community DID holds the actor
credential, and for Phase 2 that is the PCV0 kit's `communityd.service`, so
this packet's `phlogiston-communityd.service`, `phlogiston-communitywatch.service`
and their `.toml.example` files are withdrawn (kept for the record, header-marked,
never to be enabled beside PCV0) and `preflight.py` refuses when any other
installed unit starts `communityd-serve` or when `phlogiston-communityd.service`
is installed and not masked. The single README for the community services is
atproto-community `deploy/public-community-pcv0/README.md`; the community actor
is the Bluesky-hosted `did:plc:b53udqv47g2dayvpstzdefpq`, not a
`phlogiston.social` account.

`deploy-inert.sh` extracts the community runtime archive and installs the
withdrawn communitywatch unit only with the explicit `--with-community-runtime`
flag, which defaults off. Phase 2 does not use it.

Public routing (decided 2026-09-25, superseding the earlier front-door memo;
see `docs/PUBLIC-SURFACES.md`): `https://phlogiston.app` is the participant
origin and is served by the PCV0 kit's `community-live` on `127.0.0.1:3210`.
phlogiston-web collides with it on `/` and `/oauth/*`, so for Phase 2 it is
withdrawn from public routing: `phlogiston-web.service` is header-marked,
`Caddyfile.fragment` defines no site block, `deploy-inert.sh` installs the
release and unit file but enables the unit and runs the Caddy transaction only
with the explicit `--with-status-web` flag (default off), and `preflight.py`
refuses if this packet's fragment defines a `phlogiston.app` site. With the
flag, the fragment must define a site block for a distinct hostname; the
script refuses `phlogiston.app`, `phlogiston.social` and `*.phlogiston.social`.
`PHLOGISTON_COMMUNITY_URL` stays optional and is unused in Phase 2 because
phlogiston.app itself is the community. A default (flagless) deployment writes
`status_web_enabled: false` and `public_route_installed: false` into its
receipt; rolling it back needs no Caddy step, only `systemctl disable --now
phlogiston-web.service` (a no-op), removal of the unit file, and repointing
`current`, because `rollback-inert.sh` expects a Caddy backup that a flagless
deployment never creates.

The existing `pds` container is Juche custody and is not reusable. The existing
`atproto-community-demo` is retained evidence and is not the production
authority/projection. `/admin/` remains outside this unit: its application
logic is qualified, but a production operator-authentication bridge has not
been authorized or implemented. Do not expose it by manufacturing a session.

The separately activated PDS template pins the qualified upstream image by
digest, binds only `127.0.0.1:3002`, and stores its independent state under
`/var/lib/phlogiston-pds`. The community runtime archive contains both the
read-only projection packages and `communityd`; for Phase 2 it is pinned by
the preflight but not extracted, because the PCV0 kit provides both. Neither
PDS nor communityd is installed or started by the inert deployment script.

Install an immutable release under `/opt/phlogiston/releases/<sha256>/`, verify
the archive SHA-256 before extraction, then run `deploy/verify-release.py`
against the extracted directory with both exact source commits. Atomically
point `/opt/phlogiston/current` to that directory only after verification.
Create service user `phlogiston`; install the unit and an owner-only
environment file at `/etc/phlogiston/phlogiston-web.env`. The inert generation
must omit `PHLOGISTON_COMMUNITY_DID`; membership is then explicitly
indeterminate and `/community/` refuses with 503 without contacting the
observer. Add the exact DID (the PCV0 community DID) only through the later
community-activation authority; the observer it points at is PCV0's. `/var/lib/phlogiston` is the only writable web
state path and contains server-side OAuth/DPoP and opaque web sessions.

Current recovery scope is host-loss reconstruction of a zero-user deployment:
retain the exact source/releases and configuration, approved credential custody
or reenrollment records, and small operational state. There is no current
irreplaceable user repository state or PDS continuity promise. Off-host backup,
geographic key custody and a fresh backup/restore rehearsal are optional
hardening, not inert-launch prerequisites. Total-site-loss recovery is outside
this qualified envelope. Revisit user-data/PDS DR when actually hosting user
state or promising durability. Existing historical backup/rehearsal receipts
remain useful evidence and are not altered. Juche offers technical examples
only; its operational posture and user commitments are not Phlogiston policy.

With `--with-status-web` only: start Phlogiston web, then validate local
`/healthz`, client metadata, and the expected `/community/` refusal. The observer is the PCV0 kit's
`communitywatch-web` on `127.0.0.1:8080`, started under that kit's own
procedure; nothing in this packet starts it. Only afterward may a separately
approved transaction add and reload the Caddy fragment, and in Phase 2 there
is none to add. The fragment contains no `phlogiston.social` route because
PDS installation/identity is a separate effect.

Rollback removes the Caddy fragment, reloads the previously captured complete
Caddyfile, stops/disables the unit, and points `current` back to the retained
prior immutable release. Preserve `/var/lib/phlogiston`; rollback never treats
session deletion as database recovery and never touches community/PDS records.

The production-order packet is deliberately inert: web, local health,
then an independently approved Caddy transaction. Account enrollment,
membership, publication, and PDS activation are separate effects and remain
disabled. If the Q2 observation window is active, do not install the release,
units, configuration, or route because those changes alter the observed host.

## Build and install the current community artifact

The ordinary `deploy/build-communitywatch-release.sh` now packages the eight
PCV0 hot wheels, immutable `apps/community-live` source/static/package/lockfile,
and exact closed offline pnpm store under the existing `communitywatch/`
archive root. It requires Python3.12, Node24+ and pnpm11.11.0; pass the retained
build-tools wheels and verified `atproto.offline-tree.v1` store input:

```sh
deploy/build-communitywatch-release.sh --output /absolute/community-release.tar.gz \
  --community-root /absolute/atproto-community --community-commit <exact-commit> \
  --build-tools /absolute/build-tools --js-store /absolute/closed-pnpm-store \
  --js-store-manifest /absolute/pnpm-store-manifest.json \
  --js-store-manifest-sha256 <exact-manifest-sha256>
```

The builder refuses a dirty builder worktree, verifies the two pinned Python
build-tool wheels and complete store inventory, builds all eight wheels from
the supplied Git commit without network/build isolation, and records both the
community and Phlogiston builder revisions. It includes its standalone verifier.
The v2 inventory is the current artifact; retained six-wheel v1 archives remain
historical evidence and do not satisfy current PCV0 release completeness.

Verify the externally retained archive SHA256 before extracting into a new
immutable generation, then invoke its bundled verifier with both exact sources:

```sh
python3 /absolute/generation/verify-communitywatch-release.py \
  --root /absolute/generation --community-commit <exact-community-commit> \
  --builder-commit <exact-phlogiston-builder-commit>
cp -a /absolute/generation /absolute/staging-generation
python3.12 -m venv /absolute/runtime-venv
/absolute/runtime-venv/bin/python -m pip install --no-index --no-deps \
  /absolute/staging-generation/wheels/*.whl
/absolute/runtime-venv/bin/python -m pip check
cd /absolute/staging-generation/community-live
pnpm install --offline --frozen-lockfile --trust-lockfile --ignore-scripts \
  --store-dir /absolute/staging-generation/pnpm-store
pnpm typecheck
```

Perform installation in a disposable staging copy after verifying the immutable
generation: pnpm creates local dependency links and project tracking metadata.
Do not rerun release verification against that mutated runtime tree and claim
it remains the sealed inventory. Keep the verified generation retained, and
have the existing PCV0 action bind its staged runtime/executables and configuration
before activation. `--trust-lockfile` applies only to the already reviewed,
digest-bound canonical lockfile: pnpm11 otherwise rechecks registry policy even
with `--offline` on a fresh cache. The locked package bytes remain fully verified;
there is no dependency resolution change or global setting modification.

Use the PCV0 units/users/state/credential scopes and normal-mode configuration
from atproto-community `deploy/public-community-pcv0/README.md`. Fill and validate
the actual approved authority/participant/publication records and run
`validate_deployment.py validate-campaign --ready` before real activation.
Packaging and a local synthetic smoke do not supply that authority or consent.
The inert deployment still installs no community writer or public route by
default; PCV0 owns the sole communityd and participant origin. Current recovery
remains zero-user host-loss reconstruction, with no new backup/offsite gate.
