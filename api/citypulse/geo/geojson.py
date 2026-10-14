"""GeoJSON helpers (RFC 7946: WGS84, [lon, lat] order). We never reproject: a declared non-WGS84 CRS is refused."""
import json

from citypulse.core.errors import AppError

MAX_FEATURES = 200_000
_WGS84 = ("crs84", "epsg::4326", "epsg:4326", "4326")


def load_feature_collection(data: bytes) -> dict:
    try:
        gj = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        raise AppError("File is not valid UTF-8 JSON.", code="malformed_geojson") from None
    if not isinstance(gj, dict) or gj.get("type") != "FeatureCollection" or not isinstance(gj.get("features"), list):
        raise AppError("Expected a GeoJSON FeatureCollection.", code="malformed_geojson")
    if not gj["features"]:
        raise AppError("FeatureCollection has no features.", code="empty_file")
    if len(gj["features"]) > MAX_FEATURES:
        raise AppError(f"More than {MAX_FEATURES:,} features.", code="too_many_rows")
    return gj


def crs_basis(gj: dict) -> tuple[str, str]:
    """-> (crs label, basis). Legacy 'crs' member is honoured only if it names WGS84."""
    crs = gj.get("crs")
    if crs is None:
        return "WGS84 (EPSG:4326)", "assumed-wgs84"
    name = str(((crs or {}).get("properties") or {}).get("name", "")).lower()
    if any(name.endswith(w) or w in name for w in _WGS84):
        return "WGS84 (EPSG:4326)", "declared-wgs84"
    raise AppError(f"Declared CRS '{name or crs}' is not WGS84; reproject before importing (we never guess CRS).",
                   code="crs_unsupported")
