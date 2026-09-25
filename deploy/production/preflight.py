#!/usr/bin/env python3
"""Fail-closed checks for the inert Phlogiston production deployment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER = "SET_"

# Phase 2 double-writer guard. Exactly one communityd may hold the community
# actor credential: the atproto-community PCV0 kit's communityd.service. The
# withdrawn phlogiston unit may be present only if it is masked.
PCV0_COMMUNITYD_UNIT = "communityd.service"
WITHDRAWN_COMMUNITYD_UNIT = "phlogiston-communityd.service"
COMMUNITYD_WRITER_MARKER = "communityd-serve"
# Earlier entries take precedence, matching systemd's unit search order.
SYSTEMD_UNIT_DIRS = (
    "etc/systemd/system",
    "run/systemd/system",
    "usr/lib/systemd/system",
    "lib/systemd/system",
)
SYSTEMD_MASKED_STATES = {"masked", "masked-runtime"}

Systemctl = Callable[[list[str]], str]


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


def run_systemctl(args: list[str]) -> str:
    completed = subprocess.run(
        ["systemctl", *args], capture_output=True, text=True, check=True, timeout=30
    )
    return completed.stdout


def default_systemctl() -> Systemctl | None:
    return run_systemctl if shutil.which("systemctl") else None


def exec_starts(text: str) -> list[str]:
    values = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("ExecStart") and "=" in stripped:
            key, _, value = stripped.partition("=")
            if key.strip() == "ExecStart":
                values.append(value.strip())
    return values


def scan_unit_dirs(root: Path) -> tuple[dict[str, dict], bool]:
    """Return {unit name: {masked, exec_starts, path}} and whether any dir existed."""
    units: dict[str, dict] = {}
    scanned = False
    for relative in SYSTEMD_UNIT_DIRS:
        directory = root / relative
        if not directory.is_dir():
            continue
        scanned = True
        for path in sorted(directory.iterdir()):
            if path.suffix != ".service" or path.name in units:
                continue
            if path.is_symlink() and os.readlink(path) == "/dev/null":
                units[path.name] = {"masked": True, "exec_starts": [], "path": str(path)}
                continue
            if not path.is_file():
                continue
            try:
                text = path.read_text(errors="replace")
            except OSError as error:
                raise Refusal(f"systemd is not queryable: unreadable unit {path}") from error
            units[path.name] = {"masked": False, "exec_starts": exec_starts(text), "path": str(path)}
    return units, scanned


def merge_systemctl_units(units: dict[str, dict], systemctl: Systemctl) -> None:
    """Add units systemd knows about that the directory scan did not see."""
    try:
        listing = systemctl(["list-unit-files", "--type=service", "--no-legend", "--no-pager", "--plain"])
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        raise Refusal(f"systemd is not queryable: {error}") from error
    for line in listing.splitlines():
        fields = line.split()
        if not fields or not fields[0].endswith(".service"):
            continue
        name = fields[0]
        state = fields[1] if len(fields) > 1 else ""
        if state in SYSTEMD_MASKED_STATES:
            units[name] = {"masked": True, "exec_starts": [], "path": None}
            continue
        if name in units:
            continue
        try:
            text = systemctl(["cat", "--no-pager", name])
        except (OSError, subprocess.SubprocessError, RuntimeError) as error:
            raise Refusal(f"systemd is not queryable: {error}") from error
        units[name] = {"masked": False, "exec_starts": exec_starts(text), "path": None}


def check_single_community_writer(
    root: Path = Path("/"),
    systemctl: Systemctl | None = None,
) -> dict:
    """Refuse unless the PCV0 communityd.service is the only startable community writer.

    Fails closed: if no systemd unit directory exists under ``root`` and
    ``systemctl`` is unavailable or errors, the guard refuses.
    """
    units, scanned = scan_unit_dirs(root)
    if systemctl is not None:
        merge_systemctl_units(units, systemctl)
    elif not scanned:
        raise Refusal("systemd is not queryable: no unit directory under " + str(root) + " and no systemctl")

    withdrawn = units.get(WITHDRAWN_COMMUNITYD_UNIT)
    if withdrawn is not None and not withdrawn["masked"]:
        raise Refusal(f"{WITHDRAWN_COMMUNITYD_UNIT} is installed and not masked; mask it (PCV0 communityd.service is the sole writer)")

    writers = sorted(
        name
        for name, unit in units.items()
        if not unit["masked"] and any(COMMUNITYD_WRITER_MARKER in value for value in unit["exec_starts"])
    )
    foreign = [name for name in writers if name != PCV0_COMMUNITYD_UNIT]
    if foreign:
        raise Refusal("second communityd writer installed beside PCV0 " + PCV0_COMMUNITYD_UNIT + ": " + ", ".join(foreign))
    return {"community_writer_units": writers, "units_inspected": len(units)}


def validate(
    config_path: Path,
    *,
    now: datetime | None = None,
    machine_id_path: Path = Path("/etc/machine-id"),
    systemd_root: Path = Path("/"),
    systemctl: Systemctl | None | Callable[[], Systemctl | None] = default_systemctl,
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

    resolved_systemctl = systemctl() if systemctl is default_systemctl else systemctl
    writer_guard = check_single_community_writer(systemd_root, resolved_systemctl)
    return {
        "schema": config["schema"],
        "status": "accepted",
        "not_before": config["not_before"],
        "backup_destination": config["expected_backup_destination"],
        "artifacts_verified": 2,
        "community_writer_units": writer_guard["community_writer_units"],
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
