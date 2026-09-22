# Phlogiston PDS/AppView — bounded synthetic qualification

This is **not** a network AppView, PDS, firehose consumer, identity service, or
deployment of `phlogiston.app` or `phlogiston.social`.

It is a deterministic, read-only renderer for an explicitly supplied local
snapshot bearing only synthetic identities.  It demonstrates the smallest
honest interpretation of an AppView for this campaign: a manifest-bound static
presentation whose inputs, output, and limits are inspectable.  It cannot
discover ATProto content, authenticate, contact a PDS, proxy AppView methods,
receive a firehose, or make a repository mutation.

## Local qualification

```text
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m phlogiston_appview.render \
  --snapshot "$PWD/fixtures/synthetic-snapshot.json" \
  --output-root /tmp --run-id phlogiston-static --source-revision 0123456abcdef
```

The renderer refuses non-`did:example:` identities, snapshots outside its
installed `fixtures/` root, unknown fields, duplicate item IDs, symlink/path
escape, non-canonical parents, reused run children, and placeholder revisions.
The output root is an existing secure parent; each run owns one new child and a
sibling receipt. The v2 receipt binds raw input bytes, renderer implementation
bytes/revision, claimed source revision, and the exact output-member hashes.
Its output contains no live endpoint, credential, or mutable action.

## Community integration candidate

The `campaign/community-integration-20260922` line adds a bounded application,
OAuth enrollment, and operator surface over the existing `atproto-community`
authority and projection interfaces. See [the integration map](docs/COMMUNITY-INTEGRATION.md),
[OAuth/session contract](docs/OAUTH-SESSION-ENROLLMENT.md), [operator contract](docs/OPERATOR-SURFACE.md),
and [integrated recovery contract](docs/INTEGRATED-RECOVERY.md). It is not
activated or deployed.

## Authority boundary

`deploy/`, `backup/`, `restore/`, `rollback/`, and `uninstall/` are operator
preparation artifacts. They fail closed unless used against an explicitly
approved target. They grant no authority to modify DNS, TLS, Caddy, a PDS,
accounts, keys, host state, or Constellation.
