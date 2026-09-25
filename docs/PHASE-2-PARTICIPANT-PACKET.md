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
| Public site URL | `https://phlogiston.app` (owner decision 2026-09-25; see [PUBLIC-SURFACES.md](PUBLIC-SURFACES.md)) |

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

## What participants will see

Current behaviour of `community-live` as deployed for Phase 2, in plain
words. Nothing here is a promise of future features. Every sentence describes
what the software does today; the two marked placeholders are filled by the
orchestrator from the UX-disposition lane before the packet is accepted.

- **Opening the site.** `https://phlogiston.app` shows the community's name,
  one line of purpose, a "What is this?" note, and the posts currently in the
  community. Reading needs no sign-in.
- **Signing in.** Sign-in uses the participant's own Bluesky account (OAuth on
  their own PDS). No account is created anywhere, and no password is entered
  on the community site. The consent page on their PDS shows the permission
  as "Repository · Publish changes"; the community collection
  (`zone.neutral.community`) is listed only behind a details control there.
  The site can create posts on their account and can record a submission
  record in their repository; it cannot read private data, follow, like or
  delete anything.
- **Adding a post they already made.** They paste the link to one of their own
  Bluesky posts. Nothing changes on Bluesky. The site writes a small
  submission record to their repository and asks the moderator to add the
  post.
- **Composing.** "Start a discussion" publishes a new public post on their own
  Bluesky account first, then asks the moderator to add it. The page says so
  before they press the button. The post exists on Bluesky whether or not the
  moderator admits it.
- **Moderation and admission.** The single configured moderator sees waiting
  submissions, with the post text, on a queue page and admits or leaves them.
  Admission changes only the community view. Nothing is written to the
  author's account by admission.
- **Permalinks.** Each admitted discussion has a permalink
  `https://phlogiston.app/d/<key>` that opens without sign-in and can be
  pasted into the room.
- **Replies.** A signed-in participant can reply on a discussion page. The
  reply is a public reply on their own Bluesky account; the community policy
  admits it automatically, so it appears without waiting. The moderator can
  remove a reply from the community view and restore it. Replies cannot be
  added to a discussion that has been removed or closed; the page says so.
- **Removal and restore.** When the moderator removes a discussion, its page
  says it was removed from this community's view and that the author's public
  post is not deleted or changed. Restore brings it back. Only the community
  view ever changes.
- **"My discussions" (`/mine`).** Shows the participant's submissions that are
  waiting for the moderator, the discussions they are in, and unfinished
  operations they can resume. Limitations today: a submission the community's
  automatic checks could not accept ____ [PLACEHOLDER: orchestrator fills from
  the UX-disposition lane (E2), Question 1: whether `/mine` now shows a
  "Couldn't be accepted" bucket, or whether such a submission disappears from
  the list without a word and how the operator finds the reason]. Existing
  replies under a removed discussion ____ [PLACEHOLDER: orchestrator fills
  from the UX-disposition lane (E2), Question 2: whether retained replies stay
  visible under a removed root and how that is explained].
- **Notifications.** The room gets one short line when a submission is
  waiting for the moderator and one when a discussion is admitted, each with
  a link and never the post text. There is no email, no push notification,
  and no direct message to anyone.
- **What data is experimental.** The community's admission and removal
  records, the observer's projection, and the room notification cursor are
  trial data and may be reset between trials. Participants' own Bluesky posts
  and submission records live in their own repositories and are never
  changed by the community; they can be deleted by the author at any time
  with their usual client. Author display names and handles are fetched from
  the public Bluesky AppView for display only; avatars are not shown.
- **Reporting a problem.** ____ [PLACEHOLDER: the room; how and to whom a
  participant reports a problem is filled by the owner with the room in
  section 3]. A problem that stops someone completing a step is a user-path
  blocker and is fixed in the owning repository; it does not count against
  the trial's demand evidence.

## What this packet does not do

It does not authorize deployment, activation, DNS/TLS/Caddy changes,
lexicon publication, account creation, or any host change. It names people
and an activity so that, when those gates open, the trial can start as an
experiment rather than a deploy.
