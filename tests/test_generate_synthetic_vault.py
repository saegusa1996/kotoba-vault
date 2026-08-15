import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "generate_synthetic_vault.py"
SPEC = importlib.util.spec_from_file_location("generate_synthetic_vault", MODULE_PATH)
synthetic = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(synthetic)


class SyntheticVaultTests(unittest.TestCase):
    def test_generation_is_deterministic_and_refuses_nonempty_output(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]) as directory:
            output = Path(directory) / "fixture"
            synthetic.generate(output, 3)
            first = (output / "synthetic-000000.md").read_text(encoding="utf-8")

            self.assertIn("reading: あてすと", first)
            self.assertEqual(len(list(output.glob("*.md"))), 3)
            with self.assertRaises(FileExistsError):
                synthetic.generate(output, 3)

    def test_rejects_zero_count(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]) as directory:
            with self.assertRaises(ValueError):
                synthetic.generate(Path(directory) / "fixture", 0)
