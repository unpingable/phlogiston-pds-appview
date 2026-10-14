# Public surfaces — Phlogiston participant application

Updated 2026-10-12. Phlogiston is one ATProto social client for ordinary participation, composable feeds, intelligible attention/context and governed communities. The Cabinet remains its public exhibition; My Labels is one bounded contextual surface. The live participant implementation is atproto-community `apps/community-live`; this product repository owns deployment composition and documentation. The [product architecture](PRODUCT-ARCHITECTURE.md) states current direction and the [operational handoff](P0-IMPLEMENTATION-HANDOFF.md) identifies exact deployed source, runtime and rollback. Earlier static-prelaunch, operator-only and PD-E/plugin-first sequencing is historical, not a current gate.

## Host and route ownership

| Hostname | Current role | Boundary |
| --- | --- | --- |
| `phlogiston.app` | Active participant client: public Cabinet and signed-in reader, feeds, conversation, account context and personal tools | One application owns public navigation, OAuth client endpoints and participant sessions; anonymous Cabinet browse remains available |
| `community.phlogiston.app` | DNS-only authority for `app.phlogiston.community.*` | `_lexicon.community.phlogiston.app` TXT identifies the dedicated publisher; it is not a separate HTTP application or account provider |
| `lexicon.phlogiston.app` | Published schema authority's custom handle | Dedicated publisher `did:plc:a3fsoszyvzozh3b5yubhe52b`, hosted on `https://phlogiston.social`; handle/DNS and eight schema record readbacks are accepted campaign evidence |
| `phlogiston.social` | Separately active controlled ATProto PDS | Protocol, repository/account custody and hosted-handle namespace; no public registration, required identity migration or comprehensive recovery promise is inferred |
| `community.neutral.zone` | Superseded prototype namespace/site | No canonical Phlogiston publication or current runtime compatibility obligation |

The static explainer in `public/prelaunch/` is retained source/rollback material; it is no longer the active `.app` or PDS service. Canonical activation and static routing rollback/reapply were actually performed. Preserve historical receipts instead of relabeling them as shell qualification.

## One participant origin and account context

`https://phlogiston.app` is the canonical participant origin. The selected `community-live` runtime owns `/`, `/oauth/login`, `/oauth/callback` and `/oauth-client-metadata.json`. Reader, feeds, Community/Cabinet and My Labels share that navigation and restored account context. Exact current routes and their qualification are located through the [operational handoff](P0-IMPLEMENTATION-HANDOFF.md), rather than a frozen route inventory here. My Labels uses the qualified read-only Labelwatch query interface; that consumer's exact release/configuration and refusal semantics are bound in its own evidence.

Anonymous Cabinet browsing and pasteable discussion links remain public. Personal observations and participant-private submission status remain session-bound. Sign-in does not confer the moderator role or authority over another account. Read-only label observations do not admit/remove community posts, publish labels, mutate repositories or turn testimony into policy. Unknown observation is not an empty result.

Participants can use existing ordinary Bluesky accounts or the explicitly supported Phlogiston-hosted accounts without moving identity. The public profile excludes Juche and provider fallback. PDS-hosted account creation, credentials and protocol authorization remain independent of the application shell. My Labels does not create an additional registration requirement. Its fixed public Labelwatch source is `https://labelwatch.neutral.zone`; the released `recent_product` contract at source `f693a067e2957b395f970e2cdeb72b01e3945eee` uses `/exports?did=<restored-session-DID>&days=7` followed by `/exports?cursor=<returned-cursor>`. The `labelwatch.public-observations.v1` account/manifest, observation window and coverage are preserved; historical observed application/removal is not current effective label state. No OAuth credentials are sent to Labelwatch, and the retired404 front-door endpoint is not a fallback.

The community and sole moderator are `did:plc:yrdhg6whfezek67fchtrmqgu`, on `https://phlogiston.social`. Existing participant integration identities are separately scoped; they are not recruited-human usability evidence. The dedicated publisher identity does not inherit community moderation authority.

## Legacy operator surface and supersession

The retained product `web/` operator/status application is not publicly routed at the participant origin. Its historical withdrawal still describes a real collision: two applications cannot independently own the same root and OAuth endpoints. The prior inference that participant tools must therefore remain operator-only, use another hostname or wait for an Impro plugin is explicitly superseded by the owner's integrated application direction. The deployed implementation location is the existing participant runtime, with one session boundary.

This instruction does not reactivate a legacy status-web unit, change its cookie/client contract, or claim that an earlier standalone/plugin spike qualifies the new shell. No new operator `/admin/` entitlement or operational control surface is implied by participant authentication.

## Operational boundaries and current baseline locator

The [P0 implementation handoff](P0-IMPLEMENTATION-HANDOFF.md) is the current baseline locator for exact source, service configuration, receipts and bounded web rollback. This page records public role and authority boundaries; it does not duplicate a version-specific deployment ledger. A web-only successor must preserve authority/observer services, private state, credentials and rollback custody. Independent canonical signed-in acceptance remains separate from source checks and a deployment terminal.

The existing Docker `caddy` owns canonical TLS/routing, through a single-file bind of the host Caddyfile. `phlogiston.app` routes to loopback3211; community query remains loopback8081. A web-only source successor needs no Caddy/DNS/PDS route change. Preserve the authority socket/principals, credential/private state custody, provider configuration, other service identities and existing PDS/Constellation operational boundaries.

`phlogiston.social` remains a protocol origin; it is not an alternate participant frontend. Existing exact hosted-handle routes and TLS custody are PDS-owned. DNS-only Lexicon authority and publisher handle records do not create extra public applications. A later origin/client change requires its own identity/consent/permalink analysis; no such change is part of the unified shell.

Source qualification, durable producer results, immutable lane notices and independent root acceptance remain distinct. The campaign registry is `phlogiston-launch-readiness-20261012`; successors get new run identities. Current implementation authorization is explicit, so historical recruitment, notification-room, plugin or operator-only sequencing does not introduce a new approval gate.
