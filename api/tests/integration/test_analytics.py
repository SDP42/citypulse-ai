import json

import pytest

from citypulse.analytics.metrics import run_metric
from citypulse.core.errors import AppError
from citypulse.db.queries import Filters
from citypulse.ingest import pipeline
from citypulse.ingest.pipeline import run_import
from tests.conftest import NOW
from tests.integration.test_importer import HAND


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)


def load(db, settings, text=HAND, name="h.csv"):
    return run_import(db, settings, data=text.encode(), filename=name, source_id="synthetic-fixture", commit=True, now=NOW)


def summary(db, settings, **f):
    return run_metric(db, settings, "summary", Filters(**f))


def trend(db, settings, g="day", **f):
    return run_metric(db, settings, "trend", Filters(**f), granularity=g)


# Hand-calculated from the 12-row CSV (see test_importer): stored rows are
#  A1 waterlogging 2026-08-01T10:00Z (IST 08-01, point, Z-1-1)   A2 pothole 2026-08-02 (date only, point, Z-1-1)
#  A6 drain_blockage 2026-08-03 09:00 IST (no point, Z-1-1)       A7 garbage 2026-08-04T00:00Z (IST 08-04, unresolved)
#  A12 mystery 2026-08-06T00:00Z (IST 08-06, point, Z-1-1)
def test_summary_matches_hand_calculation(db, settings):
    load(db, settings)
    s = summary(db, settings)
    r = s["result"]
    assert (r["total"], r["with_point"], r["without_point"], r["undated"], r["date_only"], r["area_unresolved"]) == (5, 3, 2, 0, 1, 1)
    assert r["observed_window_ist"] == {"first_day": "2026-08-01", "last_day": "2026-08-06"}
    assert r["by_category"] == [{"category": c, "count": 1} for c in ("drain_blockage", "garbage", "mystery", "pothole", "waterlogging")]
    (area,) = r["by_area"]
    assert area["area_id"] == "zone:Z-1-1" and area["count"] == 4
    assert area["per_10k"] is None and area["per_10k_status"].startswith("not calculated")  # never a made-up rate
    assert s["input"]["count"] == 5 and s["kind"] == "computed" and s["scope"]["data_mode"] == "synthetic"
    text = " ".join(s["caveats"])
    assert "SYNTHETIC DEMO DATA" in s["caveats"][0] and "not confirmed incidents" in text
    assert "Small sample (5 < 30)" in text and "NOT exposure-adjusted" in text


def test_per_10k_calculated_only_with_a_denominator(db, settings):
    load(db, settings)
    db.execute("UPDATE area SET population=20000, population_vintage='Census 2011' WHERE area_id='zone:Z-1-1'")
    db.commit()
    a = summary(db, settings)["result"]["by_area"][0]
    assert a["per_10k"] == 2.0 and a["per_10k_status"] == "calculated"  # 4 / 20000 * 10000
    assert any("15-year-old denominator" in c for c in summary(db, settings)["caveats"])
    db.execute("UPDATE area SET population=0 WHERE area_id='zone:Z-1-1'")
    db.commit()
    a = summary(db, settings)["result"]["by_area"][0]
    assert a["per_10k"] is None  # zero denominator -> not calculated, not infinity or 0


def test_trend_day_fills_gaps_without_claiming_nothing_happened(db, settings):
    load(db, settings)
    t = trend(db, settings)
    assert [(b["start"], b["count"], b["no_reports"]) for b in t["result"]["series"]] == [
        ("2026-08-01", 1, False), ("2026-08-02", 1, False), ("2026-08-03", 1, False), ("2026-08-04", 1, False),
        ("2026-08-05", 0, True), ("2026-08-06", 1, False)]
    assert t["result"]["dated_total"] == 5 and t["result"]["timezone"] == "Asia/Kolkata"
    assert any("nothing was recorded in this source, not that nothing happened" in c for c in t["caveats"])


def test_trend_week_uses_monday_start(db, settings):
    load(db, settings)
    s = trend(db, settings, "week")["result"]["series"]
    # 2026-08-01 is a Saturday -> its week starts Monday 2026-07-27 (A1, A2); the rest fall in the week of 2026-08-03 (A6, A7, A12)
    assert [(b["start"], b["count"]) for b in s] == [("2026-07-27", 2), ("2026-08-03", 3)]


def test_ist_day_boundary_is_used_for_buckets_and_filters(db, settings):
    text = ("category,reported_at,latitude,longitude\n"
            "pothole,2026-08-07T18:29:00+00:00,19.0,72.87\n"   # 23:59 IST on 08-07
            "pothole,2026-08-07T18:30:00+00:00,19.0,72.87\n")  # 00:00 IST on 08-08
    load(db, settings, text)
    assert [(b["start"], b["count"]) for b in trend(db, settings)["result"]["series"]] == [("2026-08-07", 1), ("2026-08-08", 1)]
    assert summary(db, settings, date_from="2026-08-08", date_to="2026-08-08")["result"]["total"] == 1
    assert summary(db, settings, date_from="2026-08-07", date_to="2026-08-07")["result"]["total"] == 1


def test_undated_rows_are_counted_separately_not_dropped_silently(db, settings):
    load(db, settings, "category,reported_at\npothole,2026-08-01\ngarbage,\n", "u.csv")
    t = trend(db, settings)
    assert t["result"]["undated"] == 1 and t["result"]["dated_total"] == 1
    assert summary(db, settings)["result"]["total"] == 2  # still counted in the summary
    assert any("1 report(s) have no date" in c for c in t["caveats"])
    assert summary(db, settings, date_from="2026-01-01")["result"]["total"] == 1  # a date filter excludes undated rows


def test_filters_apply_consistently(db, settings):
    load(db, settings)
    assert summary(db, settings, category="pothole")["result"]["total"] == 1
    assert summary(db, settings, date_from="2026-08-02", date_to="2026-08-03")["result"]["total"] == 2   # A2, A6
    assert summary(db, settings, area_id="zone:Z-1-1")["result"]["total"] == 4
    empty = summary(db, settings, category="streetlight")
    assert empty["result"]["total"] == 0 and empty["result"]["by_area"] == [] and empty["result"]["observed_window_ist"]["first_day"] is None


def test_runs_are_deterministic_and_change_with_data(db, settings):
    load(db, settings)
    a, b = summary(db, settings), summary(db, settings)
    assert a["run_id"] == b["run_id"] and a["result"] == b["result"] and a["input"]["digest"] == b["input"]["digest"]
    assert db.execute("select count(*) from analysis_run").fetchone()[0] == 1  # idempotent, no pile-up
    assert summary(db, settings, category="pothole")["run_id"] != a["run_id"]     # params are part of identity
    assert trend(db, settings)["run_id"] != a["run_id"]
    load(db, settings, "category,reported_at\nstreetlight,2026-08-09\n", "more.csv")
    c = summary(db, settings)
    assert c["run_id"] != a["run_id"] and c["input"]["count"] == 6


def test_empty_database_is_a_state_not_zero_claims(db, settings):
    s = summary(db, settings)
    assert s["result"]["total"] == 0 and s["input"]["count"] == 0
    assert trend(db, settings)["result"]["series"] == []
