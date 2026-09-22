# Community slice qualification

Result: **passed in isolated synthetic infrastructure** on 2026-09-22.

Exact inputs:

- Phlogiston: `44afef7315f0d6fd34e0c0ca1fc36eb7c7b3afe2`
- atproto-community: `fe98207c486ac32bec47636206f230d15e7e7b54`
- stock PDS image:
  `ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a`
- full machine-readable receipt:
  [`../qualification/evidence/community-slice-final.json`](../qualification/evidence/community-slice-final.json)

The successful path used two separate disposable PDS containers. The
participant authored an ordinary post and community submission on one PDS.
The community actor and operator identities lived on the other. `communityd`
resolved the participant DID through an isolated DID directory, read the
participant record from the correct PDS, wrote membership/admission/removal
records only to the community repository, and returned exact record refs.

The enrolled synthetic operator requested membership, admission, and removal
through the authenticated Phlogiston handler; membership and removal exercised
its explicit intent-bound confirmation page. `communitywatch` verified
repository proofs, projected the admitted content,
and exposed a fresh committed projection. Phlogiston rendered the post before
removal and did not render it after the real removal record was ingested. The
receipt records matching observer high-water state and no degradation reasons.

Focused Phlogiston tests passed (24). Focused community integration tests
passed (115). The complete atproto-community suite passed (1,313), and all
four Lexicon publisher test files passed. Disposable containers, network,
state, socket, reader and HTTP server were removed at process exit.

This result does not qualify production OAuth, public Lexicon publication,
public registration, production deployment, backup of the newly integrated
state, or general multi-community behavior. No external network, production
account, production credential, DNS, TLS, or Q2-observed state participated.
