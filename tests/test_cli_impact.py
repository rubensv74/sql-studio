from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "cli" / "sqlstudio.py"
SPEC = importlib.util.spec_from_file_location("sqlstudio_cli_impact", CLI_PATH)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


class ImpactCliTests(unittest.TestCase):
    def test_analyze_impact_prints_json_to_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sql_file = root / "objects.sql"
            sql_file.write_text(
                "CREATE VIEW dbo.ActiveOrders AS SELECT * FROM sales.Orders;",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = CLI.analyze_impact([str(sql_file)], "dbo.ActiveOrders")

            payload = json.loads(stdout.getvalue())
            self.assertIsNone(result)
            self.assertEqual("1.0", payload["schema_version"])
            self.assertEqual("dbo.ActiveOrders", payload["root_object"])
            self.assertEqual(
                ["dbo.ActiveOrders", "sales.Orders"],
                payload["impacted_objects"],
            )

    def test_analyze_impact_writes_compact_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sql_file = root / "procedure.sql"
            output = root / "reports" / "impact.json"
            sql_file.write_text(
                "CREATE PROCEDURE dbo.RunReport AS EXEC reporting.BuildReport;",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = CLI.analyze_impact(
                    [str(sql_file)],
                    "dbo.RunReport",
                    output=str(output),
                    compact=True,
                )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(output, result)
            self.assertEqual(str(output), stdout.getvalue().strip())
            self.assertIn("reporting.BuildReport", payload["impacted_objects"])
            self.assertNotIn("\n  ", output.read_text(encoding="utf-8"))

    def test_parser_exposes_impact_command(self) -> None:
        args = CLI.build_parser().parse_args(
            ["impact", "dbo.ActiveOrders", "sql", "--recursive", "--compact"]
        )
        self.assertEqual("impact", args.cmd)
        self.assertEqual("dbo.ActiveOrders", args.root_object)
        self.assertEqual(["sql"], args.paths)
        self.assertTrue(args.recursive)
        self.assertTrue(args.compact)

    def test_main_returns_error_for_missing_impact_input(self) -> None:
        original_argv = CLI.sys.argv
        stderr = StringIO()
        try:
            CLI.sys.argv = ["sqlstudio", "impact", "dbo.ActiveOrders", "missing.sql"]
            with redirect_stdout(StringIO()), redirect_stderr(stderr):
                result = CLI.main()
        finally:
            CLI.sys.argv = original_argv

        self.assertEqual(1, result)
        self.assertIn("Input path does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
