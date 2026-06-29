import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.seen as seen_mod


class TestLoadSeen(unittest.TestCase):
    def test_returns_empty_set_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "seen_ids.json"
            with patch.object(seen_mod, "SEEN_IDS_FILE", missing):
                result = seen_mod.load_seen()
        self.assertEqual(result, set())

    def test_loads_ids_from_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "seen_ids.json"
            f.write_text(json.dumps(["abc", "def", "123"]))
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                result = seen_mod.load_seen()
        self.assertEqual(result, {"abc", "def", "123"})

    def test_returns_set_not_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "seen_ids.json"
            f.write_text(json.dumps(["x", "y"]))
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                result = seen_mod.load_seen()
        self.assertIsInstance(result, set)

    def test_empty_file_returns_empty_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "seen_ids.json"
            f.write_text("[]")
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                result = seen_mod.load_seen()
        self.assertEqual(result, set())


class TestSaveSeen(unittest.TestCase):
    def test_saves_ids_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "seen_ids.json"
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                seen_mod.save_seen({"abc", "def"})
            data = json.loads(f.read_text())
        self.assertEqual(set(data), {"abc", "def"})

    def test_output_is_sorted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "seen_ids.json"
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                seen_mod.save_seen({"zzz", "aaa", "mmm"})
            data = json.loads(f.read_text())
        self.assertEqual(data, sorted(data))

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "nested" / "dir" / "seen_ids.json"
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                seen_mod.save_seen({"x"})
            self.assertTrue(f.exists())

    def test_roundtrip(self):
        ids = {"id1", "id2", "id3"}
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "seen_ids.json"
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                seen_mod.save_seen(ids)
                loaded = seen_mod.load_seen()
        self.assertEqual(loaded, ids)

    def test_saves_empty_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "seen_ids.json"
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                seen_mod.save_seen(set())
            data = json.loads(f.read_text())
        self.assertEqual(data, [])

    def test_atomic_write_via_tmp_file(self):
        # Verifies save_seen writes to a .tmp file first then renames (no .tmp left behind)
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "seen_ids.json"
            with patch.object(seen_mod, "SEEN_IDS_FILE", f):
                seen_mod.save_seen({"a"})
            tmp = f.with_suffix(".tmp")
            self.assertFalse(tmp.exists())
            self.assertTrue(f.exists())


if __name__ == "__main__":
    unittest.main()
