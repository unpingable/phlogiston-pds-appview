from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("verify_release", ROOT / "deploy/verify-release.py")
assert SPEC and SPEC.loader
VERIFY_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY_RELEASE)
verify = VERIFY_RELEASE.verify
PREFLIGHT_SPEC = importlib.util.spec_from_file_location("production_preflight", ROOT / "deploy/production/preflight.py")
assert PREFLIGHT_SPEC and PREFLIGHT_SPEC.loader
PREFLIGHT = importlib.util.module_from_spec(PREFLIGHT_SPEC)
PREFLIGHT_SPEC.loader.exec_module(PREFLIGHT)
RENDER_SPEC = importlib.util.spec_from_file_location("render_caddy", ROOT / "deploy/production/render-caddy.py")
assert RENDER_SPEC and RENDER_SPEC.loader
RENDER = importlib.util.module_from_spec(RENDER_SPEC)
RENDER_SPEC.loader.exec_module(RENDER)


def test_web_unit_is_loopback_only_and_preserves_state_boundary() -> None:
    unit = (ROOT / "deploy/production/phlogiston-web.service").read_text()
    environment = (ROOT / "deploy/production/phlogiston-web.env.example").read_text()
    assert "ExecStart=/usr/bin/node dist/server.js" in unit
    assert "StateDirectory=phlogiston" in unit
    assert "ReadWritePaths=/var/lib/phlogiston" in unit
    assert "PORT=8092" in environment
    assert "PHLOGISTON_PUBLIC_URL=https://phlogiston.app" in environment
    assert "PHLOGISTON_COMMUNITY_DID=did:plc:..." in environment
    assert "Requires=phlogiston-communitywatch.service" not in unit
    observer = (ROOT / "deploy/production/phlogiston-communitywatch.service").read_text()
    observer_config = (ROOT / "deploy/production/communitywatch.toml.example").read_text()
    assert "communitywatch-web --config /etc/phlogiston/communitywatch.toml" in observer
    assert "User=phlogiston-observer" in observer
    assert 'bind = "127.0.0.1"' in observer_config
    assert "port = 8093" in observer_config


def test_caddy_packet_exposes_only_the_app_surface() -> None:
    fragment = (ROOT / "deploy/production/Caddyfile.fragment").read_text()
    assert "phlogiston.app" in fragment
    assert "127.0.0.1:8092" in fragment
    assert "phlogiston.social {" not in fragment
    assert "8093" not in fragment
    rendered = RENDER.render("example.net { respond ok }\n", fragment)
    assert rendered.count("phlogiston.app") == 1
    try:
        RENDER.render(rendered, fragment)
    except ValueError as error:
        assert "existing" in str(error)
    else:
        raise AssertionError("duplicate route was accepted")


def test_on_demand_tls_dispatch_preserves_pds_ownership() -> None:
    dispatch = (ROOT / "deploy/production/Caddyfile.on-demand-dispatch.fragment").read_text()
    assert "127.0.0.1:3000" in dispatch
    assert "127.0.0.1:3002" in dispatch
    assert dispatch.count("rewrite * /tls-check") == 2
    assert 'endsWith(".juche.social")' in dispatch
    assert 'endsWith(".phlogiston.social")' in dispatch
    assert "respond 403" in dispatch


def test_release_verifier_binds_inventory_and_sources(tmp_path: Path) -> None:
    payload = tmp_path / "release"
    payload.mkdir()
    (payload / "payload.txt").write_text("qualified\n")
    manifest = {
        "schema": "phlogiston.release-manifest.v1",
        "phlogiston_commit": "a" * 40,
        "community_commit": "b" * 40,
        "files": {
            "payload.txt": {
                "bytes": 10,
                "sha256": "f1734a68232317c6dc71cbf33eb5858bf56b703bc1aafd29b7ba4cf893da3f70",
            }
        },
    }
    (payload / "release-manifest.json").write_text(json.dumps(manifest))
    result = verify(payload, "a" * 40, "b" * 40)
    assert result["files_verified"] == 1

    (payload / "payload.txt").write_text("changed\n")
    try:
        verify(payload, "a" * 40, "b" * 40)
    except ValueError as error:
        assert "identity mismatch" in str(error)
    else:
        raise AssertionError("changed release payload was accepted")


def preflight_fixture(tmp_path: Path) -> tuple[Path, Path]:
    machine = tmp_path / "machine-id"
    machine.write_text("synthetic-machine\n")
    q2 = tmp_path / "q2.json"
    q2.write_text(json.dumps({"schema": "atproto.q2-closeout.v1", "uncontaminated": True, "ended_at": "2026-09-27T16:54:28Z"}))
    custody = tmp_path / "custody.json"
    custody.write_text(json.dumps({"schema": "phlogiston.secret-custody.v1", "approved": True}))
    backup = tmp_path / "backup-custody.json"
    backup.write_text(json.dumps({"schema": "phlogiston.backup-custody.v1", "status": "accepted", "destination": "phlogiston-production", "probed_at": "2026-09-27T16:54:28Z"}))
    one = tmp_path / "phlog.tar.gz"
    two = tmp_path / "observer.tar.gz"
    one.write_bytes(b"phlog")
    two.write_bytes(b"observer")
    config = {
        "schema": "phlogiston.inert-deployment.v1",
        "not_before": "2026-09-27T16:54:28Z",
        "deployment_authorized": True,
        "q2_closeout_receipt": str(q2),
        "expected_machine_id_sha256": hashlib.sha256(machine.read_bytes().strip()).hexdigest(),
        "phlogiston_artifact": str(one),
        "phlogiston_artifact_sha256": hashlib.sha256(one.read_bytes()).hexdigest(),
        "communitywatch_artifact": str(two),
        "communitywatch_artifact_sha256": hashlib.sha256(two.read_bytes()).hexdigest(),
        "secret_custody_receipt": str(custody),
        "backup_custody_receipt": str(backup),
        "expected_backup_destination": "phlogiston-production",
        "state_root": str(tmp_path / "state"),
        "observer_state_root": str(tmp_path / "observer-state"),
    }
    config_path = tmp_path / "deployment.json"
    config_path.write_text(json.dumps(config))
    return config_path, machine


def test_preflight_accepts_only_complete_post_gate_inputs(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    result = PREFLIGHT.validate(
        config,
        now=datetime(2026, 9, 27, 16, 54, 29, tzinfo=timezone.utc),
        machine_id_path=machine,
    )
    assert result["status"] == "accepted"
    assert result["artifacts_verified"] == 2


def test_preflight_refuses_each_dangerous_boundary(tmp_path: Path) -> None:
    config_path, machine = preflight_fixture(tmp_path)
    base = json.loads(config_path.read_text())
    cases = {
        "authority": {"deployment_authorized": False},
        "artifact": {"phlogiston_artifact_sha256": "0" * 64},
        "secret": {"secret_custody_receipt": str(tmp_path / "missing.json")},
        "host": {"expected_machine_id_sha256": "f" * 64},
        "backup": {"expected_backup_destination": "wrong-destination"},
        "existing": {"state_root": str(tmp_path)},
    }
    for name, change in cases.items():
        candidate = dict(base)
        candidate.update(change)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(candidate))
        try:
            PREFLIGHT.validate(
                path,
                now=datetime(2026, 9, 27, 16, 54, 29, tzinfo=timezone.utc),
                machine_id_path=machine,
            )
        except PREFLIGHT.Refusal:
            pass
        else:
            raise AssertionError(f"dangerous {name} input was accepted")


def test_preflight_refuses_before_q2_gate(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    try:
        PREFLIGHT.validate(
            config,
            now=datetime(2026, 9, 27, 16, 54, 27, tzinfo=timezone.utc),
            machine_id_path=machine,
        )
    except PREFLIGHT.Refusal as error:
        assert "boundary" in str(error)
    else:
        raise AssertionError("pre-gate deployment was accepted")


def test_deploy_and_rollback_scripts_are_guarded() -> None:
    deploy = (ROOT / "deploy/production/deploy-inert.sh").read_text()
    rollback = (ROOT / "deploy/production/rollback-inert.sh").read_text()
    for required in ("preflight.py", "verify-release.py", "caddy validate", "/community/", "inert-deployment-receipt"):
        assert required in deploy
    assert "backup_custody_receipt" in (ROOT / "deploy/production/preflight.py").read_text()
    assert "--confirm-inert-rollback" in rollback
    assert "caddy validate" in rollback
    assert "rm -rf /var/lib" not in rollback


def test_activation_templates_keep_pds_and_authority_separate() -> None:
    compose = (ROOT / "deploy/production/phlogiston-pds.compose.yaml").read_text()
    pds_env = (ROOT / "deploy/production/phlogiston-pds.env.example").read_text()
    authority = (ROOT / "deploy/production/phlogiston-communityd.service").read_text()
    authority_config = (ROOT / "deploy/production/communityd.toml.example").read_text()
    assert "ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a" in compose
    assert '"127.0.0.1:3002:3000"' in compose
    assert "PDS_HOSTNAME=phlogiston.social" in pds_env
    assert "SET_OWNER_ONLY_AT_ACTIVATION" in pds_env
    assert "communityd-serve --config" in authority
    assert 'credential_ref = "env:COMMUNITYD_CREDENTIAL_FILE"' in authority_config
    assert "operation_journal_path" in authority_config
    assert "authority_socket_path" in authority_config
    assert "/admin/" not in authority_config


def test_production_config_manifest_matches_bytes() -> None:
    manifest = json.loads((ROOT / "deploy/production/config-manifest.json").read_text())
    assert manifest["schema"] == "phlogiston.production-config-manifest.v1"
    for relative, expected in manifest["files"].items():
        actual = hashlib.sha256((ROOT / "deploy/production" / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
