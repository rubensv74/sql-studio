import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.dead_objects import (
    DeadObjectExclusion,
    DeadObjectFinding,
    DeadObjectMember,
    DeadObjectResult,
    DeadObjectSerializer,
)


class DeadObjectSerializerTests(unittest.TestCase):
    def test_serializes_candidate_contract_and_limitations(self):
        result = DeadObjectResult(
            findings=(
                DeadObjectFinding(
                    members=(DeadObjectMember("dbo.Orphan", "View"),),
                ),
            ),
            excluded_objects=(
                DeadObjectExclusion(
                    "dbo.Entry",
                    "Stored Procedure",
                    "component_contains_declared_entry_point",
                ),
            ),
            defined_object_count=2,
            entry_points=("dbo.Entry",),
            dynamic_sql_object_count=1,
        )

        payload = DeadObjectSerializer.to_dict(result)

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["classification"], "candidate_only")
        self.assertEqual(payload["summary"]["candidate_object_count"], 1)
        self.assertEqual(payload["summary"]["dynamic_sql_object_count"], 1)
        self.assertTrue(payload["limitations"]["external_usage_may_exist"])
        self.assertTrue(payload["limitations"]["dynamic_sql_may_hide_dependencies"])
        self.assertFalse(payload["limitations"]["safe_to_delete"])

    def test_write_json_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "nested" / "dead-objects.json"
            result = DeadObjectResult()

            written = DeadObjectSerializer.write_json(result, destination)

            self.assertEqual(written, destination)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(payload["dead_object_candidates"], [])


if __name__ == "__main__":
    unittest.main()
