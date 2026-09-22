import json
import tempfile
import unittest
from pathlib import Path

from phlogiston_appview.render import render_snapshot, validate_snapshot


class QualificationTest(unittest.TestCase):
    def snapshot(self):
        return json.loads((Path(__file__).parents[1] / "fixtures" / "synthetic-snapshot.json").read_text())

    def test_render_is_local_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            receipt = render_snapshot(self.snapshot(), out)
            self.assertFalse(receipt["network_contacted"])
            self.assertFalse(receipt["production_changed"])
            self.assertEqual(receipt["item_count"], 2)
            self.assertIn("not a network AppView", (out / "index.html").read_text())

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
