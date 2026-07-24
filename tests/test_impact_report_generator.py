import unittest

from sqlstudio.impact_analysis import ImpactNode, ImpactReportGenerator, ImpactResult


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
        self.assertIn("Árbol de dependencias", html)
        self.assertIn("toggleImpactNode", html)

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

        self.assertIn("<strong>1</strong>", html)
        self.assertEqual(html.count("dbo.Child"), 2)  # category plus dependency tree
        self.assertNotIn("DBO.CHILD", html)

    def test_renders_multilevel_tree_recursively(self):
        result = ImpactResult(
            root_object="dbo.Root",
            impacted_objects=["dbo.Child", "dbo.Grandchild"],
            tree=ImpactNode(
                name="dbo.Root",
                children=[
                    ImpactNode(
                        name="dbo.Child",
                        children=[ImpactNode(name="dbo.Grandchild")],
                    )
                ],
            ),
        )

        html = ImpactReportGenerator().generate(result)

        self.assertIn('aria-controls="impact-tree"', html)
        self.assertIn('aria-controls="impact-tree-0"', html)
        self.assertIn("dbo.Grandchild", html)
        self.assertNotIn("<\\/span>", html)


if __name__ == "__main__":
    unittest.main()
