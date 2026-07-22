import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
CLI_SCRIPT = REPO_ROOT / "cli" / "sqlstudio.py"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio import RepositoryEngine


class RepositoryEngineTests(unittest.TestCase):
    def test_valid_repository_scan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "project"
            project_dir.mkdir()
            (project_dir / "proc.sql").write_text(
                "CREATE OR ALTER PROCEDURE dbo.Sample AS BEGIN SET NOCOUNT ON; END",
                encoding="utf-8",
            )
            (project_dir / "view.sql").write_text(
                "CREATE VIEW dbo.SampleView AS SELECT 1 AS Id",
                encoding="utf-8",
            )
            (project_dir / "func.sql").write_text(
                "CREATE FUNCTION dbo.SampleFn() RETURNS INT AS BEGIN RETURN 1 END",
                encoding="utf-8",
            )
            (project_dir / "script.sql").write_text("SELECT 1;", encoding="utf-8")

            engine = RepositoryEngine(project_dir)
            payload = engine.scan(project_dir)

            self.assertEqual(payload["root"], str(project_dir))
            self.assertEqual(payload["summary"]["total_sql_files"], 4)
            self.assertEqual(payload["summary"]["stored_procedures"], 1)
            self.assertEqual(payload["summary"]["views"], 1)
            self.assertEqual(payload["summary"]["functions"], 1)
            self.assertEqual(payload["summary"]["scripts"], 1)

            file_types = {item["name"]: item["kind"] for item in payload["files"]}
            self.assertEqual(file_types["proc.sql"], "Stored Procedure")
            self.assertEqual(file_types["view.sql"], "View")
            self.assertEqual(file_types["func.sql"], "Function")
            self.assertEqual(file_types["script.sql"], "Script")

    def test_empty_directory_returns_empty_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = RepositoryEngine(Path(temp_dir)).scan(Path(temp_dir))
            self.assertEqual(payload["summary"]["total_sql_files"], 0)

    def test_nonexistent_directory_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            RepositoryEngine().scan(REPO_ROOT / "missing-directory")

    def test_file_path_instead_of_directory_raises_error(self):
        with tempfile.NamedTemporaryFile(suffix=".sql") as handle:
            with self.assertRaises(NotADirectoryError):
                RepositoryEngine().scan(Path(handle.name))

    def test_stored_procedure_classification(self):
        engine = RepositoryEngine()
        payload = engine.scan(self._create_sample_repo("CREATE OR ALTER PROCEDURE dbo.Test AS BEGIN RETURN END"))
        self.assertEqual(payload["files"][0]["kind"], "Stored Procedure")

    def test_view_classification(self):
        engine = RepositoryEngine()
        payload = engine.scan(self._create_sample_repo("CREATE VIEW dbo.TestView AS SELECT 1 AS Id"))
        self.assertEqual(payload["files"][0]["kind"], "View")

    def test_function_classification(self):
        engine = RepositoryEngine()
        payload = engine.scan(self._create_sample_repo("CREATE FUNCTION dbo.TestFn() RETURNS INT AS BEGIN RETURN 1 END"))
        self.assertEqual(payload["files"][0]["kind"], "Function")

    def test_generic_script_classification(self):
        engine = RepositoryEngine()
        payload = engine.scan(self._create_sample_repo("SELECT 1;"))
        self.assertEqual(payload["files"][0]["kind"], "Script")

    def test_unreadable_file_behavior(self):
        if os.name == "nt":
            self.skipTest("Unreadable-file behavior is not reliably testable on Windows")
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            target = project_dir / "locked.sql"
            target.write_text("SELECT 1;", encoding="utf-8")
            os.chmod(target, 0)
            with self.assertRaises(PermissionError):
                RepositoryEngine().scan(project_dir)

    def test_cli_success_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "sample.sql").write_text("SELECT 1;", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CLI_SCRIPT), "scan", str(project_dir)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            json.loads(result.stdout)

    def test_cli_failure_exit_code(self):
        result = subprocess.run(
            [sys.executable, str(CLI_SCRIPT), "scan", str(REPO_ROOT / "missing-directory")],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not exist", result.stderr)

    def _create_sample_repo(self, content: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        project_dir = Path(temp_dir.name)
        (project_dir / "sample.sql").write_text(content, encoding="utf-8")
        return project_dir


if __name__ == "__main__":
    unittest.main()
