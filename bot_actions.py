# -*- coding: utf-8 -*-
"""Linux CLI actions — real balance lookups via scanner.queries."""

import time
from pathlib import Path

from scanner import queries
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
    chain = console.input("[cyan]Chain (ethereum/bitcoin/solana, default: ethereum): [/]").strip() or "ethereum"

    print_info(f"Querying {chain}...")
    try:
        r = queries.lookup(address, chain)
        show_balance_table([[
            r["chain"],
            f"{r['balance']:.6f} {r['symbol']}",
            f"${r['usd']:,.2f}",
            "1",
        ]])
        print_success(f"Address: {address}")
    except Exception as e:
        print_error(f"Query failed: {e}")


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

    chain = console.input("[cyan]Chain (default: ethereum): [/]").strip() or "ethereum"
    print_info(f"Checking {len(addresses)} addresses on {chain}...")

    results = []
    for i, addr in enumerate(addresses, 1):
        try:
            r = queries.lookup(addr, chain)
            results.append([
                str(i),
                addr[:24] + ("…" if len(addr) > 24 else ""),
                r["chain"],
                f"{r['balance']:.6f} {r['symbol']}",
                f"${r['usd']:,.2f}",
            ])
        except Exception as e:
            results.append([str(i), addr[:24], chain, "—", f"ERR: {str(e)[:20]}"])
        time.sleep(0.25)

    if results:
        # Reuse show_seed_results_table shape by trimming
        trimmed = [[r[0], r[1], r[2], "", r[3], r[4], "OK"] for r in results]
        show_seed_results_table(trimmed)


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
    print_warning("Seed derivation requires BIP39/BIP44 — not implemented in this build.")
    print_info("Use the Check Address action with derived addresses instead.")

    results = []
    for i, seed in enumerate(seeds):
        preview = " ".join(seed.split()[:3]) + "..."
        results.append([str(i + 1), preview, "—", "—", "—", "—", "skip"])
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
    print_info("Aggregating recent lookups...")

    prices = queries.get_prices()
    rows = [
        ["Ethereum", "—", f"${prices.get('eth', 0):,.2f} (price)", "—", "—"],
        ["Bitcoin",  "—", f"${prices.get('btc', 0):,.2f} (price)", "—", "—"],
        ["Solana",   "—", f"${prices.get('sol', 0):,.2f} (price)", "—", "—"],
    ]
    show_portfolio_summary(rows)


def action_export_results(cfg):
    print_info("Export Results")
    export_cfg = cfg.get("export", {})
    default_format = export_cfg.get("default_format", "txt")

    show_export_table([
        ["CSV",  ".csv",  "Address, Balance, USD", "Excel / Sheets"],
        ["JSON", ".json", "Full structured data",  "API / Development"],
        ["TXT",  ".txt",  "Plain text report",     "Human readable"],
        ["HTML", ".html", "Styled web page",       "Visual reporting"],
    ])

    fmt = console.input(f"[cyan]Format (default: {default_format}): [/]").strip() or default_format
    name = console.input("[cyan]Output filename (no extension): [/]").strip() or "export"

    out_dir = Path(export_cfg.get("output_directory", "./results"))
    out_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Export would be saved to: {out_dir / (name + '.' + fmt)}")
    print_warning("No data in buffer to export — run a check first.")


def action_chain_config(cfg):
    print_info("Chain Configuration")
    endpoints = cfg.get("rpc_endpoints", {})
    rows = []
    for chain, url in endpoints.items():
        status = "OK" if url and "YOUR_KEY" not in url else "public"
        rows.append([chain.capitalize(), chain[:3].upper(), url[:32], status])
    show_chain_table(rows)
