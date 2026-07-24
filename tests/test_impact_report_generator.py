import unittest

from sqlstudio.impact_analysis import ImpactReportGenerator, ImpactResult


class TestImpactReportGenerator(unittest.TestCase):
    def test_generates_metrics_and_dependency_sections(self):
        result = ImpactResult(
            root_object="dbo.usp_Main",
            impacted_objects=["dbo.usp_Main", "dbo.ViewA", "dbo.TableB"],
        )

        html = ImpactReportGenerator().generate(
            result,
            direct_objects=["dbo.ViewA"],
        )

        self.assertIn("Informe de impacto", html)
        self.assertIn("dbo.usp_Main", html)
        self.assertIn("<strong>2</strong>", html)
        self.assertIn("Dependencias directas", html)
        self.assertIn("Dependencias indirectas", html)
        self.assertIn("dbo.ViewA", html)
        self.assertIn("dbo.TableB", html)

    def test_escapes_html_content(self):
        result = ImpactResult(
            root_object="dbo.<root>",
            impacted_objects=["dbo.<object>"],
        )

        html = ImpactReportGenerator().generate(result)

        self.assertIn("dbo.&lt;root&gt;", html)
        self.assertIn("dbo.&lt;object&gt;", html)
        self.assertNotIn("dbo.<object>", html)

    def test_removes_root_and_duplicates_case_insensitively(self):
        result = ImpactResult(
            root_object="dbo.Root",
            impacted_objects=["dbo.Root", "DBO.ROOT", "dbo.Child", "DBO.CHILD"],
        )

        html = ImpactReportGenerator().generate(result)

        self.assertEqual(html.count("dbo.Child"), 1)
        self.assertIn("<strong>1</strong>", html)


if __name__ == "__main__":
    unittest.main()
