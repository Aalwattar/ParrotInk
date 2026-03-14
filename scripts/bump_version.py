#!/usr/bin/env python3
"""
Atomic Version Bumper for ParrotInk.
Deterministic synchronization of:
1. pyproject.toml [project].version
2. packaging/pyinstaller/version_info.txt
3. uv.lock
"""

import re
import subprocess
import sys
from pathlib import Path


def bump_version(new_version: str):
    root = Path(__file__).parent.parent
    pyproject_path = root / "pyproject.toml"
    vinfo_path = root / "packaging" / "pyinstaller" / "version_info.txt"
    iss_path = root / "packaging" / "inno" / "parrotink.iss"

    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print(f"Error: Version '{new_version}' must be in X.Y.Z format.")
        sys.exit(1)

    # 1. Update pyproject.toml
    print(f"Updating {pyproject_path}...")
    content = pyproject_path.read_text(encoding="utf-8")
    new_content = re.sub(r'^version = ".*"', f'version = "{new_version}"', content, flags=re.M)
    pyproject_path.write_text(new_content, encoding="utf-8")

    # 2. Update version_info.txt
    if vinfo_path.exists():
        print(f"Updating {vinfo_path}...")
        major, minor, patch = new_version.split(".")
        v_content = vinfo_path.read_text(encoding="utf-8")

        # Update tuples: (0, 2, 10, 0)
        v_content = re.sub(
            r"filevers=\(\d+, \d+, \d+, \d+\)",
            f"filevers=({major}, {minor}, {patch}, 0)",
            v_content,
        )
        v_content = re.sub(
            r"prodvers=\(\d+, \d+, \d+, \d+\)",
            f"prodvers=({major}, {minor}, {patch}, 0)",
            v_content,
        )
        # Update strings: u'0.2.10'
        v_content = re.sub(r"u'\d+\.\d+\.\d+'", f"u'{new_version}'", v_content)

        vinfo_path.write_text(v_content, encoding="utf-8")

    # 3. Update Inno Setup script (.iss)
    if iss_path.exists():
        print(f"Updating {iss_path}...")
        iss_content = iss_path.read_text(encoding="utf-8")
        iss_content = re.sub(
            r'^#define MyAppVersion ".*"',
            f'#define MyAppVersion "{new_version}"',
            iss_content,
            flags=re.M,
        )
        iss_path.write_text(iss_content, encoding="utf-8")

    # 4. Synchronize uv.lock (The Deterministic Step)
    print("Running uv lock...")
    try:
        subprocess.run(["uv", "lock"], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running uv lock: {e.stderr.decode()}")
        sys.exit(1)

    print(f"\nSuccessfully bumped to {new_version}")
    print("Run 'git add pyproject.toml packaging/pyinstaller/version_info.txt uv.lock' to stage.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <X.Y.Z>")
        sys.exit(1)
    bump_version(sys.argv[1])
