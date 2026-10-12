# Public surfaces — Phlogiston participant application

Updated 2026-10-12. The owner has explicitly authorized implementation and deployment of one authenticated Phlogiston shell, with My Labels first and the Cabinet retained as an exhibition. The earlier static-prelaunch, operator-only and PD-E/plugin-first sequencing descriptions are superseded as current product direction. Historical source and receipts remain evidence of their original scope.

## Host and route ownership

| Hostname | Current role | Boundary |
| --- | --- | --- |
| `phlogiston.app` | Active participant application, currently the Cabinet; owner-authorized unified shell/My Labels successor in implementation | One application owns public navigation, OAuth client endpoints and participant sessions; anonymous Cabinet browse remains available |
| `community.phlogiston.app` | DNS-only authority for `app.phlogiston.community.*` | `_lexicon.community.phlogiston.app` TXT identifies the dedicated publisher; it is not a separate HTTP application or account provider |
| `lexicon.phlogiston.app` | Published schema authority's custom handle | Dedicated publisher `did:plc:a3fsoszyvzozh3b5yubhe52b`, hosted on `https://phlogiston.social`; handle/DNS and eight schema record readbacks are accepted campaign evidence |
| `phlogiston.social` | Separately active controlled ATProto PDS | Protocol, repository/account custody and hosted-handle namespace; no public registration, required identity migration or comprehensive recovery promise is inferred |
| `community.neutral.zone` | Superseded prototype namespace/site | No canonical Phlogiston publication or current runtime compatibility obligation |

The static explainer in `public/prelaunch/` is retained source/rollback material; it is no longer the active `.app` or PDS service. Canonical activation and static routing rollback/reapply were actually performed. Preserve historical receipts instead of relabeling them as shell qualification.

## One participant origin and account context

`https://phlogiston.app` is the canonical participant origin. The selected `community-live` runtime already owns `/`, `/oauth/login`, `/oauth/callback` and `/oauth-client-metadata.json`. The unified shell extends this application rather than adding a second server or OAuth client over those same routes. My Labels and the Cabinet belong to the same participant navigation and restored account context. The authorized successor adds authenticated `/home`, `/labels` and `/settings`, with signed-in Home, Collection, My Labels, Settings and My submissions navigation. The default OAuth landing becomes `/home` while an explicit permalink return is preserved; these are pending successor behavior, not endpoints claimed deployed by this direction record. My Labels uses the qualified read-only Labelwatch query interface; that consumer's exact release/configuration and refusal semantics are bound in the successor's own evidence.

Anonymous Cabinet browsing and pasteable discussion links remain public. Personal observations and participant-private submission status remain session-bound. Sign-in does not confer the moderator role or authority over another account. Read-only label observations do not admit/remove community posts, publish labels, mutate repositories or turn testimony into policy. Unknown observation is not an empty result.

Participants can use existing ordinary Bluesky accounts or the explicitly supported Phlogiston-hosted accounts without moving identity. The public profile excludes Juche and provider fallback. PDS-hosted account creation, credentials and protocol authorization remain independent of the application shell. My Labels does not create an additional registration requirement.

The community and sole moderator are `did:plc:yrdhg6whfezek67fchtrmqgu`, on `https://phlogiston.social`. Existing participant integration identities are separately scoped; they are not recruited-human usability evidence. The dedicated publisher identity does not inherit community moderation authority.

## Legacy operator surface and supersession

The retained product `web/` operator/status application is not publicly routed at the participant origin. Its historical withdrawal still describes a real collision: two applications cannot independently own the same root and OAuth endpoints. The prior inference that participant tools must therefore remain operator-only, use another hostname or wait for an Impro plugin is explicitly superseded by the owner's integrated application direction. The current implementation location is the existing participant runtime, with one session boundary.

This instruction does not reactivate a legacy status-web unit, change its cookie/client contract, or claim that an earlier standalone/plugin spike qualifies the new shell. No new operator `/admin/` entitlement or operational control surface is implied by participant authentication.

## Operational boundaries and exact current baseline

The current web-only front door source is `b5a7ed8183385c4bf2d4c185c36bf30cc71e301a`, selected by the managed `community-live.service` drop-in and a fresh immutable web generation. Authority/observer code, Node24 and dependency closure remain the `3bf402e4cf4974b5319d2f2ce0ffd76476b61b28` base generation. All four services are boot-enabled; controls were restored open after canonical lifecycle and boundary qualification. The shell successor is authorized but is not yet deployed by this direction document. See [P0 implementation handoff](P0-IMPLEMENTATION-HANDOFF.md) for exact paths, records, tests and bounded web rollback.

The existing Docker `caddy` owns canonical TLS/routing, through a single-file bind of the host Caddyfile. `phlogiston.app` routes to loopback3211; community query remains loopback8081. A web-only source successor needs no Caddy/DNS/PDS route change. Preserve the authority socket/principals, credential/private state custody, provider configuration, other service identities and existing PDS/Constellation operational boundaries.

`phlogiston.social` remains a protocol origin; it is not an alternate participant frontend. Existing exact hosted-handle routes and TLS custody are PDS-owned. DNS-only Lexicon authority and publisher handle records do not create extra public applications. A later origin/client change requires its own identity/consent/permalink analysis; no such change is part of the unified shell.

Source qualification, durable producer results, immutable lane notices and independent root acceptance remain distinct. The campaign registry is `phlogiston-launch-readiness-20261012`; successors get new run identities. Current implementation authorization is explicit, so historical recruitment, notification-room, plugin or operator-only sequencing does not introduce a new approval gate.
