# rose-border: working notes

Brief: /home/claude/work/new13/BRIEFS.md section C (+ new12/new11/new10/new9/new8 shared rules, house brief
/home/claude/newdata/BRIEF.md, GIF brief /home/claude/gifs/BRIEF.md). Format refs: fame-half-life, byelection-attention.
Scratch: /home/claude/scratch/rose-border (delete at the end, by exact path).
Raw name file /home/claude/newdata/raw_new13/osm_names_rose_kingdom.tsv is shared with lost-kingdoms: read only.

## Data construction done before writing the plan (no outcome looked at by zone or distance)

- Name file: 7,500 rows (5,778 ways, 1,482 nodes, 240 relations), sorted by URI and ending at way/999..., so not cut off
  by a row limit. 2,742 rows contain a Lancashire/Yorkshire/rose word: 903 are highways (roads, bus stops), and many
  untagged rows are railway lines, canals and named buildings. The file has only the shop, amenity, office, craft,
  leisure and highway keys, so tourism, club and building-only features appear untagged.
- Historic counties: Historic County Borders Project, UK Definition A (simplified), from GitHub
  Beyond-Notability/bn_notes shp/hcp_uk_counties (README: free for any use, acknowledgement requested).
- Modern counties: ceremonial counties built from ONS December 2023 districts (lad23_bgc); Stockton-on-Tees, which is split
  by the Tees, takes the historic county (the Tees is both lines). counties_uk.geojson was too coarse (about 230 vertices
  per county) for distances of a few km.
- Zones (historic x modern; code/01_boundaries.py, data/zones.csv): pieces under 5 km2 are boundary slivers from the two
  sources' different line work; points in slivers where historic and modern disagree are flagged and left out.
  Areas moved in 1974 (km2): Bowland and West Craven, Yorkshire to Lancashire (T_YL) 385; Saddleworth, Yorkshire to Greater
  Manchester (T_YG) 76; Sedbergh and Dent, Yorkshire to Cumbria (T_YC) 213; south Teesdale, Yorkshire to Durham (T_YD) 392;
  Furness and Cartmel, Lancashire to Cumbria (L_CU) 621; Lancashire to Greater Manchester (L_GM) 929; to Merseyside (L_MS)
  489; Warrington and Widnes to Cheshire (L_CH) 147. Also historic Cheshire in Greater Manchester (C_GM, 254) and in
  Merseyside (C_MS, Wirral, 157); and a 29 km2 Lancashire piece in West Yorkshire (Walsden/Todmorden fringe, moved before
  1974, L_YO).
- Lines: historic Lancashire/Yorkshire border 181 km; modern border of the Yorkshire counties with Lancashire, Greater
  Manchester and Cumbria 196 km.
- Denominator (03_poi_tiles.py): OpenFreeMap zoom-14 vector tiles (16,509 tiles over the region), named POIs per 1 km cell,
  business/venue classes only (transport, parking, street furniture, public services left out).

## Analysis plan (written before any share or rate was computed by zone or distance)

Question: near the lines that moved in 1974, do businesses, clubs and societies name themselves after the historic county
or the post-1974 one?

### Features (pre-set rules, code/02_features.py)
- County word: Lancashire if the name matches \b(lancashire|lancs|lancastrian)\b; Yorkshire if \b(yorkshire|yorks)\b.
  Both words: excluded (counted). "Red Rose"/"White Rose" without a county word: rose names, used only in a sensitivity
  check (they are also generic pub and flower names).
- Point: the node, or the representative point of the way/relation geometry.
- Dropped: highway rows (roads, bus stops); untagged line features (railways, canals, rail lines, footpaths); names where the
  county word is part of a street name ("Yorkshire Street Dental") or a product or breed (Yorkshire pudding, Yorkshire
  terrier, Lancashire hotpot, Lancashire cheese).
- Type: "private" (businesses, clubs, societies, venues: shop, amenity other than public services, office, craft, leisure,
  and untagged points/polygons that are not public); "public" (bodies named for an administrative area: police, councils,
  NHS, ambulance, fire and rescue, probation, courts, schools, colleges, universities, public transport executives, water and
  power utilities, armed forces and cadets); "chain" (the same normalised name at 3 or more places more than 1 km apart, e.g. a
  building society: branch names say where the firm began, not where the branch is).
- Duplicates: the same normalised name within 300 m is one feature (node and building of the same pub).
- Every feature within 40 km of the historic Lancashire/Yorkshire line, and every feature in a moved zone, is read by eye for
  its type, with decisions in code/overrides.csv; the reading is done on a name list without zone or distance columns.

### Hypotheses, measures and models
H1 (primary). In Bowland and West Craven (T_YL: historic Yorkshire, Lancashire since 1974) the share of county-named private
features that say Yorkshire (rather than Lancashire), s_T, lies between the share in historic Yorkshire that stayed in
Yorkshire (s_Y) and the share in historic Lancashire that stayed in Lancashire (s_L), both within 25 km of the historic line.
Persistence index P = (s_T - s_L) / (s_Y - s_L): 1 = named like Yorkshire (historic county persists), 0 = named like
Lancashire (the new county has taken over). 95% CI by cluster bootstrap (2,000 draws, resampling 5 km grid cells within
each zone). Decision rule: if the CI of P lies above 0.5, the historic county dominates; below 0.5, the modern county
dominates; if it spans 0.5, the result is mixed. Tests that s_T > s_L and s_T < s_Y are reported separately (logit with
zone dummies, errors clustered by 5 km cell).
M1b: logit of Yorkshire (1) vs Lancashire (0) for private features in historic Lancashire or Yorkshire within 25 km of the
historic line or in T_YL, on historic Yorkshire, T_YL (= historic Yorkshire now in Lancashire) and signed distance to the
historic line (separate slopes each side); errors clustered by 5 km cell.

H2 (secondary, rates). For each county name N (Lancashire, Yorkshire), the number of private features named for N per
1,000 named business POIs (OpenFreeMap) in each zone, as a Poisson rate ratio against the stayed zone of that historic
county (LL for Lancashire, YY for Yorkshire within 25 km of the line). Moved-out zones: Lancashire name in L_CU (Furness,
Cartmel), L_GM, L_MS, L_CH; Yorkshire name in T_YL, T_YG, T_YC, T_YD. Benchmarks with no historic claim: Lancashire name in
historic Cheshire parts of Greater Manchester and Merseyside (C_GM, C_MS), in historic Westmorland and Cumberland; Yorkshire
name in stayed Lancashire within 25 km (LL band). Persistence predicts moved zones near their stayed zone (rate ratio near
1); full replacement predicts them near the benchmark. M2 (pooled): Poisson regression on zone pieces x 5 km cells, count of
N-named private features with offset log(business POIs), indicators historic-N (H) and modern-N (M), errors clustered by
20 km block; exp(b_H) and exp(b_M) with 95% CIs. Modern-N for Lancashire = ceremonial Lancashire; for Yorkshire = the four
Yorkshire ceremonial counties. Cells with no business POI are dropped.

H3 (validation). Public bodies named for a county follow the modern line: in moved zones, public names should match the
modern county (or neither), not the historic one. Report counts.

### Checks (all pre-specified)
- Placebo P1 (false lines): the jump in the Yorkshire share at the historic line where it did not move, compared with the
  same jump at false lines 10 km inside Lancashire and 10 km inside Yorkshire (local logit within 10 km either side of each
  line); expect a large jump at the real line and none at the false ones.
- Placebo P2: within Greater Manchester and Merseyside (one modern county each), the Lancashire rate in the historic
  Lancashire part vs the historic Cheshire part. A difference means the historic line shows where the modern one is the
  same; reported alongside H2, labelled as a within-county comparison.
- Alternative specifications: bandwidths 10, 15, 40 km; including chains (one per chain name per zone); including public
  bodies; adding rose names; no deduplication; untagged features dropped; denominator all named POIs instead of business
  POIs; clustering by 10 km cell.
- Leave-one-out: T_YL split into its Ribble Valley part (Bowland) and Pendle part (Barnoldswick, Earby); each alone.
- Profiles (figures): Yorkshire share in 5 km bins of signed distance from the historic line and from the modern line,
  with Wilson intervals.
- What would count against persistence: P CI below 0.5; Yorkshire rate in T_YL not above the stayed-Lancashire band;
  Lancashire rate in Furness not above Westmorland and Cumberland.

### Honest limits stated up front
OSM coverage varies by mapper; names are a snapshot (2026) with no founding dates, so names coined before 1974 cannot be
separated from later ones; a business may be named for its owner's origin, a product, or a market far away; counts in moved
zones are small, so intervals will be wide; the design is descriptive and makes no causal claim about the reform.
Companies House (registered names) was not reachable; names come from OSM only.

## Check against the coordinator's re-query (osm_names_full_v2.tsv, read only)

The coordinator re-ran the name query with no row limit (osm_names_full_v2.tsv, 5,835 data rows). Rows whose name has a
Lancashire, Lancs, Lancastrian, Yorkshire, Yorks, Red Rose or White Rose word: original file 2,693, v2 2,048.
Features in v2 missing from the original file (and so from this analysis): 0. So the counts are unchanged by the check:
before 2,693 rose-word rows, 917 kept features, main sample 389; after adding v2's missing features (none): the same.
The reverse is not true: 645 rose-word rows of the original file are absent from v2 (179 highways, 466 others), including
175 of the 389 main-sample features (e.g. Lancashire County Cricket Club, Lancashire Law, Little Yorkshire cafe). v2 therefore
looks narrower than the original (perhaps its UK containment or keyword filter), not more complete; the original file was
kept as the source. Its 7,500 rows end at the last URI in sort order (way/999...), which also argues against truncation.

## Results (first and only run of the plan; numbers from data/results.json)

- Main sample 389 private county-named features in zones (77 Lancashire, 312 Yorkshire); 72 hand decisions (plus 3 added
  after a final read of the moved-zone names: a duplicated golf club and a surname, both before any figure was published).
- Line where it did not move: within 25 km, 59/60 Yorkshire on the Yorkshire side (98.3%, Wilson 91.1 to 99.7), 1/36 on the
  Lancashire side (2.8%, 0.5 to 14.2). Jump within 10 km +86 points (bootstrap 50 to 100); false lines -8 and +14 (CIs
  include 0). M1b logit not estimable (separation); LPM +78 points [44, 111].
- H1 (primary): NOT ESTIMABLE. No county-named private feature in Bowland and West Craven (or Saddleworth, Sedbergh-Dent,
  south Teesdale). Only 534 named business POIs in the four areas; ~3.7 Yorkshire names expected at the YY-band rate.
- H2: Lancashire name per 1,000 business POIs: LL 4.09 (49); old Lancashire Greater Manchester 1.11 (17), RR 0.27 [0.15,
  0.48]; Merseyside 0.87 (6), RR 0.21 [0.07, 0.50]; Furness 0 (5.2 expected), Warrington-Widnes 0 (6.1 expected); historic
  Cheshire parts of GM and Merseyside 0. Exploratory pooled metro comparison: 23 vs 0, 5.0 expected, RR lower bound 1.26.
  Q (GM) 27% [13, 55]; Q (Merseyside) 21% [5, 51].
- M2: Lancashire name, historic RR 15.8 [5.6, 44.6], modern 4.5 [2.1, 9.3]; both > 1 in all 12 checks. Yorkshire name
  historic 4.7 [1.4, 16.3], modern 33.5 [9.8, 115]: weakly identified (all disagreeing units are zero), reverses with chains,
  not estimable with tagged features only.
- H3: too few public bodies in moved zones (3 non-chain) to evaluate.
- Cricket league affiliations: the cricket venue files have no league field, so they were not used.

## References: verification (WebSearch/WebFetch, 2026)
43 entries. Abstract or publisher description read: Becker et al. 2016, Dell 2010, Falck et al. 2012, Gao et al. 2017,
Giovannini 2016, Gulley 1990, Haklay 2010, Hollenstein & Purves 2010, Jones & MacLeod 2004, Kavaratzis 2004, Kavaratzis &
Ashworth 2005, Keele & Titiunik 2015, Leach et al. 2016, Liesch et al. 2015, Paasi 1986 (partial), Pike 2015 (book
description), Russell 2004 (publisher description), Sublett 2021, Terlouw 2016, Terlouw 2018, Zimmerbauer et al. 2017, DCLG
2013 press release, Hansard 1974 written answer, HCBP project page; Garwood 1936 (PDF seen). Metadata confirmed only (cited for
what titles state): Zelinsky 1980, Reed 1976, Shortridge 1985, Hale 1984, Ambinakudige 2009 (from published reference
lists), Paasi 2003, Zimmerbauer & Paasi 2013, Relph (not cited in the end), Wales 2006, Goodchild 2007, Wilson 1927,
Clopper & Pearson 1934 (search listing), Cameron & Miller 2015 (sibling study's verified list), Royal Commission 1969 and
Local Government Act 1972 (Wikipedia pages read). Not verified, dropped: Alderman & Beavers 1999, Barrington-Leigh &
Millard-Ball 2017, Sjöblom 2016. Gao et al. 2017 pages not confirmed (volume/issue and DOI only). Journal word limits could
not be checked (search budget exhausted, author pages unreachable); said so in cover_note.md.

## Deliverables
index.html + js/page.js (QA qa/*.png, 0 console errors at 1280 and 390 px); header.png; data/*; code/01..09 (+03b);
release/paper (PDF 18 pp, about 7,200 words before references, abstract about 246 words, cover_note.md); release/blog
(post.html, 5 figures, meta.json); release/zenodo; reddit collage + post.md + GIF (/home/claude/gifs/scripts/rose-border.py).

## Independent review (2026)
- Re-ran 01, 02 and 04 from a fresh clone of the historic county shapefile: zones, features, profiles, robustness, zone rates and results.json reproduce exactly (clone deleted afterwards).
- Text: every output now says plainly that the pre-specified primary test (Bowland and West Craven) could not be estimated, and labels the metropolitan comparisons as secondary (the pooled metro comparison as exploratory). Causal wording on M2 removed ("associated with"); unchecked superlatives and "for a thousand years" removed; false-line changes reported with sign and as indistinguishable from zero.
- References re-checked online: added pages/DOIs for Gao et al. 2017 (31(6), 1245 to 1271), Sublett 2021 (69(4), 1 to 12), Gulley 1990 (doi), Keele and Titiunik, Cameron and Miller; Terlouw 2018 issue number dropped (not confirmed). Hale 1984 and Shortridge 1985 dropped (claims could not be checked against an abstract); "276 metropolitan areas" (Zelinsky) and the "best known rivalry" claim removed; Leach et al. 2016 claim corrected to the abstract (partial support; proximity effect depends on contact). HCBP release date removed.
- Cover note: Names (no fees, CC BY, no overall length limit, abstract max 200 words); Area and Northern History hybrid with optional paid OA, word limits not retrievable online. Geography dropped (not checked).
- GIF re-rendered over the full sample extent so the end counts match results.json (77 Lancashire, 312 Yorkshire).
