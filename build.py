#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Application builder — packages the Linux binary via PyInstaller spec."""

import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
SPEC_FILE = BASE_DIR / "crypto_checker.spec"


def build_application() -> bool:
    if not (BASE_DIR / "main.py").exists():
        print("main.py not found.")
        return False
    if not SPEC_FILE.exists():
        print(f"spec file not found: {SPEC_FILE}")
        return False

    # Fresh work dir. Keep dist/ so we can compare sizes if desired,
    # but wipe on failure paths via shutil below when needed.
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--log-level", "INFO",
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(BUILD_DIR),
        str(SPEC_FILE),
    ]

    print("=" * 60)
    print("Application Builder — Linux Edition")
    print("=" * 60)
    print(f"Python:   {sys.version.split()[0]}")
    print(f"Base:     {BASE_DIR}")
    print(f"Spec:     {SPEC_FILE}")
    print(f"Dist:     {OUTPUT_DIR}")
    print(f"Work:     {BUILD_DIR}")
    print(f"Cmd:      {' '.join(str(c) for c in cmd)}")
    print("=" * 60)
    print()

    try:
        result = subprocess.run(cmd, cwd=str(BASE_DIR))
    except KeyboardInterrupt:
        print("\nBuild interrupted.")
        return False

    if result.returncode != 0:
        print(f"PyInstaller exited with code {result.returncode}")
        return False

    exe = OUTPUT_DIR / "crypto_checker"
    if not exe.exists():
        print("Binary missing after build.")
        return False

    size_mb = exe.stat().st_size / (1024 * 1024)
    print()
    print("=" * 60)
    print(f"Built: {exe} ({size_mb:.2f} MB)")
    print("=" * 60)
    return True


def main():
    ok = build_application()
    print()
    if ok:
        print("Done.")
    else:
        print("Build unsuccessful.")
        print()
        print("If PyInstaller hangs, try a Python 3.12 or 3.13 venv:")
        print("    python3.13 -m venv .venv")
        print("    source .venv/bin/activate")
        print("    pip install -r requirements.txt pyinstaller")
        print("    python build.py")


if __name__ == "__main__":
    main()
