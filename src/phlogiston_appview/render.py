"""Offline renderer; intentionally contains no HTTP, PDS, or firehose client."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

SCHEMA = "phlogiston.synthetic-snapshot.v1"
REQUIRED = {"schema", "snapshot_id", "subject", "items"}
ITEM_REQUIRED = {"id", "uri", "text", "observed_at"}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


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


def render_snapshot(snapshot: dict, output: Path) -> dict:
    snapshot = validate_snapshot(snapshot)
    if output.exists():
        raise ValueError("output target must not exist")
    output.mkdir(parents=True)
    digest = hashlib.sha256(_canonical(snapshot)).hexdigest()
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
    (output / "index.html").write_text(page, encoding="utf-8")
    receipt = {
        "schema": "phlogiston.static-render-receipt.v1",
        "snapshot_id": snapshot["snapshot_id"],
        "snapshot_sha256": digest,
        "item_count": len(snapshot["items"]),
        "network_contacted": False,
        "production_changed": False,
    }
    (output / "receipt.json").write_bytes(_canonical(receipt) + b"\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.snapshot.is_file() or args.snapshot.is_symlink():
        raise SystemExit("snapshot must be a regular local file")
    if args.output.is_absolute() and not str(args.output).startswith("/tmp/"):
        raise SystemExit("absolute output is limited to /tmp for local qualification")
    receipt = render_snapshot(json.loads(args.snapshot.read_text(encoding="utf-8")), args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
