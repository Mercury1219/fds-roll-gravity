"""Validate release metadata and a source ZIP in memory; --build writes release assets."""

import argparse
import hashlib
import io
import os
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
NAME = "fds-roll-gravity"


def validate_and_pack():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("VERSION must contain major.minor.patch")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if f"Release-v{version}-" not in readme:
        raise ValueError("README release badge is out of sync")
    if f"## [{version}]" not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
        raise ValueError("CHANGELOG is out of sync")
    notes_path = f"docs/releases/v{version}.md"
    if not (ROOT / notes_path).read_text(encoding="utf-8").startswith(f"# FDS Roll Gravity v{version}\n"):
        raise ValueError("Release notes are out of sync")
    tag = os.environ.get("RELEASE_TAG", "")
    if tag and tag != f"v{version}":
        raise ValueError("Tag does not match VERSION")

    names = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode("utf-8").strip("\0").split("\0")
    required = {"generate_roll_ramps.py", "README.md", "LICENSE", "VERSION", "CHANGELOG.md",
                "CONTRIBUTING.md", "SECURITY.md", notes_path, "tests/test_ramps.py",
                "scripts/release.py", ".github/workflows/ci.yml"}
    if not required.issubset(names):
        raise ValueError(f"Missing tracked files: {sorted(required - set(names))}")

    # Match credential shapes, not ordinary documentation mentions.
    sensitive = re.compile(
        r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
        r"AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
        r"[A-Za-z]:[\\/]Users[\\/][^\s]+"
    )
    private_terms = [term for term in os.environ.get("RELEASE_PRIVATE_TERMS", "").split("|") if term]
    archive = io.BytesIO()
    prefix = f"{NAME}-v{version}/"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as packed:
        for name in sorted(names):
            path = Path(name)
            if path.is_absolute() or ".." in path.parts or path.suffix in (".fds", ".pyc"):
                raise ValueError(f"Unwanted release path: {name}")
            data = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
            content = data.decode("utf-8")
            if sensitive.search(content) or any(term in content for term in private_terms):
                raise ValueError(f"Sensitive content detected in {name}")
            if path.suffix == ".py":
                compile(content, name, "exec")
            entry = zipfile.ZipInfo(prefix + name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            packed.writestr(entry, data)
    with zipfile.ZipFile(io.BytesIO(archive.getvalue())) as packed:
        if packed.testzip() is not None:
            raise ValueError("Archive failed CRC validation")
        if set(packed.namelist()) != {prefix + name for name in names}:
            raise ValueError("Archive file list mismatch")
    return version, archive.getvalue(), len(names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="write ZIP and SHA256 to dist/")
    args = parser.parse_args()
    version, data, count = validate_and_pack()
    print(f"Validated version {version}, syntax, sensitive patterns, and {count} source archive files.")
    if args.build:
        target = ROOT / "dist"
        target.mkdir(exist_ok=True)
        filename = f"{NAME}-v{version}.zip"
        (target / filename).write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()
        (target / f"SHA256SUMS-v{version}.txt").write_text(
            f"{checksum}  {filename}\n", encoding="ascii"
        )
        print(f"Built {filename} and SHA256SUMS-v{version}.txt")


if __name__ == "__main__":
    main()
