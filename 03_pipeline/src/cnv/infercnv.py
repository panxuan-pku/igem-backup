#!/usr/bin/env python3
"""Load 10x samples, normalize, order by genomic position, run infercnvpy,
and build the per-window CNV signal table consumed by segments.py.

infercnvpy/scanpy are OPTIONAL dependencies — this module raises a clear
error telling you the `uv run --with` invocation if they are missing.
"""
import numpy as np
import pandas as pd

from .gene_order import CHROM_ORDER


def _import_deps():
    try:
        import anndata  # noqa: F401
        import infercnvpy as cnv
        import scanpy as sc
    except ImportError as e:
        raise ImportError(
            "scanpy/infercnvpy not installed. Run this step with: "
            "uv run --with scanpy --with infercnvpy --with matplotlib "
            "python -m src.cnv.workflow infercnv --config config/cnv.yaml"
        ) from e
    return sc, cnv


def load_samples(sample_specs, min_genes=200, max_mito_pct=20.0,
                 downsample=None, seed=0):
    """Read per-sample 10x mtx dirs → one AnnData with obs[sample|group] and layers['counts'].

    sample_specs: [{id, group, path}] — path must contain matrix.mtx[.gz],
    barcodes.tsv[.gz], genes.tsv[.gz] (standard 10x layout).
    """
    sc, _ = _import_deps()
    import anndata

    rng = np.random.default_rng(seed)
    adatas = []
    for spec in sample_specs:
        ad = sc.read_10x_mtx(spec["path"], var_names="gene_symbols", cache=False)
        ad.var_names_make_unique()
        ad.obs["sample"] = spec["id"]
        ad.obs["group"] = spec["group"]
        sc.pp.filter_cells(ad, min_genes=min_genes)
        ad.var["mt"] = ad.var_names.str.upper().str.startswith("MT-")
        sc.pp.calculate_qc_metrics(ad, qc_vars=["mt"], inplace=True, percent_top=None)
        ad = ad[ad.obs["pct_counts_mt"] < max_mito_pct].copy()
        if downsample and ad.n_obs > downsample:
            keep = rng.choice(ad.n_obs, size=downsample, replace=False)
            ad = ad[np.sort(keep)].copy()
        ad.layers["counts"] = ad.X.copy()
        adatas.append(ad)
    adata = anndata.concat(adatas, join="outer", fill_value=0)
    adata.obs_names_make_unique()
    return adata


def normalize_for_cnv(adata, target_sum=1e4):
    """Library-size normalize + log1p into .X (raw counts stay in layers['counts'])."""
    sc, _ = _import_deps()
    sc.pp.normalize_total(adata, target_sum=target_sum)
    sc.pp.log1p(adata)
    return adata


def order_by_position(adata, genes_df):
    """Restrict to genes with genomic positions and sort by (chrom, start).

    Sets adata.var['chromosome'|'start'|'end'] as infercnvpy expects.
    genes_df: output of gene_order.parse_gtf_genes.
    """
    pos = (genes_df.drop_duplicates("gene_name")
           .set_index("gene_name")[["chrom", "start", "end"]])
    names = pd.Index(adata.var_names.astype(str))
    sub = adata[:, names.isin(pos.index)].copy()
    sub.var["chromosome"] = pos.loc[sub.var_names, "chrom"].to_numpy()
    sub.var["start"] = pos.loc[sub.var_names, "start"].to_numpy()
    sub.var["end"] = pos.loc[sub.var_names, "end"].to_numpy()
    rank = {c: i for i, c in enumerate(CHROM_ORDER)}
    order = (sub.var.assign(_r=sub.var["chromosome"].map(rank))
             .sort_values(["_r", "start"]).index)
    sub = sub[:, order].copy()
    return sub


def run_infercnv(adata, reference_key="group", reference_cat="reference",
                 window_size=100, step=10, exclude_chromosomes=("chrX", "chrY")):
    """Run infercnvpy; result lands in adata.obsm['X_cnv'] (cells × windows).

    chrX/chrY are excluded by default (sex-chromosome dosage dominates the
    signal otherwise) — MUST match window_table()'s exclusion."""
    _, cnv = _import_deps()
    cnv.tl.infercnv(adata, reference_key=reference_key,
                    reference_cat=[reference_cat] if isinstance(reference_cat, str) else reference_cat,
                    window_size=window_size, step=step,
                    exclude_chromosomes=list(exclude_chromosomes) if exclude_chromosomes else None)
    return adata


def window_table(adata, window_size, step, group_col="group",
                 patient_cat="patient", ref_cat="reference",
                 exclude_chromosomes=("chrX", "chrY")):
    """Reconstruct window→gene mapping and aggregate the CNV signal.

    Returns DataFrame[chr, start, end, genes, score, ref_score] with one row
    per smoothed window; `score` = mean X_cnv over patient cells, `ref_score`
    = mean over reference cells (sanity check, should hover near 0).

    The window layout must match infercnvpy's definition: per chromosome,
    window i covers ordered genes [i*step, i*step + window_size). A hard
    assertion guards against silent mismatch if infercnvpy changes this.
    """
    if "X_cnv" not in adata.obsm:
        raise ValueError("adata.obsm['X_cnv'] missing — run run_infercnv first")
    X = adata.obsm["X_cnv"]
    X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)
    var = adata.var

    rows, w = [], 0
    excluded = set(exclude_chromosomes or ())
    for chrom in [c for c in CHROM_ORDER
                  if (var["chromosome"] == c).any() and c not in excluded]:
        sub = var[var["chromosome"] == chrom]
        n_genes = len(sub)
        n_win = (n_genes - window_size) // step + 1
        for i in range(max(n_win, 0)):
            g = sub.iloc[i * step: i * step + window_size]
            rows.append({"chr": chrom, "start": int(g["start"].min()),
                         "end": int(g["end"].max()),
                         "genes": ",".join(map(str, g.index)), "win_idx": w + i})
        w += max(n_win, 0)
    if w != X.shape[1]:
        raise RuntimeError(
            f"reconstructed {w} windows but X_cnv has {X.shape[1]} — infercnvpy "
            f"window layout differs from (i*step, window_size) or exclude_chromosomes "
            f"mismatch between run_infercnv() and window_table()"
        )

    tab = pd.DataFrame(rows).set_index("win_idx").sort_index()
    groups = adata.obs[group_col].astype(str)
    pat = (groups == str(patient_cat)).to_numpy()
    ref = (groups == str(ref_cat)).to_numpy()
    if pat.sum() == 0 or ref.sum() == 0:
        raise ValueError(f"{group_col!r} lacks {patient_cat!r} or {ref_cat!r} cells")
    tab["score"] = X[pat].mean(axis=0)
    tab["ref_score"] = X[ref].mean(axis=0)
    return tab.reset_index(drop=True)
