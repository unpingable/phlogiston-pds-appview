"""Stopped-state capture and blank-host restore for the integrated community slice."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tarfile
import time
from typing import Iterator


SCHEMA = "phlogiston.community-recovery-manifest.v1"
ATTESTATION_SCHEMA = "phlogiston.community-recovery-quiescence.v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _directory(path: Path, label: str, *, empty: bool = False) -> Path:
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ValueError(f"{label} must be an absolute existing non-symlink directory")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise ValueError(f"{label} must already be canonical")
    if empty and any(path.iterdir()):
        raise ValueError(f"{label} must be empty")
    return path


def _file(path: Path, label: str) -> Path:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be an absolute regular non-symlink file")
    return path.resolve(strict=True)


def _walk(root: Path, prefix: str) -> Iterator[tuple[str, Path]]:
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink is not admitted: {path}")
        if path.is_file():
            yield f"{prefix}/{path.relative_to(root).as_posix()}", path
        elif not path.is_dir():
            raise ValueError(f"non-regular state member is not admitted: {path}")


def _json(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(_file(path, label).read_bytes())
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} is not JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def attest(
    output: Path,
    *,
    community_pds: Path,
    participant_pds: Path,
    authority_journal: Path,
    runtime: str,
    observed_at: int | None = None,
) -> dict[str, object]:
    community_pds = _directory(community_pds, "community PDS")
    participant_pds = _directory(participant_pds, "participant PDS")
    authority_journal = _file(authority_journal, "authority journal")
    if not output.is_absolute() or output.exists() or output.is_symlink():
        raise ValueError("attestation output must be a new absolute path")
    _directory(output.parent, "attestation parent")
    value: dict[str, object] = {
        "schema": ATTESTATION_SCHEMA,
        "community_pds": str(community_pds),
        "participant_pds": str(participant_pds),
        "authority_journal": str(authority_journal),
        "writer_pids": [],
        "runtime": runtime,
        "observed_at": int(time.time() if observed_at is None else observed_at),
    }
    output.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    output.chmod(0o600)
    return value


def checkpoint(database: Path) -> dict[str, object]:
    """Checkpoint a stopped SQLite writer and prove no WAL work remains."""
    database = _file(database, "SQLite database")
    connection = sqlite3.connect(f"file:{database}?mode=rw", uri=True, timeout=5)
    try:
        row = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    finally:
        connection.close()
    if row is None or len(row) != 3 or row[0] != 0 or row[1] != row[2]:
        raise RuntimeError("SQLite checkpoint was busy or incomplete")
    sidecars = [str(database) + suffix for suffix in ("-wal", "-shm") if Path(str(database) + suffix).exists()]
    if sidecars:
        raise RuntimeError("SQLite sidecars remain after checkpoint")
    return {"result": "checkpointed", "database": str(database), "busy": row[0], "log_frames": row[1], "checkpointed_frames": row[2]}


def capture(
    archive: Path,
    *,
    community_pds: Path,
    participant_pds: Path,
    authority_journal: Path,
    public_config: Path,
    quiescence: Path,
    source: dict[str, str],
    captured_at: int | None = None,
) -> dict[str, object]:
    community_pds = _directory(community_pds, "community PDS")
    participant_pds = _directory(participant_pds, "participant PDS")
    authority_journal = _file(authority_journal, "authority journal")
    public_config = _file(public_config, "public configuration")
    attestation = _json(quiescence, "quiescence attestation")
    expected = {
        "schema": ATTESTATION_SCHEMA,
        "community_pds": str(community_pds),
        "participant_pds": str(participant_pds),
        "authority_journal": str(authority_journal),
        "writer_pids": [],
        "runtime": attestation.get("runtime"),
        "observed_at": attestation.get("observed_at"),
    }
    if attestation != expected or not isinstance(expected["runtime"], str) or not isinstance(expected["observed_at"], int):
        raise ValueError("quiescence attestation does not exactly bind stopped writers")
    for root in (community_pds, participant_pds):
        if not (root / "account.sqlite").is_file() or not (root / "actors").is_dir():
            raise ValueError("PDS state is incomplete")
        sidecars = [path for path in root.rglob("*") if path.name.endswith(("-wal", "-shm"))]
        if sidecars:
            raise ValueError("PDS SQLite sidecars remain after stopped checkpoint")
    for suffix in ("-wal", "-shm"):
        if Path(str(authority_journal) + suffix).exists():
            raise ValueError("authority journal sidecars remain after writer shutdown")
    if not archive.is_absolute() or archive.exists() or archive.is_symlink():
        raise ValueError("archive must be a new absolute path")
    _directory(archive.parent, "archive parent")
    if set(source) != {"phlogiston", "community", "pds_image"} or not all(source.values()):
        raise ValueError("source identity must bind Phlogiston, community, and PDS image")

    members = list(_walk(community_pds, "pds/community"))
    members += list(_walk(participant_pds, "pds/participant"))
    members += [("communityd/authority.sqlite3", authority_journal), ("config/public.json", public_config)]
    names = [name for name, _ in members]
    if len(names) != len(set(names)):
        raise ValueError("duplicate backup member")
    files = {
        name: {
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "mode": path.stat().st_mode & 0o777,
        }
        for name, path in sorted(members)
    }
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "captured_at": int(time.time() if captured_at is None else captured_at),
        "source": source,
        "files": files,
        "state_model": {
            "authoritative": ["pds/community", "pds/participant"],
            "custody": ["communityd/authority.sqlite3"],
            "configuration": ["config/public.json"],
            "reconstructible": ["communitywatch observer/projection database"],
            "reenrollable_excluded": ["OAuth state", "Phlogiston web sessions"],
        },
        "quiescence": attestation,
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    with tarfile.open(archive, "x") as tar:
        for name, path in sorted(members):
            info = tar.gettarinfo(str(path), arcname=f"state/{name}")
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with path.open("rb") as handle:
                tar.addfile(info, handle)
        for name, content in (
            ("manifest.json", manifest_bytes),
            ("manifest.sha256", hashlib.sha256(manifest_bytes).hexdigest().encode() + b"  manifest.json\n"),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o600
            tar.addfile(info, io.BytesIO(content))
    archive.chmod(0o600)
    return manifest


def _read(archive: Path) -> tuple[dict[str, object], dict[str, bytes]]:
    archive = _file(archive, "archive")
    with tarfile.open(archive, "r") as tar:
        members = tar.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(not member.isfile() or member.name.startswith("/") or ".." in Path(member.name).parts for member in members):
            raise ValueError("archive contains an unsafe member")
        if "manifest.json" not in names or "manifest.sha256" not in names:
            raise ValueError("archive manifest is incomplete")
        manifest_bytes = tar.extractfile("manifest.json").read()  # type: ignore[union-attr]
        checksum = tar.extractfile("manifest.sha256").read().decode().strip()  # type: ignore[union-attr]
        if checksum != f"{hashlib.sha256(manifest_bytes).hexdigest()}  manifest.json":
            raise ValueError("manifest checksum mismatch")
        manifest = json.loads(manifest_bytes)
        if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA or not isinstance(manifest.get("files"), dict):
            raise ValueError("manifest schema is unsupported")
        files = manifest["files"]
        expected = {f"state/{name}" for name in files} | {"manifest.json", "manifest.sha256"}
        if set(names) != expected:
            raise ValueError("archive does not exactly match its manifest")
        data = {name: tar.extractfile(f"state/{name}").read() for name in files}  # type: ignore[union-attr]
    for name, detail in files.items():
        if not isinstance(detail, dict) or hashlib.sha256(data[name]).hexdigest() != detail.get("sha256") or len(data[name]) != detail.get("bytes"):
            raise ValueError(f"archive content mismatch for {name}")
    return manifest, data


def inspect(archive: Path) -> dict[str, object]:
    manifest, data = _read(archive)
    return {"result": "inspected", "files": len(data), "source": manifest["source"]}


def restore(archive: Path, destination: Path, *, fail_after: int | None = None) -> dict[str, object]:
    destination = _directory(destination, "blank destination", empty=True)
    manifest, data = _read(archive)
    lock = destination / ".phlogiston-community-restore-incomplete.json"
    lock.write_text(json.dumps({"schema": "phlogiston.community-restore-lock.v1", "source": manifest["source"]}, sort_keys=True) + "\n")
    lock.chmod(0o600)
    try:
        for index, (name, content) in enumerate(sorted(data.items()), start=1):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            target.write_bytes(content)
            detail = manifest["files"][name]  # type: ignore[index]
            target.chmod(int(detail["mode"]))
            if fail_after is not None and index >= fail_after:
                raise RuntimeError("injected interrupted restore")
        for name, detail in manifest["files"].items():  # type: ignore[union-attr]
            if _sha256(destination / name) != detail["sha256"]:
                raise ValueError("restored file does not match manifest")
        lock.unlink()
    except Exception:
        raise
    return {"result": "restored", "files": len(data), "source": manifest["source"]}


def reconcile(archive: Path, destination: Path) -> dict[str, object]:
    destination = _directory(destination, "restored destination")
    if (destination / ".phlogiston-community-restore-incomplete.json").exists():
        raise ValueError("restore is incomplete")
    manifest, _ = _read(archive)
    expected = set(manifest["files"])  # type: ignore[arg-type]
    found = {path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file()}
    if found != expected:
        raise ValueError("restored file inventory differs from manifest")
    for name, detail in manifest["files"].items():  # type: ignore[union-attr]
        if _sha256(destination / name) != detail["sha256"]:
            raise ValueError("restored file content differs from manifest")
    return {"result": "reconciled", "files": len(expected), "source": manifest["source"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    att = commands.add_parser("attest")
    att.add_argument("--output", type=Path, required=True)
    att.add_argument("--community-pds", type=Path, required=True)
    att.add_argument("--participant-pds", type=Path, required=True)
    att.add_argument("--authority-journal", type=Path, required=True)
    att.add_argument("--runtime", required=True)
    cap = commands.add_parser("capture")
    cap.add_argument("--archive", type=Path, required=True)
    cap.add_argument("--community-pds", type=Path, required=True)
    cap.add_argument("--participant-pds", type=Path, required=True)
    cap.add_argument("--authority-journal", type=Path, required=True)
    cap.add_argument("--public-config", type=Path, required=True)
    cap.add_argument("--quiescence", type=Path, required=True)
    cap.add_argument("--phlogiston-source", required=True)
    cap.add_argument("--community-source", required=True)
    cap.add_argument("--pds-image", required=True)
    restore_cmd = commands.add_parser("restore")
    restore_cmd.add_argument("--archive", type=Path, required=True)
    restore_cmd.add_argument("--destination", type=Path, required=True)
    inspect_cmd = commands.add_parser("inspect")
    inspect_cmd.add_argument("--archive", type=Path, required=True)
    reconcile_cmd = commands.add_parser("reconcile")
    reconcile_cmd.add_argument("--archive", type=Path, required=True)
    reconcile_cmd.add_argument("--destination", type=Path, required=True)
    checkpoint_cmd = commands.add_parser("checkpoint")
    checkpoint_cmd.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "attest":
            result = attest(args.output, community_pds=args.community_pds, participant_pds=args.participant_pds, authority_journal=args.authority_journal, runtime=args.runtime)
        elif args.command == "capture":
            result = capture(args.archive, community_pds=args.community_pds, participant_pds=args.participant_pds, authority_journal=args.authority_journal, public_config=args.public_config, quiescence=args.quiescence, source={"phlogiston": args.phlogiston_source, "community": args.community_source, "pds_image": args.pds_image})
        elif args.command == "restore":
            result = restore(args.archive, args.destination)
        elif args.command == "inspect":
            result = inspect(args.archive)
        elif args.command == "reconcile":
            result = reconcile(args.archive, args.destination)
        else:
            result = checkpoint(args.database)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, tarfile.TarError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
