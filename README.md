# Does the 1974 border still show?

Lancashire and Yorkshire in business names. Every OpenStreetMap feature in and around historic Lancashire and Yorkshire whose name says Lancashire, Lancs, Yorkshire or Yorks, cleaned and read by eye, mapped against the historic county border, the county borders since the 1974 reorganisation and the areas that moved, with named business points of interest from OpenFreeMap as a denominator. The analysis follows a plan written before any share or rate was computed by area (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/rose-border/
Paper: https://doi.org/10.5281/zenodo.24104647
Blog post: https://blog.tristanhotham.com/2026/10/31/rose-border/
Code and data: https://github.com/Tristan-Hotham/rose-border

## Headline results

- Main sample: 389 private businesses, clubs and venues with a county word (77 Lancashire, 312 Yorkshire), after dropping roads, transport, administrative, street-derived and product names and setting aside chain branches and public bodies.
- Where the historic border did not move it is a sharp naming line: within 25 km, 59 of 60 county names on the Yorkshire side say Yorkshire (98.3%) and 1 of 36 on the Lancashire side (2.8%). Jump across the line within 10 km: 86 points (95% CI 50 to 100); false lines 10 km inside each county: -8 and 14 points (both intervals include 0).
- Primary test (Bowland and West Craven, Yorkshire to Lancashire in 1974): not estimable. No county-named private feature there, nor in Saddleworth, Sedbergh and Dent or south Teesdale; the four areas have 534 named business POIs, so only about 3.7 Yorkshire names would be expected at Yorkshire's rate.
- Secondary comparisons, Lancashire name outside today's Lancashire: 1.11 per 1,000 business POIs in the old Lancashire part of Greater Manchester vs 4.09 in Lancashire, rate ratio 0.27 (95% CI 0.15 to 0.48); Merseyside 0.21 (95% CI 0.07 to 0.50). The old Cheshire parts of the same counties have none (23 vs 0 pooled, 5.0 expected; exploratory). Furness and Cartmel: 0 found, 5.2 expected; Warrington and Widnes: 0 found, 6.1 expected.
- Pooled Poisson model, Lancashire name: historic county rate ratio 15.8 (95% CI 5.6 to 44.6), county today 4.5 (2.1 to 9.3); both above 1 in every check. The Yorkshire split is weakly identified and reverses when chains are included.

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

Hotham, T. (2026) Does the 1974 border still show? Historic and modern county names in the business landscape of Lancashire and Yorkshire. Zenodo. https://doi.org/10.5281/zenodo.24104647

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
