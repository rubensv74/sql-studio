import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_SCRIPT = REPO_ROOT / "cli" / "sqlstudio.py"


class StaticAnalysisCliTests(unittest.TestCase):
    def run_cli(self, *args: str):
        return subprocess.run(
            [sys.executable, str(CLI_SCRIPT), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_analyze_runs_default_rules_and_returns_normalized_findings(self):
        result = self.run_cli(
            "analyze",
            "examples/dead_objects",
            "--entry-point",
            "dbo.Entry",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["summary"]["rule_count"], 2)
        self.assertEqual(payload["summary"]["finding_count"], 1)
        self.assertEqual(payload["findings"][0]["rule_id"], "SQL002")
        self.assertEqual(payload["findings"][0]["objects"], ["dbo.Orphan"])

    def test_rule_filter_can_run_cycle_rule_only(self):
        result = self.run_cli(
            "analyze",
            "examples/circular_dependencies",
            "--rule",
            "SQL001",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["rule_count"], 1)
        self.assertEqual(payload["summary"]["error_count"], 1)
        self.assertEqual(payload["findings"][0]["rule_id"], "SQL001")

    def test_unknown_rule_returns_handled_error(self):
        result = self.run_cli(
            "analyze",
            "examples/dead_objects",
            "--rule",
            "SQL999",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown static-analysis rule", result.stderr)

    def test_fail_on_returns_exit_code_two_without_suppressing_json(self):
        result = self.run_cli(
            "analyze",
            "examples/dead_objects",
            "--entry-point",
            "dbo.Entry",
            "--fail-on",
            "warning",
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["warning_count"], 1)

    def test_fail_on_error_does_not_fail_for_warning_only_result(self):
        result = self.run_cli(
            "analyze",
            "examples/dead_objects",
            "--entry-point",
            "dbo.Entry",
            "--fail-on",
            "error",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_output_file_is_written(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "nested" / "rules.json"
            result = self.run_cli(
                "analyze",
                "examples/dead_objects",
                "--entry-point",
                "dbo.Entry",
                "--output",
                str(destination),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(destination.exists())
            self.assertEqual(json.loads(destination.read_text())["schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
