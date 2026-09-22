# Deployment preparation boundary

This Compose file is a local qualification job, not an AppView service. It
requires `PHLOGISTON_RENDER_IMAGE` in the exact untagged
`registry/path/image@sha256:<64 lowercase hex>` form; `compose-qualify.sh`
rejects tags before invoking Compose. It deliberately has no default image.
Its network namespace is disabled, it publishes no port, and it mounts the
project read-only so the renderer can accept only its installed fixture.

`output-parent` is an existing bind mount, but the renderer refuses it as a
direct target: it creates only a new run-id child plus a sibling receipt. The
systemd artifact is an uninstalled `phlogiston-appview@.service` template. It
uses a systemd-created `StateDirectory` at `/var/lib/phlogiston-appview-runs`
with mode 0700 and needs an exact non-placeholder source revision before it can
succeed. The local real-command test uses a temporary root; no service is run.

No production container, Caddy route, DNS record, TLS configuration, firewall,
PDS, account, credential, or persistent process is represented by this file.
