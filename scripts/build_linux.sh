#!/usr/bin/env bash
# Genera un binario one-file en dist/taxos (Linux).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -e ".[build]"
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name taxos \
  --paths src \
  --collect-data taxos \
  --hidden-import taxos.gui.wizard \
  src/taxos/cli.py

echo "Binario: $ROOT/dist/taxos"
