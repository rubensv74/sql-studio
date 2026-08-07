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
SPEC = importlib.util.spec_from_file_location("sqlstudio_cli_cycles", CLI_PATH)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


class CircularDependencyCliTests(unittest.TestCase):
    def test_command_prints_detected_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "a.sql"
            second = root / "b.sql"
            first.write_text(
                "CREATE VIEW dbo.A AS SELECT * FROM dbo.B;",
                encoding="utf-8",
            )
            second.write_text(
                "CREATE VIEW dbo.B AS SELECT * FROM dbo.A;",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = CLI.analyze_circular_dependencies([str(first), str(second)])

            payload = json.loads(stdout.getvalue())
            self.assertIsNone(result)
            self.assertEqual(1, payload["summary"]["cycle_count"])
            self.assertEqual(
                ["dbo.A", "dbo.B"],
                payload["circular_dependencies"][0]["members"],
            )

    def test_command_writes_compact_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sql_file = root / "self.sql"
            output = root / "reports" / "cycles.json"
            sql_file.write_text(
                "CREATE VIEW dbo.SelfRef AS SELECT * FROM dbo.SelfRef;",
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = CLI.analyze_circular_dependencies(
                    [str(sql_file)],
                    output=str(output),
                    compact=True,
                )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(output, result)
            self.assertEqual(str(output), stdout.getvalue().strip())
            self.assertTrue(
                payload["circular_dependencies"][0]["is_self_reference"]
            )
            self.assertNotIn("\n  ", output.read_text(encoding="utf-8"))

    def test_parser_exposes_command(self) -> None:
        args = CLI.build_parser().parse_args(
            ["circular-dependencies", "sql", "--recursive", "--compact"]
        )
        self.assertEqual("circular-dependencies", args.cmd)
        self.assertEqual(["sql"], args.paths)
        self.assertTrue(args.recursive)
        self.assertTrue(args.compact)

    def test_main_returns_error_for_missing_input(self) -> None:
        original_argv = CLI.sys.argv
        stderr = StringIO()
        try:
            CLI.sys.argv = ["sqlstudio", "circular-dependencies", "missing.sql"]
            with redirect_stdout(StringIO()), redirect_stderr(stderr):
                result = CLI.main()
        finally:
            CLI.sys.argv = original_argv

        self.assertEqual(1, result)
        self.assertIn("Input path does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
