# iGEM 2026: deletion-gene prioritization

**Start with a deletion interval or a candidate gene list; obtain an evidence ranking and a design-check report.** The pipeline integrates ClinGen and gnomAD evidence, adds Open Targets (OT) disease annotations, and checks the project's **3′UTR ≥30 bp** and module-budget requirements.

| Your starting point | Workflow |
|---|---|
| A deletion interval, or your first WHS example | [2. Deletion interval](#2-deletion-interval-whs-example) |
| A candidate list from a sample, publication or analysis | [3. Gene list](#3-gene-list) |
| Results and custom output locations | [4. Outputs](#4-outputs) |
| Understanding the repository | [7. Repository structure](#7-repository-structure) |

## 1. Installation

Use Terminal on macOS/Linux or a Conda-enabled terminal on Windows (for example, Miniforge Prompt). **Git and Conda must be available.** These commands are the same on all three systems:

```text
git clone https://github.com/panxuan-pku/igem-backup.git
cd igem-backup
conda env create --file environment.yml
conda activate virtual-screening
python scripts/test_pipeline.py --suite environment
```

Continue after **`[OK] Checks passed (environment)`**. Run all commands below from the repository root. In a new terminal, return to this directory and activate `virtual-screening` again.

## 2. Deletion interval: WHS example

This example uses the **ClinGen WHS reference interval ISCA-37429, GRCh38**. The pipeline extracts overlapping protein-coding genes from reference annotations; no BioMart export is needed. This public reference interval is not a patient-specific deletion or the historical 19-gene study set.

### 2.1 Prepare the input

Create `03_pipeline/input/raw/`. Download the [ClinGen GRCh38 region table](https://ftp.clinicalgenome.org/ClinGen_region_curation_list_GRCh38.tsv) into it, keeping the original filename. Check the interval against the [WHS record](https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-37429).

```text
python scripts/prepare_screening_input.py interval --input 03_pipeline/input/raw/ClinGen_region_curation_list_GRCh38.tsv --format clingen-tsv --region-id ISCA-37429 --genome-build GRCh38 --source "https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-37429" --output 03_pipeline/input/whs_interval_input.json
```

**Expected:** `[OK] Input preparation complete`, the interval coordinates and the path to `whs_interval_input.json`. Check the coordinates; no manual JSON editing is needed.

### 2.2 Prepare references

```text
python scripts/run_screening.py prepare
```

**Expected:** `[OK] Reference preparation complete (5/5)`. The first download is approximately **617 MiB**, saved in `03_pipeline/data/screening_refs/`. Subsequent runs verify and reuse completed files; rerun the same command after an interruption.

| Reference | Purpose |
|---|---|
| GENCODE and HGNC | Gene identity, position and transcript annotation |
| ClinGen and gnomAD | Core ranking evidence |
| HPA | Tissue-expression annotations |

The ClinGen **region table** in step 2.1 defines the input interval; the **gene evidence table** downloaded here contributes to scoring.

### 2.3 Run screening

```text
python scripts/run_screening.py run --input-file 03_pipeline/input/whs_interval_input.json --output 03_pipeline/outputs_repro/whs_interval_01
```

**Expected:** `[OK] Screening complete`, candidate counts and the path to **`interval_report.html`**. Open that file in a browser. See [section 4](#4-outputs) for the other outputs.

<details>
<summary>Use your own deletion interval: BED input</summary>

Save a GRCh38 BED file as `03_pipeline/input/raw/deletion.bed` and replace step 2.1 with:

```text
python scripts/prepare_screening_input.py interval --input 03_pipeline/input/raw/deletion.bed --format bed --genome-build GRCh38 --source "actual interval source" --output 03_pipeline/input/deletion_interval_input.json
```

Keep step 2.2. In step 2.3, use `--input-file 03_pipeline/input/deletion_interval_input.json` and a new output directory. The converter changes BED's 0-based start to 1-based inclusive coordinates; it does **not** convert genome builds. Select one row from a multi-row BED with `--row`. For CSV/TSV interval tables, run `python scripts/prepare_screening_input.py interval --help`.

</details>

## 3. Gene list

Use this route when you **already have a defined candidate set**. No deletion coordinates are required. Ensembl/HGNC IDs and uniquely resolvable gene symbols are accepted.

### 3.1 Prepare the input

Save your table as `03_pipeline/input/raw/genes.csv`, with one candidate per row. Keep its header and other columns. This example assumes a gene column named **`gene_id`**; replace `--gene-column` and `--source` with the actual column name and source URL or publication ID.

```text
python scripts/prepare_screening_input.py genes --input 03_pipeline/input/raw/genes.csv --format csv --gene-column gene_id --source "actual source URL or publication ID" --output 03_pipeline/input/gene_list_input.json
```

**Expected:** `[OK] Input preparation complete`, the number of identifiers and the path to `gene_list_input.json`. Identity checks occur during screening; duplicates or ambiguous identities produce an explicit error.

<details>
<summary>Other formats: TXT, TSV and Excel</summary>

TXT files contain one gene per line with no header:

```text
python scripts/prepare_screening_input.py genes --input 03_pipeline/input/raw/genes.txt --format txt --source "actual list source" --output 03_pipeline/input/gene_list_input.json
```

For TSV, use the CSV command with your `.tsv` path, `--format tsv` and the actual column name. Export Excel sheets as UTF-8 CSV first. Choose one format to create the input JSON.

</details>

<details>
<summary>No list yet? Practice with the complete WHS candidates from section 2</summary>

After completing section 2, use this command instead of the CSV conversion above. It reads **all candidates**, not only the highest-ranked genes:

```text
python scripts/prepare_screening_input.py genes --input 03_pipeline/outputs_repro/whs_interval_01/interval_candidates.csv --format csv --gene-column gene_id --source "WHS ISCA-37429; whs_interval_01/interval_candidates.csv; see whs_interval_01/interval_manifest.json" --output 03_pipeline/input/gene_list_input.json
```

Continue with steps 3.2 and 3.3. This demonstrates another input route for the same candidate set, not an independent source of candidates.

</details>

### 3.2 Prepare references

```text
python scripts/run_screening.py prepare
```

**Expected:** `[OK] Reference preparation complete (5/5)`. Both input routes share references; files verified in step 2.2 are reused.

### 3.3 Run screening

```text
python scripts/run_screening.py run --input-file 03_pipeline/input/gene_list_input.json --output 03_pipeline/outputs_repro/gene_list_01
```

**Expected:** `[OK] Screening complete`, candidate counts and the path to **`gene_list_report.html`**. This report covers the submitted list.

Both routes default to WHS disease ID `MONDO_0008684` for OT annotations. For another disease, add `--disease-id YOUR_DISEASE_ID` to `run`. OT annotations do not change the core ranking.

## 4. Outputs

### 4.1 Which files to read

Filenames follow **`input_type_purpose.extension`**: `interval` for deletion intervals, `gene_list` for gene lists.

| Purpose | Interval input | Gene-list input |
|---|---|---|
| Browser report | `interval_report.html` | `gene_list_report.html` |
| Summary, 16 columns | `interval_summary.csv` | `gene_list_summary.csv` |
| Full evidence | `interval_ranked.csv` | `gene_list_ranked.csv` |
| Standardized candidates | `interval_candidates.csv` | `gene_list_candidates.csv` |
| Run manifest | `interval_manifest.json` | `gene_list_manifest.json` |
| Run configuration | `interval_config.yaml` | `gene_list_config.yaml` |
| OT response snapshot | `interval_ot_snapshot.json` | `gene_list_ot_snapshot.json` |

CSV files use UTF-8 with BOM for Excel compatibility; JSON, HTML and YAML use UTF-8. The manifest records the input type, output filenames and checksums. Shared references remain in `screening_refs/`.

Both result tables preserve the same candidates, ranks and scores. **The score indicates research priority; `selected` indicates compliance with design-length and budget conditions.** Neither establishes experimental validation.

**`[WARN] Ranking generated…`** means the ranking is available with OT annotation gaps; review the report. **`[FAIL]`** means the step stopped; resolve the reported error before retrying.

### 4.2 Choose your output directory

Set **`--output "directory"`** on the `run` command:

```text
python scripts/run_screening.py run --input-file 03_pipeline/input/gene_list_input.json --output "runs/gene_list_02"
```

| System | Absolute-path example |
|---|---|
| macOS | `--output "/Users/yourname/Documents/screening/gene_list_02"` |
| Linux | `--output "/home/yourname/screening/gene_list_02"` |
| Windows | `--output "D:\screening\gene_list_02"` |

Relative paths resolve from your terminal's current directory. **The output directory must not already exist**; the program creates it. For another run, change `_01` to `_02`.

Without `--output`, the program creates `03_pipeline/outputs_repro/interval_YYYYMMDD_HHMMSS_microseconds/` or `gene_list_YYYYMMDD_HHMMSS_microseconds/` inside this repository. Custom directory names are used unchanged; files inside still carry the input-type prefix. Name prepared inputs `project_interval_input.json` or `project_gene_list_input.json`. Existing results retain their original names.

To relocate references, supply the same `--references "directory"` to both `prepare` and `run`.

## 5. Methods and reproduction

The unified configuration is **`03_pipeline/config/screening.yaml`**. ClinGen and gnomAD drive the ranking; OT, HPA and optional IMPC provide annotations. The 3′UTR check and module budget determine design selection without deleting ranking rows. DeepLOF is not enabled in this profile.

`references.json` records reference versions, sources and checksums. To replay an analysis, retain its input, references and configuration, then add `--ot-snapshot previous_run/interval_ot_snapshot.json` to `run` (use `gene_list_ot_snapshot.json` for a list run).

- [Unified screening guide](00_docs/01_guides/UNIFIED_SCREENING.html): optional arguments, evidence interpretation and troubleshooting.
- [VCT guide](00_docs/01_guides/VCT_SETUP.html): separate virtual perturbation exploration.
- [Project navigation](00_docs/01_guides/PROJECT_INDEX.html): design and historical records.

Open downloaded HTML guides in a browser. The older Williams `run_quickstart.py` remains for compatibility; this README uses the unified `run_screening.py` entry point.

## 6. Optional features and development

Basic screening only needs the environment from section 1.

| Purpose | Setup |
|---|---|
| Single-cell processing / optional CNV | In `virtual-screening`: `python -m pip install -r 03_pipeline/requirements-cnv.txt` |
| Development tests | In `virtual-screening`: `python -m pip install -r 03_pipeline/requirements-dev.txt` |
| VCT | `conda env create --file environment-vct.yml` creates a separate `virtual-cell` environment |

VCT installs AnnData, Scanpy and PyTorch in its own environment; **installing the CNV extras first is unnecessary**. Prepare its model and single-cell data using the [VCT guide](00_docs/01_guides/VCT_SETUP.html), then start it:

```text
conda activate virtual-cell
python -m uvicorn web.app:app --app-dir 05_virtual_cell --host 127.0.0.1 --port 8377
```

<details>
<summary>Developers: tests and release checks</summary>

```text
conda activate virtual-screening
python -m pip install -r 03_pipeline/requirements-dev.txt
python scripts/test_pipeline.py --suite core
python scripts/check_release.py
```

Expected: `[OK] Checks passed (core)` and `Release check passed`. The full suite needs CNV dependencies; historical Bash scripts can be run through WSL on Windows:

```text
python -m pip install -r 03_pipeline/requirements-cnv.txt
python scripts/test_pipeline.py
python -m pytest scripts/tests -q
```

Code, configurations and tests are versioned; datasets, models, generated results and agent records are excluded. `bash scripts/export_github.sh /path/to/new-empty-directory` exports release files.

</details>

## 7. Repository structure

**For screening, start with `scripts/`, `03_pipeline/` and `environment.yml`.** Other disease directories are historical experiments, not additional steps in the WHS workflow. VCT is a separate, optional tool.

```text
igem-backup/
├── README.md                    # Start here: two screening workflows
├── environment.yml              # Required: virtual-screening environment
├── environment-vct.yml          # Optional: separate virtual-cell environment
├── scripts/                     # Current input / reference / screening commands
├── 03_pipeline/
│   ├── config/screening.yaml    # Current unified screening configuration
│   ├── src/                    # Identity, evidence, ranking and optional modules
│   ├── requirements*.txt        # Basic, CNV and development dependencies
│   ├── tests/                  # Automated checks; not a user workflow
│   ├── docs/                   # Technical reference and historical inventories
│   ├── input/                  # Your raw and prepared inputs (local)
│   ├── data/screening_refs/     # Downloaded, versioned references (local)
│   └── outputs_repro/          # New screening runs (local)
├── 05_virtual_cell/             # Independent VirtualCellTool source and guide
├── 00_docs/                     # Guides, design notes and historical archives
├── 01_disease-22q11.2/          # Historical 22q11.2 exploration
├── 02_disease-williams/         # Historical Williams syndrome exploration
├── 04_reports/                 # Research history, reports and Wiki drafts
└── 06_epidemiology/             # Epidemiology research and supporting scripts
```

Local input, data and output folders appear when you prepare files or run commands; a fresh clone does not include their contents. The historical folders and epidemiology material are **not required for the screening commands above**. Inside `03_pipeline`, `pipeline.yaml`, CNV modules and archived outputs belong to earlier or optional workflows; use `screening.yaml` with `run_screening.py` for the current workflow.
