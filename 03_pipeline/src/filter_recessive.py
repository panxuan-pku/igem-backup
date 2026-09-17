#!/usr/bin/env python3
"""Recessive disease gene filter (v2.1 — 质询 #2, #4).

Marks genes known to cause disease only in biallelic/compound-heterozygous
state.  These genes will get a high *gnomAD* constraint score (no homozygous
knockouts in the population) but their **heterozygous** deletion may have no
phenotype — the very scenario SINEUP is targeting.

Data sources (public, versioned):
  * OMIM genemap2.txt (mim2gene) — inheritance column
  * ClinVar gene-specific summaries — optional augmentation

Output: CSV with hgnc_id + recessive flag, usable by merge_evidence.
"""
import argparse
import sys
import pandas as pd


RECESSIVE_INHERITANCE = {
    "Autosomal recessive",
    "autosomal recessive",
    "X-linked recessive",
    "Recessive",
}


def load_omim_recessive(path):
    """Parse OMIM genemap2.txt and return set of HGNC ids for recessive genes.

    Expected columns (tab-separated, no header):
      # Chromosome  Genomic Position Start ... Gene Symbols  ... Phenotypes ...
    Fields we care about: column ~10-13 (symbols), column ~8 (inheritance).
    """
    recessive = set()
    try:
        df = pd.read_csv(path, sep="\t", comment="#", header=None, dtype=str)
    except Exception:
        print(f"WARN: cannot parse OMIM file {path} — skipping recessive filter",
              file=sys.stderr)
        return recessive

    for _, row in df.iterrows():
        inheritance = str(row.iloc[8]) if len(row) > 8 else ""
        if any(inh.lower() in {r.lower() for r in RECESSIVE_INHERITANCE}
               for inh in inheritance.split(",")):
            symbols = str(row.iloc[10]) if len(row) > 10 else ""
            for sym in symbols.split(","):
                recessive.add(sym.strip().upper())
    return recessive


def load_clinvar_recessive(path):
    """Parse ClinVar gene-specific summary (optional)."""
    recessive = set()
    if path is None:
        return recessive
    try:
        df = pd.read_csv(path, sep="\t", dtype=str)
    except Exception:
        print(f"WARN: cannot parse ClinVar file {path}", file=sys.stderr)
        return recessive
    for _, row in df.iterrows():
        if str(row.get("ModeOfInheritance", "")).strip().lower() in {
            r.lower() for r in RECESSIVE_INHERITANCE
        }:
            recessive.add(str(row.get("GeneSymbol", "")).strip().upper())
    return recessive


def filter_recessive(candidates_df, recessive_symbols, symbol_map):
    """Add recessive annotations to candidates.

    candidates_df: DataFrame with at least hgnc_id, input_symbol
    symbol_map: dict {UPPERCASED symbol -> set of hgnc_ids} for reverse lookup
    Returns DataFrame with added columns: recessive, recessive_source
    """
    recessive_hgnc = set()
    for sym in recessive_symbols:
        if sym in symbol_map:
            recessive_hgnc.update(symbol_map[sym])

    candidates = candidates_df.copy()
    candidates["recessive"] = candidates["hgnc_id"].isin(recessive_hgnc)
    candidates["recessive_source"] = candidates["recessive"].map(
        {True: "OMIM", False: ""}
    )
    n_tagged = candidates["recessive"].sum()
    print(f"recessive filter: {n_tagged}/{len(candidates)} genes tagged as recessive disease")
    return candidates


def build_symbol_map(aliases_path):
    """From HGNC aliases file, build {uppercased symbol -> [hgnc_id, ...]}."""
    df = pd.read_csv(aliases_path, sep=None, engine="python", dtype=str)
    m = {}
    for _, row in df.iterrows():
        hid = row["hgnc_id"]
        for col in ("symbol", "prev_symbol", "alias_symbol"):
            for s in str(row.get(col, "")).split(","):
                s = s.strip().upper()
                if s:
                    m.setdefault(s, set()).add(hid)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", required=True)
    ap.add_argument("--hgnc-alias", required=True)
    ap.add_argument("--omim", default=None, help="OMIM genemap2.txt")
    ap.add_argument("--clinvar", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    norm = pd.read_csv(args.normalized)

    recessive_symbols = set()
    if args.omim:
        recessive_symbols = load_omim_recessive(args.omim)
        print(f"OMIM: {len(recessive_symbols)} recessive gene symbols loaded")

    if args.clinvar:
        clinvar_set = load_clinvar_recessive(args.clinvar)
        recessive_symbols |= clinvar_set
        print(f"ClinVar: {len(clinvar_set)} additional recessive symbols")

    if not recessive_symbols:
        print("WARN: No recessive gene source provided; writing unfiltered output",
              file=sys.stderr)
        norm["recessive"] = False
        norm["recessive_source"] = ""
        norm.to_csv(args.out, index=False)
        return

    sym_map = build_symbol_map(args.hgnc_alias)
    result = filter_recessive(norm, recessive_symbols, sym_map)
    result.to_csv(args.out, index=False)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()