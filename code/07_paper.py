"""Step 7: the paper. Fills code/paper_template.tex from data/results.json and data/zones.csv, adds the tables and compiles
with xelatex. Output: release/paper/Hotham_Rose_Border.pdf and .tex beside the f_*.pdf figures. The DOI stays a placeholder
(https://doi.org/10.5281/zenodo.24104647 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Rose_Border"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
neg = lambda s: s.replace("-", "$-$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    for k in ("f0", "f1", "f2", "f3"):
        if f == k: return neg(f"{float(v):.{k[1]}f}")
    return tex(str(v))


def ci(v, lo, hi, d=2):
    if v is None:
        return "n/a"
    s = lambda x: "$\\infty$" if x is None or x == float("inf") else f"{x:.{d}f}"
    return neg(f"{s(v)} [{s(lo)}, {s(hi)}]")


H2 = R["H2"]; SH = R["H1"]["shares"]; ZK = R["zones_km2"]
LAB = {v[0]: v[1] for v in ZONES.values()}
# Table 1: zones
rows = ""
for z in ("LL", "YY", "T_YL", "T_YG", "T_YC", "T_YD", "L_GM", "L_MS", "L_CU", "L_CH", "C_GM", "C_MS", "CC", "W_CU", "U_CU", "DD"):
    nL = H2.get(f"L_{z}", {}).get("n"); nY = H2.get(f"Y_{z}", {}).get("n")
    poi = R["poi"]["by_zone"].get(z, 0)
    rows += f"{tex(z)} & {tex(LAB[z])} & {ZK.get(z, 0):,.0f} & {poi:,} & {'' if nL is None else nL} & {'' if nY is None else nY}\\\\\n"
T1 = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Zones: historic county crossed with the county since 1974. Area (km$^2$), named business points of interest (OpenFreeMap) and county-named private features (main sample) where the row is used in Table~\\ref{tab:rates}. LL and YY counts in Table~\\ref{tab:rates} use the bands stated there.}\\label{tab:zones}"
      "\\begin{tabular}{lp{7.2cm}rrrr}\\toprule Code & Zone & km$^2$ & POIs & Lancs. & Yorks.\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
# Table 2: shares
rows = ""
for z, lab in (("LL", "Historic Lancashire, still Lancashire (within 25 km)"), ("YY", "Historic Yorkshire, still Yorkshire (within 25 km)"),
               ("T_YL", "Bowland and West Craven (Yorkshire to Lancashire)"), ("T_YG", "Saddleworth (Yorkshire to Greater Manchester)"),
               ("T_YC", "Sedbergh and Dent (Yorkshire to Cumbria)"), ("T_YD", "South Teesdale (Yorkshire to Durham)"),
               ("L_GM", "Lancashire to Greater Manchester"), ("L_MS", "Lancashire to Merseyside"), ("L_CU", "Furness and Cartmel (Lancashire to Cumbria)"),
               ("L_CH", "Warrington and Widnes (Lancashire to Cheshire)")):
    s = SH[z]
    sh = "" if s["s"] is None else neg(f"{100 * s['s']:.1f} [{100 * s['lo']:.1f}, {100 * s['hi']:.1f}]")
    rows += f"{lab} & {s['nL']} & {s['nY']} & {sh}\\\\\n"
P = R["H1"]["P"]
T2 = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{H1: county-named private features by zone and the share naming Yorkshire (Wilson 95\\% interval).}\\label{tab:shares}"
      "\\begin{tabular}{lrrl}\\toprule Zone & Lancashire & Yorkshire & \\% Yorkshire [95\\% CI]\\\\\\midrule\n" + rows +
      f"\\midrule Persistence index $P$ for T\\_YL & \\multicolumn{{3}}{{l}}{{not estimable ({tex(P.get('why', ''))})}}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
# Table 3: rates
rows = ""; cur = None
for key, r in H2.items():
    if r["name"] != cur:
        rows += f"\\multicolumn{{7}}{{l}}{{\\textit{{Name says {r['name']}}}}}\\\\\n"; cur = r["name"]
    rate = ci(r["rate"], r["rate_lo"], r["rate_hi"])
    rr = ci(r.get("rr"), r.get("rr_lo"), r.get("rr_hi")) if r.get("ref") else ""
    ex = f"{r['expected_at_ref']:.1f}" if r.get("expected_at_ref") is not None else ""
    rb = ci(r.get("rr_bench"), r.get("rrb_lo"), r.get("rrb_hi")) if r.get("bench") and r.get("rr_bench") is not None else ""
    rows += f"\\quad {tex(r['zone'])} ({r['role']}) & {r['n']} & {r['poi']:,} & {rate} & {rr} & {ex} & {rb}\\\\\n"
T3 = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{H2: county-named private features per 1,000 named business POIs by zone (exact Poisson 95\\% CI); rate ratio against the stayed zone of the historic county (LL, all of it, for the Lancashire name; YY within 25 km of the line for the Yorkshire name) with the exact conditional interval; the count expected at the stayed zone's rate; and the rate ratio against the never-in-the-county benchmark named in the text. $\\infty$: the comparison zone has none.}\\label{tab:rates}"
      "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{lrrllrl}\\toprule Zone (role) & $n$ & POIs & Rate [95\\% CI] & RR vs stayed & Expected & RR vs benchmark\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
# Table 4: M2
rows = ""
for w, nm in (("L", "Lancashire"), ("Y", "Yorkshire")):
    m = R["M2"][w]
    for k, lab in (("H", "historic county"), ("M", "county today")):
        e = m[k]
        rows += f"{nm} & {lab} & {neg(f'{e['b']:.3f}')} & ({e['se']:.3f}) & {ci(e['rr'], e['lo'], e['hi'])} & {e['p']:.4f}\\\\\n"
    rows += f"& \\multicolumn{{5}}{{p{{11cm}}}}{{units {m['units']:,}; features {m['features']}; clusters {m['clusters']}; units where the two disagree: historic only {m['cells_H1M0']}, today only {m['cells_H0M1']}}}\\\\\\midrule\n"
T4 = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{M2: Poisson regression of county-named private features on indicators for the historic county and the county today, with log named business POIs as offset; units are 5 km cells within zones; standard errors clustered by 20 km block.}\\label{tab:m2}"
      "\\begin{tabular}{llrrlr}\\toprule Name & Indicator & $b$ & (SE) & Rate ratio [95\\% CI] & $p$\\\\\\midrule\n" + rows.rstrip("\\midrule\n") + "\\\\\\bottomrule\\end{tabular}\\end{table}")
# Table 5: placebo
P1 = R["P1"]; MB = R["M1b"]
rows = ""
for k, lab in (("false_lancs", "False line 10 km inside Lancashire"), ("real", "Historic border (where it did not move)"), ("false_yorks", "False line 10 km inside Yorkshire")):
    r = P1[k]
    rows += f"{lab} & {r['nA']} & {r['nB']} & {neg(f'{100 * r['sA']:.1f}')} & {neg(f'{100 * r['sB']:.1f}')} & {neg(f'{100 * r['diff']:.1f} [{100 * r['lo']:.1f}, {100 * r['hi']:.1f}]')}\\\\\n"
T5 = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Placebo P1: change in the share naming Yorkshire across the real line and false lines (10 km windows either side; cluster bootstrap by 5 km cell). Below: M1b, linear probability model within 25 km.}\\label{tab:placebo}"
      "\\begin{tabular}{p{4.6cm}rrrrl}\\toprule Line & $n$ west & $n$ east & \\% west & \\% east & Jump, points [95\\% CI]\\\\\\midrule\n" + rows +
      f"\\midrule M1b: historic Yorkshire side (LPM, $n={MB['n']}$, {MB['clusters']} clusters) & \\multicolumn{{5}}{{p{{7cm}}}}{{{neg(f'{100 * MB['lpm']['b']:.1f} [{100 * MB['lpm']['lo']:.1f}, {100 * MB['lpm']['hi']:.1f}] points')}; logit not estimable (separation)}}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
# Table 6: robustness
rows = ""
for r in R["robust"]:
    f = lambda k: "n/a" if r[k] is None or r[k] > 1e4 else f"{r[k]:.1f}"
    fy = lambda k: "n/a" if r[k] is None or r[k] > 1e4 else f"{r[k]:.1f}"
    rows += (f"{tex(r['label'])} & {r['n']} & {100 * r['LL_s']:.1f} / {100 * r['YY_s']:.1f} & {r['TYL_n']} & "
             f"{ci(r['rr_L_LGM'], r['rr_L_LGM_lo'], r['rr_L_LGM_hi'])} & {f('L_H')} [{f('L_H_lo')}, {f('L_H_hi')}] & {f('L_M')} [{f('L_M_lo')}, {f('L_M_hi')}] & {fy('Y_H')} / {fy('Y_M')}\\\\\n")
T6 = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Robustness. $n$: county-named features in zones. Shares: \\% Yorkshire in LL / YY within the band. T\\_YL: features in Bowland and West Craven. RR GM: Lancashire name, old Lancashire part of Greater Manchester vs stayed Lancashire. M2 rate ratios for the historic county (H) and the county today (M). Bandwidth changes only the band-based quantities.}\\label{tab:robust}"
      "\\setlength{\\tabcolsep}{2.5pt}\\begin{tabular}{p{3.6cm}rlrllll}\\toprule Check & $n$ & LL / YY & T\\_YL & RR GM [95\\% CI] & Lancs. H & Lancs. M & Yorks. H / M\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
# Table A1: flow
fl = R["flow"]
rows = f"Rows in the OSM name file & {fl['file_rows']:,}\\\\\nwith a Lancashire, Yorkshire or rose word & {fl['county_or_rose']:,}\\\\\n"
for k, v in fl["dropped"].items():
    rows += f"\\quad less: {tex(k)} & $-${v:,}\\\\\n"
rows += f"\\quad less: duplicates (same name within 300 m) & $-${fl['duplicates']}\\\\\\midrule\nKept & {fl['kept']:,}\\\\\n"
for k, v in fl["kept_by_type"].items():
    rows += f"\\quad {tex(k)} & {v:,}\\\\\n"
rows += f"Outside the study zones & {fl['outside_zones']}\\\\\nMain sample: private, county word, in zones & {fl['main_n']} ({fl['main_L']} Lancashire, {fl['main_Y']} Yorkshire)\\\\\n"
TA = ("\\begin{table}[tbp]\\centering\\small\\caption{From the name file to the main sample.}\\label{tab:flow}\\begin{tabular}{lr}\\toprule Step & Number\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_ZONES", T1), ("TABLE_SHARES", T2), ("TABLE_RATES", T3), ("TABLE_M2", T4), ("TABLE_PLACEBO", T5), ("TABLE_ROBUST", T6), ("TABLE_FLOW", TA)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24104647", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("DSIT", "DCMS", "pre-registered", "preregistered"):
    assert bad not in t, bad
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = txt.split("Abstract")[1].split("Keywords")[0]
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013"))
