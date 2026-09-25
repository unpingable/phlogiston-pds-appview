# Inert deployment readiness

> **Superseded for Phase 2 (2026-09-25).** The topology below (an
> activated `communitywatch` on `127.0.0.1:8093` and a phlogiston-owned
> `communityd` unit) is kept as the record it was; for Phase 2 the
> atproto-community PCV0 kit owns every community service, the observer is
> its `communitywatch-web` on `127.0.0.1:8080`, the community actor is a
> Bluesky-hosted account, and phlogiston deploys only phlogiston-web. See
> [PHASE-2-TRIAL.md](PHASE-2-TRIAL.md) "Deployment topology".

Observed 2026-09-22. This is a readiness record, not activation authority.

## Intended topology

`phlogiston.app` terminates at the existing Caddy boundary and proxies only to
the Phlogiston OAuth/read service on `127.0.0.1:8092`. That service talks to a
separate read-only `communitywatch` API on `127.0.0.1:8093`. Community effects
remain owned by `communityd` over its separately authenticated local interface.
The future `phlogiston.social` PDS remains a distinct state, key, backup, and
service boundary; it is not the existing Juche PDS and has no route in this
packet.

The web service stores only server-side OAuth/DPoP material and opaque browser
sessions in `/var/lib/phlogiston`. Projection authority remains in the
community system. The qualified integrated backup/restore contract covers
community authority and reconstructible projection separately; deploy rollback
preserves every state path and never substitutes an older database after new
writes.

## Current external observations

Both intended hostnames resolved to the intended production IPv4 address with
no observed AAAA or CNAME record. Neither hostname completed a TLS handshake:
the shared ingress returned a TLS internal-error alert and no certificate.
There was no matching Caddy route, Phlogiston unit, runtime directory, or
service listener. Ports 8092 and 8093 were available at inspection time.

Therefore DNS presence is not deployment, TLS is not ready, and no external
OAuth/community smoke test has passed. The exact production metadata will be:

- client ID: `https://phlogiston.app/oauth-client-metadata.json`
- callback: `https://phlogiston.app/oauth/callback`
- client URI: `https://phlogiston.app`
- scope: `atproto`

The production `/admin/` application logic is qualified separately, but this
artifact intentionally has no operator-session issuance or HTTP adapter. It
must remain unavailable until that narrow authentication boundary is designed
and authorized.

## Inert deployment gate

1. Q2 must be closed or the operator must establish a non-contaminating host
   boundary; current evidence does not establish one.
2. Verify the immutable archive SHA-256 and embedded file manifest after
   transfer; retain the current empty state and exact rollback commands.
3. Install distinct service identities, owner-only configuration references,
   state directories, observer state, and verified backup destination.
4. Start read-only communitywatch, then Phlogiston web; check local health and
   exact metadata without beginning OAuth.
5. Back up the complete existing Caddyfile byte-for-byte, validate the full
   candidate configuration, add only the `phlogiston.app` route, and reload.
6. Verify DNS identity, certificate chain/hostname, redirects, metadata,
   callback routing without authorization completion, `/community/` refusal or
   empty-state behavior, restart ordering, persistence paths, backup access,
   and rollback artifact availability.

Any account, membership, admission, moderation action, record, Lexicon, or PDS
identity operation remains a later explicit boundary. The existing
`atproto-community-demo` is evidence, not production authority.
