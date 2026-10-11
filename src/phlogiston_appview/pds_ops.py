"""Bounded upstream-PDS operations; runtime custody belongs to the operator.

No install, image pull, automatic restart, public invites or migration is performed.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import sqlite3
import stat
import subprocess
import tarfile
import urllib.error
import urllib.request

from .integrated_recovery import checkpoint as checkpoint_sqlite

IMAGE = "ghcr.io/bluesky-social/pds@sha256:74c650cd620eee2e6e0272b4cb76036a0271523b1742f61f813b79dc5a8b5273"
UNIT = "phlogiston-pds.service"
CONTAINER = "phlogiston-pds"


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def directory(path: Path) -> Path:
    if not path.is_absolute() or path.is_symlink() or not path.is_dir() or path.resolve() != path:
        raise ValueError("existing canonical directory required")
    return path


def private_file(path: Path) -> Path:
    directory(path.parent)
    mode = path.lstat()
    if not stat.S_ISREG(mode.st_mode) or mode.st_mode & 0o077 or mode.st_uid != os.geteuid():
        raise ValueError("owner-only regular custody file required")
    return path


def write_private(path: Path, value: dict | str, *, replace: bool = False) -> None:
    directory(path.parent)
    content = value if isinstance(value, str) else json.dumps(value, sort_keys=True) + "\n"
    if replace:
        private_file(path)
    temporary = path.parent / ("." + path.name + "." + secrets.token_hex(8))
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)  # no-clobber publication
            temporary.unlink()
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def run(args: list[str]) -> str:
    completed = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if completed.returncode:
        raise RuntimeError("operator command refused or failed: " + args[0])
    return completed.stdout.strip()


def read_env(path: Path) -> dict[str, str]:
    result = {}
    for line in private_file(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key in result or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError("plain unique environment assignments required")
        result[key] = value
    if result.get("PDS_HOSTNAME") != "phlogiston.social" or result.get("PDS_INVITE_REQUIRED") != "true":
        raise ValueError("exact Phlogiston hostname and invite-only configuration required")
    return result


def configure(output: Path, template: Path) -> dict:
    text = template.read_text()
    generated = subprocess.run(["openssl", "ecparam", "-name", "secp256k1", "-genkey", "-noout", "-outform", "DER"], capture_output=True, check=True).stdout
    if generated[2:7] != b"\x02\x01\x01\x04\x20" or len(generated) < 39:
        raise RuntimeError("unexpected OpenSSL EC private-key encoding")
    values = {"PDS_JWT_SECRET": secrets.token_hex(32), "PDS_DPOP_SECRET": secrets.token_hex(32),
              "PDS_ADMIN_PASSWORD": secrets.token_hex(32), "PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX": generated[7:39].hex()}
    for key, value in values.items():
        text, count = re.subn(rf"(?m)^{key}=SET_OWNER_ONLY_AT_ACTIVATION$", key + "=" + value, text)
        if count != 1:
            raise ValueError("expected private template placeholder missing")
    if "SET_" in text or "PDS_INVITE_REQUIRED=true" not in text:
        raise ValueError("incomplete or registration-enabled template")
    write_private(output, text)
    read_env(output)
    return {"result": "configured", "private_environment": str(output)}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise RuntimeError("PDS redirects are refused")


def origin(base: str) -> str:
    if base == "https://phlogiston.social" or re.fullmatch(r"http://127\.0\.0\.1:[1-9][0-9]{0,4}", base):
        return base
    raise ValueError("exact Phlogiston HTTPS origin or operator loopback origin required")


def request(base: str, method: str, body: dict, admin: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if admin:
        headers["Authorization"] = "Basic " + base64.b64encode(("admin:" + admin).encode()).decode()
    req = urllib.request.Request(origin(base) + "/xrpc/" + method, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as response:
            data = response.read(1024 * 1024 + 1)
            if len(data) > 1024 * 1024:
                raise RuntimeError("PDS response exceeded bound")
            return json.loads(data)
    except (urllib.error.URLError, ValueError) as error:
        # Never echo provider bodies, passwords, tokens or request headers.
        raise RuntimeError("PDS response unavailable or invalid; reconcile private checkpoint") from None


def provision(env: Path, custody: Path, handle: str, email: str, base: str) -> dict:
    configuration = read_env(env)
    origin(base)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,61}\.phlogiston\.social", handle) or "@" not in email:
        raise ValueError("disposable hosted handle and email required")
    if custody.exists():
        state = json.loads(private_file(custody).read_text())
        if state.get("handle") != handle or state.get("origin") != base or state.get("email") != email:
            raise ValueError("checkpoint belongs to another account or origin")
        if state["phase"] == "complete":
            return {"result": "already-provisioned", "did": state["did"], "handle": handle, "custody": str(custody)}
        # An interrupted effect is checked using its already-custodied password.
        current = request(base, "com.atproto.server.createSession", {"identifier": handle, "password": state["password"]})
    else:
        state = {"phase": "prepared", "handle": handle, "email": email, "origin": base,
                 "password": secrets.token_urlsafe(32), "created_at": stamp()}
        write_private(custody, state)
        invite = request(base, "com.atproto.server.createInviteCode", {"useCount": 1}, configuration["PDS_ADMIN_PASSWORD"])
        state.update(phase="attempted_unknown", invite_code=invite["code"])
        write_private(custody, state, replace=True)
        current = request(base, "com.atproto.server.createAccount", {"handle": handle, "email": email, "password": state["password"], "inviteCode": invite["code"]})
    if not re.fullmatch(r"did:plc:[a-z2-7]{24}", current.get("did", "")) or current.get("handle") != handle:
        raise RuntimeError("created account identity did not match checkpoint")
    state.update(phase="complete", did=current["did"], completed_at=stamp())
    state.pop("invite_code", None)
    write_private(custody, state, replace=True)
    return {"result": "provisioned", "did": state["did"], "handle": handle, "custody": str(custody)}


def stopped() -> None:
    if run(["systemctl", "show", UNIT, "--property=ActiveState", "--value"]) not in {"inactive", "failed"}:
        raise RuntimeError("PDS unit is not stopped")
    if run(["docker", "ps", "--filter", "name=^/" + CONTAINER + "$", "--format", "{{.Names}}"]):
        raise RuntimeError("PDS container is still running")


def inventory(data: Path, env: Path, compose: Path) -> dict[str, Path]:
    directory(data)
    if not compose.is_absolute() or compose.is_symlink() or not compose.is_file() or compose.resolve() != compose:
        raise ValueError("canonical regular compose source required")
    if not (data / "account.sqlite").is_file() or not (data / "sequencer.sqlite").is_file():
        raise ValueError("complete upstream account and sequencer state required")
    result = {"config/pds.env": private_file(env), "config/compose.yaml": compose}
    for path in sorted(data.rglob("*")):
        mode = path.lstat()
        if stat.S_ISDIR(mode.st_mode):
            continue
        if not stat.S_ISREG(mode.st_mode) or path.is_symlink():
            raise ValueError("PDS state must contain only regular files/directories")
        result["data/" + path.relative_to(data).as_posix()] = path
    return result


def backup(data: Path, env: Path, compose: Path, archive: Path, recipient: str, receipt: Path, checkpoint: Path, image: str) -> dict:
    if not re.fullmatch(r"age1[0-9a-z]+", recipient) or not re.fullmatch(r"ghcr.io/bluesky-social/pds@sha256:[0-9a-f]{64}", image):
        raise ValueError("age recipient and exact upstream image digest required")
    directory(archive.parent)
    directory(data)
    if archive.is_relative_to(data) or env.is_relative_to(data) or compose.is_relative_to(data) or receipt.is_relative_to(data) or checkpoint.is_relative_to(data):
        raise ValueError("capture outputs and private/public configuration must be outside PDS data")
    if archive.exists() or archive.is_symlink() or receipt.exists() or checkpoint.exists():
        raise ValueError("new archive, receipt and checkpoint paths required")
    if image not in compose.read_text():
        raise ValueError("compose does not bind selected image")
    read_env(env)
    state = {"schema": "phlogiston.pds-capture.v1", "phase": "stopping", "unit": UNIT,
             "data": str(data), "archive": str(archive), "image": image, "ops_sha256": digest(Path(__file__)), "started_at": stamp(),
             "next": "inspect stopped unit/container and checkpoint; never duplicate capture or start restored writer"}
    write_private(checkpoint, state)
    run(["systemctl", "stop", UNIT]); stopped()
    state["phase"] = "stopped"; write_private(checkpoint, state, replace=True)
    for database in sorted(data.rglob("*.sqlite")):
        checkpoint_sqlite(database)
    files = inventory(data, env, compose)
    entries = {name: {"sha256": digest(path), "size": path.stat().st_size} for name, path in files.items()}
    manifest = {"schema": "phlogiston.pds-archive.v1", "image": image, "hostname": "phlogiston.social", "captured_at": stamp(), "files": entries}
    fd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as encrypted:
        producer = subprocess.Popen(["age", "--recipient", recipient], stdin=subprocess.PIPE, stdout=encrypted, stderr=subprocess.DEVNULL)
        try:
            with tarfile.open(fileobj=producer.stdin, mode="w|") as tar:
                content = json.dumps(manifest, sort_keys=True).encode(); info = tarfile.TarInfo("manifest.json"); info.size = len(content); info.mode = 0o600; tar.addfile(info, io.BytesIO(content))
                for name, path in files.items():
                    info = tar.gettarinfo(str(path), arcname=name); info.mode = 0o600; info.uid = info.gid = 0; info.uname = info.gname = ""
                    with path.open("rb") as source:
                        tar.addfile(info, source)
            producer.stdin.close()
            if producer.wait() != 0:
                raise RuntimeError("encrypted capture failed")
            encrypted.flush(); os.fsync(encrypted.fileno())
        finally:
            if producer.poll() is None:
                producer.terminate(); producer.wait()
    fd = os.open(archive.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    stopped()
    if entries != {name: {"sha256": digest(path), "size": path.stat().st_size} for name, path in inventory(data, env, compose).items()}:
        raise RuntimeError("stopped state changed during capture; archive is unqualified")
    result = {"schema": "phlogiston.pds-backup-receipt.v1", "result": "encrypted-stopped-capture", "archive": str(archive), "ciphertext_sha256": digest(archive), "image": image, "file_count": len(files), "ops_sha256": digest(Path(__file__)), "finished_at": stamp(), "service_left_stopped": True}
    write_private(receipt, result)
    state.update(phase="complete", receipt=str(receipt), next="root verifies custody and explicitly restarts original unit; restore only into isolated fenced destination")
    write_private(checkpoint, state, replace=True)
    return result


def restore(archive: Path, identity: Path, target: Path, expected: str, receipt: Path) -> dict:
    private_file(identity); private_file(archive); directory(target)
    if any(target.iterdir()) or target.stat().st_mode & 0o077 or digest(archive) != expected:
        raise ValueError("empty owner-only restore directory and exact ciphertext digest required")
    incomplete = target / ".restore-incomplete.json"
    write_private(incomplete, {"phase": "restoring", "archive_sha256": expected, "start": stamp(), "next": "never start this state before complete restore receipt and explicit writer fencing"})
    producer = subprocess.Popen(["age", "--decrypt", "--identity", str(identity), str(archive)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        with tarfile.open(fileobj=producer.stdout, mode="r|") as tar:
            members = iter(tar)
            first = next(members)
            if first.name != "manifest.json" or not first.isfile() or first.size > 8 * 1024 * 1024:
                raise ValueError("bounded first archive manifest required")
            manifest = json.loads(tar.extractfile(first).read())
            if manifest.get("schema") != "phlogiston.pds-archive.v1" or manifest.get("hostname") != "phlogiston.social":
                raise ValueError("unsupported restore identity")
            if not re.fullmatch(r"ghcr.io/bluesky-social/pds@sha256:[0-9a-f]{64}", manifest.get("image", "")) or not isinstance(manifest.get("files"), dict):
                raise ValueError("unsupported restore source identity")
            required = {"config/pds.env", "config/compose.yaml", "data/account.sqlite", "data/sequencer.sqlite"}
            if not required.issubset(manifest["files"]) or any(not name.startswith(("data/", "config/")) for name in manifest["files"]):
                raise ValueError("incomplete PDS restore members")
            seen = set()
            for member in members:
                name = PurePosixPath(member.name)
                if not member.isfile() or name.is_absolute() or ".." in name.parts or str(name) != member.name or member.name not in manifest["files"] or member.name in seen:
                    raise ValueError("unexpected or nonregular archive member")
                output = target / member.name
                output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with output.open("xb") as stream:
                    os.chmod(output, 0o600)
                    source = tar.extractfile(member)
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        stream.write(block)
                    stream.flush(); os.fsync(stream.fileno())
                if {"sha256": digest(output), "size": output.stat().st_size} != manifest["files"][member.name]:
                    raise ValueError("restored member hash or length mismatch")
                seen.add(member.name)
            if seen != set(manifest["files"]):
                raise ValueError("archive members incomplete")
        # Drain through the encrypted stream authentication boundary.
        for block in iter(lambda: producer.stdout.read(1024 * 1024), b""):
            if block.strip(b"\0"):
                raise ValueError("trailing decrypted archive bytes")
        if producer.wait() != 0:
            raise RuntimeError("encrypted archive authentication failed")
    finally:
        if producer.poll() is None:
            producer.terminate(); producer.wait()
    for database in (target / "data").rglob("*.sqlite"):
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
            if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("restored SQLite integrity failed")
    read_env(target / "config/pds.env")
    if manifest["image"] not in (target / "config/compose.yaml").read_text():
        raise ValueError("restored compose image disagrees with encrypted manifest")
    result = {"result": "restored-not-started", "archive_sha256": expected, "target": str(target), "image": manifest["image"], "files": len(seen), "finished_at": stamp(), "writer_fencing_required": True}
    write_private(receipt, result)
    incomplete.unlink()
    return result

RESTORE_NODE = r'''
const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
async function xrpc(method, body, token, query) {
  const url = new URL('http://127.0.0.1:3000/xrpc/' + method);
  if (query) for (const [key, value] of Object.entries(query)) url.searchParams.set(key, value);
  const headers = {'content-type':'application/json'};
  if (token) headers.authorization = 'Bearer ' + token;
  const response = await fetch(url, {method:body ? 'POST' : 'GET',headers,body:body ? JSON.stringify(body) : undefined,signal:AbortSignal.timeout(5000)});
  if (!response.ok) throw new Error('unqualified local API response');
  const bytes = await response.text();
  if (bytes.length > 1048576) throw new Error('response limit');
  return JSON.parse(bytes);
}
try {
  const input = [];
  for await (const chunk of process.stdin) input.push(chunk);
  const { accounts } = JSON.parse(Buffer.concat(input).toString('utf8'));
  const verified = [];
  for (const account of accounts) {
    const session = await xrpc('com.atproto.server.createSession', {identifier:account.handle,password:account.password});
    if (session.did !== account.did || session.handle !== account.handle || typeof session.accessJwt !== 'string') throw new Error('identity mismatch');
    const records = [];
    for (const expected of account.records) {
      const match = /^at:\/\/(did:plc:[a-z2-7]{24})\/([a-zA-Z0-9.]+)\/([a-zA-Z0-9._~:-]+)$/.exec(expected.uri);
      if (!match || match[1] !== account.did) throw new Error('reference mismatch');
      const current = await xrpc('com.atproto.repo.getRecord', undefined, session.accessJwt, {repo:match[1],collection:match[2],rkey:match[3]});
      if (current.uri !== expected.uri || current.cid !== expected.cid) throw new Error('record mismatch');
      if (expected.value !== undefined && JSON.stringify(canonical(current.value)) !== JSON.stringify(canonical(expected.value))) throw new Error('value mismatch');
      records.push({uri:current.uri,cid:current.cid,valueChecked:expected.value !== undefined});
    }
    verified.push({did:account.did,handle:account.handle,records});
  }
  process.stdout.write(JSON.stringify({result:'restored-auth-and-records-verified',accounts:verified})+'\n');
} catch {
  process.stderr.write('Restore local API verification failed; no credentials or provider response emitted.\n');
  process.exitCode = 1;
}
'''


def qualify_restore(container: str, target: Path, restore_receipt: Path, expectations: Path,
                    credentials: list[Path], receipt: Path) -> dict:
    """Inspect an operator-started network-none clone; never start or mount it here."""
    if not re.fullmatch(r"phlogiston-pds-restore-[a-zA-Z0-9-]+", container):
        raise ValueError("explicit disposable restore container identity required")
    directory(target)
    restored = json.loads(private_file(restore_receipt).read_text())
    if restored.get("result") != "restored-not-started" or restored.get("target") != str(target) or (target / ".restore-incomplete.json").exists():
        raise ValueError("completed exact-target restore receipt required")
    if receipt.exists() or receipt.is_symlink():
        raise ValueError("new qualification receipt required")
    if expectations.stat().st_size > 1024 * 1024:
        raise ValueError("expectations exceed bound")
    expected = json.loads(expectations.read_text())
    accounts = expected.get("accounts")
    if not isinstance(accounts, list) or not 1 <= len(accounts) <= 10 or len(credentials) != len(accounts):
        raise ValueError("one credential per bounded expected account required")
    states = [json.loads(private_file(path).read_text()) for path in credentials]
    by_did = {state.get("did"): state for state in states}
    if len(by_did) != len(states):
        raise ValueError("duplicate credential identity")
    private_input = []
    seen = set()
    total_records = 0
    for account in accounts:
        did = account.get("did", "")
        if not re.fullmatch(r"did:plc:[a-z2-7]{24}", did) or did in seen:
            raise ValueError("unique expected PLC identity required")
        seen.add(did)
        state = by_did.get(did)
        records = account.get("records")
        if not state or state.get("phase") != "complete" or state.get("handle") != account.get("handle") or not isinstance(state.get("password"), str) or not state["password"]:
            raise ValueError("exact completed account custody required")
        if not isinstance(records, list) or not records:
            raise ValueError("each restored account needs an expected record")
        total_records += len(records)
        if total_records > 50:
            raise ValueError("record verification bound exceeded")
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("cid"), str) or not record["cid"] or not re.fullmatch(r"at://" + re.escape(did) + r"/[a-zA-Z0-9.]+/[a-zA-Z0-9._~:-]+", record.get("uri", "")):
                raise ValueError("expected own exact record reference required")
        private_input.append({"did": did, "handle": state["handle"], "password": state["password"], "records": records})
    inspected = json.loads(run(["docker", "inspect", container, "--format", "{{json .}}"] ))
    container_id = inspected.get("Id", "")
    if not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise ValueError("exact Docker container identity required")
    host = inspected.get("HostConfig", {})
    if not inspected.get("State", {}).get("Running") or host.get("NetworkMode") != "none" or host.get("PortBindings") or host.get("Privileged") or host.get("PidMode") == "host" or host.get("CgroupnsMode") == "host":
        raise ValueError("running nonprivileged network-none clone without published ports required")
    if inspected.get("Config", {}).get("Image") != restored.get("image"):
        raise ValueError("restore container image differs from receipt")
    networks = inspected.get("NetworkSettings", {}).get("Networks", {})
    if set(networks) != {"none"} or networks["none"].get("IPAddress") or networks["none"].get("GlobalIPv6Address"):
        raise ValueError("clone has an external network attachment")
    mounts = inspected.get("Mounts", [])
    if len(mounts) != 1 or mounts[0].get("Type") != "bind" or mounts[0].get("Destination") != "/pds" or mounts[0].get("Source") != str(target / "data"):
        raise ValueError("clone must bind only its exact restored data directory")
    environment = dict(entry.split("=", 1) for entry in inspected.get("Config", {}).get("Env", []) if "=" in entry)
    restored_env = read_env(target / "config/pds.env")
    for key in ["PDS_HOSTNAME", "PDS_JWT_SECRET", "PDS_ADMIN_PASSWORD", "PDS_DPOP_SECRET", "PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX", "PDS_DATA_DIRECTORY", "PDS_BLOBSTORE_DISK_LOCATION"]:
        if environment.get(key) != restored_env.get(key):
            raise ValueError("clone identity/private configuration differs from restored custody")
    completed = subprocess.run(["docker", "exec", "--interactive", container_id, "node", "--input-type=module", "--eval", RESTORE_NODE], input=json.dumps({"accounts": private_input}), capture_output=True, text=True, timeout=300)
    if completed.returncode or len(completed.stdout) > 64 * 1024:
        raise RuntimeError("restored clone authentication/record verification failed; provider responses suppressed")
    verified = json.loads(completed.stdout)
    # Reconstruct an allowlisted receipt, never relay arbitrary child output.
    if verified.get("result") != "restored-auth-and-records-verified" or len(verified.get("accounts", [])) != len(accounts):
        raise ValueError("unqualified verifier result")
    for actual, expected_account in zip(verified["accounts"], accounts, strict=True):
        if actual.get("did") != expected_account["did"] or actual.get("handle") != expected_account["handle"] or actual.get("records") != [{"uri": value["uri"], "cid": value["cid"], "valueChecked": "value" in value} for value in expected_account["records"]]:
            raise ValueError("verifier result differs from exact expectations")
    after = json.loads(run(["docker", "inspect", container_id, "--format", "{{json .}}"] ))
    if any(after.get(field) != inspected.get(field) for field in ["Id", "HostConfig", "Config", "Mounts", "NetworkSettings"]) or not after.get("State", {}).get("Running"):
        raise ValueError("restore container configuration changed during qualification")
    result = {"schema": "phlogiston.pds-isolated-restore.v1", "result": verified["result"], "container": container,
              "container_id": inspected["Id"], "network": "none", "target": str(target), "image": restored["image"],
              "accounts": [{"did": account["did"], "handle": account["handle"], "records": [{"uri": record["uri"], "cid": record["cid"], "value_checked": "value" in record} for record in account["records"]]} for account in accounts],
              "archive_sha256": restored["archive_sha256"], "expectations_sha256": digest(expectations),
              "restore_receipt_sha256": digest(restore_receipt), "ops_sha256": digest(Path(__file__)), "finished_at": stamp(),
              "scope": "isolated password authentication and exact record continuity; no OAuth/PLC/relay/migration claim"}
    write_private(receipt, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("configure"); config.add_argument("--output", type=Path, required=True); config.add_argument("--template", type=Path, required=True)
    account = commands.add_parser("provision"); account.add_argument("--env", type=Path, required=True); account.add_argument("--custody", type=Path, required=True); account.add_argument("--handle", required=True); account.add_argument("--email", required=True); account.add_argument("--base-url", default="https://phlogiston.social")
    capture = commands.add_parser("backup")
    for name in ["data", "env", "compose", "archive", "receipt", "checkpoint"]: capture.add_argument("--" + name, type=Path, required=True)
    capture.add_argument("--recipient", required=True); capture.add_argument("--image", default=IMAGE)
    recover = commands.add_parser("restore")
    for name in ["archive", "identity", "target", "receipt"]: recover.add_argument("--" + name, type=Path, required=True)
    recover.add_argument("--expected", required=True)
    qualify = commands.add_parser("qualify-restore")
    qualify.add_argument("--container", required=True)
    for name in ["target", "restore-receipt", "expectations", "receipt"]: qualify.add_argument("--" + name, type=Path, required=True)
    qualify.add_argument("--credential", dest="credentials", type=Path, action="append", required=True)
    args = vars(parser.parse_args()); command = args.pop("command")
    if "base_url" in args: args["base"] = args.pop("base_url")
    try:
        result = {"configure": configure, "provision": provision, "backup": backup, "restore": restore, "qualify-restore": qualify_restore}[command](**args)
    except Exception:
        raise SystemExit("PDS operation refused or incomplete; inspect its protected checkpoint and retain stopped/fenced state") from None
    print(json.dumps(result, sort_keys=True)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
