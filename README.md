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
  --snapshot fixtures/synthetic-snapshot.json --output /tmp/phlogiston-static
```

The renderer refuses non-`did:example:` identities, non-local snapshot paths,
unknown fields, duplicate item IDs, and a non-empty output target.  Its output
contains no live endpoint, credential, or mutable action.

## Authority boundary

`deploy/`, `backup/`, `restore/`, `rollback/`, and `uninstall/` are operator
preparation artifacts. They fail closed unless used against an explicitly
approved target. They grant no authority to modify DNS, TLS, Caddy, a PDS,
accounts, keys, host state, or Constellation.
