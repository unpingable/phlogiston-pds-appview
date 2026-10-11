# P0 implementation handoff

The owner accepted the self-service public-playground successor on 2026-10-11. Component source and executable profile live in atproto-community, under BUILD.md P0 and docs/P0-LAUNCH-CONTRACT.md; this repository composes the release and does not duplicate community-live or communityd. Integration issue#1 and demo#6 yield to the bounded outcome in https://github.com/unpingable/atproto-community/issues/8. Historical two-human dogfood remains unclaimed; no recruited testers or notification room are prerequisites.

## Product boundary

phlogiston.app is the actual product, using ordinary Bluesky-hosted participant identities and their PDS records. The approved dedicated lexicon.phlogiston.app publishing intent uses existing Bluesky hosting; community.phlogiston.app remains DNS-only schema authority. Phlogiston.social identity hosting, migration, blobs, registration and PDS recovery stay deferred until a concrete user benefit warrants separately admitted work. No PDS build or service change is needed here.

The owner subsequently permitted explicitly designated Juche accounts as temporary integration-test infrastructure only. Use an isolated app and exact configured test-host exception with protected test credential custody. Do not infer Bluesky compatibility from that result; never make Juche the public fallback or migrate participants. The public profile rejects those test overrides.

## Successor implementation

Use the existing community kit's explicit `deploy/public-community-pcv0/p0/` profile: one community, one moderator, existing-public-post submission, manual root-only admission, durable per-DID/intake limits, separate site/admission pauses, private exact-subject decline/status, bounded observer candidate paging and optional notifier absent. New-DID streaming and recovery are separately qualified; a fixed-repository test poller is insufficient. No new schemas, feed/ranking or governance machinery.

The old frozen community archive remains unchanged historical custody. It cannot qualify these new controls. The successor must pass full source and installed-artifact qualification and receive new exact source/artifact/configuration identities before cutover. Preserve original schema digests and receipts; no rebuild or source tip may silently replace accepted runtime bytes. No new archive is declared qualified by this handoff.

## Activation still separate

Q2 and publisher account/location intent are already approved. Do not ask for those decisions again. Required unresolved activation evidence includes actual publisher DID/PDS and exact actual-manifest acceptance; canonical eight-document publication/readback; exact OAuth origin and credential custody; single-writer/principal preflight; application recovery/rollback; and controlled ordinary-Bluesky OAuth→write→actual-stream→bounded-queue→admit/decline→anonymous-render, with custody, DID, scopes, duplicates and observer recovery. Authentication alone, local fixtures and Juche tests do not pass this provider gate.

Existing test credentials must be explicitly authorized and enrolled through secure custody; never include private bytes in a packet. The application can recover independently of running a PDS. Public activation, DNS, production enrollment, permanent Lexicon publication and real seed posting remain separately authorized actions. Keep the two marked static site blocks intact until the accepted app-only cutover; no change to the `.social` block is part of P0.
