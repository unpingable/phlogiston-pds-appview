# Synthetic production activation packet

Status: prepared, not authorized. Deployment does not authorize any step here.
Each operation stops on stale identity, missing receipt, dependency failure,
unexpected authority, or an indeterminate write result.

| Step | Required authority and operation | Evidence / success predicate | Stop and recovery |
|---|---|---|---|
| 1. Enroll | Owner of one designated controlled synthetic account completes ATProto OAuth at `https://phlogiston.app/oauth/callback`; application authority permits session creation only. | OAuth subject DID/PDS binding, opaque eight-hour browser session, server-side DPoP custody; no membership/action records. | Revoke the same OAuth session and expire the browser session. Never try another account to settle ambiguity. |
| 2. Prove separation | Read identity/session and community projection only. | Authenticated DID is present and membership is explicitly absent. | Any automatic membership is a gate failure; revoke and preserve evidence. |
| 3. Add membership | Separately authorized community operator submits one intent-bound membership operation to `communityd`. | Durable authority receipt plus projected admitted membership for the exact DID. | Reconcile the same intent; never replay with a fresh id. Remove only through a separately recorded inverse operation. |
| 4. Admit one record | Account owner creates one bounded test submission; community operator/admission policy processes that exact URI/CID. | PDS record, admission authority record, observer projection, and public rendering agree. | Stop on URI/CID mismatch or uncertain write; reconcile exact references. |
| 5. Verify rendering | Anonymous read of `/community/` and operator provenance inspection. | Allowlisted content and states render; no private evidence or extra records appear. | Preserve authoritative state and remove route only if the presentation is unsafe. |
| 6. Remove | Separately authorized community operator records removal of the exact admitted record. | Removal authority receipt and projection hide the record while retaining provenance. | Reconcile the same removal intent. Never delete the PDS record as a substitute. |
| 7. Verify persistence | Restart/reconcile observer and reread public/operator views. | Removed content remains hidden and no duplicate action appears. | Fail closed and retain the prior projection until rebuilt from authority. |
| 8. Remove membership | If explicitly selected for the experiment, submit the exact inverse membership operation. | Authority and projection agree that membership is absent. | Do not infer membership removal from logout. |
| 9. Logout/revoke | Account owner logs out; operator verifies local session expiry and server-side OAuth revocation. | Browser cookie is expired, local OAuth session is revoked, community authority records are unchanged. | If revocation is uncertain, deny local use and reconcile that same session. |
| 10. Re-enroll | Account owner repeats OAuth using the same DID. | New session binds the same identity; prior membership/removal standing is preserved and not recreated. | A new DID or invented membership stops the exercise. |
| 11. Backup | Authorized backup operator captures the immediately current integrated state. | Checksummed application-consistent manifest and bounded clean restore prove authoritative membership/action records and reconstructed projection. | Preserve live state; a failed backup never becomes current recovery evidence. |

## Boundary

The required authorities are deliberately separate: account-owner OAuth,
Phlogiston session creation, community operator effects, and backup custody.
No successful earlier step grants a later one. The activation operator must
name the exact synthetic account, community DID, record fixture, authority
principal, backup destination, and rollback identities before starting.

No real/owner/external account, public registration, Lexicon publication, DNS
change, or general community activation is included in this packet.
