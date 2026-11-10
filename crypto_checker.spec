# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — platform-conditional.

Windows -> windowed GUI, tkinter bundled, actions/rich excluded.
Linux   -> console CLI, tkinter excluded, actions/rich bundled.
"""

import sys
from pathlib import Path

BASE = Path(SPECPATH).resolve()

# ─── bundled data ─────────────────────────────────────────────────
datas = []
cfg = BASE / "config.json"
if cfg.exists():
    datas.append((str(cfg), "."))

if sys.platform == "win32":
    # GUI mode
    datas.append((str(BASE / "scanner"), "scanner"))  # queries/gui/env/etc
    hiddenimports = [
        "tkinter", "tkinter.ttk", "tkinter.filedialog",
        "tkinter.messagebox", "tkinter.font",
        "cryptography",
        "cryptography.hazmat.primitives.ciphers",
        "cryptography.hazmat.primitives.ciphers.aead",
        "requests", "urllib3",
        "scanner.gui", "scanner.queries", "scanner.execute",
        "scanner.windows", "scanner.env", "scanner.__init__",
        "config",
    ]
    excludes = [
        "tkinter", "dummy",  # placeholder — tkinter IS bundled
        "actions", "bot_actions", "scanner.cli", "scanner.ui",
        "rich", "rich.console", "rich.table", "rich.panel",
        "rich.progress", "rich.box",
        "matplotlib", "numpy", "pandas", "web3",
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "unittest", "pydoc", "pdb",
    ]
    # Remove the tkinter placeholder so it isn't actually excluded
    excludes = [e for e in excludes if e != "tkinter"]
    console = False
    exe_name = "crypto_checker"
    icon = BASE / "icon.ico"
    icon_arg = str(icon) if icon.exists() else None
else:
    # CLI mode
    datas.append((str(BASE / "actions"), "actions"))
    datas.append((str(BASE / "scanner"), "scanner"))
    hiddenimports = [
        "cryptography",
        "cryptography.hazmat.primitives.ciphers",
        "cryptography.hazmat.primitives.ciphers.aead",
        "cryptography.hazmat.backends",
        "cryptography.hazmat.backends.openssl",
        "requests", "urllib3",
        "urllib3.exceptions", "urllib3.poolmanager",
        "urllib3.util", "urllib3.util.ssl_",
        "email", "email.mime", "email.mime.text",
        "email.mime.multipart", "email.message",
        "email.parser", "http.cookies", "http.client",
        "psutil",
        "rich", "rich.console", "rich.table",
        "rich.panel", "rich.progress", "rich.box",
        "scanner.cli", "scanner.queries", "scanner.execute",
        "scanner.env", "scanner.ui", "scanner.__init__",
        "config", "bot_actions",
        "actions.about", "actions.settings", "actions.install",
        "actions.scan", "actions.update", "actions.helper",
    ]
    excludes = [
        "tkinter", "tkinter.ttk", "tkinter.filedialog",
        "tkinter.messagebox", "tkinter.font",
        "matplotlib", "numpy", "pandas", "web3",
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "unittest", "pydoc",
    ]
    console = True
    exe_name = "crypto_checker"
    icon_arg = None


a = Analysis(
    [str(BASE / "main.py")],
    pathex=[str(BASE)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    runtime_tmpdir=None,
    console=console,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)
