import os
os.environ.setdefault("HTTPS_PROXY", "http://127.0.0.1:7897")
os.environ.setdefault("HTTP_PROXY", "http://127.0.0.1:7897")
from celloracle.data.load_promoter_base_GRN import load_human_promoter_base_GRN

df = load_human_promoter_base_GRN(version="hg38_gimmemotifsv5_fpr2")
print("shape:", df.shape)
print("columns:", list(df.columns)[:20])
print("index name:", df.index.name, "| index[:5]:", list(df.index[:5]))
print("TBX1 是否作为列(TF):", "TBX1" in list(df.columns))
print("dtype:", df.dtypes.iloc[0])
print("\n前3行前3列:")
print(df.iloc[:3, :3])
# 看非零值分布
import numpy as np
vals = df.values
print("\n值唯一性:", sorted(set(vals.ravel()))[:10], "| 非零比例:", round((vals != 0).mean(), 4))
