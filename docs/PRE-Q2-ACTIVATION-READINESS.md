# Pre-Q2 activation readiness

Frozen 2026-09-22. **Prepared, not deployed and not activated.** The protected
shared-host observation ends at `2026-09-27T16:54:28Z`; elapsed time alone is
not acceptance. Deployment requires its accepted uncontaminated closeout
receipt plus fresh host, backup and capacity observations.

## A–D. Artifacts, sources, topology and configuration

| Item | Exact identity |
|---|---|
| Phlogiston source | `2b0324a6012011a06117ab55c63f09d193d51d3d` |
| Phlogiston artifact | `phlogiston-2b0324a.tar.gz`, SHA-256 `34663965c015a24ca6a75ad7147dd313c91ee8f2b666db50b1f1a05ee55e1951`, 3,453,672 bytes, 6,556 manifest files |
| Community source | `89d04dafc8aaa55f0e327241fbb7b3521c0042f0` |
| Community runtime | `community-runtime-89d04da.tar.gz`, SHA-256 `ad954a8b607db9b98714e01471cb1f1e00da1847a6ed513430e0d25f6abcbccf`, 181,067 bytes, six exact wheels |
| PDS image | `ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a` (`@atproto/pds` 0.5.34) |
| OAuth package | `@atproto/oauth-client-node@0.0.0-spaces-alpha-20260818163953`, tar SHA-256 `ab145aa3394dff0e00bfb87f6ed4df1fcb9c7bb932104bd619d0e95be8485eed` |
| Production configuration | `deploy/production/config-manifest.json` (`phlogiston.production-config-manifest.v1`) |

The web service binds `127.0.0.1:8092`. The activated read-only projection
binds `127.0.0.1:8093`. The independently pinned PDS template publishes only
`127.0.0.1:3002 -> container:3000`; it neither reuses nor modifies Juche. The
community authority remains a peer-credentialed Unix-socket `communityd`
unit. Caddy owns public TLS/routing. The inert deployment starts only web;
community identity is unset, `/community/` returns 503 without a network
request, `/admin/` is absent, and no PDS/community authority starts.

The exact production URLs are:

- origin/client URI: `https://phlogiston.app`;
- client metadata/client ID: `https://phlogiston.app/oauth-client-metadata.json`;
- callback: `https://phlogiston.app/oauth/callback`;
- later independent PDS: `https://phlogiston.social`.

## E–I. Custody, backup, Lexicons, DNS and TLS

`docs/SECRET-CUSTODY.md` is the complete secret matrix. Current Phlogiston has
no static cookie/HMAC secret; OAuth/DPoP and opaque browser sessions are
server-generated, owner-only and re-enrollable. PDS and communityd credential
material is generated only at the separately authorized activation boundary.
No secret value is in this repository or evidence.

`docs/PRODUCTION-BACKUP-CONTRACT.md` binds the off-host backup owner. The
production host has no archive mount. A fresh, hour-bounded
`phlogiston.backup-custody.v1` probe receipt is mandatory. Authoritative PDS
trees and the communityd journal use stopped-state capture; projection and
OAuth/web sessions are reconstructed or re-enrolled. Same-version blank-host
restore and all listed refusal cases are qualified in isolation. Production
RPO/RTO and cross-version restore remain nonclaims until the first production
backup/restore evidence exists.

Canonical Lexicons remain the eight files under the community repository's
`packages/community-lexicon-publisher/lexicons/`. Their digests, publisher,
drift check, reconciliation and irreversible publication boundary are frozen
in `docs/PHLOGISTON-LEXICON-PUBLICATION-PACKET.md` in that repository. The
drift check passes. Publication is not performed: it requires a separately
authorized namespace account write and DNS TXT mutation.

Fresh read-only DNS showed both intended names resolving only to the intended
shared-host IPv4 address. DNS was not changed. No TLS certificate currently
exists for either name. Both Caddy fragments validate with the production-
version Caddy 2.10.0 image digest retained in private evidence. Automatic
HTTPS, renewal and redirect behavior remain owned by existing Caddy. The PDS
wildcard/on-demand route cannot be activated until its ask-policy verification
is correctly bound to the independent PDS.

## J–L. Deployment, rollback and verification

The executable procedure is:

```text
sudo deploy/production/deploy-inert.sh /etc/phlogiston/deployment.json
```

It refuses before the exact Q2 boundary, without an accepted matching Q2
receipt, with wrong host identity, wrong artifact hashes, unresolved
placeholders, absent secret-custody approval, stale/mismatched backup custody,
or unexpected state. It installs immutable releases, verifies embedded
manifests, installs only inert units/configuration, probes local behavior,
backs up the complete Caddyfile, validates the full candidate in the Caddy
container, reloads, verifies the public health path, and writes a receipt with
zero account/community mutations.

Rollback is explicit:

```text
sudo deploy/production/rollback-inert.sh --confirm-inert-rollback \
  /etc/phlogiston/deployment.json /exact/verified/Caddyfile.before-phlogiston.TIMESTAMP
```

It validates the rollback Caddyfile before installation, restores and reloads
it, disables only new units, and preserves state, releases, configuration and
evidence. `deploy/production/verify-external.sh` checks DNS, TLS chain/SAN,
HTTPS, exact OAuth metadata, inert community refusal and absent admin route
without beginning OAuth.

## M–N. Activation and human use

`docs/SYNTHETIC-ACTIVATION-PACKET.md` names authority, executor, exact input,
transition, evidence, stop condition and recovery for every enrollment,
membership, admission, removal, reconciliation, logout/revocation and backup
step. No step inherits authority from the previous step.

`docs/HUMAN-SMOKE-TEST.md` covers the first browser journey: login, explicit
non-membership, separately admitted membership, public community rendering,
removal persistence, logout, re-login, disconnect and intelligible refusal.
It does not pretend the intentionally absent operator HTTP surface or general
posting UI exists.

## O–P. Authority boundaries and remaining blockers

Only these facts necessarily remain open:

1. Q2 must actually close uncontaminated and its terminal aggregator/receipt
   must accept; fresh capacity and shared-host identities must then be read.
2. An operator must grant the inert shared-host deployment/Caddy effect and
   fill private host, rollback and fresh backup-custody values. No account or
   community authority is included.
3. Lexicon publication needs separate DNS and namespace-account write
   authority. Its packet is otherwise mechanical.
4. PDS/community activation needs deliberate secret generation, independent
   PDS route/on-demand TLS verification, and one named controlled account.
5. Each OAuth, membership, admission, removal, observer restart and first
   backup effect needs its own exact authority from the activation packet.

The first post-Q2 action is not deployment. Run the authoritative Q2 terminal
aggregator with its exact start/end and require `terminal=true`; create the
`atproto.q2-closeout.v1` deployment input only from that accepted result. Then
re-observe capacity, host/Caddy identity, and off-host backup custody before
running the inert preflight. The exact private command and paths are retained
in the companion record rather than this public document.

## Qualification summary

- Phlogiston Python: 41 passed.
- Node typecheck and four test files: passed from a clean offline install.
- artifact builds from two independently populated stores: byte-identical;
  exact artifact start/restart, metadata, inert 503, absent `/admin/`, and
  zero anonymous runtime files: passed.
- community runtime: two byte-identical builds; six wheels installed offline;
  `communityd-serve` and `communitywatch-web` entrypoints: passed.
- production config manifest: byte verification passed.
- dangerous preflight refusals: wrong host/artifact/backup, missing secret,
  existing state, missing authority and pre-Q2 execution passed.
- PDS Compose rendering: passed without starting a container.
- systemd unit parsing: passed; off-host verification reported only the
  expected missing installed community executables.
- Caddy fragment: valid under exact Caddy v2.10.0 image digest.
- backup probe mechanics and cleanup: passed on off-host synthetic storage;
  real NFS probe intentionally remains fresh-at-deployment work.
- Lexicon generated-copy drift and `git diff --check`: passed.

No production host, DNS, TLS, account, DID, repository, membership, admission,
moderation or community state changed during this freeze.
