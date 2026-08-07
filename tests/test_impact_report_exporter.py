import tempfile
import unittest
from pathlib import Path

from sqlstudio.impact_analysis import ImpactNode, ImpactResult
from sqlstudio.impact_analysis.report_exporter import ImpactReportExporter


class TestImpactReportExporter(unittest.TestCase):
    def test_export_uses_tree_to_classify_direct_and_indirect_impact(self):
        result = ImpactResult(
            root_object="dbo.Table",
            impacted_objects=["dbo.Table", "dbo.ViewA", "dbo.ProcB"],
            tree=ImpactNode(
                name="dbo.Table",
                children=[
                    ImpactNode(
                        name="dbo.ViewA",
                        children=[ImpactNode(name="dbo.ProcB")],
                    )
                ],
            ),
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reports" / "impact.html"
            exported = ImpactReportExporter().export(result, path)
            html = exported.read_text(encoding="utf-8")

            self.assertTrue(exported.is_file())
            self.assertIn("Impact Report", html)
            self.assertIn("Impactos directos", html)
            self.assertIn("Impactos indirectos", html)
            self.assertIn("dbo.ViewA", html)
            self.assertIn("dbo.ProcB", html)


if __name__ == "__main__":
    unittest.main()
