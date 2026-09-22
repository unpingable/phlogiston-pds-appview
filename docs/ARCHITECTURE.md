# Architecture boundary

## Selected interpretation

Phlogiston is a **bounded read-only synthetic-fixture AppView**: an offline
renderer accepts one local, schema-validated snapshot and emits a static HTML
page plus a receipt. It is an operator/demo visualization, not an ATProto
network AppView.

This choice is necessary because no authoritative Phlogiston implementation,
indexer, relay/fetch contract, identity custody, retention commitment, or
production deployment record exists. Calling a static local fixture renderer a
network AppView would overstate what it reads and verifies.

## Data flow

```text
synthetic snapshot (did:example only)
  -> exact schema/identity validation
  -> deterministic local static renderer
  -> index.html + receipt.json
```

There is deliberately no inbound or outbound network edge, PDS call, OAuth,
AppView proxy, relay/firehose consumer, identity resolution, account action,
or mutable collection.

## Non-goals

- Full-network indexing or a persistent firehose.
- Hosting a PDS or using an existing PDS.
- Binding `phlogiston.app` or `phlogiston.social` to this artifact.
- Claiming any AG-to-Docket remote path, custody outcome, or Constellation
  completion beyond the released `alpha.6 reviewed-local-copy/v1` contract.
