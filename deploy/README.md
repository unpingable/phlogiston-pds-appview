# Deployment preparation boundary

This Compose file is a local qualification job, not an AppView service. It
requires `PHLOGISTON_RENDER_IMAGE` to be an immutable digest selected by an
operator; it deliberately has no default image. Its network namespace is
disabled, it publishes no port, and it renders only the fixture supplied by a
read-only bind mount.

No production container, Caddy route, DNS record, TLS configuration, firewall,
PDS, account, credential, or persistent process is represented by this file.
