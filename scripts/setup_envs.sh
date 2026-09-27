#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Compatibility shortcut; the cross-platform entry is `conda env create`.
WITH_CNV=0
WITH_DEV=0
WITH_VCT=0
for arg in "$@"; do
    case "$arg" in
        --pipeline-only) ;;
        --with-cnv) WITH_CNV=1 ;;
        --with-dev) WITH_DEV=1 ;;
        --with-vct) WITH_VCT=1 ;;
        *) echo "Usage: $0 [--with-cnv] [--with-dev] [--with-vct]" >&2; exit 2 ;;
    esac
done
cd "$ROOT"
conda env create --file environment.yml
EXTRA_REQUIREMENTS=()
CHECKS=(--suite environment)
if [ "$WITH_CNV" = 1 ]; then
    EXTRA_REQUIREMENTS+=(-r 03_pipeline/requirements-cnv.txt)
    CHECKS+=(--with-cnv)
fi
if [ "$WITH_DEV" = 1 ]; then
    EXTRA_REQUIREMENTS+=(-r 03_pipeline/requirements-dev.txt)
    CHECKS+=(--with-dev)
fi
if [ "${#EXTRA_REQUIREMENTS[@]}" -gt 0 ]; then
    conda run -n virtual-screening python -m pip install "${EXTRA_REQUIREMENTS[@]}"
fi
conda run -n virtual-screening python scripts/test_pipeline.py "${CHECKS[@]}"
if [ "$WITH_VCT" = 1 ]; then
    conda env create --file environment-vct.yml
    conda run -n virtual-cell python -m pip check
fi
echo "Ready. Run: conda activate virtual-screening"
