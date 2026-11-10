"""Step 1: boundaries. Historic counties (Historic County Borders Project, UK Definition A) and modern ceremonial counties
(built from ONS December 2023 districts), their overlay into zones (historic x modern), the historic Lancashire/Yorkshire
line and the modern line between the Yorkshire counties and Lancashire, Greater Manchester and Cumbria.
Outputs: SCR/geo.pkl (British National Grid geometries for later steps), data/zones.csv (area of every zone piece),
data/boundaries.geojson (WGS84, simplified, for the page)."""
import pickle
import geopandas as gpd, pandas as pd, shapely
from shapely.ops import unary_union
from common import *

BNG = "EPSG:27700"
H = gpd.read_file(f"{HCT}/UKDefinitionA.shp").to_crs(BNG)
HIST = ["Lancashire", "Yorkshire", "Cheshire", "Westmorland", "Cumberland", "Durham", "Derbyshire", "Lincolnshire",
        "Nottinghamshire", "Northumberland"]
hist = {n: shapely.make_valid(H[H.NAME == n].geometry.union_all()) for n in HIST}

L = gpd.read_file(f"{GEO}/lad23_bgc.geojson").to_crs(BNG)
L["cer"] = L.LAD23NM.map(LAD2CER)
L.loc[L.LAD23NM.isin(SPLIT_LAD), "cer"] = "SPLIT"
assert set(LAD2CER) - set(L.LAD23NM) <= set(), set(LAD2CER) - set(L.LAD23NM)
cer = {c: shapely.make_valid(L[L.cer == c].geometry.union_all()) for c in CER}
split = L[L.cer == "SPLIT"].geometry.union_all()
# Stockton-on-Tees: north of the Tees is ceremonial Durham, south is North Yorkshire; the historic line is the Tees
cer["Durham"] = unary_union([cer["Durham"], split.intersection(hist["Durham"])])
cer["North Yorkshire"] = unary_union([cer["North Yorkshire"], split.difference(hist["Durham"])])
modg = {}
for c, g in cer.items():
    modg.setdefault(mod_group(c), []).append(g)
modg = {k: unary_union(v) for k, v in modg.items()}

# zone pieces
rows, pieces = [], []
for hn, hg in hist.items():
    for mn, mg in modg.items():
        g = hg.intersection(mg)
        if g.is_empty:
            continue
        parts = [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon"]
        big = [p for p in parts if p.area / 1e6 >= SLIVER_KM2]
        small = [p for p in parts if p.area / 1e6 < SLIVER_KM2]
        code = ZONES.get((hn, mn), (f"{hn[:3]}>{mn[:6]}", f"{hn} in {mn}"))[0]
        stayed = (hn == mn) or (hn == "Yorkshire" and mn == "Yorkshire")
        rows.append({"historic": hn, "modern": mn, "zone": code, "area_km2": round(sum(p.area for p in big) / 1e6, 1),
                     "sliver_km2": round(sum(p.area for p in small) / 1e6, 2), "n_parts": len(big)})
        if big:
            pieces.append({"historic": hn, "modern": mn, "zone": code, "geometry": unary_union(big)})
        if small and not stayed:
            pieces.append({"historic": hn, "modern": mn, "zone": "SLIVER", "geometry": unary_union(small)})
        elif small:
            pieces.append({"historic": hn, "modern": mn, "zone": code, "geometry": unary_union(small)})
Z = gpd.GeoDataFrame(pieces, crs=BNG)
ZT = pd.DataFrame(rows).sort_values("area_km2", ascending=False)
ZT.to_csv(f"{DATA}/zones.csv", index=False)
print(ZT[ZT.area_km2 > 0].to_string())

# lines
lh = hist["Yorkshire"].boundary.intersection(hist["Lancashire"].buffer(300))
west = unary_union([cer["Lancashire"], cer["Greater Manchester"], cer["Cumbria"]])
lm = modg["Yorkshire"].boundary.intersection(west.buffer(300))
print("historic line km", round(lh.length / 1000, 1), "modern line km", round(lm.length / 1000, 1))

region = unary_union([hist["Lancashire"], hist["Yorkshire"]] + [cer[c] for c in REGION_CER])
pickle.dump({"hist": hist, "cer": cer, "modg": modg, "zones": Z, "lh": lh, "lm": lm, "region": region}, open(f"{SCR}/geo.pkl", "wb"))

# web layers (WGS84, simplified)
feats = []
def add(g, props, tol):
    feats.append({**props, "geometry": g.simplify(tol)})
for n in ("Lancashire", "Yorkshire"):
    add(hist[n], {"layer": "historic", "name": n}, 120)
for c in ("Lancashire", "Greater Manchester", "Merseyside", "Cumbria", "Cheshire", "North Yorkshire", "West Yorkshire",
          "South Yorkshire", "East Riding of Yorkshire", "Durham"):
    add(cer[c], {"layer": "modern", "name": c}, 120)
for _, z in Z[Z.zone.str.match(r"^(T_|L_)") & (Z.zone != "L_YO")].iterrows():
    add(z.geometry, {"layer": "moved", "zone": z.zone, "name": ZONES[(z.historic, z.modern)][1]}, 80)
add(lh, {"layer": "line_hist", "name": "Historic Lancashire and Yorkshire border"}, 60)
add(lm, {"layer": "line_mod", "name": "Yorkshire counties' border since 1974"}, 60)
W = gpd.GeoDataFrame(feats, crs=BNG).to_crs("EPSG:4326")
W["geometry"] = W.geometry.set_precision(1e-4)
W.to_file(f"{DATA}/boundaries.geojson", driver="GeoJSON")
print("boundaries.geojson", os.path.getsize(f"{DATA}/boundaries.geojson") // 1024, "KB")
