# Community production-readiness qualification

Date: 2026-09-22. Result: **qualified in isolation; activation not authorized**.

## Bound sources

- Phlogiston recovery implementation: `8a20112a66c76ee58d0867836e5317fa089efbd5`
- Phlogiston OAuth/session implementation: `a881751`
- Community authority and Lexicon implementation: `fe98207`
- Community PHI1 scope amendment: `5d655c88310477e30d0f6b7a608dfce5012fd513`
- PDS image: `ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a`

Machine receipts:

- `qualification/evidence/community-lifecycle-20260922.json`
  SHA-256 `f74d29c33cd2ff326769eb9fb67ba19e91ff0b50797528d9c6d2d728c514b151`
- `qualification/evidence/community-recovery-20260922.json`
  SHA-256 `ebc1ac824110a3650264ecf8c8050c678b228574942a99e1b53d486eb8251a71`

## Results

- Phlogiston Python: 32 passed.
- Phlogiston OAuth/session: TypeScript typecheck and four test files passed.
- atproto-community Python: 1,313 passed.
- canonical Lexicon publisher: typecheck and 4 tests passed.
- community-live: typecheck and 72 tests passed outside the restricted
  loopback-listener sandbox.
- Real isolated lifecycle: two PDSes, exact membership/admission/removal,
  public render before removal, hidden after removal.
- Recovery: stopped-state capture, 962,560-byte archive, blank-host restore,
  exact authoritative references, new observer rebuild, repeated idempotent
  replay, removal preserved, and one-PDS-unavailable refusal.

The first recovery attempt correctly refused because the communityd journal
still had SQLite sidecars. The repair added an explicit stopped-writer,
non-busy `wal_checkpoint(TRUNCATE)` gate. A later verifier attempt exposed and
fixed an overly narrow mapping type check; another exposed the exact
`list_visible` pagination contract. Acceptance evidence was regenerated only
after both fixes.

## Nonclaims and blockers

No production service, DNS, TLS, account, DID, record, credential, or external
network was touched. This does not qualify production RPO/RTO, live-copy
backup, external PLC recovery, cross-version migration, or real-account
portability.

Activation remains blocked on published Lexicons; exact DNS/TLS and OAuth
client metadata/callback; production secret and backup custody; immutable
deployable artifacts; separately authorized synthetic/owner account actions;
and production backup/rollback admission. The locked OAuth dependency graph is
exact, but this isolated checkout lacked the pinned OAuth tarball in its pnpm
offline store. Tests used the already-installed exact dependency tree from the
qualified community checkout. A clean artifact build must acquire and verify
that package before activation.
