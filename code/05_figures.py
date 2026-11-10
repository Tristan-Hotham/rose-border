"""Step 5: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf,
vector) and header.png (1200 x 630). Light paper background; red = Lancashire, navy (or a white rose ringed in navy on maps)
= Yorkshire."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np, pandas as pd, geopandas as gpd
from PIL import Image
from shapely.geometry import box
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
RED, NAVY, GREY, PURPLE = "#C0392B", "#1F3A68", "#9C9384", "#5B2A86"
SEA, LAND = "#DCE6E8", "#F1E7CF"
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD):
    os.makedirs(d_, exist_ok=True)
SRC = ("Data: OpenStreetMap contributors (ODbL); OpenFreeMap POIs; Historic County Borders Project; ONS districts (OGL v3.0)\n"
       "maps.tristanhotham.com/rose-border")
BNG = "EPSG:27700"


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.055, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8.3, family=MONO, color=MUT, va="bottom", linespacing=1.4)


F = pd.read_csv(f"{DATA}/features.csv", keep_default_na=False)
for c in ("d_hist", "d_mod", "absd_hist"):
    F[c] = pd.to_numeric(F[c].replace("", np.nan))
K = F[(F.dropped == "") & (F.dup_of == "") & (F.zone != "") & (F.zone != "SLIVER") & (F.sliver == 0) & F.word.isin(["L", "Y"])]
KP = K[K.type == "private"]
B = gpd.read_file(f"{DATA}/boundaries.geojson").to_crs(BNG)
world = gpd.read_file(f"{GEO}/ne_10m_admin_0_countries.geojson")
land = world[world.ADMIN.isin(["United Kingdom", "Isle of Man"])].to_crs(BNG)
pts = gpd.GeoDataFrame(KP, geometry=gpd.points_from_xy(KP.lon, KP.lat), crs="EPSG:4326").to_crs(BNG)

# ---------- 1. the map ----------
EXT = (288000, 470000, 372000, 528000)
KEYS = [("T_YL", "1", "Bowland and West Craven", "Yorkshire to Lancashire"), ("T_YG", "2", "Saddleworth", "Yorkshire to Greater Manchester"),
        ("T_YC", "3", "Sedbergh and Dent", "Yorkshire to Cumbria"), ("L_CU", "4", "Furness and Cartmel", "Lancashire to Cumbria"),
        ("L_MS", "5", "Merseyside", "Lancashire to Merseyside"), ("L_GM", "6", "Greater Manchester", "Lancashire to Greater Manchester"),
        ("L_CH", "7", "Warrington and Widnes", "Lancashire to Cheshire"), ("T_YD", "8", "South Teesdale", "Yorkshire to Durham")]


def draw_map(ax, ext=EXT, numbers=True, dots=True, ms=26):
    ax.set_facecolor(SEA)
    clip = box(ext[0] - 5000, ext[2] - 5000, ext[1] + 5000, ext[3] + 5000)
    land.clip(clip).plot(ax=ax, color=LAND, edgecolor="#B9AE95", linewidth=0.5, zorder=1)
    mv = B[B.layer == "moved"]
    for _, z in mv.iterrows():
        col = "#9DB4DC" if z.zone.startswith("T_") else "#EBB1A8"
        gpd.GeoSeries([z.geometry], crs=BNG).plot(ax=ax, color=col, alpha=0.75, edgecolor="#8C7E66", linewidth=0.4, zorder=2)
    B[B.layer == "modern"].boundary.plot(ax=ax, color="#A89BB8", linewidth=0.6, zorder=3)
    B[B.layer == "line_mod"].plot(ax=ax, color=PURPLE, linewidth=2.6, zorder=4)
    B[B.layer == "line_hist"].plot(ax=ax, color=INK, linewidth=1.8, linestyle=(0, (3, 2)), zorder=5)
    if dots:
        p = pts.cx[ext[0]:ext[1], ext[2]:ext[3]]
        y = p[p.word == "Y"]; l = p[p.word == "L"]
        ax.scatter(y.geometry.x, y.geometry.y, s=ms, c="white", edgecolors=NAVY, linewidths=1.3, zorder=7)
        ax.scatter(l.geometry.x, l.geometry.y, s=ms, c=RED, edgecolors="white", linewidths=0.7, zorder=8)
    if numbers:
        for code, n, nm, _ in KEYS:
            g = mv[mv.zone == code]
            if g.empty: continue
            pp = g.geometry.iloc[0].representative_point() if code != "L_GM" else g.geometry.iloc[0].centroid
            x, yy = pp.x, pp.y
            if not (ext[0] < x < ext[1] and ext[2] < yy < ext[3]): continue
            ax.text(x, yy, n, ha="center", va="center", fontsize=10.5, family=MONO, color="white", zorder=9,
                    bbox=dict(boxstyle="circle,pad=0.25", fc=INK, ec="white", lw=1))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


fig = plt.figure(figsize=(14, 10))
title(fig, "Where the rose borders run", f"Every business, club and venue in OpenStreetMap whose name says Lancashire or Yorkshire ({len(KP):,} in the region)")
ax = fig.add_axes([0.02, 0.07, 0.64, 0.8])
draw_map(ax)
txt = "\n".join(f"{n}  {nm}\n   {mv_}" for _, n, nm, mv_ in KEYS)
fig.text(0.68, 0.6, "Moved in 1974\n" + txt, fontsize=9.3, family=MONO, color=INK, va="top", linespacing=1.4)
hand = [Line2D([], [], marker="o", ls="", ms=8, mfc=RED, mec="white", label="Name says Lancashire"),
        Line2D([], [], marker="o", ls="", ms=8, mfc="white", mec=NAVY, mew=1.4, label="Name says Yorkshire"),
        Line2D([], [], color=INK, lw=1.8, ls=(0, (3, 2)), label="Historic Lancashire and\nYorkshire border"),
        Line2D([], [], color=PURPLE, lw=2.6, label="Border of the Yorkshire\ncounties since 1974"),
        Patch(fc="#9DB4DC", ec="#8C7E66", label="Left Yorkshire in 1974"), Patch(fc="#EBB1A8", ec="#8C7E66", label="Left Lancashire in 1974")]
fig.legend(handles=hand, loc="upper left", frameon=False, fontsize=10.5, bbox_to_anchor=(0.675, 0.87))
foot(fig)
out(fig, "map")

# ---------- 2. profiles ----------
PR = pd.read_csv(f"{DATA}/profiles.csv")
fig, axs = plt.subplots(1, 2, figsize=(12, 5.6), sharey=True)
fig.subplots_adjust(top=0.78, bottom=0.22, left=0.08, right=0.98, wspace=0.08)
title(fig, "Cross the old line and the names change", "Share of county-named businesses, clubs and venues that say Yorkshire, by distance from each border (5 km bands, 95% intervals)")
for ax, (kind, lab) in zip(axs, (("hist", "Distance from the historic border (km)"), ("mod", "Distance from the 1974 Yorkshire border (km)"))):
    d = PR[(PR.line == kind) & (PR.n > 0)]
    ax.axvspan(-40, 0, color="#F3D9D3", alpha=0.6, lw=0); ax.axvspan(0, 40, color="#DCE4F1", alpha=0.6, lw=0)
    ax.errorbar(d.mid, d.s, yerr=[(d.s - d.lo).clip(lower=0), (d.hi - d.s).clip(lower=0)], fmt="none", ecolor=MUT, elinewidth=1.2, capsize=0, zorder=2)
    ax.scatter(d.mid, d.s, s=18 + 4 * np.sqrt(d.n) * 4, c=[NAVY if v > 0.5 else RED for v in d.s], edgecolors="white", zorder=3)
    ax.axvline(0, color=INK, lw=1.2, ls=(0, (3, 2)) if kind == "hist" else "-")
    ax.set_xlim(-40, 40); ax.set_ylim(-0.04, 1.06); ax.set_xlabel(lab)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.text(-20, 0.55, "Lancashire\nside", ha="center", color=RED, fontsize=11, path_effects=HALO)
    ax.text(20, 0.45, "Yorkshire\nside", ha="center", color=NAVY, fontsize=11, path_effects=HALO)
axs[0].set_ylabel("Names saying Yorkshire")
foot(fig, "Dot size: number of named features. Historic border: Historic County Borders Project. 1974 border: ONS districts grouped into counties.\n" + SRC.split("\n")[1])
out(fig, "profile")

# ---------- 3. rates by zone ----------
H2 = R["H2"]
ROWS = {"L": [("LL", "Historic Lancashire, still Lancashire"), ("L_GM", "Moved: to Greater Manchester"), ("L_MS", "Moved: to Merseyside"),
              ("L_CU", "Moved: Furness and Cartmel, to Cumbria"), ("L_CH", "Moved: Warrington and Widnes, to Cheshire"),
              ("C_GM", "Never Lancashire: Cheshire part of Gtr Manchester"), ("C_MS", "Never Lancashire: Wirral (Merseyside)"),
              ("W_CU", "Never Lancashire: Westmorland"), ("CC", "Never Lancashire: Cheshire"), ("T_YL", "Gained: Bowland and West Craven")],
        "Y": [("YY", "Historic Yorkshire, still Yorkshire (25 km band)"), ("T_YL", "Moved: Bowland and West Craven, to Lancashire"),
              ("T_YG", "Moved: Saddleworth, to Greater Manchester"), ("T_YC", "Moved: Sedbergh and Dent, to Cumbria"),
              ("T_YD", "Moved: south Teesdale, to Durham"), ("LL", "Never Yorkshire: Lancashire (25 km band)"),
              ("L_GM", "Never Yorkshire: Lancashire part of Gtr Manchester"), ("W_CU", "Never Yorkshire: Westmorland")]}
fig, axs = plt.subplots(2, 1, figsize=(11, 11), gridspec_kw={"height_ratios": [10, 8]})
fig.subplots_adjust(top=0.86, bottom=0.13, left=0.4, right=0.93, hspace=0.38)
title(fig, "Do the moved areas keep their old county's name?", "County-named businesses, clubs and venues per 1,000 named points of interest (95% intervals)")
for ax, w in zip(axs, ("L", "Y")):
    rows = ROWS[w]; col = RED if w == "L" else NAVY
    for i, (z, lab) in enumerate(rows):
        r = H2[f"{w}_{z}"]
        y = len(rows) - 1 - i
        ax.plot([max(r["rate_lo"], 0.01), r["rate_hi"]], [y, y], color=col, lw=2, alpha=0.6, solid_capstyle="round")
        if r["n"] > 0:
            ax.scatter([r["rate"]], [y], s=60, c=col, edgecolors="white", zorder=3)
        else:
            ax.scatter([0.01], [y], s=60, marker="<", c="white", edgecolors=col, zorder=3)
        ax.text(1.03, y, f"{r['n']}", transform=ax.get_yaxis_transform(), va="center", fontsize=10, family=MONO, color=MUT)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([l for _, l in rows][::-1], fontsize=10.5)
    ax.set_xscale("log"); ax.set_xlim(0.008, 150)
    ax.set_xticks([0.01, 0.1, 1, 10, 100]); ax.set_xticklabels(["none", "0.1", "1", "10", "100"])
    ax.set_title("Name says " + ("Lancashire" if w == "L" else "Yorkshire"), color=col, fontsize=14, loc="left", family=DISP, fontweight="bold")
    ax.text(1.03, len(rows) - 0.3, "n", transform=ax.get_yaxis_transform(), fontsize=9.5, family=MONO, color=MUT)
    ax.set_xlabel("per 1,000 named points of interest (log scale)")
foot(fig, "Open triangles: none found (the line shows the upper 95% limit). n = county-named features.\n" + SRC)
out(fig, "rates")

# ---------- 4. observed vs expected ----------
EXP = [("Y", "T_YL", "Bowland and West Craven\n(Yorkshire name)"), ("Y", "T_YG", "Saddleworth\n(Yorkshire name)"), ("Y", "T_YC", "Sedbergh and Dent\n(Yorkshire name)"),
       ("L", "L_CU", "Furness and Cartmel\n(Lancashire name)"), ("L", "L_MS", "Merseyside, old Lancashire part\n(Lancashire name)"),
       ("L", "L_GM", "Greater Manchester, old Lancashire part\n(Lancashire name)"), ("L", "L_CH", "Warrington and Widnes\n(Lancashire name)")]
fig, ax = plt.subplots(figsize=(12, 6.8))
fig.subplots_adjust(top=0.8, bottom=0.17, left=0.3, right=0.96)
title(fig, "Fewer old-county names than the old county would have", "Found, and expected if the area were named like the county it left or like a neighbour that was never in it")
for i, (w, z, lab) in enumerate(EXP):
    r = H2[f"{w}_{z}"]; y = len(EXP) - 1 - i; col = RED if w == "L" else NAVY
    ax.barh(y + 0.25, r["expected_at_ref"], height=0.24, color="#D6CDB8", edgecolor="none")
    ax.barh(y, r["n"], height=0.3, color=col)
    ax.barh(y - 0.25, r.get("expected_at_bench") or 0, height=0.24, color="none", edgecolor=MUT, hatch="///", lw=0.6)
    ax.text(max(r["expected_at_ref"], r["n"]) + 1, y + 0.25, f"{r['expected_at_ref']:.0f} if named like the old county", va="center", fontsize=9.5, color=MUT)
    ax.text(r["n"] + 1, y, f"{r['n']} found", va="center", fontsize=10.5, color=col, fontweight="bold")
ax.set_yticks(range(len(EXP))); ax.set_yticklabels([l for _, _, l in EXP][::-1], fontsize=10.5)
ax.set_xlabel("County-named businesses, clubs and venues")
ax.set_xlim(0, 1.45 * max(max(H2[f"{w}_{z}"]["expected_at_ref"], H2[f"{w}_{z}"]["n"]) for w, z, _ in EXP))
hand = [Patch(fc="#D6CDB8", label="expected at the old county's rate"), Patch(fc=GREY, label="found"), Patch(fc="none", ec=MUT, hatch="///", label="expected at a never-in-it neighbour's rate")]
ax.legend(handles=hand, loc="lower right", frameon=False, fontsize=10)
foot(fig)
out(fig, "expected")

# ---------- 5. pooled model and robustness ----------
RB = pd.DataFrame(R["robust"]); RB = RB[RB.group != "band"].reset_index(drop=True)
fig, axs = plt.subplots(1, 2, figsize=(13, 7.4), sharey=True)
fig.subplots_adjust(top=0.76, bottom=0.17, left=0.3, right=0.98, wspace=0.08)
title(fig, "Historic county or county today?", "Rate ratios from the pooled Poisson model: being in the historic county vs being in the county of that name today (95% intervals)")
for ax, w, col in zip(axs, ("L", "Y"), (RED, NAVY)):
    for i, r in RB.iterrows():
        y = len(RB) - 1 - i
        for k, off, mk in (("H", 0.17, "o"), ("M", -0.17, "s")):
            v, lo, hi = r[f"{w}_{k}"], r[f"{w}_{k}_lo"], r[f"{w}_{k}_hi"]
            if not (np.isfinite(v) and lo is not None and np.isfinite(lo) and np.isfinite(hi) and v < 1e4): continue
            ax.plot([lo, hi], [y + off, y + off], color=col if k == "H" else GREY, lw=1.8)
            ax.scatter([v], [y + off], marker=mk, s=40, c=col if k == "H" else "white", edgecolors=col if k == "H" else GREY, zorder=3)
    ax.axvline(1, color=MUT, lw=1, ls=":")
    ax.set_xscale("log"); ax.set_xlim(0.3, 300); ax.set_xticks([0.5, 1, 5, 10, 50, 100]); ax.set_xticklabels(["0.5", "1", "5", "10", "50", "100"])
    ax.set_title("Name says " + ("Lancashire" if w == "L" else "Yorkshire"), color=col, fontsize=14, loc="left", family=DISP, fontweight="bold")
    ax.set_xlabel("rate ratio (log scale)")
axs[0].set_yticks(range(len(RB))); axs[0].set_yticklabels(RB.label[::-1], fontsize=10.5)
hand = [Line2D([], [], marker="o", color=GREY, mfc=GREY, ls="-", label="historic county (holding today's county fixed)"),
        Line2D([], [], marker="s", color=GREY, mfc="white", ls="-", label="county today (holding the historic county fixed)")]
fig.legend(handles=hand, loc="upper left", bbox_to_anchor=(0.3, 0.86), ncol=2, frameon=False, fontsize=10)
foot(fig, "Units: 5 km cells within each zone, offset by named business POIs; errors clustered by 20 km block. Rows not drawn could not be estimated.\n" + SRC.split("\n")[1])
out(fig, "robust")

# ---------- 6. placebo lines ----------
P1 = R["P1"]
fig, ax = plt.subplots(figsize=(10, 5.2))
fig.subplots_adjust(top=0.72, bottom=0.2, left=0.1, right=0.97)
title(fig, "The jump is at the real line, not beside it", "Change in the share saying Yorkshire across the historic border and false borders\n10 km either side (10 km windows, 95% intervals)")
labs = [("false_lancs", "false line\n10 km inside Lancashire"), ("real", "historic border"), ("false_yorks", "false line\n10 km inside Yorkshire")]
for i, (k, lab) in enumerate(labs):
    r = P1[k]
    if r.get("diff") is None: continue
    ax.bar(i, 100 * r["diff"], color=INK if k == "real" else GREY, width=0.55)
    ax.plot([i, i], [100 * r["lo"], 100 * r["hi"]], color=MUT, lw=2)
    ax.text(i, 100 * r["hi"] + 3, f"{100 * r['diff']:+.0f} points\n(n {r['nA']} and {r['nB']})", ha="center", va="bottom", fontsize=10, color=INK)
ax.set_xticks(range(3)); ax.set_xticklabels([l for _, l in labs]); ax.axhline(0, color=MUT, lw=0.8)
ax.set_ylabel("percentage points"); ax.set_ylim(-40, 125)
foot(fig)
out(fig, "placebo")

# ---------- header ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.patch.set_facecolor(PAPER)
ax = fig.add_axes([0.5, 0.02, 0.48, 0.96]); draw_map(ax, ext=(310000, 450000, 410000, 500000), numbers=False, ms=22)
fig.text(0.05, 0.78, "Does the 1974\nborder still show?", fontsize=40, family=DISP, fontweight="bold", color=INK, va="top", linespacing=1.0)
fig.text(0.05, 0.47, "Lancashire and Yorkshire\nin business names", fontsize=21, color=RED, va="top", linespacing=1.15)
fig.text(0.05, 0.25, "Every shop, club and venue in OpenStreetMap\nthat names itself after either county,\nand the lines moved in 1974", fontsize=13.5, color=MUT, va="top", linespacing=1.35)
fig.text(0.05, 0.05, "maps.tristanhotham.com/rose-border", fontsize=11, family=MONO, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER)
plt.close(fig)
im = Image.open(f"{ROOT}/header.png"); assert im.size == (1200, 630), im.size
print("figures done", sorted(os.listdir(IMG)), sorted(f for f in os.listdir(BLOG) if f.endswith(".png")))
