# -*- coding: utf-8 -*-
"""Rich UI helpers."""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

console = Console()

VERSION = "2.2.0-linux"
TITLE = "Crypto Checker"


def print_banner():
    console.print()
    console.print(Panel(
        f"[bold white]{TITLE}[/bold white] [dim]v{VERSION}[/dim]\n"
        "[dim]Multi-chain wallet balance checker — Linux Edition[/dim]",
        border_style="bright_cyan",
        box=box.DOUBLE,
        padding=(1, 2),
    ))
    console.print()


def show_menu_table(menu_items):
    table = Table(
        title=f"[bold cyan]{TITLE}[/bold cyan]",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        title_style="bold white",
        show_header=True,
        header_style="bold bright_white",
        padding=(0, 2),
    )
    table.add_column("#", style="bold yellow", justify="center", width=4)
    table.add_column("Icon", style="white", justify="center", width=4)
    table.add_column("Action", style="white", min_width=30)
    table.add_column("Description", style="dim", min_width=30)

    for idx, icon, action, desc in menu_items:
        style = "bold red" if action.lower() == "exit" else "white"
        table.add_row(idx, icon, f"[{style}]{action}[/{style}]", desc)

    console.print()
    console.print(table)
    console.print()
    return console.input("[bold cyan]  Select option >[/] ").strip()


def show_balance_table(rows):
    t = Table(title="[bold cyan]Balance Report[/]", box=box.SIMPLE_HEAVY, border_style="cyan")
    t.add_column("Chain", style="bold white", width=14)
    t.add_column("Balance", style="yellow", width=18)
    t.add_column("USD Value", justify="right", style="bold green", width=14)
    t.add_column("Tokens", justify="center", style="dim", width=18)
    for row in rows:
        t.add_row(*row)
    console.print(t)
    console.print()


def show_chain_table(rows):
    t = Table(title="[bold cyan]Chain Configuration[/]", box=box.ROUNDED, border_style="dim")
    t.add_column("Chain", style="bold white", width=14)
    t.add_column("Token", justify="center", style="yellow", width=10)
    t.add_column("RPC", style="dim", width=34)
    t.add_column("Status", justify="center", width=12)
    for row in rows:
        t.add_row(*row)
    console.print(t)
    console.print()


def show_export_table(rows):
    t = Table(title="[bold cyan]Export Formats[/]", box=box.DOUBLE_EDGE, border_style="cyan")
    t.add_column("Format", style="bold white", width=10)
    t.add_column("Extension", style="dim", width=12)
    t.add_column("Fields", style="white", width=36)
    t.add_column("Use Case", style="yellow", width=20)
    for row in rows:
        t.add_row(*row)
    console.print(t)
    console.print()


def show_portfolio_summary(rows):
    t = Table(title="[bold cyan]Portfolio Summary[/]", box=box.DOUBLE_EDGE, border_style="green")
    t.add_column("Chain", style="bold white", width=14)
    t.add_column("Balance", style="yellow", width=18)
    t.add_column("USD", justify="right", style="bold green", width=14)
    t.add_column("Tokens", justify="center", style="dim", width=10)
    t.add_column("Share %", justify="right", style="cyan", width=10)
    for row in rows:
        t.add_row(*row)
    console.print(t)
    console.print()


def show_proxy_pool_table(rows):
    t = Table(title="[bold cyan]Proxy Pool Status[/]", box=box.ROUNDED, border_style="cyan")
    t.add_column("#", style="dim", justify="right", width=4)
    t.add_column("Proxy", style="bright_white", width=36)
    t.add_column("Type", style="cyan", width=8)
    t.add_column("Latency", justify="right", style="yellow", width=10)
    t.add_column("Status", justify="center", width=10)
    t.add_column("Last Used", style="dim", width=12)
    for row in rows:
        t.add_row(*row)
    console.print(t)
    console.print()


def show_seed_results_table(rows):
    t = Table(title="[bold cyan]Address Check Results[/]", box=box.DOUBLE_EDGE, border_style="cyan")
    t.add_column("#", style="dim", justify="right", width=4)
    t.add_column("Address", style="bright_white", width=28)
    t.add_column("Chain", style="cyan", width=12)
    t.add_column("Hash", style="bright_green", width=42)
    t.add_column("Balance", justify="right", style="yellow", width=16)
    t.add_column("USD", justify="right", style="bold green", width=14)
    t.add_column("Flag", justify="center", width=12)
    for row in rows:
        t.add_row(*row)
    console.print(t)
    console.print()


def print_success(msg):
    console.print(f"  [bold green]OK[/] {msg}")


def print_error(msg):
    console.print(f"  [bold red]!![/] {msg}")


def print_info(msg):
    console.print(f"  [bold blue]--[/] {msg}")


def print_warning(msg):
    console.print(f"  [bold yellow]??[/] {msg}")


def separator():
    console.print("[dim]" + "-" * 60 + "[/dim]")


def progress_bar(description, total=100, transient=False):
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40, complete_style="cyan", finished_style="bright_green"),
        TextColumn("[bold]{task.percentage:>3.0f}%"),
        console=console,
        transient=transient,
    )


def show_simple_list(title, items):
    if title:
        console.print(f"\n[bold cyan]{title}[/bold cyan]")
    for item in items:
        console.print(f"  [bright_white]*[/] {item}")
    console.print()
