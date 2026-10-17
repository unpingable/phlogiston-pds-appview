# Native PDS account onboarding and exit: verified standing, 2026-10-17

This is the separate hosted-identity work under [#10](https://github.com/unpingable/atproto-community/issues/10) and [#40](https://github.com/unpingable/atproto-community/issues/40). It does not gate the existing-account client release. No real-user invitation, public registration, production configuration change, or deployment is included. Intended cohort identity and consent remain in private operator custody.

## What actually works

The deployed stock PDS answers `0.4.5037`. Public registry inspection on this date found `0.4` and `latest` pointing to index `sha256:3a8feb3415e319dbcc13372293b7ef1fb05a318a6ff1d55968cf99ba6633c5d4`; its amd64 member is the deployed `sha256:74c650cd620eee2e6e0272b4cb76036a0271523b1742f61f813b79dc5a8b5273` and labels version `0.4.5037`, distribution revision `ed2dcb8616cd56ceab8e4f34973d2b2c67ea1bd9`. There was no published `0.5` or `0.5.40` image tag. A newer source package alone is not a qualified upgrade image. Do not repeat the accepted [#50](https://github.com/unpingable/atproto-community/issues/50) same-version restore to fill the cross-version obligation.

`https://phlogiston.social/account` renders the upstream account page in Chromium. It offers **Create a new account** and **Sign in**. Creation first asks for a 3–18 character service-domain username; the second step requires invite code, email and password. The native invalid-invite case displays “The invite code is not valid”. Direct `com.atproto.server.createAccount` without a code returns HTTP 400 `InvalidInviteCode`. `describeServer` reports `inviteCodeRequired: true`. Neither negative case created an account.

The page is deliberately navigation-only. A raw HTTP request without `Sec-Fetch-Mode: navigate` and `Sec-Fetch-Dest: document` returns 400; this does not mean `/account` is unavailable. `/.well-known/change-password` redirects to the native `/account/reset-password` route. Route existence does not establish successful email recovery.

A fresh operator fixture was created using the existing protected provisioning kit, without changing DNS, Caddy, registration configuration or OAuth registration. The long-name first attempt was conclusively refused with HTTP 400 `InvalidHandle` / `Handle too long`; exact account lookup found no row, and the unused invite was disabled and verified. A separately recorded shorter intent succeeded. The kit now refuses invalid service usernames before creating a private intent or invite. It retains its existing unknown-outcome reconciliation behavior; it never blindly repeats account creation.

## Current hosted-user blockers

- Outbound SMTP and sender-address configuration are absent. Actual verification, password reset, email change, email-dependent account deletion and lost-session recovery are not qualified. Deploying mail configuration and any credentials requires separate owner authorization; do not substitute operator-held user passwords or logged reset tokens.
- The live server exposes no Terms/Privacy links in `describeServer` (`links: {}`, `contact: {}`). The native signup consent text names those policies but renders no hyperlinks. Existing client policies distinguish externally hosted accounts; hosted-identity custody requires its own accepted disclosures and discoverable support contact before signup. Existing 18+ eligibility and no-paid-legal-review decision remain intact; no new legal clearance is asserted.
- Native invalid and missing invite refusal are demonstrated. Expiry, one-use consumption/race, disabled-code refusal, capacity reserve and partial-creation reconciliation across both native and XRPC paths are not all qualified. Do not describe a `useCount: 1` code as expiring or a missing signup link as an admission control. No new invitation daemon or account-management system is introduced.
- Exact chosen-handle DNS and valid TLS must be verified before user onboarding. Wildcard DNS does not establish wildcard TLS. DID-based disposable OAuth testing does not qualify handle discovery for real account holders.
- #50's exact same-version blank-host restore and the existing daily encrypted/off-host verified backups remain accepted. No blobs existed in #50. Real migration/cutover, external DID/service binding, relay/client behavior, grants and app-password consequences, interrupted migration and refusal/rollback remain unqualified. Current public image tags provide no newer version for cross-version restore.
- The actual hosted-user consent, initial account cap/reserve, operator-unavailability custody and wind-down disposition still require owner acceptance. This work does not accept the separate outstanding moderation reconsideration, decline-category or Cabinet-retention decisions.

## Account-holder guide prepared for activation

This is a draft for operator review, not an invitation. Use an existing account with `phlogiston.app` today if desired; hosted accounts are currently unavailable to real users.

After the separate hosting gates and owner activation decision, the operator privately confirms that each prospective account holder wants experimental hosting and supplies the accepted hosting terms, privacy/data-custody notice, support contact, limitations and exit instructions before issuing a code. The account holder visits the **stock** `https://phlogiston.social/account` page, chooses **Create a new account**, enters an accepted username and their private code, and supplies their own email and password. Never send the password to the operator. Complete actual email verification and recovery qualification before relying on the account. An invitation does not grant Cabinet membership, moderator authority or client write permissions.

Account management belongs to the same upstream `/account` page. Disposable-fixture inspection verified the Account panel offers email verification, email/username/password management, 2FA (requires a verified email), deactivation and deletion, plus separate Devices and Apps pages. Only availability was inspected: none of these account-changing workflows has passed end-to-end qualification. An unremembered native inspection session signed out through its account menu and returned to the welcome screen. Closing an earlier clean browser without explicit sign-out is not evidence that every server-side device session was revoked. Ordinary Phlogiston sign-in uses provider OAuth and the same optional, separately authorized interactions as an external account. Disconnecting the client and revoking its grant do not delete the hosted identity or public repository.

For exit, retain access to the account's confirmed email and owner credentials, export the repository and separately retain every blob, and verify the destination's migration prerequisites. Follow the [upstream migration procedure](https://github.com/bluesky-social/pds/blob/main/ACCOUNT_MIGRATION.md) only after a disposable end-to-end rehearsal of the exact procedure. A repository export is not a full account backup: DID authority/service bindings, blobs, sessions, app passwords and OAuth grants have separate continuity conditions. No lossless migration, automatic grant transfer, post-effect rollback or recovery from operator disappearance is promised by current evidence. Do not delete/deactivate the source as a substitute for a verified migration.

## Prepared upstream configuration change (not installed)

Use existing upstream environment settings; no custom account service is needed. The exact patch requires owner-selected public hosting-policy URLs, support address, verified sender and protected SMTP credential custody:

```text
PDS_INVITE_REQUIRED=true
PDS_TERMS_OF_SERVICE_URL=<accepted public hosting terms URL>
PDS_PRIVACY_POLICY_URL=<accepted public hosting privacy URL>
PDS_CONTACT_EMAIL_ADDRESS=<operator support email>
PDS_EMAIL_FROM_ADDRESS=<verified outbound sender>
PDS_EMAIL_SMTP_URL=<protected SMTP URL; never commit or log>
```

These are proposal fields, not executable configuration. The upstream names are declared in `packages/pds/src/config/env.ts`; `config.ts` maps policy URLs to the provider's policy links and requires the SMTP URL and sender together. Verify against the exact deployed upstream image before installing. Keep user invitation allocation (`PDS_INVITE_INTERVAL`) unset; the inspected upstream default is no recurring user-issued invite allocation. No short-lived-invite or account-cap enforcement is implied by these settings.

At the separately authorized configuration transaction, preserve the whole existing protected environment and state; never rerun `configure` or regenerate keys/secrets. Change only the accepted assignments using the established deployment procedure, retain an exact protected rollback copy, and verify native signup links, `describeServer` policy/contact output, invite-required behavior and actual mail delivery/recovery with a disposable deliverable mailbox. A working client policy URL is insufficient until its text actually covers hosted identity custody. SMTP must not be tested by sending to prospective real users or exposing recovery tokens in logs. This proposal does not authorize credential provisioning, DNS records, service restart or production installation.

## Evidence and bounded formalization consideration

Private operational receipt: `phlogiston-pds-20261011/native-onboarding-7164e26d-f474-4f90-8025-b5883a4c42f5/` in the existing portfolio campaign custody. It records only public identities and classifications; private fixture credentials remain separately protected. The definite failed-account result and invite-retirement receipt are retained. After rechecking no account, zero uses and the disabled code, the exact failed private intent was retired (332 bytes); its generated password no longer has a recovery consumer. Successful fixture custody is owned by the client qualification supervisor until its records and grants are retired. Upstream `com.atproto.admin.deleteAccount` is available for exact disposable-fixture cleanup after test closeout; this does not qualify the account holder’s email-dependent deletion workflow.

Proposition: preflight refusal of an invalid service-domain username performs no invite/account request and publishes no private account intent. Source: `provision` in `src/phlogiston_appview/pds_ops.py`; regression cases in `tests/test_pds_ops.py`; decision owner: PDS lane, independently reviewed by the parent. Practical tests suffice for this small local precondition. This proves neither all upstream reserved-name/email constraints nor provider effect idempotency. The existing journal/reconciliation contract remains unchanged. No historical verdict is changed by the fixture correction.
