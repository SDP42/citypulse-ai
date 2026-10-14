import csv
import io

import pytest
from fastapi.testclient import TestClient

from citypulse.core.settings import Settings, get_settings
from citypulse.db.deps import get_db
from citypulse.ingest import pipeline
from citypulse.main import app
from tests.contract.test_api import up
from tests.integration.test_importer import HAND


@pytest.fixture
def client(db, monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_settings] = lambda: Settings(data_mode="synthetic")
    c = TestClient(app)
    assert c.post("/imports", **up()).status_code == 200
    yield c
    app.dependency_overrides.clear()


def test_summary_then_lineage_then_records_agree(client):
    s = client.get("/analytics/summary").json()
    run = s["run_id"]
    lin = client.get(f"/lineage/analysis-runs/{run}").json()
    assert lin["verification"]["status"] == "verified" and lin["input"]["count"] == 5
    assert lin["metric"]["version"] == s["metric_version"] and "not a confirmed incident" in lin["metric"]["definition"]
    assert [x["source_id"] for x in lin["sources"]] == ["synthetic-fixture"] and lin["sources"][0]["is_synthetic"] == 1
    assert len(lin["batches"]) == 1 and lin["batches"][0]["rows_accepted"] == 5 and lin["batches"][0]["file_sha256"]
    rec = client.get(lin["records_url"], params={"limit": 200}).json()
    assert rec["total"] == 5 and len(rec["items"]) == 5
    listed = client.get("/observations", params={"limit": 200}).json()["items"]
    assert {r["observation_id"] for r in rec["items"]} == {r["observation_id"] for r in listed}   # number == rows behind it
    stored = client.get(f"/analysis-runs/{run}").json()
    assert stored["result"] == s["result"] and stored["input"]["digest"] == s["input"]["digest"]


def test_lineage_detects_data_change(client):
    run = client.get("/analytics/summary").json()["run_id"]
    other = "category,reported_at\nstreetlight,2026-08-09\n"
    assert client.post("/imports", files={"file": ("m.csv", io.BytesIO(other.encode()), "text/csv")}, data={"source_id": "synthetic-fixture"}).status_code == 200
    lin = client.get(f"/lineage/analysis-runs/{run}").json()
    assert lin["verification"]["status"] == "data_changed_since_run" and lin["verification"]["current_count"] == 6


def test_filtered_run_records_use_same_filters(client):
    s = client.get("/analytics/summary", params={"category": "pothole"}).json()
    rec = client.get(f"/analysis-runs/{s['run_id']}/records").json()
    assert rec["total"] == 1 and rec["items"][0]["external_id"] == "A2" and rec["items"][0]["category"] == "pothole"


def test_trends_endpoint_and_validation(client):
    t = client.get("/analytics/trends", params={"granularity": "week"}).json()
    assert t["scope"]["granularity"] == "week" and [b["count"] for b in t["result"]["series"]] == [2, 3]
    assert client.get("/analytics/trends", params={"granularity": "year"}).status_code == 422
    assert client.get("/analytics/summary", params={"date_from": "08/01/2026"}).status_code == 422
    assert client.get("/analysis-runs/run_nope").status_code == 404
    assert client.get("/lineage/analysis-runs/run_nope").json()["code"] == "not_found"


def test_export_is_formula_safe_and_labelled(client):
    r = client.get("/observations/export.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert 'filename="SYNTHETIC_citypulse_observations.csv"' in r.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert len(rows) == 5 and {x["data_mode"] for x in rows} == {"synthetic"}
    evil = next(x for x in rows if x["external_id"] == "A7")
    assert evil["text"] == "'=cmd|' /C calc'!A0"             # neutralised: a spreadsheet will show text, not run it
    assert all(not x["text"].startswith(("=", "+", "@")) for x in rows)
    a1 = next(x for x in rows if x["external_id"] == "A1")
    assert a1["latitude"] == "19.0" and a1["quality_flags"] == "[]"   # numbers are not mangled
    assert len(list(csv.DictReader(io.StringIO(client.get("/observations/export.csv", params={"category": "pothole"}).text)))) == 1


def test_quarantine_export(client):
    b = client.get("/imports").json()["items"][0]["batch_id"]
    r = client.get(f"/imports/{b}/quarantine/export.csv")
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert len(rows) == 6 and rows[0]["row_number"] == "4" and rows[0]["error_codes"] == "invalid_timestamp"
    assert "SYNTHETIC_quarantine_" in r.headers["content-disposition"]
    assert client.get("/imports/nope/quarantine/export.csv").status_code == 404


def test_boundary_routes(client):
    ns = b'{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"name":"North"},"geometry":{"type":"Polygon","coordinates":[[[72.8,19.0],[72.9,19.0],[72.9,19.05],[72.8,19.05],[72.8,19.0]]]}}]}'
    f = lambda: {"file": ("b.geojson", io.BytesIO(ns), "application/geo+json")}  # noqa: E731
    p = client.post("/boundaries/preview", files=f(), data={"source_id": "synthetic-fixture"}).json()
    assert p["status"] == "preview" and p["qa"]["ok"]
    assert client.post("/boundaries", files=f(), data={"source_id": "synthetic-fixture"}).status_code == 422  # label required
    c = client.post("/boundaries", files=f(), data={"source_id": "synthetic-fixture", "label": "v1", "level": "ward"}).json()
    assert c["status"] == "active"
    assert [a["name"] for a in client.get("/areas").json()["items"]] == ["North"]
    v = client.get("/boundaries").json()["items"]
    assert v[0]["label"] == "v1" and v[0]["status"] == "active" and v[0]["qa"]["ok"]
