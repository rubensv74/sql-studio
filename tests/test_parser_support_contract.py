from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ParserSupportContractTests(unittest.TestCase):
    def test_parser_support_contract_documents_scope_and_limitations(self) -> None:
        contract = ROOT / "docs" / "parser-support.md"
        self.assertTrue(contract.is_file())
        text = contract.read_text(encoding="utf-8")
        self.assertIn("Supported reference and definition patterns", text)
        self.assertIn("Object-scope ownership", text)
        self.assertIn("Known limitations", text)
        self.assertIn("source -> target", text)
        self.assertIn("multiple durable definitions", text)
        self.assertIn("OPENJSON", text)
        self.assertIn("standalone `GO`", text)
        self.assertIn("correct object", text)

        architecture = ROOT / "docs" / "object-scoped-parser.md"
        self.assertTrue(architecture.is_file())
        architecture_text = architecture.read_text(encoding="utf-8")
        self.assertIn("object-scoped parser model", architecture_text)
        self.assertIn("Scope-owned evidence", architecture_text)
        self.assertIn("source -> target", architecture_text)

    def test_representative_fixture_corpus_exists(self) -> None:
        complex_corpus = ROOT / "tests" / "fixtures" / "tsql_complex"
        complex_expected = {
            "complex_view.sql",
            "merge_update.sql",
            "temp_and_derived.sql",
            "README.md",
        }
        self.assertTrue(
            complex_expected.issubset({path.name for path in complex_corpus.iterdir()})
        )

        real_corpus = ROOT / "tests" / "fixtures" / "real_repository"
        real_expected = {"json_stage_procedure.sql", "utility_catalog_script.sql"}
        self.assertTrue(
            real_expected.issubset({path.name for path in real_corpus.iterdir()})
        )

        scope_corpus = ROOT / "tests" / "fixtures" / "object_scopes"
        scope_expected = {"multi_modules.sql", "guarded_tables.sql"}
        self.assertTrue(
            scope_expected.issubset({path.name for path in scope_corpus.iterdir()})
        )


if __name__ == "__main__":
    unittest.main()
