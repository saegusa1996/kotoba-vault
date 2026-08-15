import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools" / "migrate_word_notes.py"
SPEC = importlib.util.spec_from_file_location("migrate_word_notes", MODULE_PATH)
migrate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = migrate
SPEC.loader.exec_module(migrate)


class MigrationTests(unittest.TestCase):
    def test_folder_normalization(self):
        cases = {
            "あたためる": "あ",
            "がっこう": "か",
            "パーティー": "は",
            "ちょっと": "ち",
            None: None,
        }
        for reading, expected in cases.items():
            with self.subTest(reading=reading):
                self.assertEqual(migrate.folder_for_reading(reading), expected)

    def test_inserts_reading_before_aliases(self):
        original = "---\naliases:\n  - 温め\n---\n\nBody\n"
        changed = migrate.add_reading_property(original, "あたためる")
        self.assertIn("reading: あたためる\naliases:", changed)
        self.assertTrue(changed.endswith("\nBody\n"))

    def test_finds_reading_from_kana_filename_without_mutation(self):
        reading, source = migrate.extract_reading(Path("あたためる.md"), "Body\n")
        self.assertEqual(reading, "あたためる")
        self.assertEqual(source, "filename")
        self.assertEqual(migrate.folder_for_reading(reading), "あ")

    def test_duplicate_planned_destinations_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]) as directory:
            root = Path(directory)
            first = root / "one" / "同名.md"
            second = root / "two" / "同名.md"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text("---\nreading: かな\n---\n", encoding="utf-8")
            second.write_text("---\nreading: かに\n---\n", encoding="utf-8")

            plans = migrate.build_plans(root)

            self.assertEqual(len(plans), 2)
            self.assertTrue(all(plan.collision for plan in plans))
            with self.assertRaises(SystemExit):
                migrate.apply_plans(root, plans, add_reading=True, move=True)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())

    def test_fail_on_unresolved_makes_no_changes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]) as directory:
            root = Path(directory)
            unresolved = root / "漢字.md"
            resolved = root / "かな.md"
            unresolved.write_text("Body\n", encoding="utf-8")
            resolved.write_text("Body\n", encoding="utf-8")
            plans = migrate.build_plans(root)

            with self.assertRaises(SystemExit):
                migrate.apply_plans(
                    root,
                    plans,
                    add_reading=True,
                    move=True,
                    fail_on_unresolved=True,
                )

            self.assertEqual(unresolved.read_text(encoding="utf-8"), "Body\n")
            self.assertEqual(resolved.read_text(encoding="utf-8"), "Body\n")

    def test_atomic_metadata_write_preserves_bom(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]) as directory:
            path = Path(directory) / "かな.md"
            path.write_bytes(migrate.codecs.BOM_UTF8 + b"Body\n")

            text, had_bom = migrate.read_utf8(path)
            migrate.write_utf8(path, migrate.add_reading_property(text, "かな"), had_bom)

            self.assertTrue(path.read_bytes().startswith(migrate.codecs.BOM_UTF8))
            self.assertIn("reading: かな", path.read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
