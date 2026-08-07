import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_SCRIPT = REPO_ROOT / "cli" / "sqlstudio.py"


class DeadObjectCliTests(unittest.TestCase):
    def _write_fixture(self, root: Path) -> None:
        (root / "entry.sql").write_text(
            "CREATE PROCEDURE dbo.Entry AS SELECT * FROM dbo.Helper;",
            encoding="utf-8",
        )
        (root / "helper.sql").write_text(
            "CREATE VIEW dbo.Helper AS SELECT 1 AS Id;",
            encoding="utf-8",
        )
        (root / "orphan.sql").write_text(
            "CREATE VIEW dbo.Orphan AS SELECT 2 AS Id;",
            encoding="utf-8",
        )

    def test_cli_reports_only_unexcluded_root_candidates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_fixture(root)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_SCRIPT),
                    "dead-objects",
                    str(root),
                    "--entry-point",
                    "DBO.ENTRY",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["classification"], "candidate_only")
            self.assertEqual(payload["summary"]["candidate_object_count"], 1)
            self.assertEqual(
                payload["dead_object_candidates"][0]["members"][0]["name"],
                "dbo.Orphan",
            )
            self.assertEqual(payload["entry_points"], ["dbo.Entry"])

    def test_cli_can_write_compact_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_fixture(root)
            destination = root / "reports" / "dead.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_SCRIPT),
                    "dead-objects",
                    str(root),
                    "--entry-point",
                    "dbo.Entry",
                    "--compact",
                    "--output",
                    str(destination),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(destination.is_file())
            self.assertNotIn("\n  ", destination.read_text(encoding="utf-8"))

    def test_cli_rejects_unknown_entry_point(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_fixture(root)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_SCRIPT),
                    "dead-objects",
                    str(root),
                    "--entry-point",
                    "dbo.Missing",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("not a defined SQL object", completed.stderr)


if __name__ == "__main__":
    unittest.main()
