"""Shared paths, constants and helpers for the rose-border study ("Does the 1974 border still show?
Lancashire and Yorkshire in business names").

Inputs (read in place, never modified):
  RAW/osm_names_rose_kingdom.tsv  OpenStreetMap features in the UK whose name contains Lancashire, Lancs, Yorkshire, Yorks,
                                  Red Rose, White Rose and early kingdom names, queried through QLever (osm-planet),
                                  retrieved 2026. Columns ?x (OSM URI), ?name, ?shop, ?amenity, ?office, ?craft,
                                  ?leisure, ?highway, ?wkt. ODbL, (c) OpenStreetMap contributors. Shared with the
                                  lost-kingdoms study: read only.
  HCT/UKDefinitionA.shp           Historic Counties Trust, Historic County Borders Project, UK Definition A (simplified,
                                  WGS84, release 2024-05-29), from the GitHub repository Beyond-Notability/bn_notes
                                  (shp/hcp_uk_counties). Free for any use with acknowledgement.
  GEO/lad23_bgc.geojson           ONS Local Authority Districts, December 2023, generalised clipped (Open Government
                                  Licence v3.0; contains OS data Crown copyright and database right). Grouped into
                                  ceremonial counties below.
  OFM (network)                   OpenFreeMap vector tiles (OpenMapTiles schema, OpenStreetMap data, ODbL), zoom 14,
                                  poi layer: the count of named points of interest per grid cell, the denominator for
                                  name rates. Fetched by 03_poi_tiles.py into SCR and aggregated; tiles not kept.
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("RB_RAW", "/home/claude/newdata/raw_new13")
GEO = os.environ.get("RB_GEO", "/home/claude/newdata/raw/geo")
SCR = os.environ.get("RB_SCRATCH", "/home/claude/scratch/rose-border")
HCT = os.environ.get("RB_HCT", os.path.join(SCR, "dl/bn/shp/hcp_uk_counties"))
FONTS = os.environ.get("RB_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "rose-border"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
TITLE = "Does the 1974 border still show?"
SUB = "Lancashire and Yorkshire in business names"

# ---- pre-specified constants (NOTES.md, analysis plan) ----
BAND_KM = 25.0          # main bandwidth around the historic Lancashire/Yorkshire line
BANDS = [10.0, 15.0, 25.0, 40.0]
SLIVER_KM2 = 5.0        # pieces of (historic x modern) smaller than this are boundary slivers: modern = historic
CELL_KM = 5.0           # grid for the rate models
BLOCK_KM = 20.0         # cluster blocks
DEDUP_M = 300.0         # same normalised name within this distance = one feature
CHAIN_N = 3             # same normalised name at this many places (>1 km apart) = a chain or brand
NBOOT = 2000
SEED = 1974

# OpenFreeMap poi classes that are not businesses, clubs or venues (left out of the denominator)
NONBUS = {"bus", "railway", "parking", "bicycle_parking", "motorcycle_parking", "gate", "bollard", "lift_gate", "waste_basket",
          "telephone", "post", "atm", "toilets", "information", "entrance", "drinking_water", "bench", "shelter", "fuel",
          "charging_station", "car_sharing", "bicycle_rental", "ferry_terminal", "aerialway", "garden", "park", "brownfield",
          "grave_yard", "cemetery", "playground", "pitch", "swimming", "water_park", "border_control", "harbor", "survey_point",
          "town_hall", "police", "fire_station", "hospital", "prison", "place_of_worship", "school", "college", "library",
          "taxi", "recycling", "vending_machine", "airport", "aerodrome", "tram"}

# modern (ceremonial) county of each 2023 district in and around the study region
CER = {
    "Lancashire": ["Burnley", "Chorley", "Fylde", "Hyndburn", "Lancaster", "Pendle", "Preston", "Ribble Valley", "Rossendale",
                   "South Ribble", "West Lancashire", "Wyre", "Blackburn with Darwen", "Blackpool"],
    "Greater Manchester": ["Bolton", "Bury", "Manchester", "Oldham", "Rochdale", "Salford", "Stockport", "Tameside", "Trafford", "Wigan"],
    "Merseyside": ["Knowsley", "Liverpool", "Sefton", "St. Helens", "Wirral"],
    "Cumbria": ["Cumberland", "Westmorland and Furness"],
    "Cheshire": ["Cheshire East", "Cheshire West and Chester", "Halton", "Warrington"],
    "North Yorkshire": ["North Yorkshire", "York", "Middlesbrough", "Redcar and Cleveland"],
    "West Yorkshire": ["Bradford", "Calderdale", "Kirklees", "Leeds", "Wakefield"],
    "South Yorkshire": ["Barnsley", "Doncaster", "Rotherham", "Sheffield"],
    "East Riding of Yorkshire": ["East Riding of Yorkshire", "Kingston upon Hull, City of"],
    "Durham": ["County Durham", "Darlington", "Hartlepool"],
    "Derbyshire": ["High Peak", "Derbyshire Dales", "North East Derbyshire", "Chesterfield", "Bolsover", "Amber Valley",
                   "Erewash", "South Derbyshire", "Derby"],
    "Lincolnshire": ["North Lincolnshire", "North East Lincolnshire", "West Lindsey"],
    "Nottinghamshire": ["Bassetlaw"],
}
LAD2CER = {l: c for c, ls in CER.items() for l in ls}
SPLIT_LAD = {"Stockton-on-Tees"}   # split by the Tees between ceremonial Durham and North Yorkshire: modern = historic
YORKS_CER = {"North Yorkshire", "West Yorkshire", "South Yorkshire", "East Riding of Yorkshire"}
REGION_CER = {"Lancashire", "Greater Manchester", "Merseyside", "Cumbria", "Cheshire", "North Yorkshire", "West Yorkshire",
              "South Yorkshire", "East Riding of Yorkshire", "Durham"}

# zones: (historic county, modern group) -> code and label
def mod_group(cer):
    if cer in YORKS_CER: return "Yorkshire"
    return cer

ZONES = {
    ("Yorkshire", "Yorkshire"): ("YY", "Historic Yorkshire, still in a Yorkshire county"),
    ("Yorkshire", "Lancashire"): ("T_YL", "Bowland and West Craven: Yorkshire to Lancashire in 1974"),
    ("Yorkshire", "Greater Manchester"): ("T_YG", "Saddleworth: Yorkshire to Greater Manchester"),
    ("Yorkshire", "Cumbria"): ("T_YC", "Sedbergh and Dent: Yorkshire to Cumbria"),
    ("Yorkshire", "Durham"): ("T_YD", "South Teesdale: Yorkshire to Durham"),
    ("Lancashire", "Lancashire"): ("LL", "Historic Lancashire, still in Lancashire"),
    ("Lancashire", "Greater Manchester"): ("L_GM", "Lancashire to Greater Manchester"),
    ("Lancashire", "Merseyside"): ("L_MS", "Lancashire to Merseyside"),
    ("Lancashire", "Cumbria"): ("L_CU", "Furness and Cartmel: Lancashire to Cumbria"),
    ("Lancashire", "Cheshire"): ("L_CH", "Warrington and Widnes: Lancashire to Cheshire"),
    ("Lancashire", "Yorkshire"): ("L_YO", "Walsden and Todmorden fringe: Lancashire to Yorkshire before 1974"),
    ("Cheshire", "Greater Manchester"): ("C_GM", "Historic Cheshire in Greater Manchester"),
    ("Cheshire", "Merseyside"): ("C_MS", "Historic Cheshire in Merseyside (Wirral)"),
    ("Cheshire", "Cheshire"): ("CC", "Historic Cheshire, still in Cheshire"),
    ("Westmorland", "Cumbria"): ("W_CU", "Historic Westmorland, in Cumbria"),
    ("Cumberland", "Cumbria"): ("U_CU", "Historic Cumberland, in Cumbria"),
    ("Durham", "Durham"): ("DD", "Historic Durham, still in Durham"),
}

COUNTY_RE = {"L": re.compile(r"\b(lancashire|lancs|lancastrian)\b", re.I),
             "Y": re.compile(r"\b(yorkshire|yorks)\b", re.I)}
ROSE_RE = {"L": re.compile(r"\bred\s+rose\b", re.I), "Y": re.compile(r"\bwhite\s+rose\b", re.I)}
STREET_RE = re.compile(r"\b(lancashire|lancs|yorkshire|yorks)\s+(street|st|road|rd|lane|terrace|avenue|close|drive|way|row|"
                       r"square|grove|crescent|gardens|walk|place|hill|bridge|bank|fold|brow|mount)\b", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\b(the|ltd|limited|plc)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    raise ValueError(f)
