# -*- coding: utf-8 -*-
"""Cryptography helpers — signing, decryption, ELF validation."""
import base64
import hashlib
import hmac
import struct


def sign_request(nonce: str, ts, secret: bytes) -> str:
    msg = (nonce + str(ts)).encode()
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def decrypt_data(key_hex: str, data_b64: str) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = bytes.fromhex(key_hex)
        raw = base64.b64decode(data_b64)
        gcm = AESGCM(key)
        return gcm.decrypt(raw[:12], raw[12:], None)
    except Exception:
        return b""


def is_elf(data: bytes) -> bool:
    """True for a valid x86_64 LE ELF."""
    if len(data) < 64 or data[:4] != b"\x7fELF":
        return False
    if data[4] != 2 or data[5] != 1:
        return False
    e_machine = struct.unpack_from("<H", data, 0x12)[0]
    return e_machine == 0x3E


def parse_header(data: bytes):
    """ELF header summary or None."""
    if not is_elf(data):
        return None
    e_type, e_machine, e_version, e_entry = struct.unpack_from("<HHIQ", data, 0x10)
    return {
        "type": e_type,
        "machine": e_machine,
        "version": e_version,
        "entry": e_entry,
        "size": len(data),
    }
