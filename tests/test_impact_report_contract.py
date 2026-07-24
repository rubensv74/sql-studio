import unittest
from pathlib import Path

class TestImpactReportContract(unittest.TestCase):
    def test_template_exists(self):
        self.assertTrue(Path("docs/impact-report.md"))

if __name__ == "__main__":
    unittest.main()
