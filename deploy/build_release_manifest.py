"""Create the deterministic manifest embedded in a Phlogiston release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phlogiston-commit", required=True)
    parser.add_argument("--community-commit", required=True)
    parser.add_argument("--store-manifest-sha256", required=True)
    parser.add_argument("--oauth-tarball-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.root.is_absolute() or not args.root.is_dir() or args.output.exists():
        raise SystemExit("release root must exist and output must be new")
    for value in (args.phlogiston_commit, args.community_commit, args.store_manifest_sha256, args.oauth_tarball_sha256):
        if len(value) != 40 and len(value) != 64:
            raise SystemExit("invalid source or digest identity")
        int(value, 16)
    files = {}
    for path in sorted(args.root.rglob("*")):
        if path == args.output or path.is_dir() or path.is_symlink():
            continue
        relative = path.relative_to(args.root).as_posix()
        files[relative] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    value = {
        "schema": "phlogiston.release-manifest.v1",
        "phlogiston_commit": args.phlogiston_commit,
        "community_commit": args.community_commit,
        "oauth_package": {
            "name": "@atproto/oauth-client-node",
            "version": "0.0.0-spaces-alpha-20260818163953",
            "tarball_sha256": args.oauth_tarball_sha256,
            "lockfile_sri": "sha512-XEJS6GMk5mG136FVcoSzzFynnMKGsJ3J2Z0oVWotwkYdCyawN1UCoxtKalMqzFRSsk6uWyiNKig1OK+XwC+weQ==",
        },
        "dependency_store_manifest_sha256": args.store_manifest_sha256,
        "pds_image": "ghcr.io/bluesky-social/pds@sha256:d155af1c906d7848e7dea9d59a8a7def065a04b77aa98ae56ea05a8d4eadb63a",
        "files": files,
    }
    args.output.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
