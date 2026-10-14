# Data policy & collection plan

## Principles
Lawful public or user-authorised data only · record licence + attribution per source · immutable raw snapshots (hashed) · synthetic and real never mixed · minimise personal data (redact before indexing) · no bulk scraping, respect rate limits/terms.

## Rule (set by product owner 2026-10-14)
**Only openly licensed, free data is collected.** No licence stated = not collected. Share-alike (ODbL, CC BY-SA) obligations are tracked per file in `data/raw/MANIFEST.json`.

## Collected (all in `data/raw/`, gitignored; reproducible via `scripts/`)
| Source | Licence | Size | Use |
|---|---|---|---|
| OSM Geofabrik Western Zone pbf | ODbL 1.0 | 221 MB | → `data/processed/osm/` roads (11,671), waterways (1,179), named places (981) for map, drainage context, place-matching gazetteer |
| DataMeet BMC ward boundaries | CC BY-SA 2.5 IN | 1 MB | 24 ward polygons |
| OpenCity Mumbai Census 2011 | Public Domain | 67 KB | ward population (exposure denominator; joined → `mumbai_wards.geojson`) |
| Open-Meteo archive, 3 Mumbai cells, 2018–2026 | CC BY 4.0 | 267 KB | daily rainfall context |

## Deliberately NOT collected
| Source | Why |
|---|---|
| MCGM Disaster Management Plan PDF | No licence statement; 704 MB. Revisit if licence confirmed |
| IMD public API | Reference page states no licence/terms. Revisit after reading IMD's data policy |
| Praja Foundation reports | Copyrighted NGO publication |
| DataMeet slum-cluster layer | Same licence but sensitive and derived from a third-party PDF; not needed for MVP |
| NASA POWER | Licence not stated on the docs pages I could read (a search snippet said CC BY 4.0; unconfirmed) |
| NASA IMERG | Needs a free Earthdata account — you create it, we don't |
| data.gov.in | Blocks automation (403); no BMC complaint dataset found. Manual search by you |

**Reality check:** no open record-level Mumbai complaint dataset exists that I could find. Observations will stay synthetic until a partner export arrives (imported through the licence-declaring upload path).

## Source status
`candidate → verified → (research-only | blocked | disabled)`. "Verified" = exact resource opened, contents + licence inspected, sample parsed, limits recorded (Appendix A fields).

## Retention
Raw files kept in `data/raw/` (gitignored); quarantined rows stored redacted; configurable retention before any real pilot.
