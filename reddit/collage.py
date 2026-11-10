"""Reddit collage (r/dataisbeautiful style): the rose border map, the jump at the line, and the moved areas. Light background,
labels on paper or sea. Output: reddit/rose_border_collage.png (2700 px wide)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import box
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
PAPER, INK, MUT, SEA, LAND = "#F6EED8", "#2B2119", "#6E604E", "#DCE6E8", "#F1E7CF"
RED, NAVY, PURPLE = "#C0392B", "#1F3A68", "#5B2A86"
plt.rcParams.update({"font.family": "Source Serif 4", "figure.facecolor": PAPER, "axes.facecolor": PAPER, "axes.edgecolor": MUT,
                     "xtick.color": MUT, "ytick.color": MUT, "axes.spines.top": False, "axes.spines.right": False})
R = jload(f"{DATA}/results.json"); H2 = R["H2"]; SH = R["H1"]["shares"]; X = R["x"]
BNG = "EPSG:27700"
F = pd.read_csv(f"{DATA}/features.csv", keep_default_na=False)
K = F[(F.dropped == "") & (F.dup_of == "") & (F.type == "private") & F.word.isin(["L", "Y"]) & (F.zone != "") & (F.zone != "SLIVER")]
pts = gpd.GeoDataFrame(K, geometry=gpd.points_from_xy(K.lon, K.lat), crs="EPSG:4326").to_crs(BNG)
B = gpd.read_file(f"{DATA}/boundaries.geojson").to_crs(BNG)
world = gpd.read_file(f"{GEO}/ne_10m_admin_0_countries.geojson")
land = world[world.ADMIN.isin(["United Kingdom", "Isle of Man"])].to_crs(BNG)

fig = plt.figure(figsize=(18, 13.5), dpi=150)
fig.text(0.03, 0.965, "Does the 1974 border still show?", fontsize=40, family=DISP, fontweight="bold", color=INK, va="top")
fig.text(0.03, 0.905, f"Every shop, club and venue in OpenStreetMap named after Lancashire or Yorkshire ({R['flow']['main_n']}), against the old county border and the lines redrawn in 1974",
         fontsize=16, color=MUT, va="top")
ax = fig.add_axes([0.02, 0.07, 0.56, 0.8])
EXT = (288000, 470000, 372000, 528000)
ax.set_facecolor(SEA)
land.clip(box(EXT[0] - 5000, EXT[2] - 5000, EXT[1] + 5000, EXT[3] + 5000)).plot(ax=ax, color=LAND, edgecolor="#B9AE95", linewidth=0.5)
for _, z in B[B.layer == "moved"].iterrows():
    gpd.GeoSeries([z.geometry], crs=BNG).plot(ax=ax, color="#9DB4DC" if z.zone.startswith("T_") else "#EBB1A8", alpha=0.8, edgecolor="#8C7E66", linewidth=0.4)
B[B.layer == "modern"].boundary.plot(ax=ax, color="#A89BB8", linewidth=0.6)
B[B.layer == "line_mod"].plot(ax=ax, color=PURPLE, linewidth=3)
B[B.layer == "line_hist"].plot(ax=ax, color=INK, linewidth=2, linestyle=(0, (3, 2)))
p = pts.cx[EXT[0]:EXT[1], EXT[2]:EXT[3]]
ax.scatter(p[p.word == "Y"].geometry.x, p[p.word == "Y"].geometry.y, s=46, c="white", edgecolors=NAVY, linewidths=1.6, zorder=6)
ax.scatter(p[p.word == "L"].geometry.x, p[p.word == "L"].geometry.y, s=46, c=RED, edgecolors="white", linewidths=0.8, zorder=7)
# labels on the Irish Sea
for (x, y, t) in ((296000, 448000, "Irish\nSea"),):
    ax.text(x, y, t, fontsize=14, style="italic", color="#7F97A3", ha="left")
ax.set_xlim(EXT[0], EXT[1]); ax.set_ylim(EXT[2], EXT[3]); ax.set_aspect("equal"); ax.axis("off")
hand = [Line2D([], [], marker="o", ls="", ms=10, mfc=RED, mec="white", label="Name says Lancashire"),
        Line2D([], [], marker="o", ls="", ms=10, mfc="white", mec=NAVY, mew=1.6, label="Name says Yorkshire"),
        Line2D([], [], color=INK, lw=2, ls=(0, (3, 2)), label="Historic Lancashire and Yorkshire border"),
        Line2D([], [], color=PURPLE, lw=3, label="Border of the Yorkshire counties since 1974"),
        Patch(fc="#9DB4DC", ec="#8C7E66", label="Left Yorkshire in 1974 (Bowland, Saddleworth, Sedbergh...)"),
        Patch(fc="#EBB1A8", ec="#8C7E66", label="Left Lancashire in 1974 (Furness, Manchester, Liverpool...)")]
fig.legend(handles=hand, loc="upper left", bbox_to_anchor=(0.6, 0.875), frameon=False, fontsize=13.5)

# panel: jump at the line
a2 = fig.add_axes([0.63, 0.47, 0.34, 0.17])
PR = pd.read_csv(f"{DATA}/profiles.csv"); d = PR[(PR.line == "hist") & (PR.n > 0)]
a2.axvspan(-40, 0, color="#F3D9D3", lw=0); a2.axvspan(0, 40, color="#DCE4F1", lw=0)
a2.scatter(d.mid, 100 * d.s, s=30 + 25 * np.sqrt(d.n), c=[NAVY if v > 0.5 else RED for v in d.s], edgecolors="white", zorder=3)
a2.axvline(0, color=INK, ls=(0, (3, 2)))
a2.set_xlim(-40, 40); a2.set_ylim(-8, 108); a2.set_yticks([0, 50, 100]); a2.set_yticklabels(["0%", "50%", "100%"], fontsize=12)
a2.set_xlabel("km from the old border (Lancashire side left)", fontsize=12.5); a2.tick_params(labelsize=12)
fig.text(0.63, 0.675, f"Cross the old line and the rose flips", fontsize=19, family=DISP, fontweight="bold", color=INK)
fig.text(0.63, 0.655, f"Within 25 km, share saying Yorkshire: {SH['YY']['nY']} of {SH['YY']['n']} on one side, {SH['LL']['nY']} of {SH['LL']['n']} on the other", fontsize=12.5, color=MUT)

# panel: moved areas
a3 = fig.add_axes([0.79, 0.16, 0.18, 0.2])
rows = [("LL", "Lancashire today"), ("L_GM", "Old Lancashire part\nof Gtr Manchester"), ("L_MS", "Old Lancashire part\nof Merseyside"),
        ("C_GM", "Old Cheshire part of\nGtr Manchester"), ("L_CU", "Furness and Cartmel\n(now Cumbria)")]
for i, (z, lab) in enumerate(rows):
    r = H2[f"L_{z}"]; y = len(rows) - 1 - i
    a3.barh(y, r["rate"], color=RED if r["n"] else "white", edgecolor=RED, height=0.62)
    a3.text(r["rate"] + 0.1, y, f"{r['rate']:.1f}" if r["n"] else "none", va="center", fontsize=12.5, color=INK)
a3.set_yticks(range(len(rows))); a3.set_yticklabels([l for _, l in rows][::-1], fontsize=12)
a3.set_xlim(0, 5.6); a3.set_xlabel("per 1,000 businesses", fontsize=12); a3.tick_params(axis="x", labelsize=11)
fig.text(0.63, 0.392, "Leave Lancashire and the name thins", fontsize=19, family=DISP, fontweight="bold", color=INK)
fig.text(0.63, 0.372, "Lancashire-named businesses per 1,000 named businesses on the map", fontsize=12.5, color=MUT)
fig.text(0.63, 0.055, ("The planned main test could not be run: Bowland, Barnoldswick and Saddleworth\n(left Yorkshire in 1974) have no county-named businesses on the map."),
         fontsize=12.5, color=INK, style="italic")
fig.text(0.03, 0.02, "Data: OpenStreetMap contributors (ODbL), via QLever and OpenFreeMap; Historic County Borders Project; ONS districts (OGL v3.0)   ·   maps.tristanhotham.com/rose-border",
         fontsize=11.5, family="IBM Plex Mono", color=MUT)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rose_border_collage.png")
fig.savefig(out, dpi=150, facecolor=PAPER)
print(out)
