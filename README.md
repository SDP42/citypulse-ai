# CityPulse AI

**A local-first civic evidence workbench.** It turns scattered city reports into patterns you can defend: every number traces back to the source rows, the import batch and the data licence — and the interface is loud about what it does *not* know.

> ⚠️ An analytical tool — **not** an emergency system, **not** official civic guidance, and not a replacement for municipal complaint channels. A report is not a confirmed incident; a hotspot is a statistic, not a verdict.

## What works today
| | |
|---|---|
| **Import** | CSV or GeoJSON points, with preview, column mapping, per-row validation, quarantine (nothing silently fixed), PII redaction, idempotent re-import |
| **Boundaries** | Bring your own ward/zone polygons: QA report (validity, names, CRS, overlaps), whole-file rejection, versioned activation |
| **Analytics** | Report summary and trends (Asia/Kolkata days), per-area counts, per-10k rates only when a real denominator exists |
| **Provenance** | Click any number → metric definition → run → import batch → source & licence → the exact rows; verified live |
| **Honesty by design** | Permanent data-mode badge (synthetic vs real, never mixed), "no data" ≠ "no problem", gap days labelled "no reports recorded", formula-safe CSV export |
| **Offline** | Core path runs with the network disabled; no paid APIs, no model required |

Not built yet: map view, repeat-location (recurrence) analysis, document Q&A, analyst agent, forecasting. See [docs/PHASES.md](docs/PHASES.md).

## Data
The app ships with **synthetic demo data** (fictional zones; deterministic generator in `scripts/make_fixtures.py`). Open-licensed context data (Mumbai wards, Census 2011 population, OpenStreetMap roads/drains, rainfall) can be fetched into `data/raw/` — licences and obligations are in [NOTICE.md](NOTICE.md). There is **no open record-level Mumbai complaint dataset**; real observations must come from a partner or NGO export, imported with a declared licence.

## Quick start
Requires Python 3.12 and Node 20+.

```bash
make setup      # backend venv + web deps
make fixtures   # generate synthetic data
make dev        # API :8000 + web :5173   (or run `make api` and `make web` in two terminals)
make test       # pytest + vitest
```
Open http://localhost:5173, go to **Import**, and load `data/fixtures/synthetic_reports.csv` — you'll see 1,405 rows stored, 96 quarantined (with reasons) and 49 duplicates skipped. Then open **Overview** and click a number.

## Stack
Python 3.12 · FastAPI · SQLite (WAL) · shapely/pyproj/H3 — Vite · React · TypeScript · Tailwind · deck.gl/MapLibre (planned). Rationale: [ADR-0001](docs/decisions/ADR-0001-stack.md).

```
api/       backend (modular monolith)      web/      frontend
data/      fixtures committed; raw/db ignored   scripts/  fixtures, OSM clip, wards build, manifest
docs/      product, architecture, API, phases, workflow, security, data policy
```

## Docs
[PRODUCT](docs/PRODUCT.md) · [ARCHITECTURE](docs/ARCHITECTURE.md) · [API](docs/API.md) · [PHASES & sub-phases](docs/PHASES.md) · [WORKFLOW](docs/WORKFLOW.md) · [WORKDONE](docs/WORKDONE.md) · [DESIGN](docs/DESIGN.md) · [TESTING](docs/TESTING.md) · [SECURITY](docs/SECURITY.md) · [DATA_POLICY](docs/DATA_POLICY.md) · [LEARNING](docs/LEARNING.md) · [source register](docs/data-source-register.md)

## License
Code: [MIT](LICENSE). Data: see [NOTICE.md](NOTICE.md) — each dataset keeps its own licence.
