from pathlib import Path
import importlib.util
import json


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("verify_release", ROOT / "deploy/verify-release.py")
assert SPEC and SPEC.loader
VERIFY_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY_RELEASE)
verify = VERIFY_RELEASE.verify


def test_web_unit_is_loopback_only_and_preserves_state_boundary() -> None:
    unit = (ROOT / "deploy/production/phlogiston-web.service").read_text()
    environment = (ROOT / "deploy/production/phlogiston-web.env.example").read_text()
    assert "ExecStart=/usr/bin/node dist/server.js" in unit
    assert "StateDirectory=phlogiston" in unit
    assert "ReadWritePaths=/var/lib/phlogiston" in unit
    assert "PORT=8092" in environment
    assert "PHLOGISTON_PUBLIC_URL=https://phlogiston.app" in environment
    assert "SET_EXACT_COMMUNITY_DID_BEFORE_START" in environment
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
