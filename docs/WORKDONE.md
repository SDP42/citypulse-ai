# Work done (append-only log)

Newest at the bottom. Each entry: date · batch · what changed · evidence · open issues.

---

## 2026-10-14 · Phase 0 — audit
- The project directory was empty. Toolchain: macOS arm64, Python 3.12.13, Node 22.20.0.
- Read the 152-page blueprint (key notes 001–050, 093–100, 123–133, appendices A–L).

## 2026-10-14 · Phase 1 — scaffold (batch 1)
- **Docs:** README, CLAUDE.md, PRODUCT, ARCHITECTURE, PHASES, WORKFLOW, WORKDONE, DESIGN, TESTING, SECURITY, DATA_POLICY, LEARNING, ADR-0001, source register.
- **Backend (`api/`):** FastAPI app, settings (offline-safe defaults), provenance/lineage models, error shape with correlation IDs, SQLite connection + migration runner, `001_core.sql` (sources, batches, areas, observations, quarantine, audit), `/health`, `/sources`, tests in `tests/unit/test_core.py`.
- **Frontend (`web/`):** Vite + React + TS + Tailwind shell, data-mode badge, Sources panel, tab nav. **Evidence:** `tsc -b` clean, `vite build` succeeded (183 kB JS).
- **Data:** `data/source_register.json` (9 sources, all `candidate`/`research-only` except our own); `scripts/make_fixtures.py` (seeded synthetic reports with injected defects + fictional zones).

## 2026-10-14 · Phase 2 — source verification (partial, read-only)
| Source | Finding | Status |
|---|---|---|
| IMD API reference | Endpoint families incl. `districtrainfall`, `districtwarning`, `current_wx`; JSON; no auth, licence, rate limit or refresh schedule stated | candidate |
| data.gov.in terms | Automated fetch → HTTP 403; must read manually | candidate |
| Geofabrik Western Zone | `western-zone-latest.osm.pbf` ≈ 210 MB, ODbL 1.0, data to 2026-10-13 | candidate (not downloaded) |
| BMC complaints | No record-level public dataset found; Praja Foundation PDF reports contain ward-wise tables (licence unknown) | research-only |
| MCGM DMP / IMERG / Smart Cities | Not yet opened | candidate |

**No external data files were downloaded.** Downloads await your approval (see open items).

## Verification (executed 2026-10-14)
- `pytest -q` in `api/` → **3 passed** (blank-DB migration + idempotency, register status vocabulary, `/health` + error shape). Uses real SQLite in memory; no network.
- `make fixtures` → wrote 1550 synthetic rows + 9 fictional zones to `data/fixtures/`.
- `tsc -b` + `vite build` clean.
- **Not yet tested:** web ↔ API in a browser (`make dev`), Vitest/Playwright (none written), any real-data path.
- Note: `pip install -e .` hung in this environment; deps were installed directly and pytest uses `pythonpath=["."]`. `make setup` now installs deps directly for the same reason.

## 2026-10-14 · Phase 2 — data collection (approved by user; open-licence only)
- **Downloaded & hashed** (`data/raw/MANIFEST.json`): OSM Western Zone pbf (221,215,934 B, ODbL), BMC wards GeoJSON (CC BY-SA 2.5 IN), Census 2011 ward CSVs ×3 (public domain), Open-Meteo rainfall ×3 cells (CC BY 4.0).
- **Derived:** `scripts/extract_osm_mumbai.py` → 11,671 roads, 1,179 waterways, 981 places (8 s). `scripts/build_wards.py` → 24 wards joined to population: total 12,442,373, 24/24 names matched, all geometries valid.
- **Sanity checks:** monsoon rainfall 1.3–2.8 m/yr (plausible); the 3 rainfall cells are near-identical → confirms rainfall is area context, not street evidence.
- **Not collected (and why):** MCGM DMP PDF (no licence, 704 MB), IMD API (no licence stated), Praja, slum clusters, NASA POWER/IMERG, data.gov.in. See `docs/DATA_POLICY.md`.
- **Register:** 12 sources; `osm-extract`, `datameet-bmc-wards`, `opencity-mumbai-census`, `openmeteo-archive` now `verified`; the rest remain `candidate`/`research-only`.
- Backend tests still 3 passed. No tests yet for the new scripts (NOT TESTED).

## 2026-10-14 · Phase 3 batch 1 — CSV importer (+ closing Phases 1 and 2)
**Why:** the blueprint's first dependable connector is manual file import; it also proves repeatable offline ingestion, which closes Phase 2.

**How it works:** `POST /imports/preview` (dry run, no writes) → `POST /imports` (single transaction). Parse (encoding/delimiter sniffing, limits) → column mapping (auto + user override; unrecognised headers are refused, never guessed) → per-row validation → area assignment (point-in-polygon, else area name, else unresolved) → dedupe (in-file, cross-file, conflicting IDs) → batch + observations + quarantine + audit event. Mode guard prevents mixing synthetic and real. Details: [API.md](API.md).

**Files:** `api/migrations/002_import.sql`; `api/citypulse/{core/csv_safety.py, core/errors.py (+422/409/413 shapes), db/{seed,deps}.py, geo/areas.py, ingest/{parse,normalise,pipeline}.py, api/routes/{imports,observations}.py, main.py}`; tests `tests/{unit/test_ingest_units.py, integration/test_importer.py, integration/test_offline_smoke.py, contract/test_api.py}`; web `src/features/{import/ImportPanel,incidents/IncidentsPanel}.tsx`, `src/lib/{api,format}.ts`, vitest setup + 2 test files; `docs/API.md`.

**Evidence (all executed 2026-10-14):**
- `make test` → backend **43 passed**, web **5 passed** (2 files); `tsc -b` clean; `vite build` OK.
- Hand-calculated 12-row CSV: exactly 5 stored / 6 quarantined / 1 duplicate, with the exact error-code counts asserted.
- Fixture file (1,550 rows): 1,405 stored · 96 quarantined · 49 duplicates (sum = 1,550). Per-code counts equal independent counts taken straight from the file (38 missing category, 30 invalid dates, 30 swapped coordinates).
- Real browser run (Vite + FastAPI): preview → commit → Incidents table showed 1,405 reports (1,346 with a point, 59 without); quarantine table with plain-language reasons; synthetic badge visible throughout.
- Offline smoke test: network calls raise; migrate → seed → import → query still passes.
- **Bug found by tests and fixed:** phone numbers written as `98765 43210` were not redacted.

**Failure cases covered:** empty file, no header, malformed CSV, oversize file, unknown/non-importable source, unmapped required field, bad mapping JSON, invalid/out-of-range/future dates, swapped/out-of-bounds/partial coordinates, missing category, duplicate and conflicting IDs, re-import, failed-batch retry, missing time, formula-like text, PII, mode mismatch, missing licence, 500 without leaking internals, invalid pagination/date filters.

**Risks / limits:** quarantine excerpts are redacted for phone/email only (names/addresses are not detected); `GET /observations` filters by string comparison of ISO dates (fine for current formats, revisit with analytics); preview echoes the user's own first rows unredacted back to them; real-mode path is tested with the real ward file but not with real complaint data (none exists yet).

**Undo:** delete `002_import.sql`, the `ingest/`, `geo/areas.py`, `db/{seed,deps}.py`, the two routes + main.py wiring, and the new web features; `rm data/db/citypulse.sqlite*`.

### Phase gates (blueprint note 133 — PASS / FAIL / NOT TESTED)
**Phase 1 — Architecture & scaffold → PASS**
| Criterion | Result | Evidence |
|---|---|---|
| Decision records, data flow, schema/API draft | PASS | ADR-0001, ARCHITECTURE.md, API.md, migrations 001–002 |
| Stack approved by user | PASS | user approval 2026-10-14 → ADR status ACCEPTED |
| Backend + web skeleton run | PASS | pytest/vitest/tsc/vite + live browser run |
| `make dev` one-command start | NOT TESTED | API and web were started separately; `make test` was run |

**Phase 2 — Sources & fixtures → PASS WITH EXPLICIT RISKS**
| Criterion | Result | Evidence |
|---|---|---|
| Verified/pending source matrix | PASS | 12 sources; 4 verified with evidence, rest candidate/research-only |
| Offline fixture import, repeatable | PASS | offline smoke test; re-import → `already_imported`, 0 rows |
| Visible data-mode badge | PASS | DataModeBadge test + screenshot |
| Synthetic fixtures with defects | PASS | injected defects caught with matching counts |
| Real-data path | NOT TESTED | no real complaint dataset exists; wards/census/OSM/rainfall are context layers, not yet loaded into analytics |
Explicit risks: boundary vintage unstated (DataMeet); no real observations; MCGM/IMD sources unresolved.

## 2026-10-14 · Phase 3 batch 2 + Phase 4 start (GeoJSON, boundaries, export, analytics + lineage)
**Why:** finish dependable ingestion (Phase 3) and deliver the first traceable numbers (Phase 4) — the core product promise that any number can be traced to its rows.

**What was built** (details in [API.md](API.md)):
1. **GeoJSON point import** through the same pipeline/rules as CSV (one set of validation; cross-format dedupe).
2. **Boundary registry:** QA report (validity, names, CRS basis, overlaps; gaps explicitly "not assessed"), whole-file rejection on blockers, versioned activation, history kept.
3. **Formula-injection-safe CSV export** of observations and quarantine, labelled SYNTHETIC in file name and column.
4. **Analytics + lineage:** `summary-1.0.0`, `trend-1.0.0`, deterministic `run_id`s, `/lineage/analysis-runs/{id}` with live "are the rows still the same?" verification; web Overview page (KPIs, trend chart with honest gap buckets, category/area breakdown) and a **Provenance X-ray v0** drawer.
- Fix made along the way: date filters now use the same Asia/Kolkata day as trends (they briefly used UTC days → a number and its rows could disagree at midnight).

**Files:** `api/migrations/003_boundaries_analytics.sql`; `api/citypulse/{db/queries.py, geo/geojson.py, geo/boundaries.py, analytics/metrics.py, ingest/parse.py (+GeoJSON), ingest/pipeline.py (format switch), api/routes/{analytics,boundaries,export,observations}.py}`; web `features/{overview/{OverviewPanel,TrendChart},provenance/LineageDrawer,import/BoundaryPanel}.tsx`, `lib/{api,format}.ts`; tests `tests/integration/{test_geojson_boundaries,test_analytics}.py`, `tests/contract/test_analytics_api.py`, `web/src/features/overview/TrendChart.test.tsx`.

**Evidence (executed 2026-10-14):**
- `make test` → backend **75 passed**, web **10 passed**; `tsc -b` clean; `vite build` OK.
- Hand-calculated analytics on the 12-row CSV: totals 5 / with point 3 / date-only 1 / unresolved area 1; daily series `1,1,1,1,0(gap),1`; ISO weeks `2 + 3`; per-10k `4/20000*10000 = 2.0`, and `None` for no/zero population.
- **Mutation check:** deliberately breaking the IST offset and the export neutraliser made the corresponding tests fail; code restored (tests do discriminate).
- **Upgrade path:** the live dev DB (created at migration 002) upgraded to 003 on startup with data intact; `/analytics/summary` twice → identical `run_fef9527c7183`.
- **Real browser:** Overview renders (1,405 reports, trend, categories, areas "not calculated"); clicking a number opens the lineage drawer: metric → run → "✓ rows behind this number are exactly the rows it was computed from" → batch + sha256 → source SYNTHETIC + licence → first rows.
- **Real BMC wards file through boundary QA (preview only, nothing stored):** 24/24 usable, valid, unique names, 0 overlaps, CRS declared WGS84, bbox 72.776,18.894–72.98,19.27.

**Failure cases covered:** malformed/empty GeoJSON, non-Point in a point file, unsupported CRS, self-intersecting/duplicate/missing-name/non-polygon/out-of-range boundaries, label missing, licence missing (real mode), boundary re-import & failed-retry, mode isolation of areas, formula/negative-number export, filters, empty DB, undated rows, IST midnight boundary, data-changed-since-run, unknown run, invalid granularity/date.

**Risks / limits:** gap detection between polygons is not implemented; boundary activation does not re-assign existing observations; per-10k uses Census 2011 (15-year-old) and is caveated; metric digests hash all matching IDs in Python (fine at 10⁵ rows, revisit beyond); analysis runs are recorded by GET (idempotent; deviation documented); no map yet; `make dev` still not run as a single command (NOT TESTED).

**Undo:** delete `003_boundaries_analytics.sql` + the new modules/routes/web features listed above and the main.py router lines; `rm data/db/citypulse.sqlite*` (migration 003 cannot be rolled back on an existing DB).

### Phase gates (note 133)
**Phase 3 — Schema & ingestion → PASS**
| Criterion | Result | Evidence |
|---|---|---|
| Blank-DB migration + upgrade | PASS | migration test; live DB 002→003 upgrade |
| Import preview, validation, quarantine | PASS | CSV + GeoJSON tests, UI run |
| Idempotency (re-import adds 0 rows) | PASS | CSV, GeoJSON, boundaries, cross-format |
| Formula-injection-safe export | PASS | export test + mutation check |
| Transactional/whole-batch rules for geometry | PASS | boundary & point-file refusal tests |
| Real complaint data import | NOT TESTED | no real dataset exists |

**Phase 4 — Deterministic analytics → IN PROGRESS** (summary, trend, lineage PASS; recurrence/related-record explorer NOT STARTED)

## 2026-10-14 · Repo hygiene + sub-phase plan (sub-phase 1.7)
- Added MIT `LICENSE`, `NOTICE.md` (data attribution & share-alike obligations), rewrote `README.md` (what works / what doesn't, data reality, quick start).
- `docs/PHASES.md` rewritten: every phase now has sub-phases (`N.M`) with a done-when test and status; Track B phases list their sub-phases. Newly surfaced work: **1.5** verify `make dev`, **1.6** CI, **2.5** tests for data scripts, **2.6** licence resolution, **2.7** real-mode fixture DB, **3.6–3.8** repair/privacy/xlsx, **4.6–4.8** denominators/freshness/metric dictionary.
- `docs/WORKFLOW.md`: unit of work is a sub-phase.
- No code changed; no tests added in this entry.

## Open items needing the user
1. ~~Approve the stack~~ — approved 2026-10-14.
2. Boundary vintage: confirm the DataMeet wards match current BMC wards before any real-pilot claim.
3. Licence decisions: do you want me to look for IMD's data policy, or a smaller licensed MCGM excerpt?
4. Any partner/NGO complaint CSV (the only realistic source of real observations)?
5. SA obligation: if you publish derived datasets (wards/OSM layers), they must carry CC BY-SA / ODbL terms.
