"""Create only the bounded, synthetic Phlogiston state beside a stopped PDS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import time

from .h0_recovery import _canonical_existing


def write_json(path: Path, value: dict, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    path.chmod(mode)


def prepare(root: Path, did: str) -> None:
    root = _canonical_existing(root, "isolated state root")
    if not did.startswith("did:"):
        raise ValueError("only a synthetic DID-related identifier is accepted")
    write_json(root / "app/application-state.json", {
        "schema": "phlogiston.application-state.v1", "synthetic_identities": [did],
        "preferences": {"surface": "offline-static", "network": "none"},
    })
    write_json(root / "app/policy.json", {
        "schema": "phlogiston.local-policy.v1", "acl": {"mode": "preview-only"},
        "quench": {"mode": "refuse-without-root"},
    })
    write_json(root / "config/public.json", {
        "schema": "phlogiston.pds-qualification-config.v1", "network": "internal-only",
        "delegated": ["relay", "appview", "feed-generator", "search", "moderation"],
    }, 0o644)
    write_json(root / "config/secret-references.json", {
        "schema": "phlogiston.secret-reference-inventory.v1",
        "references": ["isolated-key-custodian/v1"],
    })
    write_json(root / "keys/attestation.json", {
        "schema": "phlogiston.key-attestation.v1",
        "fingerprints": ["synthetic-isolated-key-set"],
    })


def attest_stopped(root: Path, runtime: str, observed_at: int | None = None) -> None:
    root = _canonical_existing(root, "isolated state root")
    write_json(root / "quiescence.json", {
        "schema": "phlogiston.h0-quiescence.v1", "source_root": str(root),
        "writer_pids": [], "runtime": runtime,
        "observed_at": int(time.time() if observed_at is None else observed_at),
    })


def stage_key_attestation(source: Path, destination: Path) -> None:
    if not source.is_absolute() or source.is_symlink() or not source.is_file():
        raise ValueError("source key attestation must be an absolute regular file")
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise ValueError("destination key attestation must be a new absolute path")
    _canonical_existing(destination.parent, "external key-attestation parent")
    shutil.copyfile(source, destination)
    destination.chmod(0o600)


def harden_stopped_pds(root: Path) -> None:
    root = _canonical_existing(root, "isolated state root")
    pds = root / "pds"
    if pds.is_symlink() or not pds.is_dir():
        raise ValueError("isolated PDS state directory is required")
    for path in sorted(pds.rglob("*")):
        if path.is_symlink():
            raise ValueError("PDS state cannot contain symlinks")
        if path.is_dir():
            path.chmod(0o700)
        elif path.is_file():
            path.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser()
    command = parser.add_subparsers(dest="command", required=True)
    prepare_cmd = command.add_parser("prepare")
    prepare_cmd.add_argument("--root", type=Path, required=True)
    prepare_cmd.add_argument("--did", required=True)
    attest_cmd = command.add_parser("attest-stopped")
    attest_cmd.add_argument("--root", type=Path, required=True)
    attest_cmd.add_argument("--runtime", required=True)
    stage_cmd = command.add_parser("stage-key-attestation")
    stage_cmd.add_argument("--source", type=Path, required=True)
    stage_cmd.add_argument("--destination", type=Path, required=True)
    harden_cmd = command.add_parser("harden-stopped-pds")
    harden_cmd.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.root, args.did)
        elif args.command == "attest-stopped":
            attest_stopped(args.root, args.runtime)
        elif args.command == "harden-stopped-pds":
            harden_stopped_pds(args.root)
        else:
            stage_key_attestation(args.source, args.destination)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
