# Integrated community recovery

Status: qualified against two isolated stock PDS instances; not a production
backup or cross-version migration claim.

## State model

| Class | State | Recovery treatment |
|---|---|---|
| Authoritative | both PDS state trees, including repositories, keys and blobs | stopped-state capture, exact restore |
| Custody | `communityd` idempotency/operation journal | explicit non-busy checkpoint, exact restore |
| Configuration | public topology and source/image identities | manifest-bound exact restore |
| Reconstructible | communitywatch observer/projection database | excluded; rebuilt from repository records |
| Re-enrollable secret state | OAuth client state and Phlogiston web sessions | excluded; new enrollment required |

The operator must stop every PDS/communityd writer before attestation. The
communityd journal is checkpointed with `PRAGMA wal_checkpoint(TRUNCATE)` and
capture refuses busy/incomplete checkpoints, SQLite sidecars, symlinks,
partial PDS trees, unsupported manifests, mismatched checksums, or an
unbound source identity.

Restore accepts only a canonical empty destination. It creates a durable
incomplete marker before writing any member and removes that marker only after
every restored byte matches the manifest. A failed/duplicate restore cannot be
reconciled or mistaken for authoritative state.

The qualification restarts both restored PDSes using the pinned image, proves
the exact membership/admission/removal references survive, rebuilds a new
observer from repository proof, repeats delivery to exercise idempotence, and
confirms removed content stays absent. It then makes one PDS unavailable and
requires a dependency-unavailable result with no widened authority or false
projection-completion claim.

This does not qualify live-copy backup, production key custody, a production
RPO/RTO, cross-version migration, OAuth-session restoration, or external PLC
reconstruction.
