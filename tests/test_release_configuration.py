from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).parents[1]


class ReleaseConfigurationTests(unittest.TestCase):
    def test_ci_covers_every_supported_python_minor(self):
        workflow = (
            PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
        ).read_text(encoding="utf-8")

        for version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
            self.assertIn('"{}"'.format(version), workflow)
        self.assertIn("python -m unittest discover -v", workflow)

    def test_publish_workflow_uses_trusted_publishing(self):
        workflow = (
            PROJECT_ROOT / ".github" / "workflows" / "publish.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("id-token: write", workflow)
        self.assertIn("actions/upload-artifact@v7", workflow)
        self.assertIn("actions/download-artifact@v8", workflow)
        self.assertIn("pypa/gh-action-pypi-publish@release/v1", workflow)
        self.assertIn("name: testpypi", workflow)
        self.assertIn("name: pypi", workflow)
        self.assertIn("https://test.pypi.org/legacy/", workflow)
        self.assertNotIn("PYPI_TOKEN", workflow)


if __name__ == "__main__":
    unittest.main()
