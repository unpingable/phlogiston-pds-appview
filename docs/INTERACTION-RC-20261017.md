# Interaction release handoff — proposed

The final engineering slice for [#51](https://github.com/unpingable/atproto-community/issues/51)
is prepared on isolated branches. Runtime implementation lives in
`atproto-community/apps/community-live`, while this repository owns the composed
product/deployment. Public source is `unpingable/phlogiston`.

The frozen implementation is `bf10f79f49643999146b80a6c4e3f732b975a99e`; public
candidate is `860fcae4b9a97ee47982c487e7d9bc6659fefe39`. The independently reviewed
candidate reuses existing opt-in interaction work and fixes consent, disconnect,
account isolation and uncertain-effect recovery. It preserves the accepted reader,
Cabinet, curation and attention functionality. No unrelated branch was merged.

TypeScript, 340 named unit/integration cases and 17 Chromium checks pass. Independent
source review ran 26 cases and resolved eight material findings. Actual disposable
PDS OAuth and public record readbacks cover consent, refusal, posts/replies, likes/
reposts, undo, lost-response/restart recovery, Disable, old-refresh refusal and reader
reconnection. Private implementation PR contains complete receipts and limitations.
The wider Python suite passed 1,485 cases; its one fresh-checkout permission failure
was corrected by restoring specified local pause fixture modes, and all 29 affected
cases passed. One unchanged Ruff formatting failure remains explicitly recorded.

[Exact artifact and proposed procedure](../deploy/production/interaction-rc-20261017/README.md).
Archive SHA-256: `cb68d85ea7ee8ff7d31b74c6e215834609dcda860061d04db08d80e5a46a475e`.

Read-only current live service and public source readback confirm `26b0c5f`, not the
older `43053e4` still named at the top of P0-IMPLEMENTATION-HANDOFF. No change to the
live service was made. This candidate is not release acceptance or announcement.
#32 requires actual selected-revision readback; #37/#38 retain their explicit owner
policy decisions; #35 remains the owner's announcement. Closed L0 work stays closed.

PDS readiness is independently tracked by #10/#40 and PR #3, aimed at the two
owner-selected first account holders. Client release does not defer that work;
PDS recovery/email/migration/consent evidence does not grant public registration
or real-user invitations. Report its readiness separately.

Formalization consideration: under the existing serialized producer, pinned hashes
and unchanged private-state schema, source packaging preserves byte identity and a
completed guarded rollback restores the exact previous web generation. Independent
reproduction/file-hash checks and existing producer receipts suffice here. No
power-loss atomicity, provider-effect rollback or full disaster recovery is claimed.
Decision owner is root engineering for packet correctness and the owner for release.
