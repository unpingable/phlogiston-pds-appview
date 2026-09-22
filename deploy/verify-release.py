"""Verify an extracted Phlogiston release without executing it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def verify(root: Path, phlogiston_commit: str, community_commit: str) -> dict[str, object]:
    root = root.resolve(strict=True)
    manifest_path = root / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != "phlogiston.release-manifest.v1":
        raise ValueError("release manifest schema mismatch")
    if manifest.get("phlogiston_commit") != phlogiston_commit:
        raise ValueError("Phlogiston source identity mismatch")
    if manifest.get("community_commit") != community_commit:
        raise ValueError("community source identity mismatch")
    declared = manifest.get("files")
    if not isinstance(declared, dict):
        raise ValueError("release manifest files must be an object")
    actual: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            target = path.resolve(strict=True)
            if not target.is_relative_to(root):
                raise ValueError(f"release symlink escapes root: {relative}")
        elif path.is_file() and path != manifest_path:
            actual.add(relative)
    if actual != set(declared):
        raise ValueError("release file inventory mismatch")
    for relative, expected in declared.items():
        path = root / relative
        if path.stat().st_size != expected.get("bytes") or digest(path) != expected.get("sha256"):
            raise ValueError(f"release file identity mismatch: {relative}")
    return {
        "schema": manifest["schema"],
        "phlogiston_commit": phlogiston_commit,
        "community_commit": community_commit,
        "files_verified": len(actual),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phlogiston-commit", required=True)
    parser.add_argument("--community-commit", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.phlogiston_commit, args.community_commit), sort_keys=True))


if __name__ == "__main__":
    main()
