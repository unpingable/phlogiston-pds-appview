import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

from phlogiston_appview.archive import backup, restore
from phlogiston_appview.receipt import verify_receipt
from phlogiston_appview.render import render_snapshot, validate_snapshot
from phlogiston_appview import render as renderer
from phlogiston_appview.deploy_validate import validate_image


PROJECT = Path(__file__).parents[1]
FIXTURE = (PROJECT / "fixtures" / "synthetic-snapshot.json").resolve()


class QualificationTest(unittest.TestCase):
    def snapshot(self):
        return json.loads(FIXTURE.read_text())

    def test_render_is_local_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            output, receipt_path, receipt = render_snapshot(FIXTURE, root, "q-local", "77c9dcb")
            self.assertFalse(receipt["network_contacted"])
            self.assertFalse(receipt["production_changed"])
            self.assertEqual(receipt["item_count"], 2)
            self.assertEqual(set(receipt["output_members"]), {"index.html"})
            self.assertIn("not a network AppView", (output / "index.html").read_text())
            self.assertEqual(verify_receipt(output, receipt_path, FIXTURE, Path(renderer.__file__).resolve()), receipt)

    def test_cli_accepts_only_trusted_fixture_and_run_owned_child(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            command = ["python3", "-m", "phlogiston_appview.render", "--snapshot", str(FIXTURE), "--output-root", str(root), "--run-id", "q-cli", "--source-revision", "77c9dcb"]
            env = {**os.environ, "PYTHONPATH": str(PROJECT / "src")}
            result = subprocess.run(command, env=env, text=True, capture_output=True, check=True)
            self.assertTrue((root / "q-cli" / "index.html").is_file(), result.stdout)
            repeated = subprocess.run(command, env=env, text=True, capture_output=True)
            self.assertNotEqual(repeated.returncode, 0)
            foreign = root / "foreign.json"
            foreign.write_text(FIXTURE.read_text())
            command[4] = str(foreign)
            rejected = subprocess.run(command, env=env, text=True, capture_output=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("escapes", rejected.stderr)

    def test_refuses_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            link = root / "link"
            link.symlink_to("/tmp")
            with self.assertRaisesRegex(ValueError, "non-symlink|canonical"):
                render_snapshot(FIXTURE, link, "q-link", "77c9dcb")

    def test_rejects_real_or_foreign_identity(self):
        data = self.snapshot()
        data["subject"] = "did:invalid:not-a-fixture"
        with self.assertRaisesRegex(ValueError, "synthetic"):
            validate_snapshot(data)

    def test_rejects_duplicate_item(self):
        data = self.snapshot()
        data["items"].append(dict(data["items"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_snapshot(data)

    def test_image_admission_refuses_tags(self):
        good = "registry.example/phlogiston/renderer@sha256:" + "a" * 64
        self.assertEqual(validate_image(good), good)
        for bad in ("python:3.12", "repo/image:tag@sha256:" + "a" * 64, "repo/image@sha256:" + "A" * 64):
            with self.assertRaises(ValueError):
                validate_image(bad)

    def test_backup_restore_and_tamper_boundaries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            renderer_path = Path(renderer.__file__).resolve()
            output, receipt, _ = render_snapshot(FIXTURE, root, "q-backup", "77c9dcb")
            archive = root / "render.tar"
            backup(output, receipt, FIXTURE, renderer_path, archive)
            blank_host = root / "blank-host"
            blank_host.mkdir()
            restored, restored_receipt = restore(archive, blank_host, "q-restored", FIXTURE, renderer_path)
            self.assertEqual((restored / "index.html").read_bytes(), (output / "index.html").read_bytes())
            self.assertEqual(verify_receipt(restored, restored_receipt, FIXTURE, renderer_path)["run_id"], "q-backup")
            (restored / "extra.html").write_text("not admitted")
            with self.assertRaisesRegex(ValueError, "members"):
                verify_receipt(restored, restored_receipt, FIXTURE, renderer_path)
            tampered = root / "tampered.tar"
            with tarfile.open(tampered, "w") as tar:
                for source, name in ((output / "index.html", "index.html"), (receipt, "receipt.json")):
                    tar.add(source, arcname=name)
                extra = root / "extra"
                extra.write_text("extra")
                tar.add(extra, arcname="extra")
            with self.assertRaisesRegex(ValueError, "exactly regular"):
                restore(tampered, root, "q-tampered", FIXTURE, renderer_path)
            missing = root / "missing.tar"
            with tarfile.open(missing, "w") as tar:
                tar.add(output / "index.html", arcname="index.html")
            with self.assertRaisesRegex(ValueError, "exactly regular"):
                restore(missing, root, "q-missing", FIXTURE, renderer_path)

    def test_restore_detects_receipt_content_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            renderer_path = Path(renderer.__file__).resolve()
            output, receipt, _ = render_snapshot(FIXTURE, root, "q-tamper", "77c9dcb")
            altered = json.loads(receipt.read_text())
            altered["output_members"]["index.html"] = "0" * 64
            receipt.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError, "content hashes"):
                backup(output, receipt, FIXTURE, renderer_path, root / "should-not-exist.tar")

    def test_uninstall_is_inspection_only(self):
        script = PROJECT / "uninstall" / "uninstall-synthetic.sh"
        result = subprocess.run([str(script), "--inspect-only", "/tmp/phlogiston-candidate"], text=True, capture_output=True, check=True)
        self.assertIn("operator-approved-removal-target", result.stdout)
