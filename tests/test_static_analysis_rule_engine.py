import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sqlstudio.dependencies import DependencyGraph, DependencyNode
from sqlstudio.parser.ast import SqlDocument
from sqlstudio.rules import (
    Finding,
    RuleContext,
    RuleResult,
    Severity,
    StaticAnalysisRuleEngine,
)


class _FakeRule:
    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        self.title = f"Rule {rule_id}"
        self.description = "test"
        self.default_severity = Severity.INFO

    def evaluate(self, context: RuleContext) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            title=self.title,
            default_severity=self.default_severity,
        )


class StaticAnalysisRuleEngineTests(unittest.TestCase):
    def test_default_rule_ids_are_stable(self):
        self.assertEqual(StaticAnalysisRuleEngine().rule_ids, ("SQL001", "SQL002"))

    def test_duplicate_rule_ids_are_rejected_case_insensitively(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            StaticAnalysisRuleEngine([_FakeRule("sql900"), _FakeRule("SQL900")])

    def test_unknown_selected_rule_is_rejected(self):
        context = RuleContext(documents=(), graph=DependencyGraph())
        with self.assertRaisesRegex(ValueError, "Unknown static-analysis rule"):
            StaticAnalysisRuleEngine().run(context, rule_ids=["SQL999"])

    def test_selected_rules_execute_in_requested_order_without_duplicates(self):
        engine = StaticAnalysisRuleEngine([_FakeRule("SQL100"), _FakeRule("SQL200")])
        context = RuleContext(documents=(), graph=DependencyGraph())
        result = engine.run(context, rule_ids=["sql200", "SQL100", "SQL200"])
        self.assertEqual(tuple(item.rule_id for item in result.rule_results), ("SQL200", "SQL100"))

    def test_default_rules_share_graph_and_emit_cycle_and_dead_candidate(self):
        graph = DependencyGraph()
        graph.add_dependency(
            DependencyNode("dbo.A", "Stored Procedure"),
            DependencyNode("dbo.B", "Stored Procedure"),
        )
        graph.add_dependency(
            DependencyNode("dbo.B", "Stored Procedure"),
            DependencyNode("dbo.A", "Stored Procedure"),
        )
        context = RuleContext(documents=(SqlDocument(sql_text=""),), graph=graph)

        result = StaticAnalysisRuleEngine().run(context)

        self.assertEqual(len(result.findings), 2)
        self.assertEqual({finding.rule_id for finding in result.findings}, {"SQL001", "SQL002"})
        self.assertEqual(result.count(Severity.ERROR), 1)
        self.assertEqual(result.count("warning"), 1)
        self.assertTrue(result.has_at_or_above("warning"))

    def test_entry_point_suppresses_dead_candidate_but_not_cycle_rule(self):
        graph = DependencyGraph()
        graph.add_dependency(
            DependencyNode("dbo.A", "Stored Procedure"),
            DependencyNode("dbo.B", "Stored Procedure"),
        )
        graph.add_dependency(
            DependencyNode("dbo.B", "Stored Procedure"),
            DependencyNode("dbo.A", "Stored Procedure"),
        )
        context = RuleContext(
            documents=(),
            graph=graph,
            entry_points=("dbo.A",),
        )
        result = StaticAnalysisRuleEngine().run(context)
        self.assertEqual(tuple(f.rule_id for f in result.findings), ("SQL001",))

    def test_finding_normalizes_objects_and_properties(self):
        finding = Finding(
            rule_id="sql777",
            severity=Severity.WARNING,
            title=" Demo ",
            message=" Message ",
            objects=("dbo.B", "dbo.a", "dbo.B"),
            properties=(("z", 1), ("a", True)),
        )
        self.assertEqual(finding.rule_id, "SQL777")
        self.assertEqual(finding.objects, ("dbo.a", "dbo.B"))
        self.assertEqual(finding.properties, (("a", True), ("z", 1)))


if __name__ == "__main__":
    unittest.main()
