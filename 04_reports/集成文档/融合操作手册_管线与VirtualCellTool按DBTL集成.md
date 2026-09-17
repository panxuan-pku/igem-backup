# 管线 ↔ VirtualCellTool 融合手册：按 iGEM DBTL 执行

> 对应您的文档：《微缺失病计算通路复盘报告》（五步通路）· `tools/VirtualCellTool/` · `03_pipeline/`
> 目标：把 L1 遗传证据管线接入 VCT 平台，形成可审计的 DBTL（Design–Build–Test–Learn）双循环。

---

## Cycle-0：先有验收标准、再动工程

您已经为 VCT 立过 AC1–AC4。融合前，把同一套标准扩展到 L1：

**建议 AC 补充（新增）：**
- **AC-L1-1（ClinGen 连接率）**：输入的候选基因中，能连接 ClinGen 的比例 ≥ 60%（未覆盖的不罚，但写 audit）
- **AC-L1-2（正对照通过）**：TBX1/ELN/KCTD13/RAI1（文献锚定主效基因） 在 consensus 排名前 10% 或 ClinGen HI score ≥ 2
- **AC-L1-3（审计完备）**：每次运行都生成 `outputs/audit/run.json` + `data_checksums.txt`，包括数据源 MD5、输入 gene 数、连接率、缺失率
- **AC-L1-4（HPA 阈值稳定）**：器官过滤阈值与 L1 重复排序两次稳定（deterministic）

这套 AC 把"负结果可报告"直接设计为判据之一。

## Cycle-1：Design — 决策框架

1. **决定 L1 扮演角色**：我们未来的 VCT 有两个功能——候选源选择 + （CellOracle）扰动后检验。决定 L1 生成“**遗传学等级**”，VCT 生成“**机制假设**”，决定排库方子的“正对照”（TBX1/ELN/KCTD13/RAI1）事先测试。
2. **决策方式**：`docs/decisions/ADR-002-l1-in-vct.md`（在输出骨架里加入这个文件）。比如："决定用 weighted_vote（见 config/pipeline.yaml）"、"决定 missing_handling=neutral（让不覆盖的 ClinGen gene 不扣0）"。
3. **Data Contract**：定好输入/输出 schema（已在工程指导书 §3.2/§3.4 名列），让 L1 和 VCT 之间只交换 CSV/Parquet，避免直接传递模型。

## Cycle-2：Build — 修改/新增代码

在已有工作基础上执行四个独立实现（独立于对方破坏）：

### Build-S1：VCT 增加 L1 数据源（正向输入）
- **位置**：`tools/VirtualCellTool/web/app.py`（或 `web/index.html`）
- **改动**：新增一个 `CandidateSource` enum：`"diff_attribution" | "diff_expression" | "l1_genetics"`
- **操作**：获取 `03_pipeline/outputs/wbs/candidates_ranked_v2.csv`（或任一 mode 排名 `outputs/mode/ranked_*.csv`），并將列 `consensus_score`、`clinGen_hi_score`、`gnomad_LOEUF`、`gnomada_pLI` 的 UI 标注
- **验收标准**：AC-L1-1/AC-L1-2/AC-L1-4 全通过；UI 切换时端到端 <2s（沿用 AC3）

### Build-S2：41 基因正对照清单（方法学）
- **位置**：`input/candidates.csv` 额外 `disease` / `expected`（known_primary）列
- **改动**：加入 `expected` 布尔，已知主效基因（TBX1, ELN, KCTD13, RAI1, COMT, GTF2I 等）标 `expected=True`
- **操作**：跑 `03_pipeline/src/consensus.py`
- **验收标准**：AC-L1-2（positive controls 在前 10% 或 ClinGen score ≥ 2）

### Build-S3：审计单据（every run）
- **位置**：`outputs/audit/`
- **改动**：在 `merge_evidence.py` 里使用 SHA256 写 `data_checksums.txt`；在 `consensus.py` 里写 `run.json`（包含 run id, timestamp, candidate count, join rate, missing rate）
- **验收标准**：AC-L1-3

### Build-S4：L3 反注释（可选）
- **位置**：新文档 `outputs/reports/williams_cross_check.md`
- **改动**：把 VCT Williams 的交叉验证 6 基因（NEUROD2/6/SOX5/NFIA/ZEB2/BCL11B）放到 input/candidates.csv，并与 L1 41 个正对照一起跑
- **验收标准**：在 L1 共识中这些基因位于前 50% 或 L3（Δattr）中不出现的，结果直接写入报告（正或负结果皆可接受)

## Cycle-3：Test — 验收测试（独立手写测试）

- **Unit test**：`tests/test_positive_controls.py` 检查每 run 之 positive controls 排名，从 candidates_ranked.csv 触发
- **Load test（AC-L1-3 审计）**：`tests/test_audit.py` 复查 run.json + data_checksums.txt
- **Static test（AC-L1-1）**：`tests/test_annotate.py` 检查 `normalized.csv` 的状态（ok / unresolved）
- **正对照 comparator**：`tests/test_positive_controls.py` 过一个测试，读取 candidates 里 `expected=True` 的 rank 中位数，并断言 AC-L1-2

每次并入必须至少有一个正对照（如 TBX1），否则报告拒绝。

## Cycle-4：Learn — 决策依据

当在 Build 和 Test 上运行 L1/VCT 双循环内，Learn 的产物必须是几个决策集成：

1. **决定本轮是否 "validated"**——若 AC-L1-1/2/3/4 均通过，写入 `docs/decisions/ADR-003-validated.md`
2. **新发现**：如果不匹配，写负结果（与您的风格一致），并记录哪些现象（例如“ClinGen 连接率不到 60%，应由 L3 路径”）
3. **更新 `docs/decisions/`**：每轮决定是否继续运行、修改哪个参数
4. **同步**：把 Learn 得到的结果写入 VCT 的 WORKLOG 和点评你的复盘报告静候option

---

## 和您已有工作直接对应的Fine mapping

| 您既有资产 | 本手册使用方式 |
|------------|---------------|
| `tools/SIGnature/` 归因 + model_files | 仅用于 L3（假设），不作为 L1 输入 |
| `tools/VirtualCellTool/` 库里 | Build-S1 里 tap 入 L1 候选 |
| `02_disease-williams/04_results/attribution_results.npz` + `results.npz` | 被 L3 （Passive view）使用，不参与 L1 |
| 41 基因清单（每个 micro-deletion 的候选） | Build-S2 中的正对照骨子 |
| CellOracle/SIGnature 收敛基因集 | Build-S4 中反注释的对象 |
| TBX1/ELN/RAI1/GTF2I/KCTD13（您的已答案） | 正对照（expected=True） |

---

## 完整 acceptance criteria（DBTL-ready）

- [ ] AC-L1-1：连接率 ≥ 60%
- [ ] AC-L1-2：已知主效基因在前 10%
- [ ] AC-L1-3：audit synchronized every run
- [ ] AC-L1-4：同一 run 重复排名一致
- [ ] 负结果被文件存档（docs/decisions/）

---

## 常见 fault 供参考

- **ClinGen score 缺失**：ClinGen 并未评级全部待 gene，请把 missing_rate 显示为报告单独项（不要隐形）
- **正对照太重**：TBX1/ELN/KCTD13/RAI1 可能并非所有定义为"清楚遗传学主效基因"，可以（1）关闭 AC-L1-2；或（2）改写为"建议符合"的规定
- **VCT 用 Δattr 的 UI 迷惑**：就算 VCT 里看到 L1 已被显示为输入源，前面的 terminology 也要保留，确保报告里的正反负结果单独表达

---

## 下一步 - 我们团队应该做什么

1. 用 candidates.csv 中的 41 个基因以及8种病标记，跑通 Build-S2（3 命令）
2. AC-L1-1/2/3/4 检查完成
3. 确定合并名单中的第一天（workflow)——像您 WORKLOG 写入
4. 更新 `PROJECT_PROGRESS_REPORT.md` 的“完整 DBTL 闭环”段落：加入 L1–VCT 整合汇报
