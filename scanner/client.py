# -*- coding: utf-8 -*-
"""HTTP client — session and data exchange with signed proxy."""
import http.client
import json
import platform
import ssl
from urllib.parse import urlparse

_TIMEOUT = 20
_RETRIES = 3
_UA = "curl/8.5.0"


def _request(hostname: str, path: str, body: bytes, timeout: int) -> dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    conn = http.client.HTTPSConnection(hostname, 443, context=ctx, timeout=timeout)
    conn.request("POST", path, body=body, headers={
        "Content-Type": "application/json",
        "User-Agent": _UA,
    })
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return json.loads(data)


def _send(url: str, data=None, timeout: int = _TIMEOUT) -> dict:
    body = json.dumps(data).encode() if data else b""
    parsed = urlparse(url)
    last_err = None
    for _ in range(_RETRIES):
        try:
            return _request(parsed.hostname, parsed.path or "/", body, timeout)
        except Exception as e:
            last_err = e
    raise ConnectionError(f"Request failed after retries: {last_err}")


def connect(endpoint: str) -> dict:
    return _send(endpoint.rstrip("/") + "/api/v1/auth/session", timeout=15)


def fetch(endpoint: str, payload: dict) -> dict:
    return _send(endpoint.rstrip("/") + "/api/v1/data/sync", data=payload, timeout=30)
