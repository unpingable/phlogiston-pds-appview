import json
import tempfile
import tarfile
import unittest
from pathlib import Path

from phlogiston_appview.h0_recovery import capture, inspect, rebuild_index, reconcile_restored, restore


REV = "7cccef654a9d94d935deba1ee62490b316549ef6"
APP_REV = "d1585553c4211748b3ab4600283c4965e90030ab"
IMAGE = "registry.test/pds@sha256:" + "a" * 64


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode())


def state(root):
    for name in ("pds/account.sqlite", "pds/sequencer.sqlite", "pds/did_cache.sqlite", "pds/actors/did:plc:synthetic/store.sqlite", "pds/blocks/ab/blob"):
        write(root / name, b"synthetic-pinned-pds-state:" + name.encode())
    write(root / "app/application-state.json", json.dumps({"synthetic_identities": ["did:plc:synthetic"]}))
    write(root / "app/policy.json", json.dumps({"schema": "phlogiston.local-policy.v1", "quench": {"mode": "refuse"}}))
    write(root / "config/public.json", json.dumps({"network": "none"}))
    write(root / "config/secret-references.json", json.dumps({"schema": "phlogiston.secret-reference-inventory.v1", "references": ["local-test-key-custodian/v1"]}))
    write(root / "keys/attestation.json", json.dumps({"schema": "phlogiston.key-attestation.v1", "fingerprints": ["sha256:synthetic"]}))
    attestation = root / "quiescence.json"
    write(attestation, json.dumps({"schema": "phlogiston.h0-quiescence.v1", "source_root": str(root), "writer_pids": [], "runtime": "isolated-test", "observed_at": 1000}))
    return attestation


class H0RecoveryTest(unittest.TestCase):
    def capture(self, root, source, attestation):
        return capture(source, root / "recovery.tar", run_id="h0-test", pds_revision=REV, pds_version="0.4.5034; embedded-pds=0.5.34", pds_image=IMAGE, app_revision=APP_REV, attestation=attestation, captured_at=1000)

    def test_capture_and_blank_host_restore_match_all_members(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); source = root / "source"; source.mkdir(); attestation = state(source)
            manifest = self.capture(root, source, attestation)
            destination = root / "blank"; destination.mkdir()
            external_keys = root / "external-keys.json"; external_keys.write_bytes((source / "keys/attestation.json").read_bytes())
            result = restore(root / "recovery.tar", destination, max_age_seconds=30, now=1001, key_attestation=external_keys)
            self.assertEqual(result["identities"], ["did:plc:synthetic"])
            self.assertEqual((destination / "pds/blocks/ab/blob").read_bytes(), (source / "pds/blocks/ab/blob").read_bytes())
            self.assertEqual(manifest["consistency"]["sqlite_wal_sidecars"], "absent-after-checkpoint")

    def test_negative_cases_refuse_without_healthy_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); source = root / "source"; source.mkdir(); attestation = state(source)
            self.capture(root, source, attestation)
            keys = root / "keys"; keys.write_bytes((source / "keys/attestation.json").read_bytes())
            stale = root / "stale"; stale.mkdir()
            with self.assertRaisesRegex(ValueError, "stale"):
                restore(root / "recovery.tar", stale, max_age_seconds=1, now=1002, key_attestation=keys)
            wrong_key = root / "wrong"; wrong_key.mkdir(); keys.write_text("{}")
            with self.assertRaisesRegex(ValueError, "key"):
                restore(root / "recovery.tar", wrong_key, max_age_seconds=30, now=1001, key_attestation=keys)
            nonempty = root / "nonempty"; nonempty.mkdir(); (nonempty / "old").write_text("x")
            with self.assertRaisesRegex(ValueError, "non-empty"):
                restore(root / "recovery.tar", nonempty, max_age_seconds=30, now=1001, key_attestation=source / "keys/attestation.json")

    def test_capture_refuses_wal_or_partial_pds_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); source = root / "source"; source.mkdir(); attestation = state(source)
            write(source / "pds/account.sqlite-wal", b"writer remains")
            with self.assertRaisesRegex(ValueError, "WAL/SHM"):
                self.capture(root, source, attestation)
            (source / "pds/account.sqlite-wal").unlink(); (source / "pds/blocks/ab/blob").unlink()
            with self.assertRaisesRegex(ValueError, "disk blob"):
                self.capture(root, source, attestation)

    def test_expected_pins_inspect_rebuild_and_duplicate_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); source = root / "source"; source.mkdir(); attestation = state(source)
            manifest = self.capture(root, source, attestation)
            with self.assertRaisesRegex(ValueError, "expected pds image"):
                inspect(root / "recovery.tar", pds_image="registry.test/pds@sha256:" + "b" * 64)
            destination = root / "blank"; destination.mkdir()
            result = restore(root / "recovery.tar", destination, max_age_seconds=30, now=1001,
                key_attestation=source / "keys/attestation.json", pds_revision=REV,
                pds_version=manifest["pds"]["version"], pds_image=IMAGE, app_revision=APP_REV,
                config_sha256=manifest["files"]["config/public.json"]["sha256"])
            self.assertEqual(result["result"], "restored")
            self.assertEqual(rebuild_index(destination)["result"], "rebuilt")
            with self.assertRaisesRegex(ValueError, "already exists"):
                rebuild_index(destination)
            with self.assertRaisesRegex(ValueError, "non-empty"):
                restore(root / "recovery.tar", destination, max_age_seconds=30, now=1001,
                    key_attestation=source / "keys/attestation.json")

    def test_corrupt_or_missing_archive_refuses(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); source = root / "source"; source.mkdir(); attestation = state(source)
            self.capture(root, source, attestation)
            archive = root / "recovery.tar"
            corrupt = root / "corrupt.tar"; corrupt.write_bytes(b"broken-tar")
            with self.assertRaises(Exception):
                inspect(corrupt)
            missing = root / "missing.tar"; missing.write_bytes(b"not-a-tar")
            with self.assertRaises(Exception):
                inspect(missing)

    def test_well_formed_bad_checksum_and_declared_member_refuse(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); source = root / "source"; source.mkdir(); attestation = state(source)
            self.capture(root, source, attestation)
            archive = root / "recovery.tar"
            for name, omit in (("bad-checksum", None), ("missing-member", "state/pds/account.sqlite")):
                target = root / f"{name}.tar"
                with tarfile.open(archive, "r") as original, tarfile.open(target, "w") as replacement:
                    for member in original.getmembers():
                        if member.name == omit:
                            continue
                        data = original.extractfile(member).read()
                        if member.name == "manifest.sha256":
                            data = b"0" * 64 + b"  manifest.json\n"
                        info = tarfile.TarInfo(member.name); info.size = len(data); info.mode = member.mode
                        replacement.addfile(info, __import__("io").BytesIO(data))
                with self.assertRaises(Exception):
                    inspect(target)

    def test_missing_db_config_version_key_and_interrupted_refuse(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); source = root / "source"; source.mkdir(); attestation = state(source)
            (source / "pds/account.sqlite").unlink()
            with self.assertRaisesRegex(ValueError, "account.sqlite"):
                self.capture(root, source, attestation)
            write(source / "pds/account.sqlite", b"restored-db")
            manifest = self.capture(root, source, attestation)
            for kw, value, label in (("pds_version", "wrong", "version"),
                                     ("config_sha256", "0" * 64, "configuration")):
                dest = root / f"blank-{label}"; dest.mkdir()
                with self.assertRaisesRegex(ValueError, label):
                    restore(root / "recovery.tar", dest, max_age_seconds=30, now=1001,
                        key_attestation=source / "keys/attestation.json", **{kw: value})
            missing_key = root / "blank-key"; missing_key.mkdir()
            with self.assertRaisesRegex(ValueError, "external key"):
                restore(root / "recovery.tar", missing_key, max_age_seconds=30, now=1001)
            interrupted = root / "interrupted"; interrupted.mkdir()
            (interrupted / ".phlogiston-h0-restore-incomplete.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "non-empty"):
                restore(root / "recovery.tar", interrupted, max_age_seconds=30, now=1001,
                    key_attestation=source / "keys/attestation.json")
            # A completed restore can be reconciled read-only after a lost response.
            complete = root / "complete"; complete.mkdir()
            restore(root / "recovery.tar", complete, max_age_seconds=30, now=1001,
                key_attestation=source / "keys/attestation.json")
            self.assertEqual(inspect(root / "recovery.tar")["result"], "inspected")
            self.assertEqual(reconcile_restored(root / "recovery.tar", complete)["result"], "reconciled")
            (complete / ".phlogiston-h0-restore-incomplete.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "incomplete"):
                reconcile_restored(root / "recovery.tar", complete)
