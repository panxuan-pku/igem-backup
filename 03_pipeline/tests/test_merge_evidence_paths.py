"""Regression tests for data-source resolution and missing-source failures."""

import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _command(normalized, output, audit, data_dir):
    return [
        sys.executable, "-m", "src.merge_evidence",
        "--normalized", str(normalized),
        "--config", str(ROOT / "config" / "pipeline.yaml"),
        "--out", str(output),
        "--audit", str(audit),
        "--data-dir", str(data_dir),
    ]


def test_nested_audit_does_not_change_data_source(tmp_path):
    normalized = tmp_path / "normalized.csv"
    pd.DataFrame([{"hgnc_id": "HGNC:12766", "input_symbol": "NSD2"}]).to_csv(normalized, index=False)
    output = tmp_path / "nested" / "evidence.parquet"
    audit = tmp_path / "nested" / "deep" / "audit"
    output.parent.mkdir()
    result = subprocess.run(
        _command(normalized, output, audit, ROOT / "data"),
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    frame = pd.read_parquet(output)
    assert len(frame) == 1
    assert frame.loc[0, "input_symbol"] == "NSD2"
    assert pd.notna(frame.loc[0, "gnomad_pLI"])
    assert "clinGen_hi_score" in frame.columns
    assert (audit / "data_checksums.txt").exists()


def test_missing_sources_fail_before_output(tmp_path):
    normalized = tmp_path / "normalized.csv"
    pd.DataFrame([{"hgnc_id": "HGNC:12766", "input_symbol": "NSD2"}]).to_csv(normalized, index=False)
    output = tmp_path / "evidence.parquet"
    audit = tmp_path / "audit"
    result = subprocess.run(
        _command(normalized, output, audit, tmp_path / "empty"),
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "missing required evidence files" in result.stderr
    assert not output.exists()
    assert not audit.exists()
