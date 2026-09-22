# Horizon 0 recovery qualification contract

## Scope

This repository contains a deterministic, local qualification harness for a
synthetic PDS and the bounded Phlogiston renderer. It is not a production
backup, deployment, or activation procedure.

The harness uses a pinned upstream PDS image in an isolated local Docker
project with no published ports. It creates synthetic state, verifies a
stopped-layout capture, restores into a separate blank local directory, and
checks repository, blob, and application-state correspondence. It uses only
synthetic identities and explicitly marked test values.

## Qualification boundary

The implementation refuses incomplete PDS layouts, SQLite WAL/SHM sidecars,
unexpected archive members, stale archives, incorrect key attestations,
version/configuration mismatches, duplicate delivery, and non-empty restore
targets. An interrupted restore retains its incomplete marker and is not
implicitly resumed.

The harness emits a local receipt when an operator runs it. Receipts,
manifests, observed timings, capacity measurements, runtime identifiers, and
other occurrence evidence are deliberately not committed to this repository.
They are not a claim of production readiness, recovery-time objective, or
authorization to operate a PDS.

## Running local unit qualification

```text
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Running `qualification/run-h0-isolated.sh` requires an independently admitted
local Docker environment and writes only its explicitly supplied local receipt.
It performs no production, DNS, TLS, Caddy, account, or activation action.
