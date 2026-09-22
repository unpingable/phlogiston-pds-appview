# Deployable artifact qualification — 2026-09-22

Result: **qualified off-host; not deployed**.

## Bound identities

- Phlogiston source: `a301edf86e940e1bf77cb566902c1812d80b9a4c`
- community source: `89d04da7f37d435d34796f4f8ab17bcf2b611884`
- PDS image retained by the release manifest:
  `ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a`
- pnpm: `11.11.0`; Node: `24.13.0`
- dependency-store manifest SHA-256:
  `3997a2fdccec8400974a22c3561db0d4008c18c2777ef54fd098161548644437`
- dependency-store bundle SHA-256:
  `371a2f15b467151e74998d3c4784627641ce39ff2db26a58c5d6075104d08819`

The previously missing package was independently fetched from the npm registry
at exact version `0.0.0-spaces-alpha-20260818163953`. Its 15,909-byte tarball
has SHA-256
`ab145aa3394dff0e00bfb87f6ed4df1fcb9c7bb932104bd619d0e95be8485eed`
and SHA-512 SRI
`sha512-XEJS6GMk5mG136FVcoSzzFynnMKGsJ3J2Z0oVWotwkYdCyawN1UCoxtKalMqzFRSsk6uWyiNKig1OK+XwC+weQ==`.
Both match the exact lockfile entry and the package-internal name/version.

## Clean build

`pnpm fetch --frozen-lockfile` populated a new empty store with 40 packages and
reported zero reused packages. The store was checksummed path-by-path. The
release builder then:

1. verifies the complete store manifest and exact OAuth tarball identities;
2. archives the exact clean Git source;
3. installs and compiles in a fresh temporary tree with `--offline` and
   `--frozen-lockfile`;
4. removes that dependency tree and performs a fresh production-only install;
5. removes pnpm's time/path-bearing non-runtime metadata;
6. emits an embedded manifest for every regular payload file; and
7. normalizes ordering, timestamps, ownership, hardlinks, and gzip metadata.

The same command was run once against the original clean store and once
against a separately extracted immutable store bundle. Both produced the same
3,445,138-byte archive:

```text
d0746f9793a97202e20fc8253e49b2f8bfff2cefbccc438346babc772b62dd16
```

`cmp` confirmed byte identity. `deploy/verify-release.py` then verified 6,541
payload files and both source commits from a fresh extraction. The production
tree contains no `tsx` development package. A scoped owned-source scan found no
private keys, service secrets, tokens, or populated credential variables;
dependency source containing generic PEM marker strings was not misreported as
a credential.

## Exact-artifact runtime result

The extracted artifact was started twice against a bounded loopback synthetic
read-only projection. Both starts passed `/healthz`. OAuth metadata reported
scope `atproto`, DPoP-bound tokens, refresh support, and the exact loopback
callback in the isolated run. `/community/` rendered the synthetic projected
record and projection generation. `/admin/` returned 404 because production
operator-session issuance is deliberately absent. Anonymous reads created zero
runtime files. No OAuth enrollment or authority operation was attempted.

Python tests passed 35/35. The clean offline Node qualification passed
typechecking and all four test files, including OAuth/session, projection,
public rendering, storage, malformed projection refusal, and identity versus
membership separation. The extracted manifest and restart smoke passed.

## Production standing and nonclaims

DNS for both intended names resolved to the intended host at inspection time,
but neither name completed TLS and no matching Caddy route, service unit,
runtime state, or listener existed. Therefore no inert production deployment
or external smoke occurred. The Q2 production observation window remains an
independent safety gate against changing this shared host.

This result does not qualify a real PDS, external OAuth callback, Lexicon
publication, operator login, account, membership, community record, Caddy
transaction, TLS certificate, production backup, or rollback. The publication
and synthetic-activation packets retain those boundaries explicitly.
