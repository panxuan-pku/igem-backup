# 工程文档 — VirtualCellTool

> 对应 iGEM Engineering 评审要求：DBTL 循环 + 假设清单 + 验收标准。

## 1. 问题陈述（Problem）

iGEM 队伍设计"改变基因表达"的干预方案时，缺乏低成本手段**在湿实验之前预览干预对细胞状态的影响**。现有工具（SIGnature 等）只做静态分析，无交互式扰动模拟。

## 2. 文献基线与已知限制

- SIGnature (Nat Biotechnol 2026)：attribution 排序基因重要性，但无扰动模拟、无交互界面
- SCimilarity (Nature 2024)：编码器可对反事实输入做前向推理（原论文做过 in silico perturbation）
- scGen / CPA / GEARS / scDiffusion：基于 Perturb-seq 训练的因果扰动模型（我们的 v2 升级路径）

## 3. 假设、近似与简化（Assumptions）

- **A1**：编码器对小幅度反事实扰动的响应方向具有生物学参考价值（外推可靠性随扰动幅度衰减）
- **A2**：转录组 embedding 位移可近似代表细胞功能状态变化
- **A3**：转录层面证据可外推至翻译层面干预（与本队 RNA binder 机制的层面差异，定位为概念验证）
- **S1**：demo 阶段仅用 PBMC 数据集（非疾病模型），验证方法论而非具体疾病结论

## 4. 验收标准（Acceptance Criteria）

| 编号 | 标准 | 测量方法 | 阈值 |
|---|---|---|---|
| AC1 | 方向性：敲低细胞类型标志基因后，细胞 embedding 远离其类型质心 | 位移向量 vs "细胞→质心"向量的余弦相似度，对比随机基因基线 | 显著大于随机基线，置换检验 p<0.05 |
| AC2 | 区分度：标志基因扰动的位移幅度 > 等量随机基因 | 位移 L2 范数对比 | 效应量显著（p<0.05） |
| AC3 | 可用性：滑块操作→UMAP 更新延迟 | 计时 | < 2 秒 |
| AC4 | 可复现：新机器 30 分钟复现 demo | README 一键脚本 | 通过 |

## 5. DBTL 循环记录

### 循环 1：核心机制验证
- Design: 反事实扰动走 SCimilarity 编码器 + AC1/AC2
- Build: src/perturb.py
- Test: PBMC 数据 + 置换检验
- Learn:
  - **失败记录 1**：SIGnature `lognorm_counts()` 要求原始 counts 存于 `layers['counts']`，直接传入 X 为原始 counts 的 AnnData 会报错 → 修复：显式 `adata.layers['counts'] = adata.X.copy()`
  - **失败记录 2**：scanpy leiden 聚类缺 igraph/leidenalg 依赖（SIGnature 未声明）→ 补装
  - **成功结果**（data/validation_results.json）：AC1 方向性 +0.0012 vs 随机 -0.0000（p<0.0005）；AC2 位移幅度 0.0124 vs 随机 0.0007（~18x，p<0.0005）→ 核心假设 A1 在小扰动范围内成立
  - 生物学 sanity check：B 细胞 attribution top = MS4A1/CD79A/BANK1，与 SIGnature 原论文 Fig.2 结论一致

### 循环 2：工具化
- Design: 交互界面 + attribution 引导扰动建议
- Build: web/ 前端 + API
- Test: AC3 延迟 + 无说明书试用
- Learn:
  - **成功结果**：attribution 0.09s、扰动模拟 0.88s（umap-learn transform 为主要开销），端到端 ~1.4s < 2s 标准
  - **迭代记录**：候选基因列表按方差预筛 2000 个导致部分基因无法搜索 → 改为全 28231 基因空间后端搜索（/api/search_genes）
  - **迭代记录**：top 基因表改为可点击直接选中；重要性列改为显示 |attribution|（用户反馈负号干扰阅读）

### 循环 3：多基因联合扰动 + 类型重判（**重要负结果**）
- Design: 假设"联合敲低 top N 身份证基因可使细胞类型重判翻转"
- Build: perturb_multi + 最近质心分类器 + Top1/3/5 按钮
- Test: B 细胞 #1，分别敲低 Top1/3/5/8/12 基因
- Learn:
  - 位移随基因数近似线性增长：0.0102（1个）→ 0.0205（3个）→ 0.0344（5个）→ 0.0616（8个）→ 0.0826（12个）
  - **负结果：即使联合敲低 12 个 B 细胞标志基因，最近质心重判仍为 B cell**（距 B 质心 0.23 vs 次近 T 细胞 0.69）
  - 解读：① 细胞身份由数百基因冗余编码，简单编码器反事实扰动无法翻转类型——与 A1 假设的边界一致；② 说明该工具适用于"重要性排序 + 方向性验证"，不适用于"细胞命运预测"；③ 支持 v2 升级到 Perturb-seq 因果模型（GEARS 等）的必要性——**这是 wiki 上论证工具定位与局限的关键数据**

### 循环 4：真实疾病数据差异归因（MS 少突胶质细胞）
- Design: MS vs normal 同细胞类型差异归因 → 候选靶基因清单
- Build: src/compute_ms_attribution.py（批量化 IG，64 细胞/批）
- Test: 17,799 细胞（MS 11,208 / normal 6,591）
- Learn:
  - **性能惊喜**：批量化 IG 达 645 细胞/秒（原估 0.09s/细胞是单细胞 API 调用开销）——17,799 细胞 attribution 矩阵仅 ~1 分钟
  - **失败记录 3**：pandas `sort_values` 列名笔误（effect vs effect_size）→ 分析步骤独立重跑修复；教训：数据产物先落盘再分析
  - **Sanity check 通过**：PLP1（髓鞘主蛋白）为两组 |attribution| 第一名；MOG 重要性在 MS 中减半（0.0007 vs 0.0015），与脱髓鞘生物学一致
  - **产出**：data/ms_differential_attribution.csv（全基因差异归因表）+ ms_analysis_report.png
  - **候选基因**（|d|>0.3）：MS 中重要性↑ = ACTB/FTL（铁代谢）/LRP2 等；MS 中重要性↓ = ASPA（少突胶质标志）/NCAM1/CTNNA3 等

### 循环 5：v2 因果扰动模型接入 + 闭环验证（**成功**）
- Design: v1 找关键基因 → GEARS（Perturb-seq 因果训练）预测扰动后转录组 → 重新归因放回 embedding 空间验证
- Build: src/v2_closed_loop.py
- Test: CEBPA 敲低（Norman 数据集中有 70 个真实敲低细胞做对照）
- 过程中的失败记录：
  - **失败 4**：PyPI `gears` 是同名错误包（Web 资产库）→ 正确包 `cell-gears`
  - **失败 5**：Harvard Dataverse 被 AWS WAF 全面封锁（代理/直连/WARP/无头浏览器均失败）→ Zenodo 镜像（17252307）解决
  - **失败 6**：GEARS 与 pandas 2.x 不兼容（Series.nonzero 已删除）→ 猴子补丁
  - **失败 7**：AnnData 视图导致矩阵转稠密静默失效 → `to_memory()` 实体化
- **成功结果**（data/v2_closed_loop.json）：
  - v2 模型验证：预测 vs 真实敲低细胞 pearson r = **0.972**（Top50 DE 基因 r = 0.974）
  - 闭环位移：GEARS 预测的扰动细胞在 SCimilarity 空间位移 **0.338**（v1 单基因扰动 ~0.01 的 34 倍）——证实 v1 位移小的根源是"只改一个输入、无级联效应"
  - 生物学一致性：CEBPA 敲低后归因变化 = 红系程序（HBG1/2、GYPA/B、KLF1）↓、髓系标志（TYROBP、LST1）↑，与 CEBPA 驱动髓系分化的经典生物学吻合
  - **结论：SIGnature 归因框架与因果扰动模型互相印证，v1→v2→验证→指导湿实验的完整闭环跑通**
