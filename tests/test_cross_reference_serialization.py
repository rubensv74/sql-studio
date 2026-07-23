import json
import tempfile
import unittest
from pathlib import Path

from sqlstudio.cross_reference import (
    CrossReference,
    CrossReferenceSerializer,
    CrossReferenceType,
)


class CrossReferenceSerializerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.references = (
            CrossReference("dbo.Report", "dbo.Orders", CrossReferenceType.READ),
            CrossReference("dbo.Job", "dbo.Refresh", CrossReferenceType.EXECUTE),
        )

    def test_to_dict_uses_versioned_schema(self) -> None:
        payload = CrossReferenceSerializer.to_dict(self.references)

        self.assertEqual("1.0", payload["schema_version"])
        self.assertEqual(2, len(payload["cross_references"]))

    def test_to_dict_orders_references_deterministically(self) -> None:
        payload = CrossReferenceSerializer.to_dict(reversed(self.references))

        self.assertEqual(
            ["dbo.Job", "dbo.Report"],
            [item["source"] for item in payload["cross_references"]],
        )

    def test_to_dict_removes_duplicates(self) -> None:
        payload = CrossReferenceSerializer.to_dict(
            (self.references[0], self.references[0])
        )

        self.assertEqual(1, len(payload["cross_references"]))

    def test_to_json_supports_compact_output(self) -> None:
        text = CrossReferenceSerializer.to_json(self.references, indent=None)

        self.assertNotIn("\n", text)
        self.assertEqual("1.0", json.loads(text)["schema_version"])

    def test_to_json_preserves_unicode(self) -> None:
        references = (
            CrossReference("dbo.InformeÑ", "dbo.Órdenes", CrossReferenceType.READ),
        )

        text = CrossReferenceSerializer.to_json(references)

        self.assertIn("InformeÑ", text)
        self.assertIn("Órdenes", text)

    def test_write_json_creates_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "reports" / "cross-references.json"

            returned = CrossReferenceSerializer.write_json(self.references, output)

            self.assertEqual(output, returned)
            self.assertTrue(output.exists())
            self.assertEqual(
                CrossReferenceSerializer.to_dict(self.references),
                json.loads(output.read_text(encoding="utf-8")),
            )


if __name__ == "__main__":
    unittest.main()
