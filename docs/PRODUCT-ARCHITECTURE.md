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

0. **Consolidation (pre-Q2-close).** One canonical source line (this
   repository, `main`); this document; spike-branch dispositions
   ([SPIKE-DISPOSITIONS.md](SPIKE-DISPOSITIONS.md)).
1. **Activate infrastructure (post-Q2).** Inert deployment, TLS, PDS live;
   Horizon 0 cross-version restore; lexicon namespace publication
   (`zone.neutral.community.*`); PCV0 integration identities.
2. **One legible public community.** The PCV0 social loop deployed for a
   single, deliberately chosen community — not "a platform." Success is a
   qualitatively new piece of evidence: *someone who isn't the operator
   joins one.*
   **Hard gate:** if external users can use it and demonstrably don't want
   to, stop. Do not answer disinterest with more substrate.
3. **Community feeds + integrated attention policy.** Per-community feed
   generators (atproto-community slice S2, authorized via its BUILD.md
   amendment process); reply-lineage acquisition (`reply.root`/`reply.parent`)
   enabling deterministic quench; atproto-acl quench vocabulary with
   `muteThread` adapter; per-reader `author_exposure_decay` as an opt-in feed
   view policy; ACL preview/explanation embedded in the community surface.
4. **Richer personal attention surface.** phlogiston.app becomes the native
   client for participating while retaining attention control: native
   ACL/quench editing, hide/demote/annotate/warn/refuse semantics, provenance
   and status cards. Generic timeline rendering stays delegated.
5. **Hardening and wider composition.** Observer-convergence measurement of
   phlogiston's own stack (lifecyclewatch's design applied inward); one
   governed operation under an applicable Constellation profile; allowlisted
   public evidence surface; recurring cross-version restore rehearsal.

## Where integration changes land

- **This repository**: product-surface modules, architecture/disposition
  records, deploy composition.
- **atproto-community**: S2 feed-generator door and (later) S14 membership
  records, each authorized by BUILD.md amendment; admission projection is the
  feed membership source; reverse-chron canonical projection unchanged
  ("ranking is view policy").
- **atproto-acl**: quench policy section, evaluator extension, `muteThread`
  adapter, reply-lineage retention in feed-exposure acquisition,
  exposure-decay vocabulary.
- **atproto-feeds**: generalized multi-feed dispatch as the community feedgen
  template; `root_uri` lineage exposure.
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
- Phase-2 evidence: external-cohort submit → admit → visible, with audit
  entry, in the single spearhead community.
- Phase-3 evidence: one community feed generator serving `getFeedSkeleton`;
  a quenched thread origin suppressed for that user across community views,
  receipted and reversible; ACL preview behavior-hash parity between CLI and
  web.
