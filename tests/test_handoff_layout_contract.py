from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from sqlstudio.cli import create_handoff


ROOT = Path(__file__).resolve().parents[1]


class HandoffLayoutContractTests(unittest.TestCase):
    def test_only_plural_handoffs_directory_is_versioned(self) -> None:
        self.assertFalse((ROOT / "handoff").exists())
        self.assertTrue((ROOT / "handoffs" / "HANDOFF_TEMPLATE.md").is_file())

    def test_cli_creates_handoff_in_canonical_plural_directory(self) -> None:
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                create_handoff("demo")
                created = Path("handoffs") / "demo.md"
                self.assertTrue(created.is_file())
                self.assertEqual(created.read_text(encoding="utf-8"), "# Handoff demo\n")
                self.assertFalse(Path("handoff").exists())
            finally:
                os.chdir(previous)

    def test_layout_decision_is_documented(self) -> None:
        text = (ROOT / "docs" / "handoff-layout.md").read_text(encoding="utf-8")
        self.assertIn("single canonical", text)
        self.assertIn("handoffs/", text)
        self.assertIn("legacy singular", text)


if __name__ == "__main__":
    unittest.main()
