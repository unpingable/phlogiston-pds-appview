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

Install an immutable release under `/opt/phlogiston/releases/<sha256>/`, verify
`release-manifest.json`, and atomically point `/opt/phlogiston/current` to that
directory. Create service user `phlogiston`; install the unit and an owner-only
environment file at `/etc/phlogiston/phlogiston-web.env`; require the exact
community DID before startup. `/var/lib/phlogiston` is the only writable web
state path and contains server-side OAuth/DPoP and opaque web sessions.

Start the read-only communitywatch successor first, then Phlogiston web, then
validate local `/healthz` and client metadata. Only afterward may a separately
approved transaction add and reload the Caddy fragment. The fragment contains
no `phlogiston.social` route because PDS installation/identity is a separate
effect.

Rollback removes the Caddy fragment, reloads the previously captured complete
Caddyfile, stops/disables the unit, and points `current` back to the retained
prior immutable release. Preserve `/var/lib/phlogiston`; rollback never treats
session deletion as database recovery and never touches community/PDS records.
