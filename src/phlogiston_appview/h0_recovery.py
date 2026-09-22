"""Fail-closed H0 capture and blank-host restore for the real PDS disk layout.

This module deliberately does not start a PDS or create an ATProto identity.  It
operates only after an operator has stopped the actual pinned PDS in an isolated
runtime and produced its local quiescence attestation.  It is a recovery tool,
not a substitution fixture or a deployment mechanism.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tarfile
import time
import os
from typing import Iterator


SCHEMA = "phlogiston.h0-recovery-manifest.v1"
RUN_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
SHA256_IMAGE = re.compile(r"[^\s@]+@sha256:[0-9a-f]{64}\Z")
SOURCE_REVISION = re.compile(r"[0-9a-f]{40}\Z")
REQUIRED = (
    "pds/account.sqlite",
    "pds/sequencer.sqlite",
    "pds/did_cache.sqlite",
    "app/application-state.json",
    "app/policy.json",
    "config/public.json",
    "config/secret-references.json",
    "keys/attestation.json",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_existing(path: Path, label: str) -> Path:
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ValueError(f"{label} must be an existing absolute non-symlink directory")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise ValueError(f"{label} must already be canonical")
    return resolved


def _regular_under(path: Path, root: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular non-symlink file")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label} escapes root") from error
    return resolved


def _canonical_json(path: Path, label: str) -> dict:
    raw = _regular_under(path, path.parents[1], label).read_bytes()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} is not JSON") from error
    if not isinstance(data, dict):
        raise ValueError(f"{label} must contain an object")
    return data


def _walk_regular(root: Path, prefix: str) -> Iterator[tuple[str, Path]]:
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink is not admitted: {path}")
        if path.is_file():
            yield f"{prefix}/{path.relative_to(root).as_posix()}", path
        elif not path.is_dir():
            raise ValueError(f"non-regular state member is not admitted: {path}")


def _members(source: Path) -> list[tuple[str, Path]]:
    for name in REQUIRED:
        _regular_under(source / name, source, name)
    actors = source / "pds/actors"
    blobs = source / "pds/blocks"
    if not actors.is_dir() or actors.is_symlink() or not blobs.is_dir() or blobs.is_symlink():
        raise ValueError("actual PDS actor-store and disk-blob directories are required")
    # The reference PDS shards actor directories before the DID directory.
    # Do not assume a one-level `actors/<did>` layout.
    actor_stores = list(actors.rglob("store.sqlite"))
    if not actor_stores:
        raise ValueError("at least one actual PDS actor store is required")
    if not any(blobs.rglob("*")) or not any(path.is_file() for path in blobs.rglob("*")):
        raise ValueError("at least one actual PDS disk blob is required")
    members = [(name, source / name) for name in REQUIRED]
    members.extend(_walk_regular(actors, "pds/actors"))
    members.extend(_walk_regular(blobs, "pds/blocks"))
    names = [name for name, _ in members]
    if len(names) != len(set(names)):
        raise ValueError("duplicate state member")
    return sorted(members)


def _assert_quiescent(source: Path, attestation: Path) -> dict:
    data = _canonical_json(attestation, "quiescence attestation")
    required = {"schema", "source_root", "writer_pids", "runtime", "observed_at"}
    if set(data) != required or data["schema"] != "phlogiston.h0-quiescence.v1":
        raise ValueError("quiescence attestation fields are not exact")
    if data["source_root"] != str(source) or data["writer_pids"] != []:
        raise ValueError("PDS writer is not attested stopped for this source")
    if not isinstance(data["runtime"], str) or not isinstance(data["observed_at"], int):
        raise ValueError("invalid quiescence attestation")
    sidecars = []
    for path in source.rglob("*.sqlite-wal"):
        sidecars.append(path.relative_to(source).as_posix())
    for path in source.rglob("*.sqlite-shm"):
        sidecars.append(path.relative_to(source).as_posix())
    if sidecars:
        raise ValueError("SQLite WAL/SHM sidecars remain; checkpoint after stopping PDS, then re-attest")
    return data


def _validate_identities(source: Path) -> list[str]:
    app = _canonical_json(source / "app/application-state.json", "application state")
    identities = app.get("synthetic_identities")
    if not isinstance(identities, list) or not identities or not all(
        isinstance(value, str) and value.startswith("did:") for value in identities
    ):
        raise ValueError("application state must name synthetic DID-related identities")
    policy = _canonical_json(source / "app/policy.json", "application policy")
    if policy.get("schema") != "phlogiston.local-policy.v1":
        raise ValueError("application policy schema is not exact")
    refs = _canonical_json(source / "config/secret-references.json", "secret reference inventory")
    if refs.get("schema") != "phlogiston.secret-reference-inventory.v1" or "references" not in refs:
        raise ValueError("secret reference inventory is not exact")
    keys = _canonical_json(source / "keys/attestation.json", "key attestation")
    if keys.get("schema") != "phlogiston.key-attestation.v1" or "fingerprints" not in keys:
        raise ValueError("key attestation is not exact")
    return sorted(identities)


def capture(source: Path, archive: Path, *, run_id: str, pds_revision: str, pds_version: str,
            pds_image: str, app_revision: str, attestation: Path, captured_at: int | None = None) -> dict:
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("invalid run id")
    if not SOURCE_REVISION.fullmatch(pds_revision) or not SOURCE_REVISION.fullmatch(app_revision):
        raise ValueError("source revisions must be exact 40-character commits")
    if not pds_version or not SHA256_IMAGE.fullmatch(pds_image):
        raise ValueError("PDS version and immutable image digest are required")
    source = _canonical_existing(source, "source root")
    if not archive.is_absolute() or archive.exists() or archive.is_symlink():
        raise ValueError("archive must be a new absolute non-symlink path")
    _canonical_existing(archive.parent, "archive parent")
    quiescence = _assert_quiescent(source, attestation)
    identities = _validate_identities(source)
    members = _members(source)
    files = {name: {"sha256": _sha256_file(path), "bytes": path.stat().st_size,
                    "mode": path.stat().st_mode & 0o777, "uid": path.stat().st_uid,
                    "gid": path.stat().st_gid} for name, path in members}
    manifest = {
        "schema": SCHEMA, "run_id": run_id, "captured_at": int(time.time() if captured_at is None else captured_at),
        "pds": {"source_revision": pds_revision, "version": pds_version, "image": pds_image,
                "database": "SQLite (account, sequencer, DID cache, per-actor store)", "blobstore": "disk"},
        "application": {"source_revision": app_revision, "surface": "local state, policy, static renderer"},
        "identities": identities, "files": files,
        "consistency": {"writer": "stopped", "quiescence": quiescence, "sqlite_wal_sidecars": "absent-after-checkpoint"},
        "excluded": ["secret values", "PLC/network state", "relays", "AppViews", "feed generators", "search", "moderation services"],
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    with tarfile.open(archive, "x") as tar:
        for name, path in members:
            info = tar.gettarinfo(str(path), arcname=f"state/{name}")
            info.uid = info.gid = 0; info.uname = info.gname = ""
            with path.open("rb") as handle:
                tar.addfile(info, handle)
        for name, data in (("manifest.json", manifest_bytes), ("manifest.sha256", hashlib.sha256(manifest_bytes).hexdigest().encode() + b"  manifest.json\n")):
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o600
            tar.addfile(info, __import__("io").BytesIO(data))
    archive.chmod(0o600)
    return manifest


def _read_archive(archive: Path) -> tuple[dict, dict[str, bytes]]:
    if not archive.is_absolute() or archive.is_symlink() or not archive.is_file():
        raise ValueError("archive must be an absolute regular non-symlink file")
    with tarfile.open(archive, "r") as tar:
        members = tar.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(not member.isfile() or member.name.startswith("/") or ".." in Path(member.name).parts for member in members):
            raise ValueError("archive member is unsafe")
        if "manifest.json" not in names or "manifest.sha256" not in names:
            raise ValueError("manifest members are missing")
        manifest_bytes = tar.extractfile("manifest.json").read()
        checksum = tar.extractfile("manifest.sha256").read().decode().strip()
        if checksum != f"{hashlib.sha256(manifest_bytes).hexdigest()}  manifest.json":
            raise ValueError("manifest checksum mismatch")
        manifest = json.loads(manifest_bytes)
        if manifest.get("schema") != SCHEMA or not isinstance(manifest.get("files"), dict):
            raise ValueError("manifest schema is not accepted")
        expected = {f"state/{name}" for name in manifest["files"]} | {"manifest.json", "manifest.sha256"}
        if set(names) != expected:
            raise ValueError("archive contents do not exactly match manifest")
        data = {name.removeprefix("state/"): tar.extractfile(f"state/{name}").read() for name in manifest["files"]}
    for name, detail in manifest["files"].items():
        if hashlib.sha256(data[name]).hexdigest() != detail.get("sha256") or len(data[name]) != detail.get("bytes"):
            raise ValueError(f"content mismatch for {name}")
    return manifest, data


def _expected(manifest: dict, *, pds_revision: str | None, pds_version: str | None,
              pds_image: str | None, app_revision: str | None, config_sha256: str | None) -> None:
    checks = (("pds source revision", manifest["pds"]["source_revision"], pds_revision),
              ("pds version", manifest["pds"]["version"], pds_version),
              ("pds image", manifest["pds"]["image"], pds_image),
              ("application revision", manifest["application"]["source_revision"], app_revision),
              ("public configuration", manifest["files"]["config/public.json"]["sha256"], config_sha256))
    for label, actual, expected in checks:
        if expected is not None and actual != expected:
            raise ValueError(f"expected {label} does not match backup")


def inspect(archive: Path, *, pds_revision: str | None = None, pds_version: str | None = None,
            pds_image: str | None = None, app_revision: str | None = None,
            config_sha256: str | None = None) -> dict:
    manifest, _ = _read_archive(archive)
    _expected(manifest, pds_revision=pds_revision, pds_version=pds_version,
              pds_image=pds_image, app_revision=app_revision, config_sha256=config_sha256)
    return {"result": "inspected", "run_id": manifest["run_id"], "files": len(manifest["files"])}


def restore(archive: Path, destination: Path, *, max_age_seconds: int, now: int | None = None,
            key_attestation: Path | None = None, pds_revision: str | None = None,
            pds_version: str | None = None, pds_image: str | None = None,
            app_revision: str | None = None, config_sha256: str | None = None) -> dict:
    destination = _canonical_existing(destination, "blank-host destination")
    if any(destination.iterdir()):
        raise ValueError("destination is non-empty; blank-host restore refuses replacement")
    manifest, data = _read_archive(archive)
    _expected(manifest, pds_revision=pds_revision, pds_version=pds_version,
              pds_image=pds_image, app_revision=app_revision, config_sha256=config_sha256)
    instant = int(time.time() if now is None else now)
    if not isinstance(max_age_seconds, int) or max_age_seconds < 0 or instant - manifest["captured_at"] > max_age_seconds:
        raise ValueError("backup is stale")
    if key_attestation is None or not key_attestation.is_absolute() or not key_attestation.is_file():
        raise ValueError("external key attestation is required and is never taken from the archive")
    source_key = data.get("keys/attestation.json")
    if source_key is None or key_attestation.read_bytes() != source_key:
        raise ValueError("external key attestation does not match backup")
    lock = destination / ".phlogiston-h0-restore-incomplete.json"
    lock.write_text(json.dumps({"schema": "phlogiston.h0-restore-lock.v1", "run_id": manifest["run_id"]}) + "\n")
    try:
        for name, content in data.items():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.parent.chmod(0o700)
            target.write_bytes(content)
            target.chmod(int(manifest["files"][name]["mode"]))
            stat = target.stat()
            if stat.st_uid != manifest["files"][name].get("uid") or stat.st_gid != manifest["files"][name].get("gid"):
                raise ValueError("restored owner policy does not match manifest")
        restored = {name: _sha256_file(destination / name) for name in manifest["files"]}
        if any(restored[name] != manifest["files"][name]["sha256"] for name in restored):
            raise ValueError("restored correspondence check failed")
        lock.unlink()
    except Exception:
        # The lock intentionally remains: this destination can never look healthy.
        raise
    return {"result": "restored", "run_id": manifest["run_id"], "identities": manifest["identities"], "files": len(data)}


def rebuild_index(destination: Path) -> dict:
    destination = _canonical_existing(destination, "restored destination")
    marker = destination / ".phlogiston-h0-restore-incomplete.json"
    if marker.exists():
        raise ValueError("incomplete restore cannot rebuild index")
    state = _canonical_json(destination / "app/application-state.json", "restored application state")
    policy = _canonical_json(destination / "app/policy.json", "restored application policy")
    output = destination / "app/reconstructible-index.json"
    if output.exists():
        raise ValueError("reconstructible index already exists")
    value = {"schema": "phlogiston.reconstructible-index.v1", "identities": state["synthetic_identities"],
             "policy_sha256": _sha256_file(destination / "app/policy.json")}
    output.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    output.chmod(0o600)
    return {"result": "rebuilt", "index_sha256": _sha256_file(output)}


def reconcile_restored(archive: Path, destination: Path) -> dict:
    manifest, _ = _read_archive(archive)
    destination = _canonical_existing(destination, "restored destination")
    if (destination / ".phlogiston-h0-restore-incomplete.json").exists():
        raise ValueError("restore remains incomplete")
    allowed = set(manifest["files"]) | {"app/reconstructible-index.json"}
    found = {path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file()}
    if not found <= allowed:
        raise ValueError("restored destination has undeclared state")
    for name, detail in manifest["files"].items():
        path = destination / name
        if not path.is_file() or _sha256_file(path) != detail["sha256"]:
            raise ValueError("restored content does not match manifest")
        stat = path.stat()
        if (stat.st_mode & 0o777, stat.st_uid, stat.st_gid) != (detail["mode"], detail["uid"], detail["gid"]):
            raise ValueError("restored metadata does not match manifest")
    return {"result": "reconciled", "run_id": manifest["run_id"], "files": len(manifest["files"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    command = parser.add_subparsers(dest="command", required=True)
    backup = command.add_parser("capture")
    backup.add_argument("--source", type=Path, required=True); backup.add_argument("--archive", type=Path, required=True)
    backup.add_argument("--run-id", required=True); backup.add_argument("--pds-revision", required=True)
    backup.add_argument("--pds-version", required=True); backup.add_argument("--pds-image", required=True)
    backup.add_argument("--app-revision", required=True); backup.add_argument("--quiescence-attestation", type=Path, required=True)
    restore_cmd = command.add_parser("restore")
    restore_cmd.add_argument("--archive", type=Path, required=True); restore_cmd.add_argument("--destination", type=Path, required=True)
    restore_cmd.add_argument("--max-age-seconds", type=int, required=True); restore_cmd.add_argument("--key-attestation", type=Path, required=True)
    inspect_cmd = command.add_parser("inspect")
    inspect_cmd.add_argument("--archive", type=Path, required=True)
    rebuild_cmd = command.add_parser("rebuild-index")
    rebuild_cmd.add_argument("--destination", type=Path, required=True)
    for sub in (restore_cmd, inspect_cmd):
        sub.add_argument("--expected-pds-revision")
        sub.add_argument("--expected-pds-version")
        sub.add_argument("--expected-pds-image")
        sub.add_argument("--expected-app-revision")
        sub.add_argument("--expected-config-sha256")
    args = parser.parse_args()
    try:
        if args.command == "capture":
            result = capture(args.source, args.archive, run_id=args.run_id, pds_revision=args.pds_revision,
                pds_version=args.pds_version, pds_image=args.pds_image, app_revision=args.app_revision,
                attestation=args.quiescence_attestation)
        elif args.command == "restore":
            result = restore(args.archive, args.destination, max_age_seconds=args.max_age_seconds,
                key_attestation=args.key_attestation, pds_revision=args.expected_pds_revision,
                pds_version=args.expected_pds_version, pds_image=args.expected_pds_image,
                app_revision=args.expected_app_revision, config_sha256=args.expected_config_sha256)
        elif args.command == "inspect":
            result = inspect(args.archive, pds_revision=args.expected_pds_revision,
                pds_version=args.expected_pds_version, pds_image=args.expected_pds_image,
                app_revision=args.expected_app_revision, config_sha256=args.expected_config_sha256)
        else:
            result = rebuild_index(args.destination)
    except (OSError, ValueError, json.JSONDecodeError, tarfile.TarError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
