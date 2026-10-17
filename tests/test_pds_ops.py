from __future__ import annotations

import io
import json
from pathlib import Path
import sqlite3
import shutil
import subprocess
import tarfile

import pytest

from phlogiston_appview import pds_ops as ops


@pytest.fixture(autouse=True)
def retire_local_substrate(tmp_path):
    # Each test owns this exact fixture directory; it has no replay consumer.
    yield
    shutil.rmtree(tmp_path)


def fixture(tmp_path: Path, monkeypatch):
    data = tmp_path / "data"; data.mkdir(mode=0o700)
    for name in ["account.sqlite", "sequencer.sqlite", "actors/example/store.sqlite"]:
        path = data / name; path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE fixture(value)"); db.execute("INSERT INTO fixture VALUES('preserved')")
    (data / "blocks").mkdir(); (data / "blocks/blob").write_bytes(b"local substitution blob")
    env = tmp_path / "pds.env"
    template = Path(__file__).resolve().parents[1] / "deploy/production/phlogiston-pds.env.example"
    ops.configure(env, template)
    compose = tmp_path / "compose.yaml"; compose.write_text("image: " + ops.IMAGE + "\n")
    identity = tmp_path / "age.identity"
    subprocess.run(["age-keygen", "-o", str(identity)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    identity.chmod(0o600)
    recipient = subprocess.run(["age-keygen", "-y", str(identity)], capture_output=True, text=True, check=True).stdout.strip()
    monkeypatch.setattr(ops, "run", lambda args: "inactive" if "show" in args else "")
    return data, env, compose, identity, recipient


def test_private_config_and_no_clobber(tmp_path):
    env = tmp_path / "env"
    ops.configure(env, Path(__file__).resolve().parents[1] / "deploy/production/phlogiston-pds.env.example")
    config = ops.read_env(env)
    assert config["PDS_INVITE_REQUIRED"] == "true"
    assert len(config["PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX"]) == 64
    assert env.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        ops.configure(env, Path(__file__).resolve().parents[1] / "deploy/production/phlogiston-pds.env.example")
    env.chmod(0o644)
    with pytest.raises(ValueError, match="owner-only"):
        ops.read_env(env)


def test_provision_custodies_before_effect_and_recovers_unknown(tmp_path, monkeypatch):
    env = tmp_path / "env"
    ops.configure(env, Path(__file__).resolve().parents[1] / "deploy/production/phlogiston-pds.env.example")
    custody = tmp_path / "account.json"
    calls = []
    def request(base, method, body, admin=None):
        state = json.loads(custody.read_text()); calls.append(method)
        if method.endswith("createInviteCode"):
            assert state["phase"] == "prepared"; return {"code": "local-fixture-invite"}
        assert state["phase"] == "attempted_unknown"
        assert body["password"] == state["password"]
        if method.endswith("createAccount"):
            raise RuntimeError("local fixture unknown response")
        return {"did": "did:plc:" + "a" * 24, "handle": "fixture.phlogiston.social", "accessJwt": "never retained"}
    monkeypatch.setattr(ops, "request", request)
    with pytest.raises(RuntimeError):
        ops.provision(env, custody, "fixture.phlogiston.social", "fixture@example.invalid", "https://phlogiston.social")
    result = ops.provision(env, custody, "fixture.phlogiston.social", "fixture@example.invalid", "https://phlogiston.social")
    assert calls == ["com.atproto.server.createInviteCode", "com.atproto.server.createAccount", "com.atproto.server.createSession"]
    assert "password" not in result and "accessJwt" not in custody.read_text()
    assert ops.provision(env, custody, "fixture.phlogiston.social", "fixture@example.invalid", "https://phlogiston.social")["result"] == "already-provisioned"
    for base in ["https://juche.social", "https://phlogiston.social.other", "https://user@phlogiston.social", "http://phlogiston.social"]:
        with pytest.raises(ValueError): ops.origin(base)


@pytest.mark.parametrize("username", ["ab", "a" * 19, "ends-with-", "-starts-with"])
def test_provision_refuses_invalid_service_username_before_intent(tmp_path, monkeypatch, username):
    env = tmp_path / "env"
    ops.configure(env, Path(__file__).resolve().parents[1] / "deploy/production/phlogiston-pds.env.example")
    custody = tmp_path / "account.json"
    def unexpected_request(*args, **kwargs):
        pytest.fail("invalid username must not create an invite or account")
    monkeypatch.setattr(ops, "request", unexpected_request)
    with pytest.raises(ValueError, match="3..18"):
        ops.provision(env, custody, username + ".phlogiston.social", "fixture@example.invalid", "https://phlogiston.social")
    assert not custody.exists()


def test_stopped_encrypted_whole_state_restore_and_no_overwrite(tmp_path, monkeypatch):
    data, env, compose, identity, recipient = fixture(tmp_path, monkeypatch)
    archive = tmp_path / "backup.age"
    result = ops.backup(data, env, compose, archive, recipient, tmp_path / "backup-receipt.json", tmp_path / "checkpoint.json", ops.IMAGE)
    assert result["service_left_stopped"]
    assert ops.read_env(env)["PDS_ADMIN_PASSWORD"].encode() not in archive.read_bytes()
    target = tmp_path / "restored"; target.mkdir(mode=0o700)
    restored = ops.restore(archive, identity, target, result["ciphertext_sha256"], tmp_path / "restore-receipt.json")
    assert restored["result"] == "restored-not-started"
    assert (target / "config/pds.env").read_bytes() == env.read_bytes()
    assert (target / "data/blocks/blob").read_bytes() == (data / "blocks/blob").read_bytes()
    assert not (target / ".restore-incomplete.json").exists()
    with pytest.raises(ValueError, match="empty"):
        ops.restore(archive, identity, target, result["ciphertext_sha256"], tmp_path / "another-receipt.json")


def test_running_writer_and_symlink_state_refuse(tmp_path, monkeypatch):
    data, env, compose, identity, recipient = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(ops, "run", lambda args: "active" if "show" in args else "")
    with pytest.raises(RuntimeError, match="not stopped"):
        ops.backup(data, env, compose, tmp_path / "backup.age", recipient, tmp_path / "receipt", tmp_path / "checkpoint", ops.IMAGE)
    assert not (tmp_path / "backup.age").exists()
    (data / "link").symlink_to(env)
    with pytest.raises(ValueError, match="regular"):
        ops.inventory(data, env, compose)


def test_ciphertext_mutation_retains_incomplete_restore(tmp_path, monkeypatch):
    data, env, compose, identity, recipient = fixture(tmp_path, monkeypatch)
    archive = tmp_path / "backup.age"
    ops.backup(data, env, compose, archive, recipient, tmp_path / "receipt", tmp_path / "checkpoint", ops.IMAGE)
    raw = bytearray(archive.read_bytes()); raw[len(raw)//2] ^= 1; archive.write_bytes(raw)
    target = tmp_path / "restore"; target.mkdir(mode=0o700)
    with pytest.raises((RuntimeError, tarfile.TarError, ValueError)):
        ops.restore(archive, identity, target, ops.digest(archive), tmp_path / "restore-receipt")
    assert (target / ".restore-incomplete.json").exists()
    assert not (tmp_path / "restore-receipt").exists()


def test_archive_path_substitution_refuses(tmp_path, monkeypatch):
    _, _, _, identity, recipient = fixture(tmp_path, monkeypatch)
    clear = io.BytesIO()
    with tarfile.open(fileobj=clear, mode="w") as tar:
        content = json.dumps({"schema": "phlogiston.pds-archive.v1", "hostname": "phlogiston.social", "image": ops.IMAGE, "files": {name: {"sha256": "none", "size": 1} for name in ["config/pds.env", "config/compose.yaml", "data/account.sqlite", "data/sequencer.sqlite", "data/../outside"]}}).encode()
        info = tarfile.TarInfo("manifest.json"); info.size = len(content); tar.addfile(info, io.BytesIO(content))
        info = tarfile.TarInfo("data/../outside"); info.size = 1; tar.addfile(info, io.BytesIO(b"x"))
    archive = tmp_path / "substitution.age"
    with archive.open("wb") as output:
        subprocess.run(["age", "-r", recipient], input=clear.getvalue(), stdout=output, check=True)
    archive.chmod(0o600); target = tmp_path / "restore"; target.mkdir(mode=0o700)
    with pytest.raises(ValueError, match="restore source identity|restore members|archive member"):
        ops.restore(archive, identity, target, ops.digest(archive), tmp_path / "receipt")
    assert not (tmp_path / "outside").exists()


def qualifier_fixture(tmp_path, monkeypatch):
    target = tmp_path / "restore"; target.mkdir(mode=0o700); (target / "config").mkdir(mode=0o700)
    env = target / "config/pds.env"
    ops.configure(env, Path(__file__).resolve().parents[1] / "deploy/production/phlogiston-pds.env.example")
    restored = tmp_path / "restored.json"
    ops.write_private(restored, {"result": "restored-not-started", "target": str(target), "image": ops.IMAGE, "archive_sha256": "a" * 64})
    did = "did:plc:" + "a" * 24; handle = "fixture.phlogiston.social"
    credentials = tmp_path / "credentials.json"
    ops.write_private(credentials, {"phase": "complete", "did": did, "handle": handle, "password": "local-substitution-password"})
    expectations = tmp_path / "expected.json"
    account = {"did": did, "handle": handle, "records": [{"uri": f"at://{did}/app.bsky.feed.post/one", "cid": "exact-cid"}]}
    expectations.write_text(json.dumps({"accounts": [account]}))
    inspection = {"Id": "b" * 64, "State": {"Running": True}, "HostConfig": {"NetworkMode": "none", "PortBindings": {}, "Privileged": False}, "Config": {"Image": ops.IMAGE, "Env": [key + "=" + value for key, value in ops.read_env(env).items()]}, "Mounts": [{"Type": "bind", "Source": str(target / "data"), "Destination": "/pds"}], "NetworkSettings": {"Networks": {"none": {"IPAddress": "", "GlobalIPv6Address": ""}}}}
    monkeypatch.setattr(ops, "run", lambda args: json.dumps(inspection))
    return target, restored, expectations, credentials, inspection, account


def test_qualifier_private_stdin_exact_output_and_isolated_clone(tmp_path, monkeypatch):
    target, restored, expectations, credentials, inspection, account = qualifier_fixture(tmp_path, monkeypatch)
    def execute(args, **kwargs):
        assert args[3] == inspection["Id"]
        assert "local-substitution-password" not in " ".join(args)
        assert json.loads(kwargs["input"])["accounts"][0]["password"] == "local-substitution-password"
        result = {"result": "restored-auth-and-records-verified", "accounts": [{**account, "records": [{**account["records"][0], "valueChecked": False}]}]}
        return subprocess.CompletedProcess(args, 0, json.dumps(result), "")
    monkeypatch.setattr(ops.subprocess, "run", execute)
    receipt = tmp_path / "qualified.json"
    result = ops.qualify_restore("phlogiston-pds-restore-fixture", target, restored, expectations, [credentials], receipt)
    assert result["network"] == "none" and "local-substitution-password" not in receipt.read_text()
    assert result["accounts"][0]["records"][0]["cid"] == "exact-cid"


@pytest.mark.parametrize("transition", ["network", "extra-network", "ports", "original-mount", "image", "private-env", "after-change"])
def test_qualifier_refuses_runtime_substitution(tmp_path, monkeypatch, transition):
    target, restored, expectations, credentials, inspection, account = qualifier_fixture(tmp_path, monkeypatch)
    calls = 0
    def inspect(args):
        nonlocal calls
        calls += 1
        if transition == "after-change" and calls > 1:
            inspection["Config"]["Image"] = "different"
        return json.dumps(inspection)
    monkeypatch.setattr(ops, "run", inspect)
    if transition == "network": inspection["HostConfig"]["NetworkMode"] = "host"
    if transition == "extra-network": inspection["NetworkSettings"]["Networks"]["bridge"] = {"IPAddress": "172.1.1.1"}
    if transition == "ports": inspection["HostConfig"]["PortBindings"] = {"3000/tcp": [{"HostPort": "3003"}]}
    if transition == "original-mount": inspection["Mounts"][0]["Source"] = "/var/lib/phlogiston-pds"
    if transition == "image": inspection["Config"]["Image"] = "other"
    if transition == "private-env": inspection["Config"]["Env"] = []
    result = {"result": "restored-auth-and-records-verified", "accounts": [{**account, "records": [{**account["records"][0], "valueChecked": False}]}]}
    monkeypatch.setattr(ops.subprocess, "run", lambda args, **kwargs: subprocess.CompletedProcess(args, 0, json.dumps(result), ""))
    receipt = tmp_path / "qualified.json"
    with pytest.raises(ValueError):
        ops.qualify_restore("phlogiston-pds-restore-fixture", target, restored, expectations, [credentials], receipt)
    assert not receipt.exists()


def test_node_runner_auth_record_checks_without_credential_output(tmp_path):
    did = "did:plc:" + "a" * 24; handle = "fixture.phlogiston.social"; uri = f"at://{did}/app.bsky.feed.post/one"
    shim = '''globalThis.fetch=async url=>({ok:true,text:async()=>JSON.stringify(String(url).includes('createSession')?{did:"DID",handle:"fixture.phlogiston.social",accessJwt:"local-private-token"}:{uri:"URI",cid:"exact",value:{text:"fixture"}})});'''.replace("DID", did).replace("URI", uri)
    account = {"did": did, "handle": handle, "password": "local-private-password", "records": [{"uri": uri, "cid": "exact", "value": {"text": "fixture"}}]}
    completed = subprocess.run(["node", "--input-type=module", "--eval", shim + ops.RESTORE_NODE], input=json.dumps({"accounts": [account]}), capture_output=True, text=True)
    assert completed.returncode == 0
    assert "local-private" not in completed.stdout + completed.stderr
    account["records"][0]["cid"] = "different"
    refused = subprocess.run(["node", "--input-type=module", "--eval", shim + ops.RESTORE_NODE], input=json.dumps({"accounts": [account]}), capture_output=True, text=True)
    assert refused.returncode == 1 and not refused.stdout
    assert "local-private" not in refused.stderr
    interrupted = subprocess.run(["node", "--input-type=module", "--eval", ops.RESTORE_NODE], input='{"accounts":[{"password":"local-private-password', capture_output=True, text=True)
    assert interrupted.returncode == 1 and not interrupted.stdout
    assert "local-private" not in interrupted.stderr
