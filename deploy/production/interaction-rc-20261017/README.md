# One proposed interaction release candidate

**Deployment status:** this exact candidate shipped on October 17 after one
owner-authorized permission correction. Run this unchanged public-source producer
with explicit `UMask=0022` so its release directories are `0755`; retain private
staging `0700` and protected receipt files `0600`. `UMask=0077` caused the first
attempt's CHDIR failure and verified rollback. See the
[release and rollback handoff](../../../docs/INTERACTION-RELEASE-20261017.md).
The original preparation record below is retained for provenance.

**Prepared only. Do not execute without owner release authorization.**

Runtime source: private `bf10f79f49643999146b80a6c4e3f732b975a99e`.
Public source: `860fcae4b9a97ee47982c487e7d9bc6659fefe39`.
Archive: `web-source.tar.gz`, SHA-256
`cb68d85ea7ee8ff7d31b74c6e215834609dcda860061d04db08d80e5a46a475e`.
The 225,719-byte archive contains 75 regular source/asset files, served by the
existing Node/tsx dependency closure. No compiled output or dependency upgrade.

Reproduce using Python 3.12.3, zlib 1.3, and the public repository containing the
exact candidate commit:

```sh
python3 package.py /path/to/phlogiston /tmp/interaction-rc.tar.gz
sha256sum /tmp/interaction-rc.tar.gz
cmp web-source.tar.gz /tmp/interaction-rc.tar.gz
```

`ARTIFACT.json` enumerates every file hash. `MANIFEST.json` additionally pins the
live baseline, toolchain/dependency receipt, producer hash, source revisions,
maximum advertised OAuth scope and an admitted upper allocation estimate of
16 MiB. Recheck actual shared-host admission immediately before installation.
On October 17 the host had only about 2.8 GiB above the required 60 GiB reserve;
no image pull or dependency copy is part of this release.

`producer.py` reuses the accepted L0p1 bounded web-only producer, changing only
obsolete help-page assertions. Historical origin run is recorded separately;
this proposed run is `aeb11507-5085-4fbe-9aaf-872aa05fccbe`. It has not run.

After owner authorization:

1. Merge the reviewed implementation, public-source and product handoff PRs with
   their exact identities preserved. If revisions change, reconcile the artifact
   manifest and review rather than deploying unidentified bytes.
2. Read current working directory/drop-in/dependency/toolchain hashes, capacity,
   and original producer status. Refuse if the pinned live baseline changed.
   Save a recovery checkpoint naming host, exact source/producer/archive hashes,
   unit/run identity, logs, terminal records and next authorized action.
3. Stage this exact packet into a fresh existing campaign leaf. Verify its hashes.
   Use the established durable root systemd oneshot mechanism with bounded memory,
   runtime and logs; do not depend on an interactive SSH process. The producer
   saves the previous drop-in before switching only `community-live`.
4. Serving the new metadata expands the advertised maximum scope; this is part
   of the owner-authorized change, not an already completed registration step.
   Reader sign-in stays at its original grant. No production credential change.
5. Verify canonical health, About revision, assets, precise metadata, signed-out
   Cabinet/terms/privacy and reader behavior. With a newly approved disposable
   identity, smoke consent, write, readback, undo and Disable. Never use an owner's
   personal account for writes. Record actual result and owner acceptance at #32.

The producer checks current baseline `26b0c5fcb38978707e6ffc763b584dd003aa829b`,
managed drop-in SHA-256 `ba664ebdb0f72c8b2f7d93116e86c84e69b72f4504688cb47bbb449e8310bc10`,
existing Node 24.13.0 and the existing `25a2816` dependency receipt. Its existing
failure handling restores saved previous bytes only if the managed drop-in is
still this producer's output. Interruption requires reconciling the original
producer/PHASE/TERMINAL and live service; do not launch a duplicate occurrence.

Rollback: restore the newly saved exact baseline `26b0c5f` drop-in, daemon-reload,
restart only `community-live`, and verify canonical source/assets. Preserve private
state and interaction journals for recovery. Disable/revoke interaction account
sessions when withdrawing write authority; code/metadata rollback alone is not
provider revocation and does not undo public records. Authority, observer and PDS
are not restarted or changed. Older retired CC3 rollback paths are invalid.

Owner decisions remain explicit: #37's one-reconsideration rule and decline
categories; #38's Cabinet-lifetime moderation/submission retention; release and
actual deployment acceptance; and the owner's #35 announcement. Existing 18+,
no paid legal review, controlled PDS/topology and no public hosted registration
remain unchanged. PDS #10/#40 is independently active.

Custody owner: root release engineering. Retain this packet for owner review and
exact replay/rollback preparation. Review at owner release disposition; retire
reproducible copies when those dependencies end. No producer execution, new SSH
identity, shared-agent mutation or production secret is included in this packet.
