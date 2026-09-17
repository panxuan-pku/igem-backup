# iGEM-Microdeletion 项目工作日志

> 项目：iGEM 2026「RNA binder 剂量补偿治疗染色体微缺失病」干实验（计算）部分
> 整理日期：2026-09-01 ｜ 来源：Hermes 会话历史提取（附会话链接）
> 配套文档：`02_disease-williams/05_report/微缺失病计算通路复盘报告.md`（方法论复盘）、`architecture.html`（架构图）

---

## 时间线总览

| 阶段 | 日期 | 主题 | 结果 |
|---|---|---|---|
| ⓪ 项目源头 | 07-27 | SIGnature 论文调研 + 仓库落地 | ✅ 技术路线起点 |
| ① 工具搭建 | 08-13 | VirtualCellTool 3小时冲刺 + GEARS 闭环 | ✅ 平台建成 |
| ② 可行性验证 | 08-16 | 22q11.2 工作流硬检查 | ✅ 基因覆盖确认 |
| ③ 方法学检验 | 08-17 | 归因 vs 真实扰动、GEARS 死路检查 | ⚠️ 负结果 |
| ④ 主线验证 | 08-18 | Williams 全通路（归因+扰动）+ 复盘报告 | ⚠️ 负结果+1 硬资产 |
| ⑤ 汇报与转向 | 08-19 / 08-26 | 汇报打磨 → 方向确定 | ✅ 定位收敛 |
| ⑥ 整理归档 | 09-01 | 目录重构 ×2 + 架构图 | ✅ 本仓库成形 |

---

## ⓪ 07-27：项目源头——SIGnature 论文调研（会话 20260727_142714）

**做了什么**：调研 Genentech 论文 *Scoring gene importance by interpreting single-cell foundation models*（Nature Biotechnology, doi:10.1038/s41587-026-03112-5），完整覆盖背景、技术思路与结果。

**关键内容**：
- **核心方法**：把 XAI 归因（IG/IxG/DeepLIFT）搬到单细胞基础模型上，输出与表达向量同形的"基因重要性分数"；系统 benchmark 5 个 FM × 3 种归因算法，选定 **SCimilarity + IG** 组合
- **招牌能力**：attribution 可对超大图谱预计算（22M 细胞/412 研究存入 TileDB），基因集签名查询分钟级完成；MS1 案例（脓毒症签名 → 新发现川崎病/SFTS/HLH 关联 + 血清诱导实验验证）
- **局限声明**（论文自己承认）：归因质量受限于 FM 表征能力；**归因 ≠ 因果**

**修改原因/决策**：这是本项目的**技术路线起点**——同日执行了两个关键动作：
1. `git clone https://github.com/Genentech/SIGnature` 到 `~/Desktop/github/SIGnature`，VS Code 打开并解析了仓库框架（核心 ~2200 行，4 个模型包装器、3 个官方 notebook）
2. 确定技术资源路线：PyPI 包 `sc-signature` + Zenodo 社区预计算归因数据 + 模型文件（后续 8 月中下载解压 Zenodo 17903196 模型包、搭建 .venv 环境）

> 注：08-13 之前的会话以调研为主（另有 5 月末的罕见病自查指南等工作，属 iGEM 团队其他子项目，未列入本日志范围）。SIGnature 运行环境（.venv py3.11 + torch/captum + 模型包解压）的具体搭建操作散落在 8 月上旬多个会话中，至 08-13 已就绪并用于 VirtualCellTool。

---

## ① 08-13：VirtualCellTool 搭建（会话 20260813_120050）

**目标**：3 小时内建成可演示的"虚拟细胞"交互平台，对齐 iGEM Engineering/Contribution/Attributions 三大评审支柱。

**做了什么（M1–M7 里程碑看板推进）**：
- 建工程文档骨架：问题陈述、假设清单、验收标准（AC1 方向性 / AC2 区分度 / AC3 延迟 / AC4 可复现）、`ATTRIBUTIONS.md` 归属登记表（从第一天维护）
- PBMC 3k 真实数据 → SCimilarity embedding → UMAP 预处理（`prepare_data.py`）
- 核心模块：`perturb.py` 扰动引擎（改基因表达→embedding 位移）、`attribute.py`（Captum IG 归因）、`web/app.py` FastAPI 交互前端（点细胞→归因→拖滑块扰动→UMAP 箭头）

**修改原因**：SIGnature（无界面）、SCimilarity（只进不出）、GEARS（无归因/前端）三个工具彼此割裂，没人把"归因找靶 → 扰动预览 → 交互演示"缝成闭环——这是明确的 Contribution 定位。

**验证结果**：AC1/AC2 双通过（方向性 p<0.0005），AC3 端到端 1.4 秒。B 细胞 attribution top = MS4A1/CD79A/BANK1，复现原论文。

**同日追加**：
- **GEARS v2 闭环**（`v2_closed_loop.py`）：接入 GEARS（cell-gears 0.1.2，HuggingFace 预训练权重）+ Norman 数据（Zenodo 镜像，官方 dataverse 被 WAF 封锁）。CEBPA 敲低验证：预测 vs 真实 r=0.972，embedding 位移 0.338（v1 的 34 倍）。**踩坑记录**：PyPI 的 `gears` 是错包要用 cell-gears；pandas2 需 Series.nonzero 猴子补丁；AnnData 视图需 `to_memory()` 才能转稠密。
- **首个真实疾病数据集**：CELLxGENE 16c1e722「Progressive MS 少突胶质细胞」（17,799 细胞）。批量 IG 645 细胞/秒算出真实归因矩阵，Sanity check 通过（PLP1 两组第一、MOG 在 MS 中重要性减半）。**坑**：CELLxGENE h5ad 的 var_names 是 Ensembl ID，需用 `var['feature_name']` 映射基因符号。
- 产出 iGEM Attributions/Contributions 幻灯内容（含 AI 辅助逐文件标注原则）。

---

## ② 08-16：22q11.2DS 工作流硬检查（会话 20260816_172608）

**问题**：要不要换更广的基础模型？

**检查结论**：
1. **基因覆盖不是问题**——SCimilarity 的 28,231 基因空间对微缺失病关键基因几乎全覆盖（22q11 9/10、Williams 7/7、Angelman 4/4、SMS 3/3）；反而 scGPT（3000 HVG）、Geneformer（~16k）会缩减空间。
2. **真正风险在细胞状态覆盖**（脑类器官 vs 成体组织），需实测而非猜测。
3. **重新定位猜想**：微缺失病致病基因本来就是已知的，"归因发现新致病基因"不成立；正确用法是差异归因刻画疾病细胞状态、发现缺失基因下游受影响程序（候选生成）。

**修改原因/决策**：不换模型，先跑 22q11.2DS（GSE244005）做 3 个 sanity check 再决定。

---

## ③ 08-17：方法学检验——归因的价值边界（会话 20260817_084149）

**做了什么**：在 Norman 真实单基因敲低数据上，算「差分归因 vs 真实差异表达」的相关性。

**结果与结论**：
| 检验 | 结果 | 结论 |
|---|---|---|
| \|DE\| vs \|Δattr\|（5 个基因） | r ≈ 0.81–0.85 | 归因追踪真实生物学，扰动基因能被捞回（KLF1 排第 1） |
| 符号相关 | r ≈ 0.03–0.12 | 归因**给不了方向** |
| 归因 vs 真实扰动效应（n=101） | r = 0.02 (p=0.83) | 归因**不预测因果**（预测性测试证实） |

**关键判断**：r=0.8 很可能是"机械相关"（IG 本质 ∝ 表达量×梯度），归因 ≈ 差异表达，无独立信息。**归因只能当候选生成器，不能当证明器。**

**同日：GEARS 死路检查**——查 8 种微缺失病的 41 个候选基因在 Norman 共表达图中的覆盖：主效基因**全军覆没**（TBX1/UBE3A/GTF2I/RAI1 全不在图内）。根因：所有 Perturb-seq 数据集都是癌细胞系（K562 等），根本不表达发育/神经基因 → 这是**结构性死路**，不是换数据集能救的。替代方案：回到 SCimilarity 嵌入层做"恢复 G → 朝健康态位移"的药效验证。

---

## ④ 08-18：Williams 主线全通路 + 复盘报告（会话 20260818_104152）

**做了什么**（当日完成下载→分析→成文全流程）：
1. **数据**：下载 GSE283473（Williams 脑类器官，CTRL1-3 + WS1-3，6 样本 ~96,969 细胞）
2. **疾病选择 pivot**：原计划 22q11.2DS + TBX1 → 实测 TBX1 在脑类器官仅 15/9293 细胞表达（心脏 TF）→ **pivot 到 Williams + GTF2I**（脑表达 TF，82% 细胞，均值 3.39）
3. **预处理**（`preprocess.py`）：合并 QC → HVG 3000 + **强制保留 7q11.23 区段 20 基因**（防止主效基因被 HVG 筛掉）→ Leiden 16 cluster → `processed.h5ad`（96,969 × 3,016）
4. **SIGnature 差异归因**（`attribution_analysis.py`）：5000+5000 子采样 → SCimilarity 对齐 → IG 批量归因 → 差异归因（WS−CTRL）。**结果**：Δattr vs DE **r=0.949**（≈差异表达镜像）；疾病信号=神经元分化基因（NEUROD2/6、SOX5、NFIA）；**删失基因自身 Δattr≈0**
5. **CellOracle 扰动验证**（`celloracle_run.py`）：hg38 promoter base GRN → GTF2I KO（→0）/OE（2×剂量补偿）→ 对比真实疾病 DE。**结果**：KO r=−0.046、OE r=+0.072，全局 ≈0 无系统信号；但 top 被恢复基因方向正确（SOX5/NEUROD2/NFIA 等神经基因被 OE 往上拉）
6. **最硬正面结果**：SIGnature 与 CellOracle 两个独立方法**收敛到同一候选集**（神经元分化程序：NEUROD2/6、SOX5、NFIA、ZEB2、BCL11B）——交叉验证成立
7. **复盘报告**：`微缺失病计算通路复盘报告.md/docx/pdf`（五步通路逐环节【问题/思路/方法/结果/不足】+ 22 术语表 + 三个根本性不足），按用户配色（H1 红 #CC0000）排版，html2pdf.py（Playwright）转 PDF

**负结果的根因分析**（写进报告的三个根本不足）：
1. **翻译层盲区**：RNA binder 作用在蛋白层，所有 mRNA 模型假设 mRNA↔蛋白耦合——药效在模型结构上不可见
2. **单基因 vs 多基因错配**：微缺失 ~25 基因同时单倍不足，段内只有 GTF2I 一个 TF 可扰
3. **删失基因稳态 mRNA"隐身"**：DE≈0、Δattr≈0，单倍不足效应在稳态转录组测不到

---

## ⑤ 08-19 / 08-26：汇报打磨与方向收敛（会话 20260819_104655、20260826_182830）

**08-19 汇报反思**：把负结果重构为 DBTL 叙事资产——"归因 vs 因果是两个独立的量"是研究生级的方法论边界发现；定位从"找靶点"收敛到"给下游 RNA binder 设计选靶"。明确 r=0.02 必须主动讲，不能藏。

**08-26 方向确定**（团队汇报后）：新目标 = 从微缺失区基因列表筛单一主效基因作 AAV+RNA binder 靶点。确立的方法论结论：
- **SIGnature 原理上筛不出主效基因**：归因≠因果 + 区域内共缺失=完全共线不可辨识 + 半剂量仅 50% 信号弱
- **主效基因必须相对"表型+细胞类型"定义**（Williams 区 ELN/GTF2I/LIMK1 各管一表型）
- **证据金字塔替代单一模型**：L1 人类遗传学（LOEUF/pLI/pHaplo）→ L2 真实 Perturb-seq → L3 虚拟扰动仅做机制假设+诚实报负结果
- **必做正对照**：RAI1/ELN/TBX1 已知答案反测流程排序能力
- A/B 线解耦：药物线靶点用文献结论定，工具线独立作为 Contribution 交付物

---

## ⑥ 09-01：项目整理归档（本仓库）

**第一轮**（应"整理工作目录"需求）：`CellOracle_Williams/` 内部按流水线重排为 `01_rawdata → 02_scripts → 03_intermediate → 04_results → 05_report` 五层编号结构；同步修正 3 个脚本内的硬编码路径；新增 README。

**第二轮**（应"整个项目版图"需求）：新建总目录 `~/Desktop/github/iGEM-Microdeletion/`，把 4 个散落仓库收拢——
```
01_disease-22q11.2/   废弃 pivot 案例（TBX1 脑不表达证据，保留）
02_disease-williams/  主线五层结构 + 复盘报告
tools/SIGnature/      归因框架（.venv + 235MB 模型）
tools/VirtualCellTool/ 交互 demo（端口 8377）
```
批量修正 **17 个文件**的旧路径（`~/Desktop/github/SIGnature` 等 → 新位置）；验证 .venv 与核心模块 import 正常；记忆系统同步更新。

**同日：archify skill 安装 + 架构图**：
- 诊断 Desktop Skill Market 下载失败原因：该 skill 仓库结构非标准（SKILL.md 在 `archify/` 子目录），skills.sh 索引抓取失效
- 手动从 GitHub 装入完整包（SKILL.md + references + bin + schemas + renderers + scripts 校验运行器），`doctor` 全绿
- 产出 `architecture.html`：五步通路映射为架构图（数据主线 / SIGnature+CellOracle 双工具分叉汇合「双方法交叉验证」/ 22q11 pivot 虚线 / tools 边界），showcase 级校验 9/9 通过，浏览器证据 pass

---

## 关键数字速查

| 指标 | 数值 | 含义 |
|---|---|---|
| GEARS held-out r | 0.972 | v2 闭环预测 vs 真实扰动（Norman/CEBPA） |
| 归因 vs 真实扰动 | r=0.02 | 归因不预测因果（n=101） |
| 差异归因 vs 差异表达 | r=0.949 | 归因≈DE 镜像，无独立信息 |
| GTF2I KO / OE vs 疾病 DE | −0.046 / +0.072 | 单基因扰动无系统信号 |
| Williams 数据 | 96,969 细胞 × 3,016 基因，16 cluster | GSE283473 |
| GTF2I 表达 | 82% 细胞，均值 3.39 | pivot 依据 |
| VCT 延迟 / 方向性 | 1.4s / p<0.0005 | AC1/AC2/AC3 通过 |

## 会话存档索引

| 日期 | 会话 | 主题 |
|---|---|---|
| 07-27 | @session:default/20260727_142714_bf5a5d3e | SIGnature 论文调研 + 仓库克隆（项目起点） |
| 08-13 | @session:default/20260813_120050_362dbb3f | VirtualCellTool 搭建 + GEARS 闭环 |
| 08-16 | @session:default/20260816_172608_b32271a2 | 22q11.2 工作流硬检查 |
| 08-17 | @session:default/20260817_084149_d3d9be1b | 归因方法学检验 + GEARS 死路 |
| 08-18 | @session:default/20260818_104152_0aea53d1 | Williams 全通路 + 复盘报告 |
| 08-19 | @session:default/20260819_104655_37786720 | 汇报反思 |
| 08-26 | @session:default/20260826_182830_c6ec3c91 | 主效基因筛选方向确定 |
| 09-01 | （本会话） | 目录重构 + archify 架构图 |
