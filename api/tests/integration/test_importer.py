import csv
import json
from pathlib import Path

import pytest

from citypulse.core.errors import AppError, Conflict
from citypulse.core.settings import ROOT, Settings
from citypulse.ingest import pipeline
from citypulse.ingest.pipeline import run_import
from tests.conftest import NOW, requires_wards

HAND = """external_id,category,text,reported_at,latitude,longitude,zone_name,status
A1,waterlogging,water on road,2026-08-01T10:00:00+00:00,19.0,72.87,,open
A2,pothole,call me 9876543210,2026-08-02,19.0,72.87,,open
A3,garbage,x,31/02/2026,19.0,72.87,,open
A4,,x,2026-08-01T10:00:00+00:00,19.0,72.87,,open
A5,pothole,x,2026-08-01T10:00:00+00:00,72.87,19.0,,open
A6,drain_blockage,x,2026-08-03 09:00,,,Synthetic Zone 11,open
A7,garbage,"=cmd|' /C calc'!A0",2026-08-04T00:00:00Z,,,Nowhere,open
A1,waterlogging,water on road,2026-08-01T10:00:00+00:00,19.0,72.87,,open
A1,waterlogging,DIFFERENT TEXT,2026-08-01T10:00:00+00:00,19.0,72.87,,open
A10,Water Logging,x,2026-08-05T10:00:00+00:00,0,0,,open
A11,potholes,x,2030-01-01T00:00:00+00:00,19.0,72.87,,open
A12,mystery,x,2026-08-06T00:00:00+00:00,19.0,72.87,,open
"""


def imp(db, settings, data, commit=False, **kw):
    return run_import(db, settings, data=data if isinstance(data, bytes) else data.encode(), filename="t.csv",
                      source_id=kw.pop("source_id", "synthetic-fixture"), commit=commit, now=NOW, **kw)


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "UPLOAD_DIR", tmp_path / "uploads")
    # raw_path is stored relative to ROOT; keep the tmp dir under ROOT-agnostic by patching ROOT too
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)


def test_hand_calculated_preview(db, settings):
    s = imp(db, settings, HAND)
    assert s["status"] == "preview"
    assert (s["rows_total"], s["rows_accepted"], s["rows_quarantined"], s["rows_duplicate"]) == (12, 5, 6, 1)
    assert s["error_counts"] == {"invalid_timestamp": 1, "missing_category": 1, "coords_possibly_swapped": 1,
                                 "conflicting_duplicate_id": 1, "coords_out_of_bounds": 1, "timestamp_out_of_range": 1}
    f = s["flag_counts"]
    assert f["pii_redacted"] == 1 and f["tz_assumed"] == 1 and f["formula_like_text"] == 1
    assert f["no_point_coordinates"] == 2 and f["location_unresolved"] == 1 and f["unrecognised_category"] == 1
    # preview writes nothing
    assert db.execute("select count(*) from observation").fetchone()[0] == 0
    assert db.execute("select count(*) from ingestion_batch").fetchone()[0] == 0


def test_commit_stores_expected_records_and_lineage(db, settings):
    s = imp(db, settings, HAND, commit=True)
    assert s["status"] == "quarantined" and s["rows_accepted"] == 5
    rows = {r["external_id"]: r for r in db.execute("select * from observation")}
    assert set(rows) == {"A1", "A2", "A6", "A7", "A12"}
    assert rows["A1"]["area_id"] == "zone:Z-1-1" and rows["A1"]["location_method"] == "point"
    assert rows["A2"]["reported_at"] == "2026-08-02" and rows["A2"]["event_time_precision"] == "day"
    assert "[phone]" in rows["A2"]["text_raw"] and "9876543210" not in rows["A2"]["text_raw"]
    assert rows["A6"]["location_method"] == "area-name" and rows["A6"]["area_id"] == "zone:Z-1-1"
    assert rows["A6"]["latitude"] is None  # never a fake point
    assert rows["A6"]["reported_at"] == "2026-08-03T03:30:00+00:00"
    assert rows["A7"]["location_method"] == "unresolved" and rows["A7"]["area_id"] is None
    assert all(r["batch_id"] == s["batch_id"] and r["source_id"] == "synthetic-fixture" for r in rows.values())
    q = db.execute("select row_number,error_codes from quarantine_row order by row_number").fetchall()
    assert [r["row_number"] for r in q] == [4, 5, 6, 10, 11, 12]  # header is row 1
    assert json.loads(q[0]["error_codes"]) == ["invalid_timestamp"]
    assert db.execute("select count(*) from audit_event where action='import'").fetchone()[0] == 1


def test_reimport_is_idempotent(db, settings):
    first = imp(db, settings, HAND, commit=True)
    again = imp(db, settings, HAND, commit=True)
    assert again["status"] == "already_imported" and again["batch_id"] == first["batch_id"]
    assert db.execute("select count(*) from observation").fetchone()[0] == 5
    assert db.execute("select count(*) from ingestion_batch").fetchone()[0] == 1


def test_same_records_in_different_file_are_duplicates_not_new_rows(db, settings):
    imp(db, settings, HAND, commit=True)
    other = "external_id,category,text,reported_at,latitude,longitude,zone_name,status\n" \
            "A1,waterlogging,water on road,2026-08-01T10:00:00+00:00,19.0,72.87,,open\n" \
            "A1,waterlogging,changed,2026-08-01T10:00:00+00:00,19.0,72.87,,open\n"
    s = imp(db, settings, other, commit=True)
    assert s["duplicates_existing"] == 1 and s["error_counts"] == {"conflicting_duplicate_id": 1}
    assert s["status"] == "failed" and s["rows_accepted"] == 0  # zero accepted fails visibly
    assert db.execute("select count(*) from observation").fetchone()[0] == 5


def test_failed_batch_can_be_retried_after_fix(db, settings):
    bad = "category,reported_at\n,2026-08-01\n"
    s = imp(db, settings, bad, commit=True)
    assert s["status"] == "failed"
    assert db.execute("select count(*) from observation").fetchone()[0] == 0
    assert db.execute("select count(*) from quarantine_row").fetchone()[0] == 1
    s2 = imp(db, settings, bad, commit=True)  # same file again: replaces the failed attempt, no unique violation
    assert s2["status"] == "failed" and db.execute("select count(*) from ingestion_batch").fetchone()[0] == 1


def test_missing_time_stays_unknown(db, settings):
    s = imp(db, settings, "category,latitude,longitude\npothole,19.0,72.87\n", commit=True)
    r = db.execute("select reported_at,event_time_precision,quality_flags from observation").fetchone()
    assert s["rows_accepted"] == 1 and r["reported_at"] is None and r["event_time_precision"] == "unknown"
    assert "missing_timestamp" in json.loads(r["quality_flags"])


def test_column_mapping_override(db, settings):
    data = "Kind,When,Lat,Lng\npothole,2026-08-01,19.0,72.87\n"
    with pytest.raises(AppError) as e:  # unrecognised header: must ask for a mapping, never guess
        imp(db, settings, data)
    assert e.value.code == "missing_required_mapping"
    s = imp(db, settings, data, mapping={"category": "Kind", "reported_at": "When", "latitude": "Lat", "longitude": "Lng"})
    assert s["rows_accepted"] == 1 and s["error_counts"] == {}


def test_data_modes_never_mix(db, settings):
    with pytest.raises(Conflict) as e:
        imp(db, settings, HAND, source_id="manual-csv-geojson")
    assert e.value.code == "data_mode_mismatch"


def test_unknown_and_non_importable_sources(db, settings):
    with pytest.raises(AppError) as e:
        imp(db, settings, HAND, source_id="nope")
    assert e.value.status == 404
    with pytest.raises(AppError) as e:
        imp(db, settings, HAND, source_id="imd-api")  # candidate API source: no file upload path
    assert e.value.code == "source_not_importable"


def test_file_size_limit(db):
    small = Settings(data_mode="synthetic", max_upload_mb=1)
    with pytest.raises(AppError) as e:
        imp(db, small, b"category\n" + b"x" * (1024 * 1024 + 1))
    assert e.value.code == "file_too_large"


def test_synthetic_fixture_file_invariants(db, settings):
    path = ROOT / "data" / "fixtures" / "synthetic_reports.csv"
    if not path.exists():
        pytest.skip("run scripts/make_fixtures.py")
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode().splitlines()))
    s = imp(db, settings, raw, commit=True)
    assert s["rows_total"] == len(rows)
    assert s["rows_accepted"] + s["rows_quarantined"] + s["rows_duplicate"] == len(rows)
    # independent counts straight from the file (each defective row must be caught, duplicates included)
    e = s["error_counts"]
    assert e.get("missing_category", 0) == sum(r["category"] == "" for r in rows)
    assert e.get("invalid_timestamp", 0) == sum(r["reported_at"] == "31/02/2026" for r in rows)
    assert e.get("coords_possibly_swapped", 0) == sum(bool(r["latitude"]) and float(r["latitude"]) > 70 for r in rows)
    assert not set(e) - {"missing_category", "invalid_timestamp", "coords_possibly_swapped"}
    assert s["flag_counts"].get("no_point_coordinates", 0) > 0
    # no accepted row may lack lineage or carry an out-of-box point
    assert db.execute("select count(*) from observation where batch_id is null or source_id is null").fetchone()[0] == 0
    assert imp(db, settings, raw, commit=True)["status"] == "already_imported"


@requires_wards
def test_real_mode_requires_licence_and_uses_wards(db):
    real = Settings(data_mode="real")
    data = "category,reported_at,latitude,longitude\npothole,2026-08-01,19.07,72.88\n"
    with pytest.raises(AppError) as e:
        imp(db, real, data, commit=True, source_id="manual-csv-geojson")
    assert e.value.code == "licence_required"
    with pytest.raises(Conflict):
        imp(db, real, data, source_id="synthetic-fixture")
    s = imp(db, real, data, commit=True, source_id="manual-csv-geojson", licence_declared="Own data, CC0")
    assert s["rows_accepted"] == 1
    area = db.execute("select area_id from observation").fetchone()[0]
    assert area.startswith("ward:")
