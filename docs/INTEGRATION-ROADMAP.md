# Phlogiston integration and product roadmap

Status: **design research only**. This document grants no authority to build,
deploy, enroll an account, ingest a relay, change DNS, or widen the synthetic
release. Later horizons are options, not prerequisites for earlier ones.

## What Phlogiston is—and is not

The qualified Phlogiston artifact is an offline renderer over a bounded
synthetic snapshot. A plausible product may grow into a
**Phlogiston-specific client, backend, and application view**: a small service
which presents selected ATProto and Observatory data for its own users. That
does not make it a network-scale ATProto AppView.

These roles stay separate:

| Role | Owner / protocol boundary | Phlogiston relationship |
| --- | --- | --- |
| Personal Data Server (PDS) | Hosts accounts, repositories and blobs; speaks repository, identity and account XRPCs | External dependency unless a separately recovered and operated PDS is approved. `phlogiston.social` is an intended identity, not an implemented PDS. |
| Relay/firehose | Aggregates repository events and supplies a sequenced stream | External source for a future bounded indexer. Not needed for the first useful application. |
| Network AppView | Maintains broad indexes and implements application query APIs | Delegate to an existing compatible service unless a concrete Phlogiston feature proves a bounded local index is necessary. |
| Phlogiston application surface | Product-specific web/client/backend and application-local state | Intended product boundary. May compose external ATProto APIs and local read models without claiming full AppView status. |
| Feed generation, search, indexing | Ranking/query services with distinct storage, moderation, deletion and abuse costs | Delegated initially; admit one bounded service only for a named user need. |
| Moderation and labeling | Labelers publish testimony; clients and user policy decide how to consume it | Labelwatch can explain provenance. ACL can apply user policy. Phlogiston must not convert observation into authority implicitly. |
| Operational monitoring | Driftwatch, Weatherwatch and component health owners publish observations | Read-only status input. Health, account standing and authority remain separate. |
| Governance and execution custody | Constellation components describe intent, authority, admission, custody and settlement | Read-only projection first; later one-use local operations only under an applicable released profile. |
| External Bluesky-compatible services | Existing AppViews, feed generators, labelers and OAuth-protected PDSes | Explicit dependencies with their own availability and policy. Compatibility is measured, not assumed. |

## Inspected basis

This roadmap was derived from source and released contracts, not project
names. The inspected local revisions were:

| Source | Revision / contract | Relevant implemented fact |
| --- | --- | --- |
| `atproto-acl` | `4a28f787016822ce3fbd9508b035de600b99182f` | DID-bound browser OAuth; timeline and named-feed acquisition; `feed_exposure`; preview/explanation; portable envelope and behavior hash. Web lock pins `@atproto/api` 0.20.42 and `@atproto/oauth-client-node` 0.5.4. |
| Quench reconnaissance | `QUENCH-RECON-2026-09-17.md` as inspected 2026-09-21 | Deterministic thread-lineage suppression is a candidate ACL extension; no separate crawler/service is justified; native thread mute has unresolved acquisition/ownership/UX questions. |
| `labelwatch` | `de403a2a7efff030c0bd2e5f7ff09d38a02211de` | `com.atproto.label.queryLabels` ingest, evidence/probe history, receipt-bearing derivation, and a public-whitelisted account climate API. Labels are testimony, not verdicts. |
| `driftwatch` | `a066133312e2cd523d9e183a79caf0d6851c61b8` | Jetstream consumer, cursor/replay limitations, identity enrichment, decision receipts, facts export and operator status. Current restoration constraints remain external to Phlogiston. |
| `weatherwatch` | `d154848cef330c7a9749dd49a564c18489679906` | Aggregate, identity-free Jetstream observations with explicit source/freshness and publication gates; no per-account authority. |
| PDS operations | `60cf91b264b958966386114036c987fda98b7a73` | PDS software is externally supplied; current operational material documents OAuth/AppView proxy compatibility and unclosed backup/restore prerequisites. |
| Constellation | `0.1.0-alpha.6`, `reviewed-local-copy/v1`, release commit `c594ce91c927ae67b9944d068f605a559a47fcb3` | Read-only `phosphor-ng.objective-detail/v1`; objective completion, execution, health, evidence and authority remain distinct. No remote authority federation. |
| ATProto standards/lexicons used by the inspected code | OAuth; DID resolution; `app.bsky.feed.getTimeline`; `app.bsky.feed.getFeed`; `com.atproto.label.queryLabels`; repository and sync APIs | Stable DID is the application key; OAuth scopes are capability-specific; AppView responses and label streams are external inputs, not local authority. |

The private companion records observed topology, unresolved TLS/host ownership,
capacity and activation dependencies. None of those details belong in this
public-safe roadmap.

## Integration decision matrix

Every row is independently optional. “Mutation” means a possible future
effect, not present authority.

| Integration | User/operator value | Owning component | Authoritative data source | Class | Authentication / authorization | Mutation boundary | Failure and uncertainty | Storage / operating cost | Restoration dependency | Future Constellation dependency | Maturity | Smallest falsifiable qualification | Reject or postpone when |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Native ACL and Quench** | Edit, preview and understand personal attention policy across timeline, discovery, named feeds, search and notifications | ACL owns policy/evaluator/receipts; Phlogiston owns presentation and surface-specific application; Quench stays an ACL vocabulary unless evidence forces separation | User-authored portable policy, DID-bound account rules, explicitly captured `feed_exposure`, and exact surface metadata | Private by default; redacted explanations may be public only by opt-in | ATProto OAuth for account binding; read scopes for preview; separately elevated scopes for effects | `hide`, `demote`, `annotate`, `warn`, and `refuse` are distinct local results. Protocol-visible mute/thread-mute is a separate, receipted effect | Missing acquisition means unknown/refuse, not allow. Conflicts show both rules and deterministic precedence. Uncertain writes reconcile the same subject; never replay blindly | Small policy DB and bounded exposure evidence; feed-scale hydration may be material | Depends on ACL clean/browser/import qualification; Quench lineage semantics remain research | None for local preview. A governed production effect may later use an applicable narrow profile | ACL available/adaptable; Quench research needed | Same DID and portable policy produce the same behavior hash and explanation in ACL CLI and Phlogiston preview; missing root data refuses only the Quench decision | Postpone native enforcement if Phlogiston cannot obtain complete surface context or preserve ACL non-adoption/rollback invariants. Reject semantic “same discourse” inference |
| **Labelwatch** | Inspect who labeled an account/object, when, and with what freshness; understand disagreement without treating labels as truth | Labelwatch owns observation/history/receipts; Phlogiston owns read presentation; ACL alone owns any chosen local interpretation | Labelwatch public-whitelisted API, receipts, source identity, observation window and coverage state | Public aggregates; account/object evidence private unless explicitly approved | Public reads may be anonymous/rate-limited; personalized label view requires DID session and field allowlist | Initially none. Optional use as ACL input requires an explicit user rule and records the interpretation | Stale, missing, conflicting and incomplete label testimony remain visible. Absence is not “unlabeled” outside coverage | Small cache for bounded responses; no copy of raw history by default | Depends on Labelwatch collection/report restoration and archive-reader truthfulness | Read-only objective links optional; no authority dependency | Available for bounded reads; adaptable UI | Given a known apply/negate sequence, show source, order, freshness and uncertainty; disabling Labelwatch yields “unavailable,” not a clean verdict | Postpone trend surfaces if retained-history coverage is incomplete. Reject any automatic enforcement derived merely from a label appearing |
| **Driftwatch** | Operators can see ingestion, lag, storage, reconstruction and publication standing and follow anomalies to evidence/objectives | Driftwatch owns observations and archives; existing ATProto objective projection owns presentation of governed work | Driftwatch status/operations facts, cursor coverage, archive receipts, saved checks and explicit gaps | Public only through allowlisted aggregate/status projection; detailed operations private | Public read projection is anonymous; operator detail requires existing access control | No initial mutation. Later repair proposal is not execution; execution needs fresh authority/admission/custody | Service 200, current collection, publication freshness, coverage and objective completion are separate. Gaps persist explicitly | Low for read projection; high for ingestion/index/reconstruction, which stays outside Phlogiston | Directly depends on current restoration, Q5b/Q6c and sustained-growth outcome for truthful status | Alpha.6 read projection now; later repair needs a released applicable effect profile | Read projection available; repair controls deliberately deferred | Pause ingestion while serving old output: UI must show healthy serving, paused collection, stale publication and unchanged authority simultaneously | Reject direct buttons or optimistic freshness. Postpone operational control until stable growth and recovery are qualified |
| **Weatherwatch** | Explain network/service conditions that may account for delayed or partial user experience | Weatherwatch owns aggregate instrument output; Phlogiston consumes public schema only | Published aggregate cards, receipts, named observer, observation window and freshness | Public, identity-free | No user auth for public status; operator source remains separate | None initially. Any effect on feeds/notifications requires an explicit user policy and receipted decision | Missing observer, stale window or observer disagreement renders unknown/degraded; “weather” never authorizes action | Negligible cached public artifacts; no raw event copy | Independent of account migration, but depends on current publication contract | None for display; future governed config change only if a profile applies | Available for bounded display | With stale weather and healthy Phlogiston, display those states separately and do not alter ranking unless a policy explicitly says so | Reject per-account forecasts or any identity-shaped derived output. Postpone adaptive behavior without a user-authored rule |
| **Constellation** | Understand requested outcome, authority, admission, attempt, settlement, evidence, uncertainty and recovery in one read-only place | Maude/AG/Docket/Monitor/NQ/Nightshift retain their released roles; Phosphor is presentation owner; Phlogiston links or embeds an allowlisted consumer projection | Exact `reviewed-local-copy/v1` response and explicit identities/references | Public allowlist plus richer authenticated operator view | Reading needs no effect authority. Operator view uses existing access controls. Every later effect has locality, audience, scope, expiry and one-use authority | H3 only: narrowly enrolled restart/deploy/backup/restore rehearsal. No arbitrary shell; verification never grants permission | Absent/stale/conflicting records are explicit. Settled is not successful. Response loss reconciles the same occurrence | Small read projection; operational components remain independently owned | Read-only adoption is complete; legacy-NQ parity and restoration standing still constrain claims | Alpha.6 suffices for read-only. New effects require an actual released profile, not matching labels | Read-only available; mutation deliberately deferred | Render an actual occurrence with objective incomplete, stale monitoring and no reusable authority without inventing any relationship | Reject remote authority federation and generic command execution. Postpone effect enrollment until one real consumer and rollback exist |
| **Identity and account portability** | Stable sign-in, PDS migration, recovery, and portable preferences/policies without handle lock-in | PDS owns repository/account; DID method controls identity; Phlogiston owns app-private state; ACL owns policy format | DID document and authenticated OAuth subject; signed repository state; explicit export envelopes | Identity/profile partly public; sessions, preferences, subscriptions and recovery private | ATProto OAuth; bind to DID, never handle; sensitive import/recovery needs recent auth and exact target | Account-local state import/export; no DID rotation or PDS migration in early horizons | DID resolution failure freezes mutation and marks reads stale. Rotation/migration must distinguish synthetic, owner, inactive-external and active-external cohorts | Small app DB/blobs initially; PDS blobs/repos and migration overlap can dominate | H0 PDS backup/restore and recovery custody are mandatory before public registration | Optional for governed migration rehearsal; DID possession alone is never operational authority | OAuth/ACL pieces adaptable; full account migration research needed | Synthetic account survives blank-host restore with DID/repo/blob correspondence; handle change does not create a second app identity | No public registration until backup/restore and migration are qualified. Reject “has DID, therefore may administer service” |
| **Human notification** | Durable in-app history and optional delivery to an operator’s chosen channel | Phlogiston owns inbox; existing notification contract/adapter owns transport; destination owner controls enrollment | Stored notification occurrence, severity, dedupe key, expiry, attempts and acknowledgments | Private/operator; carefully selected public incident summaries separate | Session for inbox; per-destination credential and approval for external delivery | Enqueue/deliver/acknowledge are separate effects. Notification is information, not authority to act | Delivery is pending/accepted/failed/uncertain; response loss reconciles same delivery; dedupe and expiry prevent storms | Small durable inbox; adapter logs and bounded retry queue | Depends on legacy-NQ notification-owner decision, not Q2 | Later governance may authorize configuration, but receiving a message confers no authority | Local-file/deterministic adapters available; live destination unqualified | Send a bounded synthetic occurrence to a preapproved test destination, lose the response, reconcile without duplicate human delivery | Postpone live adapters without exact destination. Reject escalation loops without recipient, budget and acknowledgment semantics |
| **Public evidence, provenance and research** | Let people verify claims without reading private campaign state | Producing instrument owns evidence; Phlogiston owns allowlisted composition only | Public receipts/projections with exact source revision, observation time, coverage and schema | Public allowlist; personal/private evidence excluded by default | Anonymous read; private drill-down through established operator access only | None | Missing receipt, stale source, unsupported link and conflicting evidence are rendered as such; no filename/time inference | Static/cache-sized; research datasets remain in their owning archives | Depends on each producer’s archive/custody standing | May link to public alpha.6 qualification; no dependency for ordinary receipts | Available/adaptable | Export a public evidence bundle and prove it contains no internal paths, credentials, private URLs or account evidence while preserving source/freshness | Reject “download everything.” Postpone named-account research until authorization/privacy review and coverage are adequate |
| **Feeds, search and discovery** | A useful product surface without forcing users to leave for every query | External AppView/feed generator initially; Phlogiston owns only named product-specific transformations it can explain | `getTimeline`, named `getFeed`, approved search API, or a later bounded local index with declared source | Public content plus private viewer state | OAuth for personalized timeline/viewer state; public feeds may be anonymous | Ranking/hiding is local presentation unless a separate protocol-visible action is invoked | Incomplete page/hydration/label context must be surfaced; source outage does not fall through to an unexplained local corpus | External delegation low; local relay/index/search high and continuous | Independent read delegation can precede restoration; any local index needs capacity/retention proof | None for ordinary reads; governed index operations only later | External sources available; proprietary index deliberately deferred | Render one named feed with source identity, pagination, policy explanation and graceful unavailable state without persisting post bodies unnecessarily | Avoid rebuilding Bluesky. Build locally only if a named feature cannot be satisfied externally and its storage, abuse, deletion, moderation and DR budgets pass |
| **Backup, DR and operational portability** | Recover PDS, blobs, application state, policies and indexes without identity drift or silent partial recovery | Each component owns consistent capture; operator owns recovery set and restore order; Phlogiston documents dependencies | Application-consistent backups, manifests, immutable images, schema/version pins and restore receipts | Private operational evidence; public summary may state qualification date/result | Backup and restore are distinct operator capabilities; destructive cutover needs fresh authority | Capture, restore rehearsal, cutover and rollback are separate. Partial restore must refuse unsupported service combinations | Missing member, stale generation, version skew, wrong DID/repository correspondence or unavailable destination fails closed | Largest cost: PDS blobs/repos plus index duplication and blank-host workspace | H0 requirement; present synthetic archive is not PDS recovery | Later one-use backup/restore rehearsals may use a released local-effect profile | Synthetic archive available; live PDS/application DR not qualified | Restore a synthetic owner and an inactive external cohort on a blank host, then verify identity, repo, blobs, policies and served behavior; test partial restore refusal | No public registration or production activation without real recovery. Do not call hashes alone a restore test |

## Bounded horizons

### Horizon 0 — Recoverability

Purpose: make failure boring before inviting users.

Prerequisites:

- exact deployment identities and component ownership;
- secrets referenced but never embedded in manifests;
- application-consistent PDS, blob, policy and application-state capture;
- enough isolated capacity for source plus restore plus verification;
- synthetic accounts representing owner, ordinary local user, inactive external
  identity and active external identity.

Exit criteria:

- clean build from pinned source/image;
- blank-host restore and cross-version restore pass;
- DID, repository, blob and application-state correspondence pass;
- interruption, stale backup, partial restore and rollback cases fail safely;
- RPO and RTO are measured, not aspirational;
- teardown leaves evidence but no candidate runtime.

The present two-member synthetic archive is useful harness evidence, not H0
completion.

### Horizon 1 — Useful read-only application

Purpose: provide a bounded product without owning the network.

Prerequisites: H0; DID/OAuth session design; public/private field allowlists;
external AppView/feed dependencies; explicit freshness and cache policy.

Candidate surface:

- DID login and application-local state keyed by DID;
- public timelines or named views delegated to an external AppView/feed source;
- ACL policy import/preview/explanation without effects;
- Labelwatch testimony/provenance and Weatherwatch status;
- Driftwatch and Constellation read-only operational standing;
- clear empty, stale, partial and unavailable states.

Exit criteria: authorized synthetic and read-only production-shaped journeys,
mobile/accessibility review, no mutation controls, no private-field escape, and
source outages that do not become false clean bills of health.

### Horizon 2 — Native personal control

Purpose: let users decide what may recruit their attention.

Prerequisites: H1; ACL behavior parity and portable schema; per-surface input
coverage; action ownership/non-adoption rules; separately elevated OAuth;
rollback and reconciliation.

Candidate surface:

- native ACL editing, previews and reason explanations;
- explicit hide/demote/annotate/warn/refuse semantics;
- portable policies/preferences and conflict-safe replacement;
- Quench reply-lineage control only after root acquisition and ownership are
  qualified;
- durable in-app notifications and optional approved adapters.

Exit criteria: web/CLI behavior identity, pre-existing action non-adoption,
uncertain-write reconciliation, removal restoring expected visibility, and
complete explanations on every supported surface. Semantic discourse inference
is not part of this horizon.

### Horizon 3 — Governed operations

Purpose: allow a small set of inspectable recovery operations.

Prerequisites: stable sustained operations; H0 recovery; current monitoring;
an applicable released Constellation profile; named executor locality and
identity; one-use authority; rollback.

Candidate operations: one component restart, immutable deployment, backup, or
restore rehearsal. Each capability is enrolled separately. No remote shell and
no implied authority federation.

Exit criteria: fresh observation before action and continuation, exact
admission/custody/settlement, response-loss reconciliation, expiry/replay and
wrong-locality refusal, and independent inspection of the completed occurrence.

### Horizon 4 — Wider composition

Purpose: add integrations only where a real consumer has emerged.

Prerequisites: earlier horizons remain independently operable; explicit data
and authority contracts; sustainable storage/abuse/deletion/backup budgets.

Candidates: selective cross-application identity/evidence, one bounded local
feed or search index, and approved external notification adapters. Exit is a
falsifiable product-specific qualification—not protocol compatibility in the
abstract.

### Deferred frontier

- a full relay-consuming, network-scale AppView;
- general firehose retention and global search;
- semantic discourse-propagation enforcement;
- claim federation or authority federation;
- cross-application identity that treats DID possession as sufficient
  authority;
- any integration without an actual consumer and an owner willing to operate
  its storage, privacy, abuse and recovery obligations.

## Explicit non-goals

- No universal social identity authority.
- No automatic trust in foreign claims or labels.
- No arbitrary remote execution.
- No mandatory adoption of the entire Constellation suite.
- No replacement of mature ATProto infrastructure without a concrete product
  reason.
- No public registration before backup/restore and migration are qualified.
- No production implementation merely because this roadmap names a
  possibility.
- No conflation of a Phlogiston-specific backend with a full ATProto AppView.
- No ambient conversion of weather, monitoring, labels, evidence or
  reachability into permission.

## The intentionally boring next step

Complete Horizon 0 for a recoverable PDS and bounded application state. Then
build only the Horizon 1 read surface: DID login, delegated public views, ACL
preview, label provenance, and honest operational status. Keep Quench effects,
local indexing and governed operations behind their own evidence gates.

That sequence preserves the ambitious options while ensuring the first public
claim is modest and testable: Phlogiston can restore what it owns, show where
its data came from, and say when that claim is no longer true.
