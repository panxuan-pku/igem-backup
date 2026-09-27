#!/usr/bin/env python3
"""One merged pipeline: deletion interval or gene list → ranking → design annotations."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from run_quickstart import download, sha256

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_pipeline"))
from src.screening import CONFIG, add_impc, load_config, merge_core, rank_candidates, select_modules
from src.screening_inputs import build_candidates, transcript_design
from src.opentargets import annotate_snapshot, fetch_snapshot


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def verify_references(directory):
    lock = json.loads((directory / "references.json").read_text())
    if lock.get("status") != "complete":
        raise ValueError("reference preparation is incomplete")
    for name, expected in load_config()["references"].items():
        recorded = lock["files"][name]
        if any(recorded[k] != expected[k] for k in ("url", "version")):
            raise ValueError(f"reference version/source mismatch: {name}")
        if sha256(directory / name) != recorded["sha256"]:
            raise ValueError(f"reference checksum mismatch: {name}")
    return lock


def prepare(directory):
    if directory.exists():
        # A failed download can resume only if its completed files are unchanged.
        lock = json.loads((directory / "references.json").read_text())
    else:
        directory.mkdir(parents=True)
        lock = {"created_utc": now(), "status": "preparing", "files": {}}
        write_json(directory / "references.json", lock)
    for name, source in load_config()["references"].items():
        if name in lock["files"]:
            record = lock["files"][name]
            if any(record[k] != source[k] for k in ("url", "version")) or sha256(directory / name) != record["sha256"]:
                raise ValueError(f"existing reference changed; use a new directory: {name}")
            print(f"已核对 {name}", flush=True)
            continue
        print(f"下载 {name} ({source['version']})", flush=True)
        lock["files"][name] = {**download(source["url"], directory / name), "version": source["version"]}
        write_json(directory / "references.json", lock)
    lock["status"] = "complete"
    write_json(directory / "references.json", lock)
    verify_references(directory)
    print(f"参考快照已固定：{directory.resolve()}")


def code_provenance():
    def git(*args):
        result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
        return result.stdout.strip() if result.returncode == 0 else "unavailable"
    paths = [Path(__file__).resolve(), ROOT / "scripts/run_quickstart.py", CONFIG]
    paths += sorted((ROOT / "03_pipeline/src").rglob("*.py"))
    return {"git_commit": git("rev-parse", "HEAD"), "git_status": git("status", "--porcelain"),
            "file_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in paths},
            "python": sys.version, "packages": {p: importlib.metadata.version(p) for p in ("pandas", "numpy", "PyYAML", "requests")}}


def report(output, ranked, manifest):
    cols = ["rank", "symbol", "gene_id", "consensus_score", "evidence_status", "ot_status", "ot_disease_score",
            "utr3_bp", "utr3_status", "selected", "selection_reason", "evidence_notes"]
    table = ranked[[c for c in cols if c in ranked]].to_html(index=False, escape=True, na_rep="未获得", border=0)
    content = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>统一筛选报告</title><style>body{{font:17px/1.75 system-ui;margin:40px auto;max-width:1180px;padding:0 24px;color:#193344;background:#f5f8fb}}section{{background:white;padding:20px 26px;margin:18px 0;border-radius:12px}}h1,h2{{line-height:1.3}}.table{{overflow:auto}}td,th{{padding:10px;border-bottom:1px solid #dde4eb;text-align:left;min-width:80px}}code{{overflow-wrap:anywhere}}</style>
<h1>统一候选筛选报告</h1><p>疾病编号：{escape(manifest['disease_id'])} · 完成状态：{escape(manifest['status'])}</p>
<section><h2>1. 本次输入与范围</h2><p>{escape(json.dumps(manifest['input'], ensure_ascii=False))}</p>
<p>{len(ranked)} 个蛋白编码候选。部分区间重叠会保留并标记；列表输入仅覆盖所提交的基因。两种输入都使用同一个排序器。</p></section>
<section><h2>2. 如何读结果</h2><p>rank 越小越靠前；consensus_score 是当前候选集合中的相对证据分数，不是概率。OT、IMPC 和表达仅作注释。selected 表示通过本项目 3′UTR ≥30 bp 门槛且在固定模块预算内，不代表治疗效果或完成载体设计。</p>
<p>OT available = 有直接关联记录；no_record = 查询成功但无该疾病直接记录；query_failed = 查询或版本核验失败。空值不能当作 0 分或无关联。其他疾病和预设表型单独列在 CSV 中。</p>
<p>IMPC 未提供时记 not_supplied；人鼠同源关系需有来源。ClinGen 隐性疾病关联和小鼠 viable 均不自动排除。gnomAD 有质量标记的数值保留原值，但不计分。</p></section>
<section><h2>3. 排名与设计检查</h2><div class="table">{table}</div></section>
<section><h2>4. 下载与复现</h2><p><a href="ranked.csv">完整排名及注释</a> · <a href="candidates.csv">统一候选</a> · <a href="manifest.json">输入、版本和校验值</a> · <a href="ot_snapshot.json">OT 查询快照</a> · <a href="config.yaml">运行配置</a></p>
<p>复现应复用同一参考目录和 OT 快照。HGNC / ClinGen 新下载的内容可能变化；OT 实时服务升级后应使用旧快照或明确升级配置重跑。结果不能直接跨不同候选集合比较。</p></section></html>"""
    (output / "report.html").write_text(content)


def run(args):
    config = load_config()
    if args.module_budget <= 0 or args.module_size <= 0:
        raise ValueError("module budget and size must be positive")
    references = args.references.resolve()
    lock = verify_references(references)
    genes = args.genes
    if args.gene_list:
        genes = [s.strip() for s in args.gene_list.read_text().splitlines() if s.strip()]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "running", "started_utc": now(), "disease_id": args.disease_id,
                "phenotype_ids": args.phenotype_id, "reference_directory": str(references),
                "references": lock, "code": code_provenance(),
                "input": {"interval": args.interval, "genes": genes, "source": args.input_source,
                          "genome_build": "GRCh38", "coordinate_system": "1-based-inclusive"},
                "module_budget_bp": args.module_budget, "assumed_module_bp": args.module_size,
                "optional_inputs": {}}
    for label, path in (("gene_list", args.gene_list), ("impc_evidence", args.impc_evidence), ("ot_snapshot", args.ot_snapshot)):
        if path:
            manifest["optional_inputs"][label] = {"path": str(path.resolve()), "sha256": sha256(path)}
    write_json(output / "manifest.json", manifest)
    (output / "config.yaml").write_text(CONFIG.read_text())
    try:
        print("1/4 核对候选编号、位置与转录本", flush=True)
        frame = build_candidates(references / "annotation.gtf.gz", references / "hgnc.tsv", interval=args.interval, genes=genes)
        frame = transcript_design(references / "annotation.gtf.gz", frame)
        frame.to_csv(output / "candidates.csv", index=False)
        print("2/4 合并固定版本证据", flush=True)
        frame = merge_core(frame, references)
        if args.impc_evidence:
            frame = add_impc(frame, args.impc_evidence)
        print("3/4 查询或重放 OT 注释（不改变排名）", flush=True)
        snapshot = json.loads(args.ot_snapshot.read_text()) if args.ot_snapshot else fetch_snapshot(
            frame.gene_id.tolist(), args.disease_id, args.phenotype_id, config["ot_release"])
        write_json(output / "ot_snapshot.json", snapshot)
        frame = annotate_snapshot(frame, snapshot, args.disease_id, args.phenotype_id, config["ot_release"])
        print("4/4 统一排名、30 bp 设计门槛与模块预算", flush=True)
        ranked, _ = rank_candidates(frame)
        ranked = select_modules(ranked, args.module_budget, args.module_size)
        if len(ranked) != len(frame) or set(ranked.gene_id) != set(frame.gene_id):
            raise ValueError("ranker did not preserve the candidate set")
        ranked.to_csv(output / "ranked.csv", index=False)
        manifest.update(status="completed_with_annotation_gaps" if ranked.ot_status.eq("query_failed").any() else "complete",
                        completed_utc=now(), candidate_gene_ids=sorted(frame.gene_id),
                        ot_status_counts=ranked.ot_status.value_counts().to_dict(),
                        output_sha256={p.name: sha256(p) for p in (output / "ranked.csv", output / "candidates.csv", output / "ot_snapshot.json", output / "config.yaml")})
        report(output, ranked, manifest)
        write_json(output / "manifest.json", manifest)
    except Exception as exc:
        manifest.update(status="failed", error=str(exc), ended_utc=now())
        write_json(output / "manifest.json", manifest)
        raise
    print(f"{manifest['status']}：{output / 'report.html'}", flush=True)


def main():
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="download and lock the reference bundle")
    prep.add_argument("--references", type=Path, required=True)
    screen = sub.add_parser("run", help="rank a supplied interval or gene list")
    screen.add_argument("--references", type=Path, required=True)
    inputs = screen.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--interval", help="GRCh38, 1-based inclusive, e.g. chr4:start-end; no commas")
    inputs.add_argument("--genes", nargs="+", help="HGNC IDs, Ensembl gene IDs or symbols")
    inputs.add_argument("--gene-list", type=Path, help="one gene per line, no header")
    screen.add_argument("--input-source", default="user_supplied; source_not_verified")
    screen.add_argument("--disease-id", default=config["disease_id"])
    screen.add_argument("--phenotype-id", action="append", default=[])
    screen.add_argument("--ot-snapshot", type=Path)
    screen.add_argument("--impc-evidence", type=Path)
    screen.add_argument("--module-budget", type=int, default=config["module_budget_bp"])
    screen.add_argument("--module-size", type=int, default=config["assumed_module_bp"])
    screen.add_argument("--output", type=Path, default=ROOT / "03_pipeline/outputs_repro" / ("screening_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))
    args = parser.parse_args()
    try:
        prepare(args.references.resolve()) if args.command == "prepare" else run(args)
    except Exception as exc:
        parser.exit(1, f"筛选停止：{exc}\n")


if __name__ == "__main__":
    main()
