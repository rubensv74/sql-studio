from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PerformanceScopeContractTests(unittest.TestCase):
    def test_scope_decision_is_documented(self):
        decision = ROOT / "docs" / "performance-tooling-scope.md"
        self.assertTrue(decision.is_file())
        text = decision.read_text(encoding="utf-8")
        self.assertIn("deferred to post-MVP", text)
        self.assertIn("Re-entry gate", text)

    def test_unsupported_performance_stubs_are_removed(self):
        legacy_paths = (
            "cli/profiler.py",
            "cli/benchmark.py",
            "profiler/profile.schema.json",
            "benchmark/benchmark.schema.json",
            "benchmarks/BENCHMARK_TEMPLATE.md",
            "core/benchmark.schema.json",
        )
        for relative_path in legacy_paths:
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT / relative_path).exists())


if __name__ == "__main__":
    unittest.main()
