"""Step 2: the named features. Reads the shared OSM name file (read only), keeps names with a Lancashire or Yorkshire word
(or a red/white rose), drops roads, lines, street-derived and product names, classifies type (private, public, chain),
removes duplicates, applies the hand decisions in code/overrides.csv, and attaches historic county, modern county, zone,
distances to the two lines, 5 km cell and 20 km block.
Outputs: data/features.csv (every kept feature with all flags), SCR/readlist.csv (names for reading by eye, no zone columns)."""
import csv, pickle, sys
import numpy as np, pandas as pd, geopandas as gpd, shapely
from shapely import wkt as swkt
from pyproj import Transformer
from common import *

csv.field_size_limit(10 ** 9)
rows = list(csv.reader(open(f"{RAW}/osm_names_rose_kingdom.tsv", encoding="utf-8"), delimiter="\t"))
hdr = [h.lstrip("?") for h in rows[0]]
D = pd.DataFrame(rows[1:], columns=hdr)
n_file = len(D)
D["name"] = D.name.str.strip().str.strip('"')
D["osm"] = D.x.str.strip("<>").str.replace("https://www.openstreetmap.org/", "", regex=False)
D["L"] = D.name.str.contains(COUNTY_RE["L"].pattern.replace("(","(?:"), case=False); D["Y"] = D.name.str.contains(COUNTY_RE["Y"].pattern.replace("(","(?:"), case=False)
D["rL"] = D.name.str.contains(ROSE_RE["L"]); D["rY"] = D.name.str.contains(ROSE_RE["Y"])
D = D[D.L | D.Y | D.rL | D.rY].copy()
flow = {"file_rows": n_file, "county_or_rose": len(D)}
for k in ("shop", "amenity", "office", "craft", "leisure", "highway"):
    D[k] = D[k].str.strip('"')
D["gtype"] = D.wkt.str.extract(r"^([A-Z]+)")[0]


def point(w):
    w = re.sub(r"\^\^<[^>]*>$", "", w.strip()).strip('"')
    g = swkt.loads(w)
    if g.geom_type == "Point":
        return g.x, g.y
    if g.geom_type in ("LineString", "MultiLineString"):
        p = g.interpolate(0.5, normalized=True)
        return p.x, p.y
    p = g.representative_point()
    return p.x, p.y


xy = [point(w) for w in D.wkt]
D["lon"] = [round(a, 6) for a, b in xy]; D["lat"] = [round(b, 6) for a, b in xy]
D = D.drop(columns=["wkt", "x"])

# word class
D["word"] = np.where(D.L & D.Y, "both", np.where(D.L, "L", np.where(D.Y, "Y", np.where(D.rL & D.rY, "rose_both", np.where(D.rL, "rose_L", "rose_Y")))))
tagged = D[["shop", "amenity", "office", "craft", "leisure"]].ne("").any(axis=1)
PUBLIC = re.compile(r"\b(police|constabulary|council|nhs|ambulance|fire and rescue|fire & rescue|fire station|probation|"
                    r"court|courts|magistrates|county hall|passenger transport|metro\b|university|college|school|academy|"
                    r"sixth form|hospital|health|clinical commissioning|ccg|primary care|mental health|hospice|water\b|"
                    r"electricity|power ?grid|gas\b|army|regiment|cadet|cadets|reserve|territorial|air ambulance|coroner|"
                    r"crown prosecution|record office|archive|archives|library|museum|wildlife trust|national park|"
                    r"environment agency|highways|combined authority|mayor|fusiliers)\b", re.I)
PRODUCT = re.compile(r"\b(yorkshire|lancashire)\s+(pudding|puddings|terrier|terriers|tea|hotpot|hot pot|cheese|parkin|"
                     r"curd|rhubarb|relish|crisps|caviar)\b", re.I)
D["dropped"] = ""
D.loc[D.highway != "", "dropped"] = "highway"
D.loc[(D["dropped"] == "") & D.gtype.isin(["LINESTRING", "MULTILINESTRING"]) & ~tagged, "dropped"] = "line (railway, canal, path)"
D.loc[(D["dropped"] == "") & D.name.str.contains(STREET_RE), "dropped"] = "street name"
D.loc[(D["dropped"] == "") & D.name.str.contains(PRODUCT), "dropped"] = "product or breed"
D["type"] = np.where(D.name.str.contains(PUBLIC) | D.amenity.isin(["police", "townhall", "courthouse", "fire_station", "school",
                     "college", "university", "hospital", "clinic", "doctors", "library", "prison"]), "public", "private")

# hand decisions
O = pd.read_csv(os.path.join(ROOT, "code", "overrides.csv"), dtype=str).fillna("") if os.path.exists(
    os.path.join(ROOT, "code", "overrides.csv")) else pd.DataFrame(columns=["osm", "name", "set", "value", "why"])
n_over = 0
for _, o in O.iterrows():
    m = D.osm == o.osm
    if not m.any():
        sys.exit(f"override not found {o.osm} {o['name']}")
    D.loc[m, o["set"]] = o.value; n_over += 1
flow["overrides"] = n_over

# geography
geo = pickle.load(open(f"{SCR}/geo.pkl", "rb"))
tb = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
D["x"], D["y"] = tb.transform(D.lon.values, D.lat.values)
pts = shapely.points(D.x.values, D.y.values)
D["hist"] = ""
for n, g in geo["hist"].items():
    D.loc[shapely.contains(g, pts), "hist"] = n
D["modern"] = ""
for c, g in geo["cer"].items():
    D.loc[shapely.contains(g, pts) & (D.modern == ""), "modern"] = c
D["zone"] = ""
Z = geo["zones"]
for _, z in Z.iterrows():
    D.loc[shapely.contains(z.geometry, pts) & (D.zone == ""), "zone"] = z.zone
dH = shapely.distance(geo["lh"], pts) / 1000; dM = shapely.distance(geo["lm"], pts) / 1000
D["d_hist"] = np.round(np.where(D["hist"] == "Yorkshire", dH, np.where(D["hist"] == "Lancashire", -dH, np.nan)), 2)
D["d_mod"] = np.round(np.where(D.modern.isin(YORKS_CER), dM, np.where(D.modern.isin(["Lancashire", "Greater Manchester", "Cumbria"]), -dM, np.nan)), 2)
D["absd_hist"] = np.round(dH, 2)
D["cell5"] = (np.floor(D.x / 5000)).astype(int).astype(str) + "_" + (np.floor(D.y / 5000)).astype(int).astype(str)
D["block20"] = (np.floor(D.x / 20000)).astype(int).astype(str) + "_" + (np.floor(D.y / 20000)).astype(int).astype(str)
lad = gpd.read_file(f"{GEO}/lad23_bgc.geojson").to_crs("EPSG:27700")
j = gpd.sjoin(gpd.GeoDataFrame(D[["osm"]], geometry=gpd.points_from_xy(D.x, D.y), crs="EPSG:27700"), lad[["LAD23NM", "geometry"]], how="left", predicate="within")
D["lad"] = j.drop_duplicates("osm").set_index("osm").LAD23NM.reindex(D.osm).fillna("").values

# duplicates: same normalised name within DEDUP_M (keep the first: tagged, then node)
D["nn"] = D.name.map(norm)
D["dup_of"] = ""
K = D[D["dropped"] == ""].copy()
K["rank"] = (~K[["shop", "amenity", "office", "craft", "leisure"]].ne("").any(axis=1)).astype(int) * 2 + (~K.osm.str.startswith("node")).astype(int)
K = K.sort_values(["nn", "rank", "osm"])
for nn, g in K.groupby("nn"):
    if len(g) < 2:
        continue
    keep = []
    for i, r in g.iterrows():
        hit = next((k for k in keep if math.hypot(r.x - D.at[k, "x"], r.y - D.at[k, "y"]) < DEDUP_M), None)
        if hit is None:
            keep.append(i)
        else:
            D.at[i, "dup_of"] = D.at[hit, "osm"]
# chains: same normalised name at CHAIN_N or more places more than 1 km apart (after deduplication)
U = D[(D["dropped"] == "") & (D.dup_of == "")]
chain = set()
for nn, g in U.groupby("nn"):
    if len(g) < CHAIN_N:
        continue
    xy_ = g[["x", "y"]].values
    far = [k for k in range(len(g)) if all(np.hypot(*(xy_[k] - xy_[m])) > 1000 for m in range(k))]
    if len(far) >= CHAIN_N:
        chain.add(nn)
D["chain"] = D.nn.isin(chain).astype(int)
D.loc[(D.chain == 1) & (D.type == "private"), "type"] = "chain"
# re-apply type overrides (they win over the chain rule)
for _, o in O[O["set"] == "type"].iterrows():
    D.loc[D.osm == o.osm, "type"] = o.value
D["tagged"] = D[["shop", "amenity", "office", "craft", "leisure"]].ne("").any(axis=1).astype(int)
D["tag"] = D.apply(lambda r: next((f"{k}={r[k]}" for k in ("shop", "amenity", "office", "craft", "leisure") if r[k]), ""), axis=1)
D["sliver"] = (D.zone == "SLIVER").astype(int)
cols = ["osm", "name", "word", "type", "tag", "tagged", "gtype", "dropped", "dup_of", "chain", "lon", "lat", "hist", "modern", "zone",
        "lad", "d_hist", "d_mod", "absd_hist", "cell5", "block20", "sliver"]
D[cols].sort_values("osm").to_csv(f"{DATA}/features.csv", index=False)
# list for reading by eye: name and tags only, no zone or distance
R = D[(D["dropped"] == "") & (D.dup_of == "") & ((D.absd_hist <= 40) | D.zone.str.match(r"^(T_|L_|C_|U_|W_)"))]
R[["osm", "name", "type", "tag", "gtype"]].sort_values("name").to_csv(f"{SCR}/readlist.csv", index=False)
flow.update({"dropped": D[D["dropped"] != ""]["dropped"].value_counts().to_dict(), "duplicates": int((D.dup_of != "").sum()),
             "kept": int(((D["dropped"] == "") & (D.dup_of == "")).sum()), "chains_names": len(chain), "readlist": len(R)})
jsave(flow, f"{SCR}/flow02.json", indent=1)
print(json.dumps(flow, indent=1))
K = D[(D["dropped"] == "") & (D.dup_of == "")]
print(K.type.value_counts().to_dict(), K.word.value_counts().to_dict())
