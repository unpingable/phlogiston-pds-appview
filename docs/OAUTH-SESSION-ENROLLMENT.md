# OAuth and session enrollment

Status: qualified in isolated tests; not activated.

Phlogiston uses the official `@atproto/oauth-client-node` client pinned in
`web/pnpm-lock.yaml`. The requested scope is exactly `atproto`; this component
does not request repository-write, community-authority, moderation, or PDS
administration grants.

## Three separate states

1. **PDS identity/custody** — a DID and its OAuth session prove control of an
   ATProto account. The OAuth client discovers the account's PDS and persists
   DPoP/session material server-side.
2. **Phlogiston session** — the browser receives only a random opaque
   `phlogiston_session` cookie. Its hashed record is stored with a creation
   time, CSRF secret, DID, and an eight-hour limit. Every authenticated request
   restores the upstream OAuth session; revoked, expired, or invalid provider
   state invalidates the local session.
3. **Community authority** — membership comes only from the communitywatch
   projection of community authority records. Fresh absence is `not-member`.
   Stale or unavailable projection state is `indeterminate`. OAuth completion
   never creates membership or admission.

`POST /session/logout` removes only the local Phlogiston session.
`POST /session/disconnect` invokes the OAuth client's provider sign-out and
then removes the local session. Both require the session-bound CSRF token.
OAuth state, OAuth sessions, and web sessions live in mode-0700/0600 server
storage and never enter integrated community backups; users re-enroll after a
blank-host restore.

## Multi-PDS and failure behavior

The OAuth client resolves the supplied handle/DID and talks to the discovered
authorization server. There is no configured single-PDS shortcut. A PDS or
authorization-server failure during enrollment returns dependency-unavailable
and creates no local session. A valid session with unavailable communitywatch
remains authenticated while its membership is explicitly indeterminate.

Production still requires published HTTPS client metadata, an exact callback,
key and cookie-secret custody, clean-environment dependency installation, and
a separately authorized synthetic/owner enrollment.
