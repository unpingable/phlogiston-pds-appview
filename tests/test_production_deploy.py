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
    assert unit.splitlines()[0].startswith("# Withdrawn from public routing for Phase 2:")
    assert "ExecStart=/usr/bin/node dist/server.js" in unit
    assert "StateDirectory=phlogiston" in unit
    assert "ReadWritePaths=/var/lib/phlogiston" in unit
    assert "PORT=8092" in environment
    assert "PHLOGISTON_PUBLIC_URL=https://phlogiston.app" in environment
    assert "PHLOGISTON_COMMUNITY_DID=did:plc:..." in environment
    assert "PHLOGISTON_PROJECTION_ORIGIN=http://127.0.0.1:8080" in environment
    assert "8093" not in environment
    assert "Requires=phlogiston-communitywatch.service" not in unit
    observer = (ROOT / "deploy/production/phlogiston-communitywatch.service").read_text()
    observer_config = (ROOT / "deploy/production/communitywatch.toml.example").read_text()
    assert "communitywatch-web --config /etc/phlogiston/communitywatch.toml" in observer
    assert "User=phlogiston-observer" in observer
    assert 'bind = "127.0.0.1"' in observer_config
    assert "port = 8093" in observer_config


WITHDRAWN_HEADER = "# Withdrawn for Phase 2: the PCV0 kit owns this service (see docs/PHASE-2-TRIAL.md). Never enable beside PCV0 communityd.service."


def test_community_runtime_templates_are_withdrawn_for_phase_2() -> None:
    for name in (
        "phlogiston-communityd.service",
        "phlogiston-communitywatch.service",
        "communityd.toml.example",
        "communitywatch.toml.example",
    ):
        text = (ROOT / "deploy/production" / name).read_text()
        assert text.splitlines()[0] == WITHDRAWN_HEADER, name
    deploy = (ROOT / "deploy/production/deploy-inert.sh").read_text()
    assert "--with-community-runtime" in deploy
    assert 'with_community_runtime=0' in deploy
    head, _, gated = deploy.partition('if [ "$with_community_runtime" -eq 1 ]; then\n  # Not used for Phase 2')
    assert gated, "community runtime install is not gated"
    for community_only in ("phlogiston-communitywatch.service", "communitywatch.toml", "verify-communitywatch-release.py", "phlogiston-observer"):
        assert community_only not in head, community_only
        assert community_only in gated, community_only
    assert "phlogiston-communityd.service" not in deploy


def test_caddy_fragment_is_withdrawn_for_phase_2() -> None:
    fragment = (ROOT / "deploy/production/Caddyfile.fragment").read_text()
    active = [line for line in fragment.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    assert active == [], active
    assert "phlogiston.app" in fragment  # the comment explains who owns the site
    assert "phlogiston.social {" not in fragment
    assert "8093" not in fragment
    assert PREFLIGHT.check_caddy_fragment_withdrawn(ROOT / "deploy/production/Caddyfile.fragment") == {"caddy_fragment_site_lines": 0}
    pcv0_site = "phlogiston.app {\n\treverse_proxy 127.0.0.1:3210\n}\n"
    try:
        RENDER.render(pcv0_site, fragment)
    except ValueError as error:
        assert "existing" in str(error)
    else:
        raise AssertionError("rendered over the PCV0-owned phlogiston.app site")
    rendered = RENDER.render("example.net { respond ok }\n", fragment)
    try:
        RENDER.render(rendered, fragment)
    except ValueError as error:
        assert "existing" in str(error)
    else:
        raise AssertionError("duplicate marker was accepted")


def test_preflight_refuses_phlogiston_app_site_in_kit_fragment(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    colliding = tmp_path / "Caddyfile.fragment"
    colliding.write_text("# comment mentioning phlogiston.app is fine\nphlogiston.app {\n\treverse_proxy 127.0.0.1:8092\n}\n")
    try:
        PREFLIGHT.validate(
            config,
            now=datetime(2026, 9, 27, 16, 54, 29, tzinfo=timezone.utc),
            machine_id_path=machine,
            systemd_root=systemd_fixture(tmp_path),
            systemctl=None,
            caddy_fragment=colliding,
        )
    except PREFLIGHT.Refusal as error:
        assert "phlogiston.app" in str(error) and "PCV0" in str(error)
    else:
        raise AssertionError("phlogiston.app site block in the kit fragment was accepted")
    distinct = tmp_path / "distinct.fragment"
    distinct.write_text("# phlogiston.app belongs to PCV0\nstatus.example.net {\n\treverse_proxy 127.0.0.1:8092\n}\n")
    assert PREFLIGHT.check_caddy_fragment_withdrawn(distinct) == {"caddy_fragment_site_lines": 3}
    try:
        PREFLIGHT.check_caddy_fragment_withdrawn(tmp_path / "absent.fragment")
    except PREFLIGHT.Refusal as error:
        assert "not readable" in str(error)
    else:
        raise AssertionError("absent fragment was accepted")


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
        "state_root": str(tmp_path / "state"),
        "observer_state_root": str(tmp_path / "observer-state"),
    }
    config_path = tmp_path / "deployment.json"
    config_path.write_text(json.dumps(config))
    return config_path, machine


PCV0_COMMUNITYD_UNIT = "[Service]\nUser=communityd\nExecStart=/opt/atproto-community/.venv/bin/communityd-serve --config /etc/atproto-community/communityd.toml\n"


def systemd_fixture(tmp_path: Path, *, pcv0: bool = True) -> Path:
    root = tmp_path / "systemd-root"
    etc = root / "etc/systemd/system"
    lib = root / "lib/systemd/system"
    etc.mkdir(parents=True)
    lib.mkdir(parents=True)
    (lib / "ssh.service").write_text("[Service]\nExecStart=/usr/sbin/sshd -D\n")
    if pcv0:
        (etc / "communityd.service").write_text(PCV0_COMMUNITYD_UNIT)
    return root


def validate_at_gate(config: Path, machine: Path, systemd_root: Path, systemctl=None) -> dict:
    return PREFLIGHT.validate(
        config,
        now=datetime(2026, 9, 27, 16, 54, 29, tzinfo=timezone.utc),
        machine_id_path=machine,
        systemd_root=systemd_root,
        systemctl=systemctl,
    )


def test_preflight_accepts_only_complete_post_gate_inputs(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    result = validate_at_gate(config, machine, systemd_fixture(tmp_path))
    assert result["status"] == "accepted"
    assert result["artifacts_verified"] == 2
    assert result["community_writer_units"] == ["communityd.service"]
    assert result["recovery_scope"] == "zero-user-host-loss-reconstruction"
    assert result["total_site_loss_recovery_claimed"] is False
    assert not (tmp_path / "backup-custody.json").exists()
    assert "backup_custody_receipt" not in json.loads(config.read_text())


def test_preflight_accepts_without_pcv0_writer_and_with_masked_withdrawn_unit(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    root = systemd_fixture(tmp_path, pcv0=False)
    withdrawn = ROOT / "deploy/production/phlogiston-communityd.service"
    (root / "lib/systemd/system/phlogiston-communityd.service").write_text(withdrawn.read_text())
    (root / "etc/systemd/system/phlogiston-communityd.service").symlink_to("/dev/null")
    result = validate_at_gate(config, machine, root)
    assert result["community_writer_units"] == []


def test_preflight_refuses_second_communityd_writer(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    root = systemd_fixture(tmp_path)
    (root / "lib/systemd/system/other-communityd.service").write_text(
        "[Service]\nExecStart=/opt/other/venv/bin/communityd-serve --config /etc/other/communityd.toml\n"
    )
    try:
        validate_at_gate(config, machine, root)
    except PREFLIGHT.Refusal as error:
        assert "other-communityd.service" in str(error)
    else:
        raise AssertionError("second communityd writer was accepted")


def test_preflight_refuses_module_launched_communityd_writer(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    root = systemd_fixture(tmp_path)
    (root / "lib/systemd/system/other-communityd.service").write_text(
        "[Service]\nExecStart=/opt/other/venv/bin/python -m communityd.serve_cli --config /etc/other/communityd.toml\n"
    )
    try:
        validate_at_gate(config, machine, root)
    except PREFLIGHT.Refusal as error:
        assert "other-communityd.service" in str(error)
    else:
        raise AssertionError("module-launched communityd writer was accepted")


def test_preflight_refuses_unmasked_withdrawn_phlogiston_communityd(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    root = systemd_fixture(tmp_path)
    withdrawn = ROOT / "deploy/production/phlogiston-communityd.service"
    (root / "etc/systemd/system/phlogiston-communityd.service").write_text(withdrawn.read_text())
    try:
        validate_at_gate(config, machine, root)
    except PREFLIGHT.Refusal as error:
        assert "phlogiston-communityd.service" in str(error)
        assert "mask" in str(error)
    else:
        raise AssertionError("unmasked withdrawn communityd unit was accepted")


def test_preflight_guard_uses_systemctl_listing_and_masked_state(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    root = systemd_fixture(tmp_path)
    calls: list[list[str]] = []

    def systemctl(args: list[str]) -> str:
        calls.append(args)
        if args[0] == "list-unit-files":
            return "communityd.service enabled enabled\ngenerated-communityd.service static -\nphlogiston-communityd.service masked enabled\n"
        if args[0] == "cat" and args[-1] == "generated-communityd.service":
            return "# /run/systemd/generator/generated-communityd.service\n[Service]\nExecStart=/srv/x/communityd-serve\n"
        raise AssertionError(f"unexpected systemctl call {args}")

    try:
        validate_at_gate(config, machine, root, systemctl)
    except PREFLIGHT.Refusal as error:
        assert "generated-communityd.service" in str(error)
    else:
        raise AssertionError("communityd writer known only to systemctl was accepted")
    assert calls[0][0] == "list-unit-files"

    def only_masked(args: list[str]) -> str:
        if args[0] == "list-unit-files":
            return "communityd.service enabled enabled\nphlogiston-communityd.service masked enabled\n"
        raise AssertionError(f"unexpected systemctl call {args}")

    (root / "etc/systemd/system/phlogiston-communityd.service").write_text(
        (ROOT / "deploy/production/phlogiston-communityd.service").read_text()
    )
    result = validate_at_gate(config, machine, root, only_masked)
    assert result["community_writer_units"] == ["communityd.service"]


def test_preflight_guard_fails_closed_when_systemd_is_not_queryable(tmp_path: Path) -> None:
    config, machine = preflight_fixture(tmp_path)
    try:
        validate_at_gate(config, machine, tmp_path / "no-systemd-here")
    except PREFLIGHT.Refusal as error:
        assert "not queryable" in str(error)
    else:
        raise AssertionError("absent systemd was accepted")

    def broken(args: list[str]) -> str:
        raise OSError("systemctl unavailable")

    try:
        validate_at_gate(config, machine, systemd_fixture(tmp_path), broken)
    except PREFLIGHT.Refusal as error:
        assert "not queryable" in str(error)
    else:
        raise AssertionError("failing systemctl was accepted")


def test_preflight_refuses_each_dangerous_boundary(tmp_path: Path) -> None:
    config_path, machine = preflight_fixture(tmp_path)
    base = json.loads(config_path.read_text())
    cases = {
        "authority": {"deployment_authorized": False},
        "artifact": {"phlogiston_artifact_sha256": "0" * 64},
        "secret": {"secret_custody_receipt": str(tmp_path / "missing.json")},
        "host": {"expected_machine_id_sha256": "f" * 64},
        "existing": {"state_root": str(tmp_path)},
    }
    for name, change in cases.items():
        candidate = dict(base)
        candidate.update(change)
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(candidate))
        try:
            validate_at_gate(path, machine, systemd_fixture(tmp_path / name))
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
            systemd_root=systemd_fixture(tmp_path),
            systemctl=None,
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
    assert "--with-status-web" in deploy
    assert "with_status_web=0" in deploy
    head, _, gated = deploy.partition('if [ "$with_status_web" -eq 1 ]; then\n  # Not used for Phase 2')
    assert gated, "status-web install is not gated"
    for status_only in ("systemctl enable --now phlogiston-web.service", "render-caddy.py", "caddy reload", "Caddyfile.before-phlogiston"):
        assert status_only not in head, status_only
        assert status_only in gated, status_only
    assert "https://phlogiston.app/healthz" not in deploy
    for refused in ("phlogiston.app|phlogiston.social|*.phlogiston.social)", "defines no site block"):
        assert refused in gated, refused
    preflight = (ROOT / "deploy/production/preflight.py").read_text()
    assert "backup_custody_receipt" not in preflight
    assert "zero-user-host-loss-reconstruction" in preflight
    assert "communityd-serve" in preflight
    assert "check_caddy_fragment_withdrawn" in preflight
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
