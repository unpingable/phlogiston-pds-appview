"""Current release closure and deterministic inventory refusal cases."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

import pytest

DEPLOY = Path(__file__).parents[1] / "deploy"
sys.path.insert(0, str(DEPLOY))
from community_release import PACKAGES, inventory, sha256, verify_offline_tree

SPEC = importlib.util.spec_from_file_location("verify_community_release", DEPLOY / "verify-communitywatch-release.py")
assert SPEC and SPEC.loader
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)
COMMUNITY = "a" * 40
BUILDER = "b" * 40


@pytest.fixture
def release(tmp_path):
    root = tmp_path / "release"
    root.mkdir()
    files = {"community-live/package.json": json.dumps({"packageManager": "pnpm@11.11.0"}), "community-live/pnpm-lock.yaml": "retained-lock", "community-live/tsconfig.json": "{}", "community-live/src/server.ts": "retained-server", "community-live/static/app.css": "retained-style", "verify-communitywatch-release.py": "verifier", "community_release.py": "helper", "pnpm-store/v11/files/fixture": "retained\n"}
    files.update({"wheels/" + name.replace("-", "_") + "-0.1.0-py3-none-any.whl": name for name in PACKAGES})
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    manifest = {"schema": "atproto.offline-tree.v1", "kind": "pnpm-store", "files": [{"path": "v11/files/fixture", "bytes": 9, "sha256": hashlib.sha256(b"retained\n").hexdigest()}]}
    (root / "pnpm-store-manifest.json").write_text(json.dumps(manifest))
    subprocess.run([sys.executable, str(DEPLOY / "build_communitywatch_manifest.py"), "--root", str(root), "--community-commit", COMMUNITY, "--builder-commit", BUILDER, "--python-version", "3.12.3", "--node-version", "v24.13.0", "--pnpm-version", "11.11.0", "--setuptools-sha256", "1" * 64, "--wheel-sha256", "2" * 64, "--output", str(root / "communitywatch-release-manifest.json")], check=True)
    return root


def reseal(root):
    path = root / "communitywatch-release-manifest.json"
    value = json.loads(path.read_text())
    value["files"] = inventory(root, {path.name})
    path.write_text(json.dumps(value))


def test_current_complete_artifact_and_source_bindings(release):
    result = VERIFY.verify(release, COMMUNITY, BUILDER)
    assert result["hot_wheels"] == 8 and result["community_live"] is True
    with pytest.raises(ValueError, match="identity"):
        VERIFY.verify(release, "c" * 40, BUILDER)
    with pytest.raises(ValueError, match="builder"):
        VERIFY.verify(release, COMMUNITY, "c" * 40)


@pytest.mark.parametrize("changed", ["community-live/src/server.ts", "community-live/pnpm-lock.yaml", "wheels/community_policy-0.1.0-py3-none-any.whl"])
def test_content_mutation_refuses(release, changed):
    (release / changed).write_text("changed")
    with pytest.raises(ValueError, match="inventory"):
        VERIFY.verify(release, COMMUNITY, BUILDER)


def test_missing_worker_wheel_refuses_even_resealed_inventory(release):
    (release / "wheels/community_notify-0.1.0-py3-none-any.whl").unlink()
    reseal(release)
    with pytest.raises(ValueError, match="eight"):
        VERIFY.verify(release, COMMUNITY, BUILDER)


def test_missing_frontend_refuses_even_resealed_inventory(release):
    (release / "community-live/static/app.css").unlink()
    reseal(release)
    with pytest.raises(ValueError, match="immutable payload"):
        VERIFY.verify(release, COMMUNITY, BUILDER)


def test_pathname_substitution_and_unlisted_file_refuse(release, tmp_path):
    (release / "extra").write_text("extra")
    with pytest.raises(ValueError, match="inventory"):
        VERIFY.verify(release, COMMUNITY, BUILDER)
    (release / "extra").unlink()
    (release / "substitution").symlink_to(tmp_path)
    with pytest.raises(ValueError, match="non-regular"):
        VERIFY.verify(release, COMMUNITY, BUILDER)


def test_offline_tree_existing_v1_vector_and_gap_refusal(release):
    manifest = release / "pnpm-store-manifest.json"
    digest = sha256(manifest)
    verify_offline_tree(release / "pnpm-store", manifest, digest)
    (release / "pnpm-store/v11/files/fixture").unlink()
    with pytest.raises(ValueError, match="closed manifest"):
        verify_offline_tree(release / "pnpm-store", manifest, digest)


def test_historical_six_wheel_v1_not_current(release):
    path = release / "communitywatch-release-manifest.json"
    value = json.loads(path.read_text())
    value["schema"] = "phlogiston.communitywatch-release-manifest.v1"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="historical"):
        VERIFY.verify(release, COMMUNITY, BUILDER)
