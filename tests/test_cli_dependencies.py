from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "cli" / "sqlstudio.py"
SPEC = importlib.util.spec_from_file_location("sqlstudio_cli", CLI_PATH)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


class DependencyCliTests(unittest.TestCase):
    def test_collect_sql_files_accepts_files_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sql_file = root / "one.sql"
            sql_file.write_text("SELECT 1;", encoding="utf-8")

            files = CLI._collect_sql_files([str(sql_file), str(sql_file)])

            self.assertEqual([sql_file], files)

    def test_collect_sql_files_honors_recursive_option(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            nested = root / "nested"
            nested.mkdir()
            top_level = root / "top.sql"
            child = nested / "child.sql"
            top_level.write_text("SELECT 1;", encoding="utf-8")
            child.write_text("SELECT 2;", encoding="utf-8")

            direct = CLI._collect_sql_files([str(root)], recursive=False)
            recursive = CLI._collect_sql_files([str(root)], recursive=True)

            self.assertEqual([top_level], direct)
            self.assertEqual([child, top_level], recursive)

    def test_analyze_dependencies_prints_json_to_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sql_file = root / "view.sql"
            sql_file.write_text(
                "CREATE VIEW dbo.ActiveOrders AS SELECT * FROM sales.Orders;",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = CLI.analyze_dependencies([str(sql_file)])

            payload = json.loads(stdout.getvalue())
            self.assertIsNone(result)
            self.assertEqual(1, payload["schema_version"])
            self.assertEqual("dbo.ActiveOrders", payload["nodes"][0]["name"])
            self.assertEqual("sales.Orders", payload["edges"][0]["target"])

    def test_analyze_dependencies_writes_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sql_file = root / "procedure.sql"
            output = root / "reports" / "dependencies.json"
            sql_file.write_text(
                "CREATE PROCEDURE dbo.RunReport AS EXEC reporting.BuildReport;",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = CLI.analyze_dependencies(
                    [str(sql_file)],
                    output=str(output),
                    compact=True,
                )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(output, result)
            self.assertEqual(str(output), stdout.getvalue().strip())
            self.assertEqual("executes", payload["edges"][0]["kind"])
            self.assertNotIn("\n  ", output.read_text(encoding="utf-8"))

    def test_main_returns_error_for_missing_input(self) -> None:
        original_argv = CLI.sys.argv
        stderr = StringIO()
        try:
            CLI.sys.argv = ["sqlstudio", "dependencies", "missing.sql"]
            with redirect_stdout(StringIO()):
                from contextlib import redirect_stderr

                with redirect_stderr(stderr):
                    result = CLI.main()
        finally:
            CLI.sys.argv = original_argv

        self.assertEqual(1, result)
        self.assertIn("Input path does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
