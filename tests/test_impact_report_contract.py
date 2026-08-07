import unittest
from pathlib import Path


class TestImpactReportContract(unittest.TestCase):
    def test_contract_exists_and_defines_required_sections(self):
        contract = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "impact-report.md"
        )

        self.assertTrue(contract.is_file())
        content = contract.read_text(encoding="utf-8")
        for section in (
            "## Semántica de impacto",
            "## Clasificación",
            "## Contrato JSON 1.0",
            "## Salida HTML",
        ):
            self.assertIn(section, content)


if __name__ == "__main__":
    unittest.main()
