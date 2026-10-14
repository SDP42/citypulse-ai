import json

import pytest

from citypulse.core.errors import AppError
from citypulse.core.settings import Settings
from citypulse.geo.boundaries import import_boundaries
from citypulse.ingest import pipeline
from citypulse.ingest.pipeline import _source, run_import
from tests.conftest import NOW, requires_wards
from tests.integration.test_importer import HAND


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)


def sq(x0, y0, x1, y1):
    return [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]


def fc(*features, **extra):
    return json.dumps({"type": "FeatureCollection", "features": list(features), **extra}).encode()


def poly(name, ring, key="name"):
    return {"type": "Feature", "properties": {key: name} if name is not None else {}, "geometry": {"type": "Polygon", "coordinates": ring}}


def point(props, lon, lat):
    return {"type": "Feature", "properties": props, "geometry": {"type": "Point", "coordinates": [lon, lat]}}


def bnd(db, settings, data, commit=False, source="synthetic-fixture", label="v1", **kw):
    return import_boundaries(db, settings, data=data, filename="b.geojson", source_id=source, label=label, vintage="2026",
                             name_property=kw.get("name_property"), level="ward", licence_declared=kw.get("licence"),
                             commit=commit, source_row=_source(db, source, settings, need_licence=kw.get("licence"), commit=commit))


NS = fc(poly("North", sq(72.80, 19.00, 72.90, 19.05)), poly("South", sq(72.80, 18.95, 72.90, 19.00)))


# ---------------- GeoJSON points ----------------
def imp(db, settings, data, filename="p.geojson", commit=True):
    return run_import(db, settings, data=data, filename=filename, source_id="synthetic-fixture", commit=commit, now=NOW)


def test_geojson_points_use_lon_lat_order_and_same_rules(db, settings):
    data = fc(
        point({"external_id": "G1", "category": "pothole", "reported_at": "2026-08-01"}, 72.87, 19.0),
        point({"external_id": "G2", "category": "pothole", "reported_at": "2026-08-01"}, 19.0, 72.87),   # lat/lon swapped
        {"type": "Feature", "properties": {"external_id": "G3", "category": "garbage", "zone_name": "Synthetic Zone 11"}, "geometry": None},
    )
    s = imp(db, settings, data)
    assert s["format"] == "geojson" and s["parser_version"] == "geojson-points-1.0.0"
    assert (s["rows_total"], s["rows_accepted"], s["rows_quarantined"]) == (3, 2, 1)
    assert s["error_counts"] == {"coords_possibly_swapped": 1}
    assert s["flag_counts"]["crs_assumed_wgs84"] == 1 and s["flag_counts"]["missing_timestamp"] == 1
    r = {x["external_id"]: x for x in db.execute("select * from observation")}
    assert (r["G1"]["longitude"], r["G1"]["latitude"]) == (72.87, 19.0) and r["G1"]["area_id"] == "zone:Z-1-1"
    assert r["G3"]["latitude"] is None and r["G3"]["location_method"] == "area-name"


def test_geojson_non_point_refuses_whole_file(db, settings):
    data = fc(point({"category": "pothole"}, 72.87, 19.0), poly("X", sq(72.8, 19.0, 72.9, 19.05)))
    with pytest.raises(AppError) as e:
        imp(db, settings, data)
    assert e.value.code == "geometry_not_point" and "1 feature" in e.value.message
    assert db.execute("select count(*) from observation").fetchone()[0] == 0


@pytest.mark.parametrize("data,code", [(b"{not json", "malformed_geojson"), (b'{"type":"Feature"}', "malformed_geojson"),
                                       (fc(), "empty_file"),
                                       (fc(point({"category": "x"}, 1, 1), crs={"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::32643"}}), "crs_unsupported")])
def test_geojson_bad_files(db, settings, data, code):
    with pytest.raises(AppError) as e:
        imp(db, settings, data)
    assert e.value.code == code


def test_same_record_in_csv_and_geojson_is_one_record(db, settings):
    csv_ = "external_id,category,reported_at,latitude,longitude\nX1,pothole,2026-08-01,19.0,72.87\n"
    run_import(db, settings, data=csv_.encode(), filename="a.csv", source_id="synthetic-fixture", commit=True, now=NOW)
    s = imp(db, settings, fc(point({"external_id": "X1", "category": "pothole", "reported_at": "2026-08-01"}, 72.87, 19.0)))
    assert s["duplicates_existing"] == 1 and db.execute("select count(*) from observation").fetchone()[0] == 1


# ---------------- boundaries ----------------
def test_boundary_preview_qa_and_commit_switches_active_areas(db, settings):
    p = bnd(db, settings, NS)
    assert p["status"] == "preview" and p["qa"]["ok"] and p["qa"]["usable_features"] == 2
    assert p["crs_basis"] == "assumed-wgs84" and p["qa"]["gaps"] == "not assessed" and p["qa"]["overlap_count"] == 0
    assert db.execute("select count(*) from boundary_version").fetchone()[0] == 0  # preview writes nothing
    c = bnd(db, settings, NS, commit=True)
    assert c["status"] == "active"
    active = {r[0] for r in db.execute("select name from area where is_synthetic=1 and is_active=1")}
    assert active == {"North", "South"}
    assert db.execute("select count(*) from area where is_synthetic=1 and is_active=0").fetchone()[0] == 9  # old zones kept, inactive
    # new imports now resolve against the new version
    s = run_import(db, settings, data=b"category,latitude,longitude\npothole,19.02,72.87\n", filename="x.csv",
                   source_id="synthetic-fixture", commit=True, now=NOW)
    assert s["rows_accepted"] == 1
    assert db.execute("select area_id from observation").fetchone()[0] == f"{c['boundary_version_id']}:North"
    # re-import: idempotent
    assert bnd(db, settings, NS, commit=True)["status"] == "already_imported"
    assert db.execute("select count(*) from boundary_version").fetchone()[0] == 1


def test_invalid_geometry_quarantines_whole_file_and_keeps_existing_areas(db, settings):
    bowtie = [[[72.8, 19.0], [72.9, 19.05], [72.9, 19.0], [72.8, 19.05], [72.8, 19.0]]]
    data = fc(poly("Good", sq(72.8, 18.95, 72.9, 19.0)), poly("Bow", bowtie))
    c = bnd(db, settings, data, commit=True)
    assert c["status"] == "failed" and c["qa"]["blocking_issue_counts"] == {"invalid_geometry": 1}
    assert "Self-intersection" in c["qa"]["blocking_issues"]["invalid_geometry"][0]["reason"]
    assert db.execute("select count(*) from area where name='Good'").fetchone()[0] == 0  # no partial ward set
    assert db.execute("select count(*) from area where is_synthetic=1 and is_active=1").fetchone()[0] == 9  # unchanged
    assert db.execute("select status from boundary_version").fetchone()[0] == "failed"
    assert bnd(db, settings, data, commit=True)["status"] == "failed"  # retry replaces failed record, no unique violation
    assert db.execute("select count(*) from boundary_version").fetchone()[0] == 1


def test_blocking_issue_kinds(db, settings):
    data = fc(poly("A", sq(72.8, 18.95, 72.9, 19.0)), poly("a", sq(72.8, 19.0, 72.9, 19.05)),   # duplicate name (case-insens.)
              poly(None, sq(72.9, 19.0, 73.0, 19.05)),                                           # missing name
              point({"name": "P"}, 72.9, 19.0),                                                  # not a polygon
              poly("Far", sq(72.9, 18.0, 400.0, 19.0)))                                          # outside lon range
    q = bnd(db, settings, data)["qa"]
    assert q["ok"] is False
    assert q["blocking_issue_counts"] == {"not_polygon": 1, "bad_coordinates": 1, "missing_name": 1, "duplicate_name": 1}


def test_overlap_is_a_warning_not_a_blocker(db, settings):
    data = fc(poly("A", sq(72.80, 18.95, 72.90, 19.00)), poly("B", sq(72.85, 18.95, 72.95, 19.00)))
    q = bnd(db, settings, data)["qa"]
    assert q["ok"] and q["overlap_count"] == 1 and q["overlap_warnings"][0]["overlap_ratio_of_smaller"] == 0.5


def test_touching_borders_are_not_overlaps(db, settings):
    assert bnd(db, settings, NS)["qa"]["overlap_count"] == 0


def test_boundary_crs_handling(db, settings):
    declared = fc(poly("A", sq(72.8, 18.95, 72.9, 19.0)), crs={"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}})
    assert bnd(db, settings, declared)["crs_basis"] == "declared-wgs84"
    utm = fc(poly("A", sq(72.8, 18.95, 72.9, 19.0)), crs={"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::32643"}})
    with pytest.raises(AppError) as e:
        bnd(db, settings, utm)
    assert e.value.code == "crs_unsupported"


def test_name_property_autodetect_and_override(db, settings):
    data = fc(poly("Ward A", sq(72.8, 18.95, 72.9, 19.0), key="ward"))
    assert bnd(db, settings, data)["qa"]["name_property"] == "ward"
    custom = fc({"type": "Feature", "properties": {"label": "L1"}, "geometry": {"type": "Polygon", "coordinates": sq(72.8, 18.95, 72.9, 19.0)}})
    assert bnd(db, settings, custom)["qa"]["ok"] is False  # no usable name property: refused, never guessed
    assert bnd(db, settings, custom, name_property="label")["qa"]["ok"]


def test_boundary_label_required_to_commit(db, settings):
    with pytest.raises(AppError) as e:
        bnd(db, settings, NS, commit=True, label="  ")
    assert e.value.code == "label_required"


@requires_wards
def test_real_boundaries_need_licence_and_do_not_touch_synthetic_zones(db):
    real = Settings(data_mode="real")
    with pytest.raises(AppError) as e:
        bnd(db, real, NS, commit=True, source="manual-csv-geojson")
    assert e.value.code == "licence_required"
    c = bnd(db, real, NS, commit=True, source="manual-csv-geojson", licence="Own data")
    assert c["status"] == "active"
    assert db.execute("select count(*) from area where is_synthetic=1 and is_active=1").fetchone()[0] == 9   # synthetic untouched
    assert db.execute("select count(*) from area where is_synthetic=0 and is_active=1").fetchone()[0] == 2   # wards replaced by version
