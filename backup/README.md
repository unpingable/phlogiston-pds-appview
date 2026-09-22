# Backup preparation

Only the synthetic snapshot, rendered static files, and render receipt belong
to this campaign. The archive helper verifies the exact input hash, renderer
source hash/revision, and output member manifest before producing an exact
two-member archive (`index.html`, `receipt.json`). No PDS database, actor
repository, blob, account, or credential is an input. A future production use
needs a separately approved application-consistent backup design; this
directory is intentionally not one.
