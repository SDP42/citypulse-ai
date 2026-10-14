"""Clip the Geofabrik Western Zone pbf to the Greater Mumbai bbox and write small GeoJSON layers.

Layers (ODbL derived data - keep the attribution): waterways (drains/canals/streams/rivers),
roads (motorway..tertiary), places (suburb/neighbourhood/locality = gazetteer for place matching).
Usage: api/.venv/bin/python scripts/extract_osm_mumbai.py
"""
import json
from pathlib import Path

import osmium as o

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "osm" / "western-zone-latest.osm.pbf"
OUT = ROOT / "data" / "processed" / "osm"
BBOX = (72.74, 18.86, 73.02, 19.31)  # BMC ward bbox + margin
WATER = {"drain", "canal", "stream", "river", "ditch"}
ROADS = {"motorway", "trunk", "primary", "secondary", "tertiary"}
PLACES = {"suburb", "neighbourhood", "quarter", "locality"}


def inside(lon, lat):
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fac = o.geom.GeoJSONFactory()
    layers = {"waterways": [], "roads": [], "places": []}
    fp = o.FileProcessor(str(SRC), o.osm.NODE | o.osm.WAY).with_locations().with_filter(
        o.filter.KeyFilter("waterway", "highway", "place"))
    for obj in fp:
        t = obj.tags
        if obj.is_node():
            if t.get("place") in PLACES and t.get("name") and inside(obj.location.lon, obj.location.lat):
                layers["places"].append({"type": "Feature", "geometry": {"type": "Point",
                    "coordinates": [obj.location.lon, obj.location.lat]},
                    "properties": {"osm_id": obj.id, "name": t.get("name"), "place": t.get("place")}})
            continue
        kind, key = (("waterways", t.get("waterway")) if t.get("waterway") in WATER else
                     ("roads", t.get("highway")) if t.get("highway") in ROADS else (None, None))
        if not kind:
            continue
        try:
            first = obj.nodes[0].location
            if not inside(first.lon, first.lat):
                continue
            geom = json.loads(fac.create_linestring(obj))
        except o.InvalidLocationError:
            continue
        layers[kind].append({"type": "Feature", "geometry": geom,
                             "properties": {"osm_id": obj.id, "type": key, "name": t.get("name")}})
    for name, feats in layers.items():
        p = OUT / f"mumbai_{name}.geojson"
        p.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
        print(f"{name}: {len(feats)} features, {p.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
