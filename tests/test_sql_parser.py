import json
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

from sqlstudio import SQLParser


class SQLParserTests(unittest.TestCase):
    def test_stored_procedure_parsing(self):
        parser = SQLParser()
        document = parser.parse("CREATE OR ALTER PROCEDURE dbo.TestProc (@Id INT) AS BEGIN DECLARE @x INT; SET @x = 1; END")
        self.assertTrue(document.objects)
        self.assertEqual(document.objects[0].object_type, "Stored Procedure")
        self.assertEqual(document.objects[0].variables[0].name, "@x")

    def test_view_parsing(self):
        parser = SQLParser()
        document = parser.parse("CREATE VIEW dbo.TestView AS SELECT * FROM dbo.TableA")
        self.assertEqual(document.objects[0].object_type, "View")
        self.assertTrue(document.objects[0].references)

    def test_function_parsing(self):
        parser = SQLParser()
        document = parser.parse("CREATE FUNCTION dbo.TestFn(@x INT) RETURNS INT AS BEGIN RETURN 1 END")
        self.assertEqual(document.objects[0].object_type, "Function")

    def test_trigger_parsing(self):
        parser = SQLParser()
        document = parser.parse("CREATE TRIGGER dbo.TestTrigger ON dbo.TableA AFTER INSERT AS BEGIN SELECT 1 END")
        self.assertEqual(document.objects[0].object_type, "Trigger")

    def test_variables_and_parameters(self):
        parser = SQLParser()
        document = parser.parse("CREATE PROCEDURE dbo.TestProc (@Id INT = 1, @Out INT OUTPUT) AS BEGIN DECLARE @x INT; SET @x = 2; END")
        self.assertEqual(len(document.objects[0].variables), 1)
        self.assertEqual(document.objects[0].parameters[0].name, "@Id")
        self.assertTrue(document.objects[0].parameters[0].default_value == "1")
        self.assertTrue(document.objects[0].parameters[1].output)

    def test_dynamic_sql_and_temporary_tables(self):
        parser = SQLParser()
        document = parser.parse("CREATE PROCEDURE dbo.TestProc AS BEGIN EXEC('SELECT 1'); EXEC sp_executesql N'SELECT 1'; CREATE TABLE #Temp (Id INT); END")
        self.assertTrue(document.objects[0].dynamic_sql)
        self.assertIn("#", document.objects[0].temporary_tables)

    def test_exec_sp_executesql_is_marked_dynamic(self):
        parser = SQLParser()
        document = parser.parse(
            "CREATE PROCEDURE dbo.DynamicProc AS BEGIN "
            "EXEC sp_executesql N'SELECT 1'; END"
        )

        self.assertTrue(document.objects[0].dynamic_sql)

    def test_cross_database_reference(self):
        parser = SQLParser()
        document = parser.parse("SELECT * FROM OtherDb.dbo.TableA")
        self.assertTrue(document.objects[0].references if document.objects else False)

    def test_comments_are_ignored_when_collecting_references(self):
        parser = SQLParser()
        document = parser.parse(
            "CREATE PROCEDURE dbo.TestProc AS BEGIN\n"
            "SELECT * FROM dbo.RealTable;\n"
            "/* ignored FROM dbo.IgnoredTable */\n"
            "SELECT 1;\n"
            "END"
        )
        reference_names = [reference.name for reference in document.objects[0].references]
        self.assertEqual(reference_names, ["RealTable"])

    def test_malformed_sql(self):
        parser = SQLParser()
        document = parser.parse("CREATE PROCEDURE dbo.BadProc AS BEGIN DECLARE @x INT SET @x = 1")
        self.assertTrue(document.objects)

    def test_cli_parse_command(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as handle:
            handle.write("CREATE VIEW dbo.SampleView AS SELECT 1 AS Id")
            path = handle.name
        try:
            result = subprocess.run(
                [sys.executable, str(CLI_SCRIPT), "parse", path],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["objects"][0]["object_type"], "View")
        finally:
            Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
