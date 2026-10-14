import json
import sqlite3

from fastapi import APIRouter, Depends, Query

from citypulse.core.settings import Settings, get_settings
from citypulse.db.deps import get_db
from citypulse.db.queries import FROM, Filters, where

router = APIRouter()
DATE = r"^\d{4}-\d{2}-\d{2}$"


def filters(category: str | None = None, area_id: str | None = None, source_id: str | None = None,
            date_from: str | None = Query(None, pattern=DATE), date_to: str | None = Query(None, pattern=DATE)) -> Filters:
    return Filters(category, area_id, source_id, date_from, date_to)


@router.get("/observations")
def list_observations(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), f: Filters = Depends(filters),
                      con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    w, args = where(settings.data_mode == "synthetic", f)
    total = con.execute(f"SELECT COUNT(*) {FROM} WHERE {w}", args).fetchone()[0]
    q = con.execute(f"""SELECT o.observation_id,o.source_id,o.batch_id,o.external_id,o.category,o.text_raw,o.reported_at,
                        o.event_time_precision,o.status_source,o.latitude,o.longitude,o.area_id,a.name AS area_name,
                        o.location_method,o.location_confidence,o.quality_flags {FROM} WHERE {w}
                        ORDER BY (o.reported_at IS NULL), o.reported_at DESC, o.observation_id LIMIT ? OFFSET ?""",
                    [*args, limit, offset]).fetchall()
    items = []
    for r in q:
        d = dict(r)
        d["quality_flags"] = json.loads(d["quality_flags"])
        d["text"] = d.pop("text_raw")
        items.append(d)
    point = con.execute(f"SELECT COUNT(*) {FROM} WHERE {w} AND o.latitude IS NOT NULL", args).fetchone()[0]
    return {
        "items": items, "total": total, "limit": limit, "offset": offset,
        "scope": {"data_mode": settings.data_mode, **f.as_dict()},
        "quality": {"with_point_coordinates": point, "without_point_coordinates": total - point},
        "caveats": ["Rows are reports, not confirmed incidents. Missing coordinates are never filled in."],
    }


@router.get("/areas")
def list_areas(con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    rows = con.execute("""SELECT a.area_id,a.name,a.level,a.boundary_source,a.boundary_version,a.population,
                          a.population_vintage,
                          (SELECT COUNT(*) FROM observation o WHERE o.area_id=a.area_id) AS observations
                          FROM area a WHERE a.is_synthetic=? AND a.is_active=1 ORDER BY a.area_id""",
                       (int(settings.data_mode == "synthetic"),)).fetchall()
    return {"items": [dict(r) for r in rows], "data_mode": settings.data_mode}
