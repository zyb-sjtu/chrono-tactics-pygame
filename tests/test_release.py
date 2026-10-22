"""Reject unusable delivery artifacts before executing extracted source."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.verify_release import verify


class ReleaseIntegrityChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "release.zip"
        self.commit = "a" * 40

    def write_archive(self, version="0.2.0", extra=None):
        with zipfile.ZipFile(self.archive, "w") as package:
            package.comment = json.dumps({"format": "chrono-tactics-source-v1", "version": "0.2.0",
                                          "commit": self.commit}).encode("ascii")
            package.writestr("chrono-tactics-pygame-0.2.0/VERSION.txt", version)
            if extra:
                package.writestr(extra, "unwanted")
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.archive.with_suffix(".zip.sha256").write_text(digest + "  release.zip\n", encoding="ascii")

    def reject(self, message, expected=None):
        with patch("scripts.verify_release.subprocess.run") as execute:
            with self.assertRaisesRegex(ValueError, message):
                verify(self.archive, expected)
            execute.assert_not_called()

    def test_changed_archive_fails_checksum_before_execution(self):
        self.write_archive()
        with self.archive.open("ab") as output:
            output.write(b"tampered")
        self.reject("SHA256")

    def test_wrong_source_commit_is_rejected(self):
        self.write_archive()
        self.reject("Unexpected source commit", "b" * 40)

    def test_version_file_must_match_metadata(self):
        self.write_archive(version="9.9.9")
        self.reject("Source version")

    def test_unsafe_paths_and_workspace_artifacts_are_rejected(self):
        for extra in ("chrono-tactics-pygame-0.2.0/../../escape", "/absolute",
                      "chrono-tactics-pygame-0.2.0/.venv/python.exe",
                      "chrono-tactics-pygame-0.2.0/.git/config",
                      "chrono-tactics-pygame-0.2.0/dist/old.zip",
                      "chrono-tactics-pygame-0.2.0/C:/escape"):
            with self.subTest(extra=extra):
                self.write_archive(extra=extra)
                self.reject("Unsafe or unwanted")
