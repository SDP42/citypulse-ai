# API contract (implemented routes only)

Base: `http://127.0.0.1:8000` (web dev proxies `/api/*`). All errors: `{code, message, correlation_id, fields}` — never a stack trace or file path. Validation errors are `422 validation_error` with per-field messages.

| Route | Mutates? | Notes |
|---|---|---|
| `GET /health` | no | version, `data_mode`, `network`, `llm_provider` |
| `GET /sources` · `GET /sources/{id}/status` | no | source register incl. status, licence, limitations, evidence |
| `POST /imports/preview` | **no** | multipart: `file`, `source_id`, optional `mapping` (JSON), `timezone`. Dry run: counts, error/flag codes, mapping, 5 sample rows |
| `POST /imports` | yes | same + `licence_declared` (required for non-synthetic sources). Single transaction; idempotent |
| `GET /imports` · `GET /imports/{batch_id}` | no | batch history and detail |
| `GET /imports/{batch_id}/quarantine` | no | `limit` ≤ 200, `offset`; redacted excerpts, error codes |
| `GET /observations` | no | filters `category, area_id, source_id, date_from, date_to`; `limit` ≤ 200; deterministic order; returns `scope`, `quality`, `caveats` |
| `GET /observations/export.csv` | no | formula-injection-safe CSV (cells starting `= + - @` get an apostrophe; numbers untouched); same filters; file name prefixed `SYNTHETIC_` in synthetic mode; `data_mode` column |
| `GET /imports/{batch_id}/quarantine/export.csv` | no | quarantined rows as CSV, same safety + labelling |
| `POST /boundaries/preview` · `POST /boundaries` · `GET /boundaries` | commit: yes | GeoJSON polygon file → QA report → versioned, activated boundary set (see below) |
| `GET /analytics/summary` · `GET /analytics/trends?granularity=day\|week` | records a run* | versioned metrics, same filters as `/observations` |
| `GET /analysis-runs/{id}` · `/analysis-runs/{id}/records` | no | stored result; the exact rows behind it (re-derived from stored filters) |
| `GET /lineage/analysis-runs/{id}` | no | metric definition → run → scope → input digest + live verification → batches → sources/licences |
| `GET /areas` | no | areas of the active data mode with observation counts and population (+vintage) |

## Import semantics
- Limits: 25 MB file (`MAX_UPLOAD_MB`), 200,000 rows, 10,000 chars/cell.
- Encoding: UTF-8 (BOM ok) → cp1252 (flagged) → latin-1 (flagged). Delimiter sniffed (`, ; tab |`). Cells are text only; nothing is evaluated.
- **Quarantine (row rejected, kept redacted):** `missing_category`, `invalid_timestamp`, `timestamp_out_of_range`, `coords_possibly_swapped`, `coords_out_of_bounds`, `coords_invalid_range`, `coords_incomplete`, `coords_not_numeric`, `conflicting_duplicate_id`, `field_too_long`.
- **Kept with a flag:** `missing_timestamp` (never replaced by import time), `no_point_coordinates`, `location_unresolved`, `tz_assumed` (Asia/Kolkata), `dmy_format_assumed`, `pii_redacted` (phone/email), `formula_like_text`, `unrecognised_category`, `outside_all_areas`, `text_truncated`.
- Swapped coordinates are **not auto-corrected** (blueprint 029).
- Date-only values are stored as dates (`precision=day`), not midnight instants.
- Idempotency: `(source, file sha256, parser_version)` → batch; `(source, record_hash)` → record. Same file again → `already_imported`, 0 rows. Zero accepted rows → batch `failed`, nothing stored.
- Mode guard: synthetic sources only in `DATA_MODE=synthetic`, real only in `real` (`409 data_mode_mismatch`).
- Raw upload kept immutable at `data/raw/uploads/<sha16>_<name>` (gitignored).

## GeoJSON points
`POST /imports` auto-detects GeoJSON (`.geojson`/`.json` or a `{` body). Point features only; **any** non-Point feature refuses the whole file (`geometry_not_point`). Coordinates are `[lon, lat]`; properties map through the same column mapping and the same validation as CSV, so a record imported from CSV and from GeoJSON has the same hash and is deduplicated. Null geometry = no point (kept at area level). A declared non-WGS84 `crs` is refused (`crs_unsupported`); no `crs` → WGS84 assumed and flagged `crs_assumed_wgs84`.

## Boundaries
QA blocks on: invalid geometry, non-polygon, bad/out-of-range coordinates, missing name, duplicate name (case-insensitive) — **any** blocker rejects the whole file (no partial ward set; existing areas stay active). Overlaps >1% of the smaller polygon are warnings. **Gaps are not assessed** (reported as such). On success the file becomes the active version for the current data mode; previous areas are kept inactive. Existing observations are not re-assigned. Real mode needs `licence_declared`. Same file again → `already_imported`.

## Analytics (Phase 4, first slice)
- Metrics: `summary-1.0.0` (total, with/without point, undated, date-only, by category, by area with per-10k only where a population denominator exists else `not calculated`) and `trend-1.0.0` (day/ISO-week buckets, Asia/Kolkata; gap buckets flagged `no_reports`, undated rows counted separately).
- Day boundaries: both filters and trends use the **Asia/Kolkata calendar day** (date-only values are used as-is), so a number and its rows can never disagree at midnight.
- *Idempotent runs:* `run_id = hash(metric, version, params, data mode, input digest)`. Same inputs → same run and same result; any data change → new run, and old runs report `data_changed_since_run` on `/lineage`. A GET that records a run is a deliberate deviation from the blueprint's `POST /analysis-runs`, justified by this idempotency; revisit if runs ever carry side effects.
- Every response carries `scope`, `input {count, digest, source_ids, batch_ids}`, `quality {denominator, exclusions}`, `caveats`, `kind: computed`. Small samples (<30) and synthetic mode add explicit caveats.

## Planned (not implemented): recurrence/hotspots, `/documents/search`, `/reports/*`, `/agent/*`.
