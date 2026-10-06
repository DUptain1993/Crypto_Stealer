#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Application builder — packages the Linux binary."""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "dist"
OUTPUT_DIR.mkdir(exist_ok=True)

SEP = os.pathsep


def build_application() -> bool:
    main_py = BASE_DIR / "main.py"
    if not main_py.exists():
        print("main.py not found.")
        return False

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "crypto_checker",
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(BASE_DIR / "build"),
        "--specpath", str(BASE_DIR / "spec"),
        "--add-data", f"actions{SEP}actions",
        "--add-data", f"scanner{SEP}scanner",
        "--add-data", f"config.json{SEP}.",
        "--hidden-import", "cryptography",
        "--hidden-import", "requests",
        "--hidden-import", "psutil",
        "--exclude-module", "tkinter",
        "--exclude-module", "test",
        "--strip",
        str(main_py),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if result.returncode != 0:
        print("Build failed.")
        print(result.stderr[-1000:])
        return False

    exe = OUTPUT_DIR / "crypto_checker"
    if not exe.exists():
        print("Binary missing after build.")
        return False

    size = exe.stat().st_size / (1024 * 1024)
    print(f"Built: {exe} ({size:.2f} MB)")
    return True


def main():
    print("=" * 60)
    print("Application Builder — Linux Edition")
    print("=" * 60)
    ok = build_application()
    print("=" * 60)
    print("Done." if ok else "Build unsuccessful.")


if __name__ == "__main__":
    main()
