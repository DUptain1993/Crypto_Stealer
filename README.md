# Crypto Checker — Linux Edition

Multi-chain wallet balance checker with portfolio analytics, batch processing,
and export tooling. Console-driven, cross-platform Python.

## Features

- Multi-chain balance lookup (EVM, BTC, SOL, BSC, Polygon, Arbitrum)
- Batch address checking with async engine
- Portfolio analytics and USD aggregation
- Export to TXT / CSV / JSON / HTML
- Configurable RPC endpoints per chain
- Rich terminal UI

## Install

    pip install -r requirements.txt

## Run

    ./run.sh

or:

    python3 main.py

## Configuration

Edit `config.json`. RPC endpoints per chain under `rpc_endpoints`.
Export behaviour under `export`. Runtime sync settings under `system`.

## Build

    python3 build.py

Produces `dist/crypto_checker`.

## License

MIT.
