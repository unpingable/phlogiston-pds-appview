# Community runtime recut and isolated re-qualification — 2026-09-25

Result: **recut verified off-host; isolated community slice and recovery
passed; not deployed.** Nothing touched the shared host, DNS, TLS, Caddy,
a live PDS, or the Q2 observation window.

## Bound identities

| Item | Value |
| --- | --- |
| Community source | `cdfec53b38e2ba8f4c6258d431c6531460712d02` (branch `campaign/phlogiston-integration-20260922`; PCV2 user-path slices on top of `89d04da`) |
| Phlogiston source | `f7be2996124c787c325742df6b23493d29fe6d6b` |
| Community runtime | `.release/pre-q2-20260925/community-runtime-cdfec53.tar.gz`, SHA-256 `63108dfee47149a986e78c5216aa100e6315212bd55618e49394793768a739d6`, 181,067 bytes, six wheels |
| Build tools | setuptools 80.9.0 (`062d3422…`), wheel 0.45.1 (`708e7481…`), Python 3.12.3, runtime contract `>=3.12,<3.13` |
| PDS image | `ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a` |

## Recut

`deploy/build-communitywatch-release.sh` was run unchanged (the PHI2
procedure has not drifted) with a fresh build venv, the retained build-tool
wheels, and `git archive` of the exact commit. `deploy/verify-communitywatch-release.py`
verified six wheel files and the commit binding from a fresh extraction.

Finding worth stating plainly: the six wheels are **byte-identical** to the
`89d04da` cut. PCV2 changed `apps/community-live`, added
`packages/community-notify`, and changed deploy files; none of those are in
this artifact's package set. The archive differs from the previous cut only
in its manifest's commit binding. So this artifact is a re-attestation, not a
new runtime, and the Phase 2 participation surface (`community-live`), the
reply-policy worker, and the notifier have **no release artifact at all**:
the PCV0 kit runs them from a source checkout (`corepack pnpm start`,
`apps/community-live` without a lockfile). That is recorded as a gap in
[PHASE-2-TRIAL.md](PHASE-2-TRIAL.md) and in the tranche closeout; it is not
hidden by this receipt.

## Isolated community slice and recovery

`qualification/run-community-slice.sh` with `ATPROTO_COMMUNITY_ROOT` at the
pinned clone, two isolated stock-PDS containers, a local PLC stand-in, no
external network:

- `qualification/evidence/community-slice-20260925.json`: `passed`; community
  DID `did:plc:ajnmye6kqwu4f7rir54tg52c`, participant on a second PDS;
  membership add, admission, render before removal, hidden after removal,
  observer health `ok`, `highWaterMatches` true.
- `qualification/evidence/community-recovery-20260925.json`: capture,
  restore into blank state, reconcile; 14 files; source bindings match the
  identities above.

This exercises phlogiston-web, `communityd`, `communitywatch`, membership,
admission and removal against real PDS repositories. It does **not** exercise
`community-live`; that is the purpose of the separate real-PDS synthetic-user
harness in atproto-community `qualification/pcv2/`.

## Nonclaims

No inert or production deployment, no host inspection, no lexicon
publication, no backup of production state, no cross-version restore (which
still needs the first production backup), and no claim that this artifact
alone deploys Phase 2.
