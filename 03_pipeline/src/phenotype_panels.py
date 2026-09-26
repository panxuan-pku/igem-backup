"""Configured phenotype evidence views; no scoring or candidate filtering."""
import pandas as pd


def load_phenotype_panels(cfg):
    panels = cfg.get("phenotype_panels", [])
    if not isinstance(panels, list):
        raise ValueError("phenotype_panels must be a list")
    seen = set()
    for panel in panels:
        if not isinstance(panel, dict):
            raise ValueError("phenotype_panels entries must be mappings")
        for key in ("id", "disease", "phenotype"):
            if not isinstance(panel.get(key), str) or not panel[key].strip():
                raise ValueError(f"phenotype_panels: {key} must be a nonempty string")
        tissues = panel.get("tissues")
        if (not isinstance(tissues, list) or not tissues
                or any(not isinstance(t, str) or not t.strip() for t in tissues)):
            raise ValueError("phenotype_panels: tissues must be a nonempty list of names")
        if len(set(tissues)) != len(tissues) or panel["id"] in seen:
            raise ValueError("phenotype_panels: duplicate tissue names or panel IDs")
        seen.add(panel["id"])
    return panels


def tissue_column(tissue):
    return f"hpa_tissue::{tissue}::ntpm"


def tissue_coverage(tissues, available):
    found = [t for t in tissues if t in available]
    missing = [t for t in tissues if t not in available]
    return {"available_tissues": found, "missing_tissues": missing,
            "coverage_status": "complete" if not missing else "partial" if found else "unavailable"}


def describe_panels(frame, panels):
    summaries = []
    for panel in panels:
        available = [t for t in panel["tissues"] if tissue_column(t) in frame.columns]
        columns = [tissue_column(t) for t in available]
        values = frame[columns].apply(pd.to_numeric, errors="coerce")
        summaries.append({**panel, **tissue_coverage(panel["tissues"], available),
                          "genes_with_expression": int(values.notna().any(axis=1).sum()),
                          "candidate_count": len(frame)})
    return summaries


def render_phenotype_panels(frame, panels):
    if not panels:
        return []

    def show(value):
        if pd.isna(value) or value == "":
            return "无数据"
        return " ".join(str(value).splitlines()).replace("|", "\\|")

    lines = ["", "## 分表型证据面板", "",
             "以下展示全部候选，沿用总排名顺序；不是表型独立排名，不改变总分、权重或候选集合。",
             "表型—组织对应关系由配置指定；表达仅为组织背景证据，不代表表型因果或安全性。",
             "0 表示测得的零表达；无数据不等于零表达。覆盖状态指组织列可用性，逐基因缺失另列。"]
    evidence = [("clinGen_hi_score", "ClinGen HI"),
                ("clinGen_haploinsufficiency_status", "ClinGen HI 状态"),
                ("gnomad_pLI", "pLI"), ("gnomad_LOEUF", "LOEUF")]
    evidence = [(col, label) for col, label in evidence if col in frame.columns]
    for panel in panels:
        status = {"complete": "组织列齐全", "partial": "覆盖不完整",
                  "unavailable": "无法评估：无可用组织列"}[panel["coverage_status"]]
        lines += ["", f"### {show(panel['disease'])} / {show(panel['phenotype'])} ({show(panel['id'])})", "",
                  f"{status}；有表达记录的候选：{panel['genes_with_expression']}/{len(frame)}。",
                  "缺少的组织列：" + ("、".join(show(t) for t in panel["missing_tissues"]) or "无") + "。"]
        if panel["missing_tissues"]:
            lines.append("请核对 HPA 源数据及合并配置；旧证据表需使用同一面板配置重新合并，不能据此推断组织不表达。")
        headers = ["总排名（参考）", "基因", "HGNC", "总分（参考）"]
        headers += [label for _, label in evidence]
        headers += [show(t) + " nTPM" for t in panel["tissues"]] + ["逐基因组织覆盖"]
        lines += ["", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for _, row in frame.iterrows():
            values = [pd.to_numeric(row.get(tissue_column(t)), errors="coerce") for t in panel["tissues"]]
            n = sum(pd.notna(v) for v in values)
            cells = [row.get("rank"), row.get("input_symbol"), row.get("hgnc_id"), row.get("consensus_score")]
            cells += [row.get(col) for col, _ in evidence] + values
            cells += [f"{n}/{len(values)}" + ("（无数据）" if n == 0 else "（覆盖不完整）" if n < len(values) else "")]
            lines.append("| " + " | ".join(show(v) for v in cells) + " |")
    return lines
