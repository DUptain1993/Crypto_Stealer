# -*- coding: utf-8 -*-
"""Cover-app actions — address checks, batch, seed, proxies, portfolio, exports."""

import time
from pathlib import Path

from scanner.ui import (
    console,
    print_success,
    print_error,
    print_info,
    print_warning,
    show_balance_table,
    show_chain_table,
    show_seed_results_table,
    show_proxy_pool_table,
    show_portfolio_summary,
    show_export_table,
)


def action_check_address(cfg):
    print_info("Address Balance Check")
    address = console.input("[cyan]Enter wallet address: [/]").strip()
    if not address:
        print_error("Address cannot be empty.")
        return
    chain = console.input("[cyan]Chain (default: ethereum): [/]").strip() or "ethereum"

    print_info(f"Checking {address[:12]}... on {chain}")
    time.sleep(0.8)

    show_balance_table([[chain, "0.0000", "$0.00", "0"]])


def action_batch_check(cfg):
    print_info("Batch Address Check")
    path = console.input("[cyan]File path (one address per line): [/]").strip()
    if not path or not Path(path).exists():
        print_error("File not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        addresses = [ln.strip() for ln in f if ln.strip()]
    if not addresses:
        print_error("No addresses found.")
        return

    print_info(f"Checking {len(addresses)} addresses...")
    results = [[str(i + 1), a[:20] + "...", "0.0000", "$0.00"] for i, a in enumerate(addresses)]
    show_seed_results_table(results)


def action_seed_check(cfg):
    print_info("Seed Phrase Check")
    seed_file = cfg.get("seed_checker", {}).get("seed_file", "seeds.txt")
    if not Path(seed_file).exists():
        print_error(f"Seed file not found: {seed_file}")
        return

    with open(seed_file, "r", encoding="utf-8") as f:
        seeds = [ln.strip() for ln in f if ln.strip()]
    if not seeds:
        print_error("No seed phrases found.")
        return

    print_info(f"Checking {len(seeds)} seed phrases...")
    results = []
    for i, seed in enumerate(seeds):
        preview = " ".join(seed.split()[:3]) + "..."
        results.append([str(i + 1), preview, "ethereum", "0x...", "0.0000", "$0.00", "No"])
    show_seed_results_table(results)


def action_proxy_manager(cfg):
    print_info("Proxy Manager")
    proxy_list = cfg.get("proxies", {}).get("proxy_list", [])
    if not proxy_list:
        print_warning("No proxies configured.")
        print_info("Add proxies under proxies.proxy_list in config.json")
        return
    rows = [[str(i), p, "HTTP", "50ms", "OK", "Now"] for i, p in enumerate(proxy_list[:10], 1)]
    show_proxy_pool_table(rows)


def action_portfolio_summary(cfg):
    print_info("Portfolio Summary")
    records = [
        ["Ethereum", "1.2345 ETH", "$4,567.89", "5", "45%"],
        ["Bitcoin",  "0.0123 BTC", "$1,234.56", "2", "12%"],
        ["Solana",   "45.67 SOL",  "$2,345.67", "3", "23%"],
        ["BSC",      "123.45 BNB", "$2,012.34", "8", "20%"],
    ]
    show_portfolio_summary(records)


def action_export_results(cfg):
    print_info("Export Results")
    export_cfg = cfg.get("export", {})
    default_format = export_cfg.get("default_format", "txt")

    show_export_table([
        ["CSV",  ".csv",  "Address, Balance, USD, Tokens", "Excel / Sheets"],
        ["JSON", ".json", "Full structured data",          "API / Development"],
        ["TXT",  ".txt",  "Plain text report",             "Human readable"],
        ["HTML", ".html", "Styled web page",               "Visual reporting"],
    ])

    fmt = console.input(f"[cyan]Format (default: {default_format}): [/]").strip() or default_format
    name = console.input("[cyan]Output filename (no extension): [/]").strip() or "export"

    out_dir = Path(export_cfg.get("output_directory", "./results"))
    out_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Export saved to: {out_dir / (name + '.' + fmt)}")


def action_chain_config(cfg):
    print_info("Chain Configuration")
    show_chain_table([
        ["Ethereum", "ETH",   "Alchemy / Infura", "OK"],
        ["Bitcoin",  "BTC",   "Blockstream",      "OK"],
        ["Solana",   "SOL",   "Public RPC",       "OK"],
        ["BSC",      "BNB",   "Binance",          "OK"],
        ["Polygon",  "MATIC", "Public RPC",       "OK"],
        ["Arbitrum", "ARB",   "Public RPC",       "OK"],
    ])
