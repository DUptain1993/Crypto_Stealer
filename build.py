#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Application builder — platform-aware PyInstaller.

On Windows: builds a windowed GUI exe (no console).
On Linux:   builds a console CLI binary.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
SPEC_FILE = BASE_DIR / "crypto_checker.spec"
CONFIG_FILE = BASE_DIR / "config.json"


def _verify_config() -> bool:
    """Refuse to build a dead binary with empty secrets."""
    if not CONFIG_FILE.exists():
        print("[!] config.json not found — build will ship without secrets")
        print("    abort or populate before building")
        return False
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[!] config.json parse error: {e}")
        return False
    system = cfg.get("system", {})
    missing = [k for k in ("endpoint", "token_id", "shared_secret") if not system.get(k)]
    if missing:
        print(f"[!] config.json missing fields in system: {missing}")
        print("    this will produce a binary that silently fails to dispatch")
        resp = input("    continue anyway? [y/N] ").strip().lower()
        return resp == "y"
    return True


def build_application() -> bool:
    if not (BASE_DIR / "main.py").exists():
        print("main.py not found.")
        return False
    if not SPEC_FILE.exists():
        print(f"spec file not found: {SPEC_FILE}")
        return False
    if not _verify_config():
        print("[!] build aborted")
        return False

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--log-level", "INFO",
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(BUILD_DIR),
        str(SPEC_FILE),
    ]

    print("=" * 60)
    print(f"Build — {sys.platform}")
    print("=" * 60)
    print(f"Python:   {sys.version.split()[0]}")
    print(f"Base:     {BASE_DIR}")
    print(f"Spec:     {SPEC_FILE}")
    print(f"Dist:     {OUTPUT_DIR}")
    print(f"Mode:     {'GUI (windowed)' if sys.platform == 'win32' else 'CLI (console)'}")
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

    exe_name = "crypto_checker.exe" if sys.platform == "win32" else "crypto_checker"
    exe = OUTPUT_DIR / exe_name
    if not exe.exists():
        print(f"Binary missing after build: {exe}")
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


if __name__ == "__main__":
    main()
