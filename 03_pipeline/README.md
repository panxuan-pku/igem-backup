# Microdeletion candidate prioritization

**Current entry point:** run `scripts/run_screening.py` from the repository root with `03_pipeline/config/screening.yaml`. Follow the [root README](../README.md) for the complete **WHS interval** and **gene-list** workflows, including installation and expected outputs.

## 1. Install once

From the repository root, on macOS, Linux or Windows with Conda available:

```text
conda env create --file environment.yml
conda activate virtual-screening
python scripts/test_pipeline.py --suite environment
```

The base environment installs only screening dependencies. CNV and developer extras are optional; VCT has a separate environment. See the root README for commands.

## 2. Current workflow and files

```text
Raw interval / gene table
  → scripts/prepare_screening_input.py
  → prepared input JSON
  → scripts/run_screening.py run
  → interval_* or gene_list_* outputs

scripts/run_screening.py prepare
  → data/screening_refs/ + references.json
  → shared references for both input routes
```

| Location | Role |
|---|---|
| `config/screening.yaml` | Unified scoring, transcript and design policy |
| `src/` | Candidate identification, evidence integration, ranking and extensions |
| `input/` | Local raw files and prepared inputs |
| `data/screening_refs/` | Downloaded references and checksum manifest |
| `outputs_repro/` | Separate directories for new runs |
| `tests/` | Automated implementation checks |
| `docs/` | Technical reference and historical inventories |

Each unified run writes seven files with the input-type prefix: `report.html`, `summary.csv`, `ranked.csv`, `candidates.csv`, `manifest.json`, `config.yaml` and `ot_snapshot.json`. For example, interval input produces `interval_report.html`; gene-list input produces `gene_list_report.html`. The summary retains 16 fields; full evidence remains available separately. See the [unified guide](../00_docs/01_guides/UNIFIED_SCREENING.html) for interpretation and optional arguments.

<a id="data-sources"></a>
## 3. Reference sources

**Data are not included in Git.** `python scripts/run_screening.py prepare` downloads and records the references used by the unified workflow. `references.json` stores their URLs, versions, timestamps and SHA256 checksums.

| Source | Current role | Official entry |
|---|---|---|
| GENCODE | GRCh38 gene locations and transcript annotation | [Human releases](https://www.gencodegenes.org/human/) |
| HGNC | Approved gene IDs, symbols and aliases | [Downloads](https://www.genenames.org/download/) |
| ClinGen | Gene dosage-sensitivity evidence | [FTP files](https://ftp.clinicalgenome.org/) |
| gnomAD | Loss-of-function constraint | [Downloads](https://gnomad.broadinstitute.org/downloads) |
| HPA | Tissue RNA expression annotations | [Downloads](https://www.proteinatlas.org/about/download) |
| Open Targets | Disease and optional phenotype annotations | [Platform](https://platform.opentargets.org/) |

The ClinGen **region** table used by the WHS example defines its input; the ClinGen **gene** table provides evidence. These are different downloads. Keep the same reference files and OT snapshot to reproduce a run. A checksum identifies a file; it cannot recover a missing file or independently establish its origin.

<details>
<summary>Historical manual evidence tables</summary>

Earlier `merge_evidence` workflows read `clinGen_gene_curation_list_GRCh38.tsv`, `gnomad_constraint.tsv`, `rna_tissue_consensus.tsv` and `hgnc_aliases.tsv` from a manually prepared data directory. They used different versions, including gnomAD v2.1.1. Do not substitute these tables for the unified reference set without checking schemas and versions. Their old download instructions and source registrations are historical records, not the current installation route.

</details>

## 4. Optional and historical modules

- **DeepLOF:** conversion and scoring interfaces exist, but the unified profile does not enable these scores. This does not mean a DeepLOF model was trained or run.
- **CNV:** expression-based inference did not recover the known microdeletion in our historical check. Current screening starts from a known interval or a candidate list; automatic CNV development is paused. See the [historical CNV decision](docs/index.html#cnv-decision).
- **Earlier ranking:** `config/pipeline.yaml`, `src.consensus_v2` and the Williams `run_quickstart.py` remain for compatibility. They are not the first-run workflow. Their existing filenames remain unchanged.
- **Expression and inheritance extensions:** retained for research; not all are automatically connected to unified screening.

[Technical reference](docs/reference/index.html) and [historical inventories](docs/index.html) document earlier modules. Archived results under `outputs/history/` are local records, not inputs required by the root README. Keep new results in separate output directories.
