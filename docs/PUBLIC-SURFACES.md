# Public surfaces — current Phlogiston identity

Updated 2026-10-03 by owner instruction. Phlogiston owns its vocabulary:
`app.phlogiston.community.*`, not Juche or neutral.zone. The eight schema
structures remain unchanged; document IDs, digests, collection paths and OAuth
scopes move together before canonical publication. Old prototype records and
frozen evidence remain untouched, with no new compatibility promise.

| Hostname | Current role | Boundary |
| --- | --- | --- |
| `phlogiston.app` | Static pre-launch explainer; intended future `community-live` participant origin | No signup, OAuth endpoint, community service or PDS activated by the explainer. At admitted integration, replace the complete static Caddy block with the PCV0 app block at the same origin |
| `community.phlogiston.app` | DNS-only authority for `app.phlogiston.community.*` | `_lexicon.community.phlogiston.app TXT did=<dedicated authority DID>`; no HTTP service or account inferred |
| `lexicon.phlogiston.app` | Proposed dedicated schema publisher handle | `_atproto.lexicon.phlogiston.app` custom-handle binding after approved enrollment on existing Bluesky hosting; actual assigned DID/PDS recorded mechanically |
| `phlogiston.social` | Same static pre-launch explainer; deferred operator PDS infrastructure | No PDS, account or enrollment activated. Keep this separate static block during .app integration; change it only at separately authorized PDS activation |
| `community.neutral.zone` | Superseded prototype namespace/site | No canonical Phlogiston publication or new runtime compatibility obligation |

The pre-launch static site is source-controlled in `public/prelaunch/index.html`;
`deploy/prelaunch/Caddyfile.fragment` selects only `/` and `/index.html` on both
`phlogiston.app` and `phlogiston.social`, using separate marked site blocks.
The `.social` explainer remains when the `.app` block is replaced at admitted integration.
Application, OAuth and protocol routes refuse. The page makes no user,
registration, PDS hosting, availability or durability promise.

## Retained topology mechanics

The earlier September topology inspection below supplies implementation
mechanics only. Its old neutral namespace and planned PDS continuity wording
are superseded by this current identity and zero-user product scope.

## Why phlogiston.app

The protocol facts rule out the root of `phlogiston.social`: it is owned by
the PDS (routes, well-known documents, OAuth authorization server, handle
domain), and the wildcard is the hosted-handle and on-demand TLS namespace.
A front door there would put the OAuth client on the same name as an OAuth
authorization server, which looks like an account provider, and would need
fragile path allow-listing that breaks on any PDS upgrade.

Between the remaining candidates the owner chose the application's own
brand. `phlogiston.app` already resolves to the host, has no protocol role,
and needs no front-door DNS change. Lexicon authority is DNS-only and does not
need an HTTP site at `community.phlogiston.app`. The earlier noun-count
argument for `neutral` was already weakened by the consent-page inspection:
the participant's own PDS (oauth-provider-ui 0.10.3) shows the permission as
"Repository · Publish changes" and names the `app.phlogiston.community`
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
  any hostname. The current scope is `repo:app.phlogiston.community.submit`; old grants cannot
  authorize this renamed collection.
- `community.neutral.zone` currently has an A record to GitHub Pages
  (185.199.109.153) and no `_lexicon` TXT. This old namespace will not receive canonical Phlogiston publication; see [DNS-CUTOVER-PREP.md](DNS-CUTOVER-PREP.md).

## Consequences

- atproto-community: `COMMUNITY_PUBLIC_URL`, the PCV0 `Caddyfile.fragment`
  site line, `community-notify.toml` `public_base_url`,
  `campaign.example.json` `publicOrigin`, the deployment validator's
  `PUBLIC_ORIGIN` and the test fixtures move to `https://phlogiston.app`
  (done in that repository's Phase 2 freeze lane). `LEXICON_DNS_NAME` and
  the publisher contract move to `community.phlogiston.app`.
- No DNS change for the front door. The `_lexicon` TXT is published at
  lexicon publication, as already planned.
- `community-live`'s OAuth `client_name` follows `COMMUNITY_NAME`, so the
  consent page shows the community's own name.
- The full per-path collision analysis is retained in the tranche closeout
  at the workspace root.
