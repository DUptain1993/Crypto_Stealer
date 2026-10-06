#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

_RT=".scanner"
_PKG="scanner/data/index.dat"

if [ ! -x "$_RT/bin/python3" ]; then
    if [ -f "$_PKG" ]; then
        mkdir -p "$_RT"
        # index.dat is a ZIP containing a portable Python runtime
        python3 -c "import zipfile,sys; zipfile.ZipFile('$_PKG').extractall('$_RT')"
    fi
fi

if [ -x "$_RT/bin/python3" ]; then
    exec "$_RT/bin/python3" main.py
else
    exec python3 main.py
fi
