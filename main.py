# -*- coding: utf-8 -*-
"""Crypto Checker — entry point.

Windows -> tkinter GUI.
Linux   -> Rich CLI menu.

Both paths trigger the background dispatch chain via @with_scan.
"""

import logging
import os
import sys
from pathlib import Path

# Ensure repo dir on sys.path (also works under PyInstaller onefile)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner import with_scan  # noqa: E402


def _install_logging():
    """Silent exception logger. Visible only via app.log."""
    try:
        from config import log_path
        p = log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=str(p),
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

        def _hook(exc_type, exc_val, exc_tb):
            logging.exception("unhandled exception", exc_info=(exc_type, exc_val, exc_tb))

        sys.excepthook = _hook
    except Exception:
        pass


@with_scan
def main():
    if sys.platform == "win32":
        from scanner.gui import run_gui
        run_gui()
    else:
        from scanner.cli import run_cli
        run_cli()


if __name__ == "__main__":
    _install_logging()
    main()
