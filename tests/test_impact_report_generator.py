import unittest

from sqlstudio.impact_analysis import ImpactNode, ImpactReportGenerator, ImpactResult


class TestImpactReportGenerator(unittest.TestCase):
    def test_generates_metrics_and_dependency_sections(self):
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

        html = ImpactReportGenerator().generate(result)

        self.assertIn("Informe de impacto", html)
        self.assertIn("dbo.Table", html)
        self.assertIn("Impactos directos", html)
        self.assertIn("Impactos indirectos", html)
        self.assertIn("Árbol de impacto", html)
        self.assertIn("toggleImpactNode", html)
        self.assertIn("<strong>2</strong>", html)
        self.assertIn("<strong>1</strong>", html)

    def test_explicit_direct_objects_remain_supported(self):
        result = ImpactResult(
            root_object="dbo.Root",
            impacted_objects=["dbo.Root", "dbo.Child", "dbo.Grandchild"],
        )

        html = ImpactReportGenerator().generate(
            result,
            direct_objects=["dbo.Child"],
        )

        self.assertIn("Impactos directos", html)
        self.assertIn("dbo.Child", html)
        self.assertIn("dbo.Grandchild", html)

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
        self.assertEqual(html.count("dbo.Child"), 2)  # category plus impact tree
        self.assertNotIn("DBO.CHILD", html)

    def test_renders_multilevel_tree_recursively(self):
        result = ImpactResult(
            root_object="dbo.Root",
            impacted_objects=["dbo.Root", "dbo.Child", "dbo.Grandchild"],
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
