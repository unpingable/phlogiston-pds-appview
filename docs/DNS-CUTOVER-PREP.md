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
| `community.neutral.zone` | A | not needed for Phase 2 | none required. Leave the Pages record or remove it at the owner's discretion; do **not** create an A record to the host (the site role is retired) |
| `_lexicon.community.neutral.zone` | TXT | `did=<schema authority DID>` | at lexicon publication only, by the owner, per the PCV0 README's publication gate. The value is the dedicated schema-authority DID, never the community actor |

## TTL notes

- Nothing in the front-door path changes, so TTLs do not matter for
  cutover. Keep the existing `phlogiston.app` TTL.
- If the owner later removes the `community.neutral.zone` Pages record, no
  service depends on it; the TTL only decides how long stale caches keep
  returning the Pages address, which is harmless.
- For the `_lexicon` TXT, use the registrar default; the lexicon publisher
  reads it once at publication and re-reads it on verification. Wait one
  TTL after creating it before running the publisher's DNS check.

## Service target

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

- Front door: restore the previous complete Caddyfile from the byte-for-byte
  backup taken before the PCV0 site block was added, validate, reload. That
  removes the `phlogiston.app` site; the name then resolves to the host and
  Caddy answers with its default (no site) behaviour.
- No DNS change to roll back for the front door.
- If the `_lexicon` TXT was created and publication was aborted, leave the
  TXT in place (it is inert without published records) or remove it; the
  publisher's receipt is the record of what happened.

## Validation commands (read-only; run after the PCV0 Caddy site is live)

```sh
dig +short A phlogiston.app                      # expect 192.46.223.21
dig +short AAAA phlogiston.app                   # expect empty
dig +short A community.neutral.zone              # expect Pages or empty; never the host
dig +short TXT _lexicon.community.neutral.zone   # empty until publication
curl -sI https://phlogiston.app/                 # HTTP/2 200, HSTS header, no cookie
curl -s https://phlogiston.app/oauth-client-metadata.json
#   expect client_id https://phlogiston.app/oauth-client-metadata.json,
#   redirect_uris ["https://phlogiston.app/oauth/callback"],
#   scope "atproto repo:app.bsky.feed.post?action=create repo:zone.neutral.community.submit?action=create"
openssl s_client -connect phlogiston.app:443 -servername phlogiston.app </dev/null 2>/dev/null |
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

`deploy/production/verify-external.sh` was written for the withdrawn
phlogiston-web route (it expects scope `atproto` and a `/community/` 503)
and is not the check for the Phase 2 front door; use the commands above and
[PRODUCTION-VERIFICATION.md](PRODUCTION-VERIFICATION.md).
