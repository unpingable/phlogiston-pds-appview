# Inert production deployment packet

This packet installs no service by itself. It contains only the Phlogiston
OAuth/read surface. It creates no PDS account, OAuth enrollment, membership,
admission, moderation action, record, or Lexicon.

The intended allocation on the shared host is:

| Component | Boundary |
|---|---|
| Phlogiston web | systemd `phlogiston-web.service`, `127.0.0.1:8092` |
| communitywatch web/API | separate read-only unit, proposed `127.0.0.1:8093` |
| future Phlogiston PDS | separate container/unit and loopback port; deliberately unset |
| communityd | separate authority-bearing unit over a peer-authenticated Unix socket |
| Caddy | existing shared container/config, route only `phlogiston.app` to 8092 |

The existing `pds` container is Juche custody and is not reusable. The existing
`atproto-community-demo` is retained evidence and is not the production
authority/projection. `/admin/` remains outside this unit: its application
logic is qualified, but a production operator-authentication bridge has not
been authorized or implemented. Do not expose it by manufacturing a session.

The separately activated PDS template pins the qualified upstream image by
digest, binds only `127.0.0.1:3002`, and stores its independent state under
`/var/lib/phlogiston-pds`. The community runtime archive contains both the
read-only projection packages and `communityd`; the latter remains a separate
unit, Unix-socket authority boundary, credential and journal. Neither PDS nor
communityd is installed or started by the inert deployment script.

Install an immutable release under `/opt/phlogiston/releases/<sha256>/`, verify
the archive SHA-256 before extraction, then run `deploy/verify-release.py`
against the extracted directory with both exact source commits. Atomically
point `/opt/phlogiston/current` to that directory only after verification.
Create service user `phlogiston`; install the unit and an owner-only
environment file at `/etc/phlogiston/phlogiston-web.env`. The inert generation
must omit `PHLOGISTON_COMMUNITY_DID`; membership is then explicitly
indeterminate and `/community/` refuses with 503 without contacting the
observer. Add the exact DID and start communitywatch only through the later
community-activation authority. `/var/lib/phlogiston` is the only writable web
state path and contains server-side OAuth/DPoP and opaque web sessions.

Immediately before deployment, the off-host backup operator must issue the
fresh custody receipt described in `docs/PRODUCTION-BACKUP-CONTRACT.md`; the
production host has no direct NFS mount. Start Phlogiston web without
communitywatch, then validate local `/healthz`, client metadata, and the
expected `/community/` refusal. Communitywatch is
packaged and configured off-host but remains stopped until an exact community
DID and observer database exist. Only afterward may a separately
approved transaction add and reload the Caddy fragment. The fragment contains
no `phlogiston.social` route because PDS installation/identity is a separate
effect.

Rollback removes the Caddy fragment, reloads the previously captured complete
Caddyfile, stops/disables the unit, and points `current` back to the retained
prior immutable release. Preserve `/var/lib/phlogiston`; rollback never treats
session deletion as database recovery and never touches community/PDS records.

The production-order packet is deliberately inert: observer, web, local health,
then an independently approved Caddy transaction. Account enrollment,
membership, publication, and PDS activation are separate effects and remain
disabled. If the Q2 observation window is active, do not install the release,
units, configuration, or route because those changes alter the observed host.
