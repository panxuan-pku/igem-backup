# ATTRIBUTIONS — 工作归属登记表

> iGEM 评审要求：明确区分自有工作 vs 文献/过往队伍/外部工具。每引入一个新资源当场登记。

## 外部模型与数据

| 组件 | 来源 | 用途 | 许可/引用 |
|---|---|---|---|
| SCimilarity 预训练权重 + gene_order.tsv | Genentech, Zenodo record 17903196 | 细胞 embedding 编码器 | Heimberg et al., Nature 2024 |
| SIGnature Python 包 | github.com/Genentech/SIGnature | attribution 管线、数据对齐 | Biancalani et al., Nat Biotechnol 2026 |
| PBMC 3k 数据集 | 10x Genomics / scanpy 内置 | demo 与验证用真实细胞数据 | 10x Genomics 公开数据 |
| Progressive MS 少突胶质细胞数据集 | CELLxGENE collection 16c1e722（Oligodendrocytes in MS, 17,799 细胞, MS vs normal） | 真实疾病数据差异归因 | CELLxGENE 公开数据 |
| Captum (Integrated Gradients) | Meta AI | IG attribution 算法 | github.com/pytorch/captum |
| GEARS (cell-gears 0.1.2) | snap-stanford (Roohani et al., Nat Biotechnol 2024) | v2 因果扰动预测模型 | github.com/snap-stanford/GEARS |
| GEARS 预训练权重 | HuggingFace matthewshu/gears-norman（sc-interp 项目） | Norman 上预训练的 GEARS | Roohani et al. 2024 / sc-interp |
| GEARS 数据镜像（norman.zip, gene2go, essential genes） | Zenodo record 17252307（官方源 Harvard Dataverse 被 WAF 封锁后的镜像） | GEARS 训练数据与 GO 注释 | Norman et al., Science 2019 |
| CIPHER 线性响应理论 | Kuznets-Speck et al., "CIPHER: Covariance-based Inference of Perturbation...", bioRxiv 2025 | v3 线性响应扰动预测引擎 | Kuznets-Speck et al. (Northwestern Goyal Lab) |
| Nature Methods 2025 基准（线性基线） | Ahlmann-Eltze et al., Nat Methods 2025, DOI 10.1038/s41592-025-02772-6 | control-mean + additive 强制基线参考 | const-ae / Wolf lab |

## 自有工作（本队原创）

| 模块 | 文件 | 说明 |
|---|---|---|
| 反事实扰动引擎 | src/perturb.py | 修改基因表达→重算 embedding→位移分析 |
| 交互式虚拟细胞网页 | web/ | 滑块调表达量→UMAP 实时显示细胞状态迁移 |
| 验证分析 | src/validate.py | AC1/AC2 定量验收测试 |
| 使用文档 | README.md, docs/ | 面向未来 iGEM 队伍 |
| CIPHER 线性响应引擎 | src/cipher_engine.py | 统计物理涨落-耗散定理，仅需对照细胞数据预测全转录组扰动响应 |
| 线性基线引擎 | src/linear_baseline.py | Nature Methods 2025 强制基线（control-mean + additive） |
| 路径管理 | src/paths.py | 集中式根目录相对路径解析 |
| 数据管线 | src/prepare_data.py | PBMC3k → SCimilarity 对齐 → embedding → UMAP |

## AI 辅助声明

| 文件/模块 | AI 工具 | 人工工作 |
|---|---|---|
| （逐文件登记） | Hermes Agent (Nous Research) | 设计决策、参数调优、结果判读 |
