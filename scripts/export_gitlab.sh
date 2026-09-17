#!/usr/bin/env bash
# Make a clean, self-contained source tree suitable for creating a GitLab repo.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/08_gitlab_export}"
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
  --exclude='/08_gitlab_export/' \
  --exclude='/03_pipeline/outputs_repro/' \
  --exclude='/03_pipeline/data/scrna/GSE283473/CTRL1/' \
  --exclude='/03_pipeline/data/scrna/GSE283473/WS1/' \
  --exclude='/03_pipeline/data/scrna/GSE283473/CTRL1_repro/' \
  --exclude='/03_pipeline/data/scrna/GSE283473/WS1_repro/' \
  "$ROOT/" "$DEST/"
python3 "$DEST/scripts/check_release.py" --root "$DEST"
echo "Clean export: $DEST"
