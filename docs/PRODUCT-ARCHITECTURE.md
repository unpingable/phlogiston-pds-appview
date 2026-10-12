# Phlogiston product architecture

Updated 2026-10-12 under the owner's explicit instruction to implement and deploy the integrated signed-in Phlogiston application, with **My Labels first**. This instruction supersedes the earlier operator-only surface restriction, plugin-first PD-E sequencing and demand-trial prerequisite for building the participant application. It does not relabel historical trials or spikes as successful. The web-only shell successor `7851bcbff5f8e96d23a9573575b23695a3d43142 is now deployed; the Cabinet remains available. Independent canonical signed-in acceptance is recorded separately.

## Product and participant path

Phlogiston is one participant application at `https://phlogiston.app`. Its authenticated shell composes personal ATProto tools and bounded community exhibitions. A participant signs in with an existing supported ATProto account, then uses My Labels and the Cabinet from the same application navigation. My Labels is the first personal utility; the Cabinet remains a human-curated collection of author-custodied public posts, browsable without sign-in. It is an exhibition within Phlogiston rather than the definition of the entire product.

The product owns navigation, account context, presentation, disclosure and qualified component composition. Integration does not merge service authority. Personal label observations do not admit or remove community posts; admission does not turn a label into a verdict or distribution policy. Labels retain their source and meaning as testimony.

Existing ordinary Bluesky accounts and explicitly supported Phlogiston-hosted accounts work without identity migration. `phlogiston.social` is separately live PDS infrastructure, not the participant application origin or a requirement to move an account. Public PDS registration is not offered by this application. Juche is excluded from the public profile and is never a provider fallback.

## Unified authenticated shell

The current participant server is the qualified `community-live` application. The deployed successor adds the Phlogiston shell and the bounded Labelwatch consumer there; it does not route the retained legacy `web/` operator application over the same OAuth endpoints.

The shell uses the existing OAuth/session boundary and the restored session DID as the account context. My Labels presents bounded read-only observations for that account through the released Labelwatch query contract. Exact consumer configuration, transport, coverage interpretation and source revision must be bound in its implementation and deployment receipts. The actual source/deployment receipts bind the released consumer; they do not establish that a particular observation is complete.

The current released public read contract is fixed `https://labelwatch.neutral.zone`: begin with `/exports?did=<restored-session-DID>&days=7`, then read the returned `/exports?cursor=<cursor>`. Labelwatch source `f693a067e2957b395f970e2cdeb72b01e3945eee` provides the `recent_product` frontier and `labelwatch.public-observations.v1` manifest. The consumer binds both responses to the same account/manifest and uses no OAuth credentials for these public reads. Observed application/removal events on the account or its records are not a reconstructed list of currently effective labels; current state remains unknown. The retired front-door query returning404 is not an alternate API or fallback.

Missing, stale, unavailable or unqualified acquisition is shown as unknown/refused, not as an empty result or permission to act. Label source, target and available provenance remain legible. No label publication, account mutation, community authority or operator entitlement follows from viewing My Labels. The reused OAuth grant remains minimal create-submit consent; viewing My Labels adds no permission and sends no OAuth credentials to Labelwatch; any later capability requiring additional consent must use its own explicit contract.

Signed-in navigation brings the personal surface and Cabinet together. The deployed shell introduces account Home, My Labels and Settings; the anonymous root continues to show the Cabinet. Session actions move to Settings in the P0 profile. The default post-OAuth landing is account Home, while explicit return links retain their destination. Anonymous users can continue to browse the Cabinet; participant-private pages retain their session requirement. Submission still concerns an existing public post owned by the submitting account. Its public submission record, private decline and community visibility remain distinct. The UI cannot make a public submission private or delete the author's source post.

## Component roles and authority boundaries

| Component | Product role | Boundary |
| --- | --- | --- |
| Phlogiston participant shell | Unified navigation, signed-in account context, My Labels first, Cabinet exhibition | Application-local session state keyed by verified DID; no authority merely from composition |
| `community-live` | Current participant runtime and owner-authorized shell implementation location | OAuth terminates here; authenticated community actions use the socket-attested authority contract |
| `communityd` | Sole community authority writer | Only the configured moderator can admit/decline/remove; protected private decisions and uncertain operations stay with the authority journal |
| `communitywatch` and query service | Verified read-only community observation | No participant/moderator credentials, no authority writes; candidate coverage is not an admission decision |
| Labelwatch | Personal label/provenance observations for My Labels through its released read contract | Read-only consumer; testimony is not judgment, policy or community membership |
| atproto-acl / quench | Personal policy tools composed only through their qualified contracts | Policy effects and consent remain user-authored and receipted; My Labels does not implement them implicitly |
| atproto-feeds | Feed-generator component | Qualified feed behavior is separately owned; shell navigation is not a feed release |
| weatherwatch / driftwatch | Potential further observed-condition surfaces | No released UI or completeness guarantee inferred from this direction |
| `phlogiston.social` PDS | Controlled account/repository hosting | Independent protocol and private custody boundary; comprehensive restore/migration qualification remains deferred |
| Constellation | Existing operational observation and governed operations supporting ATProto | Generic tooling does not absorb PDS-specific deployment/configuration or participant authority |
| Legacy `web/` and synthetic renderer | Retained historical/operator or local qualification artifacts | Not the canonical participant runtime; no competing public OAuth origin is reactivated by this change |

The configured community and sole moderator are `did:plc:yrdhg6whfezek67fchtrmqgu`. The dedicated publisher is `did:plc:a3fsoszyvzozh3b5yubhe52b`, with `lexicon.phlogiston.app` handle and DNS-only Lexicon authority at `community.phlogiston.app`. The accepted publication binds eight unchanged schema structures. See [public surfaces](PUBLIC-SURFACES.md) and the [operational handoff](P0-IMPLEMENTATION-HANDOFF.md) for exact deployment identities and receipts.

## Current sequencing and explicit supersessions

1. Keep the active Cabinet, qualified community authority and public source/permalink behavior working.
2. The unified authenticated Phlogiston shell and **My Labels first** have been source-qualified and deployed using the existing session and released read-only Labelwatch interface. The owner has explicitly authorized this implementation and deployment now; it does not wait for a recruited cohort, another moderator, a notification room, a community feed generator or an Impro plugin.
3. Compose additional personal tools when their owning component contract and actual participant utility justify them. Do not create a generic client, policy engine, new acquisition service or operational management framework merely to populate navigation.

The earlier Phase-2/Phase-3 trial order and standalone/operator-only restriction are superseded as scheduling constraints for this owner-authorized participant application. [PHASE-2-TRIAL.md](PHASE-2-TRIAL.md), earlier readiness documents and component PD-E/PD-E0 records remain historical evidence of their stated scopes. A plugin spike does not require today's participant tools to live in another client, and is not proof that the current unified shell was tested. No plugin, feed generator, notification worker or historical host bridge is reintroduced solely to preserve that old sequence.

The retained operator `web/` cannot simply share `/`, `/oauth/*` or client metadata with the active participant server. One canonical application owns those routes. This supersedes the operator-only product decision while preserving the real route/session collision boundary.

## Integration ownership and verification

Product architecture, public surfaces and deployment composition remain product-owned. UI/session/consumer integration changes land in the owning participant runtime. Community semantics and journals remain atproto-community-owned; Labelwatch query semantics and availability remain Labelwatch-owned; personal policy and feed releases remain their components' responsibility. PDS-specific configuration/procedures/adapters stay ATProto-owned. No generic Constellation change is authorized or needed by this participant shell.

The current deployed participant web source is `7851bcbff5f8e96d23a9573575b23695a3d43142`; `b5a7ed8183385c4bf2d4c185c36bf30cc71e301a` is the retained exact web rollback. authority, observer, Node24 and dependency closure remain the `3bf402e4cf4974b5319d2f2ce0ffd76476b61b28` base generation. Source checks passed168unit/13browser and1486Python cases. Durable web-only deployment `ffd5ea53-0cb0-4d3c-8e66-4e91ee7b38e4` completed exit0; only web restarted, public collection/seed pages and anonymous401 account routes passed, with open controls and other services unchanged. This direction record does not replace those receipts or independent signed-in acceptance. Reuse the bounded web-only generation switch and preserve credentials, private state, open controls, other service identities and rollback custody.

Qualification checks the restored-account boundary, bounded read transport/parser behavior, truthful unknown/refusal, Cabinet continuity, anonymous/private route separation and actual canonical rendering. Independent acceptance is separate from source tests, a producer terminal and a lane completion notice. Historical demand evidence remains a separate claim; controlled operator identities do not demonstrate independent-human demand. Missing evidence never becomes a released guarantee.

Exploratory contextual overlays remain recorded in [TYPED-CONTEXTUAL-OVERLAYS-RESEARCH.md](TYPED-CONTEXTUAL-OVERLAYS-RESEARCH.md), outside this shell implementation. Host-loss, total-site-loss, uncertain-write recovery and comprehensive PDS migration/restore claims retain their existing bounded qualification limits.
