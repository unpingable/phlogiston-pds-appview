# Phlogiston PDS operations

This kit operates the stock Bluesky PDS at `https://phlogiston.social`. Public registration stays closed. It does not modify Juche, migrate real users, or change other host services. Root's campaign checkpoint records exact host, source revision, digest, credential custody, retained artifacts and currently active producers. Read and reconcile it before operations; do not duplicate a producer after losing supervision.

The current reviewed remote kit is staged under `/opt/phlogiston-pds/20261011-bootstrap`; verify each executor hash against its lane/source receipt before use. Preserve an exact source receipt when staging a later version. Runtime paths are `/etc/phlogiston/pds.env`, `/etc/phlogiston/phlogiston-pds.compose.yaml`, `/var/lib/phlogiston-pds`, unit `phlogiston-pds.service`, container `phlogiston-pds`, private listener `127.0.0.1:3002`. Verify actual host/machine identity and capacity against root's checkpoint. Admit allocation before image pulls or recovery copies: both the shared host and this runtime host have a 60 GiB unallocated reserve; root owns aggregate accounting. Do not apply another host's capacity sample here.

## Recorded live state and custody

As recorded on 2026-10-11, the controlled service is publicly reachable at `https://phlogiston.social/xrpc/_health`, version `0.4.5037`, on the existing host `192.46.223.21`. Pinned amd64 upstream image: `ghcr.io/bluesky-social/pds@sha256:74c650cd620eee2e6e0272b4cb76036a0271523b1742f61f813b79dc5a8b5273`. The PDS unit is enabled at boot; Docker's `unless-stopped` policy supervises the container. Unit active state alone does not establish PDS HTTP health or useful observer progress. Reconcile actual host identity/source/unit/container rather than trusting these historical values blindly.

Operational recovery/evidence registry: `/data/git/atproto-nutrition/portfolio-private/campaigns/phlogiston-pds-20261011`. Begin with `CHECKPOINT.json`, `BOOTSTRAP-SOURCE.json`, `TEST-CREDENTIAL-CUSTODY.json` and the specific run/terminal receipts. Current account custody is remote `/etc/phlogiston/test-accounts/*.json`, with protected browser-test copies under `/tmp/phlogiston-pds-20261011-private/accounts`. The curator's normal app password is separately protected in `/etc/phlogiston/communityd-credential.json`; the application does not receive the PDS admin credential. Do not print/read private bytes into ordinary logs or evidence. Public account/record evidence is in the registry's `NORMAL-USER-RECORDS.json`, `LIVE-PDS-RECORD-READBACK.json`, and `LIVE-OBSERVER-EVIDENCE.json`; remote normal-user record evidence is `/var/lib/phlogiston-campaign/20261011/normal-user-records.json`.

Root recorded normal provisioning for three disposable accounts and a completed browser OAuth→submission→real-stream candidate→admission lifecycle. The immutable browser receipt is `browser-1f47f7ea-b747-41ff-8e2d-017bf1637edd/BROWSER-RECEIPT.json`; inspect it for exact scope before reusing a success claim. Additional duplicate/pause cases and Constellation operation qualification have their own terminal records, not this prose.

One small age-encrypted stopped backup was captured, the original restarted, and encrypted offhost custody retained. `BACKUP-CUSTODY.json` records remote `/var/backups/phlogiston`, offhost `/home/jbeck/.local/share/phlogiston-pds/backups`, and separately protected identities `/home/jbeck/.config/phlogiston-pds/backup.agekey` and `/etc/phlogiston/backup.agekey`. Follow the actual backup result/receipt SHA256; a destination path alone is not a verified archive. Independent restore and migration were not launched/qualified. Review credential custody at completion or 2026-10-12, and source/backup custody at 2026-10-18, under root's checkpoint.

## Current operating boundary

Constellation tools support the ATProto product. PDS-specific deployment, configuration, procedures and adapters remain ATProto-owned; they are not embedded into the generic tooling repositories. Any feedback to generic tooling requires a separate scope justified by actual production-viability evidence.

Constellation owns generic observation and governed operational custody. This repository supplies only PDS-specific bounded executors; it does not install a parallel health timer, automatic updater, management daemon, admission authority or generic execution framework. Root's current binding evidence and limits are recorded in [PDS-EXECUTION-20261011.md](../../docs/PDS-EXECUTION-20261011.md). Existing released AG admission, Docket execution custody and Phosphor visibility must be reused only through their actual current consumer contracts; a document naming a component is not proof that a remote operation is implemented or accepted.

The current campaign completion is controlled PDS hosting, automated disposable identity tests, functioning application integration and honest Constellation binding. Root has retained one small encrypted backup. Comprehensive restore/migration/disaster-recovery qualification is deferred; the reference commands below are source capabilities for a later explicitly scoped occurrence, not outstanding launch gates or completed provider qualifications. No standalone health units are supplied or installed. Use the existing Constellation observation consumer and root's exact operational checkpoint, preserving its permission boundary and source identities.

The installed Constellation capability under current qualification is BARv1 **Start** of this exact unit from inactive/failed state; it is not Restart, deployment, arbitrary commands or automatic maintenance. `CONSTELLATION-RUN.json` names the current durable root producer and its recovery procedure. Do not claim governed Start succeeded until root records its terminal result plus actual AG/Docket/evaluation receipts. Existing canary and unrelated consumers remain untouched; do not substitute a direct restart and describe it as governed execution.

## Private configuration and disposable accounts

Create root-only custody directories first. The CLI requires new paths and never prints secret values:

```sh
/opt/phlogiston-pds/20261011-bootstrap/deploy/production/pds-ops.sh configure \
  --output /etc/phlogiston/pds.env \
  --template /opt/phlogiston-pds/20261011-bootstrap/deploy/production/phlogiston-pds.env.example
```

Never regenerate or overwrite this environment after accounts exist. Preserve the PLC rotation key, JWT/DPOP values and admin password with the whole PDS state. The template requires invites; no invite code is published. Admin provisioning uses a private one-use invite followed by stock `createAccount`:

```sh
/opt/phlogiston-pds/20261011-bootstrap/deploy/production/pds-ops.sh provision \
  --env /etc/phlogiston/pds.env \
  --custody /var/lib/phlogiston-campaign/20261011/author-a-account.json \
  --handle author-a-20261011.phlogiston.social \
  --email author-a-20261011@phlogiston.social \
  --base-url http://127.0.0.1:3002
```

The same command supports `curator-20261011` and `author-b-20261011` with distinct private custody files. A completed checkpoint is reused; an uncertain account effect checks the same already-custodied password instead of repeating account creation. If reconciliation fails, retain the checkpoint and inspect account state through the authorized admin interface. Do not delete it and blindly start over. Passwords/tokens/invites belong only in protected runtime custody, never shell arguments, source, screenshots or ordinary receipts. Normal account APIs publish records; admin APIs are only provisioning/control, not record-writing credentials.

DNS and Caddy must resolve/serve the exact authorized hosted handles. The current campaign uses these explicit TLS hostnames:

```caddy
phlogiston.social, curator-20261011.phlogiston.social, author-a-20261011.phlogiston.social, author-b-20261011.phlogiston.social {
    reverse_proxy 127.0.0.1:3002
}
```

Root owns the DNS change and exact Caddy transaction: verify the previous config hash, change only the Phlogiston block, validate the complete candidate and reload. Preserve every unrelated block and the existing global on-demand policy. This static route does not require touching Juche or installing the old shared TLS dispatcher. New fixture handles require corresponding exact routing/DNS; provisioning itself does not invent or deploy routes. Do not open wildcard registration or grant unconditional certificate issuance.

## Add one additional disposable identity

1. Choose a new unique hosted handle such as `author-c-20261012.phlogiston.social`, a matching disposable email, and one new protected provisioning checkpoint under `/etc/phlogiston/test-accounts/`. Record its accountable owner, intended regression consumer, lifetime and retirement in the existing campaign checkpoint. Existing wildcard DNS can resolve the name, but **wildcard DNS is not wildcard TLS**.
2. Confirm DNS points that exact name to the admitted host. Capture the current Caddy config bytes/hash and compare against the prior route receipt. Add only this exact hostname to the existing Phlogiston static site block serving `127.0.0.1:3002`; retain all prior authorized hosts, every unrelated block and the global on-demand policy. Produce a reviewed complete candidate, run `caddy validate --config <candidate>`, install the exact candidate only if the original hash still agrees, and reload the existing Caddy service. This is a service-specific exact route transaction, not a wildcard enrollment or a new route manager. Record new config/hash and rollback copy in the route receipt.
3. Run the normal `provision` command shown above with the new handle/email and new custody path. It may use the root-local PDS address for private provisioning; the publicly advertised PDS remains exactly `https://phlogiston.social`. Do not regenerate `pds.env`. Inspect returned public DID/handle and retained credential file ownership/mode without displaying the password.
4. Verify ordinary TLS for the exact new hostname and `https://<newhandle>/.well-known/atproto-did` equals the returned DID. Independently resolve the PLC DID document and check its PDS service points to `https://phlogiston.social`. The handle is display/discovery input, never independent DID authority. Allow an initial normal TLS issuance delay; do not fall back to another provider or weaken TLS/issuer checks.
5. Use the fixture-post helper for one labeled post, then the existing normal OAuth/browser harness and application to self-submit its exact URI/CID. Capture actual record/stream/decision/view evidence under the established durable test runner. Never use the admin credential for record publication, browser sign-in or community authority. The next agent does not need to recruit a human for disposable-account consent.

Provisioning recovery is deliberately conservative. If a protected checkpoint is `attempted_unknown`, repeated invocation only checks the same password through normal `createSession`; absence/read failure cannot justify another `createAccount`. A `prepared` checkpoint also currently takes this readback path, even if the invite request failed before any account dispatch; the helper does not automatically restart that pre-account phase. Reconcile the exact protected checkpoint, source version and PDS account state through the existing authorized admin interface. Retain the original uncertain custody/evidence; do not silently delete/reset it to force redispatch. If exact source/state evidence establishes no account was attempted, root may retire that unused intent under explicit ownership and begin a separately recorded fresh provisioning case. Normal fresh provisioning has passed three actual account creations; this documented partial-state limit is not a speculative automation promise.

## Publish a fresh normal-account fixture post

The reusable executor avoids ad hoc scripts and admin record injection:

```sh
python3 /opt/phlogiston-pds/20261011-bootstrap/deploy/production/pds-fixture-post.py \
  --account /etc/phlogiston/test-accounts/author-a-20261011.json \
  --case p0-new-case-author-a-20261012 \
  --checkpoint /var/lib/phlogiston-campaign/20261011/p0-new-case-author-a-20261012.json
```

Use the actual custody filename from its provisioning receipt; the example is not permission to invent/recreate credentials. Stage the helper with its exact source hash and imported package first if the current kit copy lacks it. It uses only fixed public Phlogiston HTTPS and normal `createSession`/`repo.createRecord`, produces labeled disposable content and returns public URI/CID only. One case has one checkpoint path: deterministic DID+case rkey and durable exact record precede dispatch, same-case execution is flock-fenced, and retries read the exact address first. A matching record reconciles; an attempted unknown effect with absence/error/conflict refuses another write. Keep that checkpoint and reconcile; do not create a second checkpoint for the same case. Use a different case ID/path for an intentionally fresh post. No credentials/tokens belong in command arguments, stdout or public intent files.

## Deferred recovery reference: encrypted stopped backup and isolated restore

Ensure no browser/lifecycle producer is still writing, pause new community writes/admissions using their existing controls, and record a durable root execution checkpoint with the exact source/image, host, run identity, logs, artifacts, custody and recovery action. A prolonged capture must run under the approved durable execution mechanism. Private age identity custody is separately protected; the public recipient can be recorded in normal receipts.

```sh
/opt/phlogiston-pds/20261011-bootstrap/deploy/production/pds-ops.sh backup \
  --data /var/lib/phlogiston-pds --env /etc/phlogiston/pds.env \
  --compose /etc/phlogiston/phlogiston-pds.compose.yaml \
  --archive /var/lib/phlogiston-campaign/20261011/pds-backup.age \
  --recipient PUBLIC_AGE_RECIPIENT \
  --receipt /var/lib/phlogiston-campaign/20261011/pds-backup-receipt.json \
  --checkpoint /var/lib/phlogiston-campaign/20261011/pds-backup-checkpoint.json
```

All output paths must be new and outside the data directory. Capture stops the named unit, confirms its container is stopped, checkpoints SQLite, encrypts whole state/config directly, and leaves the original stopped. Root explicitly restarts that original unit after inspecting the producer/receipt, including failure handling. A lost supervisor must reconcile the existing checkpoint/archive, never create a replacement capture merely because the conversation ended. Partial ciphertext is not a qualified backup; retain it only for a named reconciliation dependency, then retire it under exact ownership checks.

Transfer ciphertext and its SHA256 receipt to independent custody, retaining the private age identity separately. On a disposable recovery filesystem, create a new empty 0700 target; decrypt only there:

```sh
/opt/phlogiston-pds/20261011-bootstrap/deploy/production/pds-ops.sh restore \
  --archive /protected/pds-backup.age --identity /protected/backup.agekey \
  --target /protected/restore-20261011 --expected CIPHERTEXT_SHA256 \
  --receipt /protected/restore-20261011-receipt.json
```

Success is `restored-not-started`; an incomplete marker means no runtime may start from that directory. Do not overwrite original state. Start only a disposable clone with **no external network** and no published ports, using the exact restore image and restored environment:

```sh
docker run --detach --name phlogiston-pds-restore-20261011 \
  --network none --restart no --memory 1g --cpus 1 --pids-limit 256 \
  --log-driver json-file --log-opt max-size=10m --log-opt max-file=2 \
  --env-file /protected/restore-20261011/config/pds.env \
  --mount type=bind,source=/protected/restore-20261011/data,target=/pds \
  ghcr.io/bluesky-social/pds@sha256:74c650cd620eee2e6e0272b4cb76036a0271523b1742f61f813b79dc5a8b5273
```

There is no privilege/host PID/host cgroup namespace or cgroup hierarchy mount. Root owns allocation/start/stop. Keep the original and restored writable state separate; this network-none clone cannot publish PLC or relay effects. Qualify account passwords and expected exact records through the clone's own loopback API:

```sh
/opt/phlogiston-pds/20261011-bootstrap/deploy/production/pds-ops.sh qualify-restore \
  --container phlogiston-pds-restore-20261011 \
  --target /protected/restore-20261011 \
  --restore-receipt /protected/restore-20261011-receipt.json \
  --expectations /protected/restore-expectations.json \
  --credential /protected/curator-account.json \
  --credential /protected/author-a-account.json \
  --credential /protected/author-b-account.json \
  --receipt /protected/restore-qualified.json
```

Expectations are `{"accounts":[{"did":"did:plc:…","handle":"…phlogiston.social","records":[{"uri":"at://did:plc:…/collection/rkey","cid":"…"}]}]}`; optional record `value` requests exact canonical JSON checking. Each credential is the corresponding completed private provisioning checkpoint. The verifier checks isolation/image/mount/config, feeds credentials through stdin to `docker exec` using immutable container ID, and checks stock `createSession` and authenticated `getRecord`; receipts exclude passwords and tokens. Actual clone state changes only through local account sign-in. This proves bounded isolated auth/record continuity, **not** OAuth grant survival, DID/relay recovery, migration, or permission to start a second public writer. Stop/remove the exact clone and retire its reproducible writable copy when root seals evidence and no replay consumer remains; preserve encrypted backup/receipt/private identity under separately recorded custody.

## Deferred update/recovery reference: pinned update and conservative rollback

1. Record the current Compose bytes/hash, configured digest, running image ID and health version. Read upstream release notes and pin a reviewed immutable digest for the correct architecture; never use floating `latest` or an automatic updater. Admit storage for both retained old and new images.
2. Pause consumers/writers and take a stopped encrypted whole-state/config backup. Verify independent custody and the private decryption-key dependency. Keep the old exact image/source and snapshot until the update is accepted.
3. Change only the pinned image in a reviewed candidate Compose, preserving data bind/env. Validate `docker compose --file <candidate> config --quiet`, then install the exact candidate and explicitly start the PDS. Inspect unit/container/HTTPS health, account/record continuity and actual lifecycle. Reconcile in-flight browser/authority operations before resuming consumers.
4. On failure, stop the new writer and inspect whether it changed data/schema or emitted public effects. **There is no automatic downgrade claim.** Reusing the old image against changed data requires upstream compatibility evidence and qualification. Otherwise restore the pre-update state into a separate fenced destination and qualify it before any controlled cutover. Never restore a stale snapshot over a live writer or assume it can rewind PLC/relay state or published effects.

Rollback may require retaining the new image for recovery, not simply changing a tag back. Root decides cutover/fencing, checks relay/identity continuity and independently accepts the result; the component being replaced does not accept its own replacement. Public migration of disposable identities to a separately hosted Phlogiston origin is authorized in this campaign but remains a distinct qualification: source service auth, target deactivated account, repo/blobs/private-state transfer, authorized PLC/identity update, target activation and source deactivation must all be checked. Restore alone supplies none of that evidence. [Official migration guide](https://atproto.com/guides/account-migration).

## Constellation consumer boundary

Constellation provides generic operational tools for this ATProto-owned service. PDS-specific configuration, deployment, qualification and operating procedures stay here. This campaign makes no changes to Constellation components. A later generic improvement requires an actual new operational lesson and a separately justified requirement.

The dedicated NQ observer and attention/remediation timers are enabled. The initial governed Start was independently accepted after Docket settlement and a fresh active-unit observation 15.382 seconds later; HTTPS health was checked separately. The authority is limited to ten uses and expires on 2026-10-18 at 22:26 UTC. Renew only with a fresh grant journal and pinned grant under the documented owner procedure. This is Start of the inactive/failed unit, not active restart or deployment. Before planned maintenance that keeps the PDS stopped beyond the three-minute detector threshold, suspend the dedicated remediation timer, record the maintenance occurrence, and restore it after service recovery. Preserve actual observation history.
