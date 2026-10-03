# DNS cutover preparation — Phase 2 front door

Status: **preparation only. No DNS change is made now**, and none is needed
for the Phase 2 front door. This records what the resolver returns today,
what it must return for the trial, and how to verify and roll back the
serving side. Read-only `dig` lookups on 2026-09-25 from the workstation;
no host, DNS, TLS or Caddy state was touched.

## Current records (read-only `dig`, 2026-09-25)

| Name | Type | Value | Meaning |
| --- | --- | --- | --- |
| `phlogiston.app` | A | `192.46.223.21` | the shared host |
| `phlogiston.social` | A | `192.46.223.21` | the shared host (PDS, separate activation) |
| `*.phlogiston.social` | CNAME (wildcard) | resolves to the host | hosted handles, on-demand TLS |
| `community.neutral.zone` | A | `185.199.109.153` | GitHub Pages; HTTPS fails the certificate check, HTTP returns 404 |
| `_lexicon.community.neutral.zone` | TXT | none | not yet published |

No AAAA records were observed for the three names (the external checks in
`deploy/production/verify-external.sh` already assert that for
`phlogiston.app`).

## Desired records

| Name | Type | Desired | Change needed |
| --- | --- | --- | --- |
| `phlogiston.app` | A | `192.46.223.21` | **none** (already the host) |
| `phlogiston.social` | A | `192.46.223.21` | none; PDS activation is separate |
| `*.phlogiston.social` | CNAME | unchanged | none; PDS activation is separate |
| `community.phlogiston.app` | A | not needed for Phase 2 | none required. DNS-only namespace authority; no HTTP site/A record is required |
| `_lexicon.community.phlogiston.app` | TXT | `did=<schema authority DID>` | after approved dedicated authority enrollment and exact-manifest acceptance, executed mechanically, per the PCV0 README's publication gate. The value is the dedicated schema-authority DID, never the community actor |

## TTL notes

- Nothing in the front-door path changes, so TTLs do not matter for
  cutover. Keep the existing `phlogiston.app` TTL.
- `community.phlogiston.app` is a DNS-only namespace authority. No Pages
  record was recovered for this new name, and no HTTP/A record is required.
- For the `_lexicon` TXT, use the registrar default; the lexicon publisher
  reads it once at publication and re-reads it on verification. Wait one
  TTL after creating it before running the publisher's DNS check.

## Service target after admitted integration

Before integration, only the static explainer is served. Replace its complete
BEGIN/END PHLOGISTON PRELAUNCH EXPLAINER block with the existing PCV0 app block;
never append a second site at the same origin. OAuth metadata remains404 until
that separately admitted application activation.

## Application service target

- Caddy (existing shared container) → `127.0.0.1:3210` (`community-live`),
  from the atproto-community PCV0 kit's `Caddyfile.fragment` site block for
  `phlogiston.app`. The phlogiston kit installs no site block
  (`deploy/production/Caddyfile.fragment` is comment-only for Phase 2).
- `phlogiston-web` on `127.0.0.1:8092` is not routed publicly.
- The observer API (`127.0.0.1:8080`) and the authority socket stay local.

## TLS expectation

- `phlogiston.app`: an exact-host site with an ordinary ACME certificate,
  issued at Caddy config load. No on-demand policy applies to it. Verify
  after reload that the certificate's SAN is exactly `phlogiston.app` and
  the issuer is the expected public CA.
- `phlogiston.social` and `*.phlogiston.social`: on-demand TLS only,
  gated by the PDS `/tls-check`, and only once the PDS is separately
  activated. Not part of Phase 2.
- If Caddy already holds a certificate for `phlogiston.app` from the
  earlier phlogiston-web route, it is reused; the site block change does
  not force reissue.

## Rollback

- Front door: restore only the exact replaced Phlogiston site block from the retained
  pre-launch fragment after comparing current configuration, validate and
  reload. Preserve concurrent unrelated shared-host routing changes.
- No DNS change to roll back for the front door.
- If the `_lexicon` TXT was created and publication was aborted, leave the
  TXT in place (it is inert without published records) or remove it; the
  publisher's receipt is the record of what happened.

## Validation commands (read-only; run after the PCV0 Caddy site is live)

```sh
dig +short A phlogiston.app                      # expect 192.46.223.21
dig +short AAAA phlogiston.app                   # expect empty
dig +short A community.phlogiston.app             # no HTTP/A record required
dig +short TXT _lexicon.community.phlogiston.app   # empty until publication
curl -sI https://phlogiston.app/                 # HTTP/2 200, HSTS header, no cookie
curl -s https://phlogiston.app/oauth-client-metadata.json
#   expect client_id https://phlogiston.app/oauth-client-metadata.json,
#   redirect_uris ["https://phlogiston.app/oauth/callback"],
#   scope "atproto repo:app.bsky.feed.post?action=create repo:app.phlogiston.community.submit?action=create"
openssl s_client -connect phlogiston.app:443 -servername phlogiston.app </dev/null 2>/dev/null |
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

`deploy/production/verify-external.sh` was written for the withdrawn
phlogiston-web route (it expects scope `atproto` and a `/community/` 503)
and is not the check for the Phase 2 front door; use the commands above and
[PRODUCTION-VERIFICATION.md](PRODUCTION-VERIFICATION.md).
