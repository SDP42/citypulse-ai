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

## Planned (not implemented): `/analytics/*`, `/documents/search`, `/analysis-runs`, `/reports/*`, `/lineage/*`, `/agent/*`.
