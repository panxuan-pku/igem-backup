#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${IGEM_PYTHON:-python3.11}"
PIPELINE_ONLY=false
case "${1:-}" in
  --pipeline-only) PIPELINE_ONLY=true ;;
  "") ;;
  *) echo "Usage: bash scripts/setup_envs.sh [--pipeline-only]" >&2; exit 2 ;;
esac
if [[ $# -gt 1 ]]; then
  echo "Usage: bash scripts/setup_envs.sh [--pipeline-only]" >&2
  exit 2
fi

"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 11), "Python 3.11 required"'

echo "Rebuilding project environments in $ROOT/.venv/"

"$PYTHON" -m venv --clear "$ROOT/.venv/pipeline"
"$ROOT/.venv/pipeline/bin/python" -m pip install -r "$ROOT/03_pipeline/requirements.txt"
"$ROOT/.venv/pipeline/bin/python" "$ROOT/scripts/test_pipeline.py" --suite environment

if [[ "$PIPELINE_ONLY" == false ]]; then
  "$PYTHON" -m venv --clear "$ROOT/.venv/vct"
  "$ROOT/.venv/vct/bin/python" -m pip install -r "$ROOT/05_virtual_cell/requirements-web.txt"

  mkdir -p "$ROOT/05_virtual_cell/.mplconfig"
  MPLCONFIGDIR="$ROOT/05_virtual_cell/.mplconfig" "$ROOT/.venv/vct/bin/python" -c 'import fastapi, torch, scanpy, captum, gears; print("VirtualCellTool environment ready")'
fi
echo "Clean environments created in $ROOT/.venv/"
