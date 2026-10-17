# Shipped client and operational handoff

Production at `https://phlogiston.app` serves public source
`860fcae4b9a97ee47982c487e7d9bc6659fefe39`, corresponding to frozen implementation
`bf10f79f49643999146b80a6c4e3f732b975a99e`. The exact unchanged archive SHA-256 is
`cb68d85ea7ee8ff7d31b74c6e215834609dcda860061d04db08d80e5a46a475e`.
The previously reviewed client PRs were merged; PDS PR #3 remains unmerged.

The owner authorized one corrective deployment after the first attempt rolled
back at service CHDIR. The correction changed only the producer's execution
`UMask=0077` to `0022`, producing public release directories `0755` and files
`0644`. The archive, manifest, producer, application and dependencies are unchanged.
Private staging remains `0700` and protected receipts `0600`. A permission rehearsal,
all 75 installed file hashes and actual web-user readability were checked.

Occurrence `4f30b945-2ccb-4251-bcc6-b6c0a42a34fd` completed successfully on
2026-10-17. Web invocation `934812a15f6943e189e29ada3b299472` is active/enabled,
with `NRestarts=0`. Only `community-live` restarted. Authority and observer
identities, private state and existing controls/configuration were preserved.

Canonical checks passed for public health, About/source identity, assets, exact
expanded OAuth metadata, help, signed-out Cabinet/permalinks and permission
boundaries. A fresh disposable test-PDS account exercised reader consent and
interaction Off, direct write refusal, mobile Following, explicit social consent,
post/like/repost/reply exact provider readbacks, same-operation deduplication,
reply lineage, owned undo, Disable/provider revocation acknowledgment, reader-only
reconnect, logout and application-data erasure. All test records, the fixture
account/actor key, its scoped invitation and local/remote credentials were retired.

The normal Bluesky OAuth handoff reached `https://bsky.social`; full fresh consent
remains untested because no approved disposable provider credential/browser
consent was available. Previously accepted reader OAuth was not repurposed as
social-consent evidence. No physical power-loss qualification is claimed.
The frozen source qualification and its existing limits remain unchanged.

Full versioned results, original failed diagnostic receipts and correction details
are in the [implementation release record](https://github.com/unpingable/atproto-community/blob/a174ffa/docs/releases/interaction-rc-20261017/CORRECTIVE-DEPLOYMENT.md).

Rollback retains `26b0c5fcb38978707e6ffc763b584dd003aa829b` and the exact previous
managed drop-in at
`/var/lib/phlogiston-campaign/20261017/interaction-permissions-4f30b945-2ccb-4251-bcc6-b6c0a42a34fd/previous-dropin.conf`,
SHA-256 `ba664ebdb0f72c8b2f7d93116e86c84e69b72f4504688cb47bbb449e8310bc10`.
For an authorized rollback, confirm the current managed drop-in hash is this
candidate's `b4c87d897ab62ddc278bf7b545bb9a278e5908401c39680c270740c3ca5a318c`,
restore the saved bytes, daemon-reload and restart only `community-live`; verify
health, About and previous reader metadata. Preserve journals/private state.
Revoking effective write authority additionally requires ending/revoking interaction
sessions; a code rollback does not revoke grants or remove public records.

Existing governance behavior is preserved. The one-reconsideration rule,
moderation-decline categories and Cabinet moderation-record retention remain owner
decisions pending review. PDS email/recovery/consent/identity-cutover blockers remain
independent and unchanged. No real-user invitation, public registration, activation
or public announcement occurred. Shipping this client does not launch hosting.

The duplicate staging archive was retired. The active generation, exact Git archive,
dependency closure, previous generation and minimal receipts remain necessary for
operation/recovery; root release engineering reviews custody at the next release
or October 24. Remote free space remained above the 60 GiB reserve. No SSH key,
VM, image pull or dependency copy was created. The producer is terminal/inactive.
The client workstream is parked; no further implementation or research is running.
