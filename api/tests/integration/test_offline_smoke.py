"""Blueprint 096: the core path must work with the network disabled."""
import socket

import pytest

from citypulse.core.settings import ROOT
from citypulse.db.connection import connect, migrate
from citypulse.db.seed import seed_all
from citypulse.ingest import pipeline
from citypulse.ingest.pipeline import run_import


def test_import_and_query_with_network_blocked(tmp_path, monkeypatch, settings):
    def blocked(*a, **k):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(pipeline, "UPLOAD_DIR", tmp_path / "up")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    fixture = ROOT / "data" / "fixtures" / "synthetic_reports.csv"
    if not fixture.exists():
        pytest.skip("run scripts/make_fixtures.py")
    con = connect(tmp_path / "smoke.sqlite")
    migrate(con)
    assert seed_all(con)["sources"] >= 9
    s = run_import(con, settings, data=fixture.read_bytes(), filename="f.csv", source_id="synthetic-fixture", commit=True)
    assert s["rows_accepted"] > 1000
    n = con.execute("select count(*) from observation").fetchone()[0]
    assert n == s["rows_accepted"]
    top = con.execute("select area_id, count(*) c from observation group by area_id order by c desc limit 1").fetchone()
    assert top["area_id"] == "zone:Z-1-1"  # the invented hotspot dominates, as generated
