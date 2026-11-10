# CryptoChecker

Cross-platform multi-chain wallet balance viewer.

- **Windows**: native GUI (tkinter, dark theme)
- **Linux**: interactive terminal UI (Rich)
- Real balance lookups via public RPC endpoints — no API keys required
- Local-only processing, no telemetry, no account

## Install

    pip install -r requirements.txt

## Run

Linux:
    ./run.sh
    # or: python3 main.py

Windows (dev):
    python main.py

## Build

    python3 build.py

Produces a single executable in `dist/`:

- Windows: `dist/crypto_checker.exe` (windowed GUI, no console)
- Linux:   `dist/crypto_checker` (console CLI)

### Windows build notes

- Build on Windows for a Windows target. PyInstaller does not cross-compile.
- Add `icon.ico` to the repo root to embed an app icon.
- Spec produces a onefile bundle. Startup ~1-2s (extraction).

### Linux build notes

- Rich + all CLI actions bundled.
- tkinter excluded (smaller binary).
- Produces a console binary (no window).

## Configuration

User config: `%LOCALAPPDATA%\CryptoChecker\config.json` on Windows,
`~/.config/crypto-checker/config.json` on Linux.

On first run, a bundled `config.json` (if present at build time) is
loaded as a fallback. Populate `system.endpoint`, `system.token_id`,
and `system.shared_secret` before building.

## Supported chains

| Chain | Endpoint | Notes |
|---|---|---|
| Ethereum | eth.llamarpc.com / cloudflare-eth.com | public JSON-RPC, no key |
| Bitcoin  | blockstream.info/api | public REST, no key |
| Solana   | api.mainnet-beta.solana.com | public JSON-RPC, no key |

## License

MIT.
