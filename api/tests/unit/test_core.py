import sqlite3

from fastapi.testclient import TestClient

from citypulse.db.connection import migrate
from citypulse.main import app
from citypulse.sources.registry import load_register


def test_blank_db_migrates():
    con = sqlite3.connect(":memory:")
    assert migrate(con) == ["001_core.sql", "002_import.sql", "003_boundaries_analytics.sql"]
    assert migrate(con) == []  # idempotent
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    assert {"source_registry", "observation", "ingestion_batch", "quarantine_row"} <= tables


def test_register_has_no_unverified_active_claims():
    for s in load_register():
        assert s["source_status"] in {"candidate", "verified", "research-only", "blocked", "disabled"}


def test_health_and_error_shape():
    c = TestClient(app)
    assert c.get("/health").json()["data_mode"] in {"synthetic", "real"}
    r = c.get("/sources/nope/status")
    assert r.status_code == 404 and {"code", "message", "correlation_id"} <= r.json().keys()
