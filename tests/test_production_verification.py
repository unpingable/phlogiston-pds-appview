"""The production verification checks refuse to run without the explicit switch.

Only the refusal paths run here: nothing below reaches the network, systemd or
the host. The checks themselves are executed by an operator against the live
deployment (docs/PRODUCTION-VERIFICATION.md).
"""

from pathlib import Path
import shutil
import os
import subprocess

ROOT = Path(__file__).parents[1]
SCRIPTS = sorted((ROOT / "qualification/production").glob("verify-*.sh"))
PRODUCTION = ROOT / "qualification/production"
MANIFEST = ROOT / "qualification/production-verifier-manifest.json"
VALIDATOR = PRODUCTION / "validate-production-verifier-closure.py"


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
    assert "verify_indexing_record.py" in lag
    assert "--intent" in lag and "--rkey" in lag
    assert "com.atproto.repo.createRecord" not in lag
    probe = (ROOT / "qualification/production/oauth-continuity.ts").read_text()
    assert "access_token" not in probe and "refresh_token" not in probe


def test_oauth_wrapper_binds_assigned_baseline_only_to_final_timer() -> None:
    wrapper = (PRODUCTION / "verify-oauth-continuity.sh").read_text()
    baseline_call = wrapper.index('oauth-continuity.ts" baseline')
    assignment = wrapper.index('baseline_sha=$(sha256sum "$baseline"')
    final_timer = wrapper.index('systemd-run --unit="$unit" --on-active=')
    digest_binding = wrapper.index('PHLOGISTON_VERIFY_BASELINE_SHA256="$baseline_sha"')
    assert baseline_call < assignment < final_timer < digest_binding
    assert wrapper.count("PHLOGISTON_VERIFY_BASELINE_SHA256") == 1


def test_oauth_wrapper_executes_baseline_and_final_command_doubles(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    calls = tmp_path / "systemd-run.calls"
    (fake_bin / "id").write_text("#!/bin/sh\nprintf '0\\n'\n")
    (fake_bin / "install").write_text("#!/bin/sh\nfor value do target=$value; done\nmkdir -p \"$target\"\n")
    (fake_bin / "systemd-run").write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$*\" >> \"$PHLOGISTON_COMMAND_DOUBLE_LOG\"\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  if [ \"$1\" = baseline ]; then shift; shift; printf '{}\\n' > \"$1\"; fi\n"
        "  shift\n"
        "done\n"
    )
    for command in fake_bin.iterdir():
        command.chmod(0o755)
    live_root = tmp_path / "live"
    (live_root / "node_modules/.bin").mkdir(parents=True)
    tsx = live_root / "node_modules/.bin/tsx"
    tsx.write_text("#!/bin/sh\nexit 99\n")
    tsx.chmod(0o755)
    env_file = tmp_path / "community-web.env"
    env_file.write_text("# local command double\n")
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    receipt = tmp_path / "receipt.json"
    environment = {
        "PATH": f"{fake_bin}:{os.environ.get('PATH', '/usr/bin:/bin')}",
        "PHLOGISTON_PRODUCTION_VERIFY": "1",
        "PHLOGISTON_VERIFY_LOCAL_COMMAND_DOUBLE": "1",
        "PHLOGISTON_COMMAND_DOUBLE_LOG": str(calls),
    }
    result = run( PRODUCTION / "verify-oauth-continuity.sh", "--receipt", str(receipt), "--did", "did:plc:fixture", "--hours", "12", "--live-root", str(live_root), "--env-file", str(env_file), "--local-command-double-session-dir", str(session_dir), env=environment)
    assert result.returncode == 0, result.stderr
    entries = calls.read_text().splitlines()
    assert len(entries) == 2
    assert "oauth-continuity.ts baseline did:plc:fixture" in entries[0]
    assert "PHLOGISTON_VERIFY_BASELINE_SHA256=" not in entries[0]
    baseline = receipt.with_suffix(receipt.suffix + ".baseline.json")
    baseline_sha = __import__("hashlib").sha256(baseline.read_bytes()).hexdigest()
    assert f"PHLOGISTON_VERIFY_BASELINE_SHA256={baseline_sha}" in entries[1]
    assert "oauth-continuity.ts verify did:plc:fixture" in entries[1]


def test_oauth_probe_uses_sdk_iso_expiry_and_post_read_currentness() -> None:
    probe = (PRODUCTION / "oauth-continuity.ts").read_text()
    assert 'typeof value !== "string"' in probe
    assert "ISO expires_at string" in probe
    assert probe.index("assessPrerequisites") < probe.index('client.restore(did, "auto")')
    assert probe.index("readCompletedAt") > probe.index("await response.json()")
    assert "ranAt: readCompletedAt" in probe


def test_closed_production_verifier_manifest_refuses_tree_substitution(tmp_path: Path) -> None:
    passed = subprocess.run(["python3", str(VALIDATOR), "--root", str(PRODUCTION), "--manifest", str(MANIFEST)], capture_output=True, text=True, check=False)
    assert passed.returncode == 0, passed.stderr
    copied = tmp_path / "production"
    shutil.copytree(PRODUCTION, copied)
    (copied / "unexpected.py").write_text("# substitution fixture\n")
    refused = subprocess.run(["python3", str(VALIDATOR), "--root", str(copied), "--manifest", str(MANIFEST)], capture_output=True, text=True, check=False)
    assert refused.returncode == 1
    assert "close" in refused.stderr


def test_closed_manifest_refuses_links_missing_member_and_content_replacement(tmp_path: Path) -> None:
    copied = tmp_path / "production"
    shutil.copytree(PRODUCTION, copied)
    missing = copied / "lib.sh"
    missing.unlink()
    refused_missing = subprocess.run(["python3", str(VALIDATOR), "--root", str(copied), "--manifest", str(MANIFEST)], capture_output=True, text=True, check=False)
    assert refused_missing.returncode == 1
    assert "close" in refused_missing.stderr

    shutil.rmtree(copied)
    shutil.copytree(PRODUCTION, copied)
    replacement = copied / "lib.sh"
    replacement.unlink()
    replacement.write_text("#!/bin/sh\n# pathname replacement fixture\n")
    refused_replacement = subprocess.run(["python3", str(VALIDATOR), "--root", str(copied), "--manifest", str(MANIFEST)], capture_output=True, text=True, check=False)
    assert refused_replacement.returncode == 1
    assert "digest mismatch" in refused_replacement.stderr

    root_link = tmp_path / "production-link"
    root_link.symlink_to(PRODUCTION, target_is_directory=True)
    refused_root_link = subprocess.run(["python3", str(VALIDATOR), "--root", str(root_link), "--manifest", str(MANIFEST)], capture_output=True, text=True, check=False)
    assert refused_root_link.returncode == 1
    assert "root must be a real directory" in refused_root_link.stderr

    manifest_link = tmp_path / "manifest-link.json"
    manifest_link.symlink_to(MANIFEST)
    refused_manifest_link = subprocess.run(["python3", str(VALIDATOR), "--root", str(PRODUCTION), "--manifest", str(manifest_link)], capture_output=True, text=True, check=False)
    assert refused_manifest_link.returncode == 1
    assert "manifest must be a real regular file" in refused_manifest_link.stderr


def test_closed_manifest_refuses_duplicate_json_key(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate-manifest.json"
    duplicate.write_text('{"schema":"phlogiston.production-verifier-closure.v1","schema":"x","files":[]}')
    refused = subprocess.run(["python3", str(VALIDATOR), "--root", str(PRODUCTION), "--manifest", str(duplicate)], capture_output=True, text=True, check=False)
    assert refused.returncode == 1
    assert "duplicate JSON key" in refused.stderr
