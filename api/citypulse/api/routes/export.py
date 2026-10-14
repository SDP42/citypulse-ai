"""CSV export with spreadsheet formula-injection protection (blueprint 034, OWASP CSV injection).
Exports are labelled with their data mode in the file name AND in a column."""
import csv
import io
import json
import sqlite3

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from citypulse.api.routes.observations import filters
from citypulse.core.csv_safety import neutralise_formula
from citypulse.core.errors import NotFound
from citypulse.core.settings import Settings, get_settings
from citypulse.db.deps import get_db
from citypulse.db.queries import FROM, Filters, where

router = APIRouter()
MAX_EXPORT_ROWS = 100_000
OBS_COLS = ["observation_id", "source_id", "batch_id", "external_id", "category", "text", "reported_at", "event_time_precision",
            "status_source", "latitude", "longitude", "area_id", "area_name", "location_method", "location_confidence",
            "quality_flags", "data_mode"]


def _safe(v):
    return neutralise_formula(v) if isinstance(v, str) else v


def _stream(header: list[str], rows) -> StreamingResponse:
    def gen():
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(header)
        yield buf.getvalue()
        for r in rows:
            buf.seek(0), buf.truncate()
            w.writerow([_safe(v) for v in r])
            yield buf.getvalue()
    return StreamingResponse(gen(), media_type="text/csv; charset=utf-8")


@router.get("/observations/export.csv")
def export_observations(limit: int = Query(MAX_EXPORT_ROWS, ge=1, le=MAX_EXPORT_ROWS), f: Filters = Depends(filters),
                        con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    w, args = where(settings.data_mode == "synthetic", f)
    q = con.execute(f"""SELECT o.observation_id,o.source_id,o.batch_id,o.external_id,o.category,o.text_raw,o.reported_at,
                        o.event_time_precision,o.status_source,o.latitude,o.longitude,o.area_id,a.name,o.location_method,
                        o.location_confidence,o.quality_flags {FROM} WHERE {w}
                        ORDER BY (o.reported_at IS NULL), o.reported_at DESC, o.observation_id LIMIT ?""", [*args, limit])
    rows = (list(r) + [settings.data_mode] for r in q)
    resp = _stream(OBS_COLS, rows)
    prefix = "SYNTHETIC_" if settings.data_mode == "synthetic" else ""
    resp.headers["Content-Disposition"] = f'attachment; filename="{prefix}citypulse_observations.csv"'
    return resp


@router.get("/imports/{batch_id}/quarantine/export.csv")
def export_quarantine(batch_id: str, con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    b = con.execute("SELECT data_mode FROM ingestion_batch WHERE batch_id=?", (batch_id,)).fetchone()
    if not b:
        raise NotFound(f"Unknown batch '{batch_id}'.")
    q = con.execute("SELECT row_number,error_codes,redacted_excerpt FROM quarantine_row WHERE batch_id=? ORDER BY row_number", (batch_id,))
    rows = ([r[0], "; ".join(json.loads(r[1])), r[2], b["data_mode"]] for r in q)
    resp = _stream(["row_number", "error_codes", "redacted_excerpt", "data_mode"], rows)
    prefix = "SYNTHETIC_" if b["data_mode"] == "synthetic" else ""
    resp.headers["Content-Disposition"] = f'attachment; filename="{prefix}quarantine_{batch_id}.csv"'
    return resp
