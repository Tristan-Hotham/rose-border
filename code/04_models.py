"""Step 4: every pre-specified estimate (NOTES.md, analysis plan), the checks, and data/results.json.
Inputs: data/features.csv, data/poi_units.csv, data/zones.csv. Outputs: data/results.json, data/zone_rates.csv,
data/profiles.csv, data/robustness.csv."""
import warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(SEED)
F0 = pd.read_csv(f"{DATA}/features.csv", keep_default_na=False, dtype={"d_hist": str, "d_mod": str})
for c in ("d_hist", "d_mod", "absd_hist", "lon", "lat"):
    F0[c] = pd.to_numeric(F0[c].replace("", np.nan))
U0 = pd.read_csv(f"{DATA}/poi_units.csv", keep_default_na=False)
ZT = pd.read_csv(f"{DATA}/zones.csv")
ZLAB = {v[0]: v[1] for v in ZONES.values()}


def sample(types=("private",), rose=False, dedup=True, tagged_only=False):
    F = F0[(F0.dropped == "") & (F0.sliver == 0) & (F0.zone != "") & (F0.zone != "SLIVER")].copy()
    if dedup:
        F = F[F.dup_of == ""]
    if "chain1" in types:     # chains: one per chain name per zone
        ch = F[F.type == "chain"].copy(); ch["nn"] = ch.name.map(norm)
        ch = ch.drop_duplicates(["nn", "zone"])
        F = pd.concat([F[F.type != "chain"], ch])
        types = tuple(t for t in types if t != "chain1") + ("chain",)
    F = F[F.type.isin(types)]
    if rose:
        F["word"] = F.word.replace({"rose_L": "L", "rose_Y": "Y"})
    F = F[F.word.isin(["L", "Y"])]
    if tagged_only:
        F = F[F.tagged == 1]
    return F


def wilson(k, n, z=1.96):
    if n == 0:
        return None, None, None
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, (c - h) / d, (c + h) / d


def zmask(F, z, band):
    if z in ("LL", "YY") and band is not None:
        return (F.zone == z) & (F.absd_hist <= band)
    return F.zone == z


def umask(U, z, band):
    if z in ("LL", "YY") and band is not None:
        return (U.zone == z) & (U.band <= band)
    return U.zone == z


# ---------------- H1: shares ----------------
def shares(F, band=BAND_KM):
    out = {}
    for z in ("LL", "YY", "T_YL", "T_YG", "T_YC", "T_YD", "L_GM", "L_MS", "L_CU", "L_CH", "L_YO", "C_GM", "C_MS"):
        g = F[zmask(F, z, band)]
        nY, n = int((g.word == "Y").sum()), len(g)
        p, lo, hi = wilson(nY, n)
        out[z] = {"nY": nY, "nL": n - nY, "n": n, "s": p, "lo": lo, "hi": hi}
    return out


def cellsum(d):
    g = d.groupby("cell5").word.agg(lambda w: (w == "Y").sum()).rename("y").to_frame()
    g["n"] = d.groupby("cell5").size()
    return g[["y", "n"]].values.astype(float)


def boot_share(a, nboot):
    idx = rng.integers(0, len(a), size=(nboot, len(a)))
    s = a[idx].sum(axis=1)
    with np.errstate(all="ignore"):
        return s[:, 0] / s[:, 1]


def pindex(F, band=BAND_KM, tz=("T_YL",), nboot=NBOOT):
    T = F[F.zone.isin(tz)]; L = F[zmask(F, "LL", band)]; Y = F[zmask(F, "YY", band)]
    if len(T) == 0 or len(L) == 0 or len(Y) == 0:
        return {"P": None, "lo": None, "hi": None, "nT": len(T), "why": "no county-named feature in the moved zone" if len(T) == 0 else "empty reference"}
    sT, sL, sY = ((d.word == "Y").mean() for d in (T, L, Y))
    est = (sT - sL) / (sY - sL)
    bT, bL, bY = (boot_share(cellsum(d), nboot) for d in (T, L, Y))
    with np.errstate(all="ignore"):
        bs = (bT - bL) / (bY - bL)
    bs = bs[np.isfinite(bs)]
    return {"P": float(est), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5)), "nT": len(T)}


# ---------------- H2: rates ----------------
def poisson_ci(k, a=0.05):
    lo = 0.0 if k == 0 else stats.chi2.ppf(a / 2, 2 * k) / 2
    hi = stats.chi2.ppf(1 - a / 2, 2 * k + 2) / 2
    return lo, hi


def rr_exact(a, Ea, b, Eb, alpha=0.05):
    """Rate ratio (a/Ea)/(b/Eb) with the exact conditional (Clopper-Pearson) interval."""
    if Ea == 0 or Eb == 0 or a + b == 0:
        return None, None, None, None
    n = a + b
    plo = 0.0 if a == 0 else stats.beta.ppf(alpha / 2, a, n - a + 1)
    phi = 1.0 if a == n else stats.beta.ppf(1 - alpha / 2, a + 1, n - a)
    k = Eb / Ea
    if b == 0:   # reference has none: ratio unbounded above, report the lower bound only
        return float("inf"), plo / (1 - plo) * k, float("inf"), stats.binomtest(a, n, Ea / (Ea + Eb)).pvalue
    pval = stats.binomtest(a, n, Ea / (Ea + Eb)).pvalue
    return (a / Ea) / (b / Eb), plo / (1 - plo) * k, (phi / (1 - phi) * k if phi < 1 else float("inf")), pval


RATE_ROWS = [  # (name word, zone, role, reference zone, benchmark zone)
    ("L", "LL", "stayed", None, None),
    ("L", "L_GM", "moved", "LL", "C_GM"), ("L", "L_MS", "moved", "LL", "C_MS"), ("L", "L_CU", "moved", "LL", "W_CU"),
    ("L", "L_CH", "moved", "LL", "CC"), ("L", "L_YO", "moved", "LL", "YY"),
    ("L", "C_GM", "benchmark", "LL", None), ("L", "C_MS", "benchmark", "LL", None), ("L", "CC", "benchmark", "LL", None),
    ("L", "W_CU", "benchmark", "LL", None), ("L", "U_CU", "benchmark", "LL", None), ("L", "YY", "benchmark", "LL", None),
    ("L", "T_YL", "gained", "LL", "YY"),
    ("Y", "YY", "stayed", None, None),
    ("Y", "T_YL", "moved", "YY", "LL"), ("Y", "T_YG", "moved", "YY", "L_GM"), ("Y", "T_YC", "moved", "YY", "W_CU"),
    ("Y", "T_YD", "moved", "YY", "DD"),
    ("Y", "LL", "benchmark", "YY", None), ("Y", "L_GM", "benchmark", "YY", None), ("Y", "W_CU", "benchmark", "YY", None),
    ("Y", "DD", "benchmark", "YY", None), ("Y", "L_YO", "gained", "YY", "LL"),
]


def bnd(w, z, band):
    """Plan: the Lancashire name in stayed Lancashire uses all of LL; every other LL or YY comparison uses the band."""
    return None if (w == "L" and z == "LL") else band


def rates(F, U, band=BAND_KM, expo="poi_bus"):
    rows = []
    cnt = lambda w, z: int((F[zmask(F, z, bnd(w, z, band))].word == w).sum())
    ex = lambda z, w="Y": int(U[umask(U, z, bnd(w, z, band))][expo].sum())
    for w, z, role, ref, bench in RATE_ROWS:
        k, E = cnt(w, z), ex(z, w)
        lo, hi = poisson_ci(k)
        r = {"name": "Lancashire" if w == "L" else "Yorkshire", "w": w, "zone": z, "label": ZLAB.get(z, z), "role": role,
             "n": k, "poi": E, "rate": 1000 * k / E if E else None, "rate_lo": 1000 * lo / E if E else None, "rate_hi": 1000 * hi / E if E else None,
             "ref": ref, "bench": bench}
        if ref:
            rr, rlo, rhi, p = rr_exact(k, E, cnt(w, ref), ex(ref, w)); r.update({"rr": rr, "rr_lo": rlo, "rr_hi": rhi, "rr_p": p})
            r["expected_at_ref"] = E * cnt(w, ref) / ex(ref, w) if ex(ref, w) else None
        if bench:
            rb, blo, bhi, pb = rr_exact(k, E, cnt(w, bench), ex(bench, w)); r.update({"rr_bench": rb, "rrb_lo": blo, "rrb_hi": bhi, "rrb_p": pb})
            r["expected_at_bench"] = E * cnt(w, bench) / ex(bench, w) if ex(bench, w) else None
        rows.append(r)
    return rows


def qindex(F, U, w, z, ref, bench, band=BAND_KM, nboot=NBOOT, expo="poi_bus"):
    """Where the moved zone's rate sits between its benchmark (0) and its stayed zone (1); cluster bootstrap by 5 km cell."""
    def parts(zz):
        f = F[zmask(F, zz, bnd(w, zz, band)) & (F.word == w)].groupby("cell5").size()
        u = U[umask(U, zz, bnd(w, zz, band))].groupby("cell5")[expo].sum()
        return pd.concat([f.rename("k"), u.rename("e")], axis=1).fillna(0).values.astype(float)
    Ds = [parts(z), parts(ref), parts(bench)]
    r = [d[:, 0].sum() / d[:, 1].sum() for d in Ds]
    if r[1] == r[2]:
        return {"Q": None}
    est = (r[0] - r[2]) / (r[1] - r[2])
    rb = [boot_share(d, nboot) for d in Ds]
    with np.errstate(all="ignore"):
        bs = (rb[0] - rb[2]) / (rb[1] - rb[2])
    bs = bs[np.isfinite(bs)]
    return {"Q": float(est), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5)), "nboot": int(len(bs))}


# ---------------- M2: pooled Poisson ----------------
M2_ZONES = ["YY", "LL", "T_YL", "T_YG", "T_YC", "T_YD", "L_GM", "L_MS", "L_CU", "L_CH", "L_YO", "C_GM", "C_MS", "CC", "W_CU", "U_CU", "DD"]


def m2(F, U, w, expo="poi_bus", cl="block20"):
    zinfo = {v[0]: k for k, v in ZONES.items()}
    clc = cl if cl != "cell5" else "block20"
    u = U[U.zone.isin(M2_ZONES)].groupby(["zone", "cell5"]).agg(e=(expo, "sum"), cl=(clc, "first")).reset_index()
    f = F[F.zone.isin(M2_ZONES) & (F.word == w)].groupby(["zone", "cell5"]).size().rename("k").reset_index()
    d = u.merge(f, on=["zone", "cell5"], how="left").fillna({"k": 0})
    lost = int(f.k.sum() - d[d.e > 0].k.sum())
    d = d[d.e > 0]
    hn = "Lancashire" if w == "L" else "Yorkshire"
    d["H"] = d.zone.map(lambda z: int(zinfo[z][0] == hn))
    d["M"] = d.zone.map(lambda z: int(zinfo[z][1] == hn))
    X = sm.add_constant(d[["H", "M"]].astype(float))
    res = sm.GLM(d.k, X, family=sm.families.Poisson(), offset=np.log(d.e)).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.cl)[0]})
    out = {"units": len(d), "features": int(d.k.sum()), "lost_no_poi": lost, "clusters": int(d.cl.nunique()),
           "both_differ": int(((d.H != d.M)).sum())}
    for v in ("H", "M"):
        b, se = res.params[v], res.bse[v]
        out[v] = {"b": float(b), "se": float(se), "rr": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)), "hi": float(np.exp(b + 1.96 * se)), "p": float(res.pvalues[v])}
        if not np.isfinite(se) or se > 10:   # separation: not estimable
            out[v] = {"b": None, "se": None, "rr": None, "lo": None, "hi": None, "p": None, "note": "not estimable (separation)"}
    out["cells_H1M0"] = int(((d.H == 1) & (d.M == 0)).sum()); out["cells_H0M1"] = int(((d.H == 0) & (d.M == 1)).sum())
    return out


# ---------------- logit / LPM at the line (M1b) and placebo P1 ----------------
def m1b(F, band=BAND_KM):
    d = F[((F.zone == "LL") | (F.zone == "YY")) & (F.absd_hist <= band)].copy()
    d["Yn"] = (d.word == "Y").astype(int); d["HY"] = (d.zone == "YY").astype(int)
    d["dY"] = d.HY * d.absd_hist; d["dL"] = (1 - d.HY) * d.absd_hist
    X = sm.add_constant(d[["HY", "dY", "dL"]].astype(float))
    out = {"n": len(d), "nY": int(d.Yn.sum()), "clusters": int(d.cell5.nunique())}
    try:
        r = sm.GLM(d.Yn, X, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.cell5)[0]})
        if not np.isfinite(r.bse.HY) or abs(r.params.HY) > 15:
            raise ValueError("separation")
        out["logit"] = {"b": float(r.params.HY), "se": float(r.bse.HY), "p": float(r.pvalues.HY)}
        p1 = r.predict(pd.DataFrame({"const": [1.0], "HY": [1.0], "dY": [0.0], "dL": [0.0]}))[0]
        p0 = r.predict(pd.DataFrame({"const": [1.0], "HY": [0.0], "dY": [0.0], "dL": [0.0]}))[0]
        out["logit"].update({"p_Y_at_line_yorks": float(p1), "p_Y_at_line_lancs": float(p0)})
    except Exception as e:
        out["logit"] = {"note": "not estimable: near-complete separation (almost every name on each side is that side's county)"}
    r = sm.OLS(d.Yn, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.cell5)[0]})
    out["lpm"] = {"b": float(r.params.HY), "lo": float(r.params.HY - 1.96 * r.bse.HY), "hi": float(r.params.HY + 1.96 * r.bse.HY), "p": float(r.pvalues.HY)}
    return out


def jump(F, at, w=10.0, nboot=NBOOT):
    d = F[F.zone.isin(["LL", "YY"]) & F.d_hist.notna()]
    a = d[(d.d_hist >= at - w) & (d.d_hist < at)]; b = d[(d.d_hist >= at) & (d.d_hist < at + w)]
    if len(a) == 0 or len(b) == 0:
        return {"at": at, "nA": len(a), "nB": len(b), "diff": None}
    est = (b.word == "Y").mean() - (a.word == "Y").mean()
    bs = boot_share(cellsum(b), nboot) - boot_share(cellsum(a), nboot)
    bs = bs[np.isfinite(bs)]
    return {"at": at, "nA": len(a), "nB": len(b), "sA": float((a.word == "Y").mean()), "sB": float((b.word == "Y").mean()),
            "diff": float(est), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5))}


# ================= run =================
R = {"title": TITLE, "sub": SUB}
F = sample(); U = U0
R["flow"] = json.load(open(f"{SCR}/flow02.json"))
K = F0[(F0.dropped == "") & (F0.dup_of == "")]
R["flow"].update({"kept_by_type": K.type.value_counts().to_dict(), "kept_by_word": K.word.value_counts().to_dict(),
                  "sliver_dropped": int(((F0.dropped == "") & (F0.dup_of == "") & (F0.sliver == 1)).sum()),
                  "outside_zones": int(((F0.dropped == "") & (F0.dup_of == "") & (F0.zone == "")).sum()),
                  "main_n": len(F), "main_L": int((F.word == "L").sum()), "main_Y": int((F.word == "Y").sum()),
                  "both_words": int((F0.word == "both").sum())})
R["zones_km2"] = {r.zone: r.area_km2 for r in ZT.itertuples() if r.zone in ZLAB}
R["poi"] = {"business_total": int(U.poi_bus.sum()), "all_total": int(U.poi_all.sum()),
            "by_zone": U.groupby("zone").poi_bus.sum().astype(int).to_dict(),
            "LL_band": int(U[umask(U, "LL", BAND_KM)].poi_bus.sum()), "YY_band": int(U[umask(U, "YY", BAND_KM)].poi_bus.sum())}
R["H1"] = {"shares": shares(F), "P": pindex(F), "P_all_moved": pindex(F, tz=("T_YL", "T_YG", "T_YC"))}
R["M1b"] = m1b(F)
RT = rates(F, U)
R["H2"] = {f"{r['w']}_{r['zone']}": r for r in RT}
Q = {}
for w, z, role, ref, bench in RATE_ROWS:
    if role == "moved" and bench:
        Q[f"{w}_{z}"] = qindex(F, U, w, z, ref, bench)
R["Q"] = Q
R["M2"] = {"L": m2(F, U, "L"), "Y": m2(F, U, "Y")}
# H3: public bodies and chains in moved zones
pub = F0[(F0.dropped == "") & (F0.dup_of == "") & F0.zone.str.match(r"^(T_|L_)") & F0.type.isin(["public", "chain"]) & F0.word.isin(["L", "Y"])]
R["H3"] = {"n": len(pub), "rows": pub[["name", "type", "word", "zone", "modern"]].to_dict("records")}
R["H3"]["match_modern"] = int(sum(1 for r in R["H3"]["rows"] if (r["word"] == "L" and r["modern"] == "Lancashire") or (r["word"] == "Y" and r["modern"] in YORKS_CER)))
R["H3"]["match_historic_only"] = int(sum(1 for r in R["H3"]["rows"] if (r["word"] == "L" and r["zone"].startswith("L_") and r["modern"] != "Lancashire") or (r["word"] == "Y" and r["zone"].startswith("T_"))))
# exploratory (labelled): GM and Merseyside together, historic Lancashire parts vs historic Cheshire parts
a = int(((F.zone.isin(["L_GM", "L_MS"])) & (F.word == "L")).sum()); Ea = int(U[U.zone.isin(["L_GM", "L_MS"])].poi_bus.sum())
b = int(((F.zone.isin(["C_GM", "C_MS"])) & (F.word == "L")).sum()); Eb = int(U[U.zone.isin(["C_GM", "C_MS"])].poi_bus.sum())
rr, lo, hi, p = rr_exact(a, Ea, b, Eb)
R["X_metro"] = {"nL": a, "poiL": Ea, "nC": b, "poiC": Eb, "rr": rr, "lo": lo, "hi": hi, "p": p, "expected_C_at_L_rate": Eb * a / Ea}
# placebo P1
R["P1"] = {"real": jump(F, 0.0), "false_lancs": jump(F, -10.0), "false_yorks": jump(F, 10.0)}
# P2 within-county comparisons are rows L_GM vs C_GM and L_MS vs C_MS in H2 (rr_bench)
# profiles
prof = []
for kind, col, ucol in (("hist", "d_hist", "bh"), ("mod", "d_mod", "bm")):
    d = F[F[col].notna() & (F[col].abs() < 40)]
    for b0 in range(-40, 40, 5):
        g = d[(d[col] >= b0) & (d[col] < b0 + 5)]
        nY = int((g.word == "Y").sum()); p, lo, hi = wilson(nY, len(g))
        e = int(U[(U[ucol] == b0)].poi_bus.sum())
        nL = len(g) - nY
        prof.append({"line": kind, "bin": b0, "mid": b0 + 2.5, "n": len(g), "nY": nY, "nL": nL, "s": p, "lo": lo, "hi": hi, "poi": e,
                     "rY": 1000 * nY / e if e else None, "rL": 1000 * nL / e if e else None})
PR = pd.DataFrame(prof); PR.to_csv(f"{DATA}/profiles.csv", index=False)
R["profiles_rows"] = len(PR)
# leave-one-out: T_YL by district
loo = {}
for lad in ("Ribble Valley", "Pendle"):
    f = F[(F.zone == "T_YL") & (F.lad == lad)]
    loo[lad] = {"nY": int((f.word == "Y").sum()), "nL": int((f.word == "L").sum())}
R["loo_TYL"] = loo
pv = F0[(F0.dropped == "") & (F0.dup_of == "") & (F0.zone == "T_YL")]
R["TYL_all_named"] = pv[["name", "type", "word", "lad"]].to_dict("records")


# ---------------- robustness grid ----------------
def summary(F, U, band=BAND_KM, expo="poi_bus", cl="block20"):
    sh = shares(F, band); rt = {f"{r['w']}_{r['zone']}": r for r in rates(F, U, band, expo)}
    m2l, m2y = m2(F, U, "L", expo, cl), m2(F, U, "Y", expo, cl)
    return {"n": len(F), "LL_s": sh["LL"]["s"], "YY_s": sh["YY"]["s"], "LL_n": sh["LL"]["n"], "YY_n": sh["YY"]["n"], "TYL_n": sh["T_YL"]["n"],
            "TYL_nY": sh["T_YL"]["nY"], "rr_Y_TYL": rt["Y_T_YL"].get("rr"), "rr_Y_TYL_hi": rt["Y_T_YL"].get("rr_hi"),
            "rr_L_LCU": rt["L_L_CU"].get("rr"), "rr_L_LCU_lo": rt["L_L_CU"].get("rr_lo"), "rr_L_LCU_hi": rt["L_L_CU"].get("rr_hi"),
            "rr_L_LGM": rt["L_L_GM"].get("rr"), "rr_L_LGM_lo": rt["L_L_GM"].get("rr_lo"), "rr_L_LGM_hi": rt["L_L_GM"].get("rr_hi"),
            "rrb_L_LGM": rt["L_L_GM"].get("rr_bench"), "rrb_L_LGM_lo": rt["L_L_GM"].get("rrb_lo"), "rrb_L_LGM_hi": rt["L_L_GM"].get("rrb_hi"),
            "L_H": m2l["H"]["rr"], "L_H_lo": m2l["H"]["lo"], "L_H_hi": m2l["H"]["hi"], "L_M": m2l["M"]["rr"], "L_M_lo": m2l["M"]["lo"], "L_M_hi": m2l["M"]["hi"],
            "Y_H": m2y["H"]["rr"], "Y_H_lo": m2y["H"]["lo"], "Y_H_hi": m2y["H"]["hi"], "Y_M": m2y["M"]["rr"], "Y_M_lo": m2y["M"]["lo"], "Y_M_hi": m2y["M"]["hi"]}


ROB = [("Main", "main", {}, {}),
       ("Bandwidth 10 km", "band", {}, {"band": 10.0}), ("Bandwidth 15 km", "band", {}, {"band": 15.0}), ("Bandwidth 40 km", "band", {}, {"band": 40.0}),
       ("Including chains (one per name per zone)", "sample", {"types": ("private", "chain1")}, {}),
       ("Including public bodies", "sample", {"types": ("private", "public")}, {}),
       ("Including all types", "sample", {"types": ("private", "public", "chain")}, {}),
       ("Adding red and white rose names", "sample", {"rose": True}, {}),
       ("No deduplication", "sample", {"dedup": False}, {}),
       ("Tagged features only", "sample", {"tagged_only": True}, {}),
       ("Denominator: all named POIs", "denominator", {}, {"expo": "poi_all"}),
       ("Clusters: 10 km cells", "clusters", {}, {"cl": "cell10"})]
rob = []
for lab, grp, sk, mk in ROB:
    s = summary(sample(**sk), U, **mk); s.update({"label": lab, "group": grp}); rob.append(s)
RB = pd.DataFrame(rob); RB.to_csv(f"{DATA}/robustness.csv", index=False)
R["robust"] = rob
pd.DataFrame(RT).to_csv(f"{DATA}/zone_rates.csv", index=False)

# ---------------- headline numbers used in the text ----------------
sh = R["H1"]["shares"]; h2 = R["H2"]
R["x"] = {"LL_s_pc": 100 * sh["LL"]["s"], "YY_s_pc": 100 * sh["YY"]["s"], "LL_lo": 100 * sh["LL"]["lo"], "LL_hi": 100 * sh["LL"]["hi"],
          "YY_lo": 100 * sh["YY"]["lo"], "YY_hi": 100 * sh["YY"]["hi"]}
p1 = R["P1"]
R["x"].update({"jump": 100 * p1["real"]["diff"], "jump_lo": 100 * p1["real"]["lo"], "jump_hi": 100 * p1["real"]["hi"],
               "fl": 100 * p1["false_lancs"]["diff"], "fl_lo": 100 * p1["false_lancs"]["lo"], "fl_hi": 100 * p1["false_lancs"]["hi"],
               "fy": 100 * p1["false_yorks"]["diff"], "fy_lo": 100 * p1["false_yorks"]["lo"], "fy_hi": 100 * p1["false_yorks"]["hi"],
               "lpm": 100 * R["M1b"]["lpm"]["b"], "lpm_lo": 100 * R["M1b"]["lpm"]["lo"], "lpm_hi": 100 * R["M1b"]["lpm"]["hi"],
               "QGM": 100 * R["Q"]["L_L_GM"]["Q"], "QGM_lo": 100 * R["Q"]["L_L_GM"]["lo"], "QGM_hi": 100 * R["Q"]["L_L_GM"]["hi"],
               "QMS": 100 * R["Q"]["L_L_MS"]["Q"], "QMS_lo": 100 * R["Q"]["L_L_MS"]["lo"], "QMS_hi": 100 * R["Q"]["L_L_MS"]["hi"],
               "metro_n": R["X_metro"]["nL"] , "TY_poi": sum(R["H2"][f"Y_{z}"]["poi"] for z in ("T_YL", "T_YG", "T_YC", "T_YD")),
               "TY_exp": sum(R["H2"][f"Y_{z}"]["expected_at_ref"] for z in ("T_YL", "T_YG", "T_YC", "T_YD")),
               "rrGM_pc": 100 * R["H2"]["L_L_GM"]["rr"], "rrMS_pc": 100 * R["H2"]["L_L_MS"]["rr"],
               "n_rob": len(rob), "n_rob_LH_sig": int(sum(1 for r in rob if r["L_H_lo"] and r["L_H_lo"] > 1)),
               "n_rob_LM_sig": int(sum(1 for r in rob if r["L_M_lo"] and r["L_M_lo"] > 1)),
               "n_rob_GM_sig": int(sum(1 for r in rob if r["rr_L_LGM_hi"] and r["rr_L_LGM_hi"] < 1)),
               "n_rob_YM_gt_YH": int(sum(1 for r in rob if r["Y_M"] and r["Y_H"] and r["Y_M"] > r["Y_H"] and r["Y_M"] < 1e4))})
for key in h2:
    if h2[key].get("rate") is not None:
        R["x"][f"rate_{key}"] = h2[key]["rate"]
print(json.dumps({k: R[k] for k in ("flow", "H1", "M1b", "Q", "M2", "P1", "loo_TYL")}, indent=1, default=str)[:9000])
print(pd.DataFrame(RT)[["name", "zone", "role", "n", "poi", "rate", "rr", "rr_lo", "rr_hi", "rr_bench", "rrb_lo", "rrb_hi", "expected_at_ref", "expected_at_bench"]].round(3).to_string())
print(RB.round(3).to_string())
jsave(R, f"{DATA}/results.json", indent=1)
