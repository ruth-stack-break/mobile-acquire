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