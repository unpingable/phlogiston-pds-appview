"""Exact current community release inventory and existing offline-tree checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

PACKAGES = [
    "community-model", "community-space-model", "community-space-wire", "communityd",
    "communitywatch", "communitywatch-web", "community-policy", "community-notify",
]
SCHEMA = "phlogiston.communitywatch-release-manifest.v2"


def strict_json(path: Path) -> object:
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=pairs)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path, excluded: set[str] | None = None) -> dict[str, dict[str, object]]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("release root must be an exact directory")
    result = {}
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f"release contains non-regular entry: {path}")
        name = path.relative_to(root).as_posix()
        if name not in (excluded or set()):
            result[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return result


def verify_offline_tree(root: Path, manifest: Path, digest: str) -> None:
    # The existing atproto.offline-tree.v1 contract: exact keys, sorted canonical
    # regular files, no symlinks, exact bytes and hashes, no undeclared content.
    if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size > 4 * 1024**2:
        raise ValueError("offline manifest must be a bounded regular file")
    if sha256(manifest) != digest:
        raise ValueError("offline manifest digest mismatch")
    value = strict_json(manifest)
    if not isinstance(value, dict):
        raise ValueError("offline manifest must be an object")
    if set(value) != {"schema", "kind", "files"} or value["schema"] != "atproto.offline-tree.v1" or value["kind"] != "pnpm-store":
        raise ValueError("offline manifest identity mismatch")
    declared = {}
    if not isinstance(value["files"], list) or not value["files"]:
        raise ValueError("offline manifest files must be nonempty")
    for row in value["files"]:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise ValueError("offline manifest row mismatch")
        name = row["path"]
        if not isinstance(name, str) or not name or str(PurePosixPath(name)) != name or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or name in declared:
            raise ValueError("offline manifest pathname mismatch")
        if type(row["bytes"]) is not int or row["bytes"] < 0 or not isinstance(row["sha256"], str) or len(row["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["sha256"]):
            raise ValueError("offline manifest file identity mismatch")
        declared[name] = {"bytes": row["bytes"], "sha256": row["sha256"]}
    if list(declared) != sorted(declared) or inventory(root) != declared:
        raise ValueError("offline tree does not exactly match closed manifest")
