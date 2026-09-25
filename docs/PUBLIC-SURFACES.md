# Public surfaces — what the names mean

Decided 2026-09-25 (owner topology decision, final). It supersedes the
earlier front-door memo of the same day that recommended
`community.neutral.zone`; the route-ownership facts from that inspection
(the pinned PDS image `@atproto/pds` 0.5.34, inspected offline, and read-only
DNS lookups) are retained below. No DNS, TLS, or host state was changed by
this decision. Principle: one participant-facing origin, one protocol origin,
nothing else public.

| Hostname | Role | Protocol constraints | Participant-facing? | Decision |
| --- | --- | --- | --- | --- |
| `phlogiston.app` | **The canonical participant-facing/application origin.** Serves `community-live`: participation, the OAuth client (`client_id` `https://phlogiston.app/oauth-client-metadata.json`, redirect `/oauth/callback`), community views, `/d/<rkey>` permalinks, notifier permalinks | Own origin, no protocol role. Caddy site block owned by the atproto-community PCV0 kit → `127.0.0.1:3210`. Ordinary ACME certificate | Yes | **The one front door for Phase 2** |
| `phlogiston.social` (root) | PDS service hostname; operator infrastructure (invite-only accounts, backups). The Phase 2 community actor is a Bluesky-hosted account, not a phlogiston.social one | PDS owns `/`, `/xrpc/*`, `/.well-known/{atproto-did,oauth-authorization-server,oauth-protected-resource}`, `/oauth/*`, `/account*`, `/tls-check`; appears in hosted accounts' DID documents; OAuth authorization server | No | Protocol-only. Untouched. Never a front door; path routing is not safe |
| `*.phlogiston.social` | Hosted handles | Wildcard route with on-demand TLS gated by the PDS `/tls-check` | Only for accounts hosted there (not Phase 2) | Protocol-only. Untouched |
| `community.neutral.zone` | Retired as an application surface. Was the smoke-test/dev origin | `_lexicon.community.neutral.zone` TXT remains the permanent NSID authority for `zone.neutral.community.*` (DNS-only, sibling label). The NSIDs are unchanged | No | Retired as a site; DNS-only lexicon authority retained for future publication. No A record needed |
| `community.phlogiston.social` | Dropped entirely | `community` is in the PDS reserved-handle list, but an operator admin handle update could still claim it, so it must also be reserved operationally | No | Dropped |

## Why phlogiston.app

The protocol facts rule out the root of `phlogiston.social`: it is owned by
the PDS (routes, well-known documents, OAuth authorization server, handle
domain), and the wildcard is the hosted-handle and on-demand TLS namespace.
A front door there would put the OAuth client on the same name as an OAuth
authorization server, which looks like an account provider, and would need
fragile path allow-listing that breaks on any PDS upgrade.

Between the remaining candidates the owner chose the application's own
brand. `phlogiston.app` already resolves to the host, has no protocol role,
and needs no DNS change. `community.neutral.zone` carried only the lexicon
authority role, and that role is DNS-only: the `_lexicon` TXT is a sibling
label and does not need an HTTP site behind it. The earlier noun-count
argument for `neutral` was already weakened by the consent-page inspection:
the participant's own PDS (oauth-provider-ui 0.10.3) shows the permission as
"Repository · Publish changes" and names the `zone.neutral.community`
collection only in a details dialog. What a participant now meets: one site
name (`phlogiston.app`), one client name (the community's own, per
`COMMUNITY_NAME`), and Bluesky.

Once a real person has consented, the origin is sticky: moving it changes the
`client_id` (everyone re-consents) and breaks every permalink already pasted
in the room. The decision is taken before the first invitation.

## phlogiston-web is withdrawn from public routing for Phase 2

`phlogiston-web` (this repository's `web/`, the operator/status/account app
on `127.0.0.1:8092`) was routed at `phlogiston.app`. It cannot share that
origin with `community-live`: both claim `/`, and both use `/oauth/login`,
`/oauth/callback` and `/oauth-client-metadata.json`, so the OAuth client
identity would be ambiguous. For Phase 2 it is therefore withdrawn from
public routing:

- the code and its tests stay (`web/`, 23 tests);
- `deploy/production/phlogiston-web.service` is header-marked withdrawn;
- `deploy/production/Caddyfile.fragment` defines no site block (comment
  only, explaining that the PCV0 kit owns `phlogiston.app`);
- `deploy-inert.sh` installs the release and unit file but enables the unit
  and runs the Caddy transaction only with `--with-status-web` (default off);
- `preflight.py` refuses if the kit fragment defines a `phlogiston.app` site;
- `PHLOGISTON_COMMUNITY_URL` stays optional and is unused: phlogiston.app
  itself is the community.

Bringing it back needs one of two things, neither of which is a Phase 2
task: a distinct hostname with its own site block, its own certificate and
its own OAuth `client_id` (for example a status subdomain of `phlogiston.app`;
never `phlogiston.social` or `*.phlogiston.social`), or a path-mounted
rewrite under `phlogiston.app` with the app's public URL, cookie path and
OAuth redirect all rebased to that prefix, which the app does not support
today. The `/admin/` surface remains outside either option until an operator
authentication bridge is authorized.

## Route ownership (facts retained from the inspection)

- Caddy exact-host sites win over the `*.phlogiston.social` wildcard, and an
  exact-host site must use ordinary ACME: the on-demand ask is dispatched to
  the PDS `/tls-check`, which refuses any name without an account.
- `community-live` sets `Strict-Transport-Security … includeSubDomains` on
  its origin. At `phlogiston.app` that binds only `*.phlogiston.app`, which
  has no other use; at a `phlogiston.social` name it would have bound every
  hosted handle.
- The community DID (`did:plc:b53udqv47g2dayvpstzdefpq`) is independent of
  any hostname. The scope `repo:zone.neutral.community.submit` is unchanged.
- `community.neutral.zone` currently has an A record to GitHub Pages
  (185.199.109.153) and no `_lexicon` TXT. Neither needs to change for Phase
  2; see [DNS-CUTOVER-PREP.md](DNS-CUTOVER-PREP.md).

## Consequences

- atproto-community: `COMMUNITY_PUBLIC_URL`, the PCV0 `Caddyfile.fragment`
  site line, `community-notify.toml` `public_base_url`,
  `campaign.example.json` `publicOrigin`, the deployment validator's
  `PUBLIC_ORIGIN` and the test fixtures move to `https://phlogiston.app`
  (done in that repository's Phase 2 freeze lane). `LEXICON_DNS_NAME` and
  the publisher contract keep `community.neutral.zone`.
- No DNS change for the front door. The `_lexicon` TXT is published at
  lexicon publication, as already planned.
- `community-live`'s OAuth `client_name` follows `COMMUNITY_NAME`, so the
  consent page shows the community's own name.
- The full per-path collision analysis is retained in the tranche closeout
  at the workspace root.
