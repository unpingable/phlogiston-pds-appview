"""Build the deterministic current community deployment manifest."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from community_release import PACKAGES, SCHEMA, inventory, sha256, verify_offline_tree


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--community-commit", required=True)
    parser.add_argument("--builder-commit", required=True)
    parser.add_argument("--python-version", required=True)
    parser.add_argument("--node-version", required=True)
    parser.add_argument("--pnpm-version", required=True)
    parser.add_argument("--setuptools-sha256", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.root.is_absolute() or args.output.exists():
        raise SystemExit("invalid community release input")
    for commit in (args.community_commit, args.builder_commit):
        if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
            raise SystemExit("invalid source revision")
    store_manifest = args.root / "pnpm-store-manifest.json"
    verify_offline_tree(args.root / "pnpm-store", store_manifest, sha256(store_manifest))
    value = {
        "schema": SCHEMA,
        "community_commit": args.community_commit,
        "builder_commit": args.builder_commit,
        "python_build_version": args.python_version,
        "python_runtime_contract": ">=3.12,<3.13",
        "node_runtime_contract": ">=24",
        "node_build_version": args.node_version,
        "pnpm_version": args.pnpm_version,
        "build_tools": {
            "setuptools-80.9.0-py3-none-any.whl": args.setuptools_sha256,
            "wheel-0.45.1-py3-none-any.whl": args.wheel_sha256,
        },
        "packages": [name + "==0.1.0" for name in PACKAGES],
        "community_live": {"root": "community-live", "lockfile_sha256": sha256(args.root / "community-live/pnpm-lock.yaml"), "store_manifest_sha256": sha256(store_manifest)},
        "files": inventory(args.root),
    }
    args.output.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
