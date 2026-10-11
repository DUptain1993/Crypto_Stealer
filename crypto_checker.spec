# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for crypto_checker.

Bundles:
  - main.py and its imports
  - actions/ and scanner/ as data directories
  - config.json (so the packaged binary has an embedded config)

The exclude list is deliberately conservative. urllib3 (via requests)
imports email and http.cookies lazily at runtime — excluding them
causes ModuleNotFoundError on first HTTP request.
"""

from pathlib import Path

BASE = Path(SPECPATH).resolve()

config_entry = []
cfg = BASE / "config.json"
if cfg.exists():
    config_entry.append((str(cfg), "."))
else:
    print(f"[spec] warning: {cfg} not found — bundle will have no embedded config")


a = Analysis(
    [str(BASE / "main.py")],
    pathex=[str(BASE)],
    binaries=[],
    datas=[
        (str(BASE / "actions"), "actions"),
        (str(BASE / "scanner"), "scanner"),
        *config_entry,
    ],
    hiddenimports=[
        "cryptography",
        "cryptography.hazmat.primitives.ciphers",
        "cryptography.hazmat.primitives.ciphers.aead",
        "cryptography.hazmat.backends",
        "cryptography.hazmat.backends.openssl",
        "requests",
        "urllib3",
        "urllib3.exceptions",
        "urllib3.poolmanager",
        "urllib3.util",
        "urllib3.util.ssl_",
        "email",
        "email.mime",
        "email.mime.text",
        "email.mime.multipart",
        "email.message",
        "email.parser",
        "http.cookies",
        "http.client",
        "psutil",
        "rich",
        "rich.console",
        "rich.table",
        "rich.panel",
        "rich.progress",
        "rich.box",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Conservative: only drop things we know aren't used.
    # Do NOT exclude email / http.cookies / xml / xmlrpc — urllib3
    # and web3 reach for these at runtime.
    excludes=[
        "tkinter",
        "unittest",
        "pydoc",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "matplotlib",
        "numpy",
        "pandas",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="crypto_checker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
