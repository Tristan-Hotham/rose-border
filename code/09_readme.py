"""Step 9: README.md, LICENSE, reddit/post.md and release/paper/cover_note.md, filled from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
H2 = R["H2"]; SH = R["H1"]["shares"]; X = R["x"]; M2 = R["M2"]
ci = lambda r, a="rr", lo="rr_lo", hi="rr_hi": f"{r[a]:.2f} (95% CI {r[lo]:.2f} to {r[hi]:.2f})"
readme = f"""# Does the 1974 border still show?

Lancashire and Yorkshire in business names. Every OpenStreetMap feature in and around historic Lancashire and Yorkshire whose name says Lancashire, Lancs, Yorkshire or Yorks, cleaned and read by eye, mapped against the historic county border, the county borders since the 1974 reorganisation and the areas that moved, with named business points of interest from OpenFreeMap as a denominator. The analysis follows a plan written before any share or rate was computed by area (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24104647}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/rose-border/}}
Code and data: {REPO}

## Headline results

- Main sample: {R['flow']['main_n']} private businesses, clubs and venues with a county word ({R['flow']['main_L']} Lancashire, {R['flow']['main_Y']} Yorkshire), after dropping roads, transport, administrative, street-derived and product names and setting aside chain branches and public bodies.
- Where the historic border did not move it is a sharp naming line: within 25 km, {SH['YY']['nY']} of {SH['YY']['n']} county names on the Yorkshire side say Yorkshire ({X['YY_s_pc']:.1f}%) and {SH['LL']['nY']} of {SH['LL']['n']} on the Lancashire side ({X['LL_s_pc']:.1f}%). Jump across the line within 10 km: {X['jump']:.0f} points (95% CI {X['jump_lo']:.0f} to {X['jump_hi']:.0f}); false lines 10 km inside each county: {X['fl']:.0f} and {X['fy']:.0f} points (both intervals include 0).
- Primary test (Bowland and West Craven, Yorkshire to Lancashire in 1974): not estimable. No county-named private feature there, nor in Saddleworth, Sedbergh and Dent or south Teesdale; the four areas have {X['TY_poi']} named business POIs, so only about {X['TY_exp']:.1f} Yorkshire names would be expected at Yorkshire's rate.
- Secondary comparisons, Lancashire name outside today's Lancashire: {H2['L_L_GM']['rate']:.2f} per 1,000 business POIs in the old Lancashire part of Greater Manchester vs {H2['L_LL']['rate']:.2f} in Lancashire, rate ratio {ci(H2['L_L_GM'])}; Merseyside {ci(H2['L_L_MS'])}. The old Cheshire parts of the same counties have none ({R['X_metro']['nL']} vs 0 pooled, {R['X_metro']['expected_C_at_L_rate']:.1f} expected; exploratory). Furness and Cartmel: 0 found, {H2['L_L_CU']['expected_at_ref']:.1f} expected; Warrington and Widnes: 0 found, {H2['L_L_CH']['expected_at_ref']:.1f} expected.
- Pooled Poisson model, Lancashire name: historic county rate ratio {M2['L']['H']['rr']:.1f} (95% CI {M2['L']['H']['lo']:.1f} to {M2['L']['H']['hi']:.1f}), county today {M2['L']['M']['rr']:.1f} ({M2['L']['M']['lo']:.1f} to {M2['L']['M']['hi']:.1f}); both above 1 in every check. The Yorkshire split is weakly identified and reverses when chains are included.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; every county-named feature, the two borders, the moved areas, toggles by type, layers, search, full screen, popups with OSM links. |
| `header.png` | Social card, 1200 x 630. |
| `data/features.csv` | Every name with a county or rose word: classification, drop reason, duplicate and chain flags, type, historic and modern county, zone, distances to both lines. ODbL. |
| `data/zones.csv`, `data/boundaries.geojson` | Zone areas (historic x modern county); simplified borders, lines and moved areas for the map. |
| `data/poi_units.csv`, `data/poi_cells.csv.gz` | Named OpenFreeMap points of interest aggregated by zone, 5 km cell and distance band, and by 1 km cell. ODbL. |
| `data/zone_rates.csv`, `data/profiles.csv`, `data/robustness.csv`, `data/results.json` | Rates and rate ratios; distance profiles; every planned check; every number quoted anywhere. |
| `data/ofm_rose_check.csv`, `data/site.json` | County-word names found in the tiles (a cross-check); page data. |
| `code/` | Scripts in order, templates, `overrides.csv` (hand decisions), `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | Working notes and the analysis plan, written before outcomes were computed. |

## How to rerun

Needs Python 3 with pandas, numpy, geopandas, shapely, pyproj, statsmodels, scipy, mapbox-vector-tile, matplotlib, Pillow; xelatex; node with Playwright for QA. Raw inputs are listed in `code/common.py` (the historic county shapefile is cloned from GitHub Beyond-Notability/bn_notes, folder shp/hcp_uk_counties).

```
python3 code/01_boundaries.py    # zones and lines
python3 code/02_features.py      # names, classification, hand decisions
python3 code/03_poi_tiles.py     # OpenFreeMap tiles (about 16,500, 30 minutes)
python3 code/03b_poi_units.py    # denominator by zone and cell
python3 code/04_models.py        # every planned estimate, results.json
python3 code/05_figures.py       # figures and header
python3 code/06_build_site.py    # index.html and site.json
python3 code/07_paper.py         # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py
python3 code/09_readme.py        # README, LICENSE, Reddit post, cover note
python3 code/08_release.py       # blog post, Zenodo files
```

## Sources and licences

- Names: OpenStreetMap contributors, queried through QLever (osm-planet), 2026; points of interest from OpenFreeMap vector tiles (OpenMapTiles schema). Open Database Licence (ODbL).
- Historic counties: this project made use of data provided by the Historic County Borders Project (https://www.county-borders.co.uk), UK Definition A.
- Counties since 1974: ONS Local Authority Districts, December 2023 (Open Government Licence v3.0; contains OS data, Crown copyright and database right). Natural Earth (public domain) in the static figures. Place search: Wikidata (CC0).
- Text and figures CC BY 4.0; code MIT; derived data containing OpenStreetMap names or points (features.csv, poi files, site.json, ofm_rose_check.csv) ODbL.

## Citation

Hotham, T. (2026) Does the 1974 border still show? Historic and modern county names in the business landscape of Lancashire and Yorkshire. Zenodo. {{https://doi.org/10.5281/zenodo.24104647}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/,
except files that contain OpenStreetMap names or points (data/features.csv, data/poi_units.csv, data/poi_cells.csv.gz, data/site.json,
data/ofm_rose_check.csv), which are made available under the Open Database Licence (ODbL) 1.0, https://opendatacommons.org/licenses/odbl/1-0/,
(c) OpenStreetMap contributors. Historic county borders: Historic County Borders Project. District boundaries: Open Government Licence v3.0.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""**Title:** [OC] Cross the old Lancashire/Yorkshire border and business names flip: {X['YY_s_pc']:.0f}% say Yorkshire on one side, {X['LL_s_pc']:.0f}% on the other. 50 years after 1974, old Lancashire bits of Greater Manchester still use the name at ~{X['rrGM_pc']:.0f}% of Lancashire's rate.

**Body:**

I mapped every shop, club and venue in OpenStreetMap whose name says Lancashire or Yorkshire ({R['flow']['main_n']} after removing roads, bus stops, chains and public bodies) against the historic county border and the borders redrawn in 1974.

The main test I wrote down in advance could not be run: Bowland, Barnoldswick, Earby and Saddleworth (which left Yorkshire in 1974) have {X['TY_poi']} named businesses on the map between them with Sedbergh, Dent and south Teesdale, and not one private business named after either county. About {X['TY_exp']:.0f} Yorkshire names would be expected at Yorkshire's rate, so the empty map is not a verdict either way. What the map does show:

- Within 25 km of the old line: {SH['YY']['nY']} of {SH['YY']['n']} county names on the Yorkshire side say Yorkshire; {SH['LL']['nY']} of {SH['LL']['n']} on the Lancashire side.
- Old Lancashire part of Greater Manchester: {H2['L_L_GM']['rate']:.1f} Lancashire names per 1,000 businesses, vs {H2['L_LL']['rate']:.1f} in today's Lancashire (rate ratio {H2['L_L_GM']['rr']:.2f}, 95% CI {H2['L_L_GM']['rr_lo']:.2f} to {H2['L_L_GM']['rr_hi']:.2f}); old Lancashire part of Merseyside {H2['L_L_MS']['rate']:.1f}. The old Cheshire parts of Greater Manchester and Merseyside: zero found.
- Furness (now Cumbria) and Warrington/Widnes (now Cheshire): zero Lancashire names found.

Interactive map with every name and the moved areas: {PAGE}

**Source comment:**

Data: OpenStreetMap contributors (ODbL) via QLever and OpenFreeMap tiles; historic counties from the Historic County Borders Project; districts from ONS (OGL v3.0). Method: names classified and read by eye, rates per 1,000 named businesses, exact Poisson intervals, analysis pre-specified in a written plan. Descriptive only: it cannot say why names differ. Tools: Python (geopandas, statsmodels, matplotlib), MapLibre. Paper and code: {REPO}
"""
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
txt = open(os.path.join(REL, "paper", "Hotham_Rose_Border.tex"), encoding="utf-8").read()
cover = f"""# Cover note: Does the 1974 Border Still Show?

## Suggested journals (no mandatory author charges)

The manuscript is about 7,200 words before the references (about 8,400 with references and appendix), with 6 figures and 7 tables. All three venues below were checked online in 2026; none charges the author a mandatory fee.

1. **Names: A Journal of Onomastics** (American Name Society; University of Pittsburgh library publishing). APC: none; the journal states that it charges no fees for submission, processing or online production, and all articles are open access under CC BY (a fee may apply only for colour in the print version). Word limit: the manuscript guidelines set no overall article length, but the abstract may not exceed 200 words (this paper's is about 245, so it must be cut), the title 50 words, the contributor note 150 words and endnotes 400 words. Fit: very good; enterprise names as markers of vernacular regions have appeared in the journal (Sublett 2021 on "Corn Belt" enterprise names).
2. **Area** (Royal Geographical Society with IBG; Wiley). APC: none mandatory; a hybrid subscription journal in which open access is optional and paid. Word limit: not confirmed online (the author guidelines could not be retrieved); check before submitting. Area publishes shorter articles than most geography journals, so expect to cut the paper and move Tables 6 and 7 and the robustness detail to supplementary material.
3. **Northern History** (School of History, University of Leeds; Taylor and Francis). APC: none mandatory; a subscription journal in which authors can choose paid gold open access. Word limit: not confirmed online (the instructions for authors could not be retrieved); check before submitting. Fit: good if framed for historians of northern England, leading with the 1974 reorganisation and county identity and keeping the statistical detail in an appendix.

## Summary for a cover letter (150 words)

This article measures whether the 1974 reorganisation of English local government shows in how businesses name themselves. Using every OpenStreetMap feature in and around Lancashire and Yorkshire whose name contains either county, classified by fixed rules and read by eye, and named businesses from OpenFreeMap as a denominator, it compares areas that stayed in their county, areas that moved, and neighbours that were never in the county, following a plan written before outcomes were computed. Where the historic border still divides counties it divides names sharply. The pre-specified primary test, in Bowland and West Craven, could not be estimated: the area has no county-named private business on the map and too few businesses for that absence to be informative, and the paper reports this plainly. In secondary comparisons, the Lancashire name persists in historic Lancashire now in Greater Manchester and Merseyside at about a quarter to a fifth of its rate in Lancashire, with none found in the historic Cheshire parts of the same counties. Data and code are openly released.
"""
open(os.path.join(REL, "paper", "cover_note.md"), "w", encoding="utf-8").write(cover)
for t_ in (readme, post, cover):
    for bad in ("—", "–", "DSIT", "DCMS", "pre-registered"):
        assert bad not in t_, bad
print("README, LICENSE, post.md, cover_note.md written")
