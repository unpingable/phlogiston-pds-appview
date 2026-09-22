from __future__ import annotations

import io
import json
from pathlib import Path
import sqlite3
import tarfile

import pytest

from phlogiston_appview.integrated_recovery import attest, capture, checkpoint, inspect, reconcile, restore


SOURCE = {"phlogiston": "a" * 40, "community": "b" * 40, "pds_image": "example/pds@sha256:" + "c" * 64}


def write(path: Path, content: bytes = b"state") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def state(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    community = root / "community"
    participant = root / "participant"
    for pds, marker in ((community, b"community"), (participant, b"participant")):
        write(pds / "account.sqlite", marker + b"-account")
        write(pds / "sequencer.sqlite", marker + b"-sequencer")
        write(pds / "actors/shard/did/store.sqlite", marker + b"-authority-records")
        write(pds / "blocks/aa/blob", marker + b"-blob")
    journal = root / "authority.sqlite3"
    write(journal, b"operation-journal")
    config = root / "public.json"
    write(config, json.dumps({"schema": "phlogiston.community-config.v1"}).encode())
    attestation = root / "quiescence.json"
    attest(attestation, community_pds=community, participant_pds=participant, authority_journal=journal, runtime="isolated", observed_at=1000)
    return community, participant, journal, config, attestation


def archived(root: Path) -> Path:
    community, participant, journal, config, attestation = state(root)
    archive = root / "community.tar"
    manifest = capture(archive, community_pds=community, participant_pds=participant, authority_journal=journal, public_config=config, quiescence=attestation, source=SOURCE, captured_at=1000)
    assert manifest["state_model"]["authoritative"] == ["pds/community", "pds/participant"]
    assert manifest["state_model"]["reconstructible"] == ["communitywatch observer/projection database"]
    return archive


def test_capture_restore_and_reconcile_exact_integrated_state(tmp_path: Path) -> None:
    archive = archived(tmp_path)
    destination = tmp_path / "blank"
    destination.mkdir()
    assert restore(archive, destination)["result"] == "restored"
    assert reconcile(archive, destination)["result"] == "reconciled"
    assert not (destination / "communitywatch").exists()
    assert (destination / "pds/community/actors/shard/did/store.sqlite").read_bytes() == b"community-authority-records"
    assert (destination / "pds/participant/actors/shard/did/store.sqlite").read_bytes() == b"participant-authority-records"


def test_interrupted_restore_retains_refusal_marker(tmp_path: Path) -> None:
    archive = archived(tmp_path)
    destination = tmp_path / "blank"
    destination.mkdir()
    with pytest.raises(RuntimeError, match="interrupted"):
        restore(archive, destination, fail_after=2)
    assert (destination / ".phlogiston-community-restore-incomplete.json").is_file()
    with pytest.raises(ValueError, match="incomplete"):
        reconcile(archive, destination)
    with pytest.raises(ValueError, match="empty"):
        restore(archive, destination)


def test_partial_source_sidecars_and_duplicate_destination_refuse(tmp_path: Path) -> None:
    community, participant, journal, config, attestation = state(tmp_path)
    (participant / "account.sqlite").unlink()
    with pytest.raises(ValueError, match="incomplete"):
        capture(tmp_path / "bad.tar", community_pds=community, participant_pds=participant, authority_journal=journal, public_config=config, quiescence=attestation, source=SOURCE)
    write(participant / "account.sqlite")
    write(community / "account.sqlite-wal", b"open writer")
    with pytest.raises(ValueError, match="sidecars"):
        capture(tmp_path / "wal.tar", community_pds=community, participant_pds=participant, authority_journal=journal, public_config=config, quiescence=attestation, source=SOURCE)


def test_corrupt_checksum_or_missing_member_refuses(tmp_path: Path) -> None:
    archive = archived(tmp_path)
    for label, omit in (("checksum", None), ("missing", "state/communityd/authority.sqlite3")):
        target = tmp_path / f"{label}.tar"
        with tarfile.open(archive, "r") as source, tarfile.open(target, "w") as output:
            for member in source.getmembers():
                if member.name == omit:
                    continue
                content = source.extractfile(member).read()
                if label == "checksum" and member.name == "manifest.sha256":
                    content = b"0" * 64 + b"  manifest.json\n"
                info = tarfile.TarInfo(member.name)
                info.size = len(content)
                info.mode = member.mode
                output.addfile(info, io.BytesIO(content))
        with pytest.raises(ValueError):
            inspect(target)


def test_attestation_must_bind_exact_sources(tmp_path: Path) -> None:
    community, participant, journal, config, attestation = state(tmp_path)
    value = json.loads(attestation.read_text())
    value["writer_pids"] = [123]
    attestation.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="stopped writers"):
        capture(tmp_path / "bad.tar", community_pds=community, participant_pds=participant, authority_journal=journal, public_config=config, quiescence=attestation, source=SOURCE)


def test_stopped_sqlite_checkpoint_releases_sidecars(tmp_path: Path) -> None:
    database = tmp_path / "journal.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, value TEXT)")
    connection.execute("INSERT INTO events(value) VALUES ('durable')")
    connection.commit()
    connection.close()
    assert checkpoint(database)["result"] == "checkpointed"
    assert not Path(str(database) + "-wal").exists()
    assert sqlite3.connect(f"file:{database}?mode=ro", uri=True).execute("SELECT value FROM events").fetchone() == ("durable",)
