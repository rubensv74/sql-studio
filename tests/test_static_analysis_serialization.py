import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.rules import StaticAnalysisAnalyzer, StaticAnalysisSerializer


class StaticAnalysisSerializerTests(unittest.TestCase):
    def test_schema_contains_normalized_summary_rules_and_findings(self):
        result = StaticAnalysisAnalyzer().analyze_many(
            [
                "CREATE PROCEDURE dbo.Entry AS EXEC dbo.Helper;",
                "CREATE PROCEDURE dbo.Helper AS SELECT 1;",
                "CREATE PROCEDURE dbo.Orphan AS SELECT 1;",
            ],
            entry_points=["dbo.Entry"],
        )
        payload = StaticAnalysisSerializer.to_dict(result)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["summary"]["rule_count"], 2)
        self.assertEqual(payload["summary"]["finding_count"], 1)
        self.assertEqual(payload["summary"]["warning_count"], 1)
        self.assertEqual(payload["findings"][0]["rule_id"], "SQL002")
        self.assertFalse(payload["findings"][0]["properties"]["safe_to_delete"])
        self.assertTrue(payload["context"]["static_analysis_only"])

    def test_json_is_deterministic(self):
        analyzer = StaticAnalysisAnalyzer()
        texts = [
            "CREATE PROCEDURE dbo.A AS EXEC dbo.B;",
            "CREATE PROCEDURE dbo.B AS EXEC dbo.A;",
        ]
        first = StaticAnalysisSerializer.to_json(analyzer.analyze_many(texts))
        second = StaticAnalysisSerializer.to_json(analyzer.analyze_many(reversed(texts)))
        self.assertEqual(json.loads(first), json.loads(second))

    def test_write_json_creates_parent_directories(self):
        result = StaticAnalysisAnalyzer().analyze(
            "CREATE PROCEDURE dbo.Orphan AS SELECT 1;"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "nested" / "analysis.json"
            written = StaticAnalysisSerializer.write_json(result, destination)
            self.assertEqual(written, destination)
            self.assertTrue(destination.exists())
            self.assertEqual(json.loads(destination.read_text())["schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
