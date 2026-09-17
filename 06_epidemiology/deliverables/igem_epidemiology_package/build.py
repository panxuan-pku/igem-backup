# -*- coding: utf-8 -*-
"""Build the iGEM-ready epidemiology package (self-contained bilingual HTML + report.md + README)."""
import os, shutil, re

FIG_SRC = "outputs/figures"   # source SVG/PNG figures (moved here in reorg)
DATA_SRC = "outputs/data"     # source CSV tables
PKG = os.path.join("outputs", "deliverables", "igem_epidemiology_package")
FIG = os.path.join(PKG, "figures")
DATA = os.path.join(PKG, "data")
for d in (PKG, FIG, DATA):
    os.makedirs(d, exist_ok=True)

FIGURES = [
    "microdeletion_birth_prevalence",
    "22q11_2_forest",
    "microdeletion_denovo_fraction",
    "microdeletion_birth_vs_adult",
]

def load_svg_inline(name):
    p = os.path.join(FIG_SRC, name + ".svg")
    txt = open(p, encoding="utf-8").read()
    txt = re.sub(r"<\?xml[^>]*\?>", "", txt)
    txt = re.sub(r"<!DOCTYPE[^>]*>", "", txt)
    return txt.strip()

for name in FIGURES:
    for ext in ("svg", "png"):
        shutil.copy(os.path.join(FIG_SRC, f"{name}.{ext}"), os.path.join(FIG, f"{name}.{ext}"))
for csv in ("microdeletion_birth_prevalence.csv", "microdeletion_denovo_fraction.csv"):
    shutil.copy(os.path.join(DATA_SRC, csv), os.path.join(DATA, csv))

SVG = {n: load_svg_inline(n) for n in FIGURES}

# ----------------------------------------------------------------------
HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Microdeletion Syndromes &mdash; Epidemiological Overview</title>
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
         line-height: 1.6; color: #1a1a1a; max-width: 980px; margin: 0 auto; padding: 24px 20px 60px; }
  h1 { font-size: 1.9em; line-height: 1.25; margin-bottom: .2em; }
  h2 { font-size: 1.35em; margin-top: 2.2em; border-bottom: 2px solid #1f77b4; padding-bottom: .25em; }
  .lead { font-size: 1.05em; color: #333; }
  .cn { color: #555; font-size: .95em; background: #f6f8fa; border-left: 3px solid #9e9e9e;
        padding: 8px 12px; border-radius: 4px; margin: 10px 0; }
  figure { margin: 18px 0; }
  figure svg { width: 100%; height: auto; }
  figcaption { font-size: .85em; color: #555; margin-top: 4px; }
  table { border-collapse: collapse; width: 100%; font-size: .88em; margin: 12px 0; }
  th, td { border: 1px solid #ddd; padding: 6px 8px; text-align: left; }
  th { background: #eef3f8; }
  tr:nth-child(even) td { background: #fafbfc; }
  ol.refs { font-size: .85em; padding-left: 1.4em; }
  ol.refs li { margin-bottom: .5em; }
  .note { font-size: .85em; color: #666; }
  a { color: #1f77b4; }
</style>
</head>
<body>
<article>
"""

HTML_FOOT = """
</article>
</body>
</html>
"""

def fig(html, name, caption):
    return html + f"\n<figure>\n{SVG[name]}\n<figcaption>{caption}</figcaption>\n</figure>\n"

html = HTML_HEAD
html += """
<h1>Chromosomal Microdeletion Syndromes: Epidemiological Overview</h1>
<p class="lead">Background data for our dosage-compensation strategy &mdash;
birth prevalence, incidence, <em>de novo</em> rate, and the birth&rarr;adult prevalence gap
across the microdeletion syndromes in our disease panel.</p>
<p class="cn">中文说明：本页汇总我们疾病面板中染色体微缺失综合征的流行病学背景数据，
用于支撑「剂量补偿治疗」的必要性与疾病负担论证。单位统一为<b>每 10,000 例活产</b>（/万）。
&quot;计数来源&quot;的置信区间为 Clopper&ndash;Pearson 精确 95% CI；&quot;文献估计&quot;为已发表范围（非统计 CI）。</p>
"""

# ---- Section 1: birth prevalence ----
html += """
<h2>1. Birth prevalence</h2>
<p>The most common microdeletion is <b>22q11.2 (DiGeorge/velocardiofacial syndrome)</b>:
contemporary newborn screening gives <b>4.7 / 10,000 live births (95% CI 2.5&ndash;7.8)</b>,
i.e. <b>1 in 2,148</b> [1]. 1q21.1, 16p11.2 and 15q11-q13 follow. Rarer syndromes
(4p Wolf&ndash;Hirschhorn, 22q13 Phelan-McDermid, 2q37) are on the order of 1 in 50,000&ndash;100,000.</p>
<p class="cn">最常见的微缺失是 22q11.2（DiGeorge/VCFS）：安大略主动新生儿筛查给出 4.7/万（1/2,148）。
其次是 1q21.1、16p11.2、15q11-q13；最罕见的是 4p、22q13、2q37 等（约 1/5万–1/10万）。</p>
"""
html = fig(html, "microdeletion_birth_prevalence",
           "Figure 1. Birth prevalence of common microdeletion syndromes (log axis). Blue = population count with exact 95% CI; grey = literature range.")
html += """
<table>
<caption>Table 1. Birth prevalence (per 10,000 live births).</caption>
<thead><tr><th>Syndrome (region)</th><th>Prevalence /10k</th><th>95% CI or range</th><th>~1 in</th><th>Type</th></tr></thead>
<tbody>
<tr><td>22q11.2 (DiGeorge/VCFS)</td><td>4.66</td><td>2.55&ndash;7.81</td><td>2,148</td><td>count (CI)</td></tr>
<tr><td>1q21.1 deletion</td><td>4.90</td><td>1.80&ndash;10.66</td><td>2,042</td><td>count (CI)</td></tr>
<tr><td>16p11.2 (proximal)</td><td>3.60</td><td>0.74&ndash;10.52</td><td>2,800</td><td>count (CI)</td></tr>
<tr><td>15q11-q13 (PWS/Angelman)</td><td>2.94</td><td>0.36&ndash;10.60</td><td>3,400</td><td>count (CI)</td></tr>
<tr><td>15q13.3 deletion</td><td>2.50</td><td>1.80&ndash;3.30</td><td>4,000</td><td>literature</td></tr>
<tr><td>1p36 deletion</td><td>1.47</td><td>0.04&ndash;8.18</td><td>6,800</td><td>count (CI)</td></tr>
<tr><td>Williams (7q11.23)</td><td>1.00</td><td>0.50&ndash;1.30</td><td>10,000</td><td>literature</td></tr>
<tr><td>Cri-du-chat (5p)</td><td>0.50</td><td>0.20&ndash;0.67</td><td>20,000</td><td>literature</td></tr>
<tr><td>Smith-Magenis (17p11.2)</td><td>0.50</td><td>0.40&ndash;0.67</td><td>20,000</td><td>literature</td></tr>
<tr><td>Koolen-de Vries (17q21.31)</td><td>0.33</td><td>0.18&ndash;0.63</td><td>30,000</td><td>literature</td></tr>
<tr><td>3q29 deletion</td><td>0.33</td><td>0.20&ndash;0.50</td><td>30,000</td><td>literature</td></tr>
<tr><td>Wolf-Hirschhorn (4p)</td><td>0.20</td><td>0.10&ndash;0.30</td><td>50,000</td><td>literature</td></tr>
<tr><td>Phelan-McDermid (22q13)</td><td>0.20</td><td>0.10&ndash;0.30</td><td>50,000</td><td>literature</td></tr>
<tr><td>2q37 deletion</td><td>0.10</td><td>0.05&ndash;0.15</td><td>100,000</td><td>literature</td></tr>
</tbody>
</table>
"""

# ---- Section 2: incidence + forest ----
html += """
<h2>2. 22q11.2 across studies &amp; incidence</h2>
<p>Estimates vary 10-fold by <b>ascertainment method</b>: clinical/registry ascertainment
yields ~1.4/10,000, while prospective molecular newborn screening (Ontario 2021) yields
4.7/10,000 [1,7,8,9]. The Swedish population study reports a mean annual <b>incidence</b>
of <b>14.1 / 100,000 live births</b> [7].</p>
<p class="cn">22q11.2 的各研究估计相差约 10 倍，主要由<b>确定方法</b>决定：临床/登记法约 1.4/万，
主动分子筛查（安大略 2021）4.7/万。瑞典人群研究报道年均<b>发病率 14.1/10 万活产</b>。</p>
"""
html = fig(html, "22q11_2_forest",
           "Figure 2. 22q11.2 deletion birth prevalence across population-based studies; red dashed line = Ontario 2021 best estimate.")

# ---- Section 3: de novo ----
html += """
<h2>3. De novo fraction</h2>
<p>Most severe recurrent microdeletions arise <em>de novo</em> (Williams ~95%, 22q11.2 &gt;90%,
1p36/Smith-Magenis ~90%, Cri-du-chat 85&ndash;90%). In contrast, 16p11.2 is de novo in only
60&ndash;76% and 1q21.1 in ~33% &mdash; these are more often inherited from a mildly affected parent [10,11].</p>
<p class="cn">多数重症复发性微缺失为新发（de novo）：Williams ~95%、22q11.2 &gt;90%、1p36/Smith-Magenis ~90%。
而 16p11.2 仅 60&ndash;76% 新发、1q21.1 ~33%，更常遗传自症状较轻的父母。</p>
"""
html = fig(html, "microdeletion_denovo_fraction",
           "Figure 3. Proportion of cases that are de novo (remainder inherited). Values approximate (GeneReviews/literature).")
html += """
<table>
<caption>Table 2. De novo fraction by syndrome.</caption>
<thead><tr><th>Syndrome</th><th>De novo %</th><th>Note</th></tr></thead>
<tbody>
<tr><td>Williams (7q11.23)</td><td>~95</td><td>most de novo</td></tr>
<tr><td>22q11.2 (3 Mb)</td><td>&gt;90</td><td>nested deletions ~60% inherited</td></tr>
<tr><td>1p36 deletion</td><td>~90</td><td>mostly de novo</td></tr>
<tr><td>Smith-Magenis (17p11.2)</td><td>~90</td><td>most de novo</td></tr>
<tr><td>Cri-du-chat (5p)</td><td>85&ndash;90</td><td></td></tr>
<tr><td>Wolf-Hirschhorn (4p)</td><td>~85</td><td></td></tr>
<tr><td>PWS/Angelman (15q11-q13)</td><td>~70</td><td>deletion itself is de novo</td></tr>
<tr><td>16p11.2 (proximal)</td><td>60&ndash;76</td><td>duplications more often inherited</td></tr>
<tr><td>1q21.1 deletion</td><td>~33</td><td>often inherited (MoBa 2/6)</td></tr>
</tbody>
</table>
"""

# ---- Section 4: birth vs adult ----
html += """
<h2>4. Birth vs adult prevalence &mdash; selection &amp; penetrance</h2>
<p>Adult population prevalence is <b>lower</b> than birth prevalence because affected individuals
have reduced fertility and higher early mortality. 22q11.2 collapses from 4.7/10,000 at birth
to <b>0.33/10,000 in adults</b> (UK Biobank, only 5 carriers among ~151,659) &mdash; a ~93% drop
reflecting severity. By contrast, 16p11.2 stays ~2.9/10,000 in adults, consistent with
<b>incomplete penetrance</b> [10]. MoBa found recurrent NDD CNVs in 0.48% of newborns vs
0.35&ndash;0.36% of parents (~1/3 negative selection) [2].</p>
<p class="cn">成人人群患病率<b>低于</b>出生患病率（生育力下降 + 早期死亡）。22q11.2 从出生 4.7/万
降到成人 0.33/万（UK Biobank，约 93% 下降，反映重症）；16p11.2 成人仍约 2.9/万，
与<b>不完全外显</b>一致。MoBa：复发性 NDD-CNV 新生儿 0.48% vs 父母 0.35&ndash;0.36%（约 1/3 负向选择）。</p>
"""
html = fig(html, "microdeletion_birth_vs_adult",
           "Figure 4. Birth (newborn screening) vs adult population prevalence (UK Biobank, Kendall 2017).")

# ---- References ----
html += """
<h2>References</h2>
<ol class="refs">
<li>Blagojevic C, Heung T, Theriault M, et al. Estimate of the contemporary live-birth prevalence of recurrent 22q11.2 deletions: a cross-sectional analysis from population-based newborn screening. <i>CMAJ Open</i> 2021;9:E802&ndash;E809. doi:10.9778/cmajo.20200294</li>
<li>Smajlagi&#263; D, Lavrichenko K, Berland S, et al. Population prevalence and inheritance pattern of recurrent CNVs associated with neurodevelopmental disorders in 12,252 newborns and their parents. <i>Eur J Hum Genet</i> 2021;29:205&ndash;215. doi:10.1038/s41431-020-00707-7</li>
<li>Tucker T, Giroux S, Cl&#233;ment V, Langlois S, Friedman JM, Rousseau F. Prevalence of selected genomic deletions and duplications in a French-Canadian population-based sample of newborns. <i>Mol Genet Genomic Med</i> 2013;1:87&ndash;97. doi:10.1002/mgg3.12</li>
<li>Cooper GM, Coe BP, Girirajan S, et al. A copy number variation morbidity map of developmental delay. <i>Nat Genet</i> 2011;43:838&ndash;846. doi:10.1038/ng.909</li>
<li>Heilstedt HA, Ballif BC, Howard LA, et al. Physical map of 1p36, placement of breakpoints in monosomy 1p36, and clinical characterization of the syndrome. <i>Am J Hum Genet</i> 2003;72:1200&ndash;1212. doi:10.1086/375177</li>
<li>Gillentine MA, Lupo PJ, Stankiewicz P, Schaaf CP. An estimation of the prevalence of genomic disorders using chromosomal microarray data. <i>J Hum Genet</i> 2018;63:795&ndash;801. doi:10.1038/s10038-018-0451-x</li>
<li>Oskarsd&#243;ttir S, Vujic M, Fasth A. Incidence and prevalence of the 22q11 deletion syndrome: a population-based study in Western Sweden. <i>Arch Dis Child</i> 2004;89:148&ndash;151. doi:10.1136/adc.2003.026880</li>
<li>S&#248;rensen KM, Agergaard P, Olesen C, et al. Detecting 22q11.2 deletions by use of multiplex ligation-dependent probe amplification on DNA from neonatal dried blood spot samples. <i>J Mol Diagn</i> 2010;12:147&ndash;151. doi:10.2353/jmoldx.2010.090099</li>
<li>Panamonta V, Wichajarn K, Chaikitpinyo A, et al. Birth prevalence of chromosome 22q11.2 deletion syndrome: a systematic review of population-based studies. <i>J Med Assoc Thai</i> 2016;99(Suppl 5):S187&ndash;S193. PMID:29906080</li>
<li>Kendall KM, Rees E, Escott-Price V, et al. Cognitive performance among carriers of pathogenic copy number variants: analysis of 152,000 UK Biobank subjects. <i>Biol Psychiatry</i> 2017;82:103&ndash;110. doi:10.1016/j.biopsych.2016.08.014</li>
<li>GeneReviews (NCBI Bookshelf): McDonald-McGinn DM, et al. 22q11.2 Deletion Syndrome; Miller DT, et al. 16p11.2 Recurrent Deletion; Morris CA, et al. Williams Syndrome. <a href="https://www.ncbi.nlm.nih.gov/books/NBK1523/">NBK1523</a> &middot; <a href="https://www.ncbi.nlm.nih.gov/books/NBK11167/">NBK11167</a> &middot; <a href="https://www.ncbi.nlm.nih.gov/books/NBK1249/">NBK1249</a></li>
<li>Orphanet: 22q11.2 deletion syndrome (ORPHA:567); Williams syndrome (ORPHA:904); Monosomy 5p / Cri-du-chat (ORPHA:281). <a href="https://www.orpha.net">orpha.net</a></li>
</ol>
<p class="note">Data compiled from public literature and population cohorts (no internal disease database).
Full source detail and CSV tables: see <code>report.md</code> and <code>data/</code>.
Figures regenerate via <code>outputs/scripts/microdeletion_prevalence.py</code>.</p>
"""
html += HTML_FOOT
open(os.path.join(PKG, "index.html"), "w", encoding="utf-8").write(html)
print("wrote index.html (", len(html), "bytes)")