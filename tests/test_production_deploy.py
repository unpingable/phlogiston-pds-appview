from pathlib import Path


ROOT = Path(__file__).parents[1]


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
