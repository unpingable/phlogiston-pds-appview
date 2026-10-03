# Phlogiston operator surface

This is a deliberately small authenticated interface for the experiment. It
does not make Phlogiston the PDS or community authority.

## Authority boundaries

| Surface | Actual authority | Interface |
| --- | --- | --- |
| Account search/inspection, invites and creation | PDS | Official `com.atproto.server.createInviteCode`, `com.atproto.server.createAccount`, `com.atproto.admin.getAccountInfo`, and `com.atproto.admin.searchAccounts` XRPCs |
| Membership, admission, removal | `communityd` | Peer-credentialed local Unix socket and append-only authority records |
| Status and reconciliation | `communitywatch` | Public read-only committed-projection API |

The browser never invokes `goat` or another CLI as an application API. The PDS
admin password and the community authority credential never cross into HTML.
Account creation discards access/refresh JWTs at the adapter boundary.
Account results render an explicit allowlist of custody fields rather than an
arbitrary admin response.

Community removal and membership changes use a second, intent-bound
confirmation. The result page identifies the authority, operation,
disposition, and immutable record reference. Replaying the same browser intent
reaches the same durable community operation ID; it cannot broaden the effect.

## Authentication

Operators are allowlisted by stable DID. A 32-byte session key signs an
eight-hour `phlogiston_operator` cookie. Session issuance is an operator-local
command; there is no password form and no implicit PDS-account-to-operator
promotion.

```text
PYTHONPATH=src python -m phlogiston_appview.operator_server issue-session \
  --did did:example:operator
```

Secret files must not be group/world accessible. The server refuses insecure
PDS origins except explicit loopback used by isolated qualification.

## Current membership semantics

`app.phlogiston.community.memberAction` is an append-only community authority
record. The initial vocabulary permits one `add` followed by one terminal
`remove`; re-enrollment is deliberately refused until an explicit action-chain
contract exists. PDS account existence and participation never imply
membership.

## Known activation boundary

This surface is not deployed. The isolated two-PDS synthetic smoke is complete.
Real operation additionally requires OS identity enrollment for Phlogiston as
the `community-web` socket peer, exact PDS admin-secret custody, OAuth/session
integration for ordinary users, public Lexicon publication, backup coverage,
and an independently approved activation target.
