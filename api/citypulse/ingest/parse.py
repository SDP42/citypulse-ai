"""Zone A: size-limited CSV decoding and column mapping. Cells are only ever read as text."""
import csv
import io
from dataclasses import dataclass, field

import json

from citypulse.core.errors import AppError, PayloadTooLarge
from citypulse.geo.geojson import crs_basis, load_feature_collection

MAX_ROWS = 200_000
MAX_FIELD_CHARS = 10_000
DELIMS = ",;\t|"

SYNONYMS: dict[str, tuple[str, ...]] = {
    "external_id": ("external_id", "id", "complaint_id", "ticket_id", "reference", "ref"),
    "category": ("category", "type", "issue", "issue_type", "complaint_type", "service_name"),
    "text": ("text", "description", "details", "complaint", "message", "comment"),
    "reported_at": ("reported_at", "created_at", "date", "timestamp", "datetime", "requested_datetime", "reported"),
    "latitude": ("latitude", "lat", "y"),
    "longitude": ("longitude", "lon", "lng", "long", "x"),
    "area_name": ("area_name", "zone_name", "ward", "ward_name", "zone", "area", "locality"),
    "status": ("status", "state"),
}
REQUIRED = ("category",)  # time is optional: unknown stays unknown (never substituted)


@dataclass
class Parsed:
    headers: list[str]
    rows: list[dict[str, str]]
    delimiter: str
    encoding: str
    flags: list[str] = field(default_factory=list)


def decode(data: bytes) -> tuple[str, str, list[str]]:
    for enc, flag in (("utf-8-sig", None), ("cp1252", "encoding_cp1252_assumed")):
        try:
            return data.decode(enc), enc, [flag] if flag else []
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1"), "latin-1", ["encoding_latin1_fallback"]


def sniff_delimiter(text: str) -> str:
    sample = text[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=DELIMS).delimiter
    except csv.Error:
        return ","


def parse_csv(data: bytes) -> Parsed:
    if not data.strip():
        raise AppError("File is empty.", code="empty_file")
    text, enc, flags = decode(data)
    delim = sniff_delimiter(text)
    csv.field_size_limit(MAX_FIELD_CHARS * 2)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delim)
    try:
        header = next(reader)
    except StopIteration:
        raise AppError("File has no header row.", code="no_header") from None
    headers = [h.strip() for h in header]
    if not any(headers):
        raise AppError("Header row is blank.", code="no_header")
    rows: list[dict[str, str]] = []
    try:
        for rec in reader:
            if not any(c.strip() for c in rec):
                continue
            if len(rows) >= MAX_ROWS:
                raise PayloadTooLarge(f"More than {MAX_ROWS:,} rows.", code="too_many_rows")
            rows.append({h: (rec[i] if i < len(rec) else "") for i, h in enumerate(headers) if h})
    except csv.Error as e:
        raise AppError(f"Malformed CSV: {e}", code="malformed_csv") from None
    return Parsed(headers=[h for h in headers if h], rows=rows, delimiter=delim, encoding=enc, flags=flags)


def auto_map(headers: list[str]) -> dict[str, str | None]:
    lower = {h.lower().replace(" ", "_"): h for h in headers}
    return {canon: next((lower[s] for s in syns if s in lower), None) for canon, syns in SYNONYMS.items()}


def validate_mapping(mapping: dict[str, str | None], headers: list[str]) -> None:
    for canon, col in mapping.items():
        if canon not in SYNONYMS:
            raise AppError(f"Unknown field '{canon}' in mapping.", code="bad_mapping")
        if col and col not in headers:
            raise AppError(f"Mapped column '{col}' is not in the file.", fields={canon: col}, code="bad_mapping")
    missing = [r for r in REQUIRED if not mapping.get(r)]
    if missing:
        raise AppError(f"Required field(s) not mapped: {', '.join(missing)}.",
                       fields={m: "unmapped" for m in missing}, code="missing_required_mapping")


def detect_format(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith((".geojson", ".json")) or data.lstrip()[:1] == b"{":
        return "geojson"
    return "csv"


def _cell(v) -> str:
    if v is None:
        return ""
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)


def parse_geojson_points(data: bytes) -> Parsed:
    """Point FeatureCollection -> the same row shape the CSV path produces (one pipeline, one set of rules).
    Any non-Point geometry refuses the whole file: partial ingestion of a mixed file would be misleading."""
    gj = load_feature_collection(data)
    _, basis = crs_basis(gj)
    bad, keys, rows = [], [], []
    for i, f in enumerate(gj["features"]):
        if not isinstance(f, dict):
            bad.append({"feature": i, "type": None})
            continue
        g = f.get("geometry")
        if g is not None and g.get("type") != "Point":
            bad.append({"feature": i, "type": g.get("type")})
            continue
        props = f.get("properties") or {}
        for k in props:
            if k not in keys:
                keys.append(k)
        row = {k: _cell(v) for k, v in props.items()}
        c = (g or {}).get("coordinates") or []
        if len(c) >= 2:
            row["longitude"], row["latitude"] = _cell(c[0]), _cell(c[1])  # GeoJSON order is [lon, lat]
        rows.append(row)
    if bad:
        raise AppError(f"{len(bad)} feature(s) are not Points; this importer accepts Point features only "
                       f"(use the boundary importer for polygons).", fields={"first_bad_features": json.dumps(bad[:5])},
                       code="geometry_not_point")
    headers = keys + [h for h in ("longitude", "latitude") if h not in keys]
    rows = [{h: r.get(h, "") for h in headers} for r in rows]
    flags = ["crs_assumed_wgs84"] if basis == "assumed-wgs84" else []
    return Parsed(headers=headers, rows=rows, delimiter="geojson", encoding="utf-8", flags=flags)
