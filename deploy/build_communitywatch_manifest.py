"""Build the deterministic communitywatch deployment manifest."""

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--community-commit", required=True)
    parser.add_argument("--python-version", required=True)
    parser.add_argument("--setuptools-sha256", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.root.is_absolute() or args.output.exists() or len(args.community_commit) != 40:
        raise SystemExit("invalid communitywatch release input")
    int(args.community_commit, 16)
    files = {
        path.relative_to(args.root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(args.root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }
    value = {
        "schema": "phlogiston.communitywatch-release-manifest.v1",
        "community_commit": args.community_commit,
        "python_build_version": args.python_version,
        "python_runtime_contract": ">=3.12,<3.13",
        "build_tools": {
            "setuptools-80.9.0-py3-none-any.whl": args.setuptools_sha256,
            "wheel-0.45.1-py3-none-any.whl": args.wheel_sha256,
        },
        "packages": [
            "community-model==0.1.0",
            "community-space-model==0.1.0",
            "community-space-wire==0.1.0",
            "communityd==0.1.0",
            "communitywatch==0.1.0",
            "communitywatch-web==0.1.0",
        ],
        "files": files,
    }
    args.output.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
