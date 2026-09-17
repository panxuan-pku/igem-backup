#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${IGEM_PYTHON:-python3.11}"

"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 11), "Python 3.11 required"'

"$PYTHON" -m venv "$ROOT/.venv/pipeline"
"$ROOT/.venv/pipeline/bin/python" -m pip install -r "$ROOT/03_pipeline/requirements-test.txt"

"$PYTHON" -m venv "$ROOT/.venv/vct"
"$ROOT/.venv/vct/bin/python" -m pip install -r "$ROOT/05_tools/VirtualCellTool/requirements-web.txt"

"$ROOT/.venv/pipeline/bin/python" -c 'import pandas, pyarrow, yaml, pytest; print("pipeline environment ready")'
mkdir -p "$ROOT/05_tools/VirtualCellTool/.mplconfig"
MPLCONFIGDIR="$ROOT/05_tools/VirtualCellTool/.mplconfig" "$ROOT/.venv/vct/bin/python" -c 'import fastapi, torch, scanpy, captum, gears; print("VirtualCellTool environment ready")'
echo "Environments created in $ROOT/.venv/"
