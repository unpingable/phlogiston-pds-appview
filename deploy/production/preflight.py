#!/usr/bin/env python3
"""Fail-closed checks for the inert Phlogiston production deployment."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER = "SET_"


class Refusal(RuntimeError):
    pass


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise Refusal(f"unreadable JSON: {path}") from error
    if not isinstance(value, dict):
        raise Refusal(f"JSON object required: {path}")
    return value


def validate(
    config_path: Path,
    *,
    now: datetime | None = None,
    machine_id_path: Path = Path("/etc/machine-id"),
) -> dict:
    config = load_json(config_path)
    if config.get("schema") != "phlogiston.inert-deployment.v1":
        raise Refusal("deployment schema mismatch")
    serialized = json.dumps(config, sort_keys=True)
    if PLACEHOLDER in serialized:
        raise Refusal("deployment configuration contains unresolved placeholders")
    if config.get("deployment_authorized") is not True:
        raise Refusal("deployment authority absent")
    instant = now or datetime.now(timezone.utc)
    not_before = datetime.fromisoformat(str(config["not_before"]).replace("Z", "+00:00"))
    if instant < not_before:
        raise Refusal("Q2 observation boundary has not opened")

    q2 = load_json(Path(config["q2_closeout_receipt"]))
    if q2.get("schema") != "atproto.q2-closeout.v1" or q2.get("uncontaminated") is not True:
        raise Refusal("accepted uncontaminated Q2 closeout receipt absent")
    if q2.get("ended_at") != config["not_before"]:
        raise Refusal("Q2 closeout boundary mismatch")

    actual_machine = hashlib.sha256(machine_id_path.read_bytes().strip()).hexdigest()
    if actual_machine != config["expected_machine_id_sha256"]:
        raise Refusal("host identity mismatch")

    for name in ("phlogiston", "communitywatch"):
        artifact = Path(config[f"{name}_artifact"])
        if not artifact.is_file() or sha256(artifact) != config[f"{name}_artifact_sha256"]:
            raise Refusal(f"{name} artifact identity mismatch")

    custody = load_json(Path(config["secret_custody_receipt"]))
    if custody.get("schema") != "phlogiston.secret-custody.v1" or custody.get("approved") is not True:
        raise Refusal("secret custody is not approved")

    backup = load_json(Path(config["backup_custody_receipt"]))
    if backup.get("schema") != "phlogiston.backup-custody.v1" or backup.get("status") != "accepted":
        raise Refusal("off-host backup custody is not accepted")
    if backup.get("destination") != config["expected_backup_destination"]:
        raise Refusal("backup destination mismatch")
    try:
        probed_at = datetime.fromisoformat(str(backup["probed_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as error:
        raise Refusal("backup custody receipt time is invalid") from error
    if not (0 <= (instant - probed_at).total_seconds() <= 3600):
        raise Refusal("backup custody receipt is stale or future-dated")

    unexpected = [Path(config[key]) for key in ("state_root", "observer_state_root") if Path(config[key]).exists()]
    if unexpected:
        raise Refusal("unexpected existing deployment state: " + ", ".join(map(str, unexpected)))
    return {
        "schema": config["schema"],
        "status": "accepted",
        "not_before": config["not_before"],
        "backup_destination": config["expected_backup_destination"],
        "artifacts_verified": 2,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(args.config)
    except Refusal as error:
        print(json.dumps({"schema": "phlogiston.inert-preflight.v1", "status": "refused", "reason": str(error)}, sort_keys=True))
        raise SystemExit(1)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
