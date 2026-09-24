# Spike-branch dispositions

Status: record of disposition decisions for unmerged research branches
referenced by the phlogiston composition. Decided 2026-09-24 during product
consolidation. This document records; it does not modify the owning
repositories.

## `atproto-acl` @ `semantic-quench-spike` (`84f2d78`)

Contents: `semantic.py`, `exposure.py`, `semantic_topics` policy section,
`exposure-preview` CLI, 51 tests. Producer pair:
`atproto-feeds` @ `jev-desk-advisory-spike` (ephemeral inline
`SemanticEvidence v1` records keyed `(uri,cid)`).

Evaluation (JEV-SEMANTIC-QUENCH-SPIKE-2026-09-23): **VIABLE WITH COST.**

Disposition: **retain as research evidence; do not merge to mainline.**

Reasons:

1. No protocol enforcement surface exists for hiding a single post; the only
   shipped adapter is actor-level mute. A semantic judgment without an
   enforcement surface is a score in search of a lever.
2. Body-derived third-party judgments carry a privacy-disclosure burden that
   has not been resolved.
3. Classifier edge cases are uncharacterized outside the spike fixture.
4. The deterministic alternative — thread-origin quench over structural
   reply lineage (`reply.root`/`reply.parent`) — is available, needs no
   inference, and is the vocabulary the product will build first.

Revisit conditions: a post-level enforcement surface exists in-protocol AND
the privacy disclosure has an accepted design. Until both hold, semantic
discourse inference stays out of every enforcement path, including feed
view policy.

## `atproto-feeds` @ `jev-desk-advisory-spike`

Contents: desk-routing advisory classifier producer for
instantinternet.news (`/sports`, `/business`, `/weather` desks).

Evaluation (JEV-ATPROTO-SPIKE-2026-09-23): beats keyword lists (20/22
disagreements resolved in its favor); disposition NARROW. Separately: "NO
NATURAL INTEGRATION FOUND" for atproto-acl post-level classification.

Disposition: **retain as research evidence; merge consideration deferred to
the atproto-feeds owner as a desk-routing feature decision, independent of
phlogiston.** It plays no role in the phlogiston composition.

## Related retained fact

`app.bsky.graph.muteThread`, scoped mutes (`onlyReposts`/`onlyQuoteposts`),
and `viewerState.threadMuted` exist in atproto-acl's vendored lexicons but
are unused. They are the intended adapter targets for deterministic quench
when the reply-lineage acquisition seam lands (Phase 3 of
[PRODUCT-ARCHITECTURE.md](PRODUCT-ARCHITECTURE.md)).
