"""Receipt verification for the offline synthetic renderer and its archive boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .render import RECEIPT_SCHEMA, canonical_existing_directory, regular_file_under


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_receipt(
    output: Path, receipt_path: Path, snapshot: Path, renderer: Path | None = None
) -> dict:
    output = canonical_existing_directory(output, "render output")
    receipt_path = regular_file_under(receipt_path, receipt_path.parent.resolve(strict=True), "receipt")
    if not snapshot.is_absolute() or snapshot.is_symlink() or not snapshot.is_file():
        raise ValueError("snapshot must be an absolute regular non-symlink file")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    required = {
        "schema", "snapshot_id", "input_snapshot_sha256", "renderer_revision", "source_revision",
        "renderer_sha256", "run_id", "output_members", "item_count", "network_contacted",
        "production_changed",
    }
    if not isinstance(receipt, dict) or set(receipt) != required or receipt["schema"] != RECEIPT_SCHEMA:
        raise ValueError("receipt fields/schema are not exact")
    if not isinstance(receipt["output_members"], dict) or not receipt["output_members"]:
        raise ValueError("receipt has no output member manifest")
    actual = {
        member.name: _sha256(member)
        for member in output.iterdir()
        if member.is_file() and not member.is_symlink()
    }
    if {member.name for member in output.iterdir()} != set(actual):
        raise ValueError("render output contains a non-regular or symlink member")
    if actual != receipt["output_members"]:
        raise ValueError("render output members or content hashes do not match receipt")
    if _sha256(snapshot) != receipt["input_snapshot_sha256"]:
        raise ValueError("input snapshot hash does not match receipt")
    if renderer is not None:
        if not renderer.is_absolute() or renderer.is_symlink() or not renderer.is_file():
            raise ValueError("renderer must be an absolute regular non-symlink file")
        if _sha256(renderer) != receipt["renderer_sha256"]:
            raise ValueError("renderer source hash does not match receipt")
    return receipt
