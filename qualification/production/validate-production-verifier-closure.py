#!/usr/bin/env python3
"""Validate one exact, regular-file-only production-verifier closure."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat

SCHEMA = "phlogiston.production-verifier-closure.v1"


def refuse(message: str) -> None:
    raise ValueError(message)


def manifest_entries(value: object) -> list[tuple[str, str]]:
    if type(value) is not dict or set(value) != {"schema", "files"} or value["schema"] != SCHEMA or type(value["files"]) is not list:
        refuse("manifest fields are not exact")
    entries: list[tuple[str, str]] = []
    for entry in value["files"]:
        if type(entry) is not dict or set(entry) != {"path", "sha256"}:
            refuse("manifest member fields are not exact")
        path, digest = entry["path"], entry["sha256"]
        if type(path) is not str or not path or path.startswith("/") or "\\" in path or Path(path).as_posix() != path or any(part in {"", ".", ".."} for part in path.split("/")):
            refuse("manifest path is invalid")
        if type(digest) is not str or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            refuse("manifest digest is invalid")
        entries.append((path, digest))
    if not entries or entries != sorted(entries) or len({path for path, _ in entries}) != len(entries):
        refuse("manifest paths must be nonempty, sorted, and unique")
    return entries


def regular_files(root: Path) -> list[str]:
    files: list[str] = []
    for candidate in sorted(root.rglob("*")):
        relative = candidate.relative_to(root).as_posix()
        mode = candidate.lstat().st_mode
        if stat.S_ISLNK(mode):
            refuse(f"symlink refused: {relative}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            refuse(f"non-regular file refused: {relative}")
        files.append(relative)
    return files


def validate(root: Path, manifest: Path) -> None:
    if root.is_symlink() or not root.is_dir() or manifest.is_symlink() or not manifest.is_file():
        refuse("root and manifest must be real directories/files")
    entries = manifest_entries(json.loads(manifest.read_text(encoding="utf-8")))
    listed = [path for path, _ in entries]
    if listed != regular_files(root):
        refuse("manifest paths do not close the production verifier tree")
    for relative, expected in entries:
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != expected:
            refuse(f"digest mismatch: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    validate(args.root.resolve(strict=True), args.manifest.resolve(strict=True))
    print("production verifier closure: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"refused: {type(error).__name__}: {error}", file=__import__("sys").stderr)
        raise SystemExit(1)
