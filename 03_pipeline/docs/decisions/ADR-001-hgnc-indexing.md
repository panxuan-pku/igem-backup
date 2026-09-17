# ADR-001: Primary index — HGNC ID vs HGNC symbol

**Date:** 2025-09-01 · **Status:** Accepted

## Context
输入是 HGNC gene symbol 列表（每行一个），但国外数据源（ClinGen/gnomAD/HPA）以及我们内部要对同一基因建立一致的 join。HGNC 名会更新，HGNC ID 是固定。

## Decision
以 HGNC ID 为 pipeline 主键。输入做 alias mapping 之后统一从 `normalized.csv` 中产生 HGNC ID。所有数据源 join 都用 HGNC ID 作键。

## Consequences
- 输入校验强：在 normalize 阶段就判断哪些 gene symbol 不能 resolve（>10% 失败 → 报错）
- 数据源变动时不影响 repeat run
- `input_symbol` 用于展示（debug/audit）

## Notes
- 每次 run 的数据源 checksums 记录于 audit/data_checksums.txt
