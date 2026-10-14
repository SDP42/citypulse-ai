"""Idempotent seed: source register + areas (real BMC wards, synthetic zones). Safe to run on every start."""
import json
import sqlite3
from pathlib import Path

from citypulse.core.settings import ROOT
from citypulse.sources.registry import load_register

WARDS = ROOT / "data" / "processed" / "mumbai_wards.geojson"
ZONES = ROOT / "data" / "fixtures" / "synthetic_zones.geojson"


def seed_sources(con: sqlite3.Connection) -> int:
    n = 0
    for s in load_register():
        con.execute(
            """INSERT INTO source_registry (source_id, source_name, owner, canonical_url, access_method,
                 licence_name, attribution_text, terms_checked_at, source_status, is_synthetic,
                 geographic_coverage, temporal_coverage, known_limitations)
               VALUES (:source_id,:source_name,:owner,:canonical_url,:access_method,:licence_name,
                 :attribution_text,:checked_at,:source_status,:is_synthetic,:geographic_coverage,
                 :temporal_coverage,:known_limitations)
               ON CONFLICT(source_id) DO UPDATE SET source_name=excluded.source_name, owner=excluded.owner,
                 canonical_url=excluded.canonical_url, access_method=excluded.access_method,
                 licence_name=excluded.licence_name, attribution_text=excluded.attribution_text,
                 terms_checked_at=excluded.terms_checked_at, source_status=excluded.source_status,
                 is_synthetic=excluded.is_synthetic, geographic_coverage=excluded.geographic_coverage,
                 temporal_coverage=excluded.temporal_coverage, known_limitations=excluded.known_limitations""",
            {k: s.get(k) for k in ("source_id", "source_name", "owner", "canonical_url", "access_method",
                                    "licence_name", "attribution_text", "checked_at", "source_status",
                                    "is_synthetic", "geographic_coverage", "temporal_coverage",
                                    "known_limitations")} | {"is_synthetic": s.get("is_synthetic", 0)})
        n += 1
    return n


def _seed_areas(con, path: Path, synthetic: bool, id_prefix: str, name_key: str, extra) -> int:
    if not path.exists():
        return 0
    gj = json.loads(path.read_text())
    for f in gj["features"]:
        p = f["properties"]
        pop, vint, bsrc, bver = extra(p)
        con.execute(
            """INSERT INTO area (area_id,name,level,boundary_source,boundary_version,geometry_geojson,
                 is_synthetic,population,population_vintage)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(area_id) DO UPDATE SET geometry_geojson=excluded.geometry_geojson,
                 population=excluded.population""",
            (f"{id_prefix}:{p[name_key]}", p["name"] if synthetic else p["ward"], "ward" if not synthetic else "zone",
             bsrc, bver, json.dumps(f["geometry"]), int(synthetic), pop, vint))
    return len(gj["features"])


def seed_areas(con: sqlite3.Connection) -> dict[str, int]:
    wards = _seed_areas(con, WARDS, False, "ward", "ward",
                        lambda p: (p.get("population_2011"), "Census 2011", p.get("boundary_source"), p.get("boundary_vintage")))
    zones = _seed_areas(con, ZONES, True, "zone", "zone_id", lambda p: (None, None, "synthetic", "synthetic"))
    return {"wards": wards, "zones": zones}


def seed_all(con: sqlite3.Connection) -> dict:
    with con:
        sources = seed_sources(con)
        areas = seed_areas(con)
    return {"sources": sources, **areas}
