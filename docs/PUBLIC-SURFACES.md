# Public surfaces — what the three names mean

Decided 2026-09-25 from inspection of the deploy configuration, the pinned
PDS image (`@atproto/pds` 0.5.34, inspected offline), and read-only DNS
lookups. No DNS, TLS, or host state was changed. Principle: minimize the
number of public nouns a participant must understand.

| Hostname | Role | Protocol constraints | Participant-facing? | Decision |
| --- | --- | --- | --- | --- |
| `community.neutral.zone` | The community site (`community-live`): pages, `/d/<rkey>` permalinks, OAuth `client_id` and redirect, notifier permalinks | `_lexicon.community.neutral.zone` TXT is the permanent NSID authority for `zone.neutral.community.*` (DNS-only, sibling label, no conflict with serving HTTP) | Yes | **The one front door for Phase 2** |
| `phlogiston.social` (root) | PDS service hostname; operator infrastructure (community actor, backups, invite-only accounts) | PDS owns `/`, `/xrpc/*`, `/.well-known/{atproto-did,oauth-authorization-server,oauth-protected-resource}`, `/oauth/*`, `/account*`, `/tls-check`; appears in hosted accounts' DID documents; OAuth authorization server | No | Protocol-only. Never a front door; path routing is not safe |
| `*.phlogiston.social` | Hosted handles | Wildcard route with on-demand TLS gated by the PDS `/tls-check` | Only for accounts hosted there (not Phase 2) | Protocol-only |
| `community.phlogiston.social` | Not configured | `community` is a reserved handle subdomain, so no account can claim it; would need an exact-host Caddy site with ordinary ACME (the on-demand ask refuses it) | Would be | Fallback only: technically clean, but adds a second noun and reads like a handle |
| `phlogiston.app` | Operator, status, and account surface; optional "Go to the community" pointer | Own origin, own OAuth client, no protocol role | Optional, never required (PD-E) | Keep as is; not the front door |

## Why community.neutral.zone

`neutral` is already an unavoidable noun on the participant's path: the OAuth
scope `repo:zone.neutral.community.submit` appears on the consent page of the
participant's own PDS, and that namespace is permanent. Using
`community.neutral.zone` for the URL, the permalinks, and the OAuth client
means a participant meets one new noun. Any `phlogiston.*` host adds a
second, and the root of `phlogiston.social` would additionally put the OAuth
client on the same name as an OAuth authorization server, which looks like
an account provider.

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
