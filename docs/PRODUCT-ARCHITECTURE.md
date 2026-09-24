# Phlogiston product architecture

Status: **product-direction record**. This document consolidates an approved
composition decision and sequencing. It does not by itself authorize
deployment, activation, DNS changes, account enrollment, or relay ingestion;
those remain gated by [INTEGRATION-ROADMAP.md](INTEGRATION-ROADMAP.md),
[PRE-Q2-ACTIVATION-READINESS.md](PRE-Q2-ACTIVATION-READINESS.md), and the
owning components' own campaign procedures.

## Product thesis

Phlogiston is a **community-centered ATProto product**: bounded, inspectable
communities over author-custodied posts, served from an operator-owned PDS
(`phlogiston.social`) and product surface (`phlogiston.app`), with a personal
attention-policy engine (atproto-acl / quench) and observatory-grade
provenance (labelwatch / weatherwatch / driftwatch) as first-class product
surfaces.

The composition order the architecture serves:

```text
community creates a bounded social context
    ↓
feeds decide what can be surfaced there
    ↓
quench understands lineage / exposure
    ↓
ACL lets the participant express policy over that exposure
```

Phlogiston owns **composition, product surface, and pinning**. Each component
remains an independent instrument with its own repository, qualification, and
release surface. Integration changes are made inside the owning component;
phlogiston pins the qualified revision.

## Component roles

| Component | Role in product | Boundary |
| --- | --- | --- |
| PDS (`phlogiston.social`) | Account/repo/blob hosting; stock externally supplied PDS software | Unmodified upstream behavior; no fork |
| phlogiston-web (`web/`) | Product surface: DID/OAuth login, community views, policy editor, provenance/status cards | Application-local state keyed by DID |
| `src/phlogiston_appview/` | Render, receipt, operator, community, recovery modules | Bounded application view; **not** a network-scale AppView |
| atproto-community | Community semantics: `communityd` sole authority writer; `communitywatch` verified read-only projection; `community-live` OAuth app | Pinned revision; its AGENTS.md invariants are inherited here |
| atproto-acl | Personal policy compiler/evaluator, preview, receipts; quench vocabulary when qualified | Policy effects are user-authored and receipted; observation never becomes authority |
| atproto-feeds | Feed-generator machinery template (Jetstream → rank → `getFeedSkeleton` → publish) | Community feed generators derive from this pattern in their own repo |
| labelwatch / weatherwatch / driftwatch | Provenance, network-conditions, and operational-standing read surfaces | Read-only consumption; testimony, not verdicts |
| Constellation | Read-only governed-operations projection; later one-use operations under a released profile | No remote authority federation |

Generic `app.bsky` read views are delegated to existing external AppViews. A
network-scale relay-consuming AppView remains a deferred frontier per the
integration roadmap.

## Sequencing

Revised 2026-09-24 after the workspace user-path critique
(`atproto-nutrition/USER-CRITIQUE-PHLOGISTON-PLAN-2026-09-24.md`) and the
cohesion survey (`SURVEY-WORKSPACE-COHESION-2026-09-24.md`). Both stay in
place as receipts of how this sequencing changed. The composition decision
above is unchanged; what changed is what Phase 2 measures and what must be
true before it starts.

0. **Composition baseline (pre-Q2-close).** One canonical source line (this
   repository, `main`); this document; spike-branch dispositions
   ([SPIKE-DISPOSITIONS.md](SPIKE-DISPOSITIONS.md)). Done.
1. **Activate infrastructure (post-Q2).** Inert deployment, TLS, PDS live;
   Horizon 0 cross-version restore; lexicon namespace publication
   (`zone.neutral.community.*`); PCV0 integration identities. Nothing here
   is on a participant's path: participants bring their own ATProto
   account. `phlogiston.social` is operator infrastructure (community actor,
   lexicon authority, backups), not a place people register.
2. **One legible public community: a demand experiment.** The PCV0 social
   loop deployed for a single, deliberately chosen community, run as the
   experiment specified in [PHASE-2-TRIAL.md](PHASE-2-TRIAL.md). Its
   preconditions, all pre-Q2-safe and listed there, are: one participation
   URL (`community-live`), an anonymous pasteable permalink, a visible
   submission lifecycle with the room notified on admission, existing-post
   submission with the public-post consequence stated, a named cohort and
   activity, and the behavioral success criteria below.
   `submit → admit → visible → audit entry` remains the technical
   verification of the deployment. It is not the product gate.
   **Hard gate:** the trial's interpretation rule decides whether Phase 3
   opens, the trial extends once, or work stops to reassess. Disinterest is
   never answered with more substrate.
3. **Community feed generator (S2).** The one community-lane addition that
   is legible at trial scale: an `app.bsky.feed.generator` over the
   committed admission projection, reverse-chronological, every item linking
   to the community permalink, subscribable from any ordinary Bluesky
   client. Authorized through atproto-community's BUILD.md amendment
   process; the generator record is emitted through `communityd`. This also
   closes the discovery gap: the community appears where participants
   already are. Quench and `author_exposure_decay` are **not** part of this
   phase; see "Attention-policy lane" below.
4. **Standalone surfaces that earn their existence.** phlogiston.app grows
   only where standalone is the right shape: the operator surface, service
   status and recovery standing, provenance and network-condition cards
   (labelwatch, weatherwatch, driftwatch, Constellation read-only), and
   personal attention-policy editing with preview and receipts (the
   atproto-acl host bridge). It does not become a generic Bluesky client;
   timelines, threads, profiles, notifications, and media stay with the
   client the participant already uses. See "Client surface disposition".
5. **Hardening and wider composition.** Observer-convergence measurement of
   phlogiston's own stack (lifecyclewatch's design applied inward); one
   governed operation under an applicable Constellation profile;
   allowlisted public evidence surface; recurring cross-version restore
   rehearsal.

### Attention-policy lane (parallel, own evidence gate)

Thread-origin quench and per-reader exposure decay answer firehose-scale
attention problems. A human-curated community of a few dozen items has no
such problem: everything visible was admitted by a person. Quench acts on
the reader's own timeline via `app.bsky.graph.muteThread`, which works in
every client and has nothing community-specific about it. Both therefore
dogfood on instantinternet.news and real attention-pressure surfaces, under
their own evidence gate, in atproto-acl and atproto-feeds. They compose into
phlogiston later only if real use shows the need. Nothing in the community
lane waits on them.

### Client surface disposition (PD-E)

atproto-community's `PRODUCT-DIRECTION.md` PD-E records that the preferred
reader-facing vehicle is a plugin inside the Impro Bluesky client, and that
its PD-E0 spike disproved the need for a standalone read-only frontend
(steps 1–5 passed; the write-half bridge, step 6, was never attempted and
remains gated on OQ-4). That result is not overridden here:

- For Phase 2 the participation surface is `community-live`, because it is
  the only surface with the authorized write half (OAuth-terminated,
  socket-attested requests to `communityd`). The Impro plugin has no write
  path and is not required for the trial.
- phlogiston.app is constrained to what genuinely benefits from being
  standalone (Phase 4 list). It must never be required for participation and
  never duplicates community-live.
- An Impro (or other host-client) plugin remains the preferred vehicle for a
  richer *read* experience if trial evidence shows people will not visit a
  standalone page. That decision is taken on evidence from Phase 2, not
  before.

## Where integration changes land

- **This repository**: product-surface modules, architecture/disposition
  records, deploy composition.
- **atproto-community**: S2 feed-generator door and (later) S14 membership
  records, each authorized by BUILD.md amendment; admission projection is the
  feed membership source; reverse-chron canonical projection unchanged
  ("ranking is view policy").
- **atproto-community** (Phase 2 preconditions): PCV2 in its BUILD.md —
  anonymous permalink, submission lifecycle visibility, the single room
  webhook (`community-notify`), existing-post submission and honest copy.
- **atproto-acl** (attention-policy lane): quench policy section, evaluator
  extension, `muteThread` adapter, reply-lineage retention in feed-exposure
  acquisition, exposure-decay vocabulary.
- **atproto-feeds**: generalized multi-feed dispatch as the community feedgen
  template; `root_uri` lineage exposure (attention-policy lane).
- **Watch systems and Constellation**: no modification; read-only consumption
  under their published contracts.

## Guardrails (inherited, non-negotiable)

- Observation ≠ judgment ≠ distribution policy; labels are testimony.
- `communitywatch` holds no credentials; `communityd` is the sole community
  authority writer.
- No public registration before backup/restore and migration are qualified.
- Missing acquisition means unknown/refuse, not allow.
- Semantic discourse inference is not part of any enforcement path.
- Removal from a community never deletes or mutates the author's record.

## Verification anchors

- Canonical line builds clean; 42 Python tests and 17 web tests pass;
  typecheck clean (verified 2026-09-24 on `main` at the
  community-integration merge).
- Horizon 0 cross-version restore receipt before any public registration.
- Phase-2 technical verification: external-cohort submit → admit → visible,
  with audit entry, in the single spearhead community.
- Phase-2 product evidence: the behavioral observations and interpretation
  rule in [PHASE-2-TRIAL.md](PHASE-2-TRIAL.md).
- Phase-3 evidence: one community feed generator serving `getFeedSkeleton`
  with admitted-set parity against the projection, subscribed from an
  ordinary client.
- Attention-policy lane evidence (separate): a quenched thread origin
  suppressed for that user, receipted and reversible; ACL preview
  behavior-hash parity between CLI and web.
