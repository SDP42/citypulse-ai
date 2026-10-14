"""Area lookup for one data mode. Point-in-polygon via STRtree; WGS84 lon/lat (GeoJSON order)."""
import json
import sqlite3
from dataclasses import dataclass

from shapely import STRtree
from shapely.geometry import Point, shape

BOUNDS_MARGIN_DEG = 0.05


@dataclass
class AreaIndex:
    ids: list[str]
    names: dict[str, str]  # lower(name) -> area_id
    geoms: list
    tree: STRtree | None
    bounds: tuple[float, float, float, float] | None  # lon_min, lat_min, lon_max, lat_max (with margin)

    def locate(self, lon: float, lat: float) -> str | None:
        if not self.tree:
            return None
        pt = Point(lon, lat)
        for i in self.tree.query(pt, predicate="intersects"):
            return self.ids[int(i)]
        return None

    def by_name(self, name: str | None) -> str | None:
        return self.names.get(name.strip().lower()) if name else None

    def in_bounds(self, lon: float, lat: float) -> bool:
        if not self.bounds:
            return False
        b = self.bounds
        return b[0] <= lon <= b[2] and b[1] <= lat <= b[3]


def load_index(con: sqlite3.Connection, synthetic: bool) -> AreaIndex:
    rows = con.execute("SELECT area_id,name,geometry_geojson FROM area WHERE is_synthetic=? ORDER BY area_id",
                       (int(synthetic),)).fetchall()
    ids, geoms, names = [], [], {}
    for r in rows:
        if not r["geometry_geojson"]:
            continue
        ids.append(r["area_id"])
        geoms.append(shape(json.loads(r["geometry_geojson"])))
        names[r["name"].strip().lower()] = r["area_id"]
    if not geoms:
        return AreaIndex([], {}, [], None, None)
    minx = min(g.bounds[0] for g in geoms)
    miny = min(g.bounds[1] for g in geoms)
    maxx = max(g.bounds[2] for g in geoms)
    maxy = max(g.bounds[3] for g in geoms)
    m = BOUNDS_MARGIN_DEG
    return AreaIndex(ids, names, geoms, STRtree(geoms), (minx - m, miny - m, maxx + m, maxy + m))
