"""Deterministic, versioned metrics (blueprint 042/049). Every result states its scope, window, denominator and
exclusions, and is recorded as an analysis_run whose id is a hash of (metric, version, params, mode, input digest):
the same inputs always give the same run, and any later data change is detectable.

All times are bucketed in Asia/Kolkata (display/aggregation zone); stored values stay UTC (blueprint 028)."""
import hashlib
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone

from citypulse.core.settings import Settings
from citypulse.db.queries import FROM, IST_DAY, Filters, where

SUMMARY_V = "summary-1.0.0"
TREND_V = "trend-1.0.0"
MIN_SAMPLE = 30

METRICS = {
    "summary": {"version": SUMMARY_V, "title": "Report summary",
                "definition": "Count of stored report rows matching the filters. A report is not a confirmed incident; "
                              "duplicates already skipped at import; quarantined rows excluded.",
                "per_10k": "reports / area population * 10,000, only where the area has a population; otherwise 'not calculated'."},
    "trend": {"version": TREND_V, "title": "Reports over time",
              "definition": "Count of dated reports per Asia/Kolkata calendar day or ISO week (Monday start). Undated rows excluded "
                            "and counted separately. A 0 bucket means no report was recorded, not that nothing happened."},
}


def _inputs(con, synthetic: bool, f: Filters):
    w, args = where(synthetic, f)
    ids = [r[0] for r in con.execute(f"SELECT o.observation_id {FROM} WHERE {w} ORDER BY o.observation_id", args)]
    digest = hashlib.sha256("\n".join(ids).encode()).hexdigest()
    src = [r[0] for r in con.execute(f"SELECT DISTINCT o.source_id {FROM} WHERE {w} ORDER BY 1", args)]
    bat = [r[0] for r in con.execute(f"SELECT DISTINCT o.batch_id {FROM} WHERE {w} ORDER BY 1", args)]
    return w, args, len(ids), digest, src, bat


def digest_of(con, synthetic: bool, f: Filters) -> tuple[int, str]:
    _, _, n, d, _, _ = _inputs(con, synthetic, f)
    return n, d


def _mode_caveats(settings: Settings) -> list[str]:
    c = ["Rows are reports, not confirmed incidents; a high count reflects reporting as well as underlying problems."]
    if settings.data_mode == "synthetic":
        c.insert(0, "SYNTHETIC DEMO DATA — generated for demonstration; says nothing about any real place.")
    return c


def _summary(con, settings, f: Filters, w, args, n) -> tuple[dict, list[str], dict]:
    q = lambda sql, a=args: con.execute(sql, a).fetchall()  # noqa: E731
    with_point = q(f"SELECT COUNT(*) {FROM} WHERE {w} AND o.latitude IS NOT NULL")[0][0]
    undated = q(f"SELECT COUNT(*) {FROM} WHERE {w} AND o.reported_at IS NULL")[0][0]
    date_only = q(f"SELECT COUNT(*) {FROM} WHERE {w} AND o.event_time_precision='day'")[0][0]
    unresolved = q(f"SELECT COUNT(*) {FROM} WHERE {w} AND o.area_id IS NULL")[0][0]
    span = q(f"SELECT MIN({IST_DAY}), MAX({IST_DAY}) {FROM} WHERE {w} AND o.reported_at IS NOT NULL")[0]
    by_cat = [{"category": r[0], "count": r[1]} for r in
              q(f"SELECT o.category, COUNT(*) c {FROM} WHERE {w} GROUP BY o.category ORDER BY c DESC, o.category")]
    by_area, any_pop = [], False
    for r in q(f"SELECT o.area_id, a.name, a.population, a.population_vintage, COUNT(*) c {FROM} WHERE {w} AND o.area_id IS NOT NULL "
               "GROUP BY o.area_id ORDER BY c DESC, o.area_id"):
        pop = r["population"]
        calc = bool(pop and pop > 0)
        any_pop |= calc
        by_area.append({"area_id": r["area_id"], "area": r["name"], "count": r[4], "population": pop,
                        "population_vintage": r["population_vintage"],
                        "per_10k": round(r[4] / pop * 10000, 2) if calc else None,
                        "per_10k_status": "calculated" if calc else "not calculated: no population denominator"})
    caveats = _mode_caveats(settings)
    if n < MIN_SAMPLE:
        caveats.append(f"Small sample ({n} < {MIN_SAMPLE}): rankings and percentages are unstable.")
    if any_pop:
        caveats.append("Per-10k rates use Census 2011 population: a 15-year-old denominator, not current residents. "
                       "Do not read them as risk or as which area is 'worst'.")
    elif by_area:
        caveats.append("No population denominator for these areas: cross-area comparisons are raw counts and NOT exposure-adjusted.")
    result = {
        "total": n, "with_point": with_point, "without_point": n - with_point, "undated": undated, "date_only": date_only,
        "area_unresolved": unresolved, "observed_window_ist": {"first_day": span[0], "last_day": span[1]},
        "by_category": by_cat, "by_area": by_area,
    }
    quality = {"denominator": "all stored reports matching the filters", "exclusions": "quarantined rows, duplicates skipped at import"}
    return result, caveats, quality


def _trend(con, settings, f: Filters, w, args, n, granularity: str) -> tuple[dict, list[str], dict]:
    bucket = IST_DAY if granularity == "day" else f"date({IST_DAY},'-6 days','weekday 1')"
    rows = con.execute(f"SELECT {bucket} b, COUNT(*) c {FROM} WHERE {w} AND o.reported_at IS NOT NULL GROUP BY b ORDER BY b", args).fetchall()
    undated = con.execute(f"SELECT COUNT(*) {FROM} WHERE {w} AND o.reported_at IS NULL", args).fetchone()[0]
    counts = {r[0]: r[1] for r in rows}
    series = []
    if counts:
        step = timedelta(days=1 if granularity == "day" else 7)
        cur, last = date.fromisoformat(min(counts)), date.fromisoformat(max(counts))
        while cur <= last:
            k = cur.isoformat()
            series.append({"start": k, "count": counts.get(k, 0), "no_reports": k not in counts})
            cur += step
    caveats = _mode_caveats(settings)
    caveats.append("A 'no reports' bucket means nothing was recorded in this source, not that nothing happened.")
    if n < MIN_SAMPLE:
        caveats.append(f"Small sample ({n} < {MIN_SAMPLE}): do not read trends or seasonality into this series.")
    if undated:
        caveats.append(f"{undated} report(s) have no date and are not in the series.")
    result = {"granularity": granularity, "timezone": "Asia/Kolkata", "dated_total": sum(counts.values()), "undated": undated,
              "buckets": len(series), "series": series}
    quality = {"denominator": "dated reports matching the filters", "exclusions": "undated rows; quarantined rows; duplicates"}
    return result, caveats, quality


def run_metric(con: sqlite3.Connection, settings: Settings, metric: str, f: Filters, *, granularity: str = "day") -> dict:
    synthetic = settings.data_mode == "synthetic"
    w, args, n, digest, src, bat = _inputs(con, synthetic, f)
    params = {"filters": f.as_dict()} | ({"granularity": granularity} if metric == "trend" else {})
    version = METRICS[metric]["version"]
    if metric == "summary":
        result, caveats, quality = _summary(con, settings, f, w, args, n)
    else:
        result, caveats, quality = _trend(con, settings, f, w, args, n, granularity)
    run_id = "run_" + hashlib.sha256(json.dumps([metric, version, params, settings.data_mode, digest], sort_keys=True).encode()).hexdigest()[:12]
    now = datetime.now(timezone.utc).isoformat()
    payload = {"result": result, "caveats": caveats, "quality": quality}
    with con:
        con.execute(
            """INSERT OR IGNORE INTO analysis_run (run_id,metric,metric_version,params_json,data_mode,input_count,input_digest,
                 window_start,window_end,source_ids_json,batch_ids_json,created_at,result_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (run_id, metric, version, json.dumps(params, sort_keys=True), settings.data_mode, n, digest, f.date_from, f.date_to,
             json.dumps(src), json.dumps(bat), now, json.dumps(payload)))
    created = con.execute("SELECT created_at FROM analysis_run WHERE run_id=?", (run_id,)).fetchone()[0]
    return {"run_id": run_id, "metric": metric, "metric_version": version, "kind": "computed", "created_at": created,
            "scope": {"data_mode": settings.data_mode, **f.as_dict(), **({"granularity": granularity} if metric == "trend" else {})},
            "input": {"count": n, "digest": digest, "source_ids": src, "batch_ids": bat}, **payload}
