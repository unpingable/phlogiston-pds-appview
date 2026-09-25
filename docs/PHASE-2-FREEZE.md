# Phase 2 — pre-activation freeze (2026-09-25)

Status: **PRE-ACTIVATION FROZEN.** No feature, refactor, dependency, UI, or
semantic change is admitted before trial activation unless justified by a
qualification failure, a security defect, a deployment blocker, or an
external-integration defect, and any such change re-runs the synthetic
qualification below.

## Canonical pins

| Item | Value |
| --- | --- |
| atproto-community frozen code (`sourceCommit`) | `b5d8c4fef115c6cbab86443cb3c8e24b8d5809e5` |
| atproto-community deployable tip (pins + receipts on top; differs only in allowed non-code paths, enforced by `validate-cohort --ready`) | `bcbb6c6b9eabcfdfb7e7aa4b89a4381552854219` on `campaign/phlogiston-integration-20260922` (private GitHub) |
| `apps/community-live/pnpm-lock.yaml` SHA-256 | `8ce65c6037ef21373cee8d82267d906fddfd63eec956a571415ee981717eafbc` |
| Python runtime contract | `>=3.12,<3.13` |
| Qualification PDS image | `ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a` (the community actor is Bluesky-hosted; its PDS is not pinned here) |
| OAuth client | `client_id` `https://phlogiston.app/oauth-client-metadata.json`; `client_uri` `https://phlogiston.app`; redirect `https://phlogiston.app/oauth/callback`; `client_name` = `COMMUNITY_NAME`; DPoP; `token_endpoint_auth_method` none |
| phlogiston `main` | the commit carrying this document (see [PUSH-PREPARATION.md](PUSH-PREPARATION.md)); `origin/main` still `cbc6f88` |
| Pin record | atproto-community `deploy/public-community-pcv0/phase2-cohort.example.json` (`pcv0-phase2-cohort-pins-v1`) |

Deployment contract for the bounded trial: exact source checkout at the
deployable tip, `pnpm install --frozen-lockfile` (never `--prod`), exact
service pins, PCV0 kit units. Packaging remains post-trial (atproto-community
issue #2).

## Topology

`https://phlogiston.app` is the participant-facing origin and serves
`community-live` from the PCV0 kit (Caddy site in that kit, loopback :3210).
`phlogiston.social` is the PDS/protocol origin; `*.phlogiston.social` is the
hosted-handle namespace; neither is touched. `community.neutral.zone` is
retired as an application surface; `zone.neutral.community.*` NSIDs are
unchanged and the DNS-only `_lexicon.community.neutral.zone` TXT authority
is retained for lexicon publication only. `community.phlogiston.social` is
not used. `phlogiston-web` is withdrawn from public routing for Phase 2.

## Synthetic qualification at the frozen tip

| Suite | Result |
| --- | --- |
| Real isolated PDS synthetic user, canonical origin (`--origin canonical`) | 32/32 steps, 29/29 negatives, twice at `c88751d` (plus five earlier passes) |
| Same, loopback mode | 31/31, 29/29 |
| community-live unit (clean frozen-lockfile tree) | 137/137, three parallel runs |
| community-live browser suite | 9/9 |
| PCV0 deployment + notifier pytest | 120 |
| atproto-community full pytest | see closeout (`PHASE-2-FREEZE-TRANCHE-2026-09-25.md` at the workspace root) |
| phlogiston Python / web | 55 / 23 |
| roadmap validator; `validate-bundle`; `validate-cohort --ready` | clean |

Receipts: atproto-community `qualification/pcv2/evidence/synthetic-user-20260925.json`
(canonical) and `synthetic-user-loopback-20260925.json`; phlogiston
`qualification/evidence/community-slice-20260925.json` and
`community-recovery-20260925.json`.

## What remains

External actions only: the Q2 receipt, the participant packet, the external
cohort authorization (draft in atproto-community
`docs/campaigns/PHASE-2-EXTERNAL-COHORT-AUTHORIZATION.draft.md`), the
phlogiston push, the PCV0 deployment at the pins, the Caddy site and TLS for
phlogiston.app, and production-only verification
([PRODUCTION-VERIFICATION.md](PRODUCTION-VERIFICATION.md)). See
[Q2-ACTIVATION-RUNBOOK.md](Q2-ACTIVATION-RUNBOOK.md).
