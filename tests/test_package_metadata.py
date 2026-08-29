from pathlib import Path
import unittest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


PROJECT_ROOT = Path(__file__).parents[1]


class PackageMetadataTests(unittest.TestCase):
    def test_pyproject_declares_installable_package_and_runtime_dependencies(self):
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        self.assertTrue(pyproject_path.exists(), "pyproject.toml is missing")
        metadata = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

        self.assertEqual(metadata["project"]["name"], "ina229-ft232h")
        self.assertEqual(metadata["project"]["version"], "0.1.0")
        self.assertEqual(metadata["project"]["requires-python"], ">=3.10")
        self.assertEqual(metadata["project"].get("license"), "MIT")
        self.assertEqual(metadata["project"].get("license-files"), ["LICENSE"])
        self.assertTrue((PROJECT_ROOT / "LICENSE").exists())
        self.assertEqual(
            metadata["project"]["authors"],
            [{"name": "Sibo Van Gool"}],
        )
        self.assertEqual(
            metadata["project"]["urls"]["Source"],
            "https://github.com/SiboVG/ina229-ft232h",
        )
        self.assertEqual(
            metadata["project"]["urls"]["Issues"],
            "https://github.com/SiboVG/ina229-ft232h/issues",
        )
        self.assertIn("adafruit-blinka>=8.0", metadata["project"]["dependencies"])
        self.assertIn("pyftdi>=0.55", metadata["project"]["dependencies"])

    def test_readme_documents_pypi_installation(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("pip install ina229-ft232h", readme)


if __name__ == "__main__":
    unittest.main()
