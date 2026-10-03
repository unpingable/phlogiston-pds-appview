# Frozen Phlogiston deployment handoff (2026-10-03)

**DO NOT DEPLOY. Credential enrollment and deployment MUST NOT occur until all
three remaining hard gates are satisfied:**

1. Owner approval of the exact Lexicon publication account/location.
2. A consenting second participant/moderator.
3. Consent for the notification room.

Phlogiston Q2 is approved. No further Q2 decision is required. Naming a person
or room alone does not establish consent. Synthetic identities do not satisfy
these human gates. After all three are satisfied, identity resolution and
credential enrollment become mechanical under the existing plan. Permanent
Lexicon publication still requires the existing acceptance of the exact
actual-DID manifest; placeholders confer no publication authority.

## Exact qualified releases — use retained bytes, no rebuild

These identities are copied from the retained `FINAL-RECEIPT.json` in the
`owner-correction-20261003` custody record. Verify each archive SHA-256 before
extraction and use the existing bundled verifier/install/action path. Do not
substitute an older artifact, a latest tag, or a documentation-only source tip.
This terminal documentation pass does not require rebuilding either archive.

| Qualified archive | SHA-256 |
| --- | --- |
| `community-release.tar.gz` | `b7c95d396df935896bfb8054b58cf10253857b8073f1992129775c31a55ce7f1` |
| `phlogiston-inert-release.tar.gz` | `ad35f7ebb6fbcd0ab3ef76a8129b3527237595a60d84ad58c5004b3744009dee` |

Community runtime source: `ed107ed7ed5025ba62c75afa970525eed3bf1707`.
Phlogiston/builder runtime source: `80a868973903d7e5ec478b6e112dbb6147a04923`.
`FINAL-RECEIPT.json` SHA-256: `8e77f9e943f36aafc8b16dfe232e2339d17c7c791781f01cb80d807d9d1e7a04`.
The original receipt, release bytes and acceptance evidence remain unchanged;
the two archives and original receipt are owner-readable, read-only files.

## Canonical Lexicons and unchanged acceptance contract

All eight documents use `app.phlogiston.community.*`. Namespace authority is
`community.phlogiston.app`; DNS binding is `_lexicon.community.phlogiston.app`.
The exact pending account/location proposal is
`LEXICON-PHLOGISTON-APP-APPROVE-OR-REFUSE.json`, SHA-256
`576f988f4c6d1fdc1fe228614bf0304fb3ccc4afbededb0fb4b28ae098ce1f42`,
already referenced by `FINAL-RECEIPT.json`. It proposes dedicated handle
`lexicon.phlogiston.app` on the existing Bluesky hosting service; actual assigned
DID/PDS follows enrollment only after the three hard gates above.
The rebuilt document digests remain those in
[the canonical namespace record](https://github.com/unpingable/atproto-community/blob/ed107ed7ed5025ba62c75afa970525eed3bf1707/docs/PHLOGISTON-NAMESPACE.md).
No schema, namespace semantics, enrollment design or integration scope changes
are made here. Juche and neutral.zone proposals are superseded. Retained old
records/qualification receipts and explicit refusal fixtures are historical
or negative controls, never an operational namespace dependency.

## Resumption boundary

Resume [the existing activation runbook](Q2-ACTIVATION-RUNBOOK.md) directly only
when the gates and its existing mechanical preflight/publication checks pass.
The next product milestone remains owner-authorized submit → admit → render.
Keep the exact current generation/configuration and rollback path; replace the
static explainer Caddy block only in that admitted integration. The static
explainer is already live and is not Phlogiston application deployment.

Zero real users; no irreplaceable user repository state; no current PDS
continuity promise. Total-site-loss recovery is outside the current envelope.
Juche is implementation-reference-only and non-normative for Phlogiston's
operational posture, user commitments, production classification and durability.
Private invitations remain planned future work and add no current launch gate.

**Lane parked. No credential enrollment or Phlogiston deployment performed.**
