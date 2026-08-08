from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ParserSupportContractTests(unittest.TestCase):
    def test_parser_support_contract_documents_scope_and_limitations(self) -> None:
        contract = ROOT / "docs" / "parser-support.md"
        self.assertTrue(contract.is_file())
        text = contract.read_text(encoding="utf-8")
        self.assertIn("Supported reference patterns", text)
        self.assertIn("Known limitations", text)
        self.assertIn("source -> target", text)
        self.assertIn("one primary schema object", text)

    def test_representative_fixture_corpus_exists(self) -> None:
        corpus = ROOT / "tests" / "fixtures" / "tsql_complex"
        expected = {"complex_view.sql", "merge_update.sql", "temp_and_derived.sql", "README.md"}
        self.assertTrue(expected.issubset({path.name for path in corpus.iterdir()}))


if __name__ == "__main__":
    unittest.main()
