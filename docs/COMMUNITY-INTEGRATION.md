# Phlogiston community integration

Status: isolated candidate. The real stock-PDS lifecycle is qualified with
synthetic identities across two isolated PDS instances. No production
activation or real-account authority.

## Component map

| Concern | Owner | Integrated seam | Reconciliation / failure rule |
| --- | --- | --- | --- |
| Account, repository and blob custody | stock ATProto PDS `0.4.5034` / embedded `@atproto/pds` `0.5.34` | official XRPC only | PDS result is authoritative for account/repository effects; Phlogiston discards returned account JWTs |
| Participant public post and submission | participant PDS repository | participant OAuth repo write path from PCV0 | durable operation intent; response loss is exact readback, never blind replay |
| Admission, membership and removal | `communityd` | peer-credentialed Unix request boundary | deterministic create-only authority record plus operation journal/readback |
| Observation and application view | `communitywatch` / `communitywatch-web` | read-only committed projection HTTP API | stale/incomplete projection refuses; source records remain separate from projected state |
| User and operator presentation | Phlogiston | typed adapters in `phlogiston_appview.community` and `operator` | UI can request an effect but cannot mint PDS or community authority |

## Vertical slice

The intended integrated lifecycle is:

1. an authenticated participant creates an ordinary `app.bsky.feed.post` and
   `app.phlogiston.community.submit` in their own PDS repository;
2. Phlogiston reads the pending submission from the community projection;
3. an enrolled operator requests `root_admit` through the local communityd
   boundary;
4. communityd validates the exact URI/CID and writes the immutable admission
   in the community repository;
5. communitywatch verifies and projects that record, then Phlogiston renders
   the accepted discussion;
6. removal uses explicit browser confirmation and an immutable moderation
   record; the source post remains untouched;
7. reconciliation updates the projected state to removed.

Membership follows the same authority seam using
`app.phlogiston.community.memberAction`. It is not inferred from PDS account
existence, OAuth login, posting, labels, or projection activity.

## Canonical Lexicon authority

`atproto-community/packages/community-lexicon-publisher/lexicons/` is the one
canonical source tree for the eight integrated community records. The Python
model resources are generated copies. The sync check and TypeScript contract
test compare the complete inventory and canonical JSON content. Publication
remains a separate supervised ceremony; adding a local schema grants no public
namespace authority.

## Application states

Phlogiston translates infrastructure state rather than exposing journals:

- `pending`: participant record observed; no authority admission exists;
- `admitted`: exact authority record is present in a fresh projection;
- `removed`: exact removal record terminalizes the community view only;
- `stale`: projection high-water or heartbeat is behind;
- `unavailable`: authority writer or observer cannot establish a result;
- `uncertain`: attempted effect lacks exact settlement and must reconcile.

An HTTP 200 from a dependency is not enough. Result pages name the actual
authority and immutable effect reference; dashboard freshness comes from the
observer projection status.

## Deliberate limits

- no PDS fork or Phlogiston-local authority table;
- no private-community/read-access semantics;
- no delegated roles or member re-enrollment yet;
- no broad feed, ranking, search or semantic propagation work;
- no production credentials, real accounts, external relay, PLC, or AppView;
- no claim that isolated synthetic qualification establishes production
  OAuth, public Lexicon publication, or durable operational deployment.
