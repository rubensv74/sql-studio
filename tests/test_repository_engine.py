import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_SCRIPT = REPO_ROOT / "cli" / "sqlstudio.py"


def test_scan_repository_detects_sql_files_and_classifies_them(tmp_path):
    project_dir = tmp_path / "project"
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
    (project_dir / "script.sql").write_text(
        "SELECT 1;",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT), "scan", str(project_dir)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["root"] == str(project_dir)
    assert payload["summary"]["total_sql_files"] == 4
    assert payload["summary"]["stored_procedures"] == 1
    assert payload["summary"]["views"] == 1
    assert payload["summary"]["functions"] == 1
    assert payload["summary"]["scripts"] == 1

    file_types = {item["name"]: item["kind"] for item in payload["files"]}
    assert file_types["proc.sql"] == "Stored Procedure"
    assert file_types["view.sql"] == "View"
    assert file_types["func.sql"] == "Function"
    assert file_types["script.sql"] == "Script"


def test_package_api_exposes_project_index():
    from sqlstudio import RepositoryEngine

    engine = RepositoryEngine()
    assert hasattr(engine, "scan")
    assert hasattr(engine, "index")
