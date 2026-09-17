"""Tests for normalize.py"""
import pandas as pd
from src.normalize import load_alias_map, resolve

def test_resolve_ok_and_unresolved(tmp_path):
    alias = tmp_path / "aliases.tsv"
    alias.write_text("hgnc_id,symbol,prev_symbol\nHGNC:1,KCTD13,\nHGNC:2,TBX1,\n")
    m = load_alias_map(str(alias))
    df = pd.DataFrame({"gene_symbol": ["KCTD13", "TBX1", "NOT_A_GENE"]})
    out = resolve(df, m)
    assert len(out) == 3
    assert out.iloc[0]["hgnc_id"] == "HGNC:1"
    assert out.iloc[2]["status"] == "unresolved"
