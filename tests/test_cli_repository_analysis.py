import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_SCRIPT = REPO_ROOT / "cli" / "sqlstudio.py"


class RepositoryAnalysisCliTests(unittest.TestCase):
    def run_cli(self, *args: str):
        return subprocess.run(
            [sys.executable, str(CLI_SCRIPT), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_repository_analysis_prints_schema_1_json(self):
        result = self.run_cli(
            "repository-analysis",
            "examples/dead_objects",
            "--entry-point",
            "dbo.Entry",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertGreaterEqual(payload["summary"]["source_count"], 1)
        self.assertEqual(payload["context"]["dependency_direction"], "source -> target")
        self.assertTrue(payload["context"]["dead_objects_are_candidates_only"])

    def test_repository_analysis_writes_json_and_html_from_one_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "report" / "analysis.json"
            html_path = Path(temp_dir) / "report" / "analysis.html"
            result = self.run_cli(
                "repository-analysis",
                "examples/dead_objects",
                "--entry-point",
                "dbo.Entry",
                "--output",
                str(json_path),
                "--html",
                str(html_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json_path.exists())
            self.assertTrue(html_path.exists())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1.0")
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Análisis del repositorio", html)
            self.assertIn("Candidatos a objetos no utilizados", html)

    def test_repository_analysis_reports_missing_input_as_handled_error(self):
        result = self.run_cli("repository-analysis", "does-not-exist")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
