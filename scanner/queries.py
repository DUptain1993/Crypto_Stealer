# -*- coding: utf-8 -*-
"""Real balance lookups. Public RPC endpoints, no API keys required.

Returns Decimal balances. Raises ValueError on invalid addresses,
ConnectionError on network failure.
"""

import json
import re
import time
from decimal import Decimal
from functools import lru_cache

import requests

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_TIMEOUT = 20

# Known public endpoints — rotate on failure
ETH_RPCS = [
    "https://eth.llamarpc.com",
    "https://cloudflare-eth.com",
    "https://rpc.ankr.com/eth",
]
BTC_API   = "https://blockstream.info/api"
SOL_RPC   = "https://api.mainnet-beta.solana.com"
PRICE_API = "https://api.coingecko.com/api/v3/simple/price"

_ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_BTC_RE = re.compile(r"^(bc1[a-zA-HJ-NP-Z0-9]{25,87}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$")
_SOL_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def _is_eth(addr: str) -> bool:  return bool(_ETH_RE.match(addr))
def _is_btc(addr: str) -> bool:  return bool(_BTC_RE.match(addr))
def _is_sol(addr: str) -> bool:  return bool(_SOL_RE.match(addr))


def _post_json(url: str, payload: dict) -> dict:
    r = requests.post(url, json=payload, headers={"User-Agent": _UA}, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _get_json(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": _UA}, timeout=_TIMEOUT)
    r.raise_for_status()
    if "text/plain" in r.headers.get("Content-Type", "") or r.text.strip().startswith(("{", "[")):
        return r.json()
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text}


def get_eth_balance(address: str) -> Decimal:
    if not _is_eth(address):
        raise ValueError("invalid Ethereum address")
    last_err = None
    for rpc in ETH_RPCS:
        try:
            data = _post_json(rpc, {
                "jsonrpc": "2.0", "id": 1,
                "method": "eth_getBalance",
                "params": [address, "latest"],
            })
            if "result" in data and data["result"]:
                wei = int(data["result"], 16)
                return Decimal(wei) / Decimal(10**18)
            last_err = data.get("error", "no result")
        except Exception as e:
            last_err = e
            continue
    raise ConnectionError(f"all ETH RPCs failed: {last_err}")


def get_btc_balance(address: str) -> Decimal:
    if not _is_btc(address):
        raise ValueError("invalid Bitcoin address")
    try:
        data = _get_json(f"{BTC_API}/address/{address}")
    except Exception as e:
        raise ConnectionError(f"BTC API failed: {e}")
    chain = data.get("chain_stats", {})
    funded = int(chain.get("funded_txo_sum", 0))
    spent  = int(chain.get("spent_txo_sum", 0))
    return Decimal(funded - spent) / Decimal(10**8)


def get_sol_balance(address: str) -> Decimal:
    if not _is_sol(address):
        raise ValueError("invalid Solana address")
    try:
        data = _post_json(SOL_RPC, {
            "jsonrpc": "2.0", "id": 1,
            "method": "getBalance",
            "params": [address],
        })
    except Exception as e:
        raise ConnectionError(f"SOL RPC failed: {e}")
    result = data.get("result", {})
    lamports = int(result.get("value", 0))
    return Decimal(lamports) / Decimal(10**9)


@lru_cache(maxsize=1)
def _cached_prices(_ttl_bucket: int) -> dict:
    """Cache keyed on 60s bucket — re-fetches once per minute."""
    try:
        r = requests.get(
            PRICE_API,
            params={"ids": "ethereum,bitcoin,solana", "vs_currencies": "usd"},
            headers={"User-Agent": _UA},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        d = r.json()
        return {
            "eth": float(d.get("ethereum", {}).get("usd", 0)),
            "btc": float(d.get("bitcoin", {}).get("usd", 0)),
            "sol": float(d.get("solana", {}).get("usd", 0)),
        }
    except Exception:
        return {"eth": 0, "btc": 0, "sol": 0}


def get_prices() -> dict:
    bucket = int(time.time()) // 60
    return _cached_prices(bucket)


def lookup(address: str, chain: str) -> dict:
    """Unified lookup. chain in {'Ethereum','Bitcoin','Solana'} (case-insensitive)."""
    chain_lc = chain.lower()
    if chain_lc == "ethereum" or chain_lc == "eth":
        balance = get_eth_balance(address)
        symbol, price_key = "ETH", "eth"
    elif chain_lc == "bitcoin" or chain_lc == "btc":
        balance = get_btc_balance(address)
        symbol, price_key = "BTC", "btc"
    elif chain_lc == "solana" or chain_lc == "sol":
        balance = get_sol_balance(address)
        symbol, price_key = "SOL", "sol"
    else:
        raise ValueError(f"unsupported chain: {chain}")

    prices = get_prices()
    usd = float(balance) * prices.get(price_key, 0)
    return {
        "address": address,
        "chain": chain.capitalize(),
        "balance": balance,
        "symbol": symbol,
        "usd": usd,
    }
