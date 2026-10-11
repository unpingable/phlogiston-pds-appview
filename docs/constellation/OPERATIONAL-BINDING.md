# Phlogiston Constellation operational binding

Phlogiston uses the host's released BoundedAutonomousRemediationv1 path for one exact operation: systemd **Start** of inactive/failed `phlogiston-pds.service`. Existing canary enrollment remains separate. The deterministic consumer uses no model API and has only local observation/report routes; outbound notifications are disabled.

## Live enrollment

Configuration and owner-controlled authority custody live under `/etc/constellation-phlogiston`; campaign, consumer, Docket, executor and grant-use state live under `/var/lib/constellation-phlogiston`. Exact released executable copies under `/usr/libexec/constellation-phlogiston` retain separate adjacent deployment/grant-enrollment files. These bind the Phlogiston campaign/profile and grant bytes without replacing the existing canary bindings.

- NQ watcher: `svc-phlogiston-pds`, profile `nq.systemd_unit` v2, exact host/unit scope.
- Watcher admission: `9d005513-d749-4d40-be4d-e366ccf7e1cc`.
- AG runtime profile digest: `3d696134530743b965a0002a48b1e650e5a86485ef9f33c6d6ae6732cd6926d3`.
- Grant: at most10 uses, valid7days; expiration/exhaustion requires explicit owner re-enrollment with a fresh journal/pin. No automatic renewal or rate-limit claim.
- Dedicated NQ daemon and local attention/remediation units/timers are source-owned in `deploy/constellation/`. Runtime parent mode0751 and helper directory0711 are recreated by unit/tmpfiles bindings. The daemon does not initialize its database.

Released host packages inspected: `constellation-remediation`0.1.0+bar.20261003.3; `agent-governor-ng-operator-tools`, `agent-governor-ng-systemd-executor`, and `constellation-docket`0.1.0+bar.20261003.1; `nq-ng`0.2.4. Generic component source was not changed.

## Qualification and recovery handoff

The real stop → governed Start occurrence `constellation-start-002` completed on 2026-10-11 at 22:38:47 UTC. Docket settled success at 22:38:30.855; the independent active-unit postcondition followed 15.382 seconds later. HTTPS returned 200 and PDS version 0.4.5037, with no fallback start. The separate acceptance record is `constellation-evidence/constellation-start-002/ACCEPTANCE.json` in the Phlogiston campaign custody, SHA256 `30847fdbaaeae01b4ab68bc7547817b8a4d7f7dd6ee92d4aad05d783ad02533a`. The run checkpoint is `CONSTELLATION-RUN-002.json` (unit `phlogiston-constellation-qualification-20261011-002`, invocation `b7df7c6fb0e7402790d4b5f2a472d79f`).

The first occurrence exposed a local-file delivery ownership mismatch and restored the PDS without AG dispatch. The corrected evaluator runs as nq. Its original failure receipt remains separate from the accepted successor. NQ and the attention/remediation timers are now enabled; a subsequent pass abstained on the recovered service rather than issuing another Start. The released evaluator separately requires a continuous-clear interval. This proves the recorded bounded Start, not sustained application health.

Read-only operator commands against the enrolled coordinates:

```sh
ag-loopctl verify-runtime-profile --runtime-profile /etc/constellation-phlogiston/runtime-profile.json
ag-loopctl inspect --database /var/lib/constellation-phlogiston/ag/campaign.sqlite
constellation-attention state --config /etc/constellation-phlogiston/attention.toml
```

Docket exact issuance inspection uses `docket governed-loop inspect --state /var/lib/constellation-phlogiston/docket --issuance ID`. AG `recover` reconciles an occurrence's program counter and custody; it is not a service restart. Preserve unresolved spent authority and follow the released operator reconciliation law.

## Limits and custody

Start-only: this binding does not restart active units, deploy software, restore backups, or alter other PDS instances. The PDS unit's detached-container/RemainAfterExit behavior means systemd active state does not prove container or HTTPS health. Existing PDS HTTPS200 evidence is separate. Monitor project-concern acquisition and a dedicated Phosphor campaign projection are not enrolled by this binding; their availability is not represented as current Phlogiston operational support.

The released same-root premise remains explicit: the reviewed consumer can write AG/Docket/grant-use/evidence custody and reads the issuer key. Profiles and bounded grants do not create isolation from root. Torn grant journal entries fail closed and require explicit owner reconciliation. Root owns protected issuer custody, grant expiry review, operational state, and retirement after recovery dependencies end. Minimal source/evidence is retained through campaign acceptance and reviewed at campaign close or2026-10-18.

Formalization consideration: exact executable/config/subject/scope/profile identities separate Phlogiston from existing canary authority; live state-transition claims require the actual qualification receipts. Source-local deterministic config checks and existing released law suffice for this deployment binding; no new generic state machine was introduced. Physical host reboot and active-unit restart behavior remain unqualified. Root owns acceptance.

Attention permission binding: `/var/lib/constellation-phlogiston/attention` and its state/report files are nq-owned (directory0750; files0600 under UMask0077); local inbox is nq:nq0711 as required by NQ's local-file notification validation. Dedicated NQ SQLite and sidecar files must remain nq-owned. Root consumer remains root and reads the report through ordinary filesystem access; source `pass.rs` reads configured report bytes with fs::read and enforces semantic identity/freshness/window, not root-owner metadata. No separate report ownership grant or writable authority custody is conferred to nq. Parent `/var/lib/constellation-phlogiston` remains root-owned0755 for traversal; issuer/private,consumer,AG,Docket,effect andgrantjournal remain root-only.

ATProto ownership boundary: Constellation tools support this ATProto service. Phlogiston-specific deployment, operational binding and observer recovery work remains in ATProto-owned source/custody. No ATProto-specific changes are introduced into Constellation component repositories. A later generic lesson requires separate justification from actual production viability and its own component acceptance.
