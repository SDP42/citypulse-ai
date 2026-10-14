# Source register (starting matrix — blueprint 131 / App. A)

All entries are **candidate** until the exact resource is opened, sampled, and its licence recorded. Nothing here is a confirmed integration. Verification date: _pending_ (blueprint research cut-off 2026-10-14).

| source_id | Purpose | URL (portal-level, to be narrowed) | Status | Notes |
|---|---|---|---|---|
| `synthetic-fixture` | Offline demo/tests | local | verified (ours) | Always labelled SYNTHETIC; never mixed with real |
| `manual-csv-geojson` | User/partner import | local upload | verified (ours) | Formula-injection-safe; size-limited |
| `ogd-india` | Dataset discovery | https://www.data.gov.in/ | candidate | Per-resource licence (GODL-India etc.) |
| `smartcities-portal` | Candidate catalogue | https://smartcities.data.gov.in/cities | candidate | Does not imply Mumbai coverage |
| `imd-api` | Weather/rainfall/warnings context | https://api.imd.gov.in/public/api_reference.html | candidate | District-level; missing ≠ clear |
| `mcgm-dmp` | Waterlogging-prone hazard context | https://dm.mcgm.gov.in/ (DMP PDF) | candidate | Manual/map-derived; approximate |
| `nasa-imerg` | Regional rainfall (~0.1°) | https://gpm.nasa.gov/data/directory | candidate | Not street-level truth |
| `osm-extract` | Base geography / PMTiles | https://download.geofabrik.de/ | candidate | ODbL attribution; no bulk tile scraping |
| `copernicus` | Optional remote sensing | https://www.copernicus.eu/ | research-only | Post-MVP |
| `open311-pattern` | Schema shape only | https://www.open311.org/api/ | research-only | No assumed endpoint; no auto-submission |

Status vocabulary: `candidate | verified | research-only | blocked | disabled`. "Verified" = exact resource accessed, contents + licence inspected, sample parsed, limits recorded.
