"""Row validation/normalisation. Nothing is silently coerced: every repair or doubt becomes a flag,
every rejection becomes an error code. Raw values are never invented (no fake time/coordinates)."""
import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from citypulse.core.csv_safety import is_formula_like
from citypulse.geo.areas import AreaIndex
from citypulse.ingest.parse import MAX_FIELD_CHARS

CATEGORIES = {"waterlogging", "pothole", "drain_blockage", "garbage", "streetlight"}
ALIASES = {"water_logging": "waterlogging", "flooding": "waterlogging", "potholes": "pothole",
           "drain_choke": "drain_blockage", "drainage": "drain_blockage", "garbage_dump": "garbage",
           "street_light": "streetlight", "street_lights": "streetlight"}
TEXT_CAP = 2000
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
_DMY = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$")
SCHEMA_VERSION = "obs-1"


@dataclass
class RowResult:
    row_number: int
    errors: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    obs: dict | None = None
    excerpt: str = ""


def redact(text: str) -> tuple[str, bool]:
    out = _PHONE.sub("[phone]", _EMAIL.sub("[email]", text))
    return out, out != text


def slug_category(raw: str) -> str:
    s = re.sub(r"[\s\-/]+", "_", raw.strip().lower())
    return ALIASES.get(s, s)


def parse_timestamp(raw: str, tz_name: str, now: datetime) -> tuple[str, str, list[str]]:
    """-> (stored value, precision, flags). Raises ValueError with an error code."""
    s = raw.strip()
    flags: list[str] = []
    dt: datetime | None = None
    date_only: date | None = None
    m = _DMY.match(s)
    try:
        if m:
            d, mo, y, hh, mm, ss = m.groups()
            if hh is None:
                date_only = date(int(y), int(mo), int(d))
            else:
                dt = datetime(int(y), int(mo), int(d), int(hh), int(mm), int(ss or 0))
            flags.append("dmy_format_assumed")
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            date_only = date.fromisoformat(s)
        else:
            dt = datetime.fromisoformat(s)
    except ValueError:
        raise ValueError("invalid_timestamp") from None
    if date_only:
        if date_only.year < 2000 or date_only > (now + timedelta(days=1)).date():
            raise ValueError("timestamp_out_of_range")
        return date_only.isoformat(), "day", flags
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz_name))
        flags.append("tz_assumed")
    utc = dt.astimezone(timezone.utc)
    if utc.year < 2000 or utc > now + timedelta(days=1):
        raise ValueError("timestamp_out_of_range")
    return utc.isoformat(), "minute", flags


def _float(raw: str) -> float | None:
    s = raw.strip()
    if not s:
        return None
    v = float(s)  # may raise ValueError
    if math.isnan(v) or math.isinf(v):
        raise ValueError
    return v


def normalise_row(row_number: int, raw: dict[str, str], mapping: dict[str, str | None], *, source_id: str,
                  index: AreaIndex, tz_name: str, now: datetime) -> RowResult:
    res = RowResult(row_number)
    g = lambda k: (raw.get(mapping[k], "") if mapping.get(k) else "").strip()  # noqa: E731
    res.excerpt = redact(json.dumps(raw, ensure_ascii=False)[:300])[0]

    if any(len(v) > MAX_FIELD_CHARS for v in raw.values()):
        res.errors.append("field_too_long")
        return res

    category = slug_category(g("category"))
    if not category:
        res.errors.append("missing_category")
    elif category not in CATEGORIES:
        res.flags.append("unrecognised_category")

    reported_at, precision = None, "unknown"
    if g("reported_at"):
        try:
            reported_at, precision, f = parse_timestamp(g("reported_at"), tz_name, now)
            res.flags += f
        except ValueError as e:
            res.errors.append(str(e))
    else:
        res.flags.append("missing_timestamp")

    lat = lon = None
    try:
        lat, lon = _float(g("latitude")), _float(g("longitude"))
    except ValueError:
        res.errors.append("coords_not_numeric")
    if "coords_not_numeric" not in res.errors:
        if (lat is None) != (lon is None):
            res.errors.append("coords_incomplete")
        elif lat is not None:
            if abs(lat) > 90 or abs(lon) > 180:
                res.errors.append("coords_invalid_range")
            elif not index.in_bounds(lon, lat):
                res.errors.append("coords_possibly_swapped"
                                  if abs(lon) <= 90 and abs(lat) <= 180 and index.in_bounds(lat, lon)
                                  else "coords_out_of_bounds")

    area_name = g("area_name") or None
    text, pii = redact(g("text")[:TEXT_CAP])
    if len(g("text")) > TEXT_CAP:
        res.flags.append("text_truncated")
    if pii:
        res.flags.append("pii_redacted")
    if is_formula_like(g("text")):
        res.flags.append("formula_like_text")

    if res.errors:
        return res

    area_id, method, conf = None, "unresolved", None
    if lat is not None:
        area_id = index.locate(lon, lat)
        method, conf = "point", 0.9
        if area_id is None:
            res.flags.append("outside_all_areas")
    else:
        res.flags.append("no_point_coordinates")
        area_id = index.by_name(area_name)
        if area_id:
            method, conf = "area-name", 0.4
        else:
            res.flags.append("location_unresolved")

    ext = g("external_id") or None
    status = g("status").lower() or None
    h = hashlib.sha256(json.dumps([source_id, ext, category, text, reported_at, lat, lon, area_name, status],
                                  ensure_ascii=False).encode()).hexdigest()
    res.obs = {"external_id": ext, "category": category, "text_raw": text, "text_normalized": " ".join(text.lower().split()),
               "reported_at": reported_at, "event_time_precision": precision, "status_source": status,
               "latitude": lat, "longitude": lon, "area_id": area_id, "location_method": method,
               "location_confidence": conf, "record_hash": h}
    return res
