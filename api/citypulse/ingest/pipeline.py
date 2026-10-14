"""CSV import: preview (dry run, no writes) and commit (single transaction, idempotent).

Idempotency: (source_id, file sha256, parser_version) identifies a batch; (source_id, record_hash) identifies a
record. Re-importing the same file adds zero rows. Same external_id with different content -> quarantined, never
silently overwritten. A batch with zero accepted rows fails visibly instead of producing a blank "success".
"""
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from citypulse.core.errors import AppError, Conflict, NotFound
from citypulse.core.provenance import new_id, sha256_bytes
from citypulse.core.settings import ROOT, Settings
from citypulse.geo.areas import load_index
from citypulse.ingest.normalise import SCHEMA_VERSION, normalise_row
from citypulse.ingest.parse import auto_map, parse_csv, validate_mapping

PARSER_VERSION = "csv-1.0.0"
UPLOAD_DIR = ROOT / "data" / "raw" / "uploads"
IMPORTABLE_ACCESS = {"local-generated", "user-provided-file"}


def _source(con: sqlite3.Connection, source_id: str, settings: Settings, *, need_licence: str | None, commit: bool):
    s = con.execute("SELECT * FROM source_registry WHERE source_id=?", (source_id,)).fetchone()
    if not s:
        raise NotFound(f"Unknown source '{source_id}'.")
    if s["access_method"] not in IMPORTABLE_ACCESS or s["source_status"] != "verified":
        raise AppError(f"Source '{source_id}' cannot be imported by file upload.", code="source_not_importable")
    if bool(s["is_synthetic"]) != (settings.data_mode == "synthetic"):
        raise Conflict(f"Source '{source_id}' is {'synthetic' if s['is_synthetic'] else 'real'} but the app is in "
                       f"{settings.data_mode} mode. Synthetic and real data are never mixed.", code="data_mode_mismatch")
    if commit and not s["is_synthetic"] and not (need_licence or "").strip():
        raise AppError("User-supplied data requires a declared licence/permission.",
                       fields={"licence_declared": "required"}, code="licence_required")
    return s


def _process(con, data: bytes, source_id: str, mapping_override: dict | None, tz_name: str, settings: Settings, now: datetime):
    parsed = parse_csv(data)
    mapping = auto_map(parsed.headers)
    if mapping_override:
        mapping.update({k: (v or None) for k, v in mapping_override.items()})
    validate_mapping(mapping, parsed.headers)
    index = load_index(con, settings.data_mode == "synthetic")
    if not index.ids:
        raise AppError("No areas loaded for this data mode; run the seed first.", code="no_areas")

    results, errors, flags = [], Counter(), Counter(parsed.flags)
    seen_hash: dict[str, str] = {}
    seen_ext: dict[str, str] = {}
    accepted, dup_in_file, quarantined = [], 0, []
    for i, raw in enumerate(parsed.rows, start=2):  # row 1 is the header
        r = normalise_row(i, raw, mapping, source_id=source_id, index=index, tz_name=tz_name, now=now)
        if r.obs:
            o = r.obs
            if o["record_hash"] in seen_hash:
                dup_in_file += 1
                continue
            if o["external_id"] and o["external_id"] in seen_ext:
                r.errors.append("conflicting_duplicate_id")
                r.obs = None
            else:
                seen_hash[o["record_hash"]] = o["external_id"] or ""
                if o["external_id"]:
                    seen_ext[o["external_id"]] = o["record_hash"]
        if r.errors:
            for c in r.errors:
                errors[c] += 1
            quarantined.append(r)
        else:
            for f in r.flags:
                flags[f] += 1
            accepted.append(r)
    return parsed, mapping, accepted, quarantined, dup_in_file, errors, flags


def _existing_filter(con, source_id, accepted):
    """Drop rows already stored (re-import across files). Returns (new rows, dup_existing, conflicts)."""
    new, dup_existing, conflicts = [], 0, []
    for r in accepted:
        o = r.obs
        if con.execute("SELECT 1 FROM observation WHERE source_id=? AND record_hash=?", (source_id, o["record_hash"])).fetchone():
            dup_existing += 1
        elif o["external_id"] and con.execute("SELECT 1 FROM observation WHERE source_id=? AND external_id=?",
                                                (source_id, o["external_id"])).fetchone():
            r.errors.append("conflicting_duplicate_id")
            conflicts.append(r)
        else:
            new.append(r)
    return new, dup_existing, conflicts


def run_import(con: sqlite3.Connection, settings: Settings, *, data: bytes, filename: str, source_id: str,
               mapping: dict | None = None, tz_name: str = "Asia/Kolkata", licence_declared: str | None = None,
               commit: bool = False, now: datetime | None = None) -> dict:
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise AppError(f"File exceeds {settings.max_upload_mb} MB.", code="file_too_large")
    now = now or datetime.now(timezone.utc)
    _source(con, source_id, settings, need_licence=licence_declared, commit=commit)
    sha = sha256_bytes(data)

    prior = con.execute("SELECT batch_id,status FROM ingestion_batch WHERE source_id=? AND file_sha256=? AND parser_version=?",
                        (source_id, sha, PARSER_VERSION)).fetchone()
    already = prior is not None and prior["status"] in ("accepted", "quarantined")

    parsed, mp, accepted, quarantined, dup_in_file, errors, flags = _process(con, data, source_id, mapping, tz_name, settings, now)
    new, dup_existing, conflicts = _existing_filter(con, source_id, accepted)
    for r in conflicts:
        errors["conflicting_duplicate_id"] += 1
        quarantined.append(r)

    summary = {
        "source_id": source_id, "data_mode": settings.data_mode, "file_name": filename, "file_sha256": sha,
        "parser_version": PARSER_VERSION, "encoding": parsed.encoding, "delimiter": parsed.delimiter,
        "headers": parsed.headers, "mapping": mp, "rows_total": len(parsed.rows),
        "rows_accepted": len(new), "rows_quarantined": len(quarantined),
        "rows_duplicate": dup_in_file + dup_existing, "duplicates_in_file": dup_in_file,
        "duplicates_existing": dup_existing,
        "error_counts": dict(errors), "flag_counts": dict(flags), "already_imported": already,
        "sample": parsed.rows[:5],
        "caveats": ["Rows are reports, not confirmed incidents.",
                    "Rows without point coordinates are kept at area level or unresolved; they are never given a fake point.",
                    "Quarantined rows are stored redacted and can be reviewed; they are excluded from analytics."],
    }
    if not commit:
        summary["status"] = "preview"
        return summary

    if already:
        return summary | {"status": "already_imported", "batch_id": prior["batch_id"],
                          "rows_accepted": 0, "rows_quarantined": 0, "rows_duplicate": summary["rows_total"]}

    status = "failed" if not new else ("quarantined" if quarantined else "accepted")
    batch_id = new_id("batch")
    stamp = now.isoformat()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)[:80] or "upload.csv"
    raw_path = UPLOAD_DIR / f"{sha[:16]}_{safe}"
    raw_path.write_bytes(data)  # immutable raw snapshot (gitignored)

    with con:
        if prior is not None:  # previous attempt failed: replace it, keep the audit trail
            con.execute("DELETE FROM quarantine_row WHERE batch_id=?", (prior["batch_id"],))
            con.execute("DELETE FROM ingestion_batch WHERE batch_id=?", (prior["batch_id"],))
        con.execute(
            """INSERT INTO ingestion_batch (batch_id,source_id,file_name,file_sha256,started_at,finished_at,status,
                 parser_version,rows_total,rows_accepted,rows_quarantined,rows_duplicate,data_mode,licence_declared,
                 mapping_json,raw_path,summary_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (batch_id, source_id, safe, sha, stamp, stamp, status, PARSER_VERSION, summary["rows_total"], len(new),
             len(quarantined), summary["rows_duplicate"], settings.data_mode, licence_declared, json.dumps(mp),
             str(raw_path.relative_to(ROOT)),
             json.dumps({k: summary[k] for k in ("error_counts", "flag_counts", "encoding", "delimiter")})))
        for q in quarantined:
            con.execute("INSERT INTO quarantine_row (batch_id,row_number,error_codes,redacted_excerpt) VALUES (?,?,?,?)",
                        (batch_id, q.row_number, json.dumps(q.errors), q.excerpt))
        for r in new:
            o = r.obs
            con.execute(
                """INSERT INTO observation (observation_id,source_id,batch_id,external_id,category,text_raw,text_normalized,
                     reported_at,observed_at,event_time_precision,status_source,latitude,longitude,area_id,location_method,
                     location_confidence,quality_flags,record_hash,created_at,schema_version)
                   VALUES (?,?,?,?,?,?,?,?,NULL,?,?,?,?,?,?,?,?,?,?,?)""",
                (new_id("obs"), source_id, batch_id, o["external_id"], o["category"], o["text_raw"], o["text_normalized"],
                 o["reported_at"], o["event_time_precision"], o["status_source"], o["latitude"], o["longitude"],
                 o["area_id"], o["location_method"], o["location_confidence"], json.dumps(sorted(set(r.flags))),
                 o["record_hash"], stamp, SCHEMA_VERSION))
        con.execute("INSERT INTO audit_event (at,actor,action,ref,detail) VALUES (?,?,?,?,?)",
                    (stamp, "local-user", "import", batch_id,
                     json.dumps({"source_id": source_id, "status": status, "accepted": len(new), "quarantined": len(quarantined)})))
    return summary | {"status": status, "batch_id": batch_id}
