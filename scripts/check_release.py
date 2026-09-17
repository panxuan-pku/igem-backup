#!/usr/bin/env python3
"""Read-only checks for a GitHub source export/clone (stdlib only)."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


REQUIRED = (
    "README.md",
    "scripts/setup_envs.sh",
    "03_pipeline/requirements-test.txt",
    "03_pipeline/config/pipeline.yaml",
    "03_pipeline/input/candidates.csv",
    "03_pipeline/input/candidates_whs.csv",
    "03_pipeline/input/controls_wbs.txt",
    "03_pipeline/data/hgnc_aliases.tsv",
    "03_pipeline/data/clinGen_gene_curation_list_GRCh38.tsv",
    "03_pipeline/data/gnomad_constraint.tsv",
    "03_pipeline/data/rna_tissue_consensus.tsv",
    "03_pipeline/data/gencode.v44.basic.annotation.gtf.gz",
    "03_pipeline/outputs/ai_scores.csv",
    "03_pipeline/src/normalize.py",
    "03_pipeline/src/merge_evidence.py",
    "03_pipeline/src/consensus_v2.py",
    "05_tools/VirtualCellTool/requirements-web.txt",
    "05_tools/VirtualCellTool/tests_api.py",
    "05_tools/VirtualCellTool/tests_e2e_playwright.py",
    "05_tools/VirtualCellTool/src/paths.py",
    "05_tools/VirtualCellTool/web/app.py",
    "05_tools/VirtualCellTool/web/index.html",
    "05_tools/VirtualCellTool/web/plotly.min.js",
    "05_tools/VirtualCellTool/data/expr_aligned.npz",
    "05_tools/VirtualCellTool/data/embeddings.npy",
    "05_tools/VirtualCellTool/data/meta.csv",
    "05_tools/VirtualCellTool/data/ms_expr.npz",
    "05_tools/VirtualCellTool/data/ms_embeddings.npy",
    "05_tools/VirtualCellTool/data/ms_web_meta.csv",
    "05_tools/VirtualCellTool/data/ws_expr.npz",
    "05_tools/VirtualCellTool/data/ws_embeddings.npy",
    "05_tools/VirtualCellTool/data/ws_web_meta.csv",
    "05_tools/VirtualCellTool/data/umap.npy",
    "05_tools/VirtualCellTool/data/ms_umap.npy",
    "05_tools/VirtualCellTool/data/ws_umap.npy",
    "05_tools/VirtualCellTool/gears_ckpt/model.pt",
    "05_tools/VirtualCellTool/gears_ckpt/config.pkl",
    "05_tools/SIGnature/src/SIGnature/__init__.py",
    "05_tools/SIGnature/model_files/model_files/scimilarity/encoder.ckpt",
    "05_tools/SIGnature/model_files/model_files/scimilarity/gene_order.tsv",
)
OPTIONAL_REQUIRED = (
    "03_pipeline/data/scrna/GSE283473/GSM8663068_CTRL1_barcodes.tsv.gz",
    "03_pipeline/data/scrna/GSE283473/GSM8663068_CTRL1_genes.tsv.gz",
    "03_pipeline/data/scrna/GSE283473/GSM8663068_CTRL1_matrix.mtx.gz",
    "03_pipeline/data/scrna/GSE283473/GSM8663071_WS1_barcodes.tsv.gz",
    "03_pipeline/data/scrna/GSE283473/GSM8663071_WS1_genes.tsv.gz",
    "03_pipeline/data/scrna/GSE283473/GSM8663071_WS1_matrix.mtx.gz",
    "05_tools/VirtualCellTool/gears_data/norman/perturb_processed.h5ad",
)
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mplconfig", ".playwright-browsers", "test_artifacts", "outputs_repro", "07_independent_reproduction_20260916", "08_gitlab_export", "09_github_export"}
LFS_SUFFIXES = {".h5ad", ".npy", ".npz", ".pkl", ".pt", ".ckpt", ".parquet", ".gz", ".zip"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--with-optional-data", action="store_true", help="also require downloaded GEO and GEARS inputs")
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []

    required = REQUIRED + (OPTIONAL_REQUIRED if args.with_optional_data else ())
    for rel in required:
        path = root / rel
        if not path.is_file():
            errors.append(f"missing: {rel}")
            continue
        with path.open("rb") as handle:
            if handle.read(40).startswith(b"version https://git-lfs.github.com/spec"):
                errors.append(f"Git LFS pointer, content not downloaded: {rel}")
        if path.stat().st_size == 0:
            errors.append(f"empty: {rel}")

    for current, dirs, files in os.walk(root, followlinks=False):
        base = Path(current)
        for name in list(dirs) + files:
            path = base / name
            rel = path.relative_to(root)
            if name == ".git" and base != root:
                errors.append(f"nested Git metadata: {rel}")
            if path.is_symlink():
                target = path.resolve()
                if not target.is_relative_to(root) or not target.exists():
                    errors.append(f"external or broken symlink: {rel} -> {target}")
            elif path.is_file() and path.suffix.lower() in LFS_SUFFIXES:
                with path.open("rb") as handle:
                    if handle.read(40).startswith(b"version https://git-lfs.github.com/spec"):
                        errors.append(f"Git LFS pointer, content not downloaded: {rel}")
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS and not (base / name).is_symlink()]

    if errors:
        print(f"Release check failed ({len(errors)} findings):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Release check passed: {len(required)} required files present, no pointers or escaping links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
