import io

import pytest
from fastapi.testclient import TestClient

from citypulse.core.settings import Settings, get_settings
from citypulse.db.deps import get_db
from citypulse.ingest import pipeline
from citypulse.main import app
from tests.integration.test_importer import HAND

ERR_KEYS = {"code", "message", "correlation_id", "fields"}


@pytest.fixture
def client(db, monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_settings] = lambda: Settings(data_mode="synthetic")
    yield TestClient(app)
    app.dependency_overrides.clear()


def up(data=HAND, **form):
    return {"files": {"file": ("t.csv", io.BytesIO(data.encode()), "text/csv")}, "data": {"source_id": "synthetic-fixture", **form}}


def test_preview_has_no_side_effects(client, db):
    r = client.post("/imports/preview", **up())
    assert r.status_code == 200 and r.json()["rows_accepted"] == 5 and r.json()["status"] == "preview"
    assert db.execute("select count(*) from observation").fetchone()[0] == 0


def test_commit_then_list_filter_paginate(client):
    c = client.post("/imports", **up())
    assert c.status_code == 200 and c.json()["status"] == "quarantined"
    r = client.get("/observations", params={"limit": 2}).json()
    assert r["total"] == 5 and len(r["items"]) == 2 and r["scope"]["data_mode"] == "synthetic"
    assert r["quality"] == {"with_point_coordinates": 3, "without_point_coordinates": 2}  # A1,A2,A12 have points
    assert "not confirmed incidents" in r["caveats"][0]
    page2 = client.get("/observations", params={"limit": 2, "offset": 2}).json()["items"]
    ids = [i["observation_id"] for i in r["items"]] + [i["observation_id"] for i in page2]
    assert len(set(ids)) == 4  # deterministic, non-overlapping pages
    only = client.get("/observations", params={"category": "pothole"}).json()
    assert only["total"] == 1 and only["items"][0]["external_id"] == "A2"
    day = client.get("/observations", params={"date_from": "2026-08-04", "date_to": "2026-08-04"}).json()
    assert [i["external_id"] for i in day["items"]] == ["A7"]
    areas = {a["area_id"]: a["observations"] for a in client.get("/areas").json()["items"]}
    assert areas["zone:Z-1-1"] == 4  # A1, A2, A12 by point; A6 by area name


def test_batches_and_quarantine_endpoints(client):
    b = client.post("/imports", **up()).json()["batch_id"]
    assert client.get("/imports").json()["items"][0]["batch_id"] == b
    d = client.get(f"/imports/{b}").json()
    assert d["rows_total"] == 12 and d["summary"]["error_counts"]["invalid_timestamp"] == 1
    q = client.get(f"/imports/{b}/quarantine", params={"limit": 3}).json()
    assert q["total"] == 6 and len(q["items"]) == 3 and q["items"][0]["row_number"] == 4


@pytest.mark.parametrize("call,status,code", [
    (lambda c: c.get("/observations", params={"limit": 1000}), 422, "validation_error"),
    (lambda c: c.get("/observations", params={"date_from": "yesterday"}), 422, "validation_error"),
    (lambda c: c.get("/imports/nope"), 404, "not_found"),
    (lambda c: c.get("/imports/nope/quarantine"), 404, "not_found"),
    (lambda c: c.post("/imports/preview", **up(mapping="not json")), 400, "bad_mapping"),
    (lambda c: c.post("/imports/preview", **up(mapping='{"category": "ghost"}')), 400, "bad_mapping"),
    (lambda c: c.post("/imports/preview", files={"file": ("t.csv", io.BytesIO(b""), "text/csv")}, data={"source_id": "synthetic-fixture"}), 400, "empty_file"),
    (lambda c: c.post("/imports/preview", files={"file": ("t.csv", io.BytesIO(b"a\n1"), "text/csv")}, data={"source_id": "manual-csv-geojson"}), 409, "data_mode_mismatch"),
    (lambda c: c.post("/imports/preview", files={"file": ("t.csv", io.BytesIO(b"a\n1"), "text/csv")}), 422, "validation_error"),
])
def test_error_shape_is_consistent(client, call, status, code):
    r = call(client)
    assert r.status_code == status, r.text
    body = r.json()
    assert set(body) == ERR_KEYS and body["code"] == code and body["correlation_id"]


def test_no_stack_traces_or_paths_leak(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("/Users/secret/path failure")
    monkeypatch.setattr("citypulse.api.routes.imports.run_import", boom)
    r = TestClient(app, raise_server_exceptions=False).post("/imports/preview", **up())
    assert r.status_code == 500 and "secret" not in r.text and r.json()["code"] == "internal_error"
