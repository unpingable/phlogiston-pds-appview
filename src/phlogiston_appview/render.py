"""Offline renderer; intentionally contains no HTTP, PDS, or firehose client."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re

SCHEMA = "phlogiston.synthetic-snapshot.v1"
RECEIPT_SCHEMA = "phlogiston.static-render-receipt.v2"
RENDERER_REVISION = "phlogiston-static-renderer/v2"
REQUIRED = {"schema", "snapshot_id", "subject", "items"}
ITEM_REQUIRED = {"id", "uri", "text", "observed_at"}
RUN_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
SOURCE_REVISION = re.compile(r"[0-9a-f]{7,64}\Z")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_existing_directory(path: Path, label: str) -> Path:
    """Return an existing absolute, non-symlink directory without lexical escape."""
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ValueError(f"{label} must be an existing absolute non-symlink directory")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise ValueError(f"{label} must already be canonical")
    return resolved


def regular_file_under(path: Path, root: Path, label: str) -> Path:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be an absolute regular non-symlink file")
    resolved = path.resolve(strict=True)
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label} escapes its trusted root") from error
    for parent in (root, *[root / part for part in relative.parts[:-1]]):
        if parent.is_symlink():
            raise ValueError(f"{label} has a symlinked parent")
    return resolved


def trusted_fixture_root() -> Path:
    return canonical_existing_directory(Path(__file__).parents[2] / "fixtures", "fixture root")


def validate_snapshot(snapshot: object) -> dict:
    if not isinstance(snapshot, dict) or set(snapshot) != REQUIRED:
        raise ValueError("snapshot fields must be exact")
    if snapshot["schema"] != SCHEMA:
        raise ValueError("unsupported snapshot schema")
    if not isinstance(snapshot["snapshot_id"], str) or not snapshot["snapshot_id"]:
        raise ValueError("snapshot_id is required")
    if not isinstance(snapshot["subject"], str) or not snapshot["subject"].startswith("did:example:"):
        raise ValueError("only synthetic did:example subjects are accepted")
    if not isinstance(snapshot["items"], list):
        raise ValueError("items must be a list")
    ids: set[str] = set()
    for item in snapshot["items"]:
        if not isinstance(item, dict) or set(item) != ITEM_REQUIRED:
            raise ValueError("item fields must be exact")
        if not all(isinstance(item[field], str) and item[field] for field in ITEM_REQUIRED):
            raise ValueError("item values must be non-empty strings")
        if item["id"] in ids:
            raise ValueError("duplicate item id")
        ids.add(item["id"])
        prefix = f"at://{snapshot['subject']}/"
        if not item["uri"].startswith(prefix):
            raise ValueError("item URI must belong to synthetic subject")
    return snapshot


def render_snapshot(
    snapshot_path: Path,
    output_root: Path,
    run_id: str,
    source_revision: str,
    *,
    fixture_root: Path | None = None,
) -> tuple[Path, Path, dict]:
    """Render a trusted fixture into a run-owned child; never accept arbitrary input."""
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run id must be lowercase alphanumeric/hyphen and at most 64 characters")
    if not SOURCE_REVISION.fullmatch(source_revision):
        raise ValueError("source revision must be an exact lowercase hexadecimal commit identifier")
    fixture_root = canonical_existing_directory(fixture_root or trusted_fixture_root(), "fixture root")
    output_root = canonical_existing_directory(output_root, "output root")
    snapshot_path = regular_file_under(snapshot_path, fixture_root, "snapshot")
    raw_snapshot = snapshot_path.read_bytes()
    snapshot = validate_snapshot(json.loads(raw_snapshot))
    output = output_root / run_id
    receipt_path = output_root / f"{run_id}.receipt.json"
    if output.exists() or output.is_symlink() or receipt_path.exists() or receipt_path.is_symlink():
        raise ValueError("run-owned output child or receipt already exists")
    output.mkdir(mode=0o700)
    snapshot = validate_snapshot(snapshot)
    cards = "\n".join(
        "<article><h2>{}</h2><p>{}</p><code>{}</code><time>{}</time></article>".format(
            html.escape(item["id"]), html.escape(item["text"]), html.escape(item["uri"]),
            html.escape(item["observed_at"]),
        )
        for item in snapshot["items"]
    )
    page = """<!doctype html><meta charset=\"utf-8\"><title>Phlogiston fixture AppView</title>
<main><h1>Phlogiston synthetic-fixture AppView</h1><p>Offline, read-only snapshot; not a network AppView.</p>
<p>subject: <code>{subject}</code></p>{cards}</main>""".format(
        subject=html.escape(snapshot["subject"]), cards=cards
    )
    page_bytes = page.encode("utf-8")
    (output / "index.html").write_bytes(page_bytes)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "snapshot_id": snapshot["snapshot_id"],
        "input_snapshot_sha256": _sha256(raw_snapshot),
        "renderer_revision": RENDERER_REVISION,
        "source_revision": source_revision,
        "renderer_sha256": _sha256(Path(__file__).read_bytes()),
        "run_id": run_id,
        "output_members": {"index.html": _sha256(page_bytes)},
        "item_count": len(snapshot["items"]),
        "network_contacted": False,
        "production_changed": False,
    }
    receipt_path.write_bytes(_canonical(receipt) + b"\n")
    receipt_path.chmod(0o600)
    return output, receipt_path, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    try:
        output, receipt_path, receipt = render_snapshot(
            args.snapshot, args.output_root, args.run_id, args.source_revision
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
    print(json.dumps({"output": str(output), "receipt": str(receipt_path), **receipt}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
