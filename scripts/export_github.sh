#!/usr/bin/env bash
# Make a source-first GitHub export without public raw data or regenerable caches.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/09_github_export}"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd -P)"
case "$DEST" in
  "$ROOT"|"$ROOT/") echo "Refusing to export over source tree" >&2; exit 2 ;;
esac
if [ -n "$(ls -A "$DEST")" ]; then
  echo "Destination is not empty: $DEST" >&2
  exit 2
fi
EXCLUDE_DEST=()
case "$DEST" in
  "$ROOT"/*) EXCLUDE_DEST=(--exclude="/${DEST#"$ROOT"/}/") ;;
esac
rsync -a \
  "${EXCLUDE_DEST[@]}" \
  --exclude='.git/' --exclude='.venv/' --exclude='__pycache__/' \
  --exclude='.pytest_cache/' --exclude='.mplconfig/' --exclude='.mplconfig_repro/' \
  --exclude='.playwright-browsers/' --exclude='test_artifacts/' \
  --exclude='.DS_Store' --exclude='*.log' \
  --exclude='/07_independent_reproduction_20260916/' \
  --exclude='/08_gitlab_export/' --exclude='/09_github_export/' \
  --exclude='/01_disease-22q11.2/data/' \
  --exclude='/02_disease-williams/01_rawdata/' \
  --exclude='/02_disease-williams/03_intermediate/processed.h5ad' \
  --exclude='/03_pipeline/data/scrna/GSE283473/' \
  --exclude='/03_pipeline/outputs/cnv/cnv_input.h5ad' \
  --exclude='/03_pipeline/outputs_repro/' \
  --exclude='/05_tools/SIGnature/model_files/model_files.tar.gz' \
  --exclude='/05_tools/VirtualCellTool/gears_data/norman/' \
  --exclude='/05_tools/VirtualCellTool/gears_data/norman.zip' \
  --exclude='/05_tools/VirtualCellTool/data/ms_attribution_fp16.npy' \
  --exclude='/05_tools/VirtualCellTool/data/cipher_*.npz' \
  "$ROOT/" "$DEST/"
python3 "$DEST/scripts/check_release.py" --root "$DEST"
echo "GitHub export: $DEST"
echo "Install Git LFS before git add; verify LFS tracking before pushing."
