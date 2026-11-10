"""Step 6: page data (data/site.json) and index.html from code/page_template.html and code/page.css, filled from
data/results.json, with the full-screen snippet. 10.5281/zenodo.24104647, https://doi.org/10.5281/zenodo.24104647 and https://blog.tristanhotham.com/2026/10/31/rose-border/ are left for the publisher.
Places for the search box: Wikidata settlements (CC0) in the map area with a population of 1,500 or more."""
import csv
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
F = pd.read_csv(f"{DATA}/features.csv", keep_default_na=False)
K = F[(F.dropped == "") & (F.dup_of == "") & (F.zone != "") & (F.zone != "SLIVER") & (F.sliver == 0)]
K = K[K.word.isin(["L", "Y", "rose_L", "rose_Y"])]
WORD = {"L": "L", "Y": "Y", "rose_L": "rL", "rose_Y": "rY"}
ZS = {v[0]: v[1].split(":")[0] for v in ZONES.values()}
ZS.update({"YY": "", "LL": "", "CC": "", "DD": "", "W_CU": "", "U_CU": ""})
tagl = lambda t: t.replace("=", ": ").replace("_", " ") if t else ""
f = [[round(r.lon, 5), round(r.lat, 5), r["name"], r.osm, WORD[r.word], r.type, tagl(r.tag), r["hist"], r.modern,
      r.zone if ZS.get(r.zone) else ""] for _, r in K.iterrows()]
pl = []
with open("/home/claude/newdata/raw_new8/uk_settlements.tsv", encoding="utf-8") as fh:
    rd = csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE); next(rd)
    for row in rd:
        try:
            nm = row[1].split('"')[1]; lon, lat = map(float, row[2].split("(")[1].rstrip(")").split()); pop = float(row[3] or 0)
        except Exception:
            continue
        if -3.7 < lon < -0.9 and 53.25 < lat < 54.7 and pop >= 1500:
            pl.append([nm, round(lon, 4), round(lat, 4), pop])
pl = [p[:3] for p in sorted(pl, key=lambda p: -p[3])]
seen = set(); pl = [p for p in pl if not (p[0] in seen or seen.add(p[0]))]
S = {"f": f, "z": {k: v for k, v in ZS.items() if v}, "zn": {v[0]: v[1] for v in ZONES.values()}, "p": pl}
sj = json.dumps(S, ensure_ascii=False, separators=(",", ":"))
assert "—" not in sj and "–" not in sj
open(f"{DATA}/site.json", "w", encoding="utf-8").write(sj)
R["site"] = {"features": len(f), "county": sum(1 for x in f if x[4] in ("L", "Y")), "rose": sum(1 for x in f if x[4] in ("rL", "rY")), "places": len(pl)}
jsave(R, f"{DATA}/results.json", indent=1)

KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{CSS}}", open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
names = {p[0] for p in pl}
for g in re.findall(r'data-go="([^"]+)"', t):
    assert g in names, g
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB; site.json", len(sj) // 1024, "KB;", R["site"])
