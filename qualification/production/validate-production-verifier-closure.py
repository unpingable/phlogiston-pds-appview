#!/usr/bin/env python3
"""Validate one exact, regular-file-only production-verifier closure."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

SCHEMA = "phlogiston.production-verifier-closure.v1"
MAX_FILE_BYTES = 1 << 20


def refuse(message: str) -> None:
    raise ValueError(message)


def snapshot(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def stable_regular_read(path: Path, label: str) -> bytes:
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        refuse(f"{label} must be a real regular file")
    if before.st_size > MAX_FILE_BYTES:
        refuse(f"{label} exceeds the bounded read limit")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if snapshot(opened) != snapshot(before):
            refuse(f"{label} pathname changed before open")
        data = bytearray()
        while len(data) <= MAX_FILE_BYTES:
            block = os.read(fd, min(65536, MAX_FILE_BYTES + 1 - len(data)))
            if not block:
                break
            data.extend(block)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    if len(data) > MAX_FILE_BYTES or snapshot(after) != snapshot(before) or snapshot(path.lstat()) != snapshot(before):
        refuse(f"{label} changed during bounded read")
    return bytes(data)


def no_duplicate_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            refuse(f"duplicate JSON key: {key}")
        result[key] = value
    return result


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
    root_stat = root.lstat()
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        refuse("root must be a real directory")
    entries = manifest_entries(json.loads(stable_regular_read(manifest, "manifest").decode("utf-8"), object_pairs_hook=no_duplicate_object))
    listed = [path for path, _ in entries]
    if listed != regular_files(root):
        refuse("manifest paths do not close the production verifier tree")
    for relative, expected in entries:
        if hashlib.sha256(stable_regular_read(root / relative, relative)).hexdigest() != expected:
            refuse(f"digest mismatch: {relative}")
    if snapshot(root.lstat()) != snapshot(root_stat):
        refuse("root pathname changed during validation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    validate(args.root, args.manifest)
    print("production verifier closure: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"refused: {type(error).__name__}: {error}", file=__import__("sys").stderr)
        raise SystemExit(1)
