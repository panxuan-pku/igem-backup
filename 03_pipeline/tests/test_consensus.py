"""Tests for consensus scoring."""
from src.consensus import score_row

WEIGHTS = {"clinGen_hi_score": 3, "gnomad_pLI": 2, "gnomad_LOEUF": 2}

def test_score_weights():
    row = {"clinGen_hi_score": 3, "gnomad_pLI": "0.95", "gnomad_LOEUF": "0.30"}
    score, votes = score_row(row, WEIGHTS)
    assert score > 0
    assert any(v[0] == "clinGen_hi" for v in votes)

def test_stable_when_missing():
    row = {}
    score, votes = score_row(row, WEIGHTS)
    assert score == 0.0
    assert votes == []
