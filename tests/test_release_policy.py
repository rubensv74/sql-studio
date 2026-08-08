import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
RELEASE_POLICY = REPO_ROOT / "docs" / "release-policy.md"
BRANCH_PROTECTION = REPO_ROOT / "docs" / "branch-protection.md"


class ReleasePolicyTests(unittest.TestCase):
    def test_release_workflow_requires_green_main_ci(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('workflows: ["CI"]', text)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", text)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", text)
        self.assertIn("contents: write", text)

    def test_release_workflow_builds_and_creates_github_release(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python -m build", text)
        self.assertIn("gh release create", text)
        self.assertIn('--target "$sha"', text)
        self.assertIn("--generate-notes", text)
        self.assertIn("dist/*", text)

    def test_release_workflow_does_not_publish_to_pypi(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8").casefold()
        self.assertNotIn("twine", text)
        self.assertNotIn("pypi", text)
        self.assertNotIn("trusted publishing", text)

    def test_release_policy_freezes_stable_semver_and_first_release(self):
        text = RELEASE_POLICY.read_text(encoding="utf-8")
        self.assertIn("GitHub Releases only", text)
        self.assertIn("v0.19.0", text)
        self.assertRegex(text, re.compile(r"vMAJOR\.MINOR\.PATCH"))
        self.assertIn("Release tags are immutable", text)

    def test_branch_protection_contract_names_authoritative_check(self):
        text = BRANCH_PROTECTION.read_text(encoding="utf-8")
        self.assertIn("required status check: `test`", text)
        self.assertIn("block force pushes", text)
        self.assertIn("block branch deletion", text)


if __name__ == "__main__":
    unittest.main()
