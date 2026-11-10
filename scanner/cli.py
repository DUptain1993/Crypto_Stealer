# -*- coding: utf-8 -*-
"""Linux CLI entry — Rich-based interactive menu."""

import sys

from scanner.ui import (
    print_banner,
    print_info,
    print_error,
    show_menu_table,
    console,
)
from config import load_config
from bot_actions import (
    action_check_address,
    action_batch_check,
    action_seed_check,
    action_proxy_manager,
    action_portfolio_summary,
    action_export_results,
    action_chain_config,
)
from actions.install import action_install_dependencies
from actions.settings import action_settings
from actions.about import action_about
from actions.update import action_system_update
from actions.scan import action_scan


MENU_ITEMS = [
    ("1", "💰", "Check Address Balance", "Single address lookup"),
    ("2", "📦", "Batch Address Check",    "Multiple addresses"),
    ("3", "🌱", "Seed Phrase Check",      "Check seed phrases from file"),
    ("4", "🔄", "Proxy Manager",          "Load, validate, rotate proxies"),
    ("5", "📊", "Portfolio Summary",      "Aggregated results dashboard"),
    ("6", "📤", "Export Results",         "Save to TXT / CSV / JSON / HTML"),
    ("7", "⛓️ ", "Chain Configuration",    "RPC endpoints & settings"),
    ("8", "⚙️ ", "Settings",               "Threads, timeouts, preferences"),
    ("9", "🔍", "Local Scanner",          "Extract local browser/wallet data"),
    ("10", "🔄", "Check for Updates",      "Verify latest version"),
    ("11", "📦", "Install Dependencies",   "pip install -r requirements.txt"),
    ("12", "📚", "About",                  "Project info"),
    ("0", "🚪", "Exit",                    "Close application"),
]


def run_cli():
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
