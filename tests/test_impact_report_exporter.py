import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from sqlstudio.impact_analysis.report_exporter import ImpactReportExporter

class TestImpactReportExporter(unittest.TestCase):
    def test_export(self):
        result=SimpleNamespace(root_object="dbo.usp_Test", impacted_objects=["A","B"])
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"impact.html"
            exported=ImpactReportExporter().export(result,path)
            self.assertTrue(exported.exists())
            self.assertIn("Impact Report", exported.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
