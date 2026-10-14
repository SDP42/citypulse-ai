import json
import sqlite3

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from citypulse.core.errors import AppError, NotFound, PayloadTooLarge
from citypulse.core.settings import Settings, get_settings
from citypulse.db.deps import get_db
from citypulse.ingest.pipeline import run_import

router = APIRouter(prefix="/imports")
CHUNK = 1 << 20


async def _read_limited(file: UploadFile, limit_mb: int) -> bytes:
    buf = bytearray()
    while chunk := await file.read(CHUNK):
        buf += chunk
        if len(buf) > limit_mb * 1024 * 1024:
            raise PayloadTooLarge(f"File exceeds {limit_mb} MB.", code="file_too_large")
    return bytes(buf)


def _mapping(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        m = json.loads(raw)
        assert isinstance(m, dict)
        return m
    except (ValueError, AssertionError):
        raise AppError("mapping must be a JSON object of field -> column.", fields={"mapping": "invalid"}, code="bad_mapping") from None


@router.post("/preview")
async def preview(file: UploadFile = File(...), source_id: str = Form(...), mapping: str | None = Form(None),
                  timezone: str = Form("Asia/Kolkata"), con: sqlite3.Connection = Depends(get_db),
                  settings: Settings = Depends(get_settings)):
    data = await _read_limited(file, settings.max_upload_mb)
    return run_import(con, settings, data=data, filename=file.filename or "upload.csv", source_id=source_id,
                      mapping=_mapping(mapping), tz_name=timezone, commit=False)


@router.post("")
async def commit(file: UploadFile = File(...), source_id: str = Form(...), mapping: str | None = Form(None),
                 timezone: str = Form("Asia/Kolkata"), licence_declared: str | None = Form(None),
                 con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    data = await _read_limited(file, settings.max_upload_mb)
    return run_import(con, settings, data=data, filename=file.filename or "upload.csv", source_id=source_id,
                      mapping=_mapping(mapping), tz_name=timezone, licence_declared=licence_declared, commit=True)


@router.get("")
def list_batches(limit: int = Query(50, ge=1, le=200), con: sqlite3.Connection = Depends(get_db)):
    rows = con.execute("""SELECT batch_id,source_id,file_name,file_sha256,started_at,status,parser_version,rows_total,
                          rows_accepted,rows_quarantined,rows_duplicate,data_mode FROM ingestion_batch
                          ORDER BY started_at DESC, batch_id LIMIT ?""", (limit,)).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.get("/{batch_id}")
def get_batch(batch_id: str, con: sqlite3.Connection = Depends(get_db)):
    r = con.execute("SELECT * FROM ingestion_batch WHERE batch_id=?", (batch_id,)).fetchone()
    if not r:
        raise NotFound(f"Unknown batch '{batch_id}'.")
    d = dict(r)
    d["mapping"] = json.loads(d.pop("mapping_json") or "{}")
    d["summary"] = json.loads(d.pop("summary_json") or "{}")
    return d


@router.get("/{batch_id}/quarantine")
def quarantine(batch_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
               con: sqlite3.Connection = Depends(get_db)):
    if not con.execute("SELECT 1 FROM ingestion_batch WHERE batch_id=?", (batch_id,)).fetchone():
        raise NotFound(f"Unknown batch '{batch_id}'.")
    total = con.execute("SELECT COUNT(*) FROM quarantine_row WHERE batch_id=?", (batch_id,)).fetchone()[0]
    rows = con.execute("SELECT row_number,error_codes,redacted_excerpt FROM quarantine_row WHERE batch_id=? "
                       "ORDER BY row_number LIMIT ? OFFSET ?", (batch_id, limit, offset)).fetchall()
    items = [{"row_number": r["row_number"], "error_codes": json.loads(r["error_codes"]), "excerpt": r["redacted_excerpt"]}
             for r in rows]
    return {"items": items, "total": total, "limit": limit, "offset": offset}
