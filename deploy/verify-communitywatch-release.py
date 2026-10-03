"""Verify the current eight-wheel/community-live release before installation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from community_release import PACKAGES, SCHEMA, inventory, sha256, strict_json, verify_offline_tree


def verify(root: Path, community_commit: str, builder_commit: str | None = None) -> dict[str, object]:
    # Do not resolve pathname substitutions before checking the exact root.
    if root.is_symlink() or not root.is_dir():
        raise ValueError("community release root must be an exact directory")
    manifest_path = root / "communitywatch-release-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("community release manifest must be regular")
    value = strict_json(manifest_path)
    if not isinstance(value, dict):
        raise ValueError("community release manifest must be an object")
    if value.get("schema") != SCHEMA or value.get("community_commit") != community_commit:
        raise ValueError("community release identity mismatch; historical six-wheel v1 is not current")
    actual_builder = value.get("builder_commit")
    if not isinstance(actual_builder, str) or len(actual_builder) != 40 or any(c not in "0123456789abcdef" for c in actual_builder) or (builder_commit is not None and actual_builder != builder_commit):
        raise ValueError("community release builder identity mismatch")
    if value.get("packages") != [name + "==0.1.0" for name in PACKAGES]:
        raise ValueError("community release package inventory mismatch")
    actual = inventory(root, {manifest_path.name})
    if actual != value.get("files"):
        raise ValueError("community release file inventory mismatch")
    wheels = {name for name in actual if name.startswith("wheels/")}
    expected = {"wheels/" + name.replace("-", "_") + "-0.1.0-py3-none-any.whl" for name in PACKAGES}
    if wheels != expected:
        raise ValueError("community release requires exactly eight hot wheels")
    required = {"community-live/package.json", "community-live/pnpm-lock.yaml", "community-live/tsconfig.json", "community-live/src/server.ts", "community-live/static/app.css", "pnpm-store-manifest.json", "verify-communitywatch-release.py", "community_release.py"}
    if not required.issubset(actual) or any("node_modules" in Path(name).parts for name in actual):
        raise ValueError("community-live immutable payload missing or contains dependencies")
    live = value.get("community_live")
    if live != {"root": "community-live", "lockfile_sha256": sha256(root / "community-live/pnpm-lock.yaml"), "store_manifest_sha256": sha256(root / "pnpm-store-manifest.json")}:
        raise ValueError("community-live source/dependency binding mismatch")
    package = json.loads((root / "community-live/package.json").read_text())
    if value.get("pnpm_version") != "11.11.0" or package.get("packageManager") != "pnpm@11.11.0" or value.get("python_runtime_contract") != ">=3.12,<3.13" or value.get("node_runtime_contract") != ">=24":
        raise ValueError("community release runtime binding mismatch")
    verify_offline_tree(root / "pnpm-store", root / "pnpm-store-manifest.json", live["store_manifest_sha256"])
    return {"result": "verified", "community_commit": community_commit, "builder_commit": actual_builder, "files": len(actual), "hot_wheels": 8, "community_live": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--community-commit", required=True)
    parser.add_argument("--builder-commit")
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.community_commit, args.builder_commit), sort_keys=True))


if __name__ == "__main__":
    main()
