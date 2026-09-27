"""Offline failure/identity checks plus the real core CLI with synthetic inputs."""
import gzip
import importlib.util
from pathlib import Path
import subprocess
import sys
import zipfile

import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "run_quickstart.py"
spec = importlib.util.spec_from_file_location("quickstart", SCRIPT)
quickstart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quickstart)


@pytest.fixture
def inputs(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "hgnc_aliases.tsv").write_text(
        "hgnc_id\tsymbol\tensembl_gene_id\tstatus\nHGNC:1\tTEST_A\tENSG1\tApproved\n"
        "HGNC:2\tTEST_B\tENSG2\tApproved\n")
    (sources / "clinGen_gene_curation_list_GRCh38.tsv").write_text(
        "#Gene Symbol\tHaploinsufficiency Score\tTriplosensitivity Score\nTEST_A\t3\t0\nTEST_B\t2\t0\n")
    (sources / "gnomad_constraint.tsv").write_text(
        "gene\tpLI\toe_lof_upper\nTEST_A\t0.9\t0.1\nTEST_B\t0.8\t0.2\n")
    (sources / "rna_tissue_consensus.tsv").write_text(
        "Gene name\tTissue\tnTPM\nTEST_A\tliver\t1\nTEST_B\tliver\t2\n")
    gtf = tmp_path / "genes.gtf.gz"
    start, end = quickstart.INTERVAL["start"], quickstart.INTERVAL["end"]
    with gzip.open(gtf, "wt") as f:
        for name, gid, left, right, kind in [
            ("TEST_A", "ENSG1", start - 10, start, "protein_coding"),
            ("TEST_B", "ENSG2", end, end + 10, "protein_coding"),
            ("OUTSIDE", "ENSG3", end + 1, end + 10, "protein_coding"),
            ("NONCODING", "ENSG4", start, end, "lncRNA"),
        ]:
            f.write(f'chr7\ttest\tgene\t{left}\t{right}\t.\t+\t.\tgene_id "{gid}.1"; '
                    f'gene_name "{name}"; gene_type "{kind}";\n')
    return tmp_path, sources, gtf


def test_interval_boundaries_and_core_run(inputs):
    output, sources, gtf = inputs
    candidates = quickstart.candidates_from_gtf(gtf, sources / "hgnc_aliases.tsv")
    assert candidates.gene_symbol.tolist() == ["TEST_A", "TEST_B"]
    ranked = quickstart.run_pipeline(output, sources, candidates)
    assert set(ranked.hgnc_id) == {"HGNC:1", "HGNC:2"}
    assert ranked.loc[ranked["rank"].eq(1), "input_symbol"].item() == "TEST_A"
    quickstart.write_report(output, ranked)
    assert "Control genes are empty" in (output / "report.html").read_text()


@pytest.mark.parametrize("problem", ["missing_id", "ambiguous_id", "duplicate_hgnc", "symbol_conflict"])
def test_identity_conflicts_fail_closed(inputs, problem):
    output, sources, gtf = inputs
    path = sources / "hgnc_aliases.tsv"
    hgnc = pd.read_csv(path, sep="\t")
    if problem == "missing_id":
        hgnc.loc[0, "ensembl_gene_id"] = "UNKNOWN"
    elif problem == "ambiguous_id":
        hgnc = pd.concat([hgnc, hgnc.iloc[[0]]])
    elif problem == "duplicate_hgnc":
        hgnc.loc[1, "hgnc_id"] = "HGNC:1"
    else:
        hgnc["symbol"] = ["TEST_B", "TEST_A"]
    hgnc.to_csv(path, sep="\t", index=False)
    with pytest.raises(ValueError):
        candidates = quickstart.candidates_from_gtf(gtf, path)
        quickstart.run_pipeline(output, sources, candidates)
    assert not (output / "ranked.csv").exists()
    assert not (output / "report.html").exists()


def test_invalid_reference_stops_before_ranking(inputs):
    output, sources, gtf = inputs
    candidates = quickstart.candidates_from_gtf(gtf, sources / "hgnc_aliases.tsv")
    (sources / "gnomad_constraint.tsv").write_text("wrong\theader\nx\ty\n")
    with pytest.raises(RuntimeError, match="merge_evidence"):
        quickstart.run_pipeline(output, sources, candidates)
    assert not (output / "ranked.csv").exists()


def test_existing_output_never_overwritten(tmp_path):
    marker = tmp_path / "keep.txt"
    marker.write_text("keep")
    result = subprocess.run([sys.executable, str(SCRIPT), "--output", str(tmp_path)], capture_output=True)
    assert result.returncode == 2
    assert marker.read_text() == "keep"
    assert list(tmp_path.iterdir()) == [marker]


def test_download_failure_removes_partial_and_retries(tmp_path, monkeypatch):
    import requests

    class Response:
        headers = {"Content-Length": "100"}
        url = "https://example.invalid/source"
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def raise_for_status(self):
            pass
        def iter_content(self, chunk_size):
            yield b"truncated"

    attempts = []
    def get(*args, **kwargs):
        attempts.append(1)
        return Response()
    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(quickstart.time, "sleep", lambda _: None)
    target = tmp_path / "data.tsv"
    with pytest.raises(ValueError, match="Incomplete download"):
        quickstart.download(Response.url, target)
    assert len(attempts) == 3
    assert not list(tmp_path.iterdir())


def test_archive_does_not_extract_unexpected_paths(tmp_path):
    raw, sources = tmp_path / "raw", tmp_path / "sources"
    raw.mkdir()
    sources.mkdir()
    for name in ("hgnc_aliases.tsv", "clinGen_gene_curation_list_GRCh38.tsv"):
        (raw / name).write_text("synthetic")
    with gzip.open(raw / "gnomad.tsv.bgz", "wb") as stream:
        stream.write(b"synthetic")
    with zipfile.ZipFile(raw / "hpa.zip", "w") as archive:
        archive.writestr("../escaped.txt", "unwanted")
    with pytest.raises(KeyError):
        quickstart.prepare_sources(raw, sources)
    assert not (tmp_path / "escaped.txt").exists()
