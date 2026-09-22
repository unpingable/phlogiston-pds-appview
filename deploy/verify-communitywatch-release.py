"""Verify a communitywatch release directory before installation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def verify(root: Path, community_commit: str) -> dict[str, object]:
    root = root.resolve(strict=True)
    manifest_path = root / "communitywatch-release-manifest.json"
    value = json.loads(manifest_path.read_text())
    if value.get("schema") != "phlogiston.communitywatch-release-manifest.v1" or value.get("community_commit") != community_commit:
        raise ValueError("communitywatch release identity mismatch")
    expected_packages = [
        "community-model==0.1.0",
        "community-space-model==0.1.0",
        "community-space-wire==0.1.0",
        "communityd==0.1.0",
        "communitywatch==0.1.0",
        "communitywatch-web==0.1.0",
    ]
    if value.get("packages") != expected_packages:
        raise ValueError("communitywatch release package inventory mismatch")
    files = value.get("files")
    if not isinstance(files, dict):
        raise ValueError("communitywatch release inventory is invalid")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path and not path.is_symlink()
    }
    if actual != set(files):
        raise ValueError("communitywatch release file inventory mismatch")
    for name, expected in files.items():
        path = root / name
        if path.stat().st_size != expected.get("bytes") or sha256(path) != expected.get("sha256"):
            raise ValueError(f"communitywatch release file mismatch: {name}")
    return {"result": "verified", "community_commit": community_commit, "files": len(actual)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--community-commit", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.community_commit), sort_keys=True))


if __name__ == "__main__":
    main()
