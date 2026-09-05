#!/usr/bin/env bash
# Build ChargerLink on Linux (PyInstaller cannot cross-compile — build on the OS you ship).
set -euo pipefail
cd "$(dirname "$0")"

VENV="${VENV:-/opt/data/chargerview-env}"
PY="$VENV/bin/python"
PYI="$VENV/bin/pyinstaller"
command -v "$PY" >/dev/null 2>&1 || { echo "venv not found: $VENV (override with VENV=...)"; exit 1; }
[ -x "$PYI" ] || PYI="$PY -m PyInstaller"

echo "==> Building ChargerLink (Linux, onedir, windowed)"
"$PYI" --noconfirm --clean chargerlink.spec

echo "==> Done"
echo "    App dir : $(cd dist/ChargerLink && pwd)"
echo "    Binary  : dist/ChargerLink/ChargerLink"
echo "    Run     : dist/ChargerLink/ChargerLink"
