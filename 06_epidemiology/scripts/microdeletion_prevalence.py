# -*- coding: utf-8 -*-
"""
Chromosomal microdeletion syndromes — epidemiology figures.
Metrics: birth prevalence, 22q11.2 incidence, de novo fraction, birth vs adult prevalence.
CI for count-based studies computed with Clopper-Pearson exact binomial.
Literature ranges are reported min-max of published estimates (not statistical CI).
Exports every figure as PNG (raster) + PDF/SVG (vector).
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import beta as _beta

FIG_DIR = "outputs/figures"
DATA_DIR = "outputs/data"
CB = "#1f77b4"   # count-based / primary
LR = "#9e9e9e"   # literature
RED = "#d62728"

def cp_ci(k, n):
    lo = 0.0 if k == 0 else _beta.ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else _beta.ppf(0.975, k + 1, n - k)
    return lo, hi

def per10k(p):
    return p * 10000.0

def save(fig, name):
    for ext in ("png", "pdf", "svg"):
        fig.savefig(f"{FIG_DIR}/{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)

# ======================================================================
# Figure 1: birth prevalence summary (labels OUTSIDE error bars)
# ======================================================================
PRIMARY = [
    dict(name="22q11.2 (DiGeorge/VCFS)", kind="count", k=14, n=30074,
         src="Blagojevic 2021, Ontario newborn screening (CMAJ Open)"),
    dict(name="1q21.1 deletion", kind="count", k=6, n=12252,
         src="Smajlagić 2020, MoBa Norway (Eur J Hum Genet)"),
    dict(name="16p11.2 (proximal)", kind="count", k=3, n=8329,
         src="Cooper 2011, adult controls (Nat Genet)"),
    dict(name="15q11-q13 (PWS/Angelman)", kind="count", k=2, n=6813,
         src="Tucker 2013, French-Canadian newborns"),
    dict(name="1p36 deletion", kind="count", k=1, n=6813,
         src="Tucker 2013; Heilstedt 2003 (1 in 5,000)"),
    dict(name="15q13.3 deletion", kind="range", pt=2.5, lo=1.8, hi=3.3,
         src="Gillentine 2018 (J Hum Genet)"),
    dict(name="Williams (7q11.23)", kind="range", pt=1.0, lo=0.5, hi=1.3,
         src="GeneReviews / Orphanet (1 in 7,500-20,000)"),
    dict(name="Cri-du-chat (5p)", kind="range", pt=0.5, lo=0.2, hi=0.67,
         src="Orphanet (1 in 15,000-50,000)"),
    dict(name="Smith-Magenis (17p11.2)", kind="range", pt=0.5, lo=0.4, hi=0.67,
         src="GeneReviews (1 in 15,000-25,000)"),
    dict(name="Koolen-de Vries (17q21.31)", kind="range", pt=0.33, lo=0.18, hi=0.63,
         src="GeneReviews (1 in 16,000-55,000)"),
    dict(name="3q29 deletion", kind="range", pt=0.33, lo=0.2, hi=0.5,
         src="GeneReviews / literature (~1 in 30,000)"),
    dict(name="Wolf-Hirschhorn (4p)", kind="range", pt=0.2, lo=0.1, hi=0.3,
         src="Orphanet (~1 in 50,000)"),
    dict(name="Phelan-McDermid (22q13)", kind="range", pt=0.2, lo=0.1, hi=0.3,
         src="Orphanet / literature (rare, ~1 in 50,000)"),
    dict(name="2q37 deletion", kind="range", pt=0.1, lo=0.05, hi=0.15,
         src="literature (~1 in 100,000)"),
]

rows = []
for d in PRIMARY:
    r = dict(name=d["name"], src=d["src"], kind=d["kind"])
    if d["kind"] == "count":
        lo, hi = cp_ci(d["k"], d["n"])
        r["pt"] = per10k(d["k"] / d["n"]); r["lo"] = per10k(lo); r["hi"] = per10k(hi)
        r["n_cases"] = d["k"]; r["n_total"] = d["n"]
    else:
        r["pt"] = d["pt"]; r["lo"] = d["lo"]; r["hi"] = d["hi"]
        r["n_cases"] = None; r["n_total"] = None
    r["one_in"] = round(10000.0 / r["pt"])
    rows.append(r)

df = pd.DataFrame(rows).sort_values("pt", ascending=True).reset_index(drop=True)
df.to_csv(f"{DATA_DIR}/microdeletion_birth_prevalence.csv", index=False)

fig, ax = plt.subplots(figsize=(10.2, 7.4))
y = np.arange(len(df))
for i, r in df.iterrows():
    color = CB if r["kind"] == "count" else LR
    ls = "solid" if r["kind"] == "count" else "dashed"
    ax.barh(i, r["pt"], color=color, alpha=0.85, height=0.62, zorder=3)
    ax.errorbar(r["pt"], i, xerr=[[r["pt"] - r["lo"]], [r["hi"] - r["pt"]]],
                fmt="none", ecolor="#333333", elinewidth=1.4, capsize=3, ls=ls, zorder=4)
    # label placed to the RIGHT of the upper CI bound, clear of the error bar
    ax.annotate(f"1 in {r['one_in']:,}", xy=(r["hi"] * 1.35, i),
                va="center", ha="left", fontsize=8.2, color="#222222", zorder=5)
ax.set_yticks(y)
ax.set_yticklabels(df["name"], fontsize=9.5)
ax.set_xscale("log")
ax.set_xlim(0.06, 70)
ax.set_xlabel("Birth prevalence (per 10,000 live births)", fontsize=11)
ax.set_title("Birth prevalence of common chromosomal microdeletion syndromes",
             fontsize=12.5, fontweight="bold")
ax.grid(True, axis="x", which="both", ls=":", alpha=0.4, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
import matplotlib.patches as mpatches
ax.legend(handles=[
    mpatches.Patch(color=CB, label="Population count — exact 95% CI"),
    mpatches.Patch(color=LR, label="Literature estimate — reported range"),
], loc="lower right", fontsize=8.5, frameon=False)
fig.tight_layout()
save(fig, "microdeletion_birth_prevalence")

# ======================================================================
# Figure 2: 22q11.2 forest plot (multiple studies) + incidence annotation
# ======================================================================
q22 = [
    dict(label="Panamonta 2018 systematic review (pooled 6 studies)", k=156, n=1111336),
    dict(label="Oskarsdóttir 2004 Sweden (Western Sweden)", k=None, n=None, pt=1.41),
    dict(label="Sørensen 2010 Denmark (dried blood spots, 7/25,704)", k=7, n=25704),
    dict(label="Smajlagić 2020 MoBa Norway", k=1, n=12252),
    dict(label="Blagojevic 2021 Ontario newborn screening", k=14, n=30074),
]
qrows = []
for d in q22:
    if d["k"] is not None:
        lo, hi = cp_ci(d["k"], d["n"])
        qrows.append(dict(label=d["label"], pt=per10k(d["k"] / d["n"]),
                          lo=per10k(lo), hi=per10k(hi)))
    else:
        qrows.append(dict(label=d["label"], pt=d["pt"], lo=np.nan, hi=np.nan))
qdf = pd.DataFrame(qrows)

fig, ax = plt.subplots(figsize=(9.2, 4.8))
y = np.arange(len(qdf))[::-1]
for i, r in qdf.iterrows():
    ax.plot(r["pt"], i, "o", color=CB, zorder=4)
    if np.isfinite(r["lo"]):
        ax.errorbar(r["pt"], i, xerr=[[r["pt"] - r["lo"]], [r["hi"] - r["pt"]]],
                    fmt="none", ecolor="#333333", elinewidth=1.5, capsize=3, zorder=4)
    ax.annotate(f"{r['pt']:.2f}", xy=(r["pt"], i), xytext=(6, 2),
                textcoords="offset points", fontsize=8.5, color="#222222", va="bottom")
ax.set_yticks(y)
ax.set_yticklabels(qdf["label"], fontsize=9)
ax.set_xlabel("22q11.2 deletion birth prevalence (per 10,000 live births)", fontsize=10.5)
ax.set_title("22q11.2 deletion syndrome — population-based estimates", fontsize=12, fontweight="bold")
ax.axvline(4.7, color=RED, ls="--", lw=1.2)
ax.grid(True, axis="x", ls=":", alpha=0.4, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_xlim(0, 9)
# incidence note
ax.annotate("Incidence (Sweden, Oskarsdóttir 2004):\n14.1 per 100,000 live births / year (= 1.41 / 10,000)",
            xy=(0.995, 0.02), xycoords="axes fraction", ha="right", va="bottom",
            fontsize=8.2, color="#444444",
            bbox=dict(boxstyle="round,pad=0.35", fc="#f5f5f5", ec="#cccccc", lw=0.6))
fig.tight_layout()
save(fig, "22q11_2_forest")

# ======================================================================
# Figure 3: de novo fraction by syndrome (NEW metric)
# ======================================================================
DENOVO = [
    dict(name="Williams (7q11.23)", v=95, lo=None, hi=None, note="most de novo (GeneReviews)"),
    dict(name="22q11.2 (DiGeorge/VCFS)", v=90, lo=None, hi=None, note=">90% de novo for 3 Mb deletion (GeneReviews)"),
    dict(name="1p36 deletion", v=90, lo=None, hi=None, note="mostly de novo"),
    dict(name="Smith-Magenis (17p11.2)", v=90, lo=None, hi=None, note="most de novo"),
    dict(name="Cri-du-chat (5p)", v=87, lo=85, hi=90, note="~85–90% de novo"),
    dict(name="Wolf-Hirschhorn (4p)", v=85, lo=None, hi=None, note="~85% de novo"),
    dict(name="PWS/Angelman (15q11-q13)", v=70, lo=None, hi=None, note="deletion typically de novo (~70% of PWS)"),
    dict(name="16p11.2 (proximal)", v=68, lo=60, hi=76, note="60–76% de novo (meta-analysis)"),
    dict(name="1q21.1 deletion", v=33, lo=None, hi=None, note="often inherited (MoBa: 2/6 de novo)"),
]
dn = pd.DataFrame(DENOVO).sort_values("v", ascending=True).reset_index(drop=True)
dn.to_csv(f"{DATA_DIR}/microdeletion_denovo_fraction.csv", index=False)

fig, ax = plt.subplots(figsize=(8.6, 5.4))
y = np.arange(len(dn))
for i, r in dn.iterrows():
    ax.barh(i, r["v"], color=CB, alpha=0.85, height=0.62, zorder=3)
    if r["lo"] is not None:
        ax.errorbar(r["v"], i, xerr=[[r["v"] - r["lo"]], [r["hi"] - r["v"]]],
                    fmt="none", ecolor="#333333", elinewidth=1.3, capsize=3, zorder=4)
    ax.annotate(f"{int(r['v'])}%", xy=(r["v"], i), xytext=(6, 0),
                textcoords="offset points", va="center", fontsize=8.5, color="#222222")
ax.set_yticks(y)
ax.set_yticklabels(dn["name"], fontsize=9.5)
ax.set_xlim(0, 108)
ax.set_xlabel("Proportion of cases that are de novo (%)", fontsize=11)
ax.set_title("De novo fraction by microdeletion syndrome", fontsize=12.5, fontweight="bold")
ax.grid(True, axis="x", ls=":", alpha=0.4, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.annotate("Remainder = inherited from a (usually mildly affected) parent.\nValues approximate; see report for sources.",
            xy=(0.01, -0.16), xycoords="axes fraction", fontsize=8, color="#555555")
fig.tight_layout()
save(fig, "microdeletion_denovo_fraction")

# ======================================================================
# Figure 4: birth vs adult population prevalence (selection effect)
# ======================================================================
# adult UK Biobank carrier counts (Kendall 2017, n=151,659): 22q11.2 = 5, 16p11.2 = 44
n_ukb = 151659
groups = [
    ("22q11.2\n(DiGeorge/VCFS)", 4.66, (2.55, 7.81), 5 / n_ukb),
    ("16p11.2\n(proximal)", 2.94, None, 44 / n_ukb),
]
birth = np.array([g[1] for g in groups])
adult = np.array([g[3] for g in groups]) * 10000.0

fig, ax = plt.subplots(figsize=(7.4, 4.6))
x = np.arange(len(groups)); w = 0.34
b1 = ax.bar(x - w / 2, birth, w, color=CB, label="Birth prevalence\n(newborn screening)", zorder=3)
b2 = ax.bar(x + w / 2, adult, w, color="#ff7f0e", label="Adult population\n(UK Biobank, Kendall 2017)", zorder=3)
# CI for 22q11.2 birth
ax.errorbar(x[0] - w / 2, birth[0], yerr=[[birth[0] - 2.55], [7.81 - birth[0]]],
            fmt="none", ecolor="#333333", elinewidth=1.3, capsize=3, zorder=4)
for xi, bi, ad in zip(x, birth, adult):
    ax.annotate(f"{bi:.2f}", (xi - w / 2, bi), textcoords="offset points", xytext=(0, 3),
                ha="center", fontsize=8.5)
    ax.annotate(f"{ad:.2f}", (xi + w / 2, ad), textcoords="offset points", xytext=(0, 3),
                ha="center", fontsize=8.5)
ax.set_xticks(x)
ax.set_xticklabels([g[0] for g in groups], fontsize=10)
ax.set_ylabel("Prevalence (per 10,000)", fontsize=11)
ax.set_title("Birth vs adult prevalence — selection & penetrance", fontsize=12, fontweight="bold")
ax.legend(fontsize=8.5, frameon=False, loc="upper right")
ax.grid(True, axis="y", ls=":", alpha=0.4, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.set_ylim(0, 9.5)
ax.annotate("22q11.2: severe phenotype + early mortality →\n~93% lower in adults.\n16p11.2: incomplete penetrance → similar\nin adults vs newborns.",
            xy=(0.01, 0.04), xycoords="axes fraction", ha="left", va="bottom",
            fontsize=8.5, color="#444444",
            bbox=dict(boxstyle="round,pad=0.35", fc="#f5f5f5", ec="#cccccc", lw=0.6))
fig.tight_layout()
save(fig, "microdeletion_birth_vs_adult")

print("done")