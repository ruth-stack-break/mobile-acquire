"""
hasher.py

SHA-256 hashing utilities.
"""

import json
from pathlib import Path
from Crypto.Hash import SHA256


class EvidenceHasher:
    """
    Handles SHA-256 hashing.
    """

    def hash_file(self, file_path):
        """
        Compute SHA-256 hash.
        """
        file_path = Path(file_path)
        sha = SHA256.new()

        with open(
            file_path,
            "rb"
        ) as file:
            while chunk := file.read(4096):
                sha.update(chunk)

        return sha.hexdigest()

    def write_manifest(
        self,
        manifest_path,
        entries
    ):
        """
        Write manifest JSON.
        """
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(
            manifest_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                entries,
                file,
                indent=4
            )

    def write_hash_file(
        self,
        hash_file_path,
        entries
    ):
        """
        Write standard sha256sum format text file.
        """
        hash_file_path = Path(hash_file_path)
        hash_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(
            hash_file_path,
            "w",
            encoding="utf-8"
        ) as file:
            for rel_path, sha256_val in sorted(entries.items()):
                file.write(f"{sha256_val}  {rel_path}\n")