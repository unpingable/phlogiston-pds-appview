# Activation readiness packet

No step in this document is authorization to activate production.

## Required identities and publication

- Publish the canonical `zone.neutral.community.*` Lexicons from the
  atproto-community authority source, then verify generated consumers with the
  existing drift check. Do not publish a Phlogiston-maintained copy.
- Select exact production PDS image, Phlogiston commit, community commit, and
  locked Node dependency artifacts. Preserve the tested rollback identities.
- Configure `phlogiston.social` PDS identity and `phlogiston.app` application
  identity only after DNS/TLS authority is separately granted.
- Publish HTTPS OAuth client metadata at the application origin and register
  exactly `https://phlogiston.app/oauth/callback`. Cloudflare may terminate or
  proxy ingress later, but it is an ingress seam, not an application
  prerequisite.

## Secrets and custody

Provision independent PDS signing/rotation material, PDS admin secret, OAuth
key material, Phlogiston cookie/session secret, and communityd credentials by
secure references. No admin credential enters a browser session. Backups must
land in the approved durable destination with manifest and restore evidence;
OAuth/browser sessions remain deliberately re-enrollable.

## Initial topology and account sequence

Start with one community-authority PDS and one independent synthetic PDS, then
exercise a synthetic account, owner account, inactive external account, and
active external account in that order. Each real-account enrollment or record
write needs explicit authority. Successful OAuth establishes identity/session
only; a separate community authority decision establishes membership.

## Activation gate

Before any route becomes public, require:

1. immutable artifacts install from a clean environment;
2. DNS, TLS, callback and public metadata match exactly;
3. mounts, secret references, service users, and write owners match the
   approved topology;
4. fresh application-consistent backup and blank-host restore evidence;
5. health/readiness for PDS, OAuth/session service, communityd and observer;
6. explicit tests for non-member, stale projection, revoked session, duplicate
   intent, unavailable authority and one-PDS-unavailable behavior;
7. one separately authorized synthetic lifecycle with exact receipts;
8. rollback retained and an operator expressly authorizing activation.

## Rollback and post-activation checks

Rollback stops new enrollment/effects first, preserves all writes accepted
since activation, and restores the prior immutable application/configuration
generation. It never replaces a newly written PDS with a stale backup.
Trigger rollback on identity/callback mismatch, secret or mount uncertainty,
authority widening, missing receipts, inability to reconcile effects, or
unhealthy authoritative storage.

After activation verify anonymous health, authenticated identity, explicit
non-membership, separately admitted membership, two-PDS projection,
moderation/removal propagation, backup age, one bounded restore rehearsal, and
logout/revocation. Production DNS/TLS, credentials, accounts, records,
deployment, and activation all remain outside this campaign.
