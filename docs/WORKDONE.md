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

## Open items needing the user
1. ~~Approve the stack~~ — approved 2026-10-14.
2. Boundary vintage: confirm the DataMeet wards match current BMC wards before any real-pilot claim.
3. Licence decisions: do you want me to look for IMD's data policy, or a smaller licensed MCGM excerpt?
4. Any partner/NGO complaint CSV (the only realistic source of real observations)?
5. SA obligation: if you publish derived datasets (wards/OSM layers), they must carry CC BY-SA / ODbL terms.
