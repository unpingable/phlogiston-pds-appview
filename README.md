# Phlogiston

[Phlogiston](https://phlogiston.app/) is an ATProto social client for constructing and inhabiting one's social environment. The live participant application is implemented in atproto-community's `apps/community-live`. Reading, private feed curation and community submissions are live; native reply/like composition and a read-only Observe grant remain future work. Feeds, attention/context and the governed Cabinet belong to one client without merging their authority. This repository owns product direction and deployment composition, rather than a second participant runtime.

Use existing supported Bluesky or Phlogiston-hosted accounts without identity migration. The controlled `phlogiston.social` PDS is separately live, with public registration closed. My Labels consumes read-only Labelwatch observations; it does not publish labels, decide community membership or report complete current label state. PDS-specific deployment/custody remains ATProto-owned; no generic Constellation change follows from the participant shell.

Current direction and boundaries are in [PRODUCT-ARCHITECTURE.md](docs/PRODUCT-ARCHITECTURE.md) and [PUBLIC-SURFACES.md](docs/PUBLIC-SURFACES.md). Exact deployed source, receipts and rollback are in the [operational handoff](docs/P0-IMPLEMENTATION-HANDOFF.md). Earlier invite-only, operator-only and plugin-first sequencing is historical, not a current implementation gate.

## Retained local qualification and historical packages

The remaining renderer/earlier campaign sections describe their original bounded source surfaces, not the current live app or PDS status.

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

## Historical community integration candidate

The `campaign/community-integration-20260922` line adds a bounded application,
OAuth enrollment, and operator surface over the existing `atproto-community`
authority and projection interfaces. See [the integration map](docs/COMMUNITY-INTEGRATION.md),
[OAuth/session contract](docs/OAUTH-SESSION-ENROLLMENT.md), [operator contract](docs/OPERATOR-SURFACE.md),
and [integrated recovery contract](docs/INTEGRATED-RECOVERY.md). It is not
activated or deployed.

Current product direction lives in [docs/PRODUCT-ARCHITECTURE.md](docs/PRODUCT-ARCHITECTURE.md). The earlier [trial](docs/PHASE-2-TRIAL.md) and [participant packet](docs/PHASE-2-PARTICIPANT-PACKET.md) retain historical scope; they are not prerequisites for current owner-authorized work.

## Authority boundary

`deploy/`, `backup/`, `restore/`, `rollback/`, and `uninstall/` are operator
preparation artifacts. They fail closed unless used against an explicitly
approved target. They grant no authority to modify DNS, TLS, Caddy, a PDS,
accounts, keys, host state, or Constellation.
