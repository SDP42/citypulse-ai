import json
import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, Query

from citypulse.analytics.metrics import METRICS, digest_of, run_metric
from citypulse.api.routes.observations import filters
from citypulse.core.errors import Conflict, NotFound
from citypulse.core.settings import Settings, get_settings
from citypulse.db.deps import get_db
from citypulse.db.queries import FROM, Filters, where

router = APIRouter()


@router.get("/analytics/summary")
def summary(f: Filters = Depends(filters), con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Computes the summary and records an idempotent analysis run (same inputs -> same run_id)."""
    return run_metric(con, settings, "summary", f)


@router.get("/analytics/trends")
def trends(granularity: Literal["day", "week"] = "day", f: Filters = Depends(filters),
           con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    return run_metric(con, settings, "trend", f, granularity=granularity)


def _run(con, run_id: str, settings: Settings):
    r = con.execute("SELECT * FROM analysis_run WHERE run_id=?", (run_id,)).fetchone()
    if not r:
        raise NotFound(f"Unknown analysis run '{run_id}'.")
    if r["data_mode"] != settings.data_mode:
        raise Conflict(f"Run belongs to {r['data_mode']} data; the app is in {settings.data_mode} mode.", code="data_mode_mismatch")
    return r


def _filters_of(r) -> Filters:
    return Filters(**json.loads(r["params_json"])["filters"])


@router.get("/analysis-runs/{run_id}")
def get_run(run_id: str, con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    r = _run(con, run_id, settings)
    return {"run_id": r["run_id"], "metric": r["metric"], "metric_version": r["metric_version"], "created_at": r["created_at"],
            "params": json.loads(r["params_json"]), "data_mode": r["data_mode"],
            "input": {"count": r["input_count"], "digest": r["input_digest"], "source_ids": json.loads(r["source_ids_json"]),
                      "batch_ids": json.loads(r["batch_ids_json"])}, **json.loads(r["result_json"])}


@router.get("/analysis-runs/{run_id}/records")
def run_records(run_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    """The exact rows behind a number (re-derived from the stored filters)."""
    r = _run(con, run_id, settings)
    w, args = where(settings.data_mode == "synthetic", _filters_of(r))
    rows = con.execute(f"SELECT o.observation_id,o.external_id,o.category,o.reported_at,o.area_id,o.batch_id,o.source_id {FROM} "
                       f"WHERE {w} ORDER BY o.observation_id LIMIT ? OFFSET ?", [*args, limit, offset]).fetchall()
    return {"items": [dict(x) for x in rows], "total": r["input_count"], "limit": limit, "offset": offset}


@router.get("/lineage/analysis-runs/{run_id}")
def lineage(run_id: str, con: sqlite3.Connection = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Provenance X-ray data: metric definition -> run -> sources/batches -> licences, plus a live check that the
    underlying rows are still exactly the ones this number was computed from."""
    r = _run(con, run_id, settings)
    f = _filters_of(r)
    now_n, now_digest = digest_of(con, settings.data_mode == "synthetic", f)
    sources = [dict(x) for x in con.execute(
        f"SELECT source_id,source_name,source_status,is_synthetic,licence_name,attribution_text,terms_checked_at,known_limitations "
        f"FROM source_registry WHERE source_id IN ({','.join('?' * len(json.loads(r['source_ids_json']))) or 'NULL'})",
        json.loads(r["source_ids_json"]))]
    batches = [dict(x) for x in con.execute(
        f"SELECT batch_id,file_name,file_sha256,started_at,status,parser_version,rows_total,rows_accepted,rows_quarantined,rows_duplicate,"
        f"licence_declared,raw_path FROM ingestion_batch WHERE batch_id IN ({','.join('?' * len(json.loads(r['batch_ids_json']))) or 'NULL'})",
        json.loads(r["batch_ids_json"]))]
    matches = now_digest == r["input_digest"]
    return {
        "run_id": run_id, "kind": "computed", "created_at": r["created_at"],
        "metric": {"name": r["metric"], "version": r["metric_version"], **METRICS[r["metric"]]},
        "scope": {"data_mode": r["data_mode"], "window_start": r["window_start"], "window_end": r["window_end"], **f.as_dict()},
        "input": {"count": r["input_count"], "digest": r["input_digest"]},
        "verification": {"status": "verified" if matches else "data_changed_since_run", "current_count": now_n,
                         "current_digest": now_digest,
                         "message": "The rows behind this number are exactly the rows it was computed from." if matches else
                                    "Stored data has changed since this run; recompute before relying on it."},
        "sources": sources, "batches": batches, "records_url": f"/analysis-runs/{run_id}/records",
        "evidence_vs_inference": "computed from observed reports; no model inference",
    }
