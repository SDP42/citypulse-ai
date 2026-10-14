import json
import sqlite3

from fastapi import APIRouter, Depends, File, Form, UploadFile

from citypulse.api.routes.imports import _read_limited
from citypulse.core.settings import Settings, get_settings
from citypulse.db.deps import get_db
from citypulse.geo.boundaries import import_boundaries
from citypulse.ingest.pipeline import _source

router = APIRouter(prefix="/boundaries")


async def _go(file, source_id, label, vintage, name_property, level, licence, commit, con, settings):
    data = await _read_limited(file, settings.max_upload_mb)
    src = _source(con, source_id, settings, need_licence=licence, commit=commit)
    return import_boundaries(con, settings, data=data, filename=file.filename or "boundaries.geojson", source_id=source_id,
                             label=label or "", vintage=vintage, name_property=name_property, level=level,
                             licence_declared=licence, commit=commit, source_row=src)


@router.post("/preview")
async def preview(file: UploadFile = File(...), source_id: str = Form(...), label: str | None = Form(None),
                  vintage: str | None = Form(None), name_property: str | None = Form(None), level: str | None = Form(None),
                  con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    return await _go(file, source_id, label, vintage, name_property, level, None, False, con, settings)


@router.post("")
async def commit(file: UploadFile = File(...), source_id: str = Form(...), label: str = Form(...),
                 vintage: str | None = Form(None), name_property: str | None = Form(None), level: str | None = Form(None),
                 licence_declared: str | None = Form(None), con: sqlite3.Connection = Depends(get_db),
                 settings: Settings = Depends(get_settings)):
    return await _go(file, source_id, label, vintage, name_property, level, licence_declared, True, con, settings)


@router.get("")
def list_versions(con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    rows = con.execute("""SELECT boundary_version_id,label,source_id,file_name,crs,crs_basis,level,vintage,feature_count,bbox_json,
                          status,is_synthetic,created_at,qa_json FROM boundary_version WHERE is_synthetic=? ORDER BY created_at DESC""",
                       (int(settings.data_mode == "synthetic"),)).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d["bbox"] = json.loads(d.pop("bbox_json") or "null")
        d["qa"] = json.loads(d.pop("qa_json"))
        items.append(d)
    return {"items": items, "data_mode": settings.data_mode}
