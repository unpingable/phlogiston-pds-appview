# Phase 2 — the first external trial as a demand experiment

Status: **experiment design, pre-deployment.** Nothing here authorizes
deployment, activation, DNS/TLS/Caddy changes, or a public trial. Those stay
behind the Q2 observation window's terminal receipt, atproto-community's
PCV0 publication and dogfood gates, and the participant packet below.

The governing question:

> Can the first external trial measure whether humans want the community,
> rather than whether they can survive our plumbing?

## What Phase 2 is and is not

Phase 2 is one community, one existing group of people, one activity, for a
bounded window. It is not a platform launch, not an analytics program, and
not a plumbing test. The plumbing test (`submit → admit → visible → audit
entry`) is run once by the operator as *technical verification of the
deployment* before any participant is invited. It produces no product
evidence.

## Preconditions (all pre-Q2-safe; code lives in the owning repos)

| # | Precondition | Where | State |
| --- | --- | --- | --- |
| 1 | One public participation surface: `community-live` at `https://phlogiston.app`. phlogiston-web carries no participation features and is not publicly routed. | atproto-community `apps/community-live`; this repo `deploy/production` | done: phlogiston `b4213b5`, withdrawal of web routing in this freeze; community-live copy in PCV2 |
| 2 | Discussion permalink readable without login at a clean path (`/d/<rkey>`). Mutations keep their session requirement. | atproto-community PCV2-A | done: `45dc205`, hardened `5b13b31` |
| 3 | Visible submission lifecycle: submitter sees "waiting for the moderator"; moderator sees the post text in the queue; the room is notified on pending and admitted through one outbound webhook (`community-notify`). | atproto-community PCV2-B | done: `1e1f42d`, `4936d68`, `7edc744`, `cdfec53` |
| 4 | Existing-post submission by URL alongside composition; composition states that it creates a public Bluesky post; copy on the path reframed to "a moderated community collection over author-custodied public posts". | atproto-community PCV2-C | done: `e9b145b`, `6947642` |
| 5 | Named group, topic, moderator, second maintainer, activity, cohort, and room, recorded in the participant packet and accepted by the owner. | [PHASE-2-PARTICIPANT-PACKET.md](PHASE-2-PARTICIPANT-PACKET.md) | **blocked on owner** |
| 6 | Success criterion replaced with the behavioral observations and interpretation rule below. | this document; PRODUCT-ARCHITECTURE.md | done |
| 7 | PD-E / standalone-client disposition recorded. | PRODUCT-ARCHITECTURE.md "Client surface disposition" | done |
| 8 | Phase 3 trimmed to the S2 community feed generator in the community lane. | PRODUCT-ARCHITECTURE.md | done |

## Deployment topology (decided 2026-09-25)

For Phase 2 the atproto-community PCV0 kit
(`deploy/public-community-pcv0/`) owns every community service: `communityd`,
`communitywatch-index` and `communitywatch-web` (observer on
`127.0.0.1:8080`), `community-policy`, `community-live` and
`community-notify`, under that kit's users, paths
(`/var/lib/communityd`, `/var/lib/community-web`, `/var/lib/communitywatch`,
`/etc/atproto-community`) and credential. Its README is the single README for
the community services. The participant origin is `https://phlogiston.app`,
served by `community-live` on `127.0.0.1:3210` behind a Caddy site block that
the PCV0 kit owns (see [PUBLIC-SURFACES.md](PUBLIC-SURFACES.md)). phlogiston
installs only the phlogiston-web release, which reads the PCV0 observer
unchanged (`PHLOGISTON_PROJECTION_ORIGIN=http://127.0.0.1:8080`) and is
withdrawn from public routing for Phase 2: it would collide with
community-live at the same origin, so its unit is not enabled and its Caddy
fragment defines no site block. `community.neutral.zone` is retired as a
site; `community.phlogiston.social` is dropped.

The community actor is a Bluesky-hosted account
(`did:plc:b53udqv47g2dayvpstzdefpq` on
`phellinus.us-west.host.bsky.network`), not a `phlogiston.social` account.
The phlogiston PDS (`phlogiston.social`, `127.0.0.1:3002`) is separately
activated operator infrastructure and is not on the participant path.

Invariant: exactly one communityd per community DID holds the actor
credential; one journal, one socket, SO_PEERCRED-checked requesters. The
phlogiston `phlogiston-communityd.service` / `phlogiston-communitywatch.service`
units and their `.toml.example` files are withdrawn for Phase 2 (header-marked,
kept for the record) and must never run beside the PCV0 `communityd.service`;
`deploy/production/preflight.py` refuses if any other installed unit starts
`communityd-serve` or if `phlogiston-communityd.service` is installed and not
masked, and `deploy-inert.sh` extracts the community runtime only with
`--with-community-runtime`, which Phase 2 does not use.

Deployment-side prerequisites that are *not* preconditions of the experiment
design but gate its start (found by the 2026-09-24 first-user review, the
2026-09-25 topology decision, plus the existing gates):

- the current forward artifact includes `community-live`, `community-policy`
  and `community-notify`, eight installable wheels and the closed offline
  frontend dependency store. Use the verified artifact install path in
  [Q2-ACTIVATION-RUNBOOK.md](Q2-ACTIVATION-RUNBOOK.md), not editable source
  installs. The dated source-checkout freeze is historical evidence;
- done on 2026-09-25 and no longer open: the double-writer guard (PCV0
  `host-preflight` and phlogiston `preflight.py`), the `community-live`
  start path (`node_modules/.bin/tsx src/server.ts`), and the deployment
  validator's campaign/normal fault-mode distinction;
- the community-live env filled from the participant packet (name, purpose,
  moderator DID are placeholders) with `COMMUNITY_PUBLIC_URL=https://phlogiston.app`;
- the PCV0 kit's `phlogiston.app` Caddy site block installed and its
  ordinary ACME certificate verified (no DNS repoint is needed for the front
  door: `phlogiston.app` already resolves to the host; see
  [DNS-CUTOVER-PREP.md](DNS-CUTOVER-PREP.md));
- retire the `community.neutral.zone` site role: nothing to do at DNS beyond
  not creating an A record for it at the host. Canonical publication uses only
  `_lexicon.community.phlogiston.app`; no superseded authority TXT is created;
- the room webhook proven once against the real room;
- the Q2 terminal receipt; lexicon publication; PCV0 integration identities;
  the PCV0 two-account supervised integration; the operator's technical
  verification ([PRODUCTION-VERIFICATION.md](PRODUCTION-VERIFICATION.md));
  the external-cohort authorization; all in the order given by
  [Q2-ACTIVATION-RUNBOOK.md](Q2-ACTIVATION-RUNBOOK.md).

`phlogiston.social` activation prerequisites, kept separately and not gates
for Phase 2: the phlogiston PDS live on `127.0.0.1:3002`, its
`phlogiston.social` TLS and Caddy route, and the Horizon 0 cross-version
restore receipt (still required before any public registration there).

## The participant's path (what we are testing)

A friend receives one link in a group chat and is told "put something in
here."

1. Opens the community home at `https://phlogiston.app`. Sees the name, one
   line of purpose, "What is this?", and the current collection. No login
   needed to read.
2. Signs in with their own Bluesky account (OAuth on their PDS). No account
   is created anywhere.
3. Either submits a post they already made (by URL), or writes a new one
   knowing it will appear on their own Bluesky account.
4. Sees the submission marked as waiting for the moderator. The room gets a
   line saying something is waiting.
5. The moderator opens the queue, reads the post there, admits it.
6. The room gets a line with the community permalink. The submitter's page
   shows it as in the community.
7. Anyone in the room can open that permalink without signing in.
8. If the moderator removes it later, the page says so in plain words, and
   says the author's post is untouched.

Every step above has a corresponding code precondition in the table. If any
step fails for a mechanical reason during the trial, that is a **user-path
blocker**, recorded separately from demand evidence.

## Behavioral observations (from atproto-community `PRODUCT-DIRECTION.md` §2)

Record these, and only these, during the window. No sessions, retention, or
growth metrics.

- O1. Did anyone other than the operator submit something?
- O2. Did anyone submit more than once?
- O3. Did anyone visit the community without a direct prompt?
- O4. Did anyone paste the community permalink back into the room instead
  of the original Bluesky URL?
- O5. Did moderation stay trivial? (no decision needed more than a minute or
  a conversation)
- O6. Did anyone misunderstand why an item appeared or disappeared?
- O7. Did anyone ask for the same missing affordance more than once? (record
  the ask verbatim; it is forcing-case evidence for a parked slice, per
  PD-D)

The closest thing to acceptance is someone saying "put that in the
community" unprompted. Record it verbatim if it happens.

## Interpretation rule for the hard gate

The window is set in the participant packet (default: three weeks from the
day the last cohort member is admitted). There is no score. At the end of
the window:

- **Open Phase 3 (S2 feed generator)** when all of: O1 and O2 are yes for at
  least one non-operator; at least one of O3 or O4 is yes; O5 is yes.
- **Stop and reassess** when any of: O1 is no; every submission was directly
  prompted by the operator; O6 happened repeatedly and the misunderstanding
  was not a user-path blocker.
- **Extend once** (same window length, same cohort) in every other case,
  then apply the rule again with no further extension.

User-path blockers found during the window are fixed in the owning repo and
do not count against demand. Deployment blockers pause the window; the clock
resumes when the surface is back. Demand unknowns are what the rule above
decides.

"Stop and reassess" means: record the verdict, do not build more substrate,
and return to the composition question with the evidence in hand.

## Three kinds of blocker, kept apart

- **User-path blocker**: a participant could not complete a step for a
  mechanical or comprehension reason. Owned by the surface's repo. Fix,
  redeploy, continue.
- **Deployment blocker**: TLS, DNS, host, restore, publication, credentials.
  Owned by the campaign procedures. Pauses the window.
- **Demand unknown**: the surface worked and people did not use it. The only
  thing the interpretation rule is allowed to judge.
