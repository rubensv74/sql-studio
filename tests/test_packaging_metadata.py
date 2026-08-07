from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

import sqlstudio
from sqlstudio.cli import build_parser


REPO_ROOT = Path(__file__).resolve().parents[1]


class PackagingMetadataTests(unittest.TestCase):
    def test_package_version_matches_compatibility_version_file(self) -> None:
        version_file = (REPO_ROOT / "core" / "version.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(sqlstudio.__version__, version_file)
        self.assertEqual(sqlstudio.__version__, "0.16.0")

    def test_pyproject_declares_installable_console_script(self) -> None:
        with (REPO_ROOT / "pyproject.toml").open("rb") as stream:
            pyproject = tomllib.load(stream)

        self.assertEqual(pyproject["project"]["name"], "sql-studio")
        self.assertEqual(pyproject["project"]["requires-python"], ">=3.12")
        self.assertIn("version", pyproject["project"]["dynamic"])
        self.assertEqual(
            pyproject["project"]["scripts"]["sqlstudio"],
            "sqlstudio.cli:main",
        )
        self.assertEqual(
            pyproject["tool"]["setuptools"]["dynamic"]["version"]["attr"],
            "sqlstudio._version.__version__",
        )

    def test_license_contains_complete_mit_grant(self) -> None:
        license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Permission is hereby granted", license_text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"', license_text)

    def test_canonical_cli_parser_exposes_version_option(self) -> None:
        parser = build_parser()
        option_strings = {
            option
            for action in parser._actions
            for option in action.option_strings
        }
        self.assertIn("--version", option_strings)


if __name__ == "__main__":
    unittest.main()
