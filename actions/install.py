# -*- coding: utf-8 -*-
"""Install dependencies — pip install -r requirements.txt."""

import subprocess
import sys
from pathlib import Path

from scanner.ui import print_success, print_error, print_info, show_simple_list


def action_install_dependencies():
    print_info("Installing dependencies from requirements.txt...")

    base_dir = Path(__file__).parent.parent
    req_file = base_dir / "requirements.txt"

    if not req_file.exists():
        print_error("requirements.txt not found.")
        return

    packages = []
    with open(req_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                pkg = line.split(">=")[0].split("==")[0].strip()
                packages.append(pkg)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(base_dir),
        )
        ok = result.returncode == 0

        show_simple_list(
            "Dependencies",
            [f"{p} — installed" if ok else f"{p} — check version" for p in packages]
            or ["No packages listed."],
        )

        if ok:
            print_success("All dependencies installed.")
            print_info("Verify: pip show <library>")
        else:
            print_error(f"Install failed:\n{(result.stderr or '')[:500]}")
    except subprocess.TimeoutExpired:
        print_error("Install timed out (300s).")
    except Exception as e:
        print_error(f"Install error: {e}")
