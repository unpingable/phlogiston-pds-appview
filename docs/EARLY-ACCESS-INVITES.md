# Private early-access invite enrollment

Standing: **planned, Backlog**. `PHLOGISTON_EARLY_ACCESS_PLANNED` records the
bounded design, not implemented or qualified enrollment. This is for a future
initial cohort after the owner-authorized submit → admit → render integration.
It does not block that integration or replace its participant, moderator,
notification-room, Lexicon or credential holds.

Public explanation: <https://phlogiston.app/>. Early access is
invite-only; initial invitations are issued directly by the project owner.
No public signup, invite-request form, waitlist, referrals or growth automation.

## Smallest implementation

Use an owner-operated command and a private enrollment ledger alongside the
existing enrollment path. Do not create a separate registration service or PDS.
Participants bring their own ATProto identities. Implement this only when that
future cohort needs it; no UI polish or generalized invitation platform first.

An invitation contains:

| Field | Meaning |
| --- | --- |
| `invite_id` | Opaque, unpredictable invitation identifier, handed privately to the intended person |
| `issuer` | Project owner identity; issuance is an owner action |
| `issued_at`, `expires_at` | UTC issuance and finite expiry |
| `max_uses` | Exactly 1 for this initial implementation |
| `intended_role_class` | Optional proposed participant/maintainer/moderator class; never a role grant |
| `intended_participant` | Optional known DID or handle; resolve a handle to a DID and confirm the intended person during enrollment |
| `cohort_id` | Explicit early-access program/cohort binding |
| `status` | `issued`, `consumed`, `revoked`, or `expired` |

Keep invite identifiers and the identity-bearing ledger in approved private
operational custody. Public receipts, issues and source contain no usable invite
identifier, credentials or unreleased participant identity. Credentials stay in
their existing separate custody, never in the invitation or enrollment ledger.

## Owner and participant flow

1. The owner issues a finite, one-use invitation for a known prospective
   participant and records issuance durably. The owner hands it directly to them.
2. Presenting a well-formed, known, issued, unexpired invitation opens only the
   normal enrollment path. It grants no community or moderator authority.
3. Resolve and verify the participant's DID/PDS binding, normal authentication,
   required credential scopes and any intended-person/cohort binding using the
   existing enrollment checks. Possession alone is insufficient. When no intended DID/handle was supplied,
   record the owner's confirmation of the intended person before consumption. A changed or
   ambiguous handle binding requires owner confirmation of the intended person;
   it does not silently substitute another DID.
4. Obtain explicit required role/activity consent. Moderator standing requires
   its normal, separate grant. Notification-room consent is separately recorded
   by the room's authorized controller/participants, never inferred from an invite.
5. Recheck status, expiry and bindings and **atomically** consume the invitation
   and create the durable enrollment record in one local ledger transaction.
   Bind the verified DID/PDS, cohort, consent references and existing credential
   custody references, without credential bytes. External identity/credential
   work precedes this transaction; the transaction creates no PDS account.
6. A retry for the same completed transaction can return the existing enrollment
   receipt. It cannot create another enrollment or make the invite reusable.

Declining or abandoning enrollment does not consume the invite, create membership,
assign a role or enlist a room. The owner may revoke it; otherwise it expires.
Record an explicit decline separately if needed without treating it as consent.
Partially completed credential setup follows existing private enrollment cleanup;
it creates no community authority merely because it exists.

## Lifecycle and bounded acceptance

Expiry is effective at check time even before an explicit ledger update marks
`expired`. Revocation is allowed before consumption; later withdrawal uses the
normal enrollment/role withdrawal path and never restores invite usability.
Concurrent consumers, revoke/consume and expire/consume transitions serialize
through the ledger transaction. Unknown, malformed, revoked, expired, already
consumed or mismatched invitations refuse without creating enrollment state.
Issuance and consumption receipts survive host-loss reconstruction with the small
operational state; no new geographic DR or recovery-key requirement is introduced.

Before accepting implementation, exercise one normal owner-issued enrollment,
decline/abandon, expiry, revocation, reuse, malformed/unknown and identity/cohort
mismatch; prove exactly one enrollment under concurrent consumption and safe
retry after interrupted receipt delivery. Prove that missing identity, scope,
role/activity consent or required room consent cannot be bypassed by an invite.
Use synthetic participants for machinery checks; real cohort and room consent
remain human decisions.

This lane adds only entry authorization to existing enrollment. It promises no
public registration, general availability, PDS hosting, SLA or moderation outcome.
