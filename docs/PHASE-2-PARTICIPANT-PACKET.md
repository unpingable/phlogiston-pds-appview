# Phase 2 participant and activity packet — TEMPLATE

Status: **unfilled.** Every blank below is a decision only the owner can
make. Nothing in this file may be invented by an agent. Until it is filled
and accepted, atproto-community's PCV0 human-dogfood gate stays
`BLOCKED_MISSING_PARTICIPANTS` and no external person's account is in scope
(the activation/DR packet's cohort order: synthetic → owner →
inactive-external → active-external, each transition under its own written
authority).

Fill this in, then record acceptance in atproto-community's PCV0 campaign
record per that repository's process. This copy is the composition-level
reference.

## 1. The community

| Field | Value |
| --- | --- |
| Community display name (`COMMUNITY_NAME`) | ____ |
| One-line purpose shown on the home page (`COMMUNITY_PURPOSE`) | ____ |
| Topic / what belongs here (one or two sentences, plain words) | ____ |
| Public site URL | `https://community.neutral.zone` (decided 2026-09-25; see [PUBLIC-SURFACES.md](PUBLIC-SURFACES.md)) |

## 2. The people

| Role | Handle | DID | PDS | Notes |
| --- | --- | --- | --- | --- |
| Moderator (the single configured moderator DID) | ____ | ____ | ____ | must be a normal ATProto identity on a normal PDS |
| Second maintainer (distinct person, distinct PDS) | ____ | ____ | ____ | PCV0 requires two named maintainers |
| Operator (host-side) | ____ | ____ | ____ | may be the moderator; state if so |

Cohort, in the order the DR packet requires. Each row is a separate written
authorization; none grants the next.

| Cohort | Who (names or descriptions; handles once consented) | Consent obtained? | Start authority |
| --- | --- | --- | --- |
| owner | ____ | ____ | ____ |
| inactive-external (people who have accounts but rarely post) | ____ | ____ | ____ |
| active-external | ____ | ____ | ____ |

## 3. The room and the activity

| Field | Value |
| --- | --- |
| The existing room (group chat / Discord channel) whose wall this is | ____ |
| Incoming webhook URL for `community-notify` (kept in host config, never here) | present: yes / no |
| Payload style | `content` (Discord-style) / `text` (Slack-style) |
| The specific activity: what will people be asked to put in, and by whom | ____ |
| The one prompt that will be sent to the room, verbatim | ____ |

## 4. The window

| Field | Value |
| --- | --- |
| Window length (default three weeks from last cohort admission) | ____ |
| Who records the observations O1–O7 (PHASE-2-TRIAL.md), and where | ____ |
| Who applies the interpretation rule at the end | ____ |

## 5. Acceptance

| Field | Value |
| --- | --- |
| Accepted by (owner) | ____ |
| Date | ____ |
| Recorded in atproto-community PCV0 record at | ____ |

## What this packet does not do

It does not authorize deployment, activation, DNS/TLS/Caddy changes,
lexicon publication, account creation, or any host change. It names people
and an activity so that, when those gates open, the trial can start as an
experiment rather than a deploy.
