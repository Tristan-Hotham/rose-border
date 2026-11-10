"""Step 3: the denominator. Every OpenFreeMap vector tile at zoom 14 that touches the study region (historic Lancashire and
Yorkshire plus the modern counties around them) is read once, in memory; named points of interest in the poi layer are
counted per 1 km grid cell (British National Grid), split into businesses and venues (shops, food and drink, offices,
leisure, lodging, services) and everything else (transport, parking, street furniture), which is not used. POIs whose
name contains a county word are also kept as a check on the main name file (OSM from QLever).
Outputs: data/poi_cells.csv.gz (cell x, y in km, named business POIs, all named POIs), SCR/ofm_rose.csv.
Resumable: progress is kept in SCR/ofm_done.txt and SCR/ofm_part_*.csv."""
import io, sys, time, urllib.request, pickle, csv, glob
import numpy as np, pandas as pd, shapely
import mapbox_vector_tile as mvt
from pyproj import Transformer
from concurrent.futures import ThreadPoolExecutor
from common import *

Z = 14
N = 2 ** Z
UA = {"User-Agent": "historical-geography-data-study/1.0 (research; maps.tristanhotham.com)"}
geo = pickle.load(open(f"{SCR}/geo.pkl", "rb"))
region = geo["region"].buffer(1000)
to_ll = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def lonlat_tile(lon, lat):
    x = (lon + 180) / 360 * N
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * N
    return x, y


def tile_lonlat(x, y):
    lon = x / N * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / N))))
    return lon, lat


minx, miny, maxx, maxy = region.bounds
(lo0, la0), (lo1, la1) = to_ll.transform(minx, miny), to_ll.transform(maxx, maxy)
x0, y1 = lonlat_tile(lo0 - 0.1, la0 - 0.05); x1, y0 = lonlat_tile(lo1 + 0.1, la1 + 0.05)
prep = shapely.prepared.prep(region)
tiles = []
for tx in range(int(x0), int(x1) + 1):
    for ty in range(int(y0), int(y1) + 1):
        a, b = tile_lonlat(tx, ty + 1), tile_lonlat(tx + 1, ty)
        (ax, ay), (bx, by) = to_bng.transform(*a), to_bng.transform(*b)
        if prep.intersects(shapely.box(ax, ay, bx, by)):
            tiles.append((tx, ty))
print("tiles", len(tiles), file=sys.stderr)
done = set()
if os.path.exists(f"{SCR}/ofm_done.txt"):
    done = {tuple(map(int, l.split())) for l in open(f"{SCR}/ofm_done.txt")}
todo = [t for t in tiles if t not in done]
tj = json.load(urllib.request.urlopen(urllib.request.Request("https://tiles.openfreemap.org/planet", headers=UA)))
URL = tj["tiles"][0]
open(f"{SCR}/ofm_version.txt", "w").write(URL)


def fetch(t):
    tx, ty = t
    for k in range(5):
        try:
            b = urllib.request.urlopen(urllib.request.Request(URL.format(z=Z, x=tx, y=ty), headers=UA), timeout=60).read()
            d = mvt.decode(b, default_options={"y_coord_down": True})
            out = []
            lay = d.get("poi")
            if not lay:
                return t, out
            ext = lay.get("extent", 4096)
            for f in lay["features"]:
                p = f["properties"]; nm = p.get("name")
                if not nm:
                    continue
                g = f["geometry"]
                if g["type"] != "Point":
                    continue
                gx, gy = g["coordinates"]
                if not (0 <= gx < ext and 0 <= gy < ext):
                    continue   # buffer area: belongs to the neighbouring tile
                lon, lat = tile_lonlat(tx + gx / ext, ty + gy / ext)
                out.append((lon, lat, p.get("class", ""), p.get("subclass", ""), nm))
            return t, out
        except Exception as e:
            time.sleep(2 + 3 * k)
    return t, None


part = len(glob.glob(f"{SCR}/ofm_part_*.csv"))
fo = open(f"{SCR}/ofm_part_{part:03d}.csv", "w", newline="", encoding="utf-8"); w = csv.writer(fo)
fd = open(f"{SCR}/ofm_done.txt", "a")
t0 = time.time(); n = 0
with ThreadPoolExecutor(4) as ex:
    for t, out in ex.map(fetch, todo):
        if out is None:
            continue
        for r in out:
            w.writerow(r)
        fd.write(f"{t[0]} {t[1]}\n"); n += 1
        if n % 500 == 0:
            fo.flush(); fd.flush(); print(n, "of", len(todo), round(time.time() - t0), "s", file=sys.stderr)
fo.close(); fd.close()
done = {tuple(map(int, l.split())) for l in open(f"{SCR}/ofm_done.txt")}
missing = [t for t in tiles if t not in done]
print("missing tiles", len(missing), file=sys.stderr)
if missing:
    sys.exit("rerun to fetch the missing tiles")

# aggregate to 1 km cells
P = pd.concat([pd.read_csv(f, header=None, names=["lon", "lat", "cls", "sub", "name"], keep_default_na=False)
               for f in sorted(glob.glob(f"{SCR}/ofm_part_*.csv"))])
P = P.drop_duplicates(["lon", "lat", "name"])
x, y = to_bng.transform(P.lon.values, P.lat.values)
P["cx"], P["cy"] = (np.floor(x / 1000)).astype(int), (np.floor(y / 1000)).astype(int)
P["bus"] = (~P.cls.isin(NONBUS)).astype(int)
C = P.groupby(["cx", "cy"]).agg(poi_bus=("bus", "sum"), poi_all=("bus", "size")).reset_index()
C.to_csv(f"{DATA}/poi_cells.csv.gz", index=False)
rose = P[P.name.str.contains(r"(?i)\b(?:lancashire|lancs|yorkshire|yorks|red rose|white rose)\b", regex=True)]
rose.to_csv(f"{SCR}/ofm_rose.csv", index=False)
print("named POIs", len(P), "business POIs", int(P.bus.sum()), "cells", len(C), "rose POIs", len(rose), "classes",
      P.cls.value_counts().head(40).to_dict(), file=sys.stderr)
