import json
import tempfile
import unittest
from pathlib import Path
from src.hasher import EvidenceHasher


class TestEvidenceHasher(unittest.TestCase):
    def test_hash_file(self):
        hasher = EvidenceHasher()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"forensic-data")
            tmp_path = Path(tmp.name)

        try:
            # sha256 of "forensic-data" is:
            # 6b840fa6b46efd8fa315998a632a5df67645f653457a419eb793ef144f808722
            expected = "9e20ed1e913775202bd04bfe5f8d2fb731e4613440053d35b8b7e9a2d0fa319b"
            self.assertEqual(hasher.hash_file(tmp_path), expected)
        finally:
            tmp_path.unlink()

    def test_write_manifest(self):
        hasher = EvidenceHasher()
        entries = {"file1.txt": "abc", "file2.txt": "def"}

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            hasher.write_manifest(manifest_path, entries)

            with open(manifest_path, encoding="utf-8") as f:
                loaded = json.load(f)

            self.assertEqual(loaded, entries)

    def test_write_hash_file(self):
        hasher = EvidenceHasher()
        entries = {"file1.txt": "abc", "file2.txt": "def"}

        with tempfile.TemporaryDirectory() as tmpdir:
            hash_file_path = Path(tmpdir) / "acquisition_hash.txt"
            hasher.write_hash_file(hash_file_path, entries)

            with open(hash_file_path, encoding="utf-8") as f:
                content = f.read()

            expected = "abc  file1.txt\ndef  file2.txt\n"
            self.assertEqual(content, expected)
