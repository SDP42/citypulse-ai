"""Zone A: size-limited CSV decoding and column mapping. Cells are only ever read as text."""
import csv
import io
from dataclasses import dataclass, field

from citypulse.core.errors import AppError, PayloadTooLarge

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
