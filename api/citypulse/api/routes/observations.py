import json
import sqlite3

from fastapi import APIRouter, Depends, Query

from citypulse.core.errors import AppError
from citypulse.core.settings import Settings, get_settings
from citypulse.db.deps import get_db

router = APIRouter()


@router.get("/observations")
def list_observations(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                      category: str | None = None, area_id: str | None = None, source_id: str | None = None,
                      date_from: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}"),
                      date_to: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}"),
                      con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    where = ["s.is_synthetic = ?"]  # synthetic and real are never mixed in one result
    args: list = [int(settings.data_mode == "synthetic")]
    for col, val in (("o.category", category), ("o.area_id", area_id), ("o.source_id", source_id)):
        if val:
            where.append(f"{col} = ?")
            args.append(val)
    if date_from:
        where.append("o.reported_at >= ?")
        args.append(date_from)
    if date_to:
        where.append("o.reported_at < ?")
        args.append(date_to + "~")  # includes the whole end day (ISO strings sort before '~')
    w = " AND ".join(where)
    base = f"FROM observation o JOIN source_registry s ON s.source_id=o.source_id LEFT JOIN area a ON a.area_id=o.area_id WHERE {w}"
    total = con.execute(f"SELECT COUNT(*) {base}", args).fetchone()[0]
    q = con.execute(f"""SELECT o.observation_id,o.source_id,o.batch_id,o.external_id,o.category,o.text_raw,o.reported_at,
                        o.event_time_precision,o.status_source,o.latitude,o.longitude,o.area_id,a.name AS area_name,
                        o.location_method,o.location_confidence,o.quality_flags {base}
                        ORDER BY (o.reported_at IS NULL), o.reported_at DESC, o.observation_id LIMIT ? OFFSET ?""",
                    [*args, limit, offset]).fetchall()
    items = []
    for r in q:
        d = dict(r)
        d["quality_flags"] = json.loads(d["quality_flags"])
        d["text"] = d.pop("text_raw")
        items.append(d)
    point = con.execute(f"SELECT COUNT(*) {base} AND o.latitude IS NOT NULL", args).fetchone()[0]
    return {
        "items": items, "total": total, "limit": limit, "offset": offset,
        "scope": {"data_mode": settings.data_mode, "category": category, "area_id": area_id, "source_id": source_id,
                  "date_from": date_from, "date_to": date_to},
        "quality": {"with_point_coordinates": point, "without_point_coordinates": total - point},
        "caveats": ["Rows are reports, not confirmed incidents. Missing coordinates are never filled in."],
    }


@router.get("/areas")
def list_areas(con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    rows = con.execute("""SELECT a.area_id,a.name,a.level,a.boundary_source,a.boundary_version,a.population,
                          a.population_vintage,
                          (SELECT COUNT(*) FROM observation o WHERE o.area_id=a.area_id) AS observations
                          FROM area a WHERE a.is_synthetic=? ORDER BY a.area_id""",
                       (int(settings.data_mode == "synthetic"),)).fetchall()
    return {"items": [dict(r) for r in rows], "data_mode": settings.data_mode}
