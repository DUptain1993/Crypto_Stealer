# -*- coding: utf-8 -*-
"""Environment metadata and path resolution."""

import platform
import struct
import sys
from pathlib import Path

_SUPPORTED_PLATFORMS = {"linux", "win32"}

_ARCH_LABELS = {
    "AMD64": "x64", "X86_64": "x64", "X86": "x86", "I686": "x86",
    "ARM64": "arm64", "AARCH64": "arm64",
}


def get_platform_info() -> dict:
    return {
        "os": sys.platform,
        "arch": platform.machine(),
        "python": platform.python_version(),
        "bits": struct.calcsize("P") * 8,
        "impl": platform.python_implementation(),
    }


def check_version(minimum=(3, 8)) -> bool:
    return sys.version_info[:2] >= minimum


def arch_label() -> str:
    m = platform.machine().upper()
    return _ARCH_LABELS.get(m, m.lower())


def is_supported() -> bool:
    return sys.platform in _SUPPORTED_PLATFORMS


def config_dir() -> Path:
    import os
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "CryptoChecker"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "CryptoChecker"
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "crypto-checker"


def temp_dir() -> Path:
    import tempfile
    return Path(tempfile.gettempdir())
