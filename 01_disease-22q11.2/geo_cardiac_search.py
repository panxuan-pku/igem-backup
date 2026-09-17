import urllib.request, urllib.parse, json, time, os
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"

def geo_search(term, db="gds", retmax=8):
    q = urllib.parse.quote(term)
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db={db}&term={q}&retmode=json&retmax={retmax}"
    with urllib.request.urlopen(url, timeout=30) as r:
        d = json.load(r)
    return d.get("esearchresult", {}).get("idlist", [])

def geo_summary(ids, db="gds"):
    if not ids:
        return []
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db={db}&retmode=json&id={','.join(ids)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        d = json.load(r)
    out = []
    for uid in d.get("result", {}).get("uids", []):
        rec = d["result"][uid]
        out.append((rec.get("title", "")[:115], rec.get("taxon", "")[:20], rec.get("n_samples")))
    return out

queries = [
    "22q11.2 deletion syndrome cardiomyocyte",
    "22q11.2 deletion syndrome cardiac single cell",
    "TBX1 human cardiomyocyte single cell",
    "22q11.2 iPSC cardiomyocyte",
]
for q in queries:
    try:
        ids = geo_search(q)
        print(f"\n=== {q} -> {len(ids)} 条")
        for t, tax, n in geo_summary(ids):
            print(f"   [{tax}] n={n} | {t}")
    except Exception as e:
        print(f"=== {q} -> ERR {e}")
    time.sleep(0.4)
