"""The production verification checks refuse to run without the explicit switch.

Only the refusal paths run here: nothing below reaches the network, systemd or
the host. The checks themselves are executed by an operator against the live
deployment (docs/PRODUCTION-VERIFICATION.md).
"""

from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).parents[1]
SCRIPTS = sorted((ROOT / "qualification/production").glob("verify-*.sh"))


def run(script: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    clean = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), **(env or {})}
    return subprocess.run(["sh", str(script), *args], capture_output=True, text=True, env=clean, timeout=30, check=False)


def test_five_checks_are_present_and_executable() -> None:
    names = [script.name for script in SCRIPTS]
    assert names == [
        "verify-external-permalink.sh",
        "verify-identity-resolution.sh",
        "verify-indexing-lag.sh",
        "verify-notification-idempotence.sh",
        "verify-oauth-continuity.sh",
    ]
    for script in SCRIPTS:
        assert os.access(script, os.X_OK), script.name
        text = script.read_text()
        assert 'verify_guard "$@"' in text, script.name
        assert text.index("verify_guard") < text.index("curl") if "curl" in text else True, script.name


def test_checks_refuse_without_the_explicit_switch(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    for script in SCRIPTS:
        result = run(script, "--receipt", str(receipt), "--handle", "x")
        assert result.returncode == 64, (script.name, result.stderr)
        assert "PHLOGISTON_PRODUCTION_VERIFY=1" in result.stderr, script.name
        assert not receipt.exists()
        result = run(script, "--receipt", str(receipt), env={"PHLOGISTON_PRODUCTION_VERIFY": "yes"})
        assert result.returncode == 64, (script.name, result.stderr)


def test_checks_refuse_missing_relative_or_existing_receipt(tmp_path: Path) -> None:
    env = {"PHLOGISTON_PRODUCTION_VERIFY": "1"}
    existing = tmp_path / "existing.json"
    existing.write_text("{}")
    for script in SCRIPTS:
        for args, expected in (
            ((), "--receipt"),
            (("--handle", "x"), "--receipt"),
            (("--receipt", "relative.json"), "absolute"),
            (("--receipt", str(existing)), "exists"),
        ):
            result = run(script, *args, env=env)
            assert result.returncode == 64, (script.name, args, result.stderr)
            assert "refused" in result.stderr and expected in result.stderr, (script.name, args, result.stderr)
    assert existing.read_text() == "{}"


def test_checks_refuse_missing_arguments_before_any_effect(tmp_path: Path) -> None:
    env = {"PHLOGISTON_PRODUCTION_VERIFY": "1"}
    for script in SCRIPTS:
        receipt = tmp_path / f"{script.stem}.json"
        result = run(script, "--receipt", str(receipt), env=env)
        assert result.returncode == 64, (script.name, result.stderr)
        assert "usage:" in result.stderr or "refused" in result.stderr, (script.name, result.stderr)
        assert not receipt.exists(), script.name


def test_receipt_writer_is_secret_free_by_construction() -> None:
    lib = (ROOT / "qualification/production/lib.sh").read_text()
    assert "phlogiston.production-verification.v1" in lib
    lag = (ROOT / "qualification/production/verify-indexing-lag.sh").read_text()
    assert "PHLOGISTON_VERIFY_APP_PASSWORD_FILE" in lag
    assert "unset access" in lag
    assert "write_receipt" in lag and '"$access"' not in lag.split("unset access")[1]
    probe = (ROOT / "qualification/production/oauth-continuity.ts").read_text()
    assert "access_token" not in probe and "refresh_token" not in probe
