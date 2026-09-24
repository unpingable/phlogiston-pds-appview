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
| 1 | One public participation surface: `community-live` at the community site. phlogiston.app links to it and carries no participation features. | atproto-community `apps/community-live`; this repo `web/` | done: phlogiston `b4213b5`; community-live copy in PCV2 |
| 2 | Discussion permalink readable without login at a clean path (`/d/<rkey>`). Mutations keep their session requirement. | atproto-community PCV2-A | done: `45dc205`, hardened `5b13b31` |
| 3 | Visible submission lifecycle: submitter sees "waiting for the moderator"; moderator sees the post text in the queue; the room is notified on pending and admitted through one outbound webhook (`community-notify`). | atproto-community PCV2-B | done: `1e1f42d`, `4936d68`, `7edc744`, `cdfec53` |
| 4 | Existing-post submission by URL alongside composition; composition states that it creates a public Bluesky post; copy on the path reframed to "a moderated community collection over author-custodied public posts". | atproto-community PCV2-C | done: `e9b145b`, `6947642` |
| 5 | Named group, topic, moderator, second maintainer, activity, cohort, and room, recorded in the participant packet and accepted by the owner. | [PHASE-2-PARTICIPANT-PACKET.md](PHASE-2-PARTICIPANT-PACKET.md) | **blocked on owner** |
| 6 | Success criterion replaced with the behavioral observations and interpretation rule below. | this document; PRODUCT-ARCHITECTURE.md | done |
| 7 | PD-E / standalone-client disposition recorded. | PRODUCT-ARCHITECTURE.md "Client surface disposition" | done |
| 8 | Phase 3 trimmed to the S2 community feed generator in the community lane. | PRODUCT-ARCHITECTURE.md | done |

Deployment-side prerequisites that are *not* preconditions of the experiment
design but gate its start (found by the 2026-09-24 first-user review, plus the existing gates):
the atproto-community runtime must be re-cut and re-qualified at the PCV2
revision (`cdfec53`; the current qualified cut is `89d04da`);
`PHLOGISTON_COMMUNITY_URL` set in the phlogiston web env (it is commented out
in the example, so the pointer is off by default); the community-live env
filled from the participant packet (name, purpose, moderator DID are
placeholders); the PCV0 deployment validator currently requires the
campaign's fault-injection flags that the README says to remove after the
campaign, so one of the two must change before a trial deploy; the room
webhook proven once against the real room; and Q2 terminal receipt; Horizon 0 cross-version
restore; lexicon publication; PCV0 integration identities; the PCV0
two-account supervised integration; the operator's technical verification.

## The participant's path (what we are testing)

A friend receives one link in a group chat and is told "put something in
here."

1. Opens the community home. Sees the name, one line of purpose, "What is
   this?", and the current collection. No login needed to read.
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
