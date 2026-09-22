# Synthetic production activation packet

Status: prepared, not authorized. Deployment does not authorize any step here.
Each operation stops on stale identity, missing receipt, dependency failure,
unexpected authority, or an indeterminate write result.

| Step | Required authority | Executor and exact input | Expected transition and evidence | Stop and recovery |
|---|---|---|---|---|
| 1. Enroll | Account owner plus application-session authorization only | Owner submits the designated handle at `/oauth/login` and completes the callback | DID/PDS binding, opaque eight-hour session and server-side DPoP custody; before/after authority census proves zero community records | Revoke the same OAuth session and expire the browser session; never try a second account to settle ambiguity |
| 2. Prove separation | Read-only inspection | Owner loads `/me`; observer reads exact DID | Authenticated DID is present and membership is explicitly absent | Any automatic membership is a gate failure; revoke and preserve evidence |
| 3. Add membership | One exact community operator authorization | Operator submits one pre-recorded operation ID, community DID and member DID to `communityd` | Durable operation receipt plus projected active membership for the exact DID | Reconcile the same operation ID; never replay with a fresh ID; inverse needs separate authority |
| 4. Admit one record | Account owner record write plus exact admission authority | Owner creates the bounded fixture; operator supplies its exact URI/CID to `communityd` | PDS record, admission record, projection and public rendering agree | Stop on URI/CID mismatch or uncertain write; reconcile exact references |
| 5. Verify rendering | Anonymous read only | Verifier loads `/community/` and the operator provenance view | Allowlisted content/state renders; no private evidence or extra record appears | Preserve authoritative state and roll back only presentation if unsafe |
| 6. Remove | One exact community removal authorization | Operator submits the original URI/CID and removal operation ID | Removal receipt and projection hide the record while retaining provenance | Reconcile the same removal; never delete the PDS record as a substitute |
| 7. Verify persistence | Restart/reconciliation authorization, no new authority write | Operator restarts/rebuilds observer and repeats the read | Removed content remains hidden; no duplicate authority action | Fail closed and retain prior projection until rebuilt from authority |
| 8. Remove membership | Separate inverse membership authorization, only if selected | Operator submits exact DID/community and inverse operation ID | Authority and projection agree membership is absent | Do not infer membership removal from logout |
| 9. Logout/revoke | Account owner | Owner submits the CSRF-bound logout, then disconnect operation | Cookie expires, OAuth session is revoked, community records unchanged | If revocation is uncertain, deny local use and reconcile that session |
| 10. Re-enroll | Account owner plus session authorization | Owner repeats OAuth with the same account | New session binds the same DID; prior authority standing is preserved, not recreated | New DID or invented membership stops the exercise |
| 11. Backup | Backup operator, stopped-writer maintenance authority | Operator runs the exact integrated capture to the verified `phlogiston-production` destination | Checksummed manifest plus clean restore prove authoritative records and reconstructed projection | Preserve live state; failed backup never becomes current recovery evidence |

## Boundary

The required authorities are deliberately separate: account-owner OAuth,
Phlogiston session creation, community operator effects, and backup custody.
No successful earlier step grants a later one. The activation operator must
name the exact synthetic account, community DID, record fixture, authority
principal, backup destination, and rollback identities before starting.

No real/owner/external account, public registration, Lexicon publication, DNS
change, or general community activation is included in this packet.
