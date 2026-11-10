"""Step 3b: assign every named OpenFreeMap POI (from step 3, kept in SCR) to its zone, 5 km cell, 20 km block and 5 km bins of
signed distance to the historic and modern lines, and aggregate. The POIs themselves are not redistributed.
Output: data/poi_units.csv (zone x cell x distance bins: business POIs and all named POIs), data/ofm_rose_check.csv."""
import glob, pickle
import numpy as np, pandas as pd, shapely
from pyproj import Transformer
from common import *

P = pd.concat([pd.read_csv(f, header=None, names=["lon", "lat", "cls", "sub", "name"], keep_default_na=False)
               for f in sorted(glob.glob(f"{SCR}/ofm_part_*.csv"))]).drop_duplicates(["lon", "lat", "name"])
P["bus"] = (~P.cls.isin(NONBUS)).astype(int)
geo = pickle.load(open(f"{SCR}/geo.pkl", "rb"))
tb = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
x, y = tb.transform(P.lon.values, P.lat.values)
pts = shapely.points(x, y)
hist = np.full(len(P), "", dtype=object); modern = np.full(len(P), "", dtype=object); zone = np.full(len(P), "", dtype=object)
for n, g in geo["hist"].items():
    hist[shapely.contains(g, pts)] = n
for c, g in geo["cer"].items():
    m = shapely.contains(g, pts) & (modern == ""); modern[m] = c
for _, z in geo["zones"].iterrows():
    m = shapely.contains(z.geometry, pts) & (zone == ""); zone[m] = z.zone
dH = shapely.distance(geo["lh"], pts) / 1000; dM = shapely.distance(geo["lm"], pts) / 1000
d_hist = np.where(hist == "Yorkshire", dH, np.where(hist == "Lancashire", -dH, np.nan))
d_mod = np.where(np.isin(modern, list(YORKS_CER)), dM, np.where(np.isin(modern, ["Lancashire", "Greater Manchester", "Cumbria"]), -dM, np.nan))
P["zone"], P["hist"], P["modern"] = zone, hist, modern
P["cell5"] = pd.Series(np.floor(x / 5000).astype(int)).astype(str).values + "_" + pd.Series(np.floor(y / 5000).astype(int)).astype(str).values
P["block20"] = pd.Series(np.floor(x / 20000).astype(int)).astype(str).values + "_" + pd.Series(np.floor(y / 20000).astype(int)).astype(str).values
P["cell10"] = pd.Series(np.floor(x / 10000).astype(int)).astype(str).values + "_" + pd.Series(np.floor(y / 10000).astype(int)).astype(str).values
P["bh"] = np.where(np.isnan(d_hist), 999, np.floor(np.nan_to_num(d_hist, nan=0) / 5) * 5).astype(int)
P["bm"] = np.where(np.isnan(d_mod), 999, np.floor(np.nan_to_num(d_mod, nan=0) / 5) * 5).astype(int)
P["absd"] = np.round(dH, 1)
P["band"] = np.select([dH <= 10, dH <= 15, dH <= 25, dH <= 40], [10, 15, 25, 40], 999)
P = P[P.zone != ""]
U = P.groupby(["zone", "hist", "modern", "cell5", "cell10", "block20", "bh", "bm", "band"]).agg(poi_bus=("bus", "sum"), poi_all=("bus", "size")).reset_index()
U.to_csv(f"{DATA}/poi_units.csv", index=False)
rose = P[P.name.str.contains(r"(?i)\b(?:lancashire|lancs|lancastrian|yorkshire|yorks)\b", regex=True)]
rose[["name", "cls", "sub", "lon", "lat", "zone"]].sort_values("name").to_csv(f"{DATA}/ofm_rose_check.csv", index=False)
print("POIs in zones", len(P), "business", int(P.bus.sum()), "units", len(U), "county-word POIs", len(rose))
print(P.groupby("zone").bus.sum().sort_values(ascending=False).head(25).to_dict())
