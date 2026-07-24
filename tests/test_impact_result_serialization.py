import unittest

from sqlstudio.impact_analysis.models import ImpactResult
from sqlstudio.impact_analysis.serialization import ImpactResultSerializer


class TestImpactResultSerializer(unittest.TestCase):
    def test_to_dict_uses_stable_order(self):
        result = ImpactResult(
            root_object="dbo.usp_Main",
            impacted_objects=["dbo.TableB", "dbo.TableA"],
        )

        payload = ImpactResultSerializer.to_dict(result)

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["root_object"], "dbo.usp_Main")
        self.assertEqual(
            payload["impacted_objects"],
            ["dbo.TableA", "dbo.TableB"],
        )

    def test_json_round_trip(self):
        original = ImpactResult(
            root_object="dbo.usp_Main",
            impacted_objects=["dbo.TableA", "dbo.TableB"],
        )

        restored = ImpactResultSerializer.from_json(
            ImpactResultSerializer.to_json(original)
        )

        self.assertEqual(restored, original)

    def test_rejects_unsupported_schema(self):
        with self.assertRaises(ValueError):
            ImpactResultSerializer.from_dict(
                {
                    "schema_version": "2.0",
                    "root_object": "dbo.usp_Main",
                    "impacted_objects": [],
                }
            )

    def test_rejects_invalid_impacted_objects(self):
        with self.assertRaises(ValueError):
            ImpactResultSerializer.from_dict(
                {
                    "schema_version": "1.0",
                    "root_object": "dbo.usp_Main",
                    "impacted_objects": "dbo.TableA",
                }
            )


if __name__ == "__main__":
    unittest.main()
