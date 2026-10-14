"""Boundary QA + versioned import (blueprint 030/035). Blocking problems quarantine the WHOLE file (no partial
ward sets that would silently misassign reports). Overlaps are reported as warnings; gaps are NOT assessed."""
import json
import math
import sqlite3
from datetime import datetime, timezone

from shapely import STRtree
from shapely.geometry import mapping, shape
from shapely.validation import explain_validity

from citypulse.core.errors import AppError
from citypulse.core.provenance import new_id, sha256_bytes
from citypulse.core.settings import Settings
from citypulse.geo.geojson import crs_basis, load_feature_collection

NAME_KEYS = ("name", "ward", "ward_name", "zone_name", "area_name", "NAME", "Name", "WARD")
OVERLAP_WARN_RATIO = 0.01
MAX_LISTED = 20


def _coords_ok(c) -> bool:
    if isinstance(c, (int, float)):
        return math.isfinite(c)
    return all(_coords_ok(x) for x in c)


def qa(gj: dict, name_property: str | None) -> tuple[list[dict], dict]:
    feats = gj["features"]
    props = {k for f in feats[:50] if isinstance(f, dict) for k in (f.get("properties") or {})}
    name_key = name_property or next((k for k in NAME_KEYS if k in props), None)
    blocking: dict[str, list] = {"not_polygon": [], "invalid_geometry": [], "bad_coordinates": [], "missing_name": [], "duplicate_name": []}
    geoms, names, seen = [], [], {}
    for i, f in enumerate(feats):
        g = f.get("geometry") if isinstance(f, dict) else None
        nm = str(((f.get("properties") or {}).get(name_key) or "")).strip() if isinstance(f, dict) and name_key else ""
        if not g or g.get("type") not in ("Polygon", "MultiPolygon"):
            blocking["not_polygon"].append({"feature": i, "type": (g or {}).get("type")})
            continue
        try:
            if not _coords_ok(g["coordinates"]):
                raise ValueError
            geom = shape(g)
        except Exception:  # shapely/GEOS raise many types on malformed rings
            blocking["bad_coordinates"].append({"feature": i})
            continue
        minx, miny, maxx, maxy = geom.bounds
        if minx < -180 or maxx > 180 or miny < -90 or maxy > 90:
            blocking["bad_coordinates"].append({"feature": i, "reason": "outside lon/lat range"})
            continue
        if geom.is_empty or not geom.is_valid:
            blocking["invalid_geometry"].append({"feature": i, "name": nm, "reason": explain_validity(geom)})
            continue
        if not nm:
            blocking["missing_name"].append({"feature": i})
            continue
        if nm.lower() in seen:
            blocking["duplicate_name"].append({"feature": i, "name": nm, "first_seen_feature": seen[nm.lower()]})
            continue
        seen[nm.lower()] = i
        geoms.append(geom)
        names.append((nm, g))
    overlaps = []
    if geoms:
        tree = STRtree(geoms)
        for i, gm in enumerate(geoms):
            for j in tree.query(gm):
                j = int(j)
                if j <= i:
                    continue
                inter = gm.intersection(geoms[j]).area
                small = min(gm.area, geoms[j].area)
                if small > 0 and inter / small > OVERLAP_WARN_RATIO:
                    overlaps.append({"a": names[i][0], "b": names[j][0], "overlap_ratio_of_smaller": round(inter / small, 4)})
    bbox = None
    if geoms:
        b = [g.bounds for g in geoms]
        bbox = [min(x[0] for x in b), min(x[1] for x in b), max(x[2] for x in b), max(x[3] for x in b)]
    issues = {k: v[:MAX_LISTED] for k, v in blocking.items() if v}
    report = {
        "feature_count": len(feats), "usable_features": len(geoms), "name_property": name_key, "bbox": bbox,
        "blocking_issue_counts": {k: len(v) for k, v in blocking.items() if v}, "blocking_issues": issues,
        "overlap_warnings": overlaps[:MAX_LISTED], "overlap_count": len(overlaps),
        "gaps": "not assessed", "warnings": [],
    }
    if overlaps:
        report["warnings"].append(f"{len(overlaps)} polygon pair(s) overlap by more than {OVERLAP_WARN_RATIO:.0%} of the smaller one.")
    if not name_key:
        report["blocking_issue_counts"]["no_name_property"] = len(feats)
    report["ok"] = not report["blocking_issue_counts"] and len(geoms) == len(feats)
    return [{"name": n, "geometry": g} for n, g in names], report


def import_boundaries(con: sqlite3.Connection, settings: Settings, *, data: bytes, filename: str, source_id: str,
                      label: str, vintage: str | None, name_property: str | None, level: str | None,
                      licence_declared: str | None, commit: bool, source_row) -> dict:
    gj = load_feature_collection(data)
    crs, basis = crs_basis(gj)
    sha = sha256_bytes(data)
    areas, report = qa(gj, name_property)
    already = con.execute("SELECT boundary_version_id,status FROM boundary_version WHERE source_id=? AND file_sha256=?",
                          (source_id, sha)).fetchone()
    out = {"source_id": source_id, "data_mode": settings.data_mode, "file_name": filename, "file_sha256": sha, "label": label,
           "vintage": vintage, "crs": crs, "crs_basis": basis, "qa": report,
           "caveats": ["Boundaries are only as authoritative as their source; vintage must match the report period.",
                       "CRS is assumed WGS84 lon/lat unless the file declares it; nothing is reprojected.",
                       "Existing observations keep their current area; only future imports use the new boundaries."]}
    if basis == "assumed-wgs84":
        out["caveats"].append("File did not declare a CRS: WGS84 assumed (GeoJSON standard).")
    if not commit:
        return out | {"status": "preview", "already_imported": bool(already and already["status"] != "failed")}
    if not (label or "").strip():
        raise AppError("A version label is required.", fields={"label": "required"}, code="label_required")
    if already and already["status"] != "failed":
        return out | {"status": "already_imported", "boundary_version_id": already["boundary_version_id"]}

    now = datetime.now(timezone.utc).isoformat()
    bvid = new_id("bv")
    ok = report["ok"]
    with con:
        if already:  # previous failed attempt is replaced
            con.execute("DELETE FROM boundary_version WHERE boundary_version_id=?", (already["boundary_version_id"],))
        if ok:
            con.execute("UPDATE area SET is_active=0 WHERE is_synthetic=? AND is_active=1", (int(settings.data_mode == "synthetic"),))
            con.execute("UPDATE boundary_version SET status='superseded' WHERE is_synthetic=? AND status='active'",
                        (int(settings.data_mode == "synthetic"),))
        con.execute(
            """INSERT INTO boundary_version (boundary_version_id,label,source_id,file_name,file_sha256,crs,crs_basis,name_property,
                 level,vintage,licence_declared,feature_count,bbox_json,qa_json,status,is_synthetic,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (bvid, label.strip(), source_id, filename, sha, crs, basis, report["name_property"], level, vintage, licence_declared,
             report["usable_features"], json.dumps(report["bbox"]), json.dumps(report), "active" if ok else "failed",
             int(bool(source_row["is_synthetic"])), now))
        if ok:
            for a in areas:
                con.execute(
                    """INSERT INTO area (area_id,name,level,boundary_source,boundary_version,geometry_geojson,is_synthetic,
                         is_active,boundary_version_id) VALUES (?,?,?,?,?,?,?,1,?)""",
                    (f"{bvid}:{a['name']}", a["name"], level or "area", source_id, label.strip(), json.dumps(mapping(shape(a["geometry"]))),
                     int(bool(source_row["is_synthetic"])), bvid))
        con.execute("INSERT INTO audit_event (at,actor,action,ref,detail) VALUES (?,?,?,?,?)",
                    (now, "local-user", "boundary_import", bvid, json.dumps({"ok": ok, "features": report["feature_count"]})))
    return out | {"status": "active" if ok else "failed", "boundary_version_id": bvid}
