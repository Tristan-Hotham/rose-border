**Title:** [OC] Cross the old Lancashire/Yorkshire border and business names flip: 98% say Yorkshire on one side, 3% on the other. 50 years after 1974, old Lancashire bits of Greater Manchester still use the name at ~27% of Lancashire's rate.

**Body:**

I mapped every shop, club and venue in OpenStreetMap whose name says Lancashire or Yorkshire (389 after removing roads, bus stops, chains and public bodies) against the historic county border and the borders redrawn in 1974.

The main test I wrote down in advance could not be run: Bowland, Barnoldswick, Earby and Saddleworth (which left Yorkshire in 1974) have 534 named businesses on the map between them with Sedbergh, Dent and south Teesdale, and not one private business named after either county. About 4 Yorkshire names would be expected at Yorkshire's rate, so the empty map is not a verdict either way. What the map does show:

- Within 25 km of the old line: 59 of 60 county names on the Yorkshire side say Yorkshire; 1 of 36 on the Lancashire side.
- Old Lancashire part of Greater Manchester: 1.1 Lancashire names per 1,000 businesses, vs 4.1 in today's Lancashire (rate ratio 0.27, 95% CI 0.15 to 0.48); old Lancashire part of Merseyside 0.9. The old Cheshire parts of Greater Manchester and Merseyside: zero found.
- Furness (now Cumbria) and Warrington/Widnes (now Cheshire): zero Lancashire names found.

Interactive map with every name and the moved areas: https://maps.tristanhotham.com/rose-border/

**Source comment:**

Data: OpenStreetMap contributors (ODbL) via QLever and OpenFreeMap tiles; historic counties from the Historic County Borders Project; districts from ONS (OGL v3.0). Method: names classified and read by eye, rates per 1,000 named businesses, exact Poisson intervals, analysis pre-specified in a written plan. Descriptive only: it cannot say why names differ. Tools: Python (geopandas, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/rose-border
