# Retained backup hardening contract

Current scope (2026-10-03): Phlogiston has zero users, no irreplaceable user
repository state and no current PDS continuity promise. The inert launch
requirement is reconstruction after host loss from retained exact source,
configuration, approved credential custody or reenrollment records, and small
operational state. Total-site-loss recovery is outside this qualified envelope.
Off-host backup custody, fresh backup probes and restore rehearsals are useful
hardening, not current launch prerequisites. Revisit user-data/PDS DR when
actually hosting user state or promising durability. Juche's technical patterns
do not import its operational posture, user commitments or policy.

The earlier procedure below is retained as historical hardening/rehearsal
material. Its former pre-deployment backup gate is superseded; current
`deploy/production/preflight.py` does not consume an off-host custody receipt.
No new backup platform, geographic custody step or DR claim is introduced.


Note (2026-09-25): for Phase 2 the community services' state and credentials
live under the atproto-community PCV0 kit's paths (`/var/lib/communityd`,
`/var/lib/community-web`, `/var/lib/communitywatch`, `/etc/atproto-community`),
not the `/var/lib/phlogiston-communityd` / `/var/lib/phlogiston-communitywatch`
paths assumed below, and the community repository is on a Bluesky-hosted PDS,
not `phlogiston.social`. Backups for those paths are planned in the PCV0 kit,
not here; this contract continues to govern `/var/lib/phlogiston`. See
[PHASE-2-TRIAL.md](PHASE-2-TRIAL.md) "Deployment topology".

The production host has no `/tank/nfs` mount. Durable custody is owned by the
existing off-host backup operator, which reaches the established NFS export
through its reviewed Docker volume. The application must never fall back to a
same-named local directory.

## Historical pre-deployment custody gate (superseded)

Immediately before deployment, the off-host operator verifies the exact Docker
volume type/device/options and runs `deploy/production/backup-probe.sh` inside
that mounted namespace against the dedicated `phlogiston-production`
directory. The create, fsync, rename, reread/checksum and removal probe emits a
`phlogiston.backup-custody.v1` receipt. The former deployment preflight accepted only a
matching receipt no more than one hour old; this requirement no longer applies
to the current zero-user inert deployment. Mount identity remains in the
private operator configuration rather than this public repository.

No automatic expiration is configured. Backup generations remain retained
until a separate reviewed deletion decision; the first retention review is 30
days after activation. This is deliberately conservative while the cohort and
growth rate are unknown.

## Application-consistent capture

The qualified capture contract is `docs/INTEGRATED-RECOVERY.md` and
`phlogiston_appview.integrated_recovery`:

1. stop every PDS and communityd writer and record exact source/image IDs;
2. require non-busy truncate checkpoints and no SQLite sidecars;
3. attest the exact stopped state paths and zero writer PIDs;
4. capture both PDS trees, communityd journal, and public configuration;
5. exclude reconstructible communitywatch state and re-enrollable OAuth/web
   sessions;
6. verify the manifest and archive before finalizing the NFS object;
7. restore to a canonical empty destination, rebuild the projection from
   authority, and preserve removal/idempotence behavior.

The first post-activation backup is a hard acceptance gate. The source will be
small enough to stage a stopped-state archive on the production filesystem,
stream it to the off-host operator, verify its final NFS identity, and remove
only the verified transient source archive. A mature streaming capture is a
later scalability improvement, not a reason to weaken the first backup.

Partial, corrupt, stale, duplicate, non-empty-destination, version-mismatched,
wrong-key and interrupted restore cases already refuse in isolated
qualification. Same-version blank-host restore is qualified; production RPO,
production RTO, live-copy backup, cross-version migration, external PLC
recovery and real-user portability are not.
