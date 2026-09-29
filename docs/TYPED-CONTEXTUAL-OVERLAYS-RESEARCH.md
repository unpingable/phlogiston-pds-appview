# Typed contextual overlays — exploratory design direction

**Status: EXPLORATORY — NOT CURRENTLY SCHEDULED.** This is a direction for
semantic research and a possible narrow spike. It does not authorize a schema,
service, storage system, ingestion, AppView, feed ranker, policy change, or
deployment.

## Question

Can Phlogiston provide **typed contextual overlays** for ATProto objects:
separate, provenance-bearing contextual assertions that consumers may use or
ignore without modifying, claiming ownership of, or redefining the underlying
object?

The term is provisional. It names a product-level relationship, not a new
protocol abstraction or a commitment to a generic annotation framework. The
original ATProto object remains authoritative for itself. An overlay is an
assertion *about* that object, made and carried separately.

```text
ATProto object (authoritative for itself)
    -> typed contextual overlay(s) (separate assertions)
    -> optional consumers: communities, composition, search, policy,
       moderation, and external applications
```

“Metadata” alone is inadequate because it collapses semantically different
assertions into an apparently factual property. For example, these must not
all become `location = Pittsburgh`:

- a post concerns Pittsburgh;
- its author declares current presence in Pittsburgh;
- the author declares residence in Pittsburgh;
- a system infers Pittsburgh from text; or
- a community member associates the post with Pittsburgh.

Each describes a different relation, has a different privacy consequence, and
may have a different basis, author, evidence, scope, and lifetime.

## Design principle

> Enrichment must preserve the provenance of the enrichment itself.

Equivalently: do not collapse an assertion and its warrant into the thing
asserted. The overlay stays beside the source object; its subject, relation,
assertor, basis, and supporting evidence remain inspectable rather than being
normalized into a property of the source object.

A machine-readable annotation remains an assertion; structure does not turn it
into fact. Where applicable, an overlay must make it possible to determine:

- the contextual claim and the ATProto subject object;
- context type and value or referenced object;
- who asserted it and on what basis;
- whether it was declared, observed, inferred, imported, or
  community-annotated;
- evidence or source object, assertion time, and precision/scope;
- validity, expiry, supersession, or withdrawal; and
- whether confidence is meaningful for that particular assertion type.

This is a semantic checklist, not a field list or a wire format. References to
existing ATProto objects or URIs are preferred where they express the needed
relationship. No field should be added merely for anticipated generality.

## Place as the worked example

Geographic/place context motivates the direction because ordinary
`app.bsky.feed.post` records do not provide a generally useful structured
place relation, while voluntary context could help local communities, events,
venues, transit, municipal discussion, and regional discovery.

The initial model must favor explicit, coarse contextual assertions—venue,
neighborhood, municipality, city, region, named place, or event location—over
precise device coordinates. “This post concerns Pittsburgh” is neither a
presence claim nor a residence claim. An author-declared location, a
community annotation, and a text-derived inference must remain separately
typed and visible to consumers.

## Privacy boundary

This must not become passive location surveillance. Any narrowed design must
preserve these constraints:

- no residence inference from post-level place context;
- no current-physical-presence inference unless explicitly asserted;
- prefer coarse named-place semantics over coordinates where adequate;
- retain visible provenance and precision rather than hiding them behind a
  normalized location field;
- make inferred context distinguishable from author-declared and
  community-annotated context, and let consumers reject or ignore it; and
- never treat absence of contextual data as evidence about a person’s place.

## Community-first interpretation and composition boundary

Communities often have useful contextual vocabularies that a base ATProto
application need not standardize: a Pittsburgh community may use
neighborhoods, municipalities, venues, transit lines, and events; a music
community may use scenes, artists, releases, labels, and performances. The
possible Phlogiston role is a common mechanism for *typed contextual
assertions*, while domain vocabularies remain independently defined. This is
not a proposal for a universal ontology.

Such context could let a consumer ask for material relevant to a
region/community/event through explicit relations, rather than solely through
popularity, global engagement, graph prestige, lighthouse accounts, or
inferred actor authority. That makes it relevant to the positive-composition
research lane in `atproto-feeds`, but does not make it a feed-ranking system.
The two research lanes are not coupled: `atproto-feeds` may need meaningful
non-prestige inputs, while this direction asks how meaningful context can stay
an assertion rather than becoming canonical fact. Any future integration needs
its own consumer, evidence contract, and authority boundary.

The boundaries remain:

```text
Phlogiston   -> contextual relations / overlays
atproto-acl  -> user policy / constraints
atproto-feeds -> distribution / composition
```

Phlogiston must not move ranking policy into overlays; ACL must not become the
home of contextual semantics; and an overlay must not become an implicit trust
or reputation score.

Contextual richness is **not credibility**. A place tag, a source link, a
community annotation, or multiple agreeing annotations does not establish
truth, reliability, or authority. The value sought is legibility and
composability.

## Existing mechanisms and prior-art questions

Initial review identifies possible substrate and duplication risks, not a
selection:

- [ATProto Lexicon records](https://atproto.com/specs/lexicon) can describe
  custom, repository-stored record types; published Lexicons and NSID
  namespaces may already be sufficient for a narrow, independently owned
  assertion record.
- [ATProto labels](https://atproto.com/specs/label) are third-party
  assertions with producer/consumer-defined label semantics. Review whether a
  narrow use fits labels before creating a record type; do not stretch a short
  label into a provenance model it cannot express.
- Existing ATProto relation-style records and community Lexicons must be
  inspected for an already suitable subject/reference, identity, or lifecycle
  convention before Phlogiston owns anything new.
- The [W3C Web Annotation Data Model](https://www.w3.org/TR/annotation-model/)
  offers a useful target/body/provenance distinction. Take the lesson—keep an
  annotation and its target distinct—without importing JSON-LD, RDF, or its
  full model by default.
- [ActivityStreams 2.0](https://www.w3.org/TR/activitystreams-core/) and
  JSON-LD show both the value and extension cost of shared vocabularies. They
  are comparison points, not dependencies or a reason to build a generic RDF
  store.

The next review must establish whether existing ATProto mechanisms plus
conventions satisfy the actual consumer need. The purpose is to falsify new
infrastructure, not to acquire standards vocabulary.

## Research sequence and possible narrow spike

Before any implementation:

1. Define only the thin semantic model above and identify a named consumer.
2. Review ATProto Lexicons, labels, ecosystem relation records, and the
   annotation precedents for duplication or semantic collision.
3. Look for reasons Phlogiston should not own this: existing substrate may be
   enough, or the value may belong to a community-specific convention.
4. Narrow the relation and vocabulary before defining a general system.
5. Formalize only invariants needed to preserve provenance, distinction, and
   privacy.
6. Only then consider one narrow overlay type.

A future spike, if separately admitted, would attach one typed place-context
assertion to one existing ATProto post with explicit provenance and
granularity; retrieve it; and let one external consumer use or ignore it. It
would need to prove that the source object remains untouched, competing
annotations coexist, declared/inferred/community-annotated forms remain
distinct, provenance survives a round trip, consumers can select annotation
classes, and removal of Phlogiston changes nothing about the underlying
ATProto record.

## Explicit non-goals

- Precise-location tracking, passive geolocation, or residence inference.
- Global reputation, actor trust scores, or universal truth scoring.
- A universal ontology, graph-wide knowledge inference, or opaque
  embedding-derived metadata presented as fact.
- A replacement for ATProto records, a generic RDF store, or a network-scale
  AppView/indexer.
- Feed ranking inside Phlogiston or moderation policy inside Phlogiston.
- A concrete wire format, schema, or published Lexicon at this stage.

## Open questions and kill criteria

Open questions include which actors may assert which contexts; whether
assertion ownership and withdrawal need a community authority or remain
ordinary repository records; how consumers select vocabularies without
mistaking them for truth; whether competing assertions can remain legible; and
whether an explicit place/context relation provides enough value without
inference.

Narrow or abandon the direction if:

- an existing ATProto mechanism is sufficiently general and Phlogiston would
  duplicate it;
- useful semantics cannot remain distinct from truth, reputation, or authority
  claims;
- privacy costs dominate the relevant community benefit;
- community vocabularies cannot compose without an impractical universal
  ontology;
- it becomes generic metadata infrastructure without a named
  Phlogiston-specific consumer;
- consumers cannot use provenance distinctions meaningfully; or
- it encourages inference where voluntary declaration would be safer.

## Current-design tension

Phlogiston is presently a bounded synthetic renderer, with a separately gated
community-first product path that delegates generic AppView, indexing, search,
and feed machinery. A durable contextual-overlay service would therefore be
outside the qualified artifact and cannot be smuggled into Phase 2 or its
community feed-generator work. The current product also treats labels as
testimony and keeps observation, policy judgment, and distribution separate;
this direction is compatible only if overlays remain assertions with explicit
provenance and retain no implicit authority.
