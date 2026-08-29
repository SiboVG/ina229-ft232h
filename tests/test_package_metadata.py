from pathlib import Path
import tomllib
import unittest


PROJECT_ROOT = Path(__file__).parents[1]


class PackageMetadataTests(unittest.TestCase):
    def test_pyproject_declares_installable_package_and_runtime_dependencies(self):
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        self.assertTrue(pyproject_path.exists(), "pyproject.toml is missing")
        metadata = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

        self.assertEqual(metadata["project"]["name"], "ina229-ft232h")
        self.assertEqual(metadata["project"]["version"], "0.1.0")
        self.assertEqual(metadata["project"].get("license"), "MIT")
        self.assertTrue((PROJECT_ROOT / "LICENSE").exists())
        self.assertIn("adafruit-blinka>=8.0", metadata["project"]["dependencies"])
        self.assertIn("pyftdi>=0.55", metadata["project"]["dependencies"])


if __name__ == "__main__":
    unittest.main()
