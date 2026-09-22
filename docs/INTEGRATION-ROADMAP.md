# Phlogiston integration/product roadmap

## Product boundary

Phlogiston is presently an offline, synthetic-fixture visualization. It is not
a PDS, relay, network AppView, feed generator, search service, labeler,
monitoring plane, or governance authority. This roadmap is an architecture
sequence, not implementation or activation authority. Constellation remains at
reviewed-local-copy/v1: this document makes no remote AG-to-Docket claim.

The order intentionally makes useful read-only presentation possible before any
network or identity commitment. A later horizon never gates an earlier one.

## Integration matrix

| Family | Current producer/store/consumer | Candidate interface and boundary | Horizon / prerequisite | Acceptance and exit | Explicitly excluded now |
| --- | --- | --- | --- | --- | --- |
| 1. Phlogiston presentation | Synthetic JSON → static HTML → local operator | Versioned fixture/receipt; no network | H0; current qualified contract | Exact input, renderer, revision, output-member hashes verify | Public route or background service |
| 2. PDS | Existing independent PDS owns repositories/accounts | Read-only XRPC surface only after account, rate, and retention authority | H2; scoped account and recovery plan | Real-read parity and refusal/recovery tests | PDS account/key/config mutation |
| 3. Relay/firehose | External relay owns event stream | Bounded consumer with cursor, backpressure, retention and interruption proof | H3; capacity/cost and data-policy decision | Restart/cursor/replay and storage-bound evidence | Persistent firehose or relay operation |
| 4. Network AppView | AppView is a separately operated query/index surface | Explicit read-only query contract, not generic reverse proxy forwarding | H3; API, abuse, cache, auth decision | Endpoint contract, load, rollback and observability evidence | “Full AppView” implication or proxying arbitrary methods |
| 5. Feeds | Feed-generator records/query clients | Named feed algorithm/version and transparent input provenance | H3; feed ownership and moderation policy | Deterministic ranking/replay and opt-out behavior | Personalization or hidden ranking |
| 6. Search | Indexed public records → search readers | Separate index and query contract; declared retention/deletion behavior | H4; legal/policy and storage approval | Recall, deletion, access, backup/restore tests | Cross-store transparent lookup promise |
| 7. Labels/moderation | Labelwatch/accepted label sources remain independent | Read-only, provenance-preserving label display; no decision authority | H2; source freshness and terminology review | Source independence, stale-source, and response-loss tests | Label issuance, enforcement, or Labelwatch mutation |
| 8. Monitoring/operations | Driftwatch/host monitors remain operators’ systems | Health and resource metrics for a future component only | H1; metric owner, retention, notification destination | Startup/restart/backup metrics, bounded alerts | Replacing Driftwatch or live human messaging |
| 9. Governance/Constellation | Constellation v1 reviewed local copy; human operators settle effects | Display only locally reviewed objective context and custody pointers | H1; released contract applicability | Local-copy provenance/refusal proof | Remote AG→Docket, delegated production authority |
| 10. ACL/Quench and external services | ACL export and Quench/native governance are distinct systems; DNS/TLS/CDN/notifications are external | Native ACL/Quench adapter is a future narrow integration; external adapters need per-service credentials/approval | Deferred frontier; exact authority and threat model | Isolated contract/transport tests and owner sign-off | Account import, credential use, DNS/TLS/CDN/chat mutation |

## Horizons and exit criteria

**H0 — present:** retain the offline renderer, immutable receipt/archives and
synthetic identities. Exit only when source, local CLI, archive/restore, and
tamper refusal are independently reproducible. This is the only released
scope.

**H1 — operability preparation:** select artifact custody, component-specific
metrics, retention, backup/restore and rollback commands; optionally show
reviewed-local Constellation context. Exit requires a named owner, bounded
resource budget, recovery drill, and no claim of remote governance.

**H2 — bounded read-only sources:** separately approve a PDS read contract and
independent label display contract. Exit requires synthetic plus authorized
production-shaped reads, freshness/error behavior, source provenance and a
kill switch. Neither requires relay, feed, search, or public exposure.

**H3 — indexed protocol services:** only after H2 contracts stand independently,
admit a bounded relay consumer, a real query AppView contract, or one named
feed. Each has its own cursor/replay, capacity, moderation, rate, abuse,
rollback and sustained-operation qualification. No generic proxy may stand in
for an AppView API.

**H4 — discoverability:** search and larger historical index work need distinct
retention/deletion, privacy, cost, access-control and DR decisions. Exit is a
demonstrated bounded index/rebuild and user-visible data policy, not schema
compatibility.

**Deferred frontier:** native ACL/Quench integration and all external services
require an exact authority packet specifying identity, records, transport,
credentials, recipient/destination, rollback limits and telemetry. A live
account import or notification test is not implied by this roadmap.

## Cross-cutting non-goals

- No production PDS, Caddy, DNS, TLS, firewall, account, key, service, timer,
  credential, relay cursor, or durable network state changes.
- No real identity, firehose, label issuance, moderation decision, human
  notification, public endpoint, or claim that a static renderer is a network
  AppView.
- No replacement of Driftwatch, Labelwatch, legacy-NQ custody, or Constellation
  governance; those systems keep their accepted contracts and owners.

