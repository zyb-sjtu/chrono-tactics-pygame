"""Build a reproducible source ZIP from an exact committed Git tree."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def build(ref="HEAD", output_dir=None):
    commit = git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    version = git("show", commit + ":VERSION.txt").decode().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("VERSION.txt must contain a numeric semantic version")
    folder = Path(output_dir) if output_dir else ROOT / "dist"
    folder.mkdir(parents=True, exist_ok=True)
    name = "chrono-tactics-pygame-{}".format(version)
    archive = folder / (name + "-source.zip")
    git("archive", "--format=zip", "--prefix=" + name + "/", "--output=" + str(archive.resolve()), commit)
    with zipfile.ZipFile(archive, "a") as package:
        package.comment = json.dumps({"format": "chrono-tactics-source-v1", "version": version,
                                      "commit": commit}, sort_keys=True).encode("ascii")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(digest + "  " + archive.name + "\n", encoding="ascii")
    return {"archive": str(archive.resolve()), "checksum": str(checksum.resolve()),
            "version": version, "commit": commit, "sha256": digest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.ref, args.output_dir), indent=2))
