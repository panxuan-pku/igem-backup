#!/usr/bin/env python3
"""Download public references and rank a known Williams syndrome interval."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "03_pipeline"
sys.path.insert(0, str(PIPELINE))

# GeneReviews NBK1249, GRCh38, 1-based inclusive. This is a known interval,
# not a CNV inferred from expression and not the old project candidate snapshot.
INTERVAL = {"chrom": "chr7", "start": 73330452, "end": 74728172}
INTERVAL_SOURCE = "https://www.ncbi.nlm.nih.gov/books/NBK1249/"
SOURCES = {
    "hgnc_aliases.tsv": "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt",
    "clinGen_gene_curation_list_GRCh38.tsv": "https://ftp.clinicalgenome.org/ClinGen_gene_curation_list_GRCh38.tsv",
    "gnomad.tsv.bgz": "https://storage.googleapis.com/gcp-public-data--gnomad/release/2.1.1/constraint/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz",
    "hpa.zip": "https://v24.proteinatlas.org/download/tsv/rna_tissue_consensus.tsv.zip",
    "gencode.v44.basic.annotation.gtf.gz": "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/gencode.v44.basic.annotation.gtf.gz",
}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(url, path, *, progress=False):
    import requests

    partial = path.with_name(path.name + ".part")
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=(20, 60),
                              headers={"Accept-Encoding": "identity"}) as response:
                response.raise_for_status()
                downloaded, last_update = 0, time.monotonic()
                with partial.open("wb") as output:
                    for chunk in response.iter_content(1024 * 1024):
                        output.write(chunk)
                        downloaded += len(chunk)
                        if progress and time.monotonic() - last_update >= 10:
                            print(f"[INFO] {path.name}: {downloaded / 1024**2:.1f} MiB downloaded", flush=True)
                            last_update = time.monotonic()
                size = partial.stat().st_size
                expected = response.headers.get("Content-Length")
                if not size or (expected and size != int(expected)):
                    raise ValueError(f"Incomplete download: {path.name}")
                metadata = {"url": url, "resolved_url": response.url,
                            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                            "bytes": size, "sha256": sha256(partial)}
            partial.replace(path)
            return metadata
        except (requests.RequestException, ValueError):
            partial.unlink(missing_ok=True)
            if attempt == 2:
                raise
            print(f"[WARN] Retrying download {attempt + 1}/2: {path.name}", flush=True)
            time.sleep(2)


def prepare_sources(raw, sources):
    for name in ("hgnc_aliases.tsv", "clinGen_gene_curation_list_GRCh38.tsv"):
        shutil.copyfile(raw / name, sources / name)
    with gzip.open(raw / "gnomad.tsv.bgz", "rb") as stream:
        with (sources / "gnomad_constraint.tsv").open("wb") as output:
            shutil.copyfileobj(stream, output)
    # Read a single named member; never extract paths from a downloaded archive.
    with zipfile.ZipFile(raw / "hpa.zip") as archive:
        with archive.open("rna_tissue_consensus.tsv") as stream:
            with (sources / "rna_tissue_consensus.tsv").open("wb") as output:
                shutil.copyfileobj(stream, output)


def candidates_from_gtf(gtf, hgnc_path):
    import pandas as pd
    from src.cnv.gene_order import genes_in_interval, parse_gtf_genes

    genes = genes_in_interval(parse_gtf_genes(gtf), **INTERVAL)
    if genes.empty or genes.gene_id.duplicated().any():
        raise ValueError("No interval genes or duplicate gene IDs; check GENCODE annotation")
    hgnc = pd.read_csv(hgnc_path, sep="\t", dtype=str, keep_default_na=False)
    required = {"ensembl_gene_id", "hgnc_id", "symbol", "status"}
    if not required.issubset(hgnc.columns):
        raise ValueError(f"HGNC missing columns: {sorted(required - set(hgnc.columns))}")
    hgnc = hgnc[hgnc.status.eq("Approved") & hgnc.ensembl_gene_id.isin(genes.gene_id)]
    if hgnc.ensembl_gene_id.duplicated().any():
        raise ValueError("Candidate gene IDs have multiple HGNC matches; automatic merging is disabled")
    genes = genes.merge(hgnc[["ensembl_gene_id", "hgnc_id", "symbol"]],
                        left_on="gene_id", right_on="ensembl_gene_id", how="left", validate="one_to_one")
    unresolved = genes[genes.hgnc_id.isna() | genes.hgnc_id.eq("")]
    if not unresolved.empty:
        raise ValueError("Candidate IDs cannot be uniquely mapped to HGNC: " + ", ".join(unresolved.gene_id))
    if genes.hgnc_id.duplicated().any() or genes.gene_name.duplicated().any():
        raise ValueError("Conflicting candidate IDs or symbols; ranking requires unique identities")
    genes["gene_symbol"] = genes.gene_name
    genes["source"] = "GENCODE_v44_protein_coding_GRCh38"
    genes["deletion_id"] = "Williams_GeneReviews_interval"
    genes["candidate_provenance"] = [json.dumps([{
        "gene_id": row.gene_id, "hgnc_id": row.hgnc_id,
        "original_symbol": row.gene_name, "approved_symbol": row.symbol,
        "genome_build": "GRCh38", "interval_source": INTERVAL_SOURCE,
        **{"interval_" + k: v for k, v in INTERVAL.items()},
    }], ensure_ascii=False) for row in genes.itertuples()]
    return genes


def run_stage(output, module, args):
    log = output / (module.split(".")[-1] + ".log")
    command = [sys.executable, "-m", module, *map(str, args)]
    with log.open("w") as stream:
        stream.write(f"command: {command!r}\n")
        stream.flush()
        result = subprocess.run(command, cwd=PIPELINE, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"{module} failed; log: {log}\n" + log.read_text()[-3000:])


def run_pipeline(output, sources, candidates):
    import pandas as pd
    import yaml

    config = yaml.safe_load((PIPELINE / "config/pipeline.yaml").read_text())
    config["consensus_v2"]["tuning"].update(enabled=False, positive_controls=[])
    config["experiments"] = {"enabled": False}
    config["phenotype_panels"] = []
    config["pipeline_mode"] = "rank"
    config_path = output / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True))
    # HGNC ID is independently checked after the existing symbol normalizer.
    candidates.drop(columns=["hgnc_id", "symbol", "ensembl_gene_id"]).to_csv(output / "candidates.csv", index=False)
    run_stage(output, "src.normalize", ["--input", output / "candidates.csv", "--out", output / "normalized.csv",
              "--hgnc-alias", sources / "hgnc_aliases.tsv"])
    normalized = pd.read_csv(output / "normalized.csv")
    expected = dict(zip(candidates.gene_symbol, candidates.hgnc_id))
    if (len(normalized) != len(candidates) or normalized.hgnc_id.isna().any()
            or normalized.hgnc_id.duplicated().any()
            or not normalized.hgnc_id.eq(normalized.input_symbol.map(expected)).all()):
        raise ValueError("Symbol normalization conflicts with Ensembl-to-HGNC ID mapping; ranking stopped")
    run_stage(output, "src.merge_evidence", ["--normalized", output / "normalized.csv", "--config", config_path,
              "--data-dir", sources, "--out", output / "evidence.parquet", "--audit", output / "audit"])
    run_stage(output, "src.consensus_v2", ["--evidence", output / "evidence.parquet", "--config", config_path,
              "--mode", "rank", "--out", output / "ranked.csv", "--report", output / "report.md"])
    ranked = pd.read_csv(output / "ranked.csv")
    if set(ranked.hgnc_id) != set(candidates.hgnc_id) or len(ranked) != len(candidates):
        raise ValueError("Ranking did not retain all candidates; success report not generated")
    return ranked


def write_report(output, ranked):
    columns = [c for c in ("rank", "input_symbol", "hgnc_id", "consensus_score",
               "clinGen_haploinsufficiency_raw", "clinGen_haploinsufficiency_status",
               "gnomad_pLI", "gnomad_LOEUF") if c in ranked]
    coverage = {c: int(ranked[c].notna().sum()) for c in
                ("clinGen_hi_score", "gnomad_pLI", "gnomad_LOEUF")}
    labels = {"rank": "Rank", "input_symbol": "Gene", "hgnc_id": "HGNC ID",
              "consensus_score": "Consensus score", "clinGen_haploinsufficiency_raw": "Raw ClinGen HI category",
              "clinGen_haploinsufficiency_status": "ClinGen status",
              "gnomad_pLI": "gnomAD pLI", "gnomad_LOEUF": "gnomAD LOEUF"}
    table = ranked[columns].rename(columns=labels).copy()
    if "ClinGen status" in table:
        table["ClinGen status"] = table["ClinGen status"].replace({
            "not_curated": "Not curated", "not_evaluated": "Not evaluated", "no_evidence": "No evidence",
            "little_evidence": "Little evidence", "emerging_evidence": "Emerging evidence",
            "sufficient_evidence": "Sufficient evidence", "recessive_association": "Recessive association",
            "dosage_unlikely": "Dosage sensitivity unlikely"})
    text = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Williams screening results</title>
<style>body{{font:16px/1.7 system-ui;margin:32px auto;padding:0 20px;max-width:1100px;color:#243544}}
table{{border-collapse:collapse;font-size:14px}}td,th{{padding:8px;border:1px solid #ddd}}th{{background:#e7f2f2}}
.table{{overflow:auto}}a{{color:#086978}}.note{{background:#fff6e2;padding:16px}}</style>
<h1>Williams syndrome: screening results</h1><h2>1. Analysis scope</h2>
<p>GENCODE v44 was used to extract protein-coding genes overlapping GRCh38 chr7:73,330,452–74,728,172,
yielding {len(ranked)} candidates. IDs were verified against HGNC and ranked using ClinGen and gnomAD v2.1.1 evidence.
Interval source: <a href="{INTERVAL_SOURCE}">GeneReviews</a>. HPA v24.1 provides expression annotations without penalties.</p>
<p class="note">This is research prioritization within a known interval, not patient CNV detection, a pathogenicity diagnosis or treatment-effect prediction.
AI scores, single-cell expression inference and VCT are not used. Control genes are empty; weights were not tuned.
HGNC and ClinGen are updated; rankings may differ across dates.</p>
<h2>2. Reading the results</h2><p>Lower rank means higher priority; consensus_score is relative to this configuration,
not disease probability. Missing values indicate neither negative evidence nor safety. Raw ClinGen categories differ from scoring evidence:
30 means recessive association and 40 means dosage sensitivity unlikely; neither contributes a positive HI score.</p>
<p>Scorable evidence coverage: ClinGen {coverage['clinGen_hi_score']}/{len(ranked)},
gnomAD pLI {coverage['gnomad_pLI']}/{len(ranked)}, LOEUF {coverage['gnomad_LOEUF']}/{len(ranked)}.
Review the complete evidence and literature, not only the top three candidates.</p>
<div class="table">{table.to_html(index=False, na_rep="Missing", float_format=lambda v: f"{v:.4g}")}</div>
<h2>3. Files and provenance</h2><ul><li><a href="ranked.csv">Full ranking CSV</a> (including all annotations)</li>
<li><a href="candidates.csv">Generated candidates and sources</a></li><li><a href="report.md">Technical report</a></li>
<li><a href="manifest.json">Download URLs, timestamps, SHA256 and output checksums</a></li>
<li><a href="config.yaml">Run configuration</a></li></ul></html>"""
    (output / "report.html").write_text(text, encoding="utf-8")
    return coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new output directory; existing paths are never overwritten")
    args = parser.parse_args()
    output = (args.output or PIPELINE / "outputs_repro" /
              datetime.now().strftime("quickstart_williams_%Y%m%d_%H%M%S_%f")).resolve()
    if output.exists():
        parser.error(f"Output directory already exists; use a new directory: {output}")
    # Fail before network activity when run with the wrong interpreter.
    try:
        import pandas  # noqa: F401
        import pyarrow  # noqa: F401
        import requests  # noqa: F401
        import yaml  # noqa: F401
    except ImportError as error:
        parser.error(f"Missing dependency {error}; create the README environment, then conda activate virtual-screening")
    output.mkdir(parents=True)
    raw, sources = output / "downloads", output / "sources"
    raw.mkdir()
    sources.mkdir()
    manifest = {"status": "running", "interval": INTERVAL, "interval_source": INTERVAL_SOURCE,
                "genome_build": "GRCh38", "gene_type": "protein_coding", "downloads": {},
                "python": sys.version, "started_utc": datetime.now(timezone.utc).isoformat()}
    manifest_path = output / "manifest.json"
    start = time.monotonic()
    try:
        print(f"Output directory: {output}", flush=True)
        for i, (name, url) in enumerate(SOURCES.items(), 1):
            print(f"[1/4] Downloading {i}/{len(SOURCES)}: {name}", flush=True)
            manifest["downloads"][name] = download(url, raw / name)
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        prepare_sources(raw, sources)
        print("[2/4] Extracting interval candidates and checking unique gene IDs", flush=True)
        candidates = candidates_from_gtf(raw / "gencode.v44.basic.annotation.gtf.gz", sources / "hgnc_aliases.tsv")
        print(f"[3/4] Normalizing, merging evidence and ranking ({len(candidates)} candidates)", flush=True)
        ranked = run_pipeline(output, sources, candidates)
        manifest["coverage"] = write_report(output, ranked)
        manifest.update(status="success", candidates=len(candidates), elapsed_seconds=round(time.monotonic() - start, 2))
        manifest["generated_sha256"] = {str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob("*"))
                                       if p.is_file() and p != manifest_path and raw not in p.parents}
        print(f"[4/4] Complete. Open in a browser: {(output / 'report.html').as_uri()}", flush=True)
        return 0
    except Exception as error:
        manifest.update(status="failed", error=str(error))
        print(f"Screening incomplete: {error}\nDownloads and logs remain in {output}; resolve the error and rerun in a new directory.", file=sys.stderr)
        return 1
    finally:
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
