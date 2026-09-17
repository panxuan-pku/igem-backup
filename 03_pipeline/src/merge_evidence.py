#!/usr/bin/env python3
"""
Merge evidence from ClinGen, gnomAD, and HPA into evidence.parquet.
Also computes checksums for data files into audit dir.
"""
import argparse
import pandas as pd
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DATA_FILES = (
    "hgnc_aliases.tsv",
    "clinGen_gene_curation_list_GRCh38.tsv",
    "gnomad_constraint.tsv",
    "rna_tissue_consensus.tsv",
)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def join_on_hgnc(base, evidence, src_cols, name, symbol_map=None, skiprows=0):
    ev = pd.read_csv(evidence, sep="\t", dtype=str, skiprows=skiprows)
    ev.columns = [c.strip().lower().lstrip('#') for c in ev.columns]
    # Drop duplicate columns (keep first) — ClinGen has repeated PMID headers
    ev = ev.loc[:, ~ev.columns.duplicated()]
    if "hgnc_id" not in ev.columns:
        for alt in ["hgnc id", "hgncid", "gene_id", "hgncid", "gene symbol", "gene"]:
            if alt in ev.columns:
                ev = ev.rename(columns={alt: "hgnc_id"})
                break
    if "hgnc_id" not in ev.columns:
        raise ValueError(f"{name}: no hgnc_id column")
    # Map gene symbols to HGNC IDs if needed
    if symbol_map is not None and name == "clinGen":
        ev["hgnc_id"] = ev["hgnc_id"].str.upper().map(symbol_map)
        matched = ev["hgnc_id"].notna().sum()
        print(f"{name}: mapped {matched}/{len(ev)} symbols to HGNC ID")
        ev = ev[ev["hgnc_id"].notna()]
        # ClinGen uses scores 0,1,2,3,30,40
        # v2.1: preserve original score for annotation, create clean scoring column
        for col in ["haploinsufficiency score", "triplosensitivity score"]:
            if col in ev.columns:
                ev[col] = pd.to_numeric(ev[col], errors="coerce")
                # Preserve raw score before cleaning
                ev[col.replace(" score", "_raw")] = ev[col].copy()
                # 30="recessive disease association" -> neutral for haploinsufficiency
                # 40="no evidence" -> neutral
                # NULL=not curated -> neutral (v2.1: don't penalize unstudied genes)
                ev.loc[ev[col].isin([30, 40]) | ev[col].isna(), col] = pd.NA
    # gnomAD uses gene symbols directly; match on hgnc_id after symbol resolution
    # (fix: input symbols like NSD2 never matched gnomAD's historical symbol WHSC1,
    #  silently dropping the strongest constraint evidence for renamed genes)
    if name == "gnomad_constraint":
        # ev has 'gene' column, not 'hgnc_id' — rename it
        if "gene" in ev.columns:
            ev = ev.rename(columns={"gene": "gene_symbol"})
        # Keep only pLI and LOEUF columns
        keep = ["gene_symbol"] + [c for c in ["pli", "oe_lof_upper"] if c in ev.columns]
        ev = ev[keep]
        # Resolve symbols (incl. prev_symbol/alias) to HGNC ID, then merge on hgnc_id
        ev["gene_symbol"] = ev["gene_symbol"].str.strip().str.upper()
        if symbol_map is not None:
            ev["hgnc_id"] = ev["gene_symbol"].map(symbol_map)
            matched = ev["hgnc_id"].notna().sum()
            print(f"gnomAD: resolved {matched}/{len(ev)} symbols to HGNC ID")
            ev = ev[ev["hgnc_id"].notna()].drop_duplicates("hgnc_id")
        ev.columns = ["gene_symbol", "gnomad_pLI", "gnomad_LOEUF"] + (["hgnc_id"] if "hgnc_id" in ev.columns else [])
        # gnomAD uses 'NA' for missing values
        ev = ev.replace('NA', pd.NA)
        # Also handle empty strings
        ev = ev.replace('', pd.NA)
        if "hgnc_id" in ev.columns:
            merged = base.merge(ev[["hgnc_id", "gnomad_pLI", "gnomad_LOEUF"]], on="hgnc_id", how="left")
        else:
            # fallback: legacy exact-symbol match
            merged = base.merge(ev, left_on="input_symbol", right_on="gene_symbol", how="left")
        matched = merged["gnomad_pLI"].notna().sum()
        print(f"gnomAD: matched {matched}/{len(base)} candidates")
        return merged
    # Rename evidence columns to standard names
    col_rename = {
        "haploinsufficiency score": "clinGen_hi_score",
        "triplosensitivity score": "clinGen_triplo_score",
        "pli": "gnomad_pLI",
        "oe_lof_upper": "gnomad_LOEUF",  # gnomAD v2.1.1 uses oe_lof_upper as LOEUF
        "rna_expression_score": "hpa_expr",
    }
    ev = ev.rename(columns={k: v for k, v in col_rename.items() if k in ev.columns})
    cols = ["hgnc_id"] + [c for c in col_rename.values() if c in ev.columns]
    if not cols:
        raise ValueError(f"{name}: none of {list(col_rename.values())} present")
    return base.merge(ev[cols], on="hgnc_id", how="left")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audit", required=True)
    ap.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data",
                    help="evidence input directory (default: <pipeline>/data)")
    args = ap.parse_args()

    norm = pd.read_csv(args.normalized)
    if "hgnc_id" not in norm.columns:
        raise ValueError("normalized.csv must contain hgnc_id")

    base = norm[["hgnc_id", "input_symbol"]].drop_duplicates()

    # Load config for HPA organs
    import yaml
    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    
    src_dir = args.data_dir.resolve()
    missing = [name for name in REQUIRED_DATA_FILES if not (src_dir / name).is_file()]
    if missing:
        ap.error(f"missing required evidence files in {src_dir}: {', '.join(missing)}")
    audit_dir = Path(args.audit)
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Build symbol→HGNC ID map for ClinGen (which uses gene symbols, not HGNC IDs)
    symbol_map = {}
    alias = pd.read_csv(src_dir / "hgnc_aliases.tsv", sep="\t", dtype=str)
    alias.columns = [c.strip() for c in alias.columns]  # data files carry padded headers
    for _, row in alias.iterrows():
        hg = row.get("hgnc_id")
        if not hg:
            continue
        for sym_col in ["symbol", "prev_symbol", "alias_symbol"]:
            for s in str(row.get(sym_col, "")).split(","):
                s = s.strip().upper()
                if s and s not in symbol_map:
                    symbol_map[s] = hg
    
    checks = {}
    for src_name, f, skip in [
        ("clinGen", "clinGen_gene_curation_list_GRCh38.tsv", 5),
        ("gnomad_constraint", "gnomad_constraint.tsv", 0),
    ]:
        p = src_dir / f
        checks[f] = sha256_file(p)
        joined = join_on_hgnc(base, p, [
            "hgnc_id", "haploinsufficiency score", "triplosensitivity score",
            "pli", "oe_lof_upper"
        ], src_name, symbol_map=symbol_map, skiprows=skip)
        base = joined
    
    # HPA needs special handling: wide format (Gene, Tissue, nTPM) → pivot to hpa_{organ}_expr
    p = src_dir / "rna_tissue_consensus.tsv"
    checks[str(p)] = sha256_file(p)
    hpa = pd.read_csv(p, sep="\t", dtype=str)
    hpa.columns = [c.strip().lower() for c in hpa.columns]
    # Map gene symbols to HGNC ID
    hpa["hgnc_id"] = hpa["gene name"].str.upper().map(symbol_map)
    hpa = hpa[hpa["hgnc_id"].notna()]
    # Pivot to wide format
    hpa_wide = hpa.pivot_table(index="hgnc_id", columns="tissue", values="ntpm", aggfunc="first")
    hpa_wide.columns = [f"hpa_{c.lower().replace(' ', '_')}_expr" for c in hpa_wide.columns]
    hpa_wide = hpa_wide.reset_index()
    # Keep only organs we care about
    organs = cfg.get("hpa_filter", {}).get("organs", ["liver", "brain", "kidney", "gastrointestinal"])
    organ_cols = [f"hpa_{o}_expr" for o in organs]
    keep_cols = ["hgnc_id"] + [c for c in organ_cols if c in hpa_wide.columns]
    base = base.merge(hpa_wide[keep_cols], on="hgnc_id", how="left")
    print(f"hpa: joined {hpa_wide['hgnc_id'].notna().sum()} genes, organs: {[c for c in keep_cols if c != 'hgnc_id']}")
    
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    base.to_parquet(args.out, index=False)

    (audit_dir / "data_checksums.txt").write_text(
        "\n".join(f"{f}  {h}" for f, h in checks.items())
    )
    print(f"wrote {args.out} with {len(base)} rows")

if __name__ == "__main__":
    main()
