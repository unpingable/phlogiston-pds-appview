# Public surfaces — what the three names mean

Decided 2026-09-25 from inspection of the deploy configuration, the pinned
PDS image (`@atproto/pds` 0.5.34, inspected offline), and read-only DNS
lookups. No DNS, TLS, or host state was changed. Principle: minimize the
number of public nouns a participant must understand.

| Hostname | Role | Protocol constraints | Participant-facing? | Decision |
| --- | --- | --- | --- | --- |
| `community.neutral.zone` | The community site (`community-live`): pages, `/d/<rkey>` permalinks, OAuth `client_id` and redirect, notifier permalinks | `_lexicon.community.neutral.zone` TXT is the permanent NSID authority for `zone.neutral.community.*` (DNS-only, sibling label, no conflict with serving HTTP) | Yes | **The one front door for Phase 2** |
| `phlogiston.social` (root) | PDS service hostname; operator infrastructure (invite-only accounts, backups). The Phase 2 community actor is a Bluesky-hosted account, not a phlogiston.social one | PDS owns `/`, `/xrpc/*`, `/.well-known/{atproto-did,oauth-authorization-server,oauth-protected-resource}`, `/oauth/*`, `/account*`, `/tls-check`; appears in hosted accounts' DID documents; OAuth authorization server | No | Protocol-only. Never a front door; path routing is not safe |
| `*.phlogiston.social` | Hosted handles | Wildcard route with on-demand TLS gated by the PDS `/tls-check` | Only for accounts hosted there (not Phase 2) | Protocol-only |
| `community.phlogiston.social` | Not configured | `community` is in the PDS reserved-handle list, so self-registration cannot claim it (an operator using the admin handle update could, so it must also be reserved operationally); would need an exact-host Caddy site with ordinary ACME (the on-demand ask refuses it) | Would be | Fallback only: technically clean, but adds a second noun and reads like a handle |
| `phlogiston.app` | Operator, status, and account surface; optional "Go to the community" pointer | Own origin, own OAuth client, no protocol role | Optional, never required (PD-E) | Keep as is; not the front door |

## Why community.neutral.zone

The decision rests on protocol ownership, not taste. The root of
`phlogiston.social` is owned by the PDS (routes, well-known documents, OAuth
authorization server, handle domain), and the wildcard is the hosted-handle
and on-demand TLS namespace; a front door there would put the OAuth client
on the same name as an OAuth authorization server, which looks like an
account provider. `community.neutral.zone` is already the permanent lexicon
authority for the records the site writes, so the name carries a real
protocol role. On noun count: the consent page of the participant's own PDS
(oauth-provider-ui 0.10.3) shows the permission as "Repository · Publish
changes" and names the `zone.neutral.community` collection only in a details
dialog, so `neutral` is not unavoidable there; the count argument is weaker
than first stated and was corrected on 2026-09-25 after hostile review. What
remains: one site name, one client name (the community's own, per
`COMMUNITY_NAME`), and Bluesky, under the recommended option; any
`phlogiston.*` option adds a second brand and, for the wildcard, reads like a
handle.

Once a real person has consented, the origin is sticky: moving it changes
the `client_id` (everyone re-consents) and breaks every permalink already
pasted in the room. Decide before the first invitation, not after.

## Consequences

- `PHLOGISTON_COMMUNITY_URL` template stays as it is (commented, naming
  `https://community.neutral.zone`); it is set in the real host env at deploy
  time.
- Owner-gated, Q2-gated: repoint the `community.neutral.zone` A record from
  GitHub Pages to the host, and publish the `_lexicon` TXT at lexicon
  publication as already planned.
- `community-live`'s OAuth `client_name` should follow `COMMUNITY_NAME` so
  the consent page shows the community's own name rather than a fixed
  string.
- The full memo with the per-path collision analysis is retained in the
  tranche closeout at the workspace root.
