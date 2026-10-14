"""Deterministic SYNTHETIC fixtures with realistic defects (blueprint 099).

Writes data/fixtures/synthetic_reports.csv and synthetic_zones.geojson.
Zones are fictional rectangles, NOT ward boundaries. Every row is marked source_id=synthetic-fixture.
Usage: python scripts/make_fixtures.py [--seed 7]
"""
import argparse
import csv
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "fixtures"
BBOX = (72.82, 18.95, 72.92, 19.05)  # lon_min, lat_min, lon_max, lat_max (configurable)
GRID = 3  # 3x3 fictional zones
CATS = ["waterlogging", "pothole", "drain_blockage", "garbage", "streetlight"]
HOTSPOTS = {"Z-1-1": 0.34, "Z-0-2": 0.16, "Z-2-0": 0.10}  # invented concentration
DESC = {
    "waterlogging": ["water logged near bus stop", "knee deep water on road", "pani bhar gaya"],
    "pothole": ["large pothole on main road", "khadda road par"],
    "drain_blockage": ["drain overflowing", "nala jam hai"],
    "garbage": ["garbage not collected", "kachra pada hai"],
    "streetlight": ["street light not working"],
}


def zones():
    w = (BBOX[2] - BBOX[0]) / GRID
    h = (BBOX[3] - BBOX[1]) / GRID
    feats = []
    for i in range(GRID):
        for j in range(GRID):
            x0, y0 = BBOX[0] + i * w, BBOX[1] + j * h
            ring = [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h], [x0, y0]]
            feats.append({"type": "Feature",
                          "properties": {"zone_id": f"Z-{i}-{j}", "name": f"Synthetic Zone {i}{j}",
                                         "boundary_source": "synthetic", "synthetic": True},
                          "geometry": {"type": "Polygon", "coordinates": [ring]}})
    return {"type": "FeatureCollection", "features": feats}, w, h


def main(seed: int, n: int):
    rnd = random.Random(seed)
    fc, w, h = zones()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "synthetic_zones.geojson").write_text(json.dumps(fc, indent=1))
    ids = [f["properties"]["zone_id"] for f in fc["features"]]
    weights = [HOTSPOTS.get(z, 0.04) for z in ids]
    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    rows = []
    for k in range(n):
        z = rnd.choices(ids, weights)[0]
        i, j = int(z[2]), int(z[4])
        day = rnd.randrange(0, 120)
        monsoon = math.sin(math.pi * day / 120)  # more waterlogging mid-window
        cat = rnd.choices(CATS, [1 + 6 * monsoon, 2, 1.5 + 2 * monsoon, 2, 1])[0]
        t = start + timedelta(days=day, minutes=rnd.randrange(0, 1440))
        lat = BBOX[1] + (j + rnd.random()) * h
        lon = BBOX[0] + (i + rnd.random()) * w
        rows.append({"external_id": f"SYN-{k:05d}", "category": cat,
                     "text": rnd.choice(DESC[cat]), "reported_at": t.isoformat(),
                     "latitude": round(lat, 6), "longitude": round(lon, 6), "zone_name": f"Synthetic Zone {i}{j}",
                     "status": rnd.choice(["open", "closed", "in_progress"]), "source_id": "synthetic-fixture"})
    # injected defects (so quality gate / quarantine have something real to do)
    for r in rnd.sample(rows, n // 25): r["latitude"] = r["longitude"] = ""          # ward-name only
    for r in rnd.sample(rows, n // 50): r["latitude"], r["longitude"] = r["longitude"], r["latitude"]  # swapped
    for r in rnd.sample(rows, n // 50): r["reported_at"] = "31/02/2026"               # invalid date
    for r in rnd.sample(rows, n // 40): r["category"] = ""                             # missing category
    rows += [dict(r) for r in rnd.sample(rows, n // 30)]                               # exact duplicates
    with open(OUT / "synthetic_reports.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader(); wr.writerows(rows)
    print(f"wrote {len(rows)} rows + {len(fc['features'])} zones to {OUT} (SYNTHETIC)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=7); ap.add_argument("--n", type=int, default=1500)
    a = ap.parse_args(); main(a.seed, a.n)
