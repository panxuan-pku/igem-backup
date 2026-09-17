#!/usr/bin/env python3
"""
Normalize candidate gene symbols to HGNC IDs.

Reads input candidates.csv (one column 'gene_symbol'),
builds alias map from data/hgnc_aliases.tsv, and writes data/normalized.csv
with columns: hgnc_id, input_symbol, status.
"""
import argparse
from pathlib import Path
import pandas as pd
import sys

def load_alias_map(path):
    df = pd.read_csv(path, sep=None, engine="python", dtype=str)  # sniff , or \t
    df.columns = [c.strip() for c in df.columns]  # data files carry padded headers
    m = {}
    for _, row in df.iterrows():
        hg = row["hgnc_id"]
        for alias in str(row.get("symbol", "")).split(","):
            alias = alias.strip()
            if alias:
                m[alias.lower()] = hg
        for alias in str(row.get("prev_symbol", "")).split(";"):
            a = alias.strip()
            if a and a not in m:
                m[a.lower()] = hg
    return m

def resolve(df, alias_map):
    out = []
    for s in df["gene_symbol"]:
        st = s.strip()
        hid = alias_map.get(st.lower())
        status = "ok" if hid is not None else "unresolved"
        out.append({"hgnc_id": hid, "input_symbol": st, "status": status})
    return pd.DataFrame(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--hgnc-alias", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    if "gene_symbol" not in df.columns:
        df.columns = [c.strip() for c in df.columns]
        if len(df.columns) != 1:
            print("ERROR: candidates.csv must contain exactly one column 'gene_symbol'", file=sys.stderr)
            sys.exit(2)
        df = df.rename(columns={df.columns[0]: "gene_symbol"})

    alias_map = load_alias_map(args.hgnc_alias)
    norm = resolve(df, alias_map)

    unresolved = (norm["status"] == "unresolved").mean()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    norm.to_csv(args.out, index=False)
    print(f"wrote {args.out}: {len(norm)} genes, unresolved {unresolved:.1%}")

    if unresolved > 0.1:
        print("WARN: >10% candidate genes unresolved — check input symbols vs HGNC", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
