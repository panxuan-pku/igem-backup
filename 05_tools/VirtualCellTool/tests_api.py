"""Smoke-test every public API route against a running local VirtualCellTool."""
import argparse
import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = f"http://127.0.0.1:{os.environ.get('VCT_PORT', '8377')}"


def get(route, **query):
    url = BASE + route + ("?" + urlencode(query) if query else "")
    with urlopen(url, timeout=240) as response:
        assert response.status == 200, url
        body = response.read()
    return json.loads(body) if route.startswith("/api/") else body.decode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-gears", action="store_true", help="skip the two GEARS routes when Norman data is not downloaded")
    args = parser.parse_args()
    assert "VirtualCellTool" in get("/")
    datasets = {"pbmc": (2700, "MS4A1"), "ms": (17799, "MOBP"), "ws": (96969, "GTF2I")}
    for ds, (n_cells, gene) in datasets.items():
        assert get("/api/data", ds=ds)["n_cells"] == n_cells
        response = get("/api/perturb_cipher", ds=ds, gene=gene, direction="ko")
        assert response["delta_abs_max"] > 0, (ds, gene)
        print(f"{ds}: {n_cells} cells, {gene} |Δ|max={response['delta_abs_max']}")

    before = get("/api/perturb_cipher", ds="pbmc", gene="MS4A1", direction="ko")
    checks = [
        ("/api/attribute", {"cell": 1, "k": 5}, "top_genes"),
        ("/api/perturb", {"cell": 1, "gene": "MS4A1", "value": 0}, "displacement"),
        ("/api/perturb_multi", {"cell": 1, "genes": "MS4A1,CD79A", "value": 0}, "displacement"),
        ("/api/search_genes", {"q": "MS4A1"}, "matches"),
        ("/api/cell_gene_expr", {"cell": 1, "gene": "MS4A1"}, "value"),
        ("/api/gene_expr", {"gene": "MS4A1"}, "mean"),
        ("/api/gene_coverage", {"gene": "CEBPA"}, "covered"),
        ("/api/perturb_causal", {"gene": "CEBPA"}, "n_genes_predicted"),
        ("/api/cipher_status", {}, "fitted"),
        ("/api/gene_in_cipher", {"gene": "MS4A1"}, "covered"),
        ("/api/perturb_cipher", {"gene": "MS4A1"}, "delta_abs_max"),
        ("/api/perturb_baseline", {"gene": "MS4A1"}, "results"),
        ("/api/gene_expr_map", {"gene": "MS4A1"}, "values"),
        ("/api/attribution_map", {"cell": 1, "k": 5}, "rows"),
        ("/api/perturb_compare", {"gene": "MS4A1"}, "rows"),
        ("/api/celltype_response", {"gene": "MS4A1"}, "cell_types"),
        ("/api/perturb_summary", {"gene": "MS4A1"}, "heatmap"),
    ]
    if args.skip_gears:
        checks = [item for item in checks if item[0] not in {"/api/gene_coverage", "/api/perturb_causal"}]
    for route, query, key in checks:
        result = get(route, **query)
        assert key in result, (route, result)
    after = get("/api/perturb_cipher", ds="pbmc", gene="MS4A1", direction="ko")
    for key in ("ctrl_expr", "target_value", "delta_abs_max", "n_sig_genes", "top_up", "top_down"):
        assert before[key] == after[key], f"PBMC CIPHER {key} changed after loading MS/WS"
    print(f"{len(checks) + 1}/18 API routes and home page passed; dataset isolation passed")


if __name__ == "__main__":
    main()
