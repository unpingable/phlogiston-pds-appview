"""Exact two-member archive/restore boundary for synthetic rendered output."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import tarfile

from .receipt import verify_receipt
from .render import RUN_ID, canonical_existing_directory


def _archive_path(path: Path) -> Path:
    if not path.is_absolute() or path.is_symlink() or path.exists():
        raise ValueError("archive path must be a new absolute non-symlink path")
    canonical_existing_directory(path.parent, "archive parent")
    return path


def backup(output: Path, receipt: Path, snapshot: Path, renderer: Path, archive: Path) -> None:
    manifest = verify_receipt(output, receipt, snapshot, renderer)
    archive = _archive_path(archive)
    with tarfile.open(archive, "x") as tar:
        for source, name in ((output / "index.html", "index.html"), (receipt, "receipt.json")):
            info = tar.gettarinfo(str(source), arcname=name)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            with source.open("rb") as handle:
                tar.addfile(info, handle)
    # Re-open and verify the exact bytes that left the source host.
    with tarfile.open(archive, "r") as tar:
        names = [member.name for member in tar.getmembers()]
        if names != ["index.html", "receipt.json"]:
            raise ValueError("archive member list is not exact")
        archived = json.loads(tar.extractfile("receipt.json").read())
        if archived != manifest:
            raise ValueError("archive receipt does not equal verified receipt")


def restore(archive: Path, target_root: Path, run_id: str, snapshot: Path, renderer: Path) -> tuple[Path, Path]:
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("invalid run id")
    if not archive.is_absolute() or archive.is_symlink() or not archive.is_file():
        raise ValueError("archive must be an absolute regular non-symlink file")
    target_root = canonical_existing_directory(target_root, "restore target root")
    output = target_root / run_id
    receipt = target_root / f"{run_id}.receipt.json"
    if output.exists() or output.is_symlink() or receipt.exists() or receipt.is_symlink():
        raise ValueError("restore destination already exists")
    with tarfile.open(archive, "r") as tar:
        members = tar.getmembers()
        if [member.name for member in members] != ["index.html", "receipt.json"] or not all(member.isfile() for member in members):
            raise ValueError("archive must contain exactly regular index.html and receipt.json members")
        page = tar.extractfile("index.html").read()
        receipt_bytes = tar.extractfile("receipt.json").read()
    output.mkdir(mode=0o700)
    (output / "index.html").write_bytes(page)
    receipt.write_bytes(receipt_bytes)
    receipt.chmod(0o600)
    verify_receipt(output, receipt, snapshot, renderer)
    return output, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    command = parser.add_subparsers(dest="command", required=True)
    for name in ("backup", "restore"):
        sub = command.add_parser(name)
        sub.add_argument("--archive", type=Path, required=True)
        sub.add_argument("--snapshot", type=Path, required=True)
        sub.add_argument("--renderer", type=Path, required=True)
        if name == "backup":
            sub.add_argument("--output", type=Path, required=True)
            sub.add_argument("--receipt", type=Path, required=True)
        else:
            sub.add_argument("--target-root", type=Path, required=True)
            sub.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        if args.command == "backup":
            backup(args.output, args.receipt, args.snapshot, args.renderer, args.archive)
            result = {"archive": str(args.archive), "result": "backed-up"}
        else:
            output, receipt = restore(args.archive, args.target_root, args.run_id, args.snapshot, args.renderer)
            result = {"output": str(output), "receipt": str(receipt), "result": "restored"}
    except (OSError, ValueError, json.JSONDecodeError, tarfile.TarError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
