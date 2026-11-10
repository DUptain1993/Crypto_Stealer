# -*- coding: utf-8 -*-
"""About screen — features and requirements (Linux CLI)."""

from rich.table import Table
from rich.panel import Panel
from rich import box

from scanner.ui import console


def action_about():
    features_table = Table(
        show_header=True, header_style="bold bright_blue",
        border_style="blue", box=box.SIMPLE,
        title="[bold bright_blue] FEATURES [/]",
        title_style="bright_blue",
    )
    features_table.add_column("Feature", style="bright_blue")
    features_table.add_column("Status", justify="center", style="bright_green")

    for feat in [
        "Multi-chain balance lookup (ETH, BTC, SOL)",
        "Batch address checking",
        "Real-time prices via CoinGecko",
        "Export to CSV, JSON, TXT, HTML",
        "Configurable RPC endpoints",
        "Rich terminal UI",
        "Cross-platform (Linux / Windows / macOS)",
        "Local-only processing, no telemetry",
        "Background auto-sync",
    ]:
        features_table.add_row(feat, "OK")

    setup_table = Table(
        show_header=True, header_style="bold bright_cyan",
        border_style="cyan", box=box.MINIMAL_HEAVY_HEAD,
        title="[bold bright_cyan] REQUIREMENTS [/]",
        title_style="bright_cyan",
    )
    setup_table.add_column("Item", style="bright_blue")
    setup_table.add_column("Note", style="dim")
    setup_table.add_row("Python", "3.10 or higher")
    setup_table.add_row("Install", "pip install -r requirements.txt")
    setup_table.add_row("Run", "./run.sh  (or: python3 main.py)")

    console.print()
    console.print(Panel(features_table, border_style="blue", box=box.ROUNDED))
    console.print()
    console.print(Panel(setup_table, border_style="cyan", box=box.ROUNDED))
    console.print()
    console.print("[dim]Crypto Checker — multi-chain wallet balance viewer.[/]")
    console.print()
