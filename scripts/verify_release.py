"""Verify source archive integrity and exercise the extracted game offline."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import zipfile


def verify(archive, expected_commit=None):
    archive = Path(archive).resolve()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    sidecar = archive.with_suffix(archive.suffix + ".sha256").read_text(encoding="ascii").strip()
    if sidecar != digest + "  " + archive.name:
        raise ValueError("SHA256 or checksum filename mismatch")
    with zipfile.ZipFile(archive) as package, tempfile.TemporaryDirectory(prefix="chrono-release-") as temp:
        info = json.loads(package.comment)
        if info.get("format") != "chrono-tactics-source-v1":
            raise ValueError("Unknown package format")
        if not re.fullmatch(r"[0-9a-f]{40}", info["commit"]):
            raise ValueError("Invalid commit provenance")
        if expected_commit and info["commit"] != expected_commit:
            raise ValueError("Unexpected source commit")
        if not re.fullmatch(r"\d+\.\d+\.\d+", info["version"]):
            raise ValueError("Invalid package version")
        prefix = "chrono-tactics-pygame-" + info["version"]
        names = package.namelist()
        if not names or len(names) != len(set(names)) or package.testzip():
            raise ValueError("Empty, duplicate or corrupt ZIP entries")
        for entry in package.infolist():
            path = PurePosixPath(entry.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in entry.filename
                    or ":" in entry.filename or path.parts[0] != prefix
                    or any(p in {".git", ".venv", ".delivery", "dist", "__pycache__"} for p in path.parts)
                    or (entry.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError("Unsafe or unwanted archive entry: " + entry.filename)
        package.extractall(temp)
        root = Path(temp) / prefix
        if (root / "VERSION.txt").read_text(encoding="utf-8").strip() != info["version"]:
            raise ValueError("Source version differs from archive metadata")
        env = dict(os.environ, PYTHONPATH=str(root), PYGAME_HIDE_SUPPORT_PROMPT="1",
                   SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        for args in (("scripts/export_source.py", "--check"), ("main.py", "--help"),
                     ("-m", "unittest", "discover", "-s", "tests", "-p", "test_milestone.py", "-v")):
            subprocess.run([sys.executable, *args], cwd=root, env=env, check=True, timeout=180)
    print("Verified version={} commit={} sha256={}".format(info["version"], info["commit"], digest))
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    default_version = (Path(__file__).resolve().parents[1] / "VERSION.txt").read_text(encoding="utf-8").strip()
    parser.add_argument("archive", type=Path, nargs="?",
                        default=Path("dist/chrono-tactics-pygame-{}-source.zip".format(default_version)))
    parser.add_argument("--expected-commit")
    args = parser.parse_args()
    try:
        verify(args.archive, args.expected_commit)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        parser.exit(1, "Release verification failed: {}\n".format(error))
