# Production-only verification — Phase 2

Status: **prepared, not run.** These checks exercise what no isolated
harness can: real handle and PLC resolution, the real Jetstream feed, the
real room webhook, real token refresh over hours, and the public internet
path. They run only against the live deployment, after
[Q2-ACTIVATION-RUNBOOK.md](Q2-ACTIVATION-RUNBOOK.md) action 5 and before
action 7. Every check refuses to run unless `PHLOGISTON_PRODUCTION_VERIFY=1`
is set and an absolute, not yet existing receipt path is given as the first
arguments; `tests/test_production_verification.py` pins that refusal. The
scripts are in `qualification/production/`.

Receipts are JSON (`phlogiston.production-verification.v1`), mode 0600,
secret-free by construction: no token, password, cookie or webhook URL is
ever written, and the only credential any check reads (the integration
identity's app password) comes from a 0600 file named by an environment
variable and is handed to the writer through the environment, never as an
argument.

Identities: use the operator's own PCV0 integration identity for the checks
that write (indexing lag) or hold a session (OAuth continuity), never a
participant's. The record the lag check writes is a real pending submission;
the moderator leaves it unadmitted or admits and removes it, and the room
sees exactly one "pending" line for it, which the idempotence check then
proves is sent once.

| # | Check | Script | Where it runs | What it proves |
| --- | --- | --- | --- | --- |
| V1 | Real handle and PLC resolution through community-live's own path | `verify-identity-resolution.sh --handle <handle>` | any machine | `POST /oauth/login` resolves the named handle (DNS TXT or HTTPS well-known, cross-checked independently) to its DID, the DID's PDS via `plc.directory`, and redirects to that PDS's authorization server. The redirect is not followed; only its origin and the timing are recorded. Side effect: one short-lived PAR entry |
| V2 | Jetstream arrival and indexing lag | `verify-indexing-lag.sh --did <integration DID> --intent <new absolute occurrence intent> --rkey <preallocated key>` with `PHLOGISTON_VERIFY_APP_PASSWORD_FILE` | the host (observer on loopback) | one controlled `app.phlogiston.community.submit` record (root submission of the identity's own latest post) is written at the preallocated key. The durable intent is fsynced before dispatch. A lost create response is reconciled only by exact `getRecord` readback at that key; an absent attempted record is indeterminate and is never redispatched. PASS requires the observer's `first_received_at` and exactly one moderation-queue entry for the same URI. |
| V3 | One qualified notification with idempotence proof | `verify-notification-idempotence.sh --uri <from V2> --cid <from V2> [--room-observation "..."]` | the host, as root | waits for the notifier cursor to hold the `pending <uri> <cid>` key exactly once (the cursor is written only after the room accepted the message); stops the unit; polls once in the foreground as `community-notify` and requires `sent=0, baselined=0`; starts the unit; after two poll intervals requires the cursor bytes unchanged and no baseline/failure journal lines. The operator's statement of what the room showed is recorded verbatim |
| V4 | OAuth long-duration continuity | `verify-oauth-continuity.sh --did <integration DID> --hours N` | the host, as root | first writes a same-service-identity, secret-free baseline containing the SDK's ISO `expires_at` string, then schedules a transient timer with that baseline's exact SHA-256. Before final session restoration, the timer refuses a short elapsed interval or a baseline that could still be valid at the boundary. It then requires a 200 `getSession` read for the DID, takes currentness at actual read completion, and accepts only an advanced final expiry current at that instant. |
| V5 | Signed-out permalink from outside | `verify-external-permalink.sh --rkey <admitted rkey> --from "<network path>"` | a machine on another network path (refuses on the host or any machine holding the host's address) | `GET /d/<rkey>` with no cookies returns 200, no `Set-Cookie`, no sign-in wall, the community-view note present, TLS verified; the address resolved via 1.1.1.1 and the remote IP are recorded |

## Order and timing

1. V1 first (no state). Run it for the moderator's handle and for one
   integration identity on a different PDS.
2. V2, then V3 immediately (the notifier polls every 30 s; V3 waits up to
   four polls for the cursor).
3. V4 is scheduled during the same session with N at least 12 (Bluesky
   access tokens expire well within that) and, once, N of 72 to cover a
   weekend. Its result is read back before action 7 of the runbook for the
   short window; the long window may complete during the trial and is
   recorded when it does.
4. V5 after the moderator has admitted one discussion (the operator's
   technical verification provides one); run it from a mobile tether or
   another provider, never from the host's network.

## Recording

Put receipts under `/var/lib/pcv0-campaign/production-verification/` on the
host (V1 and V5 receipts are copied there from the machine that ran them)
and list their paths and `status` values in the campaign record. A `fail`
receipt stops the runbook at action 6; fix in the owning repository, redeploy
at a new pin, and rerun the failed check with a new receipt path. Never
edit a receipt.

Before V1--V5, the admitted occurrence validates the exact installed
`qualification/production/` directory against the separately pinned
`production-verifier-manifest.json` with
`validate-production-verifier-closure.py`. The validator accepts only the
manifested regular-file set and exact digests; extra paths, links, missing
members, and substitutions refuse. This source tree and its manifest are not
an authorization to install or run the checks.

## What these checks do not claim

They do not prove product comprehension, demand, or moderation load; those
are the trial's observations. They do not exercise the fault-injection
exercises (the PCV0 README's supervised integration does). They do not
test the withdrawn phlogiston-web route.
